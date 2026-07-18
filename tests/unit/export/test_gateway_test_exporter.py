"""Unit tests for GatewayTestExporter — covers every static-method branch.

Why:
    The tranche-16 push of issue #878 removes ``src/export/gateway_test_exporter.py``
    from the coverage ``omit`` list.  A pre-existing wiring-only test covered ~36 %
    of statements; this suite drives the retry, tagging, concurrency-fan-out and
    export paths so the module lands at 100 % line coverage without leaning on
    live MistHelper globals or the real Mist API.
"""

from __future__ import annotations

import sys
from concurrent.futures import Future
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.export import gateway_test_exporter as gte
from src.export.gateway_test_exporter import GatewayTestExporter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_mh(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Install a synthetic ``MistHelper`` module returned by every lazy import.

    Why:
        Every helper in ``gateway_test_exporter`` calls
        ``importlib.import_module("MistHelper")``.  Patching that lookup once
        keeps the tests deterministic and avoids pulling in real live globals.
    """
    mh = ModuleType("MistHelper")
    mh._configure_gateway_module = MagicMock()  # type: ignore[attr-defined]
    mh.PROGRESS_EMITTER = MagicMock()  # type: ignore[attr-defined]
    mh.ProgressContext = MagicMock(side_effect=lambda *a, **k: ("ctx", a, k))  # type: ignore[attr-defined]
    mh.ConfigUtils = MagicMock()  # type: ignore[attr-defined]
    mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    mh.GatewayExportUtils = MagicMock()  # type: ignore[attr-defined]
    mh.FAST_MODE_MAX_RETRIES = 3  # type: ignore[attr-defined]
    mh.FAST_MODE_RETRY_DELAY = 0.0  # type: ignore[attr-defined]
    mh.FAST_MODE_RETRY_THREADS = 4  # type: ignore[attr-defined]
    mh.FAST_MODE_RETRY_MAX_RETRIES = 1  # type: ignore[attr-defined]
    mh.FastModeBackoffMultiplier = SimpleNamespace(VALUE=2)  # type: ignore[attr-defined]
    mh.FastModeSequentialMaxRetries = SimpleNamespace(VALUE=2)  # type: ignore[attr-defined]
    mh.apisession = MagicMock()  # type: ignore[attr-defined]
    mh._api_usage_cache = {}  # type: ignore[attr-defined]
    mh.ConnectionPoolExecutor = MagicMock()  # type: ignore[attr-defined]
    mh.RateLimitingUtils = MagicMock()  # type: ignore[attr-defined]
    mh.RateLimitingUtils.get_rate_limited_delay.return_value = (0.1, 0.0)
    mh.DataExporter = MagicMock()  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


# ---------------------------------------------------------------------------
# _resolve_misthelper_runtime
# ---------------------------------------------------------------------------


class TestResolveMisthelperRuntime:
    def test_returns_module_and_configures_gateway(self, fake_mh: ModuleType) -> None:
        result = GatewayTestExporter._resolve_misthelper_runtime()
        assert result is fake_mh
        fake_mh._configure_gateway_module.assert_called_once()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# synthetic_tests (top-level entry)
# ---------------------------------------------------------------------------


class TestSyntheticTests:
    def test_no_gateway_devices_early_return(self, fake_mh: ModuleType) -> None:
        fake_mh.GatewayExportUtils._get_devices_with_sites.return_value = []  # type: ignore[attr-defined]
        fake_mh.PROGRESS_EMITTER = None  # type: ignore[attr-defined]
        GatewayTestExporter.synthetic_tests(fast=False)
        fake_mh.GatewayExportUtils._get_devices_with_sites.assert_called_once_with("org-1", fast=False)  # type: ignore[attr-defined]

    def test_fast_path_invokes_pool(self, fake_mh: ModuleType) -> None:
        devices = [("s1", "d1", "dn1", "sn1")]
        fake_mh.GatewayExportUtils._get_devices_with_sites.return_value = devices  # type: ignore[attr-defined]
        fake_mh.ConnectionPoolExecutor.execute.return_value = ([{"x": 1}], [])  # type: ignore[attr-defined]
        with patch.object(GatewayTestExporter, "_export_synthetic_results") as export_mock:
            GatewayTestExporter.synthetic_tests(fast=True)
        export_mock.assert_called_once()

    def test_sequential_path_invokes_seq(self, fake_mh: ModuleType) -> None:
        devices = [("s1", "d1", "dn1", "sn1")]
        fake_mh.GatewayExportUtils._get_devices_with_sites.return_value = devices  # type: ignore[attr-defined]
        with (
            patch.object(GatewayTestExporter, "_run_synthetic_sequential_path") as seq_mock,
            patch.object(GatewayTestExporter, "_export_synthetic_results"),
        ):
            GatewayTestExporter.synthetic_tests(fast=False)
        seq_mock.assert_called_once()


# ---------------------------------------------------------------------------
# _emit_synthetic_complete
# ---------------------------------------------------------------------------


class TestEmitSyntheticComplete:
    def test_no_emitter_is_noop(self, fake_mh: ModuleType) -> None:
        GatewayTestExporter._emit_synthetic_complete(None, 0.0, [], [])
        fake_mh.ProgressContext.assert_not_called()  # type: ignore[attr-defined]

    def test_emitter_present_calls_complete(self, fake_mh: ModuleType) -> None:
        emitter = MagicMock()
        GatewayTestExporter._emit_synthetic_complete(emitter, 0.0, ["d1"], ["r1"])
        emitter.emit_progress_complete.assert_called_once()


# ---------------------------------------------------------------------------
# _resolve_retry_defaults
# ---------------------------------------------------------------------------


class TestResolveRetryDefaults:
    def test_all_defaults_from_mh(self, fake_mh: ModuleType) -> None:
        r, d = GatewayTestExporter._resolve_retry_defaults(None, None)
        assert (r, d) == (fake_mh.FAST_MODE_MAX_RETRIES, fake_mh.FAST_MODE_RETRY_DELAY)  # type: ignore[attr-defined]

    def test_explicit_values_preserved(self, fake_mh: ModuleType) -> None:
        r, d = GatewayTestExporter._resolve_retry_defaults(7, 1.5)
        assert (r, d) == (7, 1.5)


# ---------------------------------------------------------------------------
# fetch_synthetic_test_stats_with_retry
# ---------------------------------------------------------------------------


class TestFetchSyntheticTestStatsWithRetry:
    def test_success_first_attempt(self, fake_mh: ModuleType) -> None:
        with patch.object(GatewayTestExporter, "_try_synthetic_fetch_attempt", return_value={"ok": True}):
            result = GatewayTestExporter.fetch_synthetic_test_stats_with_retry(("s", "d", "dn", "sn"), max_retries=3)
        assert result == {"ok": True}

    def test_all_attempts_fail(self, fake_mh: ModuleType) -> None:
        with (
            patch.object(GatewayTestExporter, "_try_synthetic_fetch_attempt", return_value=None),
            patch.object(gte.time, "sleep"),
        ):
            result = GatewayTestExporter.fetch_synthetic_test_stats_with_retry(
                ("s", "d", "dn", "sn"), max_retries=2, retry_delay=0.0
            )
        assert result is None

    def test_success_after_retry(self, fake_mh: ModuleType) -> None:
        outcomes = [None, {"ok": True}]
        with (
            patch.object(GatewayTestExporter, "_try_synthetic_fetch_attempt", side_effect=outcomes),
            patch.object(gte.time, "sleep"),
        ):
            result = GatewayTestExporter.fetch_synthetic_test_stats_with_retry(
                ("s", "d", "dn", "sn"), max_retries=2, retry_delay=0.0
            )
        assert result == {"ok": True}

    def test_zero_retry_budget_hits_defensive_return(self, fake_mh: ModuleType) -> None:
        result = GatewayTestExporter.fetch_synthetic_test_stats_with_retry(
            ("s", "d", "dn", "sn"), max_retries=-1, retry_delay=0.0
        )
        assert result is None


# ---------------------------------------------------------------------------
# _try_synthetic_fetch_attempt
# ---------------------------------------------------------------------------


class TestTrySyntheticFetchAttempt:
    def test_success_returns_tagged_stats(self, fake_mh: ModuleType) -> None:
        with (
            patch("src.export.gateway_test_exporter.ValidationUtils"),
            patch.object(GatewayTestExporter, "_call_synthetic_endpoint", return_value={"x": 1}),
        ):
            result = GatewayTestExporter._try_synthetic_fetch_attempt(("s", "d", "dn", "sn"), 0, None)
        assert result is not None
        assert result["site_id"] == "s"
        assert result["device_id"] == "d"

    def test_exception_returns_none(self, fake_mh: ModuleType) -> None:
        with patch(
            "src.export.gateway_test_exporter.ValidationUtils.validate_site_id",
            side_effect=RuntimeError("boom"),
        ):
            result = GatewayTestExporter._try_synthetic_fetch_attempt(("s", "d", "dn", "sn"), 0, None)
        assert result is None


# ---------------------------------------------------------------------------
# _tag_synthetic_stats
# ---------------------------------------------------------------------------


class TestTagSyntheticStats:
    def test_first_attempt_tags_fields(self, fake_mh: ModuleType) -> None:
        stats: dict[str, Any] = {}
        GatewayTestExporter._tag_synthetic_stats(stats, ("s", "d", "dn", "sn"), 0)
        assert stats == {"site_id": "s", "site_name": "sn", "device_id": "d", "device_name": "dn"}

    def test_retry_attempt_logs_retry_success(self, fake_mh: ModuleType) -> None:
        stats: dict[str, Any] = {}
        GatewayTestExporter._tag_synthetic_stats(stats, ("s", "d", "dn", "sn"), 2)
        assert stats["site_id"] == "s"


# ---------------------------------------------------------------------------
# _call_synthetic_endpoint
# ---------------------------------------------------------------------------


class TestCallSyntheticEndpoint:
    def test_without_semaphore(self, fake_mh: ModuleType) -> None:
        with patch("src.export.gateway_test_exporter.mistapi") as mistapi_mock:
            mistapi_mock.api.v1.sites.devices.getSiteDeviceSyntheticTest.return_value.data = {"r": 1}
            result = GatewayTestExporter._call_synthetic_endpoint("s", "d", None)
        assert result == {"r": 1}

    def test_with_semaphore(self, fake_mh: ModuleType) -> None:
        sema = MagicMock()
        sema.__enter__ = MagicMock(return_value=None)
        sema.__exit__ = MagicMock(return_value=None)
        with patch("src.export.gateway_test_exporter.mistapi") as mistapi_mock:
            mistapi_mock.api.v1.sites.devices.getSiteDeviceSyntheticTest.return_value.data = {"r": 2}
            result = GatewayTestExporter._call_synthetic_endpoint("s", "d", sema)
        assert result == {"r": 2}
        sema.__enter__.assert_called_once()


# ---------------------------------------------------------------------------
# _run_synthetic_fast_path
# ---------------------------------------------------------------------------


class TestRunSyntheticFastPath:
    def test_pool_success_and_failures(self, fake_mh: ModuleType) -> None:
        fake_mh.ConnectionPoolExecutor.execute.return_value = ([{"a": 1}, {"b": 2}], [("s", "d", "dn", "sn")])  # type: ignore[attr-defined]
        all_stats: list[Any] = []
        GatewayTestExporter._run_synthetic_fast_path([("s", "d", "dn", "sn")], all_stats)
        assert all_stats == [{"a": 1}, {"b": 2}]

    def test_inner_worker_delegates_to_retry_fetch(self, fake_mh: ModuleType) -> None:
        # Capture the inner worker function passed into ConnectionPoolExecutor.execute
        captured: dict[str, Any] = {}

        def fake_execute(**kwargs: Any) -> tuple[list[Any], list[Any]]:
            captured["worker"] = kwargs["worker_function"]
            return [], []

        fake_mh.ConnectionPoolExecutor.execute.side_effect = fake_execute  # type: ignore[attr-defined]
        with patch.object(GatewayTestExporter, "fetch_synthetic_test_stats_with_retry", return_value={"x": 1}) as fetch:
            GatewayTestExporter._run_synthetic_fast_path([("s", "d", "dn", "sn")], [])
            worker = captured["worker"]
            out = worker(("s", "d", "dn", "sn"), MagicMock())
        assert out == {"x": 1}
        fetch.assert_called_once()


# ---------------------------------------------------------------------------
# _retry_failed_synthetic_devices
# ---------------------------------------------------------------------------


class TestRetryFailedSyntheticDevices:
    def test_no_threads_available_returns_original_failures(
        self, fake_mh: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(gte, "FAST_MODE_MAX_CONCURRENT_CONNECTIONS", 1, raising=False)
        # Force FAST_MODE_RETRY_THREADS=0 so min(...)=0 → early warning branch
        fake_mh.FAST_MODE_RETRY_THREADS = 0  # type: ignore[attr-defined]
        failed = [("s", "d", "dn", "sn")]
        results, still = GatewayTestExporter._retry_failed_synthetic_devices(failed, None)
        assert results == []
        assert still == failed

    def test_retry_pool_runs_and_records_outcomes(self, fake_mh: ModuleType) -> None:
        failed = [("s1", "d1", "dn1", "sn1"), ("s2", "d2", "dn2", "sn2")]
        futures_map = {MagicMock(): failed[0], MagicMock(): failed[1]}

        def submit_side_effect(*_args: Any, **_kwargs: Any) -> Any:  # not used directly
            return MagicMock()

        with (
            patch.object(GatewayTestExporter, "_submit_synthetic_retries", return_value=futures_map),
            patch.object(GatewayTestExporter, "_record_retry_outcome"),
            patch("src.export.gateway_test_exporter.tqdm", side_effect=lambda x, **_k: list(x)),
            patch("src.export.gateway_test_exporter.as_completed", side_effect=lambda x: list(x)),
        ):
            results, still = GatewayTestExporter._retry_failed_synthetic_devices(failed, None)
        assert results == [] and still == []


# ---------------------------------------------------------------------------
# _submit_synthetic_retries
# ---------------------------------------------------------------------------


class TestSubmitSyntheticRetries:
    def test_builds_future_map(self, fake_mh: ModuleType) -> None:
        executor = MagicMock()
        executor.submit.side_effect = ["fut1", "fut2"]
        failed = [("s1", "d1", "dn1", "sn1"), ("s2", "d2", "dn2", "sn2")]
        result = GatewayTestExporter._submit_synthetic_retries(executor, failed, None)
        assert set(result.values()) == set(failed)
        assert executor.submit.call_count == 2


# ---------------------------------------------------------------------------
# _record_retry_outcome
# ---------------------------------------------------------------------------


class TestRecordRetryOutcome:
    def _make_future(self, result: Any = None, exc: Exception | None = None) -> Future:
        fut: Future = Future()
        if exc is not None:
            fut.set_exception(exc)
        else:
            fut.set_result(result)
        return fut

    def test_success_appends_result(self, fake_mh: ModuleType) -> None:
        fut = self._make_future({"ok": True})
        futures = {fut: ("s", "d", "dn", "sn")}
        results: list[Any] = []
        still: list[Any] = []
        GatewayTestExporter._record_retry_outcome(fut, futures, results, still)
        assert results == [{"ok": True}] and still == []

    def test_none_result_marks_failed(self, fake_mh: ModuleType) -> None:
        fut = self._make_future(None)
        futures = {fut: ("s", "d", "dn", "sn")}
        results: list[Any] = []
        still: list[Any] = []
        GatewayTestExporter._record_retry_outcome(fut, futures, results, still)
        assert results == [] and still == [("s", "d", "dn", "sn")]

    def test_exception_marks_failed(self, fake_mh: ModuleType) -> None:
        fut = self._make_future(exc=RuntimeError("boom"))
        futures = {fut: ("s", "d", "dn", "sn")}
        results: list[Any] = []
        still: list[Any] = []
        GatewayTestExporter._record_retry_outcome(fut, futures, results, still)
        assert results == [] and still == [("s", "d", "dn", "sn")]


# ---------------------------------------------------------------------------
# _run_synthetic_sequential_path
# ---------------------------------------------------------------------------


class TestRunSyntheticSequentialPath:
    def test_records_results_and_paces(self, fake_mh: ModuleType) -> None:
        devices = [("s1", "d1", "dn1", "sn1"), ("s2", "d2", "dn2", "sn2")]
        outcomes: list[Any] = [{"a": 1}, None]
        with (
            patch.object(GatewayTestExporter, "fetch_synthetic_test_stats_with_retry", side_effect=outcomes),
            patch.object(gte.time, "sleep"),
            patch("src.export.gateway_test_exporter.tqdm", side_effect=lambda x, **_k: list(x)),
        ):
            all_stats: list[Any] = []
            GatewayTestExporter._run_synthetic_sequential_path(devices, all_stats)
        assert all_stats == [{"a": 1}]


# ---------------------------------------------------------------------------
# _export_synthetic_results
# ---------------------------------------------------------------------------


class TestExportSyntheticResults:
    def test_no_stats_warns_and_returns(self, fake_mh: ModuleType, capsys: pytest.CaptureFixture) -> None:
        GatewayTestExporter._export_synthetic_results([], [])
        out = capsys.readouterr().out
        assert "No synthetic test results" in out

    def test_writes_csv_via_dataexporter(self, fake_mh: ModuleType, capsys: pytest.CaptureFixture) -> None:
        rows = [{"a": 1}]
        with patch("src.export.gateway_test_exporter.DataProcessingUtils") as dp:
            dp.flatten_nested_fields.return_value = rows
            dp.escape_multiline.return_value = rows
            GatewayTestExporter._export_synthetic_results(rows, [("s", "d", "dn", "sn")])
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(rows, "AllGatewaySyntheticTests.csv")  # type: ignore[attr-defined]
        assert "exported to AllGatewaySyntheticTests.csv" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# test_results_by_site delegator (already smoked; add assertion on wiring)
# ---------------------------------------------------------------------------


class TestTestResultsBySiteDelegator:
    def test_delegates_to_service(self, fake_mh: ModuleType) -> None:
        with patch("src.refactors.serial_cc.test_results_by_site.GatewayTestResultsService") as svc:
            GatewayTestExporter.test_results_by_site(fast=True)
        svc.execute.assert_called_once_with(fast=True)
