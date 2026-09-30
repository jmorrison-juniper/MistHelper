"""Keep the native compose provider in each development environment.

Issue #3398 records a Windows worktree that could not run scripts/compose.ps1.
The bootstrap installed both requirement files, but neither file named the
native provider. These contracts need no network, PowerShell, or container.
"""

from __future__ import annotations

import logging
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from scripts.bootstrap_worktree import REQUIREMENT_FILES, PipIndexProbe, WorktreeBootstrapper

LOGGER = logging.getLogger(__name__)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class TestBootstrapComposeProvider:
    """Protect the provider dependency and the existing Windows command path."""

    @staticmethod
    def _assert_provider_pin(lines: list[str]) -> None:
        """Reject an absent, unreviewed, or Windows-incompatible provider."""
        requirements = [
            Requirement(line.strip()) for line in lines if line.strip() and not line.lstrip().startswith("#")
        ]
        providers = [
            requirement for requirement in requirements if canonicalize_name(requirement.name) == "podman-compose"
        ]
        print(f"The compose dependency guard checked {len(requirements)} requirement records.")
        assert len(providers) == 1, "The bootstrap must install one native compose provider."
        assert str(providers[0].specifier) == "==1.6.0", "The native compose provider must use the reviewed pin."
        windows = {"sys_platform": "win32", "platform_system": "Windows", "os_name": "nt", "python_version": "3.13"}
        assert providers[0].marker is None or providers[0].marker.evaluate(
            windows
        ), "The native compose provider must install on Windows."

    def test_bootstrap_manifests_pin_the_native_provider(self) -> None:
        """The files that the bootstrap installs must include the reviewed provider."""
        LOGGER.info("Reading %d bootstrap manifests", len(REQUIREMENT_FILES))
        lines = [
            line
            for name in REQUIREMENT_FILES
            for line in (REPOSITORY_ROOT / name).read_text(encoding="utf-8").splitlines()
        ]
        LOGGER.debug("Read %d lines from %d bootstrap manifests", len(lines), len(REQUIREMENT_FILES))
        print(f"The compose dependency guard checked {len(REQUIREMENT_FILES)} bootstrap manifests.")
        assert "requirements-dev.txt" in REQUIREMENT_FILES
        self._assert_provider_pin(lines)

    @pytest.mark.parametrize(
        "lines",
        [
            pytest.param([], id="absent"),
            pytest.param(["# podman-compose==1.6.0"], id="comment-only"),
            pytest.param(["podman-compose"], id="unpinned"),
            pytest.param(["podman-compose==1.5.0"], id="unreviewed-version"),
            pytest.param(["podman-compose==1.6.0; sys_platform != 'win32'"], id="excludes-windows"),
            pytest.param(["podman-compose==1.6.0", "podman_compose==1.6.0"], id="duplicate"),
        ],
    )
    def test_dependency_guard_rejects_an_unusable_provider(self, lines: list[str]) -> None:
        """The dependency guard must fail without a usable reviewed provider."""
        with pytest.raises(AssertionError, match="native compose provider"):
            self._assert_provider_pin(lines)

    def test_windows_bootstrap_installs_both_manifests(self) -> None:
        """The Windows interpreter must receive the development manifest through pip."""
        bootstrapper = WorktreeBootstrapper(REPOSITORY_ROOT)
        LOGGER.info("Checking the Windows bootstrap install commands without starting a process")
        with (
            patch("scripts.bootstrap_worktree.sys.platform", "win32"),
            patch.object(PipIndexProbe, "fallback_index", return_value=None),
            patch("scripts.bootstrap_worktree.subprocess.run", return_value=CompletedProcess([], 0)) as install,
        ):
            installed = bootstrapper.install_requirements()
            commands = [call.args[0] for call in install.call_args_list]
        interpreter = str(REPOSITORY_ROOT / ".venv" / "Scripts" / "python.exe")
        expected = [
            [interpreter, "-m", "pip", "install", "-r", str(REPOSITORY_ROOT / name)]
            for name in ("requirements.txt", "requirements-dev.txt")
        ]
        LOGGER.debug("The Windows bootstrap issued %d install commands", len(commands))
        print(f"The Windows bootstrap guard checked {len(commands)} install commands.")
        assert installed == ["requirements.txt", "requirements-dev.txt"]
        assert commands == expected

    def test_compose_preserves_the_worktree_provider_and_missing_provider_error(self) -> None:
        """The compose script must retain its native provider and explicit repair command."""
        script_path = REPOSITORY_ROOT / "scripts" / "compose.ps1"
        LOGGER.info("Reading the compose provider script")
        script = script_path.read_text(encoding="utf-8")
        LOGGER.debug("Read %d characters from the compose provider script", len(script))
        print("The compose provider guard checked 1 script.")
        assert 'Join-Path $RepositoryRoot ".venv\\Scripts\\python.exe"' in script
        assert '$Interpreter = if (Test-Path $VenvPython) { $VenvPython } else { "python" }' in script
        assert "& $Interpreter -m podman_compose version *> $null" in script
        assert "& $Interpreter -m podman_compose -f $ComposeFile @ComposeArguments" in script
        assert "The native compose provider is absent." in script
        assert "$Interpreter -m pip install podman-compose" in script
        assert 'throw "podman-compose is required on Windows. See issue #2184."' in script
