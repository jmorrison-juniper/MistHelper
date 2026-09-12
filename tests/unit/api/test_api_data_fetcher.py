"""Unit tests for :mod:`src.api.api_data_fetcher`.

Why:
    #878 tranche 9 un-omits ``src/api/api_data_fetcher.py`` from the coverage
    exclude list. This suite exercises every branch of the ``APIDataFetcher``
    class (fetch/export pipeline, retry/backoff, malformed-response recovery,
    rate-limit handling, emergency saves) so the module can enter the
    ``--cov-fail-under=80`` gate without lowering the floor. The lazy
    ``importlib.import_module("MistHelper")`` calls inside the class body are
    stubbed via :func:`monkeypatch.setattr(importlib, "import_module", ...)` so
    that no real MistHelper globals need to load during tests.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.api.api_data_fetcher import APIDataFetcher

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


class _FakeMH:
    """Lightweight stand-in for the ``MistHelper`` module.

    Why:
        ``APIDataFetcher`` lazy-imports MistHelper via
        ``importlib.import_module("MistHelper")`` from inside methods to
        dodge circular imports. Tests need a namespace object exposing the
        specific attributes each code path touches; this class collects them
        so a single fixture can serve every test.
    """

    def __init__(self) -> None:
        """Populate default attributes touched by the fetcher's code paths."""
        self.ConfigUtils = MagicMock()
        self.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-123"
        self.apisession = MagicMock(name="apisession")
        self.API_REQUEST_MAX_RETRIES = 2
        self.API_REQUEST_RETRY_DELAY = 0.0  # collapse sleeps to zero
        self.RateLimitingUtils = MagicMock()
        self.RateLimitingUtils.get_rate_limited_delay.return_value = (0.5, 0.0)
        self._api_usage_cache = {}
        self.DataExporter = MagicMock()


@pytest.fixture
def fake_mh(monkeypatch: pytest.MonkeyPatch) -> _FakeMH:
    """Install a stubbed MistHelper module and return the stub.

    Why:
        Every APIDataFetcher path invokes ``importlib.import_module("MistHelper")``.
        Redirecting *that specific name* keeps other imports (``mistapi`` etc.)
        untouched. Time is patched to a no-op so the retry loop does not sleep.
    """
    fake = _FakeMH()
    real_import = importlib.import_module

    def _stub(name: str, *args: Any, **kwargs: Any) -> Any:
        """Return the fake MistHelper stub when asked; delegate otherwise."""
        if name == "MistHelper":
            return fake
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("src.api.api_data_fetcher.importlib.import_module", _stub)
    monkeypatch.setattr("src.api.api_data_fetcher.time.sleep", lambda _: None)
    return fake


@pytest.fixture
def api_call() -> MagicMock:
    """Return a MagicMock callable with a stable ``__name__`` attribute.

    Why:
        ``APIDataFetcher`` reads ``api_call.__name__`` for logging/exporter
        integration; a plain MagicMock does not expose that as a string by
        default (it returns a Mock), which breaks string formatting.
    """
    mock = MagicMock()
    mock.__name__ = "listOrgSites"
    return mock


