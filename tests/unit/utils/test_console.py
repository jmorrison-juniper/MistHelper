"""Unit tests for the ``echo()`` console helper (feature 1031).

Why:
    Feature 1031 replaces about 170 legacy ``logging.warning(...)  # Legacy
    console echo routed via logger.`` sites with ``echo(...)`` calls. The
    helper writes the message to stdout and emits one INFO-level log record.
    These tests lock the contract so future edits cannot silently regress
    the stdout write, the log level, or the handler configuration.

The five test cases below map one-to-one to contract clauses C-1 through
C-5 in ``specs/1031-warning-echo-refactor/contracts/echo_helper.md``.
"""

from __future__ import annotations  # WHY: PEP 604 unions and consistent style.

import logging  # WHY: caplog level assertions require the logging module.

from src.utils.console import echo  # WHY: import proves clause C-6 (stable path).

_CONSOLE_LOGGER_NAME = "src.utils.console"  # WHY: module logger name resolved by __name__.


def test_echo_plain_literal_prints_stdout_and_logs_info(capsys, caplog) -> None:
    """C-1: plain literal writes to stdout and emits one INFO record.

    Why:
        The simplest call shape must produce a single stdout line and a
        single INFO record with the literal preserved verbatim.
    """
    caplog.set_level(logging.DEBUG, logger=_CONSOLE_LOGGER_NAME)  # Capture every level so no silent drop.
    echo("Menu")  # Exercise the helper with a no-arg literal.
    captured = capsys.readouterr()  # Read stdout that print() emitted.
    assert captured.out == "Menu\n"  # Contract C-1: exact bytes to stdout.
    records = [r for r in caplog.records if r.name == _CONSOLE_LOGGER_NAME]  # Filter to this logger.
    assert len(records) == 1  # Exactly one record must be emitted.
    assert records[0].levelno == logging.INFO  # Contract C-4: INFO level.
    assert records[0].msg == "Menu"  # The msg preserves the literal for %-style deferral.
    assert records[0].args in ((), None)  # No args were passed.


def test_echo_percent_s_percent_d_formats_stdout_and_log_args(capsys, caplog) -> None:
    """C-2: format string with args produces formatted stdout and preserved log args.

    Why:
        Every migrated legacy site uses ``%s``/``%d`` style formatting. The
        helper must apply ``msg % args`` before print() and hand the raw
        (msg, args) tuple to the logger for deferred formatting.
    """
    caplog.set_level(logging.DEBUG, logger=_CONSOLE_LOGGER_NAME)  # Capture INFO records.
    echo("Site %s has %d APs", "hq-london", 42)  # Two-arg %-style call.
    captured = capsys.readouterr()  # Grab stdout for the assertion.
    assert captured.out == "Site hq-london has 42 APs\n"  # Contract C-2: formatted stdout.
    records = [r for r in caplog.records if r.name == _CONSOLE_LOGGER_NAME]  # Filter to helper logger.
    assert len(records) == 1  # Exactly one record.
    assert records[0].levelno == logging.INFO  # INFO level, never WARNING.
    assert records[0].msg == "Site %s has %d APs"  # Raw msg is preserved for deferred formatting.
    assert records[0].args == ("hq-london", 42)  # Args tuple is unchanged.
    assert records[0].getMessage() == "Site hq-london has 42 APs"  # Rendered message matches stdout.


def test_echo_literal_percent_no_args_does_not_raise(capsys, caplog) -> None:
    """C-3: literal ``%`` with no args does not raise or reinterpret.

    Why:
        Some legacy calls print percentages with no format args (for
        example ``"100% signal"``). The helper must skip ``msg % args``
        when args is empty so the literal ``%`` is preserved.
    """
    caplog.set_level(logging.DEBUG, logger=_CONSOLE_LOGGER_NAME)  # Capture INFO records.
    echo("100% signal")  # Literal percent with no args must not trigger formatting.
    captured = capsys.readouterr()  # Grab stdout for the assertion.
    assert captured.out == "100% signal\n"  # Contract C-3: literal percent preserved.
    records = [r for r in caplog.records if r.name == _CONSOLE_LOGGER_NAME]  # Filter to helper logger.
    assert len(records) == 1  # Exactly one record.
    assert records[0].levelno == logging.INFO  # INFO level.
    assert records[0].msg == "100% signal"  # Raw msg preserves the literal percent.
    assert records[0].args in ((), None)  # No args were passed.


def test_echo_never_emits_at_warning(capsys, caplog) -> None:
    """C-4: no sequence of ``echo()`` calls ever emits at WARNING.

    Why:
        The entire feature exists to remove WARNING-level pollution from
        ``data/script.log``. This test locks the level guarantee across
        multiple diverse call shapes.
    """
    caplog.set_level(logging.DEBUG, logger=_CONSOLE_LOGGER_NAME)  # Capture every level.
    echo("First")  # No-arg literal.
    echo("With %s", "arg")  # One arg.
    echo("Literal %")  # Literal percent.
    _ = capsys.readouterr()  # Drain stdout to avoid noise.
    records = [r for r in caplog.records if r.name == _CONSOLE_LOGGER_NAME]  # Filter to helper logger.
    assert len(records) == 3  # Three calls, three records.
    for record in records:  # Every record must be at INFO exactly.
        assert record.levelno == logging.INFO  # Contract C-4: no WARNING, ERROR, or CRITICAL.


def test_echo_multiple_calls_do_not_duplicate_handlers(capsys) -> None:
    """C-5: repeated ``echo()`` calls never mutate the module logger's handlers.

    Why:
        Adding handlers inside the helper would cause duplicate output and
        break the log-signal restore that motivates the whole feature.
    """
    logger = logging.getLogger(_CONSOLE_LOGGER_NAME)  # Reference the module logger.
    handler_count_before = len(logger.handlers)  # Snapshot the handler count.
    for _ in range(5):  # Call the helper multiple times to check for accretion.
        echo("noop")  # Any call shape works; the assertion is on handler count.
    _ = capsys.readouterr()  # Drain stdout.
    handler_count_after = len(logger.handlers)  # Compare against the snapshot.
    assert handler_count_after == handler_count_before  # Contract C-5: handler count unchanged.
