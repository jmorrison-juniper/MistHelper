"""Tests for the interactive-test error observer source filter.

Issue #1636 made the runner fail an option that calls ``logging.error(...)`` and
then returns None. Issue #1786 found that the observer sat on the root logger, so
it also counted records from the ``mistapi`` SDK. The SDK logs an ERROR for every
HTTP 404, and a probe-style operation treats a 404 as the answer rather than a
fault.

Menu 74 asks for 61 site insight metrics. A site rarely carries them all, so the
SDK logged 122 records and the runner reported a false failure. Menu 196 failed
the same way when an organization had no async claim job.

These tests hold both halves of the contract. A third-party record must not fail
an option, and a MistHelper record must still fail one.
"""

from __future__ import annotations

import logging

import pytest

from src.troubleshooting.interactive_test_runner import _LoggedErrorObserver


def _record(logger_name: str, level: int = logging.ERROR) -> logging.LogRecord:
    """Build a log record that claims to come from ``logger_name``."""
    return logging.LogRecord(
        name=logger_name,
        level=level,
        pathname=__file__,
        lineno=1,
        msg="synthetic record",
        args=(),
        exc_info=None,
    )


@pytest.mark.parametrize(
    "logger_name",
    ["mistapi", "websocket", "urllib3", "requests", "paramiko"],
)
def test_third_party_error_does_not_fail_the_option(logger_name: str) -> None:
    """A third-party ERROR must not count toward the failure tally."""
    observer = _LoggedErrorObserver()
    observer.emit(_record(logger_name))
    assert observer.error_count == 0, f"{logger_name} ERROR wrongly counted as an option failure"
    assert observer.ignored_count == 1, "the ignored tally must stay visible"


def test_child_logger_of_a_third_party_root_is_also_ignored() -> None:
    """A dotted child of a third-party logger must follow its root."""
    observer = _LoggedErrorObserver()
    observer.emit(_record("mistapi.__api_response"))
    assert observer.error_count == 0
    assert observer.ignored_count == 1


@pytest.mark.parametrize(
    "logger_name",
    ["src.export.site_insights", "MistHelper", "root", ""],
)
def test_misthelper_error_still_fails_the_option(logger_name: str) -> None:
    """Issue #1636 must keep working. A MistHelper ERROR still fails the option."""
    observer = _LoggedErrorObserver()
    observer.emit(_record(logger_name))
    assert observer.error_count == 1, f"{logger_name} ERROR must still fail the option"
    assert observer.ignored_count == 0


def test_below_error_level_is_never_counted() -> None:
    """A WARNING must not fail an option."""
    observer = _LoggedErrorObserver()
    observer.emit(_record("src.export", level=logging.WARNING))
    assert observer.error_count == 0
    assert observer.ignored_count == 0


def test_menu_74_probe_pattern_no_longer_fails() -> None:
    """Reproduce the menu 74 shape: 61 missing metrics, two SDK records each."""
    observer = _LoggedErrorObserver()
    for _ in range(61):
        observer.emit(_record("mistapi"))  # apirequest HTTP error
        observer.emit(_record("mistapi"))  # apiresponse parse error
    assert observer.ignored_count == 122, "the observed run logged exactly 122 records"
    assert observer.error_count == 0, "menu 74 handled every 404, so it must pass"


def test_a_real_error_beside_sdk_noise_still_fails() -> None:
    """SDK noise must not mask a genuine swallowed error in the same option."""
    observer = _LoggedErrorObserver()
    observer.emit(_record("mistapi"))
    observer.emit(_record("src.device.prompt_utils"))
    assert observer.ignored_count == 1
    assert observer.error_count == 1, "the MistHelper error must survive the filter"
