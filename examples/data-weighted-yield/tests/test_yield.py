from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from yield_analysis import load_batches, yield_rate
from faults import mean_of_rates

class YieldTests(unittest.TestCase):
    def test_independent_hand_count_oracle(self):
        self.assertEqual(yield_rate(load_batches('fixtures/batches.csv')), Fraction(1, 10))
    def test_unweighted_mutant_is_detected(self):
        self.assertNotEqual(mean_of_rates([(9,10),(1,90)]), Fraction(1,10))
    def test_order_independent(self):
        self.assertEqual(yield_rate([(1,90),(9,10)]), Fraction(1,10))
    def test_partition_additivity(self):
        self.assertEqual(yield_rate([(9,10),(1,45),(0,45)]), Fraction(1,10))
    def test_count_boundaries(self):
        self.assertEqual(yield_rate([(0,10)]), 0)
        self.assertEqual(yield_rate([(10,10)]), 1)
    def test_reject_undefined_and_impossible(self):
        for rows in [[], [(0,0)], [(11,10)], [(-1,10)], [(1,-2)], [(1.0,2)], [(True,2)]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError): yield_rate(rows)
    def test_duplicate_identity_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'): load_batches('fixtures/duplicate.csv')
    def test_csv_schema_and_noninteger(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.csv'
            for text in ['batch,good,total\nA,1.5,2\n','batch,good,total\nA,,2\n','good,total\n1,2\n']:
                p.write_text(text)
                with self.assertRaises(ValueError): load_batches(p)
