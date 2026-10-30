"""Bounded-cardinality streaming statistics with exact integer sums."""
import argparse
import csv
import itertools
import json
import time
import tracemalloc


def csv_rows(path):
    with open(path,newline='',encoding='utf-8') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=['group','value']:raise ValueError('expected group,value columns')
        for line,row in enumerate(reader,2):
            try:value=int(row['value'])
            except (ValueError,TypeError):raise ValueError('invalid integer at line %d' % line)
            if None in row or not row['group']:raise ValueError('invalid row at line %d' % line)
            yield row['group'],value


def aggregate(rows,chunk_size=1000,max_groups=1000,on_chunk=None):
    if type(chunk_size) is not int or chunk_size<=0 or type(max_groups) is not int or max_groups<=0:raise ValueError('positive integer limits required')
    iterator=iter(rows);total={};chunks=0;count=0
    while True:
        partial={};in_chunk=0
        for group,value in itertools.islice(iterator,chunk_size):
            if not isinstance(group,str) or not group or type(value) is not int:raise ValueError('nonempty group and integer value required')
            if group not in total and group not in partial and len(set(total)|set(partial))>=max_groups:raise ValueError('group cardinality exceeds memory contract')
            state=partial.setdefault(group,{'count':0,'sum':0,'min':value,'max':value})
            state['count']+=1;state['sum']+=value;state['min']=min(state['min'],value);state['max']=max(state['max'],value);in_chunk+=1
        if not in_chunk:break
        for group,p in partial.items():
            state=total.setdefault(group,{'count':0,'sum':0,'min':p['min'],'max':p['max']})
            state['count']+=p['count'];state['sum']+=p['sum'];state['min']=min(state['min'],p['min']);state['max']=max(state['max'],p['max'])
        chunks+=1;count+=in_chunk
        if on_chunk:on_chunk({'stage':'chunk_merged','chunk':chunks,'rows':in_chunk,'rows_total':count,'groups':len(total)})
    return {'groups':{g:dict(s,mean=s['sum']/s['count']) for g,s in sorted(total.items())},'rows':count,'chunks':chunks}


def generated_rows(n):
    for i in range(n):yield 'G%d' % (i%10),i%101


def measured(rows,chunk_size,max_groups):
    trace=[];start=time.perf_counter();tracemalloc.start()
    try:
        def observe(event):
            if len(trace)<20:trace.append(event)
        result=aggregate(rows,chunk_size,max_groups,observe)
        current,peak=tracemalloc.get_traced_memory()
    finally:tracemalloc.stop()
    elapsed=time.perf_counter()-start
    return {'status':'PASS','result':result,'metrics':{'duration_ms':elapsed*1000,'python_peak_bytes':peak,'rows_per_second':result['rows']/elapsed if elapsed else None,'chunk_size':chunk_size,'max_groups':max_groups,'trace_events_omitted':max(0,result['chunks']-len(trace))},'trace':trace}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--csv');p.add_argument('--rows',type=int,default=10000);p.add_argument('--chunk-size',type=int,default=1000);p.add_argument('--max-groups',type=int,default=1000);p.add_argument('--benchmark',action='store_true',help='Measure generated N and 2N; reports measurements without machine-independent pass threshold')
    args=p.parse_args()
    if args.rows<0:p.error('--rows must be nonnegative')
    if args.benchmark and args.csv:p.error('--benchmark uses generated inputs, not --csv')
    try:
        if args.benchmark:
            result={'runs':[dict(input_rows=n,**measured(generated_rows(n),args.chunk_size,args.max_groups)) for n in (args.rows,2*args.rows)],'interpretation':'Python allocations, not process RSS. Compare on same machine; no universal speed threshold.'}
        else:result=measured(csv_rows(args.csv) if args.csv else generated_rows(args.rows),args.chunk_size,args.max_groups)
    except (OSError,ValueError) as exc:
        print(json.dumps({'status':'FAIL','stage':'stream_aggregate','error_type':type(exc).__name__,'error':str(exc)}));return 1
    print(json.dumps(result));return 0

if __name__=='__main__':raise SystemExit(main())
