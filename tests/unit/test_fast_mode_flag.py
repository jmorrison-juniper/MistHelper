"""Tests for the ``--fast`` command line flag.

Issue #1796 reports that an automated sweep deleted the ``FAST_MODE_ENABLED``
declaration from ``MistHelper.py``. No test read that module global, so no gate
reported the loss. The flag then raised ``NameError`` at runtime.

These tests read the module global on ``MistHelper`` itself. They never read a
test double, per requirement FR-015. The two existing references in
``tests/unit/serial_cc/test_switch_vc_stats.py`` set an attribute on a deps
object, and neither one caught the defect.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import argparse  # Builds the namespace that the function under test reads.
from collections.abc import Iterator  # Types the fixture return value.

import pytest  # Supplies the fixture decorator.

import MistHelper  # The module that holds the flag under test.

_MISSING = object()  # Sentinel for a module that holds no flag, so the guard test still runs.


@pytest.fixture(name="restore_fast_mode", autouse=True)
def fixture_restore_fast_mode() -> Iterator[None]:
    """Save the module state before a test and restore it after the test.

    Caution: the function under test writes a module global and registers the
    parsed arguments in ``globals()``. Without this fixture a later test reads a
    changed flag.

    The fixture reads the flag through ``getattr`` with a sentinel. A missing
    declaration must fail the guard test with a clear message. It must not raise
    inside this fixture, because a setup error hides the reason.
    """
    saved_flag = getattr(MistHelper, "FAST_MODE_ENABLED", _MISSING)  # Save the flag, which may be absent.
    saved_args = vars(MistHelper).get("args")  # Save the registered arguments, which may be absent.
    yield  # Run the test.
    if saved_flag is _MISSING:  # The module held no declaration before this test.
        vars(MistHelper).pop("FAST_MODE_ENABLED", None)  # Leave the module as the test found it.
    else:  # The module already declared the flag.
        MistHelper.FAST_MODE_ENABLED = saved_flag  # Restore the earlier value for every later test.
    if saved_args is None:  # The module held no registered arguments before this test.
        vars(MistHelper).pop("args", None)  # Remove the name that the function under test added.
    else:  # The module already held registered arguments.
        MistHelper.args = saved_args  # Restore the earlier value.


def _namespace(fast: bool) -> argparse.Namespace:
    """Return the smallest namespace that the function under test reads."""
    return argparse.Namespace(fast=fast, standalone=False)  # standalone stays False to write no env var.


def test_fast_flag_sets_the_module_global(capsys: pytest.CaptureFixture[str]) -> None:
    """The ``--fast`` flag sets ``MistHelper.FAST_MODE_ENABLED`` to True."""
    MistHelper.FAST_MODE_ENABLED = False  # Start from the opposite value, so the test proves the write.
    MistHelper._setup_runtime_flags(_namespace(fast=True))  # Apply the parsed command line flags.
    capsys.readouterr()  # Drop the fast mode scope announcement, which this test does not read.
    assert MistHelper.FAST_MODE_ENABLED is True  # The module global, not a test double, holds the value.


def test_no_fast_flag_clears_the_module_global() -> None:
    """A run without ``--fast`` sets ``MistHelper.FAST_MODE_ENABLED`` to False."""
    MistHelper.FAST_MODE_ENABLED = True  # Start from the opposite value, so the test proves the write.
    MistHelper._setup_runtime_flags(_namespace(fast=False))  # Apply the parsed command line flags.
    assert MistHelper.FAST_MODE_ENABLED is False  # The default run leaves fast mode off.


def test_fast_mode_declaration_exists() -> None:
    """The module declares ``FAST_MODE_ENABLED`` at module level with a bool value.

    This test fails when a sweep deletes the declaration, per requirement FR-014.
    That deletion is the exact defect that issue #1796 reports.
    """
    assert hasattr(MistHelper, "FAST_MODE_ENABLED"), (
        "MistHelper.py must declare the module global FAST_MODE_ENABLED. "
        "A sweep that deletes the declaration breaks the --fast command line flag."
    )  # Name the flag in the failure message, per success criterion SC-002.
    assert isinstance(MistHelper.FAST_MODE_ENABLED, bool)  # The flag holds a bool, per the declaration.


def test_fast_mode_reader_reads_the_module_global() -> None:
    """The reader that the menu code calls returns the module global value."""
    MistHelper.FAST_MODE_ENABLED = True  # Set the flag directly, without the command line path.
    assert MistHelper._fast_mode_from_global() is True  # The reader observes the module global.
    MistHelper.FAST_MODE_ENABLED = False  # Set the opposite value.
    assert MistHelper._fast_mode_from_global() is False  # The reader observes the change.
