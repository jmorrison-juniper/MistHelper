"""Test the strict browser guard that issue #2241 added to the e2e conftest.

A missing Playwright package turned all 11 browser test modules into a skip, and
pytest reports a skip as a pass. The gate then reported green while it opened no
page.

The guard makes that state impossible to hide. In strict mode a missing package
stops the run instead of skipping it. These tests lock the guard.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType

import pytest

# The conftest that holds the guard. A conftest is not importable by name, so
# these tests load it by path, the same way the conftest loads its own settings.
_CONFTEST_PATH = Path(__file__).resolve().parents[3] / "tests" / "e2e" / "upgrade_portal" / "conftest.py"


@pytest.fixture(name="guard_module")
def fixture_guard_module() -> ModuleType:
    """Load the e2e conftest by path and answer the module object."""
    logging.info("Loading the browser conftest from %s", _CONFTEST_PATH)  # Report before the load.
    name = "upgrade_portal_e2e_conftest"  # One fixed name, so a second load reuses the same entry.
    spec = importlib.util.spec_from_file_location(name, _CONFTEST_PATH)
    assert spec is not None and spec.loader is not None, "the browser conftest must be loadable"
    module = importlib.util.module_from_spec(spec)  # Build an empty module for the file.
    # WHY: the conftest defines a slotted dataclass, and `dataclasses` reads the module back out
    # of `sys.modules` while it builds the class. An unregistered module answers None there.
    sys.modules[name] = module  # Register before the run, so the dataclass can find its own module.
    try:
        spec.loader.exec_module(module)  # Run the file, which defines the guard.
    finally:
        sys.modules.pop(name, None)  # Leave no stray entry behind for a later test.
    logging.debug("Loaded the browser conftest")  # Record the load after the work.
    return module


def test_the_guard_stays_quiet_when_strict_mode_is_off(
    guard_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A workstation with no browser package MUST still skip, not fail."""
    logging.info("Checking the guard with strict mode off")  # Report the plan before the work.
    monkeypatch.delenv(guard_module.STRICT_VARIABLE, raising=False)  # Leave the variable unset.
    monkeypatch.setattr(guard_module.importlib.util, "find_spec", lambda name: None)  # No package.

    # WHY: an engineer with no browser must still run the rest of the suite.
    guard_module.pytest_configure(None)


def test_the_guard_fails_a_run_that_would_skip_every_browser_test(
    guard_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Strict mode with no browser package MUST stop the run."""
    logging.info("Checking the guard with strict mode on")  # Report the plan before the work.
    monkeypatch.setenv(guard_module.STRICT_VARIABLE, guard_module.STRICT_ENABLED)  # Turn the guard on.
    monkeypatch.setattr(guard_module.importlib.util, "find_spec", lambda name: None)  # No package.

    with pytest.raises(pytest.UsageError) as failure:  # WHY: a skip would report as a pass.
        guard_module.pytest_configure(None)

    logging.debug("The guard reported %s", failure.value)  # Record the message for a failure read.
    assert "not installed" in str(failure.value), "the message must name the cause"
    assert "requirements-dev.txt" in str(failure.value), "the message must name the repair"
    assert "playwright install chromium" in str(failure.value), "the message must name the download"


def test_a_missing_parent_package_reports_a_clean_failure(
    guard_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A wholly absent package MUST raise the guard error, not an internal error.

    Why:
        `importlib.util.find_spec` answers None for a missing submodule, but it
        raises `ModuleNotFoundError` when the parent package is absent. That is
        the exact state the guard exists to catch. An unhandled raise ends the
        run in an internal error, and the repair message never prints.
    """
    logging.info("Checking the guard against a wholly absent package")  # Report the plan.
    monkeypatch.setenv(guard_module.STRICT_VARIABLE, guard_module.STRICT_ENABLED)  # Turn the guard on.

    def _raise_missing(name: str) -> None:
        """Answer the way find_spec answers when the parent package is absent."""
        raise ModuleNotFoundError("No module named 'playwright'")

    monkeypatch.setattr(guard_module.importlib.util, "find_spec", _raise_missing)

    with pytest.raises(pytest.UsageError) as failure:  # WHY: the guard must own the failure.
        guard_module.pytest_configure(None)

    assert "not installed" in str(failure.value), "the guard must print its own message"


def test_the_guard_passes_when_the_package_is_present(
    guard_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Strict mode with the browser package present MUST let the run start."""
    logging.info("Checking the guard with the package present")  # Report the plan before the work.
    monkeypatch.setenv(guard_module.STRICT_VARIABLE, guard_module.STRICT_ENABLED)  # Turn the guard on.
    monkeypatch.setattr(guard_module.importlib.util, "find_spec", lambda name: object())  # Present.

    guard_module.pytest_configure(None)  # WHY: a present package must never stop a run.


@pytest.mark.parametrize("value", ["0", "", "true", "yes", "2"])
def test_only_the_exact_value_turns_the_guard_on(
    guard_module: ModuleType, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """Any value other than the exact one MUST leave the skip in place."""
    logging.info("Checking the guard against the value %r", value)  # Report the plan.
    monkeypatch.setenv(guard_module.STRICT_VARIABLE, value)  # Set a value that is not the gate value.
    monkeypatch.setattr(guard_module.importlib.util, "find_spec", lambda name: None)  # No package.

    # WHY: one exact value keeps the gate predictable, so no stray setting fails a run.
    guard_module.pytest_configure(None)


def test_every_browser_module_still_carries_its_own_skip() -> None:
    """Each browser module MUST keep its skip, so a workstation run still works."""
    logging.info("Checking that every browser module keeps its skip")  # Report the plan.
    folder = _CONFTEST_PATH.parent  # The folder that holds the browser test modules.
    modules = sorted(path for path in folder.glob("test_*.py"))  # Read every browser test module.

    missing = [  # Collect any module that lost its own skip.
        path.name for path in modules if "importorskip" not in path.read_text(encoding="utf-8")
    ]
    logging.debug("Read %d browser modules", len(modules))  # Record the count after the read.

    assert modules, "the browser suite must hold at least one module"
    assert not missing, f"these modules lost their skip: {missing}"
