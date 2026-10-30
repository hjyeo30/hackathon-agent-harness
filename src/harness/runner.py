"""Manifest-driven command runner; a green process alone is not a full oracle."""
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

from .evidence import Evidence, fingerprint, utc_now

MAX_LOG_BYTES = 2 * 1024 * 1024
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class ManifestError(ValueError):
    pass


def within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def load_manifest(path):
    path = Path(path).resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ManifestError("Cannot read manifest: %s" % exc) from exc
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data.get("schema_version") != 1:
        raise ManifestError("schema_version must be 1")
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ManifestError("Manifest must contain at least one check")
    ids = set()
    for check in checks:
        if not isinstance(check, dict):
            raise ManifestError("Each check must be an object")
        identifier = check.get("id", "")
        if not isinstance(identifier, str) or not ID_PATTERN.fullmatch(identifier) or identifier in ids:
            raise ManifestError("Check id must be unique and a safe filename: %r" % identifier)
        ids.add(identifier)
        for field in ("requirement", "kind", "reason", "oracle"):
            if not isinstance(check.get(field), str) or not check[field].strip():
                raise ManifestError("%s: nonempty %s is required" % (identifier, field))
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(v, str) and v and "\0" not in v for v in argv):
            raise ManifestError("%s: argv must be a nonempty string array" % identifier)
        if not isinstance(check.get("required"), bool):
            raise ManifestError("%s: required must be a boolean" % identifier)
        timeout = check.get("timeout_seconds")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ManifestError("%s: timeout_seconds must be finite and positive" % identifier)
        cwd = check.get("cwd", ".")
        if not isinstance(cwd, str) or Path(cwd).is_absolute():
            raise ManifestError("%s: cwd must be manifest-relative" % identifier)
        if not within((path.parent / cwd).resolve(), path.parent):
            raise ManifestError("%s: cwd escapes manifest directory" % identifier)
        if "profile" in check and (not isinstance(check["profile"], str) or not check["profile"]):
            raise ManifestError("%s: profile must be a nonempty string" % identifier)
        if "test_framework" in check and check["test_framework"] not in ("unittest", "pytest", "playwright"):
            raise ManifestError("%s: test_framework must be unittest, pytest, or playwright" % identifier)
        if "min_tests" in check and (type(check["min_tests"]) is not int or check["min_tests"] < 1):
            raise ManifestError("%s: min_tests must be a positive integer" % identifier)
        if "min_tests" in check and "test_framework" not in check:
            raise ManifestError("%s: explicit min_tests requires test_framework" % identifier)
    return data


def resolve_argv(argv):
    result = list(argv)
    if result[0] in ("python", "python3"):
        result[0] = sys.executable
    return result


def _stop_group(process):
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            pass
        # Children may outlive a parent that has already exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        process.kill()


