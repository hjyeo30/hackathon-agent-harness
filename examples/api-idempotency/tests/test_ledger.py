import concurrent.futures
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from ledger import initialize, submit, counts, Conflict

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name,'db.sqlite'));initialize(self.path)
        self.payload={'equipment':'E1','issue':'pressure'}
    def tearDown(self):self.tmp.cleanup()
    def test_three_retries_and_restart_create_one_effect(self):
        first=submit(self.path,'k',self.payload)
        initialize(self.path) # Reopening does not erase durable state.
        others=[submit(self.path,'k',self.payload) for _ in range(2)]
        self.assertTrue(first['created']);self.assertTrue(all(not x['created'] for x in others))
        self.assertEqual({first['id'],*(x['id'] for x in others)},{first['id']})
        self.assertEqual(counts(self.path),{'requests':1,'work_orders':1})
    def test_same_key_changed_payload_conflicts(self):
        submit(self.path,'k',self.payload)
        with self.assertRaises(Conflict):submit(self.path,'k',dict(self.payload,issue='other'))
        self.assertEqual(counts(self.path)['work_orders'],1)
    def test_failure_rolls_back_both_then_retry_works(self):
        events=[]
        with self.assertRaises(RuntimeError):submit(self.path,'k',self.payload,fail_before_commit=True,events=events)
        self.assertEqual(counts(self.path),{'requests':0,'work_orders':0})
        self.assertEqual(events[0]['status'],'FAIL');self.assertEqual(events[0]['error_type'],'RuntimeError')
        self.assertTrue(submit(self.path,'k',self.payload)['created'])
        self.assertEqual(counts(self.path)['work_orders'],1)
    def test_two_concurrent_retries_have_one_effect(self):
        barrier=threading.Barrier(2)
        def work():barrier.wait();return submit(self.path,'same',self.payload)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:work(),range(2)))
        self.assertEqual(sum(x['created'] for x in results),1)
        self.assertEqual(counts(self.path)['work_orders'],1)
    def test_distinct_keys_are_distinct_work(self):
        for key in ['a','b']:submit(self.path,key,self.payload)
        self.assertEqual(counts(self.path)['work_orders'],2)
    def test_invalid_payload_has_no_effect(self):
        with self.assertRaises(ValueError):submit(self.path,'k',{'equipment':''})
        self.assertEqual(counts(self.path)['requests'],0)

if __name__=='__main__':unittest.main()
