"""Capture real SQL stages, including validation failures before JOIN."""
import argparse
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from harness.evidence import Evidence
from join_analysis import database, aggregate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fault', choices=['duplicate'])
    parser.add_argument('--output')
    args=parser.parse_args()
    directory=Path(args.output) if args.output else Path('.harness/observations')/uuid.uuid4().hex
    if directory.exists():parser.error('output already exists; use a new evidence directory')
    evidence=Evidence(directory)
    report={'scenario':'sql-join','fault':args.fault,'expected_total':150,'status':'FAIL'}
    db=None
    try:
        with evidence.span('analyze_sql') as root:
            with evidence.span('load',parent_id=root['span_id']):
                db=database()
                if args.fault:db.execute("INSERT INTO devices VALUES ('M1','Etcher')")
                for table in ('production','devices'):
                    rows=db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
                    evidence.metric('table_rows',rows,'rows',table=table)
                evidence.event('fixture.loaded',duplicate_injected=bool(args.fault))
            result=aggregate(db,span=lambda stage:evidence.span(stage,parent_id=root['span_id']))
            with evidence.span('compare_oracle',parent_id=root['span_id']):
                report['observed_total']=sum(r[2] for r in result)
                if result != [('M1','Etcher',100),('M2','Cleaner',50)]:
                    raise AssertionError('expected M1=100/M2=50 from 40+60+50')
                evidence.metric('units_total',report['observed_total'],'units')
        report['status']='PASS'
    except (ValueError,OSError,AssertionError) as exc:
        report.update(error_type=type(exc).__name__,error=str(exc))
        evidence.event('analysis.failed',error_type=type(exc).__name__,message=str(exc))
    finally:
        if db is not None:db.close()
    evidence.finish(report)
    print(json.dumps({'status':report['status'],'evidence':str(directory),'report':report}))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