def run_check(check, root, evidence, parent_id):
    identifier = check["id"]
    argv = resolve_argv(check["argv"])
    cwd = (root / check.get("cwd", ".")).resolve()
    result = {"id": identifier, "requirement": check["requirement"], "kind": check["kind"],
              "required": check["required"], "profile": check.get("profile", "core"),
              "argv": argv, "cwd": check.get("cwd", "."), "reason": check["reason"],
              "oracle": check["oracle"], "status": "BLOCKED", "returncode": None,
              "error_type": None, "stdout": identifier + ".stdout.log",
              "stderr": identifier + ".stderr.log", "test_count": None,
              "trace_scope": "command; application-internal spans require application instrumentation"}
    with evidence.span("check", parent_id, check_id=identifier) as span:
        start = time.monotonic()
        stats = {"stdout": {"bytes": 0, "truncated": False, "tail": ""},
                 "stderr": {"bytes": 0, "truncated": False, "tail": ""}}

        def pump(stream, name):
            written = 0
            with (evidence.directory / result[name]).open("w", encoding="utf-8") as output:
                while True:
                    chunk = stream.readline(65536)
                    if not chunk:
                        break
                    stats[name]["bytes"] += len(chunk)
                    text = evidence.redact(chunk.decode("utf-8", errors="replace"))
                    stats[name]["tail"] = (stats[name]["tail"] + text)[-131072:]
                    encoded = text.encode("utf-8")
                    remaining = max(0, MAX_LOG_BYTES - written)
                    if remaining:
                        part = encoded[:remaining].decode("utf-8", errors="ignore")
                        output.write(part)
                        written += len(part.encode("utf-8"))
                    if len(encoded) > remaining:
                        stats[name]["truncated"] = True
                if stats[name]["truncated"]:
                    output.write("\n[HARNESS: output truncated at %d bytes]\n" % MAX_LOG_BYTES)
            stream.close()

        process = None
        threads = []
        try:
            if not cwd.is_dir():
                raise FileNotFoundError("Check cwd does not exist: %s" % check.get("cwd", "."))
            process = subprocess.Popen(argv, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       stdin=subprocess.DEVNULL, start_new_session=(os.name == "posix"))
            for stream, name in ((process.stdout, "stdout"), (process.stderr, "stderr")):
                thread = threading.Thread(target=pump, args=(stream, name), daemon=True)
                thread.start()
                threads.append(thread)
            try:
                result["returncode"] = process.wait(timeout=check["timeout_seconds"])
                result["status"] = "PASS" if result["returncode"] == 0 else "FAIL"
                if result["returncode"] != 0:
                    result["error_type"] = "CommandFailed"
            except subprocess.TimeoutExpired:
                result.update(status="BLOCKED", error_type="TimeoutExpired")
            finally:
                _stop_group(process)
                process.wait(timeout=2)
                for thread in threads:
                    thread.join(timeout=3)
                if any(thread.is_alive() for thread in threads):
                    result.update(status="BLOCKED", error_type="OutputCaptureIncomplete")
        except (OSError, subprocess.SubprocessError) as exc:
            result.update(status="BLOCKED", error_type=type(exc).__name__, detail=str(exc))
            for name in ("stdout", "stderr"):
                log = evidence.directory / result[name]
                if not log.exists():
                    log.write_text(evidence.redact(str(exc)) if name == "stderr" else "", encoding="utf-8")
        except BaseException:
            if process:
                _stop_group(process)
            raise
        combined = stats["stdout"]["tail"] + "\n" + stats["stderr"]["tail"]
        combined = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", combined)
        framework = check.get("test_framework")
        if not framework and "unittest" in argv:
            framework = "unittest"
        if not framework and any("pytest" in part for part in argv[:3]):
            framework = "pytest"
        minimum = check.get("min_tests", 1)
        if framework == "unittest":
            found = re.findall(r"Ran\s+(\d+)\s+tests?\b", combined)
            result["test_count"] = int(found[-1]) if found else None
            if result["status"] == "PASS" and (not found or result["test_count"] < minimum):
                result.update(status="BLOCKED", error_type="NoTestsCollected")
            if result["status"] == "PASS" and re.search(r"OK\s*\([^)]*skipped=", combined):
                result.update(status="BLOCKED", error_type="TestsSkipped")
        elif framework in ("pytest", "playwright"):
            # These integrations require the framework's English console summary.
            # A wrapper that suppresses it is inconclusive, never a silent PASS.
            passed = re.findall(r"\b(\d+) passed\b", combined)
            skipped = re.findall(r"\b(\d+) (?:skipped|xfailed|did not run)\b", combined)
            result["test_count"] = int(passed[-1]) if passed else 0
            if result["status"] == "PASS" and result["test_count"] < minimum:
                result.update(status="BLOCKED", error_type="NoTestsCollected")
            if result["returncode"] == 0 and any(int(n) > 0 for n in skipped):
                result.update(status="BLOCKED", error_type="TestsSkipped")
        result["duration_seconds"] = round(time.monotonic() - start, 6)
        result["output"] = {name: {k: v for k, v in stat.items() if k != "tail"}
                            for name, stat in stats.items()}
        evidence.metric("check.duration", result["duration_seconds"], "seconds", check_id=identifier)
        for name, stat in stats.items():
            evidence.metric("check.output", stat["bytes"], "bytes", check_id=identifier, stream=name)
        span.update(status=result["status"], error_type=result["error_type"])
        evidence.event("check.result", **result)
    return result


