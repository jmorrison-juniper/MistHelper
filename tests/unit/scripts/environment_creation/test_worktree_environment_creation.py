"""Cover native environment creation and explicit platform policy for issue #3701."""

from __future__ import annotations

import logging
import platform
import subprocess
import sys
import venv
from pathlib import Path
from unittest.mock import call, patch

import pytest

from scripts.bootstrap_worktree import WorktreeBootstrapper

LOGGER = logging.getLogger(__name__)


class TestCreationPolicy:
    """Check platform decisions without claiming native Windows execution."""

    @pytest.mark.parametrize(("target_platform", "use_symlinks"), [("win32", False), ("linux", True), ("darwin", True)])
    def test_platform_selects_the_standard_venv_policy(
        self, tmp_path: Path, target_platform: str, use_symlinks: bool
    ) -> None:
        """Windows retains copies, while POSIX preserves interpreter library resolution."""
        bootstrapper = WorktreeBootstrapper(tmp_path)
        LOGGER.info("Checking the simulated %s creation decision.", target_platform)
        with (
            patch("scripts.bootstrap_worktree.sys.platform", target_platform),
            patch("scripts.bootstrap_worktree.venv.EnvBuilder", autospec=True) as builder,
        ):
            bootstrapper.create_environment()
        LOGGER.debug("Recorded %d builder decisions.", builder.call_count)
        print("The platform policy checked 1 simulated decision.")
        assert builder.call_count == 1
        assert builder.call_args == call(with_pip=True, upgrade_deps=False, symlinks=use_symlinks)
        assert builder.return_value.create.call_args == call(bootstrapper.venv_dir)

    @pytest.mark.parametrize(
        ("target_platform", "relative_path"),
        [
            ("win32", Path("Scripts") / "python.exe"),
            ("linux", Path("bin") / "python"),
            ("darwin", Path("bin") / "python"),
        ],
    )
    def test_interpreter_paths_remain_platform_specific(
        self, tmp_path: Path, target_platform: str, relative_path: Path
    ) -> None:
        """The creation choice must not change the established interpreter paths."""
        with patch("scripts.bootstrap_worktree.sys.platform", target_platform):
            interpreter = WorktreeBootstrapper(tmp_path).interpreter
        print("The interpreter path checked 1 simulated platform decision.")
        assert interpreter == tmp_path / ".venv" / relative_path


class TestCreationBoundaries:
    """Keep reuse and creation errors separate from native environment success."""

    @pytest.mark.parametrize(
        "error",
        [OSError("environment creation failed"), subprocess.CalledProcessError(-6, ["python", "-m", "ensurepip"])],
    )
    def test_creation_errors_propagate_without_success(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, error: OSError | subprocess.CalledProcessError
    ) -> None:
        """A failed builder cannot produce a successful creation report."""
        caplog.set_level(logging.DEBUG, logger="bootstrap_worktree")
        with patch("scripts.bootstrap_worktree.venv.EnvBuilder", autospec=True) as builder:
            builder.return_value.create.side_effect = error
            with pytest.raises(type(error), match="environment creation failed|ensurepip"):
                WorktreeBootstrapper(tmp_path).create_environment()
        print("The creation failure check measured 1 simulated error.")
        assert "Creating the virtual environment" in caplog.text
        assert "Created the virtual environment" not in caplog.text
        assert builder.return_value.create.call_args == call(tmp_path / ".venv")

    def test_existing_interpreter_remains_unchanged(self, tmp_path: Path) -> None:
        """Creation without recreation preserves the existing environment exactly."""
        bootstrapper = WorktreeBootstrapper(tmp_path)
        bootstrapper.interpreter.parent.mkdir(parents=True)
        bootstrapper.interpreter.write_text("existing interpreter", encoding="utf-8")
        with patch("scripts.bootstrap_worktree.venv.EnvBuilder", autospec=True) as builder:
            bootstrapper.create_environment()
        print("The reuse check measured 1 owned directory.")
        assert builder.call_count == 0
        assert bootstrapper.interpreter.read_text(encoding="utf-8") == "existing interpreter"

    def test_failed_removal_stops_recreation(self, tmp_path: Path) -> None:
        """A removal error must preserve the error and prevent a new builder."""
        bootstrapper = WorktreeBootstrapper(tmp_path)
        bootstrapper.venv_dir.mkdir()
        marker = bootstrapper.venv_dir / "preserve.txt"
        marker.write_text("preserve this environment", encoding="utf-8")
        with (
            patch("scripts.bootstrap_worktree.shutil.rmtree", side_effect=OSError("removal failed")) as removal,
            patch("scripts.bootstrap_worktree.venv.EnvBuilder", autospec=True) as builder,
        ):
            with pytest.raises(OSError, match="removal failed"):
                bootstrapper.create_environment(recreate=True)
        print("The removal failure check measured 1 owned directory.")
        assert removal.call_args == call(bootstrapper.venv_dir)
        assert builder.call_count == 0
        assert marker.read_text(encoding="utf-8") == "preserve this environment"


