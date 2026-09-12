"""Wave 5 P2 coverage for src/gateway/overrides/device_data_fetcher.py (initiative #1018).

Covers all static methods of ``DeviceDataFetcher``:
- ``fetch_all`` routes to fast vs sequential based on size + fast flag.
- ``_fetch_fast`` delegates to _deps.execute_fn and merges via _build_cache_from_results.
- ``_build_cache_from_results`` merges successes + failures into a single cache dict.
- ``_worker_fetch_device_data`` unpacks device_info tuple and calls the two fetchers under the semaphore.
- ``_fetch_sequential`` walks devices one at a time and populates the cache.
- ``_fetch_port_configs`` returns port_config on success, {} on API exception.
- ``_fetch_interface_stats`` returns if_stat on success, {} on API exception; delegates warning to helper.
- ``_log_stats_failure`` branches on '403'/'Forbidden' vs generic message.

All API dependencies are injected via _deps module-level slots which we patch directly.
No live network, no MistHelper import touched. MagicMock(spec=...) mandatory on stubs.
"""

from __future__ import annotations  # WHY: PEP 604 unions in test type hints.

import logging  # WHY: caplog verification of structured warning/info/debug lines.
import threading  # WHY: real semaphore instance (spec=threading.Semaphore) for the pool worker.
from typing import Any  # WHY: dict[str, Any] annotations mirroring the SUT.
from unittest.mock import MagicMock, patch  # WHY: mandatory spec= mocks + patch decorators.

import pytest  # WHY: fixtures + parametrize.

from src.gateway.overrides import _deps  # WHY: patch module-level DI slots directly.
from src.gateway.overrides.device_data_fetcher import DeviceDataFetcher  # WHY: SUT direct import.


class TestFetchAll:
    """``fetch_all`` chooses fast for len>5 + fast=True else sequential."""

    def test_fast_mode_above_threshold_calls_fast(self) -> None:
        """fast=True and >5 devices routes to _fetch_fast."""
        devices: dict[str, dict[str, Any]] = {  # WHY: 6 devices exceeds the >5 threshold in SUT.
            f"d{n}": {"device_name": f"n{n}", "site_id": "s"} for n in range(6)
        }
        with (
            patch.object(  # WHY: isolate fast-mode branch by stubbing the helper.
                DeviceDataFetcher, "_fetch_fast", return_value={"d0": ({}, {})}
            ) as fake_fast,
            patch.object(DeviceDataFetcher, "_fetch_sequential") as fake_seq,
        ):
            result = DeviceDataFetcher.fetch_all(devices, fast=True)

        fake_fast.assert_called_once_with(devices)  # WHY: fast branch selected.
        fake_seq.assert_not_called()  # WHY: sequential must not run in fast branch.
        assert result == {"d0": ({}, {})}  # WHY: returns whatever fast helper produced.

    def test_fast_mode_below_threshold_calls_sequential(self) -> None:
        """fast=True but only 5 devices routes to _fetch_sequential (threshold is >5, not >=5)."""
        devices: dict[str, dict[str, Any]] = {
            f"d{n}": {"device_name": f"n{n}", "site_id": "s"} for n in range(5)
        }  # WHY: exactly at threshold means sequential branch.
        with (
            patch.object(DeviceDataFetcher, "_fetch_fast") as fake_fast,
            patch.object(DeviceDataFetcher, "_fetch_sequential", return_value={}) as fake_seq,
        ):
            DeviceDataFetcher.fetch_all(devices, fast=True)

        fake_fast.assert_not_called()  # WHY: fast branch skipped below threshold.
        fake_seq.assert_called_once_with(devices)  # WHY: sequential branch chosen.

    def test_non_fast_always_sequential(self) -> None:
        """fast=False always routes to sequential regardless of size."""
        devices: dict[str, dict[str, Any]] = {
            f"d{n}": {"device_name": f"n{n}", "site_id": "s"} for n in range(10)
        }  # WHY: large batch but non-fast → sequential.
        with (
            patch.object(DeviceDataFetcher, "_fetch_fast") as fake_fast,
            patch.object(DeviceDataFetcher, "_fetch_sequential", return_value={}) as fake_seq,
        ):
            DeviceDataFetcher.fetch_all(devices, fast=False)

        fake_fast.assert_not_called()  # WHY: fast=False skips fast branch.
        fake_seq.assert_called_once_with(devices)  # WHY: sequential branch used.

    def test_fetch_all_logs_and_returns_cache(self, caplog: pytest.LogCaptureFixture) -> None:
        """fetch_all emits info banner and debug summary and returns the helper's cache verbatim."""
        devices: dict[str, dict[str, Any]] = {"d0": {"device_name": "n", "site_id": "s"}}
        with patch.object(DeviceDataFetcher, "_fetch_sequential", return_value={"d0": ({"p": 1}, {"i": 2})}):
            with caplog.at_level(logging.DEBUG):
                result = DeviceDataFetcher.fetch_all(devices, fast=False)
        assert result == {"d0": ({"p": 1}, {"i": 2})}  # WHY: returned verbatim.
        assert "Fetching live device data for 1 devices" in caplog.text  # WHY: pre-action info log.
        assert "Live data cache populated for 1 devices" in caplog.text  # WHY: post-action debug log.


