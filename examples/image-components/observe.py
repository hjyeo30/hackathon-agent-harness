"""Inspect PGM pixels with measured spans, independent count, and SVG evidence."""
import argparse
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from harness.evidence import Evidence
from image_analysis import read_pgm, components, write_overlay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fault', choices=['diagonal'])
    parser.add_argument('--output', help='New local evidence directory')
    args = parser.parse_args()
    directory = Path(args.output) if args.output else Path('.harness/observations') / uuid.uuid4().hex
    if directory.exists():
        parser.error('output already exists; use a new directory to avoid mixing runs')
    evidence = Evidence(directory)
    report = {'scenario': 'image-components', 'fault': args.fault, 'expected_regions': 3, 'status': 'FAIL'}
    try:
        with evidence.span('analyze_image') as root:
            with evidence.span('decode', parent_id=root['span_id']):
                pixels = read_pgm(Path(__file__).parent / 'fixtures' / 'diagonal-edge.pgm')
                evidence.metric('width', len(pixels[0]), 'pixels')
                evidence.metric('height', len(pixels), 'pixels')
            with evidence.span('threshold', parent_id=root['span_id']):
                binary = [[255 if value >= 128 else 0 for value in row] for row in pixels]
            with evidence.span('label_components', parent_id=root['span_id']):
                connectivity = 8 if args.fault else 4
                regions = components(binary, connectivity=connectivity)
                evidence.event('components.labeled', connectivity=connectivity, regions=len(regions))
                evidence.metric('foreground', sum(r['area'] for r in regions), 'pixels')
                evidence.metric('regions', len(regions), 'regions')
                report['observed_regions'] = len(regions)
            with evidence.span('render_overlay', parent_id=root['span_id']):
                write_overlay(directory / 'overlay.svg', pixels, regions)
                report['overlay'] = 'overlay.svg'
            with evidence.span('compare_oracle', parent_id=root['span_id']):
                expected = [{'area':1,'bbox':[1,0,1,0]}, {'area':2,'bbox':[4,0,4,1]}, {'area':1,'bbox':[0,1,0,1]}]
                if regions != expected:
                    raise AssertionError('expected three 4-connected regions at hand-labeled coordinates')
        report['status'] = 'PASS'
    except (ValueError, OSError, AssertionError) as exc:
        report.update(error_type=type(exc).__name__, error=str(exc))
        evidence.event('analysis.failed', error_type=type(exc).__name__, message=str(exc))
    evidence.finish(report)
    print(json.dumps({'status': report['status'], 'evidence': str(directory), 'report': report}))
    return 0 if report['status'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
