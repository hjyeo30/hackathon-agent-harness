"""Reviewable, collision-safe installation into an existing project."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

from .evidence import IGNORED_DIRS, IGNORED_SUFFIXES
from .runner import within


class InstallError(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_files(source):
    """Copy distributable code/docs, not caches, runtime state, or Git metadata."""
    allowed_dirs = {".agents", ".codex", "configs", "docs", "templates", "scripts", "src", "tests", "examples", "issues"}
    allowed_files = {"README.md", "START_HERE.md", "AGENTS.md", "LICENSE", "pyproject.toml",
                     "verification.json", "verification.browser.json", "package.json", "package-lock.json"}
    for directory, dirs, files in os.walk(str(source), followlinks=False):
        relative = Path(directory).relative_to(source)
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS
                         and not Path(directory, d).is_symlink()
                         and (relative != Path(".") or d in allowed_dirs))
        for name in sorted(files):
            path = Path(directory, name)
            if relative == Path(".") and name not in allowed_files:
                continue
            if path.is_symlink():
                raise InstallError("Kit contains a symlink; inspect before distribution: %s" % path.relative_to(source))
            if path.suffix in IGNORED_SUFFIXES or name == ".DS_Store":
                continue
            yield path


def rewrite_skill_links(content, skill_source, installed_file, source, target):
    """Resolve repository-relative Markdown destinations into the copied kit.

    Inline prose paths are intentionally not guessed. Skills should link scripts
    and explain that commands run from the kit root.
    """
    def replace(match):
        destination = match.group(2)
        if destination.startswith(("http:", "https:", "#", "mailto:")):
            return match.group(0)
        path_text, marker, fragment = destination.partition("#")
        referenced = (skill_source.parent / path_text).resolve()
        if not within(referenced, source):
            raise InstallError("Skill link escapes source kit: %s" % destination)
        new_target = target / ".harness" / "kit" / referenced.relative_to(source)
        relative = os.path.relpath(str(new_target), str(installed_file.parent))
        return match.group(1) + relative.replace(os.sep, "/") + (marker + fragment if marker else "") + match.group(3)
    return re.sub(r"(\]\()([^\s)]+)(\))", replace, content)


def _safe_destination(destination, target):
    if not within(destination.resolve(), target):
        raise InstallError("Destination escapes target: %s" % destination)
    cursor = destination
    while cursor != target:
        if cursor.is_symlink():
            raise InstallError("Destination contains a symlink: %s" % cursor)
        if cursor != destination and cursor.exists() and not cursor.is_dir():
            raise InstallError("Destination parent is not a directory: %s" % cursor)
        cursor = cursor.parent


def install(source, target, apply=False, skills=None):
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target or within(target, source) or within(source, target):
        raise InstallError("Source kit and target must be separate, non-nested directories")
    if target.exists() and not target.is_dir():
        raise InstallError("Target must be a directory")
    skill_root = source / ".agents" / "skills"
    available = {p.name for p in skill_root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()} if skill_root.is_dir() else set()
    chosen = set(skills) if skills else available
    if not chosen:
        raise InstallError("No skills found in the source kit")
    unknown = chosen - available
    if unknown:
        raise InstallError("Unknown skills: %s" % ", ".join(sorted(unknown)))
    if any((skill_root / name).is_symlink() for name in chosen):
        raise InstallError("Selected skill is a symlink; copy reviewed source into the kit first")
    payload = {}
    for path in source_files(source):
        relative = Path(".harness/kit") / path.relative_to(source)
        payload[relative.as_posix()] = (path.read_bytes(), path.stat().st_mode & 0o777)
    for name in sorted(chosen):
        for path in sorted((skill_root / name).rglob("*")):
            if not path.is_file():
                continue
            if path.is_symlink():
                raise InstallError("Skill contains symlink: %s" % path)
            relative = Path(".agents/skills") / name / path.relative_to(skill_root / name)
            content = path.read_bytes()
            if path.suffix == ".md":
                content = rewrite_skill_links(content.decode("utf-8"), path, target / relative,
                                              source, target).encode("utf-8")
            payload[relative.as_posix()] = (content, path.stat().st_mode & 0o777)
    agent_root = source / ".codex/agents"
    if agent_root.is_dir():
        for path in sorted(agent_root.glob("*.toml")):
            if path.is_symlink():
                raise InstallError("Agent file is symlink: %s" % path)
            payload[(Path(".codex/agents") / path.name).as_posix()] = (path.read_bytes(), 0o644)
    entry = """# Installed hackathon kit