class TestFetchFast:
    """``_fetch_fast`` delegates to _deps.execute_fn and merges results."""

    def test_delegates_to_execute_fn_and_returns_cache(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """execute_fn is called with worker + retry=None; return values are merged into the cache."""
        successful = [("d1", {"port_a": 1}, {"if_a": 2})]  # WHY: one successful worker result tuple.
        failed: list[tuple[str, Any]] = [("d2", "err")]  # WHY: one failed device tuple.
        fake_execute = MagicMock(return_value=(successful, failed))  # WHY: replaces _deps.execute_fn.
        monkeypatch.setattr(_deps, "execute_fn", fake_execute)

        devices: dict[str, dict[str, Any]] = {
            "d1": {"device_name": "n1", "site_id": "s1"},
            "d2": {"device_name": "n2", "site_id": "s2"},
        }
        with caplog.at_level(logging.INFO):
            result = DeviceDataFetcher._fetch_fast(devices)

        assert result == {"d1": ({"port_a": 1}, {"if_a": 2}), "d2": ({}, {})}  # WHY: successes + fail blanks.
        call_kwargs = fake_execute.call_args.kwargs  # WHY: assert on kwargs shape used by SUT.
        assert call_kwargs["worker_function"] is DeviceDataFetcher._worker_fetch_device_data
        assert call_kwargs["batch_description"] == "override devices"
        assert call_kwargs["retry_function"] is None
        assert call_kwargs["work_items"] == list(devices.items())
        assert "Fetched data for 1/2 devices" in caplog.text  # WHY: legacy summary log preserved.


class TestBuildCacheFromResults:
    """``_build_cache_from_results`` merges successes + failed devices into unified cache."""

    def test_merges_successes_and_failures(self) -> None:
        """Successes stored as-is; failed devices get empty tuple placeholder."""
        successes = [("d1", {"p": 1}, {"i": 2}), ("d2", {"p": 3}, {"i": 4})]  # WHY: two successful workers.
        failures: list[tuple[str, Any]] = [("d3", "err"), ("d4", "err2")]  # WHY: two failed devices.
        result = DeviceDataFetcher._build_cache_from_results(successes, failures)
        assert result == {
            "d1": ({"p": 1}, {"i": 2}),
            "d2": ({"p": 3}, {"i": 4}),
            "d3": ({}, {}),
            "d4": ({}, {}),
        }  # WHY: all 4 devices present; failures get blank tuples so third pass still emits rows.

    def test_empty_inputs_return_empty_cache(self) -> None:
        """No successes and no failures → empty cache dict."""
        assert DeviceDataFetcher._build_cache_from_results([], []) == {}


class TestWorkerFetchDeviceData:
    """``_worker_fetch_device_data`` unpacks tuple and calls two fetch helpers under the semaphore."""

    def test_calls_both_fetchers_and_returns_tuple(self) -> None:
        """Both fetchers are called with (site_id, device_id, device_name) and return values are packed."""
        device_info = ("dev-42", {"device_name": "alpha", "site_id": "site-x"})  # WHY: exact SUT tuple shape.
        semaphore = MagicMock(spec=threading.Semaphore)  # WHY: mandatory spec= mock for context manager.
        semaphore.__enter__ = MagicMock(return_value=None)  # WHY: SUT uses `with connection_semaphore:`.
        semaphore.__exit__ = MagicMock(return_value=False)

        with (
            patch.object(DeviceDataFetcher, "_fetch_port_configs", return_value={"p1": {}}) as fake_pc,
            patch.object(DeviceDataFetcher, "_fetch_interface_stats", return_value={"i1": {}}) as fake_if,
        ):
            result = DeviceDataFetcher._worker_fetch_device_data(device_info, semaphore)

        assert result == ("dev-42", {"p1": {}}, {"i1": {}})  # WHY: SUT-mandated tuple layout.
        fake_pc.assert_called_once_with("site-x", "dev-42", "alpha")  # WHY: arg order + values.
        fake_if.assert_called_once_with("site-x", "dev-42", "alpha")  # WHY: same identifiers passed through.
        semaphore.__enter__.assert_called_once()  # WHY: slot was acquired.
        semaphore.__exit__.assert_called_once()  # WHY: slot was released.


class TestFetchSequential:
    """``_fetch_sequential`` iterates devices, calls two fetchers each, populates cache."""

    def test_populates_cache_from_two_devices(self, caplog: pytest.LogCaptureFixture) -> None:
        """Two devices produce two cache entries with (port_config, if_stat) tuples."""
        devices: dict[str, dict[str, Any]] = {
            "d1": {"device_name": "n1", "site_id": "s1"},
            "d2": {"device_name": "n2", "site_id": "s2"},
        }
        with (
            patch.object(DeviceDataFetcher, "_fetch_port_configs", side_effect=[{"p": 1}, {"p": 2}]),
            patch.object(DeviceDataFetcher, "_fetch_interface_stats", side_effect=[{"i": 1}, {"i": 2}]),
        ):
            with caplog.at_level(logging.INFO):
                result = DeviceDataFetcher._fetch_sequential(devices)

        assert result == {"d1": ({"p": 1}, {"i": 1}), "d2": ({"p": 2}, {"i": 2})}  # WHY: per-device cache.
        assert "Sequential fetch for 2 devices" in caplog.text  # WHY: pre-action info log.


def _make_api_stub(
    get_device_return: Any = None,
    get_stats_return: Any = None,
    get_device_exc: BaseException | None = None,
    get_stats_exc: BaseException | None = None,
) -> MagicMock:
    """Build a MagicMock scaffold matching the mistapi.api.v1.sites.* chain used by the SUT.

    Chained attribute access requires an unspec'd MagicMock; we compensate by scoping
    each method's behavior explicitly so tests remain contract-focused.
    """
    fake = MagicMock()  # WHY: unspec'd because we mock the full mistapi module namespace.
    if get_device_exc is not None:
        fake.api.v1.sites.devices.getSiteDevice.side_effect = get_device_exc  # WHY: raise on device fetch.
    else:
        fake.api.v1.sites.devices.getSiteDevice.return_value = get_device_return  # WHY: return canned response.
    if get_stats_exc is not None:
        fake.api.v1.sites.stats.getSiteDeviceStats.side_effect = get_stats_exc  # WHY: raise on stats fetch.
    else:
        fake.api.v1.sites.stats.getSiteDeviceStats.return_value = get_stats_return  # WHY: return canned response.
    return fake


class TestFetchPortConfigs:
    """``_fetch_port_configs`` returns port_config on success, {} on exception."""

    def test_success_returns_port_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Successful API call returns the port_config dict."""
        fake_resp = MagicMock(spec=object)  # WHY: opaque response object; only .data is used.
        fake_resp.data = {"port_config": {"ge-0/0/0": {"role": "wan"}}}  # WHY: API .data shape.
        monkeypatch.setattr(_deps, "mistapi", _make_api_stub(get_device_return=fake_resp))
        monkeypatch.setattr(_deps, "apisession", MagicMock(spec=object))  # WHY: opaque session passthrough.

        result = DeviceDataFetcher._fetch_port_configs("site-1", "dev-1", "name-1")
        assert result == {"ge-0/0/0": {"role": "wan"}}  # WHY: SUT unwraps .data -> .port_config.

    def test_missing_port_config_key_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing port_config key still returns an empty dict (not KeyError)."""
        fake_resp = MagicMock(spec=object)  # WHY: response object with no port_config key.
        fake_resp.data = {}  # WHY: no port_config key.
        monkeypatch.setattr(_deps, "mistapi", _make_api_stub(get_device_return=fake_resp))
        monkeypatch.setattr(_deps, "apisession", MagicMock(spec=object))

        assert DeviceDataFetcher._fetch_port_configs("s", "d", "n") == {}  # WHY: dict.get default.

    def test_exception_returns_empty_and_warns(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """API exception is swallowed; warning is logged; empty dict returned."""
        monkeypatch.setattr(_deps, "mistapi", _make_api_stub(get_device_exc=RuntimeError("boom")))
        monkeypatch.setattr(_deps, "apisession", MagicMock(spec=object))

        with caplog.at_level(logging.WARNING):
            result = DeviceDataFetcher._fetch_port_configs("s", "d", "n")
        assert result == {}  # WHY: SUT contract: no crash, empty on failure.
        assert "Could not fetch device config for n (d): boom" in caplog.text  # WHY: legacy format.


class TestFetchInterfaceStats:
    """``_fetch_interface_stats`` returns if_stat on success, {} on exception (via _log_stats_failure)."""

    def test_success_returns_if_stat(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Successful stats API call returns the if_stat dict."""
        fake_resp = MagicMock(spec=object)  # WHY: opaque response object; only .data is used.
        fake_resp.data = {"if_stat": {"ge-0/0/0": {"up": True}}}  # WHY: API .data shape.
        monkeypatch.setattr(_deps, "mistapi", _make_api_stub(get_stats_return=fake_resp))
        monkeypatch.setattr(_deps, "apisession", MagicMock(spec=object))

        assert DeviceDataFetcher._fetch_interface_stats("s", "d", "n") == {"ge-0/0/0": {"up": True}}

    def test_missing_if_stat_key_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing if_stat key returns empty dict."""
        fake_resp = MagicMock(spec=object)  # WHY: opaque response object with no if_stat key.
        fake_resp.data = {}  # WHY: no if_stat key.
        monkeypatch.setattr(_deps, "mistapi", _make_api_stub(get_stats_return=fake_resp))
        monkeypatch.setattr(_deps, "apisession", MagicMock(spec=object))

        assert DeviceDataFetcher._fetch_interface_stats("s", "d", "n") == {}

    def test_exception_delegates_to_log_helper_and_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Exception path calls the specialized _log_stats_failure helper and returns {}."""
        exc = RuntimeError("network down")  # WHY: reference kept so we can assert delegation arg.
        monkeypatch.setattr(_deps, "mistapi", _make_api_stub(get_stats_exc=exc))
        monkeypatch.setattr(_deps, "apisession", MagicMock(spec=object))

        with patch.object(DeviceDataFetcher, "_log_stats_failure") as fake_log:
            result = DeviceDataFetcher._fetch_interface_stats("s", "d", "n")

        assert result == {}  # WHY: empty on failure.
        fake_log.assert_called_once_with("n", "d", exc)  # WHY: delegation contract.


class TestLogStatsFailure:
    """``_log_stats_failure`` branches on '403'/'Forbidden' vs generic message."""

    def test_403_message_uses_permission_specific_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """A '403' substring routes to the permission-specific warning line."""
        exc = RuntimeError("HTTP 403 error")  # WHY: contains '403'.
        with caplog.at_level(logging.WARNING):
            DeviceDataFetcher._log_stats_failure("alpha", "dev-1", exc)
        assert "Insufficient permissions" in caplog.text  # WHY: permission-specific message.
        assert "alpha" in caplog.text  # WHY: device name interpolated.
        assert "dev-1" in caplog.text  # WHY: device id interpolated.

    def test_forbidden_message_uses_permission_specific_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """A 'Forbidden' substring routes to the permission-specific warning line."""
        exc = RuntimeError("Access Forbidden by policy")  # WHY: contains 'Forbidden'.
        with caplog.at_level(logging.WARNING):
            DeviceDataFetcher._log_stats_failure("beta", "dev-2", exc)
        assert "Insufficient permissions" in caplog.text  # WHY: same specific branch.

    def test_generic_exception_uses_generic_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Non-permission exceptions fall through to the generic legacy warning line."""
        exc = RuntimeError("connection reset")  # WHY: neither '403' nor 'Forbidden'.
        with caplog.at_level(logging.WARNING):
            DeviceDataFetcher._log_stats_failure("gamma", "dev-3", exc)
        assert "Could not fetch device stats for gamma (dev-3): connection reset" in caplog.text
        assert "Insufficient permissions" not in caplog.text  # WHY: specific branch suppressed.
