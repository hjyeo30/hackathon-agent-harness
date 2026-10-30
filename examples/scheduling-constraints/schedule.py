"""Tiny exhaustive scheduling oracle; half-open time intervals [start,end)."""
import itertools
import json
from pathlib import Path
import time


def overlap(a,b):return a[0]<b[1] and b[0]<a[1]


def validate(jobs, schedule, maintenance=None):
    """Independent output checker; does not call the scheduling algorithm."""
    maintenance=maintenance or {};errors=[];by_id={j['id']:j for j in jobs}
    if set(schedule)!=set(by_id):return ['schedule must contain every job exactly once']
    for name,j in by_id.items():
        machine,start,end=schedule[name]
        if machine not in j['machines']:errors.append(name+': machine not allowed')
        if type(start) is not int or type(end) is not int or start<0 or end-start!=j['duration']:errors.append(name+': invalid duration/start')
        if j.get('deadline') is not None and end>j['deadline']:errors.append(name+': deadline exceeded')
        for dep in j.get('after',[]):
            if dep not in schedule or start<schedule[dep][2]:errors.append(name+': precedence violated')
        for window in maintenance.get(machine,[]):
            if overlap((start,end),window):errors.append(name+': maintenance overlap')
    for a,b in itertools.combinations(schedule,2):
        ma,sa,ea=schedule[a];mb,sb,eb=schedule[b]
        if ma==mb and overlap((sa,ea),(sb,eb)):errors.append(a+'/'+b+': machine overlap')
    return errors


def solve(jobs,maintenance=None):
    maintenance=maintenance or {};ids=[j['id'] for j in jobs]
    if len(jobs)>7:raise ValueError('exhaustive teaching oracle limited to 7 jobs')
    if len(set(ids))!=len(ids) or any(type(j['duration']) is not int or j['duration']<=0 or not j['machines'] or any(dep not in ids for dep in j.get('after',[])) for j in jobs):raise ValueError('invalid job contract')
    if any(len(window)!=2 or window[0]<0 or window[1]<=window[0] for windows in maintenance.values() for window in windows):raise ValueError('invalid maintenance interval')
    best=None;best_end=None
    for ordered in itertools.permutations(jobs):
        position={j['id']:i for i,j in enumerate(ordered)}
        if any(position[d]>=position[j['id']] for j in ordered for d in j.get('after',[])):continue
        for machines in itertools.product(*(j['machines'] for j in ordered)):
            current={};available={}
            for j,machine in zip(ordered,machines):
                start=max([available.get(machine,0)]+[current[d][2] for d in j.get('after',[])])
                for lo,hi in sorted(maintenance.get(machine,[])):
                    if overlap((start,start+j['duration']),(lo,hi)):start=hi
                end=start+j['duration'];current[j['id']]=(machine,start,end);available[machine]=end
            if validate(jobs,current,maintenance):continue
            end=max((x[2] for x in current.values()),default=0)
            if best_end is None or end<best_end:best,best_end=current,end
    if best is None:raise ValueError('no feasible schedule')
    return best


def main():
    start=time.perf_counter();spec=json.loads(Path('fixtures/jobs.json').read_text())
    result=solve(spec['jobs'],spec['maintenance']);errors=validate(spec['jobs'],result,spec['maintenance'])
    print(json.dumps({'status':'PASS' if not errors else 'FAIL','schedule':result,'violations':errors,'metrics':{'jobs':len(result),'makespan':max(x[2] for x in result.values()),'duration_ms':(time.perf_counter()-start)*1000},'stage_summary':['validate_input','enumerate_topological_orders_and_machines','place','independent_constraint_check','select_minimum_makespan']}))
    return bool(errors)

if __name__=='__main__':raise SystemExit(main())
