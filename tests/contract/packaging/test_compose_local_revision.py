"""Verify local image revisions without changing shared containers."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.contract.packaging.test_compose_rebuild_warning import (
    _COMPOSE,
    _COMPOSE_BUILD,
    _SCRIPT,
    _git,
    _make_revision_repository,
)

logger = logging.getLogger(__name__)


class TestLocalBuildRevision:
    """Execute the helper without a container runtime or remote connection."""

    @pytest.fixture(name="revision_checkout")
    def fixture_revision_checkout(self, tmp_path: Path) -> tuple[Path, Path]:
        """Prepare tracked helper files and a native-command test harness."""
        repository, _, _ = _make_revision_repository(tmp_path)
        (repository / "scripts").mkdir()
        for source in (_SCRIPT, _COMPOSE, _COMPOSE_BUILD):
            target = repository / ("scripts/compose.ps1" if source == _SCRIPT else source.name)
            shutil.copyfile(source, target)
        (repository / ".gitignore").write_text("ignored.log\n", encoding="utf-8")
        _git(repository, "add", "scripts/compose.ps1", "compose.yml", "compose.build.yml", ".gitignore")
        _git(repository, "commit", "-m", "deployment helper")
        _git(repository, "update-ref", "refs/remotes/origin/main", "HEAD")
        harness = tmp_path / "revision-harness.ps1"
        harness.write_text(
            r"""
