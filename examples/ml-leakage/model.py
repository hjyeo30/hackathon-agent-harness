"""Tiny 1D mean-imputation/nearest-centroid pipeline; synthetic teaching only."""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import time

@dataclass(frozen=True)
class Model:
    fill: float
    negative_center: float
    positive_center: float

    def predict(self, value):
        x=self.fill if value is None else float(value)
        if not math.isfinite(x):raise ValueError('finite feature required')
        # Deterministic tie policy: class zero.
        return int(abs(x-self.positive_center)<abs(x-self.negative_center))


def fit(rows):
    if not rows or {label for _,label in rows}!={0,1}:raise ValueError('both binary classes required in training')
    observed=[float(x) for x,_ in rows if x is not None]
    if not observed or not all(math.isfinite(x) for x in observed):raise ValueError('finite observed training values required')
    fill=sum(observed)/len(observed)
    groups={label:[fill if x is None else float(x) for x,y in rows if y==label] for label in (0,1)}
    return Model(fill,sum(groups[0])/len(groups[0]),sum(groups[1])/len(groups[1]))


def evaluate(model, rows):
    if not rows or any(label not in (0,1) for _,label in rows):raise ValueError('nonempty binary evaluation set required')
    tp=fp=tn=fn=0
    for x,y in rows:
        p=model.predict(x)
        tp += p==1 and y==1; fp += p==1 and y==0
        tn += p==0 and y==0; fn += p==0 and y==1
    return {'tp':tp,'fp':fp,'tn':tn,'fn':fn,'accuracy':(tp+tn)/len(rows),
        'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None}

if __name__=='__main__':
    start=time.perf_counter();data=json.loads(Path('fixtures/split.json').read_text())
    model=fit(data['train']);result=evaluate(model,data['test'])
    print(json.dumps({'status':'PASS','model':model.__dict__,'evaluation':result,'metrics':{'train_rows':len(data['train']),'test_rows':len(data['test']),'duration_ms':(time.perf_counter()-start)*1000},'stage_summary':['load_fixed_split','fit_train_only','freeze_model','evaluate_holdout'],'limitation':'Synthetic mechanism check, not real-world performance evidence'}))