class TestNativeEnvironment:
    """Run the real supported interpreter and the standard-library environment builder."""

    @pytest.fixture
    def native_environment(self, tmp_path: Path) -> WorktreeBootstrapper:
        """Create one native environment without discovering uv or downloading packages."""
        bootstrapper = WorktreeBootstrapper(tmp_path / "worktree with spaces")
        LOGGER.info("Creating one native environment with offline ensurepip.")
        with patch("scripts.bootstrap_worktree.shutil.which", return_value=None) as discovery:
            bootstrapper.create_environment()
        LOGGER.debug("Created one native environment with %d uv discoveries.", discovery.call_count)
        print("The fresh creation check measured 1 native environment and 0 uv discoveries.")
        assert discovery.call_count == 0
        return bootstrapper

    class TestInterpreterRecord:
        """Share the exact interpreter checks with explicit negative cases."""

        @staticmethod
        def read(bootstrapper: WorktreeBootstrapper) -> list[str]:
            """Import pip and six standard modules in the real isolated environment."""
            probe = (
                "import ensurepip, json, pathlib, pip, sqlite3, ssl, sys, venv\n"
                "print(sys.prefix)\nprint(sys.base_prefix)\n"
                "print('.'.join(str(value) for value in sys.version_info[:3]))\nprint(pip.__version__)\n"
            )
            LOGGER.info("Reading one native interpreter record.")
            result = subprocess.run(
                [str(bootstrapper.interpreter), "-I", "-c", probe],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            readings = result.stdout.splitlines()
            LOGGER.debug("Read %d fields from one native interpreter.", len(readings))
            print("The native interpreter imported pip and 6 standard modules.")
            return readings

        @staticmethod
        def check(bootstrapper: WorktreeBootstrapper, readings: list[str]) -> None:
            """Reject an incomplete record or an interpreter outside the owned environment."""
            print("The interpreter guard checked 1 record.")
            assert len(readings) == 4, "The interpreter record must contain four fields."
            assert readings[0] == str(bootstrapper.venv_dir), "The environment prefix must name the owned directory."
            assert readings[1] == sys.base_prefix, "The base prefix must name the supported Python installation."
            assert readings[0] != readings[1], "The environment and base prefixes must differ."
            assert readings[2] == platform.python_version(), "The interpreter must retain the supported Python version."
            assert readings[3] != "", "The interpreter must provide pip."

        @pytest.mark.parametrize(
            ("field", "invalid_value", "message"),
            [
                (0, "wrong environment", "environment prefix"),
                (1, "wrong base", "base prefix"),
                (2, "0.0.0", "version"),
                (3, "", "provide pip"),
            ],
        )
        def test_guard_rejects_an_invalid_record(
            self, tmp_path: Path, field: int, invalid_value: str, message: str
        ) -> None:
            """Negative records prove the same check can fail without native environment creation."""
            bootstrapper = WorktreeBootstrapper(tmp_path)
            readings = [str(bootstrapper.venv_dir), sys.base_prefix, platform.python_version(), "26.1"]
            readings[field] = invalid_value
            with pytest.raises(AssertionError, match=message):
                self.check(bootstrapper, readings)

    def test_native_creation_provides_a_working_interpreter(self, native_environment: WorktreeBootstrapper) -> None:
        """A real environment starts with pip, standard modules, and separated prefixes."""
        readings = self.TestInterpreterRecord.read(native_environment)
        self.TestInterpreterRecord.check(native_environment, readings)
        assert native_environment.interpreter.is_symlink() is (sys.platform != "win32")

    def test_recreate_repairs_an_owned_partial_environment(self, tmp_path: Path) -> None:
        """Recreation replaces an actual copied environment and preserves a neighboring directory."""
        bootstrapper = WorktreeBootstrapper(tmp_path / "partial worktree with spaces")
        neighbor = tmp_path / "neighbor.txt"
        neighbor.write_text("leave this file unchanged", encoding="utf-8")
        LOGGER.info("Creating one native copied environment without pip.")
        venv.EnvBuilder(with_pip=False, upgrade_deps=False, symlinks=False).create(bootstrapper.venv_dir)
        stale = bootstrapper.venv_dir / "previous-install.txt"
        stale.write_text("partial environment", encoding="utf-8")
        LOGGER.debug("Created one native partial environment.")
        assert bootstrapper.interpreter.is_symlink() is False
        LOGGER.info("Recreating only the owned partial environment.")
        bootstrapper.create_environment(recreate=True)
        LOGGER.debug("Recreated one native environment.")
        readings = self.TestInterpreterRecord.read(bootstrapper)
        self.TestInterpreterRecord.check(bootstrapper, readings)
        print("The recovery check measured 2 native creations and 1 neighboring file.")
        assert bootstrapper.interpreter.is_symlink() is (sys.platform != "win32")
        assert stale.exists() is False
        assert neighbor.read_text(encoding="utf-8") == "leave this file unchanged"