$ErrorActionPreference = "Stop"
$NativeGit = (Get-Command git -CommandType Application | Select-Object -First 1).Source
function global:git {
    $Arguments = $args
    if ($Arguments -contains "fetch") {
        $global:LASTEXITCODE = 0
        return
    }
    if ($env:REVISION_TEST_GIT_FAILURE -and $Arguments -contains $env:REVISION_TEST_GIT_FAILURE) {
        $global:LASTEXITCODE = 7
        return
    }
    if ($env:REVISION_TEST_BAD_HEAD -and $Arguments -contains "rev-parse") {
        "invalid"
        $global:LASTEXITCODE = 0
        return
    }
    if ($Arguments -contains "diff") {
        # PowerShell consumes the bare separator when a function replaces a native command.
        $Arguments = $Arguments[0..6] + @("--") + $Arguments[7..($Arguments.Count - 1)]
    }
    & $NativeGit @Arguments
    $global:LASTEXITCODE = $LASTEXITCODE
}
function global:python {
    if ($args -contains "build") {
        Write-Host "BUILD:$env:MISTHELPER_BUILD_REVISION|$env:MISTHELPER_BUILD_IMAGE"
        if ($env:REVISION_TEST_PROVIDER -eq "throw") { throw "Simulated provider error" }
        $global:LASTEXITCODE = [int]$env:REVISION_TEST_PROVIDER
    } else {
        $global:LASTEXITCODE = 0
    }
}
function global:podman {
    $env:REVISION_TEST_LABEL
    $global:LASTEXITCODE = 0
}
try {
    & (Join-Path $env:REVISION_TEST_ROOT "scripts/compose.ps1") $env:REVISION_TEST_COMMAND
    $Result = $LASTEXITCODE
} finally {
    Write-Host "RESTORED:$env:MISTHELPER_BUILD_REVISION|$env:MISTHELPER_BUILD_IMAGE"
}
exit $Result
""",
            encoding="utf-8",
        )
        return repository, harness

    def run_helper(
        self, checkout: tuple[Path, Path], command: str, settings: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        """Run the actual script with only the native command boundaries replaced."""
        executable = shutil.which("pwsh")
        if executable is None:
            pytest.skip("PowerShell 7 is required to execute the compose helper")
        environment = os.environ.copy()
        for name in ("MISTHELPER_BUILD_REVISION", "MISTHELPER_BUILD_IMAGE"):
            environment.pop(name, None)
        environment.update(REVISION_TEST_ROOT=str(checkout[0]), REVISION_TEST_COMMAND=command, **settings)
        logger.info("Executing the compose %s command", command)
        result = subprocess.run(
            [executable, "-NoProfile", "-File", str(checkout[1])],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        logger.debug("The compose command returned status %d", result.returncode)
        return result

    @pytest.mark.parametrize("state", ["clean", "staged", "unstaged", "untracked", "ignored"])
    @pytest.mark.parametrize("preserve", [False, True])
    def test_build_revision(self, revision_checkout: tuple[Path, Path], state: str, preserve: bool) -> None:
        """Build labels identify each checkout state and preserve the caller environment."""
        repository = revision_checkout[0]
        if state in ("staged", "unstaged"):
            (repository / "src/app.py").write_text("changed\n", encoding="utf-8")
        if state == "staged":
            _git(repository, "add", "src/app.py")
        if state in ("untracked", "ignored"):
            (repository / ("ignored.log" if state == "ignored" else "new.py")).write_text("new\n", encoding="utf-8")
        settings = (
            {"MISTHELPER_BUILD_REVISION": "caller-revision", "MISTHELPER_BUILD_IMAGE": "caller-image"}
            if preserve
            else {}
        )
        result = self.run_helper(revision_checkout, "build", settings)
        suffix = "-dirty" if state in ("staged", "unstaged", "untracked") else ""
        expected = _git(repository, "rev-parse", "HEAD") + suffix
        overlay = yaml.safe_load(_COMPOSE_BUILD.read_text(encoding="utf-8"))

        assert result.returncode == 0, result.stderr
        assert f"BUILD:{expected}|ghcr.io/jmorrison-juniper/misthelper:latest" in result.stdout
        assert f"RESTORED:{'caller-revision|caller-image' if preserve else '|'}" in result.stdout
        assert overlay["services"]["misthelper"]["build"]["labels"]["org.opencontainers.image.revision"] == (
            "${MISTHELPER_BUILD_REVISION:?Run scripts/compose.ps1 build to set the source revision}"
        )

    @pytest.mark.parametrize("failure", ["rev-parse", "status", "bad-head", "provider-exit", "provider-throw"])
    @pytest.mark.parametrize("preserve", [False, True])
    def test_build_failure(self, revision_checkout: tuple[Path, Path], failure: str, preserve: bool) -> None:
        """Metadata failures stop the build, and provider failures restore both variables."""
        settings = (
            {"MISTHELPER_BUILD_REVISION": "caller-revision", "MISTHELPER_BUILD_IMAGE": "caller-image"}
            if preserve
            else {}
        )
        if failure in ("rev-parse", "status"):
            settings["REVISION_TEST_GIT_FAILURE"] = failure
        if failure == "bad-head":
            settings["REVISION_TEST_BAD_HEAD"] = "1"
        if failure.startswith("provider"):
            settings["REVISION_TEST_PROVIDER"] = "9" if failure == "provider-exit" else "throw"
        result = self.run_helper(revision_checkout, "build", settings)

        assert result.returncode != 0, result.stdout
        assert ("BUILD:" in result.stdout) == failure.startswith("provider")
        assert f"RESTORED:{'caller-revision|caller-image' if preserve else '|'}" in result.stdout
        assert (
            "source revision" in result.stderr or "checkout status" in result.stderr or failure.startswith("provider")
        )

    @pytest.mark.parametrize(
        ("label_kind", "expected_message", "exit_code"),
        [
            ("current", "The image is current", 0),
            ("dirty", "uncommitted changes", 1),
            ("missing", "no revision label", 1),
            ("invalid", "does not name a commit", 1),
            ("option", "does not name a commit", 1),
            ("unknown", "does not name a commit", 1),
            ("documentation", "none changes an image input", 0),
            ("source", "Changed image inputs: src/app.py", 1),
        ],
    )
    def test_check_revision(
        self, revision_checkout: tuple[Path, Path], label_kind: str, expected_message: str, exit_code: int
    ) -> None:
        """Local and CI clean labels share freshness decisions, while dirty labels fail safely."""
        repository = revision_checkout[0]
        revision = _git(repository, "rev-parse", "HEAD")
        label = {
            "dirty": f"{revision}-dirty",
            "missing": "",
            "invalid": "bad-label",
            "option": "--help",
            "unknown": "f" * 40,
        }.get(label_kind, revision)
        if label_kind in ("documentation", "source"):
            target = repository / ("documentation.md" if label_kind == "documentation" else "src/app.py")
            target.write_text("later\n", encoding="utf-8")
            _git(repository, "add", str(target))
            _git(repository, "commit", "-m", "later change")
            _git(repository, "update-ref", "refs/remotes/origin/main", "HEAD")
        result = self.run_helper(revision_checkout, "check-revision", {"REVISION_TEST_LABEL": label})
        assert result.returncode == exit_code, result.stderr
        assert expected_message in result.stdout + result.stderr
        if label_kind in ("dirty", "missing"):
            assert "The image is current" not in result.stdout
            assert "not the CI image" not in result.stdout