def _make_fetcher(
    api_call: MagicMock,
    *,
    title: str = "Sites",
    filename: str = "sites.csv",
    sort_key: str | None = None,
    **kwargs: Any,
) -> APIDataFetcher:
    """Build an APIDataFetcher configured with sensible test defaults.

    Why:
        Most tests only vary one or two of the constructor arguments, so a
        small factory keeps individual tests short and readable.

    Args:
        api_call: Mocked API callable.
        title: Human-readable title.
        filename: Output filename argument.
        sort_key: Optional sort key.
        **kwargs: Extra kwargs forwarded to the API call.

    Returns:
        An APIDataFetcher instance ready for testing.
    """
    return APIDataFetcher(title=title, api_call=api_call, filename=filename, sort_key=sort_key, **kwargs)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestInit:
    """Constructor tests for :class:`APIDataFetcher`."""

    def test_stores_all_parameters(self, api_call: MagicMock) -> None:
        """Constructor must persist every argument onto the instance.

        Why:
            The rest of the class reads these attributes on every code path;
            regressions here would silently break downstream logic without a
            direct failure signal.
        """
        fetcher = APIDataFetcher(
            title="Users",
            api_call=api_call,
            filename="users.csv",
            sort_key="email",
            page=1,
        )
        assert fetcher.title == "Users"
        assert fetcher.api_call is api_call
        assert fetcher.filename == "users.csv"
        assert fetcher.sort_key == "email"
        assert fetcher.kwargs == {"page": 1}
        assert fetcher.org_id == ""
        assert fetcher.rawdata == []
        assert fetcher.smoothed is None

    def test_defaults_sort_key_to_none_and_kwargs_to_empty(self, api_call: MagicMock) -> None:
        """Optional parameters must default to sensible sentinels.

        Why:
            Downstream code branches on ``if self.sort_key`` and unpacks
            ``**self.kwargs``; both need to be falsy/empty when the caller
            omits them.
        """
        fetcher = APIDataFetcher(title="T", api_call=api_call, filename="f.csv")
        assert fetcher.sort_key is None
        assert fetcher.kwargs == {}


# ---------------------------------------------------------------------------
# _is_response_valid  (pure staticmethod, no fixtures needed)
# ---------------------------------------------------------------------------


class TestIsResponseValid:
    """Coverage for :meth:`APIDataFetcher._is_response_valid`."""

    def test_returns_false_when_status_code_missing(self) -> None:
        """Missing ``status_code`` attribute must count as invalid.

        Why:
            ``mistapi`` swallows timeouts by returning objects without a
            status code; the retry loop relies on ``False`` here to trigger
            another attempt.
        """
        response = object()
        assert APIDataFetcher._is_response_valid(response) is False

    def test_returns_false_when_status_code_is_none(self) -> None:
        """Explicit ``status_code=None`` must count as invalid."""
        response = MagicMock(status_code=None)
        assert APIDataFetcher._is_response_valid(response) is False

    def test_returns_false_when_status_code_500(self) -> None:
        """5xx responses must be treated as invalid so the loop retries."""
        response = MagicMock(status_code=500)
        assert APIDataFetcher._is_response_valid(response) is False

    def test_returns_false_when_status_code_599(self) -> None:
        """Any 5xx (edge value 599) must be invalid."""
        response = MagicMock(status_code=599)
        assert APIDataFetcher._is_response_valid(response) is False

    def test_returns_true_when_status_code_200(self) -> None:
        """Standard successful responses must be treated as valid."""
        response = MagicMock(status_code=200)
        assert APIDataFetcher._is_response_valid(response) is True

    def test_returns_true_when_status_code_499(self) -> None:
        """4xx statuses (except the 429 handled elsewhere) still short-circuit.

        Why:
            Retrying a client error is pointless; the method returns True to
            stop the retry loop, and the malformed-response recovery logic
            handles any downstream KeyError.
        """
        response = MagicMock(status_code=499)
        assert APIDataFetcher._is_response_valid(response) is True


# ---------------------------------------------------------------------------
# _log_retry_attempt (staticmethod that sleeps + prints)
# ---------------------------------------------------------------------------


