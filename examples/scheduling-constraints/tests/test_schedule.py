import copy
import json
from pathlib import Path
import unittest
from schedule import solve,validate
from faults import overlapping_schedule

class ScheduleTests(unittest.TestCase):
    def setUp(self):self.spec=json.loads(Path('fixtures/jobs.json').read_text());self.jobs=self.spec['jobs'];self.maintenance=self.spec['maintenance']
    def test_tiny_optimum_oracle(self):
        result=solve(self.jobs,self.maintenance)
        self.assertEqual(validate(self.jobs,result,self.maintenance),[])
        # J2 needs 3 units, then J3 needs 1 => lower bound 4; result attains it.
        self.assertEqual(max(x[2] for x in result.values()),4)
        self.assertEqual(result['J2'][0],'B')
    def test_invalid_fast_mutant_rejected(self):
        self.assertTrue(any('machine overlap' in e for e in validate(self.jobs,overlapping_schedule())))
    def test_boundary_touch_is_allowed(self):
        jobs=[{'id':'a','duration':2,'machines':['A']},{'id':'b','duration':1,'machines':['A']}]
        self.assertEqual(validate(jobs,{'a':('A',0,2),'b':('A',2,3)}),[])
    def test_missing_wrong_machine_and_precedence(self):
        result=solve(self.jobs,self.maintenance)
        missing=dict(result);del missing['J1'];self.assertTrue(validate(self.jobs,missing))
        wrong=dict(result);wrong['J3']=('B',0,1)
        errors=validate(self.jobs,wrong)
        self.assertTrue(any('machine not allowed' in e for e in errors));self.assertTrue(any('precedence' in e for e in errors))
    def test_deadline_and_cycle_infeasible(self):
        jobs=copy.deepcopy(self.jobs);jobs[-1]['deadline']=3
        with self.assertRaisesRegex(ValueError,'no feasible'):solve(jobs,self.maintenance)
        jobs=copy.deepcopy(self.jobs);jobs[0]['after']=['J3']
        with self.assertRaisesRegex(ValueError,'no feasible'):solve(jobs)
    def test_maintenance_and_missing_dependency(self):
        jobs=[{'id':'a','duration':3,'machines':['A']}]
        self.assertEqual(solve(jobs,{'A':[[1,2],[3,4]]})['a'],('A',4,7))
        jobs[0]['after']=['unknown']
        with self.assertRaises(ValueError):solve(jobs)
