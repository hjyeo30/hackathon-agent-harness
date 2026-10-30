import unittest
from join_analysis import database,aggregate
from faults import unchecked_total

class JoinTests(unittest.TestCase):
    def setUp(self): self.db=database()
    def tearDown(self): self.db.close()
    def test_hand_count(self): self.assertEqual(aggregate(self.db),[('M1','Etcher',100),('M2','Cleaner',50)])
    def test_duplicate_join_regression_and_mutant(self):
        self.db.execute("INSERT INTO devices VALUES ('M1','Etcher')")
        self.assertEqual(unchecked_total(self.db),250)
        with self.assertRaisesRegex(ValueError,'not unique'): aggregate(self.db)
    def test_orphan_not_silently_dropped(self):
        self.db.execute("INSERT INTO production VALUES ('d','UNKNOWN',20)")
        with self.assertRaisesRegex(ValueError,'unknown'): aggregate(self.db)
    def test_zero_and_empty(self):
        self.db.execute('DELETE FROM production')
        self.assertEqual(aggregate(self.db),[])
        self.db.execute("INSERT INTO production VALUES ('zero','M1',0)")
        self.assertEqual(aggregate(self.db),[('M1','Etcher',0)])
    def test_failed_transaction_rolls_back(self):
        self.db.commit()
        try:
            with self.db:
                self.db.execute("INSERT INTO production VALUES ('d','M1',5)")
                self.db.execute("INSERT INTO production VALUES ('a','M1',5)")
        except Exception: pass
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM production WHERE batch='d'").fetchone()[0],0)
