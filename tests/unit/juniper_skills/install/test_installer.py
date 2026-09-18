"""Test the Juniper skill installer junction safety rules."""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

import pytest

from src.juniper_skills.install import SkillInstaller


class TestSkillInstaller:
    """Verify safe junction install and removal behavior."""

    def setup_method(self) -> None:
        self._require_windows()  # Require Windows because the contract uses directory junctions.
        self.root = Path.cwd() / ".pytest-juniper-skills-install" / uuid.uuid4().hex  # Keep test files in the worktree.
        self.store = self.root / "store"  # Isolate the canonical store from the real user store.
        self.repo = self.root / "repo"  # Isolate the repository target from the real worktree.
        self.home = self.root / "home"  # Isolate user skill targets from the real profile.
        self.skill = self.store / "skills" / "juniper-test-skill"  # Use a real skill package shape.
        self.skill.mkdir(parents=True)  # Create the canonical skill package for junction tests.
        self._write_skill_file("SKILL.md", self._skill_text())  # Add the required skill entry file.
        (self.repo / ".github").mkdir(parents=True)  # Create the repository metadata folder for .gitignore.
        (self.repo / ".gitignore").write_text("# test rules\n", encoding="utf-8")  # Seed an existing ignore file.
        self.installer = SkillInstaller(self.store, self.repo, self.home)  # Point the installer at isolated paths.

    def teardown_method(self) -> None:
        self._remove_tree(self.root)  # Remove test folders and any junctions created by the test.

    def test_install_verify_and_uninstall_keep_source_files(self) -> None:
        outcomes = self.installer.install_skill("juniper-test-skill")  # Publish the test skill to all hosts.
        assert [outcome.action for outcome in outcomes].count("created") == 3  # Confirm each host received a junction.
        verify = self.installer.verify_skill("juniper-test-skill")  # Read SKILL.md through all three junction paths.
        assert [outcome.action for outcome in verify] == [
            "verified",
            "verified",
            "verified",
        ]  # Confirm discovery files read.
        second = self.installer.install_skill("juniper-test-skill")  # Run install again to prove idempotence.
        assert [outcome.action for outcome in second].count(
            "unchanged"
        ) == 3  # Confirm the second run changes no junction.
        uninstall = self.installer.uninstall_skill("juniper-test-skill")  # Remove the junctions from each host.
        assert [outcome.action for outcome in uninstall].count(
            "removed"
        ) == 3  # Confirm each junction was removed safely.
        assert (self.skill / "SKILL.md").is_file()  # Prove junction removal did not delete canonical contents.

    def test_install_refuses_to_overwrite_real_directory(self) -> None:
        real_target = self.repo / ".github" / "skills" / "juniper-test-skill"  # Select one contract target.
        real_target.mkdir(parents=True)  # Create a hand-written skill directory that the installer must preserve.
        (real_target / "SKILL.md").write_text("manual skill\n", encoding="utf-8")  # Add content that must survive.
        outcomes = self.installer.install_skill("juniper-test-skill")  # Try to install over a real directory.
        assert [outcome.action for outcome in outcomes] == ["refused"]  # Confirm the installer stops before changes.
        assert (real_target / "SKILL.md").read_text(
            encoding="utf-8"
        ) == "manual skill\n"  # Confirm content stayed intact.
        assert not (
            self.home / ".copilot" / "skills" / "juniper-test-skill"
        ).exists()  # Confirm no partial install occurred.

    def test_catalog_is_generated_from_skill_directory(self) -> None:
        outcomes = self.installer.generate_catalog()  # Generate the catalog from the canonical skill folder.
        catalog_text = (self.store / "CATALOG.md").read_text(encoding="utf-8")  # Read the generated catalog.
        assert outcomes[0].action == "generated"  # Confirm the installer reports catalog generation.
        assert "`juniper-test-skill`" in catalog_text  # Confirm the catalog lists the installed domain skill.

    def _write_skill_file(self, name: str, content: str) -> None:
        (self.skill / name).write_text(content, encoding="utf-8")  # Write deterministic skill test content.

    def _remove_tree(self, root: Path) -> None:
        if not root.exists():  # Nothing needs cleanup when setup failed early.
            return  # Keep teardown idempotent.
        for path in sorted(root.rglob("*"), reverse=True):  # Remove child paths before their parents.
            self._remove_path(path)  # Remove junctions without following them.
        shutil.rmtree(root, ignore_errors=True)  # Remove any empty folders left after safe path cleanup.

    def _remove_path(self, path: Path) -> None:
        if self._is_junction(path):  # A junction must be removed with rmdir to preserve its source.
            path.rmdir()  # Remove only the junction entry.

    def _is_junction(self, path: Path) -> bool:
        checker = getattr(path, "is_junction", None)  # Use the Windows junction detector supplied by pathlib.
        return bool(checker and checker())  # Return false where junction detection is unavailable.

    def _require_windows(self) -> None:
        if os.name != "nt":  # The installer contract is Windows-specific.
            pytest.skip("Windows directory junctions are required for this installer.")  # Explain the skipped platform.

    def _skill_text(self) -> str:
        return "\n".join(  # Build a small valid skill entry file for discovery tests.
            [
                "---",
                "name: juniper-test-skill",
                "description: Test skill for installer verification.",
                "---",
                "",
                "# Juniper test skill",
                "",
                "Read this file to verify junction discovery.",
                "",
            ]
        )
