"""Test the repository GitHub account setup in the worktree bootstrap."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.bootstrap_worktree import GitHubAccountChecker


class TestGitHubAccountChecker:
    """Cover the local credential username repair."""

    def test_configures_the_expected_username(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """The bootstrap writes the expected account to the repository config."""
        calls: list[list[str]] = []

        monkeypatch.setattr("scripts.bootstrap_worktree.shutil.which", lambda name: "git" if name == "git" else None)
        monkeypatch.setattr(
            "scripts.bootstrap_worktree.subprocess.run",
            lambda command, **kwargs: calls.append(command) or subprocess.CompletedProcess(command, 0, "", ""),
        )

        assert GitHubAccountChecker().configure_git_username(tmp_path)

        assert calls == [
            [
                "git",
                "-C",
                str(tmp_path),
                "config",
                "--local",
                "credential.https://github.com.username",
                "jmorrison-juniper",
            ]
        ]

    def test_reports_a_failed_git_config(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A Git failure returns false and names the failure."""
        monkeypatch.setattr("scripts.bootstrap_worktree.shutil.which", lambda name: "git")
        monkeypatch.setattr(
            "scripts.bootstrap_worktree.subprocess.run",
            lambda command, **kwargs: subprocess.CompletedProcess(command, 1, "", "permission denied"),
        )

        with caplog.at_level("WARNING", logger="bootstrap_worktree"):
            configured = GitHubAccountChecker().configure_git_username(tmp_path)

        assert configured is False
        assert "permission denied" in caplog.text
