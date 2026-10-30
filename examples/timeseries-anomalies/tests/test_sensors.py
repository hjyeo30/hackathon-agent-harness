import json
from pathlib import Path
import unittest
from sensors import analyze
from faults import zero_fill_spikes

class SensorTests(unittest.TestCase):
    def setUp(self):self.data=json.loads(Path('fixtures/sensors.json').read_text())
    def test_known_event_times(self):
        r=analyze(self.data['readings'],self.data['reference'])
        kinds=[(e['time'],e['kind']) for e in r['events']]
        self.assertEqual(kinds,[(4,'sustained_shift'),(5,'spike'),(6,'missing'),(9,'sustained_shift'),(10,'stuck')])
        self.assertEqual(r['baseline'],10)
    def test_missing_mutant_detected(self):
        self.assertEqual(zero_fill_spikes([(0,None)]),[0])
        self.assertEqual(analyze([(0,None)],[10])['events'],[{'time':0,'kind':'missing'}])
    def test_normal_no_event(self):
        self.assertEqual(analyze(list(enumerate([10,10.1,9.9,10,10.2])),[10])['events'],[])
    def test_spike_boundary_exclusive(self):
        self.assertFalse(any(e['kind']=='spike' for e in analyze([(0,13)],[10])['events']))
        self.assertTrue(any(e['kind']=='spike' for e in analyze([(0,13.01)],[10])['events']))
    def test_gap_breaks_continuity(self):
        r=analyze([(0,10),(1,10),(5,10),(6,10)],[10])
        self.assertEqual([e['kind'] for e in r['events']],['gap'])
    def test_invalid_order_and_nonfinite(self):
        for rows in [[(1,10),(0,10)],[(0,10),(0,11)],[(0,float('nan'))]]:
            with self.subTest(rows=rows),self.assertRaises(ValueError):analyze(rows,[10])