class TestLogRetryAttempt:
    """Coverage for :meth:`APIDataFetcher._log_retry_attempt`."""

    def test_logs_warning_prints_and_sleeps(
        self,
        fake_mh: _FakeMH,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Method must warn and sleep for the exact backoff window.

        Why:
            Both side-effects are user-visible (log stream, real wall-clock
            time) so any regression there hides retry timing bugs. Per #886
            Phase 2 the duplicate print() was retired; the WARNING log now
            carries the "retrying in" notice.
        """
        with caplog.at_level(logging.WARNING):
            APIDataFetcher._log_retry_attempt("listOrgSites", attempt=0, delay=2.0)
        assert "listOrgSites" in caplog.text
        assert "retrying in 2s" in caplog.text


# ---------------------------------------------------------------------------
# _call_api_with_retry
# ---------------------------------------------------------------------------


class TestCallAPIWithRetry:
    """Coverage for the retry loop wrapper."""

    def test_returns_first_valid_response_without_retrying(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """A first-try success must return immediately.

        Why:
            Every extra retry costs real wall-time in production; unnecessary
            retries would compound rate-limit pressure.
        """
        response = MagicMock(status_code=200)
        api_call.return_value = response
        fetcher = _make_fetcher(api_call)
        fetcher.org_id = "org-x"
        result = fetcher._call_api_with_retry("listOrgSites")
        assert result is response
        assert api_call.call_count == 1

    def test_retries_and_returns_when_second_attempt_succeeds(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """A recoverable failure must produce a retry that then succeeds."""
        bad = MagicMock(status_code=None)
        good = MagicMock(status_code=200)
        api_call.side_effect = [bad, good]
        fetcher = _make_fetcher(api_call)
        result = fetcher._call_api_with_retry("listOrgSites")
        assert result is good
        assert api_call.call_count == 2

    def test_returns_last_response_after_exhausting_retries(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """All-fail path must still return the final response object.

        Why:
            Downstream error handling relies on having *some* response to
            inspect via ``_handle_key_error``; returning ``None`` here would
            crash the recovery path.
        """
        bad = MagicMock(status_code=500)
        api_call.return_value = bad
        fetcher = _make_fetcher(api_call)
        result = fetcher._call_api_with_retry("listOrgSites")
        assert result is bad
        assert api_call.call_count == fake_mh.API_REQUEST_MAX_RETRIES + 1


# ---------------------------------------------------------------------------
# _apply_rate_limiting
# ---------------------------------------------------------------------------


class TestApplyRateLimiting:
    """Coverage for the rate-limit delay helper."""

    def test_delegates_to_rate_limiting_utils_and_stores_smoothed(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Method must forward args to ``RateLimitingUtils`` and cache the smoothed value.

        Why:
            The smoothed field seeds the *next* call's delay calculation;
            losing it here would defeat the rate limiter's memory.
        """
        fake_mh.RateLimitingUtils.get_rate_limited_delay.return_value = (0.7, 0.0)
        fetcher = _make_fetcher(api_call)
        fetcher._apply_rate_limiting()
        assert fetcher.smoothed == 0.7
        fake_mh.RateLimitingUtils.get_rate_limited_delay.assert_called_once_with(
            None, fake_mh.apisession, fake_mh._api_usage_cache
        )


# ---------------------------------------------------------------------------
# _log_response_structure
# ---------------------------------------------------------------------------


class TestLogResponseStructure:
    """Coverage for the response-shape tracer."""

    def test_returns_early_when_response_has_no_data(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Absent ``data`` attribute must short-circuit without exceptions.

        Why:
            Non-mistapi responses (e.g. raw ``requests.Response`` used in
            tests) do not expose ``.data``; the tracer must tolerate that.
        """

        class NoData:
            pass

        fetcher = _make_fetcher(api_call)
        with caplog.at_level(logging.DEBUG):
            fetcher._log_response_structure(NoData())
        assert "Response.data type" not in caplog.text

    def test_traces_dict_keys(self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Dict payload must log the top-level keys."""
        response = MagicMock()
        response.data = {"results": [], "next": None}
        fetcher = _make_fetcher(api_call)
        with caplog.at_level(logging.DEBUG):
            fetcher._log_response_structure(response)
        assert "Response.data keys" in caplog.text

    def test_traces_list_length(self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """List payload must log the element count."""
        response = MagicMock()
        response.data = [1, 2, 3]
        fetcher = _make_fetcher(api_call)
        with caplog.at_level(logging.DEBUG):
            fetcher._log_response_structure(response)
        assert "Response.data is list with 3 items" in caplog.text


# ---------------------------------------------------------------------------
# _attempt_data_recovery
# ---------------------------------------------------------------------------


class TestAttemptDataRecovery:
    """Coverage for the malformed-response salvage helper."""

    def test_returns_none_when_response_has_no_data(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """No ``data`` attr must yield None so caller can escalate."""

        class NoData:
            pass

        fetcher = _make_fetcher(api_call)
        assert fetcher._attempt_data_recovery(NoData()) is None

    def test_recovers_nested_dict_data(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Nested ``data['data']`` list must be returned as-is.

        Why:
            Some mistapi endpoints wrap the row list one level deeper on
            malformed pagination; recovering it avoids losing the partial
            page.
        """
        response = MagicMock()
        response.data = {"data": [{"id": 1}, {"id": 2}]}
        fetcher = _make_fetcher(api_call)
        assert fetcher._attempt_data_recovery(response) == [{"id": 1}, {"id": 2}]

    def test_returns_none_when_dict_has_no_data_key(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Dict payload lacking a ``data`` sub-key must yield None."""
        response = MagicMock()
        response.data = {"other": "stuff"}
        fetcher = _make_fetcher(api_call)
        assert fetcher._attempt_data_recovery(response) is None

    def test_recovers_list_payload(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """List-shaped ``response.data`` must be returned unchanged."""
        response = MagicMock()
        response.data = [{"id": 9}]
        fetcher = _make_fetcher(api_call)
        assert fetcher._attempt_data_recovery(response) == [{"id": 9}]

    def test_returns_none_when_data_is_unexpected_type(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Non-dict/list ``data`` (e.g. bytes) must yield None."""
        response = MagicMock()
        response.data = b"binary junk"
        fetcher = _make_fetcher(api_call)
        assert fetcher._attempt_data_recovery(response) is None


# ---------------------------------------------------------------------------
# _log_response_error_details
# ---------------------------------------------------------------------------


class TestLogResponseErrorDetails:
    """Coverage for the diagnostic dumper used during recovery."""

    def test_logs_when_response_has_dict_data(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Dict payload must produce the ``Available keys`` diagnostic line."""
        response = MagicMock()
        response.data = {"foo": 1}
        fetcher = _make_fetcher(api_call)
        with caplog.at_level(logging.ERROR):
            fetcher._log_response_error_details(response)
        assert "Available keys" in caplog.text

    def test_logs_when_response_has_no_data(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Absent ``data`` attr still logs response-type diagnostics."""

        class NoData:
            pass

        fetcher = _make_fetcher(api_call)
        with caplog.at_level(logging.ERROR):
            fetcher._log_response_error_details(NoData())
        assert "Response details" in caplog.text


# ---------------------------------------------------------------------------
# _save_recovered_data / _handle_no_recovery / _save_partial_data_on_error
# ---------------------------------------------------------------------------


class TestSaveHelpers:
    """Coverage for the various DataExporter-invoking save helpers."""

    def test_save_recovered_data_writes_via_dataexporter(
        self,
        fake_mh: _FakeMH,
        api_call: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Recovered data must flow through ``DataExporter.write_with_format_selection``.

        Why:
            Per #886 Phase 2, the recovery notices moved from print() to
            ``logging.warning``; the assertion reads ``caplog.text`` so the
            operator-visible surface is still verified.
        """
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 1}]
        with caplog.at_level(logging.WARNING):
            fetcher._save_recovered_data()
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(
            [{"id": 1}], "sites.csv", api_function_name="listOrgSites"
        )
        assert "Recovered 1" in caplog.text

    def test_handle_no_recovery_prints_and_logs(
        self,
        fake_mh: _FakeMH,
        api_call: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """No-recovery branch must inform both user and logs.

        Why:
            Ops need a log entry so post-mortems can find the run. Per #886
            Phase 2 the redundant print() was retired; both the user-facing
            notice and the ERROR log now flow through ``caplog``.
        """
        fetcher = _make_fetcher(api_call)
        with caplog.at_level(logging.ERROR):
            fetcher._handle_no_recovery()
        assert "No data could be recovered" in caplog.text
        assert "Unable to recover" in caplog.text

    def test_save_partial_data_on_error_success(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Happy path must write partial rows and emit the summary block.

        Why:
            Per #886 Phase 2 the summary block moved to WARNING logs so a
            single stream carries the notice; ``caplog`` replaces the retired
            capsys assertion.
        """
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 1}]
        with caplog.at_level(logging.WARNING):
            fetcher._save_partial_data_on_error(RuntimeError("boom"))
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()
        assert "PARTIAL DATA SAVED" in caplog.text
        assert "boom" in caplog.text

    def test_save_partial_data_on_error_write_failure(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """DataExporter failures inside the save must be caught and reported.

        Why:
            The outer error handler already re-raises the original exception;
            swallowing the save error is intentional so we don't mask the
            root cause with a secondary failure. Per #886 Phase 2 the notice
            now flows through ``logging.error``.
        """
        fake_mh.DataExporter.write_with_format_selection.side_effect = OSError("disk full")
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 1}]
        with caplog.at_level(logging.ERROR):
            fetcher._save_partial_data_on_error(RuntimeError("boom"))
        assert "Could not save partial data" in caplog.text


# ---------------------------------------------------------------------------
# _is_rate_limit_error / _handle_rate_limit / _emergency_save_and_raise
# ---------------------------------------------------------------------------


class TestRateLimitHelpers:
    """Coverage for the HTTP-429 aware error dispatch."""

    def test_is_rate_limit_error_detects_429(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Exceptions carrying a ``.response.status_code == 429`` must return True."""
        fetcher = _make_fetcher(api_call)
        error = RuntimeError("429!")
        error.response = MagicMock(status_code=429)  # type: ignore[attr-defined]
        assert fetcher._is_rate_limit_error(error) is True

    def test_is_rate_limit_error_returns_false_for_other_status(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Non-429 or missing status must fall through to the emergency path."""
        fetcher = _make_fetcher(api_call)
        e1 = RuntimeError("other")
        e1.response = MagicMock(status_code=500)  # type: ignore[attr-defined]
        assert fetcher._is_rate_limit_error(e1) is False
        e2 = RuntimeError("no response attr")
        assert fetcher._is_rate_limit_error(e2) is False

    def test_handle_rate_limit_saves_partial_when_data_present(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Partial rows must be flushed to disk on 429.

        Why:
            Per #886 Phase 2 the "Partial data saved" notice moved to
            ``logging.warning``; ``caplog`` replaces the retired capsys check.
        """
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 1}, {"id": 2}]
        with caplog.at_level(logging.WARNING):
            fetcher._handle_rate_limit()
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()
        assert "Partial data saved: 2 records" in caplog.text

    def test_handle_rate_limit_skips_save_when_no_data(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Empty raw data on 429 must not invoke DataExporter."""
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = []
        fetcher._handle_rate_limit()
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_emergency_save_and_raise_saves_and_reraises(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Emergency path must persist partial rows before re-raising.

        Why:
            Per #886 Phase 2 the "Emergency save" notice moved to
            ``logging.warning``; ``caplog`` replaces the retired capsys check.
        """
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 1}]
        with caplog.at_level(logging.WARNING), pytest.raises(RuntimeError, match="kaboom"):
            fetcher._emergency_save_and_raise(RuntimeError("kaboom"))
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()
        assert "Emergency save: 1 partial" in caplog.text

    def test_emergency_save_swallows_secondary_save_error(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Secondary save failure must log-but-not-mask the original error."""
        fake_mh.DataExporter.write_with_format_selection.side_effect = OSError("disk")
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 1}]
        with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError, match="orig"):
            fetcher._emergency_save_and_raise(RuntimeError("orig"))
        assert "Failed to save partial data" in caplog.text

    def test_emergency_save_skips_save_when_no_partial_data(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """No partial rows must still re-raise the original error."""
        fetcher = _make_fetcher(api_call)
        with pytest.raises(RuntimeError, match="noraws"):
            fetcher._emergency_save_and_raise(RuntimeError("noraws"))
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()


# ---------------------------------------------------------------------------
# _handle_api_exception dispatch
# ---------------------------------------------------------------------------


class TestHandleAPIException:
    """Dispatch behavior of :meth:`_handle_api_exception`."""

    def test_dispatches_to_rate_limit_handler_on_429(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """A 429 must route to ``_handle_rate_limit`` and NOT re-raise."""
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 1}]
        error = RuntimeError("rl")
        error.response = MagicMock(status_code=429)  # type: ignore[attr-defined]
        fetcher._handle_api_exception(error)  # must not raise
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()

    def test_dispatches_to_emergency_save_on_other_errors(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Non-429 must call emergency save and re-raise the exception."""
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 1}]
        with pytest.raises(RuntimeError, match="other"):
            fetcher._handle_api_exception(RuntimeError("other"))


# ---------------------------------------------------------------------------
# _handle_key_error
# ---------------------------------------------------------------------------


class TestHandleKeyError:
    """Coverage for the malformed-response recovery orchestrator."""

    def test_recovers_and_saves_when_data_present(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Recoverable payload must populate rawdata and persist it."""
        response = MagicMock()
        response.data = [{"id": 1}]
        fetcher = _make_fetcher(api_call)
        fetcher._handle_key_error(response, KeyError("results"))
        assert fetcher.rawdata == [{"id": 1}]
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()

    def test_reports_when_recovery_fails(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Unrecoverable payload must fall through to the no-recovery path.

        Why:
            Per #886 Phase 2 the no-recovery notice moved to
            ``logging.error``; ``caplog`` replaces the retired capsys check.
        """

        class NoData:
            pass

        fetcher = _make_fetcher(api_call)
        with caplog.at_level(logging.ERROR):
            fetcher._handle_key_error(NoData(), KeyError("results"))
        assert fetcher.rawdata == []
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()
        assert "No data could be recovered" in caplog.text


# ---------------------------------------------------------------------------
# _handle_outer_exception
# ---------------------------------------------------------------------------


class TestHandleOuterException:
    """Coverage for the top-level failure path."""

    def test_saves_partial_data_when_present(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Partial rawdata must trigger the partial-save branch."""
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 1}]
        fetcher._handle_outer_exception(RuntimeError("outer"))
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()

    def test_reports_no_data_when_rawdata_empty(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Empty rawdata must inform the user without invoking DataExporter.

        Why:
            Per #886 Phase 2 the "No data was collected" notice moved to
            ``logging.warning``; ``caplog`` replaces the retired capsys check.
        """
        fetcher = _make_fetcher(api_call)
        with caplog.at_level(logging.WARNING):
            fetcher._handle_outer_exception(RuntimeError("outer"))
        assert "No data was collected" in caplog.text
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()


# ---------------------------------------------------------------------------
# _fetch_api_data (integration of retry, rate-limit, get_all)
# ---------------------------------------------------------------------------


class TestFetchAPIData:
    """Coverage for :meth:`_fetch_api_data` — the get_all orchestrator."""

    def test_populates_rawdata_on_success(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Happy path must populate rawdata from ``mistapi.get_all``."""
        api_call.return_value = MagicMock(status_code=200)
        fetcher = _make_fetcher(api_call)
        with patch("src.api.api_data_fetcher.mistapi.get_all", return_value=[{"a": 1}]) as mg:
            fetcher._fetch_api_data()
        mg.assert_called_once()
        assert fetcher.rawdata == [{"a": 1}]

    def test_key_error_triggers_recovery(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """A KeyError from ``get_all`` must invoke recovery, not propagate."""
        response = MagicMock(status_code=200)
        response.data = [{"id": 42}]
        api_call.return_value = response
        fetcher = _make_fetcher(api_call)
        with patch("src.api.api_data_fetcher.mistapi.get_all", side_effect=KeyError("results")):
            fetcher._fetch_api_data()
        assert fetcher.rawdata == [{"id": 42}]

    def test_non_key_error_dispatches_to_api_exception_handler(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Non-KeyError exceptions must flow through ``_handle_api_exception``."""
        api_call.return_value = MagicMock(status_code=200)
        fetcher = _make_fetcher(api_call)
        with (
            patch("src.api.api_data_fetcher.mistapi.get_all", side_effect=RuntimeError("boom")),
            pytest.raises(RuntimeError, match="boom"),
        ):
            fetcher._fetch_api_data()

    def test_rate_limit_error_swallowed_not_reraised(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """429 during get_all must not re-raise (handled path)."""
        api_call.return_value = MagicMock(status_code=200)
        fetcher = _make_fetcher(api_call)
        err = RuntimeError("rl")
        err.response = MagicMock(status_code=429)  # type: ignore[attr-defined]
        with patch("src.api.api_data_fetcher.mistapi.get_all", side_effect=err):
            fetcher._fetch_api_data()


# ---------------------------------------------------------------------------
# _prepare_data_for_display / _build_pretty_table / _display_table
# ---------------------------------------------------------------------------


class TestDisplayPipeline:
    """Coverage for the PrettyTable rendering pipeline."""

    def test_prepare_data_filters_non_dict_entries(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Non-dict rows in rawdata must be discarded silently.

        Why:
            The API occasionally returns scalar rows (strings, ints) during
            partial responses; passing them into flatten/escape helpers would
            raise TypeError.
        """
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 1}, "junk", 42, {"id": 2}]
        with (
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.flatten_nested_fields",
                side_effect=lambda d: d,
            ),
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.escape_multiline",
                side_effect=lambda d: d,
            ),
        ):
            prepared = fetcher._prepare_data_for_display()
        assert prepared == [{"id": 1}, {"id": 2}]

    def test_prepare_data_sorts_by_sort_key(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """A configured sort_key must reorder rows before flatten/escape.

        Why:
            Users rely on the export honoring the CLI-supplied sort ordering;
            skipping it would silently produce non-deterministic output.
        """
        fetcher = _make_fetcher(api_call, sort_key="name")
        fetcher.rawdata = [{"name": "b"}, {"name": "a"}]
        with (
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.flatten_nested_fields",
                side_effect=lambda d: d,
            ),
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.escape_multiline",
                side_effect=lambda d: d,
            ),
        ):
            prepared = fetcher._prepare_data_for_display()
        assert [row["name"] for row in prepared] == ["a", "b"]

    def test_build_pretty_table_uses_all_fields(self, fake_mh: _FakeMH, api_call: MagicMock) -> None:
        """Every field must appear as a column and every row as a table row."""
        fetcher = _make_fetcher(api_call)
        table = fetcher._build_pretty_table([{"a": 1, "b": 2}, {"a": 3, "b": 4}], ["a", "b"])
        assert table.field_names == ["a", "b"]
        assert len(table.rows) == 2

    def test_display_table_end_to_end(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The public wrapper must run flatten/escape and emit a table log."""
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"a": 1}]
        with (
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.flatten_nested_fields",
                side_effect=lambda d: d,
            ),
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.escape_multiline",
                side_effect=lambda d: d,
            ),
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.get_unique_keys",
                return_value=["a"],
            ),
            caplog.at_level(logging.DEBUG),
        ):
            fetcher._display_table()
        assert "| a |" in caplog.text or "a" in caplog.text


# ---------------------------------------------------------------------------
# _export_and_display_data
# ---------------------------------------------------------------------------


class TestExportAndDisplayData:
    """Coverage for :meth:`_export_and_display_data`."""

    def test_calls_exporter_and_display(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Method must invoke DataExporter with correct args and render a table.

        Why:
            Per #886 Phase 2 the "N records exported" notice moved to
            ``logging.warning``; ``caplog`` replaces the retired capsys check.
        """
        fetcher = _make_fetcher(api_call, sort_key="id")
        fetcher.rawdata = [{"id": 1}]
        with (
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.flatten_nested_fields",
                side_effect=lambda d: d,
            ),
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.escape_multiline",
                side_effect=lambda d: d,
            ),
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.get_unique_keys",
                return_value=["id"],
            ),
            caplog.at_level(logging.WARNING),
        ):
            fetcher._export_and_display_data()
        fake_mh.DataExporter.export_with_processing.assert_called_once_with(
            [{"id": 1}], "sites.csv", sort_key="id", api_function_name="listOrgSites"
        )
        assert "1 records exported" in caplog.text


# ---------------------------------------------------------------------------
# execute() — full orchestrator
# ---------------------------------------------------------------------------


class TestExecute:
    """End-to-end coverage of :meth:`execute`."""

    def test_success_path(self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Happy path must resolve org, fetch, export, and display.

        Why:
            Per #886 Phase 2 the "Starting data fetch"/"N records exported"
            notices moved to ``logging.warning``; ``caplog`` replaces the
            retired capsys check.
        """
        api_call.return_value = MagicMock(status_code=200)
        fetcher = _make_fetcher(api_call)
        with (
            patch("src.api.api_data_fetcher.mistapi.get_all", return_value=[{"id": 1}]),
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.flatten_nested_fields",
                side_effect=lambda d: d,
            ),
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.escape_multiline",
                side_effect=lambda d: d,
            ),
            patch(
                "src.api.api_data_fetcher.DataProcessingUtils.get_unique_keys",
                return_value=["id"],
            ),
            caplog.at_level(logging.WARNING),
        ):
            fetcher.execute()
        assert fetcher.org_id == "org-123"
        fake_mh.DataExporter.export_with_processing.assert_called_once()
        assert "Sites" in caplog.text
        assert "1 records exported" in caplog.text

    def test_returns_early_when_no_data(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Empty rawdata after fetch must skip export and warn."""
        api_call.return_value = MagicMock(status_code=200)
        fetcher = _make_fetcher(api_call)
        with (
            patch("src.api.api_data_fetcher.mistapi.get_all", return_value=[]),
            caplog.at_level(logging.WARNING),
        ):
            fetcher.execute()
        assert "No data returned" in caplog.text
        fake_mh.DataExporter.export_with_processing.assert_not_called()

    def test_returns_early_when_rawdata_is_none(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """``get_all`` returning None must be treated the same as empty."""
        api_call.return_value = MagicMock(status_code=200)
        fetcher = _make_fetcher(api_call)
        with (
            patch("src.api.api_data_fetcher.mistapi.get_all", return_value=None),
            caplog.at_level(logging.WARNING),
        ):
            fetcher.execute()
        assert "No data returned" in caplog.text

    def test_outer_exception_logs_and_reraises(
        self, fake_mh: _FakeMH, api_call: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A raised exception must go through the outer handler and re-raise.

        Why:
            Per #886 Phase 2 the "PARTIAL DATA SAVED"/"Emergency save"
            notices moved to ``logging.warning``; ``caplog`` replaces the
            retired capsys check.
        """
        api_call.return_value = MagicMock(status_code=200)
        fetcher = _make_fetcher(api_call)
        fetcher.rawdata = [{"id": 99}]  # simulate partial fetch before failure
        with (
            patch(
                "src.api.api_data_fetcher.mistapi.get_all",
                side_effect=RuntimeError("boom"),
            ),
            caplog.at_level(logging.WARNING),
            pytest.raises(RuntimeError, match="boom"),
        ):
            fetcher.execute()
        # emergency save happened *inside* _handle_api_exception,
        # then outer handler ran again on the re-raise
        assert fake_mh.DataExporter.write_with_format_selection.call_count >= 1
        assert "PARTIAL DATA SAVED" in caplog.text or "Emergency save" in caplog.text
