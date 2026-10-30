import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class ObservationTests(unittest.TestCase):
    def test_success_and_failure_produce_causal_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            for fault in (None, 'duplicate'):
                directory = Path(temp) / (fault or 'success')
                argv = [sys.executable, 'observe.py', '--output', str(directory)]
                if fault: argv += ['--fault', fault]
                result = subprocess.run(argv, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 1 if fault else 0, result.stderr)
                report = json.loads((directory/'report.json').read_text())
                self.assertEqual(report['status'], 'FAIL' if fault else 'PASS')
                spans = json.loads((directory/'trace.json').read_text())['spans']
                root = next(span for span in spans if span['parent_id'] is None)
                self.assertTrue(any(span['parent_id'] == root['span_id'] for span in spans))
                self.assertTrue(all(span['duration_seconds'] >= 0 for span in spans))
                if fault:
                    failing = [span for span in spans if span['status']=='FAIL']
                    self.assertTrue(any(span['stage']=='validate_dimension_key' for span in failing))
                    self.assertEqual(root['status'], 'FAIL')