def verify(manifest, output_dir=None, check_ids=None, profile=None):
    manifest = Path(manifest).resolve()
    root = manifest.parent
    data = load_manifest(manifest)
    ids = set(check_ids or [])
    unknown = ids - {check["id"] for check in data["checks"]}
    if unknown:
        raise ManifestError("Unknown check ids: %s" % ", ".join(sorted(unknown)))
    selected = [check for check in data["checks"]
                if (not ids or check["id"] in ids)
                and (profile is None or check.get("profile", "core") == profile)]
    if not selected:
        raise ManifestError("Selection contains no checks")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = stamp + "-" + uuid.uuid4().hex[:8]
    base = Path(output_dir).resolve() if output_dir else root / ".harness" / "runs"
    # In-project evidence must stay in the ignored runtime area to avoid hashing itself.
    if within(base, root) and not within(base, root / ".harness"):
        raise ManifestError("In-project output-dir must be under .harness; external paths are also supported")
    evidence = Evidence(base / run_id, run_id)
    before = fingerprint(root)
    report = {"schema_version": 1, "run_id": run_id, "started_at": utc_now(),
              "manifest": manifest.name,
              "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
              "source_before": before, "selected_checks": [c["id"] for c in selected],
              "selection": {"check_ids": sorted(ids), "profile": profile},
              "evidence_dir": str(evidence.directory), "checks": [],
              "scope_note": "PASS covers selected checks only; not omitted profiles or human confirmation."}
    try:
        with evidence.span("verification") as root_span:
            selected_ids = {check["id"] for check in selected}
            for check in data["checks"]:
                if check["id"] not in selected_ids:
                    report["checks"].append({"id": check["id"], "required": check["required"],
                                             "profile": check.get("profile", "core"),
                                             "status": "NOT RUN", "reason": "Outside explicit selection"})
            for check in selected:
                report["checks"].append(run_check(check, root, evidence, root_span["span_id"]))
            required = [r for r in report["checks"] if r["id"] in selected_ids and r["required"]]
            observed = [r for r in report["checks"] if r["id"] in selected_ids]
            if any(r["status"] == "FAIL" for r in required):
                status = "FAIL"
            elif any(r["status"] != "PASS" for r in required):
                status = "BLOCKED"
            elif not any(r["status"] == "PASS" for r in observed):
                status = "BLOCKED"
            else:
                status = "PASS"
            report["source_after"] = fingerprint(root)
            report["source_changed_during_run"] = before != report["source_after"]
            if report["source_changed_during_run"] and status == "PASS":
                status = "BLOCKED"
                report["error_type"] = "SourceChangedDuringRun"
            report["status"] = status
            root_span["status"] = status
    except KeyboardInterrupt:
        report.update(status="BLOCKED", error_type="Interrupted")
        raise
    finally:
        report["finished_at"] = utc_now()
        for status in ("PASS", "FAIL", "BLOCKED", "NOT RUN"):
            evidence.metric("checks.count", sum(c["status"] == status for c in report["checks"]),
                            "checks", status=status)
        evidence.finish(report)
    return report


def exit_code(report):
    return {"PASS": 0, "FAIL": 1}.get(report.get("status"), 2)


def print_report(report):
    for check in report["checks"]:
        suffix = " — " + check["error_type"] if check.get("error_type") else ""
        print("%s %s%s" % (check["status"], check["id"], suffix))
    print("Overall: %s (selected scope only)" % report["status"])
    print("Evidence: %s" % report["evidence_dir"])
