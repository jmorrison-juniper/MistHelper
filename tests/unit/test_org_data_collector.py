"""Wave 8 P2 coverage — OrgDataCollector (bulk org-level read sweep)."""

from __future__ import annotations

import logging  # WHY: caplog assertions filter on the WARNING/ERROR channel emitted since #886 slice 12
import time as _stdlib_time  # WHY: patch time.time on the shared module (mypy-strict friendly)
from unittest.mock import MagicMock  # WHY: MagicMock(spec=Callable) is mandatory per project standard

import pytest  # WHY: caplog + monkeypatch fixtures assert log output + patch time.time

from src import org_data_collector as odc  # WHY: SUT under test — grab module for private helpers
from src.org_data_collector import (  # WHY: Public entry point + Operation dataclass
    ALL_OPERATIONS,
    Operation,
    OrgDataCollector,
)


def _make_export_fn() -> MagicMock:
    """Return a MagicMock(spec=callable) that records export_data_fn invocations."""
    return MagicMock(spec=lambda **kwargs: None)  # WHY: spec=callable satisfies strict style


def test_execute_cancels_when_user_declines(caplog: pytest.LogCaptureFixture) -> None:
    """When operator answers something other than 'y', execute short-circuits without collecting."""
    export_fn = _make_export_fn()  # WHY: should never be called on cancel
    get_org = MagicMock(spec=lambda: "org-1")  # WHY: returns org id
    get_org.return_value = "org-1"  # WHY: explicit return value
    safe_input = MagicMock(spec=lambda prompt, context: prompt)  # WHY: safe_input signature
    safe_input.return_value = "n"  # WHY: non-affirmative reply triggers cancel
    caplog.set_level(logging.WARNING)  # WHY: cancel confirmation emits via logging.warning since #886 slice 12.
    OrgDataCollector.execute(export_fn, get_org, safe_input)  # WHY: run the entrypoint
    export_fn.assert_not_called()  # WHY: no operations executed on cancel
    assert "Cancelled." in caplog.text  # WHY: user-visible cancel confirmation


