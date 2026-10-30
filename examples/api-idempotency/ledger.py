"""SQLite idempotency example: one transaction owns request identity and effect."""
import argparse
import hashlib
import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

class Conflict(ValueError):
    pass


def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS requests (
          request_key TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, result_id TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS work_orders (
          id TEXT PRIMARY KEY, equipment TEXT NOT NULL, issue TEXT NOT NULL);
        """)


def submit(path, key, payload, *, fail_before_commit=False, events=None):
    if not isinstance(key,str) or not key.strip(): raise ValueError('request key required')
    if not isinstance(payload,dict) or set(payload)!={'equipment','issue'}:
        raise ValueError('payload must contain equipment and issue')
    if not all(isinstance(v,str) and v.strip() for v in payload.values()):
        raise ValueError('payload values must be nonempty strings')
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    trace_id=uuid.uuid4().hex; started=time.perf_counter(); state='FAIL'; error=None
    db=sqlite3.connect(path,timeout=5,isolation_level=None)
    try:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT payload_hash,result_id FROM requests WHERE request_key=?',(key,)).fetchone()
        if existing:
            if existing[0]!=digest: raise Conflict('same key has different payload')
            db.execute('COMMIT');state='REPLAY'
            return {'id':existing[1],'created':False,'trace_id':trace_id}
        result_id=uuid.uuid4().hex
        db.execute('INSERT INTO work_orders VALUES (?,?,?)',(result_id,payload['equipment'],payload['issue']))
        db.execute('INSERT INTO requests VALUES (?,?,?)',(key,digest,result_id))
        if fail_before_commit: raise RuntimeError('injected failure before commit')
        db.execute('COMMIT');state='CREATED'
        return {'id':result_id,'created':True,'trace_id':trace_id}
    except Exception as exc:
        error=type(exc).__name__
        if db.in_transaction: db.execute('ROLLBACK')
        raise
    finally:
        db.close()
        if events is not None:
            events.append({'timestamp':datetime.now(timezone.utc).isoformat(),'trace_id':trace_id,
                           'request_key_hash':hashlib.sha256(key.encode()).hexdigest()[:16],
                           'span_id':trace_id,'parent_id':None,'stage':'transaction','status':state,
                           'error_type':error,'duration_ms':(time.perf_counter()-started)*1000})


def counts(path):
    with sqlite3.connect(path) as db:
        return {table:db.execute('SELECT count(*) FROM '+table).fetchone()[0]
                for table in ('requests','work_orders')}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--db',default='.runs/orders.sqlite');args=parser.parse_args()
    initialize(args.db);events=[]
    for _ in range(3): print(json.dumps(submit(args.db,'demo-event',{'equipment':'E1','issue':'pressure'},events=events)))
    print(json.dumps({'metric':'durable_rows','value':counts(args.db),'unit':'rows'}))
    Path(args.db).with_suffix('.events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in events))
