"""Command-line entrypoints; all operations stay local."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys

from .bootstrap import InstallError, install
from .evidence import fingerprint
from .runner import ManifestError, exit_code, load_manifest, print_report, resolve_argv, verify, within


def verify_main(argv=None):
    parser = argparse.ArgumentParser(description="Run real checks and save local logs, metrics and command spans. Exit: 0 selected required checks pass, 1 fail, 2 blocked.")
    parser.add_argument("--manifest", default="verification.json")
    parser.add_argument("--check", action="append", help="Run one check id; repeat for multiple ids. Omitted checks remain NOT RUN.")
    parser.add_argument("--profile", help="Explicit profile, e.g. core or browser. No implicit browser success.")
    parser.add_argument("--output-dir", help="Run parent directory; inside project must be under .harness.")
    args = parser.parse_args(argv)
    try:
        report = verify(args.manifest, args.output_dir, args.check, args.profile)
        print_report(report)
        return exit_code(report)
    except ManifestError as exc:
        print("BLOCKED: %s" % exc, file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("BLOCKED: interrupted; partial evidence preserved", file=sys.stderr)
        return 2


def doctor_main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only prerequisite inspection. Executable presence is not proof of app/browser operation.")
    parser.add_argument("--manifest")
    parser.add_argument("--profile")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = {"python": platform.python_version(), "platform": platform.system(),
              "python_supported": sys.version_info >= (3, 9), "checks": [],
              "probe_scope": "read-only file and executable presence; commands, app and browser not run",
              "codex": shutil.which("codex"), "node": shutil.which("node")}
    try:
        if args.manifest:
            manifest = Path(args.manifest).resolve()
            data = load_manifest(manifest)
            checks = [c for c in data["checks"] if args.profile is None or c.get("profile", "core") == args.profile]
            if not checks:
                raise ManifestError("Profile contains no checks")
            for check in checks:
                cwd = (manifest.parent / check.get("cwd", ".")).resolve()
                binary = resolve_argv(check["argv"])[0]
                executable = str((cwd / binary).resolve()) if "/" in binary else shutil.which(binary)
                exists = bool(executable and os.path.isfile(executable) and os.access(executable, os.X_OK))
                report["checks"].append({"id": check["id"], "cwd_exists": cwd.is_dir(),
                                          "executable_exists": exists, "executable": executable,
                                          "required": check["required"], "executed": False})
        report["status"] = "READY TO TRY" if report["python_supported"] and all(
            c["cwd_exists"] and c["executable_exists"] for c in report["checks"] if c["required"]) else "BLOCKED"
    except ManifestError as exc:
        report.update(status="BLOCKED", error=str(exc))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("%s — Python %s, %s" % (report["status"], report["python"], report["platform"]))
        print(report["probe_scope"])
        for check in report["checks"]:
            print("%s: executable=%s cwd=%s; NOT EXECUTED" % (check["id"], check["executable_exists"], check["cwd_exists"]))
        if report.get("error"):
            print(report["error"])
    return 0 if report["status"] == "READY TO TRY" else 2


def evidence_bundle_problems(directory, run_id):
    """Require readable, usable evidence belonging to this run, not a tamper signature."""
    problems = []
    if not isinstance(run_id, str) or not run_id:
        problems.append("Report has no valid run_id")
    for name, key in (("trace.json", "spans"), ("metrics.json", "metrics")):
        try:
            data = json.loads((directory / name).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problems.append("Unreadable evidence %s: %s" % (name, exc))
            continue
        if not isinstance(data, dict) or data.get("run_id") != run_id:
            problems.append("Evidence run identity mismatch: " + name)
            continue
        entries = data.get(key)
        if not isinstance(entries, list) or not entries or not all(isinstance(e, dict) for e in entries):
            problems.append("Missing or malformed evidence entries: " + name)
            continue
        if key == "spans":
            ids = [e.get("span_id") for e in entries]
            if not all(isinstance(i, str) and i for i in ids) or len(set(ids)) != len(ids):
                problems.append("Invalid span identities: " + name)
            elif any(e.get("parent_id") is not None and e["parent_id"] not in ids for e in entries):
                problems.append("Unknown parent span: " + name)
            if any(not e.get("stage") or e.get("status") not in ("PASS", "FAIL", "BLOCKED")
                   or not isinstance(e.get("duration_seconds"), (int, float)) for e in entries):
                problems.append("Incomplete span evidence: " + name)
        elif any(not e.get("name") or not e.get("unit") or not isinstance(e.get("value"), (int, float))
                 for e in entries):
            problems.append("Incomplete metric evidence: " + name)
    try:
        events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        if not events or any(not isinstance(e, dict) or e.get("run_id") != run_id
                             or not e.get("event") or not e.get("timestamp") for e in events):
            problems.append("Missing, malformed or mismatched event evidence: events.jsonl")
    except (OSError, ValueError) as exc:
        problems.append("Unreadable evidence events.jsonl: %s" % exc)
    return problems


def check_final(manifest, report_path, required_files=(), profile=None):
    manifest, report_path = Path(manifest).resolve(), Path(report_path).resolve()
    root = manifest.parent
    data = load_manifest(manifest)
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ManifestError("Cannot read verification report: %s" % exc) from exc
    if not isinstance(report, dict):
        raise ManifestError("Verification report must be an object")
    problems = []
    if report.get("schema_version") != 1 or report.get("status") != "PASS":
        problems.append("Report is not a schema v1 PASS")
    problems.extend(evidence_bundle_problems(report_path.parent, report.get("run_id")))
    if report.get("manifest_sha256") != hashlib.sha256(manifest.read_bytes()).hexdigest():
        problems.append("Manifest changed or report belongs to another manifest")
    current = fingerprint(root)
    if report.get("source_after") != current or report.get("source_before") != current:
        problems.append("Source/fixtures changed; affected verification must be rerun")
    raw_results = report.get("checks", [])
    if not isinstance(raw_results, list):
        raise ManifestError("Verification report checks must be an array")
    results = {c["id"]: c for c in raw_results if isinstance(c, dict) and isinstance(c.get("id"), str)}
    if len(results) != len(raw_results):
        problems.append("Malformed or duplicate result entries")
    selected = [c for c in data["checks"] if profile is None or c.get("profile", "core") == profile]
    if not selected:
        problems.append("Final-check profile contains no checks")
    for check in selected:
        if not check["required"]:
            continue
        result = results.get(check["id"], {})
        if result.get("status") != "PASS":
            problems.append("Required check is not PASS: " + check["id"])
            continue
        if result.get("returncode") != 0:
            problems.append("PASS contradicts the process exit code: " + check["id"])
        for stream in ("stdout", "stderr"):
            name = result.get(stream)
            path = (report_path.parent / name).resolve() if isinstance(name, str) else None
            if path is None or not within(path, report_path.parent) or not path.is_file():
                problems.append("Missing %s evidence: %s" % (stream, check["id"]))
    for relative in required_files:
        path = (root / relative).resolve()
        if Path(relative).is_absolute() or not within(path, root) or not path.is_file():
            problems.append("Missing or out-of-project required file: " + relative)
    return {"status": "PASS" if not problems else "BLOCKED", "problems": problems,
            "scope": profile or "all manifest checks", "human_confirmation": "NOT ASSESSED",
            "submission": "NOT PERFORMED"}


def final_main(argv=None):
    parser = argparse.ArgumentParser(description="Check current files against recorded verification. Does not submit or invent human confirmation.")
    parser.add_argument("--manifest", default="verification.json")
    parser.add_argument("--report", required=True, help="Specific run/report.json, not an unqualified latest flag")
    parser.add_argument("--profile", help="Limit readiness claim to this explicit profile")
    parser.add_argument("--require-file", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        result = check_final(args.manifest, args.report, args.require_file, args.profile)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["status"] == "PASS" else 2
    except ManifestError as exc:
        print("BLOCKED: %s" % exc, file=sys.stderr)
        return 2


def bootstrap_main(argv=None):
    parser = argparse.ArgumentParser(description="Plan a kit install; --apply writes only reviewed, collision-free files. Existing AGENTS/config stay unchanged.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--source", default=str(Path(__file__).resolve().parents[2]), help="Source kit root")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--skill", action="append", help="Selected skill directory name; repeat. Default: all kit skills.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = install(args.source, args.target, args.apply, args.skill)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("%s: %s" % ("APPLIED" if args.apply else "DRY RUN", report["target"]))
            for action in ("create", "update", "unchanged"):
                paths = [c["path"] for c in report["changes"] if c["action"] == action]
                print("%s: %d" % (action, len(paths)))
                for path in paths:
                    if action != "unchanged":
                        print("  " + path)
            print("Preserved: AGENTS.md, .codex/config.toml")
            print(report["activation"])
        return 0
    except (InstallError, OSError) as exc:
        print("BLOCKED: %s" % exc, file=sys.stderr)
        return 2
