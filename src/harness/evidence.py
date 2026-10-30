"""Bounded, local evidence with explicit span and metric semantics."""
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import time
import traceback
import uuid

IGNORED_DIRS = {
    ".git", ".harness", ".runs", "node_modules", "__pycache__", ".pytest_cache",
    ".venv", "venv", "playwright-report", "test-results", ".mypy_cache",
    ".ruff_cache", ".cache", "build", "dist", ".next",
}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def fingerprint(root):
    """Hash contents and executable bits, including untracked files; never follow symlinks.

    Conservative project scope: docs/config/fixtures count, generated runtime
    directories do not. This is evidence identity, not a security signature.
    """
    root = Path(root).resolve()
    digest = hashlib.sha256()
    count = 0
    for directory, dirs, files in os.walk(str(root), followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS
                         and not Path(directory, d).is_symlink())
        for name in sorted(files):
            path = Path(directory, name)
            if path.suffix in IGNORED_SUFFIXES or name == ".DS_Store":
                continue
            relative = path.relative_to(root).as_posix()
            digest.update(relative.encode("utf-8") + b"\0")
            if path.is_symlink():
                digest.update(b"symlink\0" + os.readlink(str(path)).encode("utf-8"))
            else:
                digest.update(b"file\0" + str(path.stat().st_mode & 0o111).encode("ascii") + b"\0")
                with path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            digest.update(b"\0")
            count += 1
    return {"sha256": digest.hexdigest(), "file_count": count,
            "scope": "project contents and executable bits including untracked; runtime/build caches excluded"}


class Redactor:
    """Best-effort text redaction, not permission to log sensitive payloads."""

    def __init__(self, environ=None):
        environ = os.environ if environ is None else environ
        self.values = sorted({value for key, value in environ.items()
                              if re.search(r"TOKEN|PASSWORD|SECRET|API_KEY", key, re.I)
                              and len(value) >= 6}, key=len, reverse=True)

    def __call__(self, text):
        for value in self.values:
            text = text.replace(value, "[REDACTED]")
        text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+", r"\1[REDACTED]", text)
        text = re.sub(r"(?i)((?:api[_-]?key|password|token|secret)\s*[=:]\s*)[^\s,;]+",
                      r"\1[REDACTED]", text)
        return text

    def clean(self, value):
        """Redact values before JSON encoding so quotes cannot corrupt the file."""
        if isinstance(value, str):
            return self(value)
        if isinstance(value, dict):
            return {key: self.clean(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.clean(item) for item in value]
        return value


class Evidence:
    """Events describe actions; spans describe causal stages; metrics name units."""

    def __init__(self, directory, run_id=None):
        self.directory = Path(directory)
        if any((self.directory / name).exists() for name in ("events.jsonl", "report.json", "trace.json", "metrics.json")):
            raise FileExistsError("Evidence directory already contains a run; choose a new run directory")
        self.directory.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or uuid.uuid4().hex
        self.spans = []
        self.metrics = []
        self.redact = Redactor()

    def event(self, event, **fields):
        record = {"timestamp": utc_now(), "run_id": self.run_id, "event": event, **fields}
        line = json.dumps(self.redact.clean(record), ensure_ascii=False, sort_keys=True)
        with (self.directory / "events.jsonl").open("a", encoding="utf-8") as out:
            out.write(line + "\n")

    def metric(self, name, value, unit, **labels):
        self.metrics.append({"name": name, "value": value, "unit": unit, "labels": labels})

    @contextlib.contextmanager
    def span(self, stage, parent_id=None, **attributes):
        span = {"span_id": uuid.uuid4().hex[:16], "parent_id": parent_id,
                "stage": stage, "started_at": utc_now(), "attributes": attributes,
                "status": "PASS", "error_type": None}
        start = time.monotonic()
        self.event("span.started", span_id=span["span_id"], stage=stage, parent_id=parent_id)
        try:
            yield span
        except BaseException as exc:
            span.update(status="FAIL", error_type=type(exc).__name__, error_message=str(exc),
                        exception_traceback="".join(traceback.format_exception(type(exc), exc, exc.__traceback__, limit=12)))
            raise
        finally:
            span["duration_seconds"] = round(time.monotonic() - start, 6)
            self.spans.append(span)
            self.event("span.finished", **span)

    def finish(self, report):
        for name, data in (("report.json", report),
                           ("trace.json", {"run_id": self.run_id, "spans": self.spans}),
                           ("metrics.json", {"run_id": self.run_id, "metrics": self.metrics})):
            value = json.dumps(self.redact.clean(data), ensure_ascii=False, indent=2, sort_keys=True)
            (self.directory / name).write_text(value + "\n", encoding="utf-8")
