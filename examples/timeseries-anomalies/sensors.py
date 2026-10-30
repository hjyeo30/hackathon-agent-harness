"""Explainable synthetic anomaly candidates, not a diagnosis of equipment failure."""
import json
import math
from pathlib import Path
import statistics
import time


def analyze(readings,reference,spike_delta=3.0,drift_delta=0.5,stuck_run=4):
    if not reference or any(not math.isfinite(v) for v in reference):raise ValueError('finite reference required')
    if spike_delta<=0 or drift_delta<=0 or stuck_run<2:raise ValueError('invalid detector settings')
    baseline=statistics.median(reference);events=[];previous_time=None;last=None;run=0;window=[];drifting=False
    for timestamp,value in readings:
        if type(timestamp) not in (int,float) or not math.isfinite(timestamp) or (previous_time is not None and timestamp<=previous_time):raise ValueError('timestamps must be finite, unique and increasing')
        if previous_time is not None and timestamp-previous_time>1:
            events.append({'time':timestamp,'kind':'gap','missing_steps':timestamp-previous_time-1})
            window=[];run=0;last=None;drifting=False
        previous_time=timestamp
        if value is None:
            events.append({'time':timestamp,'kind':'missing'});window=[];run=0;last=None;drifting=False;continue
        if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('value must be finite or null')
        if abs(value-baseline)>spike_delta:events.append({'time':timestamp,'kind':'spike','deviation':value-baseline})
        run=run+1 if value==last else 1;last=value
        if run==stuck_run:events.append({'time':timestamp,'kind':'stuck','run_length':run})
        window=(window+[value])[-3:]
        shifted=len(window)==3 and (all(x-baseline>=drift_delta for x in window) or all(x-baseline<=-drift_delta for x in window))
        if shifted and not drifting:events.append({'time':timestamp,'kind':'sustained_shift','window_size':3})
        drifting=shifted
    return {'baseline':baseline,'events':events}

if __name__=='__main__':
    start=time.perf_counter();data=json.loads(Path('fixtures/sensors.json').read_text());result=analyze(data['readings'],data['reference'])
    print(json.dumps({'status':'PASS','result':result,'metrics':{'readings':len(data['readings']),'events':len(result['events']),'duration_ms':(time.perf_counter()-start)*1000},'stage_summary':['validate_time_order','load_prior_reference','detect_missing_gaps','evaluate_candidates'],'limitation':'Candidate events; no causal or real-world accuracy claim'}))
