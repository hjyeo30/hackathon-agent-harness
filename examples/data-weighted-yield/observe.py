"""Run the teaching fixture with real nested spans and an independent oracle."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from harness.evidence import Evidence
from yield_analysis import load_batches, yield_rate
from faults import mean_of_rates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fault', choices=['mean', 'duplicate'])
    parser.add_argument('--output', help='New local evidence directory')
    args = parser.parse_args()
    directory = Path(args.output) if args.output else Path('.harness/observations') / uuid.uuid4().hex
    if directory.exists():
        parser.error('output already exists; use a new directory to avoid mixing runs')
    evidence = Evidence(directory)
    report = {'scenario': 'weighted-yield', 'fault': args.fault, 'expected_fraction': '1/10', 'status': 'FAIL'}
    try:
        with evidence.span('analyze') as root:
            with evidence.span('load_csv', parent_id=root['span_id']):
                filename = 'duplicate.csv' if args.fault == 'duplicate' else 'batches.csv'
                batches = load_batches(Path(__file__).parent / 'fixtures' / filename)
                evidence.event('input.validated', rows=len(batches), fixture=filename)
                evidence.metric('input_rows', len(batches), 'rows')
            with evidence.span('aggregate', parent_id=root['span_id']):
                result = mean_of_rates(batches) if args.fault == 'mean' else yield_rate(batches)
                report['observed_fraction'] = str(result)
                evidence.metric('yield_rate', float(result), 'ratio')
            with evidence.span('compare_oracle', parent_id=root['span_id']):
                if result != Fraction(1, 10):
                    raise AssertionError('expected 1/10 from hand-counted 10 good / 100 total')
                evidence.event('oracle.matched', expected='1/10', observed=str(result))
        report['status'] = 'PASS'
    except (ValueError, OSError, AssertionError) as exc:
        report.update(error_type=type(exc).__name__, error=str(exc))
        evidence.event('analysis.failed', error_type=type(exc).__name__, message=str(exc))
    evidence.finish(report)
    print(json.dumps({'status': report['status'], 'evidence': str(directory), 'report': report}))
    return 0 if report['status'] == 'PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
