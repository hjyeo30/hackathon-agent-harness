"""Reject ambiguous dimensional joins before publishing aggregate results."""
import json
from contextlib import nullcontext
import sqlite3
import time


def database():
    connection = sqlite3.connect(':memory:')
    connection.executescript("""
      CREATE TABLE production(batch TEXT PRIMARY KEY, device TEXT NOT NULL, units INTEGER NOT NULL CHECK(units>=0));
      CREATE TABLE devices(device TEXT NOT NULL, label TEXT NOT NULL);
      INSERT INTO production VALUES ('a','M1',40),('b','M1',60),('c','M2',50);
      INSERT INTO devices VALUES ('M1','Etcher'),('M2','Cleaner');
    """)
    return connection


def aggregate(connection, span=None):
    stage = span or (lambda name: nullcontext())
    with stage('validate_dimension_key'):
        duplicates=connection.execute('SELECT device FROM devices GROUP BY device HAVING COUNT(*) > 1').fetchall()
        if duplicates: raise ValueError('dimension key is not unique')
    with stage('validate_orphans'):
        missing=connection.execute('SELECT COUNT(*) FROM production p LEFT JOIN devices d ON p.device=d.device WHERE d.device IS NULL').fetchone()[0]
        if missing: raise ValueError('production has unknown device')
    with stage('join_and_aggregate'):
        rows=connection.execute('SELECT p.device,d.label,SUM(p.units) FROM production p JOIN devices d ON p.device=d.device GROUP BY p.device,d.label ORDER BY p.device').fetchall()
    with stage('reconcile_total'):
        original=connection.execute('SELECT COALESCE(SUM(units),0) FROM production').fetchone()[0]
        if sum(row[2] for row in rows)!=original: raise ValueError('join changed total units')
    return rows

if __name__=='__main__':
    start=time.perf_counter()
    with database() as db:
        result=aggregate(db)
        print(json.dumps({'status':'PASS','result':result,'metrics':{'input_rows':3,'output_groups':len(result),'total_units':sum(r[2] for r in result),'duration_ms':(time.perf_counter()-start)*1000},'stage_summary':['load','validate_dimension_key','check_orphans','join','reconcile_total']}))
