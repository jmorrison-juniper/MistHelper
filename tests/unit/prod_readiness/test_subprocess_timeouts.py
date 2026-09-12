"""Tests that every helper subprocess call carries a timeout (issue #1943).

A child process that never exits holds its parent forever. Four helper
modules called ``subprocess.run`` with no ``timeout=`` argument. Three of the
four run inside a CI quality gate, so a stalled git call or a stalled network
read held the gate until the six-hour job limit ended it.

These tests read the real call keywords through a recording double. They fail
whenever a caller drops the bound again.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


class _RecordingRun:
    """Stand in for ``subprocess.run`` and keep the keywords it received."""

    def __init__(self, returncode: int = 0, stdout: Any = "") -> None:
        # The caller reads returncode and stdout, so the double carries both.
        self.returncode = returncode
        self.stdout = stdout
        # The test asserts on this map after the call under test returns.
        self.captured: dict[str, Any] = {}

    def __call__(self, *args: Any, **kwargs: Any) -> _RecordingRun:
        """Record the keywords and return this object as the result."""
        self.captured = dict(kwargs)  # Copy, so a later call cannot mutate it.
        return self  # The caller reads .returncode and .stdout off the result.


class _TimeoutRun:
    """Stand in for ``subprocess.run`` and always raise the timeout error."""

    def __call__(self, *_args: Any, **_kwargs: Any) -> Any:
        """Fail the way a wedged child process fails."""
        raise subprocess.TimeoutExpired(cmd="stub", timeout=1)


@pytest.fixture
def repository_root() -> Iterator[Path]:
    """Yield the repository root, because two calls read files below it."""
    yield Path(__file__).resolve().parents[2]


class TestSymbolDiffTimeout:
    """The symbol comparator must bound its git call."""

    def test_git_show_passes_a_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from tools.symbol_diff import comparator

        recorder = _RecordingRun(returncode=0, stdout="x = 1\n")
        monkeypatch.setattr(comparator.subprocess, "run", recorder)

        comparator.SymbolTableComparator().read_revision("HEAD", Path("a.py"))

        assert recorder.captured["timeout"] == comparator._GIT_TIMEOUT_SECONDS

    def test_a_stalled_git_show_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from tools.symbol_diff import comparator

        monkeypatch.setattr(comparator.subprocess, "run", _TimeoutRun())

        result = comparator.SymbolTableComparator().read_revision("HEAD", Path("a.py"))

        # The caller must skip the file, not crash the whole gate.
        assert result is None


class TestComplianceAnalyzerTimeout:
    """The compliance analyzer must bound its git call."""

    def test_check_ignore_passes_a_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from tools.compliance_analyzer import engine

        recorder = _RecordingRun(returncode=0, stdout=b"")
        monkeypatch.setattr(engine.subprocess, "run", recorder)
        monkeypatch.setattr(engine.ComplianceAnalyzer, "_resolve_git_executable", staticmethod(lambda: "git"))

        engine.ComplianceAnalyzer._filter_git_ignored([Path("a.py")])

        assert recorder.captured["timeout"] == engine._GIT_TIMEOUT_SECONDS

    def test_a_stalled_check_ignore_keeps_every_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from tools.compliance_analyzer import engine

        monkeypatch.setattr(engine.subprocess, "run", _TimeoutRun())
        monkeypatch.setattr(engine.ComplianceAnalyzer, "_resolve_git_executable", staticmethod(lambda: "git"))
        files = [Path("a.py"), Path("b.py")]

        result = engine.ComplianceAnalyzer._filter_git_ignored(files)

        # The analyzer fails open, so it must never hide a file after a stall.
        assert result == files


class TestComplexityCheckTimeout:
    """The complexity check must bound its radon call."""

    def test_radon_passes_a_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import check_top5_complexity

        recorder = _RecordingRun(returncode=0, stdout="{}")
        monkeypatch.setattr(check_top5_complexity.subprocess, "run", recorder)

        check_top5_complexity._run_radon("MistHelper.py")

        assert recorder.captured["timeout"] == check_top5_complexity._RADON_TIMEOUT_SECONDS

    def test_a_stalled_radon_raises_a_named_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import check_top5_complexity

        monkeypatch.setattr(check_top5_complexity.subprocess, "run", _TimeoutRun())

        with pytest.raises(RuntimeError, match="bound"):
            check_top5_complexity._run_radon("MistHelper.py")


class TestVerdictRegisterTimeout:
    """The CodeQL verdict register must bound its network call."""

    def test_gh_api_passes_a_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import codeql_verdict_register as register

        recorder = _RecordingRun(returncode=0, stdout="[]")
        monkeypatch.setattr(register.subprocess, "run", recorder)

        register.AlertSource("owner/repo", "py/rule").fetch()

        assert recorder.captured["timeout"] == register._GH_TIMEOUT_SECONDS

    def test_a_stalled_gh_api_raises_a_named_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import codeql_verdict_register as register

        monkeypatch.setattr(register.subprocess, "run", _TimeoutRun())

        with pytest.raises(RuntimeError, match="bound"):
            register.AlertSource("owner/repo", "py/rule").fetch()
