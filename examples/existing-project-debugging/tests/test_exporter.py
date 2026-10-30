import csv
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from exporter import export_active
from faults import drops_last_row

class ExportTests(unittest.TestCase):
    def test_regression_last_row_without_newline(self):
        text=Path('fixtures/last-row.csv').read_text();out,m=export_active(text)
        self.assertEqual([r['item'] for r in csv.DictReader(io.StringIO(out))],['last'])
        self.assertEqual(m['output_rows'],1)
        self.assertNotEqual([r['item'] for r in drops_last_row(text)],['last'])
    def test_one_row_and_quoted_multiline(self):
        out,m=export_active('item,status\n"line1\nline2",active')
        self.assertEqual(list(csv.DictReader(io.StringIO(out)))[0]['item'],'line1\nline2')
        self.assertEqual(m['input_rows'],1)
    def test_empty_result_preserves_header(self):
        out,m=export_active('item,status\nx,inactive\n')
        self.assertEqual(list(csv.DictReader(io.StringIO(out))),[]);self.assertEqual(m['output_rows'],0)
        self.assertTrue(out.startswith('item,status'))
    def test_invalid_status_is_not_silently_dropped(self):
        with self.assertRaises(ValueError):export_active('item,status\nx,unknown\n')
    def test_cli_output_and_metrics_are_separate(self):
        p=subprocess.run([sys.executable,'exporter.py','fixtures/last-row.csv'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0);self.assertEqual(json.loads(p.stderr)['output_rows'],1)
        self.assertEqual(list(csv.DictReader(io.StringIO(p.stdout)))[0]['item'],'last')

if __name__=='__main__':unittest.main()
