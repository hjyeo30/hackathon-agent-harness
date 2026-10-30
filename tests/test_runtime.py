"""Behavior tests: false-green prevention, causal evidence and bounded execution."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from harness.cli import check_final, doctor_main, verify_main
from harness.evidence import Evidence, Redactor, fingerprint
from harness.runner import ManifestError, MAX_LOG_BYTES, exit_code, load_manifest, verify


def command(identifier="one", code="print('verified')", required=True, **extra):
    return {"id": identifier, "requirement": "R-test", "kind": "integration",
            "argv": ["python3", "-c", code], "cwd": ".", "timeout_seconds": 5,
            "required": required, "reason": "Reproduce a real runner failure boundary",
            "oracle": "Explicit process output and exit state", **extra}


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manifest = self.root / "verification.json"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, checks):
        self.manifest.write_text(json.dumps({"schema_version": 1, "checks": checks}), encoding="utf-8")

    def run_checks(self, checks, **kwargs):
        self.write(checks)
        return verify(self.manifest, **kwargs)

    def test_success_has_logs_metrics_and_parented_spans(self):
        report = self.run_checks([command()])
        self.assertEqual(report["status"], "PASS")
        path = Path(report["evidence_dir"])
        self.assertIn("verified", (path / "one.stdout.log").read_text())
        trace = json.loads((path / "trace.json").read_text())
        parent = next(s for s in trace["spans"] if s["stage"] == "verification")
        child = next(s for s in trace["spans"] if s["stage"] == "check")
        self.assertEqual(child["parent_id"], parent["span_id"])
        metrics = json.loads((path / "metrics.json").read_text())["metrics"]
        self.assertTrue(any(m["name"] == "check.duration" and m["unit"] == "seconds" for m in metrics))
        self.assertEqual(check_final(self.manifest, path / "report.json")["status"], "PASS")

    @unittest.skipUnless(os.name == "posix", "Executable permission semantics are POSIX-specific")
    def test_executable_permission_change_invalidates_prior_pass(self):
        executable = self.root / "run.sh"
        executable.write_text("#!/bin/sh\nexit 0\n")
        executable.chmod(0o755)
        report = self.run_checks([command(argv=["./run.sh"])])
        self.assertEqual(report["status"], "PASS")
        executable.chmod(0o644)
        self.assertEqual(check_final(self.manifest, Path(report["evidence_dir"]) / "report.json")["status"], "BLOCKED")
        rerun = verify(self.manifest)
        self.assertEqual(rerun["status"], "BLOCKED")
        self.assertEqual(rerun["checks"][0]["error_type"], "PermissionError")

    def test_corrupt_evidence_cannot_claim_final_pass(self):
        report = self.run_checks([command()])
        directory = Path(report["evidence_dir"])
        for name in ("trace.json", "metrics.json", "events.jsonl"):
            with self.subTest(name=name):
                path = directory / name
                original = path.read_text()
                path.write_text("not json")
                result = check_final(self.manifest, directory / "report.json")
                self.assertEqual(result["status"], "BLOCKED")
                self.assertTrue(any(name in p for p in result["problems"]))
                path.write_text(original)

    def test_evidence_from_other_run_or_empty_entries_blocks_final(self):
        report = self.run_checks([command()])
        directory = Path(report["evidence_dir"])
        for name, key in (("trace.json", "spans"), ("metrics.json", "metrics")):
            path = directory / name
            original = path.read_text()
            data = json.loads(original)
            with self.subTest(name=name, issue="identity"):
                data["run_id"] = "another-run"
                path.write_text(json.dumps(data))
                self.assertEqual(check_final(self.manifest, directory / "report.json")["status"], "BLOCKED")
            with self.subTest(name=name, issue="empty"):
                data["run_id"], data[key] = report["run_id"], []
                path.write_text(json.dumps(data))
                self.assertEqual(check_final(self.manifest, directory / "report.json")["status"], "BLOCKED")
            path.write_text(original)
        events = directory / "events.jsonl"
        events.write_text(json.dumps({"run_id": "another-run", "event": "span.finished", "timestamp": "now"}) + "\n")
        self.assertEqual(check_final(self.manifest, directory / "report.json")["status"], "BLOCKED")

    def test_nonzero_exit_is_failed_with_error_evidence(self):
        report = self.run_checks([command(code="import sys; print('bad row', file=sys.stderr); sys.exit(7)")])
        self.assertEqual(exit_code(report), 1)
        self.assertEqual(report["checks"][0]["returncode"], 7)
        self.assertIn("bad row", (Path(report["evidence_dir"]) / "one.stderr.log").read_text())

    def test_missing_executable_is_blocked(self):
        report = self.run_checks([command(argv=["a-command-that-does-not-exist-harness-test"])])
        self.assertEqual(exit_code(report), 2)
        self.assertEqual(report["checks"][0]["error_type"], "FileNotFoundError")

    def test_missing_cwd_is_blocked(self):
        report = self.run_checks([command(cwd="missing")])
        self.assertEqual(report["status"], "BLOCKED")

    def test_timeout_is_not_success(self):
        report = self.run_checks([command(code="import time; time.sleep(10)", timeout_seconds=0.1)])
        self.assertEqual(report["checks"][0]["error_type"], "TimeoutExpired")
        self.assertLess(report["checks"][0]["duration_seconds"], 3)

    @unittest.skipUnless(os.name == "posix", "Process groups are POSIX-specific")
    def test_timeout_stops_child_process_group(self):
        marker = self.root / ".harness" / "escaped.txt"
        child = "import time; from pathlib import Path; time.sleep(0.7); Path(%r).write_text('escaped')" % str(marker)
        code = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',%r]); time.sleep(10)" % child
        report = self.run_checks([command(code=code, timeout_seconds=0.1)])
        self.assertEqual(report["status"], "BLOCKED")
        time.sleep(0.8)
        self.assertFalse(marker.exists())

    def test_unittest_zero_discovery_is_blocked(self):
        (self.root / "empty").mkdir()
        report = self.run_checks([command(argv=["python3", "-m", "unittest", "discover", "-s", "empty"])])
        self.assertEqual(report["checks"][0]["error_type"], "NoTestsCollected")

    def test_skipped_unittest_does_not_prove_required_behavior(self):
        tests = self.root / "tests"
        tests.mkdir()
        (tests / "test_skip.py").write_text("import unittest\nclass T(unittest.TestCase):\n @unittest.skip('missing browser')\n def test_flow(self): pass\n")
        report = self.run_checks([command(argv=["python3", "-m", "unittest", "discover", "-s", "tests"])])
        self.assertEqual(report["checks"][0]["error_type"], "TestsSkipped")

    def test_playwright_console_summary_must_show_executed_tests(self):
        for summary, expected in (("3 skipped", "TestsSkipped"), ("Running 0 tests", "NoTestsCollected"),
                                  ("3 passed (1.4s)", None)):
            report = self.run_checks([command(code="print(%r)" % summary, test_framework="playwright", min_tests=1)])
            self.assertEqual(report["checks"][0]["error_type"], expected)
            self.assertEqual(report["status"], "PASS" if expected is None else "BLOCKED")

    def test_explicit_minimum_prevents_incomplete_suite_claim(self):
        report = self.run_checks([command(code="print('1 passed (0.1s)')", test_framework="playwright", min_tests=2)])
        self.assertEqual(report["status"], "BLOCKED")

    def test_empty_manifest_and_empty_selection_rejected(self):
        self.write([])
        with self.assertRaises(ManifestError):
            verify(self.manifest)
        self.write([command()])
        with self.assertRaises(ManifestError):
            verify(self.manifest, profile="browser")
        with self.assertRaises(ManifestError):
            verify(self.manifest, check_ids=["typo"])

    def test_path_escape_and_duplicate_id_rejected(self):
        for checks in ([command(cwd="../")], [command(), command()], [command(id="../../escape")]):
            self.write(checks)
            with self.assertRaises(ManifestError):
                load_manifest(self.manifest)

    def test_bad_schema_types_rejected(self):
        for extra in ({"required": "yes"}, {"timeout_seconds": -1}, {"timeout_seconds": float("nan")},
                      {"argv": "echo hi"}, {"reason": ""}):
            self.write([command(**extra)])
            with self.assertRaises(ManifestError):
                load_manifest(self.manifest)

    def test_argv_is_literal_not_shell_evaluated(self):
        payload = "$(touch INJECTED); `touch INJECTED2`"
        report = self.run_checks([command(argv=["python3", "-c", "import sys; print(sys.argv[1])", payload])])
        self.assertEqual(report["status"], "PASS")
        self.assertFalse((self.root / "INJECTED").exists())
        self.assertFalse((self.root / "INJECTED2").exists())
        self.assertIn(payload, (Path(report["evidence_dir"]) / "one.stdout.log").read_text())

    def test_omitted_required_profile_blocks_final_all_scope(self):
        report = self.run_checks([command(), command("browser", profile="browser")], profile="core")
        path = Path(report["evidence_dir"]) / "report.json"
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(next(c for c in report["checks"] if c["id"] == "browser")["status"], "NOT RUN")
        self.assertEqual(check_final(self.manifest, path)["status"], "BLOCKED")
        self.assertEqual(check_final(self.manifest, path, profile="core")["status"], "PASS")

    def test_new_untracked_source_invalidates_old_evidence(self):
        report = self.run_checks([command()])
        (self.root / "new_feature.py").write_text("changed = True\n")
        result = check_final(self.manifest, Path(report["evidence_dir"]) / "report.json")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("Source/fixtures" in p for p in result["problems"]))

    def test_source_change_during_check_blocks_pass(self):
        report = self.run_checks([command(code="from pathlib import Path; Path('mutated.py').write_text('x=1')")])
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["error_type"], "SourceChangedDuringRun")

    def test_runtime_evidence_does_not_invalidate_fingerprint(self):
        report = self.run_checks([command()])
        before = fingerprint(self.root)
        (self.root / ".harness" / "notes.txt").write_text("new runtime note")
        self.assertEqual(before, fingerprint(self.root))
        self.assertEqual(check_final(self.manifest, Path(report["evidence_dir"]) / "report.json")["status"], "PASS")

    def test_missing_log_and_missing_delivery_file_block_final(self):
        report = self.run_checks([command()])
        directory = Path(report["evidence_dir"])
        (directory / "one.stdout.log").unlink()
        result = check_final(self.manifest, directory / "report.json", ["answer.csv"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("stdout" in p for p in result["problems"]))
        self.assertTrue(any("answer.csv" in p for p in result["problems"]))

    def test_missing_trace_blocks_final_bundle_claim(self):
        report = self.run_checks([command()])
        directory = Path(report["evidence_dir"])
        (directory / "trace.json").unlink()
        result = check_final(self.manifest, directory / "report.json")
        self.assertTrue(any("trace.json" in p for p in result["problems"]))

    def test_malformed_report_is_rejected(self):
        self.write([command()])
        path = self.root / ".harness/report.json"
        path.parent.mkdir()
        path.write_text("[]")
        with self.assertRaises(ManifestError):
            check_final(self.manifest, path)

    def test_bounded_output_is_explicit(self):
        report = self.run_checks([command(code="print('x' * %d)" % (MAX_LOG_BYTES + 10000))])
        result = report["checks"][0]
        self.assertTrue(result["output"]["stdout"]["truncated"])
        self.assertLess((Path(report["evidence_dir"]) / "one.stdout.log").stat().st_size, MAX_LOG_BYTES + 100)

    def test_known_secret_is_redacted(self):
        value = "unique-sensitive-value-12345"
        old = os.environ.get("HARNESS_TEST_TOKEN")
        os.environ["HARNESS_TEST_TOKEN"] = value
        try:
            report = self.run_checks([command(code="import os; print(os.environ['HARNESS_TEST_TOKEN'])")])
            for path in Path(report["evidence_dir"]).iterdir():
                self.assertNotIn(value, path.read_text())
        finally:
            if old is None:
                os.environ.pop("HARNESS_TEST_TOKEN", None)
            else:
                os.environ["HARNESS_TEST_TOKEN"] = old

    def test_redaction_keeps_json_well_formed(self):
        evidence = Evidence(self.root / ".harness/redaction")
        evidence.event("example", detail='token=secret-value "quoted"')
        evidence.finish({"detail": "password=sensitive"})
        report = json.loads((evidence.directory / "report.json").read_text())
        self.assertEqual(report["detail"], "password=[REDACTED]")
        line = json.loads((evidence.directory / "events.jsonl").read_text())
        self.assertIn("[REDACTED]", line["detail"])

    def test_application_span_records_actual_failure_and_preserves_runs(self):
        evidence = Evidence(self.root / ".harness/analysis")
        with self.assertRaises(ValueError):
            with evidence.span("parse-input"):
                raise ValueError("missing total column")
        evidence.finish({"status": "FAIL"})
        trace = json.loads((evidence.directory / "trace.json").read_text())["spans"][0]
        self.assertEqual(trace["error_type"], "ValueError")
        self.assertIn("missing total column", trace["exception_traceback"])
        self.assertIn("test_runtime.py", trace["exception_traceback"])
        with self.assertRaises(FileExistsError):
            Evidence(evidence.directory)

    def test_doctor_does_not_execute_the_check(self):
        self.write([command(code="from pathlib import Path; Path('UNEXPECTED').write_text('bad')")])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = doctor_main(["--manifest", str(self.manifest), "--json"])
        self.assertEqual(code, 0)
        self.assertFalse((self.root / "UNEXPECTED").exists())
        self.assertFalse(json.loads(output.getvalue())["checks"][0]["executed"])

    def test_invalid_cli_returns_blocked(self):
        self.write([])
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(verify_main(["--manifest", str(self.manifest)]), 2)


if __name__ == "__main__":
    unittest.main()