Read [the kit entrypoint](kit/START_HERE.md) and the current project's existing
instructions. This installation does not replace AGENTS.md or Codex config.

Ask Codex to use `$hackathon-start` for this project. Discoverable skills are
in `.agents/skills`; custom agents are in `.codex/agents`. If this Codex version
does not discover them, report that limitation instead of pretending it did.

Kit scripts live under `.harness/kit/scripts`. A project verification manifest
must describe this project's real commands; the kit's example manifest verifies
only the kit examples. Never present example checks as project verification.

Installation metadata: `install.json`. Runtime evidence: `runs/`.
"""
    payload[".harness/START_HERE.md"] = (entry.encode("utf-8"), 0o644)
    state_path = target / ".harness/install.json"
    _safe_destination(state_path, target)
    prior = {}
    prior_skills = []
    if state_path.exists():
        try:
            previous_state = json.loads(state_path.read_text(encoding="utf-8"))
            if previous_state.get("schema_version") != 1:
                raise InstallError("Unsupported install metadata version")
            prior = previous_state.get("files", {})
            prior_skills = previous_state.get("skills", [])
        except (OSError, ValueError) as exc:
            raise InstallError("Cannot read existing install metadata: %s" % exc) from exc
        if not isinstance(prior, dict):
            raise InstallError("Invalid install metadata")
    changes, conflicts = [], []
    for relative, (content, mode) in sorted(payload.items()):
        destination = target / relative
        _safe_destination(destination, target)
        if destination.with_name(destination.name + ".harness-tmp").exists():
            conflicts.append(relative + " (temporary installation path exists)")
            continue
        desired = sha(content)
        if destination.exists():
            if not destination.is_file():
                conflicts.append(relative + " (not a regular file)")
                continue
            current = sha(destination.read_bytes())
            if current == desired:
                action = "unchanged"
            elif prior.get(relative) == current:
                action = "update"
            else:
                conflicts.append(relative)
                continue
        else:
            action = "create"
        changes.append({"path": relative, "action": action, "sha256": desired})
    if conflicts:
        raise InstallError("No files changed. Existing edited/unowned files conflict: " + ", ".join(conflicts))
    if apply:
        # Every destination is checked before the first write. Existing user files
        # are never overwritten unless their bytes match our recorded old copy.
        for change in changes:
            if change["action"] == "unchanged":
                continue
            destination = target / change["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            content, mode = payload[change["path"]]
            temporary = destination.with_name(destination.name + ".harness-tmp")
            if temporary.exists():
                raise InstallError("Temporary install path already exists: %s" % temporary)
            try:
                with temporary.open("xb") as out:
                    out.write(content)
                temporary.chmod(mode)
                temporary.replace(destination)
            finally:
                if temporary.exists():
                    temporary.unlink()
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state = {"schema_version": 1, "skills": sorted(chosen | set(prior_skills)),
                 "files": {**prior, **{c["path"]: c["sha256"] for c in changes}},
                 "preserved": ["AGENTS.md", ".codex/config.toml"]}
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"applied": apply, "target": str(target), "selected_skills": sorted(chosen),
            "changes": changes, "preserved": ["AGENTS.md", ".codex/config.toml"],
            "selection_note": "Selection adds/updates skills; previously installed skills are not disabled or removed.",
            "activation": "Read .harness/START_HERE.md and invoke $hackathon-start"}
