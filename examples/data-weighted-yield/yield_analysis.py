"""Production yield with explicit count and identity contracts; no dependencies."""
import argparse
import csv
from fractions import Fraction
import json
import re
import time


def load_batches(path):
    with open(path, newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['batch', 'good', 'total']:
            raise ValueError('expected columns: batch,good,total')
        rows, seen = [], set()
        for line, row in enumerate(reader, 2):
            identity = row.get('batch', '')
            if not identity or identity in seen:
                raise ValueError('missing or duplicate batch at line %d' % line)
            if None in row or any(not re.fullmatch(r'[0-9]+', row.get(k) or '') for k in ('good', 'total')):
                raise ValueError('integer counts required at line %d' % line)
            seen.add(identity)
            rows.append((int(row['good']), int(row['total'])))
    return rows


def yield_rate(batches):
    if not batches:
        raise ValueError('empty input has no yield')
    for good, total in batches:
        if type(good) is not int or type(total) is not int or total <= 0 or not 0 <= good <= total:
            raise ValueError('require integer 0 <= good <= total and total > 0')
    return Fraction(sum(g for g, _ in batches), sum(t for _, t in batches))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', nargs='?', default='fixtures/batches.csv')
    args = parser.parse_args()
    start = time.perf_counter()
    stage = 'load'
    try:
        batches = load_batches(args.csv)
        stage = 'aggregate'
        rate = yield_rate(batches)
    except (ValueError, OSError) as exc:
        print(json.dumps({'status':'FAIL','stage':stage,'error_type':type(exc).__name__,'error':str(exc)}))
        return 1
    print(json.dumps({'status':'PASS','result':{'yield_fraction':str(rate),'yield_percent':float(rate*100)},
        'metrics':{'rows':len(batches),'good_count':sum(x[0] for x in batches),'total_count':sum(x[1] for x in batches),'duration_ms':(time.perf_counter()-start)*1000},
        'stage_summary':['load_csv','validate_identity_and_counts','sum_counts','divide_once']}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