def test_execute_runs_all_operations_when_confirmed(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """When operator confirms with 'y', execute runs every registered operation exactly once."""
    export_fn = _make_export_fn()  # WHY: recording stub
    get_org = MagicMock(spec=lambda: "org-1")  # WHY: returns org id
    get_org.return_value = "org-1"  # WHY: explicit return
    safe_input = MagicMock(spec=lambda prompt, context: prompt)  # WHY: safe_input signature
    safe_input.return_value = "Y"  # WHY: mixed-case affirmative exercises normalization
    monkeypatch.setattr(_stdlib_time, "time", lambda: 0.0)  # WHY: pin elapsed to 0 for deterministic banner output
    caplog.set_level(logging.WARNING)  # WHY: summary banner emits via logging.warning since #886 slice 12.
    OrgDataCollector.execute(export_fn, get_org, safe_input)  # WHY: run the full sweep
    assert export_fn.call_count == len(ALL_OPERATIONS)  # WHY: one export per registered operation
    out = caplog.text  # WHY: capture summary banner
    assert "Org Data Collection Complete" in out  # WHY: closing banner title printed
    assert f"Total:     {len(ALL_OPERATIONS)}" in out  # WHY: total reflects registry size


def test_confirm_run_accepts_lowercase_y() -> None:
    """A trimmed lowercase 'y' returns True."""
    safe_input = MagicMock(spec=lambda prompt, context: prompt)  # WHY: safe_input signature
    safe_input.return_value = " y "  # WHY: extra whitespace exercises the strip()
    assert odc._confirm_run(safe_input, total=5) is True  # WHY: affirmative branch


def test_confirm_run_rejects_blank_input(caplog: pytest.LogCaptureFixture) -> None:
    """Blank input is treated as decline; logs 'Cancelled.'"""
    safe_input = MagicMock(spec=lambda prompt, context: prompt)  # WHY: safe_input signature
    safe_input.return_value = ""  # WHY: empty reply is non-affirmative
    caplog.set_level(logging.WARNING)  # WHY: cancel confirmation emits via logging.warning since #886 slice 12.
    assert odc._confirm_run(safe_input, total=3) is False  # WHY: cancel path
    assert "Cancelled." in caplog.text  # WHY: user-facing message


def test_maybe_print_category_prints_on_change(caplog: pytest.LogCaptureFixture) -> None:
    """Different category prints a banner and returns the new tag."""
    caplog.set_level(logging.WARNING)  # WHY: category banner emits via logging.warning since #886 slice 12.
    result = odc._maybe_print_category("Alpha", "Beta")  # WHY: exercise category change
    assert result == "Alpha"  # WHY: new tag returned
    assert "Alpha" in caplog.text  # WHY: banner label surfaced


def test_maybe_print_category_skips_on_same(caplog: pytest.LogCaptureFixture) -> None:
    """Same category returns previous verbatim and logs nothing."""
    caplog.set_level(logging.WARNING)  # WHY: verify no banner emitted on the no-op branch.
    result = odc._maybe_print_category("Alpha", "Alpha")  # WHY: exercise no-op branch
    assert result == "Alpha"  # WHY: previous tag preserved
    assert caplog.text == ""  # WHY: no banner reprinted


def test_run_single_ok_returns_ok_sentinel(caplog: pytest.LogCaptureFixture) -> None:
    """A successful export logs OK and returns _RESULT_OK."""
    export_fn = _make_export_fn()  # WHY: stub, no side effects
    api_call = MagicMock(spec=lambda: None)  # WHY: dummy api_call carries __name__
    api_call.__name__ = "listOrgSomething"  # WHY: readable name for progress line
    op = Operation(api_call=api_call, data_type="things", category="Cat")  # WHY: minimal Operation
    caplog.set_level(logging.WARNING)  # WHY: OK status emits via logging.warning since #886 slice 12.
    result = odc._run_single(export_fn, op, index=1, total=1)  # WHY: exercise success path
    assert result == odc._RESULT_OK  # WHY: success sentinel returned
    assert "OK" in caplog.text  # WHY: trailing status printed


def test_run_single_failure_returns_failed_sentinel(caplog: pytest.LogCaptureFixture) -> None:
    """An export exception logs FAILED and returns _RESULT_FAILED."""

    def _boom(**_kwargs: object) -> None:  # WHY: injected export_fn raises
        raise RuntimeError("kaboom")  # WHY: forces the exception branch of _run_single

    api_call = MagicMock(spec=lambda: None)  # WHY: dummy api_call carries __name__
    api_call.__name__ = "listOrgSomething"  # WHY: readable name for progress line
    op = Operation(api_call=api_call, data_type="things", category="Cat")  # WHY: minimal Operation
    caplog.set_level(logging.WARNING)  # WHY: failure marker emits via logging.warning since #886 slice 12.
    result = odc._run_single(_boom, op, index=2, total=5)  # WHY: exercise failure path
    assert result == odc._RESULT_FAILED  # WHY: failure sentinel returned
    assert "FAILED (RuntimeError)" in caplog.text  # WHY: failure marker printed


def test_build_export_kwargs_paginated_default_sort() -> None:
    """Paginated operation with no sort_key gets _DEFAULT_LIMIT and _DEFAULT_SORT_KEY."""
    api_call = MagicMock(spec=lambda: None)  # WHY: any callable satisfies the field
    api_call.__name__ = "listOrgSomething"  # WHY: name only referenced for logging
    op = Operation(api_call=api_call, data_type="things", category="Cat")  # WHY: defaults for paginated + sort_key
    kwargs = odc._build_export_kwargs(op)  # WHY: exercise the default-fallback branches
    assert kwargs["limit"] == odc._DEFAULT_LIMIT  # WHY: paginated defaults to _DEFAULT_LIMIT
    assert kwargs["sort_key"] == odc._DEFAULT_SORT_KEY  # WHY: sort_key defaults to "name"
    assert kwargs["api_call"] is api_call  # WHY: bound to the operation's callable
    assert kwargs["data_type"] == "things"  # WHY: propagated verbatim


def test_build_export_kwargs_non_paginated_no_limit() -> None:
    """Non-paginated operation sets limit=None."""
    api_call = MagicMock(spec=lambda: None)  # WHY: any callable satisfies the field
    api_call.__name__ = "listOrgSomething"  # WHY: name only referenced for logging
    op = Operation(
        api_call=api_call, data_type="single", category="Cat", paginated=False, sort_key="id"
    )  # WHY: exercises paginated=False + explicit sort_key
    kwargs = odc._build_export_kwargs(op)  # WHY: exercise the non-paginated branch
    assert kwargs["limit"] is None  # WHY: non-paginated APIs must not receive limit
    assert kwargs["sort_key"] == "id"  # WHY: explicit sort_key preserved


def test_build_export_kwargs_merges_api_kwargs() -> None:
    """Per-operation api_kwargs override the base dict."""
    api_call = MagicMock(spec=lambda: None)  # WHY: any callable satisfies the field
    api_call.__name__ = "listOrgSomething"  # WHY: name only referenced for logging
    op = Operation(
        api_call=api_call,
        data_type="things",
        category="Cat",
        api_kwargs={"distinct": "mac"},
    )  # WHY: exercises the api_kwargs merge branch
    kwargs = odc._build_export_kwargs(op)  # WHY: exercise the merge
    assert kwargs["distinct"] == "mac"  # WHY: api_kwargs merged into the base dict


def test_report_failure_prints_and_returns_sentinel(caplog: pytest.LogCaptureFixture) -> None:
    """_report_failure logs FAILED with the class name and returns _RESULT_FAILED."""
    error = ValueError("bad thing")  # WHY: concrete exception with distinguishable class name
    caplog.set_level(logging.WARNING)  # WHY: failure marker emits via logging.warning since #886 slice 12.
    result = odc._report_failure("listOrgWhatever", error)  # WHY: exercise the failure helper directly
    assert result == odc._RESULT_FAILED  # WHY: failure sentinel returned
    assert "FAILED (ValueError)" in caplog.text  # WHY: class name surfaced in the marker


def test_split_elapsed_converts_seconds() -> None:
    """_split_elapsed returns (minutes, seconds) as integers."""
    minutes, seconds = odc._split_elapsed(125.7)  # WHY: 125.7s => 2m 5s
    assert (minutes, seconds) == (2, 5)  # WHY: floor-divide + remainder


def test_print_summary_banner_prints_all_lines(caplog: pytest.LogCaptureFixture) -> None:
    """_print_summary_banner emits total, succeeded, failed, skipped, and duration."""
    totals = odc._RunTotals(succeeded=3, failed=1, skipped=0, elapsed=65.0)  # WHY: distinct counts + duration
    caplog.set_level(logging.WARNING)  # WHY: summary banner emits via logging.warning since #886 slice 12.
    odc._print_summary_banner(total=4, totals=totals, minutes=1, seconds=5)  # WHY: exercise banner
    out = caplog.text  # WHY: capture banner text
    assert "Total:     4" in out  # WHY: total surfaced
    assert "Succeeded: 3" in out  # WHY: success count surfaced
    assert "Failed:    1" in out  # WHY: failure count surfaced
    assert "Skipped:   0" in out  # WHY: skip count surfaced
    assert "Duration:  1m 5s" in out  # WHY: duration formatted


def test_collect_all_tally_reflects_mix_of_results(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """_collect_all tallies OK and FAILED sentinels over the full ALL_OPERATIONS run."""
    seen: list[str] = []  # WHY: capture per-call names to prove iteration ran

    def _export(**kwargs: object) -> None:  # WHY: injected export_fn tracks calls
        seen.append(str(kwargs.get("data_type", "?")))  # WHY: record which op ran
        if len(seen) == 3:  # WHY: force one failure to exercise the FAILED branch
            raise RuntimeError("simulated")  # WHY: raises through _run_single

    monkeypatch.setattr(_stdlib_time, "time", lambda: 0.0)  # WHY: pin elapsed to 0 for deterministic run
    caplog.set_level(logging.WARNING)  # WHY: silence banner output through caplog since #886 slice 12.
    totals = odc._collect_all(_export, total=len(ALL_OPERATIONS))  # WHY: run the collector
    assert totals.failed == 1  # WHY: exactly one forced failure
    assert totals.succeeded == len(ALL_OPERATIONS) - 1  # WHY: rest succeeded
    assert totals.skipped == 0  # WHY: no skip sentinel produced today
    assert len(seen) == len(ALL_OPERATIONS)  # WHY: every op attempted
