"""Verify that the real parser handles help before bootstrap side effects."""

from __future__ import annotations

import os
import subprocess  # nosec B404  # Exercise the CLI with fixed arguments and no shell.
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import MistHelper
from src.foundation.support.refactors.main_entrypoint import ApplicationBootstrap, MainEntrypoint


class TestHelpArgumentParsing:
    """Exercise help, invalid arguments, and program names through the real parser."""

    @pytest.mark.parametrize(
        "arguments",
        [("--help",), ("-h",), ("--menu", "1", "--help"), ("-h", "--testinteractive"), ("-help",), ("--h",)],
    )
    def test_help_stops_before_startup(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], arguments: tuple[str, ...]
    ) -> None:
        """Help must exit before logs, dependency checks, or authentication can start."""
        startup = MagicMock(side_effect=AssertionError("Help must stop before startup"))
        monkeypatch.setattr(MainEntrypoint, "activate_context", startup)
        monkeypatch.setattr(sys, "argv", ["MistHelper.py", *arguments])
        with pytest.raises(SystemExit) as error:
            MainEntrypoint.run()
        assert error.value.code == 0
        assert "usage:" in capsys.readouterr().out.lower()
        startup.assert_not_called()

    @pytest.mark.parametrize("argument", ["--helpme", "help", "--HELP"])
    def test_invalid_help_variants_fail_before_startup(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], argument: str
    ) -> None:
        """Invalid tokens must produce parser errors without dependency or session work."""
        startup = MagicMock(side_effect=AssertionError("Invalid arguments must stop before startup"))
        monkeypatch.setattr(MainEntrypoint, "activate_context", startup)
        monkeypatch.setattr(sys, "argv", ["MistHelper.py", argument])
        with pytest.raises(SystemExit) as error:
            MainEntrypoint.run()
        assert error.value.code == 2
        assert "error:" in capsys.readouterr().err.lower()
        startup.assert_not_called()

    def test_empty_argument_list_is_not_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An empty parser input follows normal startup instead of the help exit path."""
        startup = MagicMock(side_effect=RuntimeError("Normal startup was reached"))
        monkeypatch.setattr(MainEntrypoint, "activate_context", startup)
        bootstrap = ApplicationBootstrap(argv=[])
        with pytest.raises(RuntimeError, match="Normal startup was reached"):
            bootstrap.bootstrap_for_cli()
        startup.assert_called_once()

    @pytest.mark.parametrize(
        "process_arguments",
        [
            ["MistHelper.py"],
            ["--help"],
            ["MistHelper.py", "--menu", "1"],
            ["MistHelper.py", "--menu", "1", "--org", "abc"],
        ],
    )
    def test_program_name_is_not_a_help_argument(
        self, monkeypatch: pytest.MonkeyPatch, process_arguments: list[str]
    ) -> None:
        """Only parsed arguments trigger help, and normal startup remains reachable."""
        startup = MagicMock(side_effect=RuntimeError("Normal startup was reached"))
        monkeypatch.setattr(MainEntrypoint, "activate_context", startup)
        monkeypatch.setattr(sys, "argv", process_arguments)
        with pytest.raises(RuntimeError, match="Normal startup was reached"):
            MainEntrypoint.run()
        startup.assert_called_once()


class TestHelpSubprocessInvocation:
    """Check both help flags in a fresh process without runtime files."""

    @pytest.mark.parametrize("flag", ["--help", "-h"])
    def test_help_exits_without_runtime_files(self, tmp_path: Path, flag: str) -> None:
        """The CLI must print usage and exit before it creates the data directory."""
        environment = os.environ.copy()
        environment["DISABLE_AUTO_INSTALL"] = "true"
        result = subprocess.run(  # nosec B603  # The interpreter, script, and flags are controlled.
            [sys.executable, str(Path(MistHelper.__file__).resolve()), flag],
            capture_output=True,
            text=True,
            timeout=60,
            env=environment,
            cwd=tmp_path,
            check=False,
        )
        assert result.returncode == 0, (result.stdout[:400], result.stderr[:400])
        assert "usage:" in result.stdout.lower()
        assert not (tmp_path / "data").exists()
