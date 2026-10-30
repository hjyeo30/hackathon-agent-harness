import unittest
from stream_analysis import aggregate,csv_rows,generated_rows,measured
from faults import mean_of_chunk_means

class SinglePass:
    def __init__(self):self.used=False
    def __iter__(self):
        if self.used:raise AssertionError('input was iterated twice')
        self.used=True
        yield from [('A',0),('A',0),('A',9)]

class StreamTests(unittest.TestCase):
    def test_hand_count_and_negative_values(self):
        r=aggregate(csv_rows('fixtures/groups.csv'),chunk_size=2)
        self.assertEqual(r['rows'],5)
        self.assertEqual(r['groups'],{'A':{'count':3,'sum':9,'min':0,'max':9,'mean':3},'B':{'count':2,'sum':80,'min':-20,'max':100,'mean':40}})
    def test_partition_independence(self):
        expected=aggregate(csv_rows('fixtures/groups.csv'),chunk_size=100)['groups']
        for size in (1,2,3,4,5):self.assertEqual(aggregate(csv_rows('fixtures/groups.csv'),size)['groups'],expected)
    def test_unequal_chunk_mutant_detected(self):self.assertNotEqual(mean_of_chunk_means([0,0,9],2),3)
    def test_single_pass_empty_and_large_integer(self):
        self.assertEqual(aggregate(SinglePass(),2)['groups']['A']['mean'],3)
        self.assertEqual(aggregate([])['groups'],{})
        self.assertEqual(aggregate([('A',2**60),('A',1)])['groups']['A']['sum'],2**60+1)
    def test_cardinality_and_invalid_parameters(self):
        for rows in [[('A',1),('B',2)], [('A',1),('A',2),('B',3)]]:
            with self.assertRaisesRegex(ValueError,'cardinality'):aggregate(rows,chunk_size=2,max_groups=1)
        for size in (0,-1,1.5):
            with self.assertRaises(ValueError):aggregate([],chunk_size=size)
    def test_metrics_trace_budget_and_large_flow(self):
        report=measured(generated_rows(10000),chunk_size=50,max_groups=10)
        self.assertEqual(sum(s['count'] for s in report['result']['groups'].values()),10000)
        self.assertEqual(len(report['trace']),20)
        self.assertEqual(report['metrics']['trace_events_omitted'],180)
        self.assertGreater(report['metrics']['python_peak_bytes'],0)
