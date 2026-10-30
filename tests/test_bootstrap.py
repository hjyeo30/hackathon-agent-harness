"""Installation preserves existing projects and refuses ambiguous overwrites."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from harness.bootstrap import InstallError, install


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.source, self.target = base / "kit", base / "project"
        skill = self.source / ".agents/skills/hackathon-start"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: hackathon-start\ndescription: Start a task\n---\nRead [guide](../../../docs/guide.md).\n")
        (self.source / "docs").mkdir()
        (self.source / "docs/guide.md").write_text("# Guide\n")
        (self.source / "START_HERE.md").write_text("Start here\n")
        agents = self.source / ".codex/agents"
        agents.mkdir(parents=True)
        (agents / "hackathon-reviewer.toml").write_text('name = "hackathon-reviewer"\n')
        self.target.mkdir()
        (self.target / "AGENTS.md").write_text("USER RULES\n")
        (self.target / ".codex").mkdir()
        (self.target / ".codex/config.toml").write_text("# user settings\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_dry_run_has_no_mutation_then_apply_preserves_user_rules(self):
        report = install(self.source, self.target)
        self.assertFalse(report["applied"])
        self.assertFalse((self.target / ".harness").exists())
        install(self.source, self.target, apply=True)
        self.assertEqual((self.target / "AGENTS.md").read_text(), "USER RULES\n")
        self.assertEqual((self.target / ".codex/config.toml").read_text(), "# user settings\n")

    def test_repeat_is_idempotent_and_links_resolve(self):
        install(self.source, self.target, apply=True)
        again = install(self.source, self.target, apply=True)
        self.assertTrue(all(change["action"] == "unchanged" for change in again["changes"]))
        skill = self.target / ".agents/skills/hackathon-start/SKILL.md"
        self.assertIn("../../../.harness/kit/docs/guide.md", skill.read_text())
        self.assertTrue((skill.parent / "../../../.harness/kit/docs/guide.md").resolve().is_file())

    def test_selected_skill_includes_referenced_mcp_configuration(self):
        configs = self.source / "configs"
        configs.mkdir()
        (configs / "browser.toml").write_text('[mcp_servers.browser]\ncommand = "npx"\n')
        (self.source / "docs/guide.md").write_text("Use [MCP fragment](../configs/browser.toml).\n")
        install(self.source, self.target, apply=True, skills=["hackathon-start"])
        guide = self.target / ".harness/kit/docs/guide.md"
        fragment = (guide.parent / "../configs/browser.toml").resolve()
        self.assertEqual(fragment.read_text(), (configs / "browser.toml").read_text())

    def test_modified_installed_file_refused_before_any_writes(self):
        install(self.source, self.target, apply=True)
        modified = self.target / ".agents/skills/hackathon-start/SKILL.md"
        modified.write_text("USER EDIT")
        (self.source / "docs/new.md").write_text("new upstream file")
        with self.assertRaises(InstallError):
            install(self.source, self.target, apply=True)
        self.assertEqual(modified.read_text(), "USER EDIT")
        self.assertFalse((self.target / ".harness/kit/docs/new.md").exists())

    def test_unmodified_owned_file_can_update(self):
        install(self.source, self.target, apply=True)
        (self.source / "docs/guide.md").write_text("# Improved guide\n")
        report = install(self.source, self.target, apply=True)
        self.assertTrue(any(c["action"] == "update" for c in report["changes"]))
        self.assertEqual((self.target / ".harness/kit/docs/guide.md").read_text(), "# Improved guide\n")

    def test_unknown_skill_and_nested_install_refused(self):
        with self.assertRaises(InstallError):
            install(self.source, self.target, skills=["../../private"])
        with self.assertRaises(InstallError):
            install(self.source, self.source / "nested", apply=True)

    def test_symlink_destination_refused(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.target / ".harness").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(InstallError):
            install(self.source, self.target, apply=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_skill_reference_cannot_escape_source(self):
        (self.source / ".agents/skills/hackathon-start/SKILL.md").write_text("[private](../../../../secret.txt)")
        with self.assertRaises(InstallError):
            install(self.source, self.target, apply=True)

    def test_parent_file_conflict_prevents_partial_install(self):
        (self.target / ".agents").write_text("a user file, not a directory")
        with self.assertRaises(InstallError):
            install(self.source, self.target, apply=True)
        self.assertFalse((self.target / ".harness").exists())

    def test_temporary_collision_prevents_partial_install(self):
        path = self.target / ".harness/kit/docs/guide.md.harness-tmp"
        path.parent.mkdir(parents=True)
        path.write_text("previous interrupted work")
        with self.assertRaises(InstallError):
            install(self.source, self.target, apply=True)
        self.assertFalse((self.target / ".agents").exists())
        self.assertEqual(path.read_text(), "previous interrupted work")


if __name__ == "__main__":
    unittest.main()
