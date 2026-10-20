"""Regression tests for the MistHelper dependency version comparison."""

from __future__ import annotations  # WHY: keep annotation behavior consistent on Python 3.13.

import os  # WHY: disable import-time package installation before importing MistHelper.

os.environ["DISABLE_AUTO_INSTALL"] = "true"  # WHY: tests must never mutate the Python environment.

import MistHelper as mh  # WHY: import after setting the safety environment variable.


def test_version_compare_handles_unequal_lengths() -> None:
    """PEP 440 treats ``1`` and ``1.0.0`` as equal versions.

    Why:
        The dependency check must keep the old equal-release behavior.
    """
    assert mh._version_satisfies("1", "pkg==1.0.0") is True  # WHY: unequal segment counts compare correctly.


def test_version_compare_handles_leading_zeros() -> None:
    """PEP 440 ignores leading zeros when it orders versions.

    Why:
        The dependency check must keep the old normalized-number behavior.
    """
    assert mh._version_satisfies("01.002", "pkg==1.2") is True  # WHY: leading zeros must not alter equality.


def test_version_compare_handles_non_numeric_suffix() -> None:
    """A release candidate stays below the final release.

    Why:
        The dependency check must not accept a release candidate as final.
    """
    assert mh._version_satisfies("1.0rc1", "pkg>=1.0") is False  # WHY: suffix order must stay intact.


def test_version_compare_handles_numeric_order() -> None:
    """Numeric comparison orders ``1.10`` after ``1.9``.

    Why:
        The dependency check must keep numeric ordering instead of text order.
    """
    assert mh._version_satisfies("1.10", "pkg>1.9") is True  # WHY: numeric segments must not use string order.


def test_version_compare_handles_equality() -> None:
    """Equivalent version spellings compare equal.

    Why:
        The dependency check must keep equality for normalized release forms.
    """
    assert mh._version_satisfies("1.0.0", "pkg==1") is True  # WHY: PEP 440 normalizes equivalent releases.


def test_version_compare_accepts_missing_constraint() -> None:
    """A missing constraint accepts an installed package.

    Why:
        The dependency check must keep the old behavior for bare requirements.
    """
    assert mh._version_satisfies("1.0rc1", "pkg") is True  # WHY: no constraint means the version is not compared.


def test_version_compare_rejects_invalid_installed_version() -> None:
    """An invalid installed version fails a real constraint.

    Why:
        The dependency check must stay safe when package metadata is malformed.
    """
    assert mh._version_satisfies("not-a-version", "pkg>=1.0") is False  # WHY: invalid metadata cannot prove compliance.
