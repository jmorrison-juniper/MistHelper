"""Regression tests for the MistHelper dependency version comparison."""

from __future__ import annotations  # WHY: keep annotation behavior consistent on Python 3.13.

import os  # WHY: disable import-time package installation before importing MistHelper.

os.environ["DISABLE_AUTO_INSTALL"] = "true"  # WHY: tests must never mutate the Python environment.

import MistHelper as mh  # WHY: import after setting the safety environment variable.


def test_version_compare_handles_unequal_lengths() -> None:
    """PEP 440 treats ``1`` and ``1.0.0`` as equal versions."""
    assert mh._version_satisfies("1", "pkg==1.0.0") is True  # WHY: unequal segment counts compare correctly.


def test_version_compare_handles_leading_zeros() -> None:
    """PEP 440 ignores leading zeros when it orders versions."""
    assert mh._version_satisfies("01.002", "pkg==1.2") is True  # WHY: leading zeros must not alter equality.


def test_version_compare_handles_non_numeric_suffix() -> None:
    """A release candidate stays below the final release."""
    assert mh._version_satisfies("1.0rc1", "pkg>=1.0") is False  # WHY: suffix order must stay intact.


def test_version_compare_handles_numeric_order() -> None:
    """Numeric comparison orders ``1.10`` after ``1.9``."""
    assert mh._version_satisfies("1.10", "pkg>1.9") is True  # WHY: numeric segments must not use string order.


def test_version_compare_handles_equality() -> None:
    """Equivalent version spellings compare equal."""
    assert mh._version_satisfies("1.0.0", "pkg==1") is True  # WHY: PEP 440 normalizes equivalent releases.
