"""Measure fit/transform/predict/evaluate with a train-only imputation oracle."""
import argparse
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from harness.evidence import Evidence
from model import fit
from faults import fit_with_test_imputation


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fault',choices=['leakage'])
    parser.add_argument('--output')
    args=parser.parse_args()
    directory=Path(args.output) if args.output else Path('.harness/observations')/uuid.uuid4().hex
    if directory.exists():parser.error('output already exists; use a new evidence directory')
    evidence=Evidence(directory)
    report={'scenario':'ml-leakage','fault':args.fault,'expected_train_fill':5,'status':'FAIL','limitation':'Synthetic mechanism evidence only'}
    try:
        with evidence.span('evaluate_pipeline') as root:
            with evidence.span('load_split',parent_id=root['span_id']):
                data=json.loads((Path(__file__).parent/'fixtures/split.json').read_text())
                for split in ('train','test'):evidence.metric('split_rows',len(data[split]),'rows',split=split)
            with evidence.span('fit',parent_id=root['span_id']):
                model=fit_with_test_imputation(data['train'],[(100,1)]) if args.fault else fit(data['train'])
                evidence.event('model.fitted',training_imputation=model.fill,used_evaluation_features=bool(args.fault))
                report['observed_train_fill']=model.fill
            with evidence.span('transform',parent_id=root['span_id']):
                transformed=[model.fill if x is None else x for x,_ in data['test']]
                evidence.metric('imputed_values',sum(x is None for x,_ in data['test']),'values')
            with evidence.span('predict',parent_id=root['span_id']):
                predictions=[model.predict(x) for x in transformed]
            with evidence.span('evaluate',parent_id=root['span_id']):
                labels=[y for _,y in data['test']]
                correct=sum(p==y for p,y in zip(predictions,labels))
                report['predictions']=predictions
                evidence.metric('accuracy',correct/len(labels),'ratio')
            with evidence.span('compare_oracle',parent_id=root['span_id']):
                if model.fill!=5 or predictions!=[0,0,1]:
                    raise AssertionError('training-only oracle: fill5 and held-out predictions [0,0,1]')
        report['status']='PASS'
    except (ValueError,OSError,AssertionError) as exc:
        report.update(error_type=type(exc).__name__,error=str(exc))
        evidence.event('analysis.failed',error_type=type(exc).__name__,message=str(exc))
    evidence.finish(report)
    print(json.dumps({'status':report['status'],'evidence':str(directory),'report':report}))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
