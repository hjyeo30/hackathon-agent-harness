import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from pathlib import Path

from server import make_server, parse_csv, select_rows, summarize, export_csv

FIXTURE = Path('fixtures/unequal-batches.csv').read_text()
MULTI = Path('fixtures/multi-equipment.csv').read_text()


class CalculationTests(unittest.TestCase):
    def test_weighted_not_mean_of_percentages(self):
        rows = parse_csv(FIXTURE)
        self.assertEqual(summarize(rows)['yield_rate'], .1)
        faulty = sum(r['good']/r['total'] for r in rows)/len(rows)
        self.assertNotAlmostEqual(faulty, .1)

    def test_inclusive_dates_and_equipment(self):
        rows = select_rows(parse_csv(MULTI), {'equipment':'E1','start':'2026-10-02','end':'2026-10-02'})
        self.assertEqual([r['batch'] for r in rows], ['B'])
        self.assertEqual(summarize(rows)['total'], 90)

    def test_invalid_counts_duplicate_and_dates(self):
        for text in [FIXTURE.replace('9,10','11,10'), FIXTURE.replace('9,10','0,0'),
                     FIXTURE.replace('B,E1','A,E1'), FIXTURE.replace('2026-10-01','2026-02-30'),
                     FIXTURE.replace('9,10','nan,10'), 'batch,equipment,date,good,total\n']:
            with self.subTest(text=text), self.assertRaises(ValueError): parse_csv(text)

    def test_empty_filter_is_not_zero_yield(self):
        result=summarize(select_rows(parse_csv(FIXTURE), {'equipment':'missing'}))
        self.assertIsNone(result['yield_rate'])
        self.assertEqual(result['count'],0)

    def test_invalid_filter_and_safe_export(self):
        with self.assertRaises(ValueError): select_rows(parse_csv(FIXTURE), {'start':'2026-10-03','end':'2026-10-01'})
        rows=parse_csv(FIXTURE.replace('A,E1','=1+1,E1'))
        self.assertIn("'=1+1",export_csv(rows).decode())


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.server=make_server('127.0.0.1',0,cls.tmp.name)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base='http://127.0.0.1:%d'%cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.tmp.cleanup()

    def post(self,path,payload):
        request=urllib.request.Request(self.base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        return urllib.request.urlopen(request,timeout=3)

    def test_real_analyze_export_and_trace(self):
        payload={'csv':MULTI,'filters':{'equipment':'E1','end':'2026-10-01'}}
        with self.post('/api/analyze',payload) as response:
            result=json.load(response);trace=response.headers['X-Trace-Id']
        self.assertEqual(result['yield_rate'],.9)
        with self.post('/api/export',payload) as response: exported=response.read().decode()
        self.assertIn('A,E1,2026-10-01,9,10',exported)
        self.assertNotIn('B,E1',exported);self.assertNotIn('C,E2',exported)
        events=[json.loads(x) for x in Path(self.tmp.name,'events.jsonl').read_text().splitlines()]
        events=[x for x in events if x.get('trace_id')==trace]
        self.assertTrue(any(x['stage']=='filter' and x.get('duration_ms',-1)>=0 for x in events))
        self.assertTrue(any(x.get('output_rows')==1 for x in events))
        self.assertTrue(any(x.get('parent_id') for x in events))
        self.assertNotIn(MULTI,Path(self.tmp.name,'events.jsonl').read_text())

    def test_error_is_400_with_failure_stage(self):
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self.post('/api/analyze',{'csv':FIXTURE.replace('9,10','11,10')})
        error=raised.exception;self.assertEqual(error.code,400)
        result=json.load(error);self.assertEqual(result['error'],'invalid_input')
        events=[json.loads(x) for x in Path(self.tmp.name,'events.jsonl').read_text().splitlines()]
        self.assertTrue(any(x.get('trace_id')==result['trace_id'] and x['stage']=='parse' and x.get('status')=='FAIL' for x in events))

    def test_unexpected_error_is_500_not_success(self):
        with patch('server.summarize', side_effect=RuntimeError('injected internal failure')):
            with self.assertRaises(urllib.error.HTTPError) as raised:
                self.post('/api/analyze', {'csv': FIXTURE})
        self.assertEqual(raised.exception.code, 500)
        result = json.load(raised.exception)
        self.assertEqual(result['error'], 'internal_error')
        self.assertNotIn('injected', result['message'])
        events = [json.loads(x) for x in Path(self.tmp.name, 'events.jsonl').read_text().splitlines()]
        matching = [x for x in events if x.get('trace_id') == result['trace_id']]
        self.assertTrue(any(x.get('stage') == 'aggregate' and x.get('status') == 'FAIL' for x in matching))
        self.assertTrue(any(x.get('stage') == 'unhandled' and 'RuntimeError' in x.get('traceback', '') for x in matching))


if __name__=='__main__':unittest.main()
