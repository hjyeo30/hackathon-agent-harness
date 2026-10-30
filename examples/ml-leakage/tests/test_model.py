import json
from pathlib import Path
import unittest
from model import fit,evaluate,Model
from faults import fit_with_test_imputation

class ModelTests(unittest.TestCase):
    def setUp(self):self.data=json.loads(Path('fixtures/split.json').read_text())
    def test_independent_fitted_values(self):
        m=fit(self.data['train'])
        self.assertEqual(m.fill,5)
        self.assertAlmostEqual(m.negative_center,7/3)
        self.assertEqual(m.positive_center,9)
        self.assertEqual([m.predict(x) for x in [None,1,9]],[0,0,1])
    def test_leakage_regression_mutant(self):
        a=fit_with_test_imputation(self.data['train'],[(100,1)])
        b=fit_with_test_imputation(self.data['train'],[(-100,0)])
        self.assertNotEqual(a,b)
        # Correct training parameters cannot see either held-out set.
        m=fit(self.data['train']);before=m.__dict__.copy()
        evaluate(m,[(100,1)]);evaluate(m,[(-100,0)])
        self.assertEqual(m.__dict__,before)
    def test_confusion_and_minority_failure_visible(self):
        result=evaluate(Model(0,0,1000),[(0,0)]*9+[(1,1)])
        self.assertEqual(result['accuracy'],0.9)
        self.assertEqual(result['recall'],0)
        self.assertIsNone(result['precision'])
    def test_holdout_and_invalid_input(self):
        self.assertEqual(evaluate(fit(self.data['train']),self.data['test'])['accuracy'],1)
        for rows in [[],[(None,0),(None,1)],[(0,0)],[(float('nan'),0),(1,1)]]:
            with self.subTest(rows=rows),self.assertRaises(ValueError):fit(rows)
        with self.assertRaises(ValueError):evaluate(fit(self.data['train']),[])
    def test_tie_policy(self):self.assertEqual(Model(5,0,10).predict(5),0)
