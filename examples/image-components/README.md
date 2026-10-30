# 이미지: 실제 픽셀에서 영역·좌표를 검증

## 과제와 업무 정의
P2 PGM의 밝기>=128인 픽셀을 결함 후보로 세고 연결 영역과 bounding box를 구한다.
x=열, y=행, bbox 끝 좌표는 포함이다. 기본은 상하좌우 4연결이며 8연결은 명시적으로 선택한다.
이 합성 예제는 실제 반도체 결함 인식 성능이나 공정 원인을 증명하지 않는다.

## 실행과 직접 확인
```bash
python3 image_analysis.py --output .harness/overlay.svg
python3 image_analysis.py --connectivity 8
python3 -m unittest discover -s tests -v
```
SVG를 브라우저로 열어 실제 원픽셀 위의 빨간 영역 상자를 확인한다. PGM은 텍스트로도 픽셀을 직접 셀 수 있다.
CLI는 width_px/height_px/foreground_px/regions/duration_ms와 단계 순서를 출력한다.

## 독립 oracle
fixtures/diagonal-edge.pgm은 가로5,세로3이다. (1,0),(0,1)은 대각선 두 픽셀이므로 4연결에서는 각각 1개 영역,
8연결에서는 2픽셀짜리 1영역이다. 오른쪽 경계 (4,0),(4,1)은 2픽셀짜리 영역이다.
따라서 4연결은 총3영역/4픽셀, 8연결은 총2영역/4픽셀이다.
`faults.py`가 대각선을 몰래 연결하면 3영역 oracle을 통과하지 못한다.
127/128/129는 임계값 포함 여부, 비정사각형은 축 혼동, 오른쪽 픽셀은 경계 누락을 검출한다.

## 원인 분석과 검증 분배
디코드 실패는 포맷/픽셀 개수, foreground 수 오류는 임계값/색상 범위, 영역만 오류는 연결 정의,
상자만 어긋나면 x/y·inclusive 좌표·표시 배율을 조사한다. 이 순서로 문제 경계를 좁힌다.
수치 테스트와 SVG 구조 검사로 계산/좌표를 검증하고 사람이 오버레이를 확인한다. SVG 생성만으로 시각 QA 완료라 하지 않는다.
PNG/JPEG, RGB/BGR, EXIF 회전, 리사이즈 역변환은 별도 도메인 경계이며 이 예제의 PGM 검증에 포함되지 않는다.
선택 확장은 실제 입력 형식이 요구할 때만 추가한다. 관련 알고리즘을 바꾼 뒤 동일 fixture 회귀를 실행한다.

`stage_summary`는 단계 설명이며 계측된 span이 아니다. 공통 verify runner의 trace.json은 검사 명령 단위 span을 기록한다.

## 실제 nested trace와 실패 증거 실습
저장소의 공통 Evidence API를 쓰는 `observe.py`는 별도의 실행이다. 외부 패키지는 필요 없지만 저장소의 `src/harness`가 필요하다.
```bash
python3 observe.py
python3 observe.py --fault diagonal
```
두 번째 명령은 의도한 결함 때문에 exit1이어야 정상적인 검증이다. 성공으로 위장하지 않는다.
출력된 `.harness/observations/<run>/`의 report.json, events.jsonl, metrics.json, trace.json을 읽는다.
root/child span과 parent_id, 실제 duration_seconds, 실패 stage/error_type을 확인한다.
정상 실행에서는 oracle이 일치한다. 결함 실행에서는 계산/라벨링은 실행됐지만 compare_oracle에서 실패한다.
이미지는 실패한 경우에도 overlay.svg가 남아 좌표와 결과를 직접 볼 수 있다. 출력 디렉터리 재사용은 거절한다.
