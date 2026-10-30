"""Small, observable CSV application. Python 3.9+, no external services."""
import argparse
import csv
import io
import json
import re
import threading
import time
import traceback
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

FIELDS = ["batch", "equipment", "date", "good", "total"]
MAX_BODY = 1_048_576


class Evidence:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.run_id = uuid.uuid4().hex
        self.lock = threading.Lock()

    def emit(self, **event):
        event.update(run_id=self.run_id, timestamp=datetime.now(timezone.utc).isoformat())
        with self.lock:
            with (self.directory / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    @contextmanager
    def span(self, trace_id, stage, parent_id=None):
        span_id = uuid.uuid4().hex
        started = time.perf_counter()
        self.emit(trace_id=trace_id, span_id=span_id, parent_id=parent_id,
                  stage=stage, event="start")
        try:
            yield span_id
        except Exception as exc:
            self.emit(trace_id=trace_id, span_id=span_id, parent_id=parent_id,
                      stage=stage, event="end", status="FAIL",
                      error_type=type(exc).__name__, duration_ms=(time.perf_counter()-started)*1000)
            raise
        else:
            self.emit(trace_id=trace_id, span_id=span_id, parent_id=parent_id,
                      stage=stage, event="end", status="PASS",
                      duration_ms=(time.perf_counter()-started)*1000)


def parse_csv(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("CSV 파일에 데이터가 필요합니다.")
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    if reader.fieldnames != FIELDS:
        raise ValueError("열은 batch,equipment,date,good,total 순서여야 합니다.")
    rows, seen = [], set()
    for line, raw in enumerate(reader, 2):
        if None in raw or any(v is None for v in raw.values()):
            raise ValueError("행 %d: 열 개수가 다릅니다." % line)
        if not raw["batch"].strip() or not raw["equipment"].strip():
            raise ValueError("행 %d: batch와 equipment가 필요합니다." % line)
        if raw["batch"] in seen:
            raise ValueError("행 %d: batch ID가 중복됩니다." % line)
        seen.add(raw["batch"])
        try:
            if date.fromisoformat(raw["date"]).isoformat() != raw["date"]:
                raise ValueError()
        except ValueError:
            raise ValueError("행 %d: 날짜는 YYYY-MM-DD 형식이어야 합니다." % line)
        if not all(re.fullmatch(r"[0-9]+", raw[k]) for k in ("good", "total")):
            raise ValueError("행 %d: 수량은 음이 아닌 정수여야 합니다." % line)
        good, total = int(raw["good"]), int(raw["total"])
        if total == 0 or good > total:
            raise ValueError("행 %d: total > 0, 0 <= good <= total 이어야 합니다." % line)
        rows.append(dict(raw, good=good, total=total))
    if not rows:
        raise ValueError("CSV 파일에 데이터 행이 필요합니다.")
    return rows


def select_rows(rows, filters):
    if not isinstance(filters, dict):
        raise ValueError("filters는 객체여야 합니다.")
    equipment = filters.get("equipment", "")
    start, end = filters.get("start", ""), filters.get("end", "")
    if not all(isinstance(v, str) for v in (equipment, start, end)):
        raise ValueError("필터 값은 문자열이어야 합니다.")
    for value in (start, end):
        if value:
            try:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError()
            except ValueError:
                raise ValueError("기간은 YYYY-MM-DD 형식이어야 합니다.")
    if start and end and start > end:
        raise ValueError("시작일은 종료일보다 늦을 수 없습니다.")
    return [r for r in rows if (not equipment or r["equipment"] == equipment)
            and (not start or r["date"] >= start) and (not end or r["date"] <= end)]


def summarize(rows):
    good, total = sum(r["good"] for r in rows), sum(r["total"] for r in rows)
    return {"count": len(rows), "good": good, "total": total,
            "yield_rate": good / total if total else None}


def export_csv(rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(FIELDS)
    for row in rows:
        values = [row[k] for k in FIELDS]
        # Exported untrusted text must not become a spreadsheet formula.
        values = [("'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "\t", "\r")) else v)
                  for v in values]
        writer.writerow(values)
    return stream.getvalue().encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Do not duplicate raw URL/data in access logs.

    def send_bytes(self, status, body, content_type, trace_id=""):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Trace-Id", trace_id)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, payload, trace_id=""):
        self.send_bytes(status, json.dumps(payload, ensure_ascii=False).encode(),
                        "application/json; charset=utf-8", trace_id)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self.send_bytes(200, Path(__file__).with_name("index.html").read_bytes(), "text/html; charset=utf-8")
        elif path == "/health":
            self.send_json(200, {"status": "ready", "app": "web-filter-export", "run_id": self.server.evidence.run_id})
        else:
            self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ("/api/analyze", "/api/export"):
            self.send_json(404, {"error": "not_found"})
            return
        trace_id = uuid.uuid4().hex
        evidence = self.server.evidence
        started = time.perf_counter()
        status = 200
        try:
            with evidence.span(trace_id, "request") as parent:
                with evidence.span(trace_id, "decode", parent):
                    length = int(self.headers.get("Content-Length", "0"))
                    if length <= 0 or length > MAX_BODY:
                        raise ValueError("요청 크기는 1 바이트 이상 1 MiB 이하여야 합니다.")
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise ValueError("요청은 JSON 객체여야 합니다.")
                with evidence.span(trace_id, "parse", parent):
                    rows = parse_csv(payload.get("csv"))
                with evidence.span(trace_id, "filter", parent):
                    selected = select_rows(rows, payload.get("filters", {}))
                evidence.emit(trace_id=trace_id, parent_id=parent, stage="rows", event="metric",
                              input_rows=len(rows), output_rows=len(selected), unit="rows")
                with evidence.span(trace_id, "aggregate" if path.endswith("analyze") else "export", parent):
                    if path.endswith("analyze"):
                        result = summarize(selected)
                        result.update(equipment=sorted(set(r["equipment"] for r in rows)),
                                      rows=selected, trace_id=trace_id)
                        body, content_type = json.dumps(result, ensure_ascii=False).encode(), "application/json; charset=utf-8"
                    else:
                        body, content_type = export_csv(selected), "text/csv; charset=utf-8"
            self.send_bytes(200, body, content_type, trace_id)
        except (ValueError, UnicodeDecodeError) as exc:
            status = 400
            self.send_json(400, {"error": "invalid_input", "message": str(exc), "trace_id": trace_id}, trace_id)
        except Exception as exc:
            status = 500
            evidence.emit(trace_id=trace_id, stage="unhandled", event="error",
                          error_type=type(exc).__name__, traceback=traceback.format_exc())
            self.send_json(500, {"error": "internal_error", "message": "내부 오류입니다. 확인 ID로 로그를 확인하세요.",
                                 "trace_id": trace_id}, trace_id)
        finally:
            evidence.emit(trace_id=trace_id, stage="http", event="metric", route=path,
                          status_code=status, duration_ms=(time.perf_counter()-started)*1000,
                          unit="milliseconds")


def make_server(host, port, log_dir):
    server = ThreadingHTTPServer((host, port), Handler)
    server.evidence = Evidence(log_dir)
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--log-dir", default=".runs/web")
    args = parser.parse_args()
    server = make_server(args.host, args.port, args.log_dir)
    print(json.dumps({"event": "ready", "host": args.host, "port": server.server_port,
                      "run_id": server.evidence.run_id}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
