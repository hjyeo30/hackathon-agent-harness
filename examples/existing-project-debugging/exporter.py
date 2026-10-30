"""CSV export reproducer: preserve the last row, including no trailing newline."""
import argparse
import csv
import io
import json
import sys
import time


def export_active(text):
    reader=csv.DictReader(io.StringIO(text))
    if reader.fieldnames!=['item','status']:raise ValueError('expected item,status columns')
    output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=reader.fieldnames);writer.writeheader()
    read_count=write_count=0
    for row in reader:
        if None in row or any(v is None for v in row.values()):raise ValueError('invalid row width')
        if row['status'] not in ('active','inactive'):raise ValueError('unknown status')
        read_count+=1
        if row['status']=='active':writer.writerow(row);write_count+=1
    return output.getvalue(),{'input_rows':read_count,'output_rows':write_count,'unit':'rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');args=p.parse_args();start=time.perf_counter()
    try:
        with open(args.input,encoding='utf-8',newline='') as source:result,metrics=export_active(source.read())
        sys.stdout.write(result)
        print(json.dumps(dict(metrics,stage='export',status='PASS',duration_ms=(time.perf_counter()-start)*1000)),file=sys.stderr)
    except (ValueError,OSError) as exc:
        print(json.dumps({'stage':'export','status':'FAIL','error_type':type(exc).__name__,'message':str(exc)}),file=sys.stderr)
        sys.exit(2)
