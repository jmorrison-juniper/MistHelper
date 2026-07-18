"""Unit tests for ``src.export.org_device_stats_exporter``.

Why:
    #878 tranche 20 -- un-omit ``org_device_stats_exporter.py`` from the
    coverage configuration and pin behavior via a full test suite so future
    refactors of Menu 13-16 exporters (device stats, port stats, VPN peer
    stats, VC stats) cannot silently regress. Covers cache-hit helpers,
    site-loading fallback, fast-mode retry/flatten helpers, save/summary
    helpers, and orchestration entry points including the ``switch_vc_stats``
    delegation.
"""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a stub ``MistHelper`` module in ``sys.modules``.

    Why:
        ``OrgDeviceStatsExporter`` reaches out to ``mh.APIDataFetcher``,
        ``mh.mistapi``, ``mh.PROGRESS_EMITTER``, cache/config utilities, and
        several ``FAST_MODE_*`` constants via a lazy
        ``importlib.import_module("MistHelper")`` call. The real MistHelper
        module has heavy side effects and network hooks, so tests replace it
        with a lightweight ``ModuleType`` populated with ``MagicMock``
        stand-ins plus the concrete constants the code compares against.

    Returns:
        The stubbed ``MistHelper`` module (also registered in ``sys.modules``).
    """
    mh = ModuleType("MistHelper")
    mh.CSV_FRESHNESS_MINUTES = 60
    mh.PROGRESS_EMITTER = MagicMock()
    mh.mistapi = MagicMock()
    mh.apisession = MagicMock()
    mh.APIDataFetcher = MagicMock()
    mh.ProgressContext = MagicMock()
    mh.OrgSiteExporter = MagicMock()
    mh.CacheUtils = MagicMock()
    mh.FilePathUtils = MagicMock()
    mh.DataExporter = MagicMock()
    mh.ConfigUtils = MagicMock()
    mh.ConnectionPoolExecutor = MagicMock()
    mh.FAST_MODE_MAX_RETRIES = 2
    mh.FAST_MODE_RETRY_DELAY = 0.01
    mh.FAST_MODE_RETRY_THREADS = 2
    mh.FastModeBackoffMultiplier = SimpleNamespace(VALUE=2)
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


# ---------------------------------------------------------------------------
# Cache-hit helper tests (three near-identical helpers)
# ---------------------------------------------------------------------------


class TestDeviceStatsCacheHit:
    """Cover the five branches of ``_device_stats_cache_hit``."""

    def test_not_fast_returns_false(self, fake_mh):
        """Non-fast mode should bypass all cache logic."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        assert OrgDeviceStatsExporter._device_stats_cache_hit("x.csv", False) is False

    def test_no_file_returns_false(self, fake_mh):
        """Fast mode without an existing cache file should return False."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch("os.path.exists", return_value=False):
            assert OrgDeviceStatsExporter._device_stats_cache_hit("x.csv", True) is False

    def test_fresh_cache_returns_true(self, fake_mh, capsys):
        """Fresh cache should return True and emit user-visible cache-hit notice."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=1000.0),
            patch("src.export.org_device_stats_exporter.time.time", return_value=1000.0),
        ):
            assert OrgDeviceStatsExporter._device_stats_cache_hit("x.csv", True) is True
        assert "Fast mode" in capsys.readouterr().out

    def test_stale_cache_returns_false(self, fake_mh):
        """Stale cache should return False without printing."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=0.0),
            patch("src.export.org_device_stats_exporter.time.time", return_value=1e9),
        ):
            assert OrgDeviceStatsExporter._device_stats_cache_hit("x.csv", True) is False

    def test_exception_returns_false(self, fake_mh):
        """Freshness-check exceptions should not propagate."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", side_effect=OSError("boom")),
        ):
            assert OrgDeviceStatsExporter._device_stats_cache_hit("x.csv", True) is False


class TestPortStatsCacheHit:
    """Cover the five branches of ``_port_stats_cache_hit``."""

    def test_not_fast(self, fake_mh):
        """Non-fast mode should bypass port-stats cache logic."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        assert OrgDeviceStatsExporter._port_stats_cache_hit("x.csv", False) is False

    def test_no_file(self, fake_mh):
        """Missing cache file returns False."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch("os.path.exists", return_value=False):
            assert OrgDeviceStatsExporter._port_stats_cache_hit("x.csv", True) is False

    def test_fresh(self, fake_mh, capsys):
        """Fresh cache returns True and prints operator-facing notice."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=100.0),
            patch("src.export.org_device_stats_exporter.time.time", return_value=100.0),
        ):
            assert OrgDeviceStatsExporter._port_stats_cache_hit("x.csv", True) is True
        assert "cached" in capsys.readouterr().out

    def test_stale(self, fake_mh):
        """Stale cache returns False."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=0.0),
            patch("src.export.org_device_stats_exporter.time.time", return_value=1e9),
        ):
            assert OrgDeviceStatsExporter._port_stats_cache_hit("x.csv", True) is False

    def test_exception(self, fake_mh):
        """Freshness-check exceptions swallowed."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", side_effect=OSError("nope")),
        ):
            assert OrgDeviceStatsExporter._port_stats_cache_hit("x.csv", True) is False


class TestVpnPeerStatsCacheHit:
    """Cover the five branches of ``_vpn_peer_stats_cache_hit``."""

    def test_not_fast(self, fake_mh):
        """Non-fast mode returns False."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        assert OrgDeviceStatsExporter._vpn_peer_stats_cache_hit("x.csv", False) is False

    def test_no_file(self, fake_mh):
        """No file yet returns False."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch("os.path.exists", return_value=False):
            assert OrgDeviceStatsExporter._vpn_peer_stats_cache_hit("x.csv", True) is False

    def test_fresh(self, fake_mh, capsys):
        """Fresh cache returns True."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=500.0),
            patch("src.export.org_device_stats_exporter.time.time", return_value=500.0),
        ):
            assert OrgDeviceStatsExporter._vpn_peer_stats_cache_hit("x.csv", True) is True
        assert "cached" in capsys.readouterr().out

    def test_stale(self, fake_mh):
        """Stale cache returns False."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=0.0),
            patch("src.export.org_device_stats_exporter.time.time", return_value=1e9),
        ):
            assert OrgDeviceStatsExporter._vpn_peer_stats_cache_hit("x.csv", True) is False

    def test_exception(self, fake_mh):
        """Exception path swallowed."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", side_effect=OSError("bad")),
        ):
            assert OrgDeviceStatsExporter._vpn_peer_stats_cache_hit("x.csv", True) is False


# ---------------------------------------------------------------------------
# device_stats + vpn_peer_stats entry points
# ---------------------------------------------------------------------------


class TestDeviceStats:
    """Cover ``device_stats`` cache-hit and emitter branches."""

    def test_cache_hit_returns_early(self, fake_mh):
        """Fresh cache should skip API fetch and emitter side effects."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch.object(OrgDeviceStatsExporter, "_device_stats_cache_hit", return_value=True):
            OrgDeviceStatsExporter.device_stats(fast=True)
        fake_mh.APIDataFetcher.assert_not_called()

    def test_full_path_with_emitter(self, fake_mh):
        """Cache miss should invoke fetcher and both emitter callbacks."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        emitter = fake_mh.PROGRESS_EMITTER
        with patch.object(OrgDeviceStatsExporter, "_device_stats_cache_hit", return_value=False):
            OrgDeviceStatsExporter.device_stats(fast=False)
        fake_mh.APIDataFetcher.assert_called_once()
        emitter.emit_progress_start.assert_called_once()
        emitter.emit_progress_complete.assert_called_once()

    def test_full_path_without_emitter(self, fake_mh):
        """Missing emitter should not raise."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fake_mh.PROGRESS_EMITTER = None
        with patch.object(OrgDeviceStatsExporter, "_device_stats_cache_hit", return_value=False):
            OrgDeviceStatsExporter.device_stats(fast=False)
        fake_mh.APIDataFetcher.assert_called_once()


class TestVpnPeerStats:
    """Cover ``vpn_peer_stats`` cache-hit and emitter branches."""

    def test_cache_hit(self, fake_mh):
        """Fresh cache short-circuits VPN peer stats fetch."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch.object(OrgDeviceStatsExporter, "_vpn_peer_stats_cache_hit", return_value=True):
            OrgDeviceStatsExporter.vpn_peer_stats(fast=True)
        fake_mh.APIDataFetcher.assert_not_called()

    def test_full_path_with_emitter(self, fake_mh):
        """Cache miss with emitter invokes both progress callbacks."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        emitter = fake_mh.PROGRESS_EMITTER
        with patch.object(OrgDeviceStatsExporter, "_vpn_peer_stats_cache_hit", return_value=False):
            OrgDeviceStatsExporter.vpn_peer_stats(fast=False)
        fake_mh.APIDataFetcher.assert_called_once()
        emitter.emit_progress_start.assert_called_once()
        emitter.emit_progress_complete.assert_called_once()

    def test_full_path_without_emitter(self, fake_mh):
        """Missing emitter should not raise on VPN peer stats path."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fake_mh.PROGRESS_EMITTER = None
        with patch.object(OrgDeviceStatsExporter, "_vpn_peer_stats_cache_hit", return_value=False):
            OrgDeviceStatsExporter.vpn_peer_stats(fast=False)
        fake_mh.APIDataFetcher.assert_called_once()


# ---------------------------------------------------------------------------
# device_port_stats + fast-mode delegation
# ---------------------------------------------------------------------------


class TestDevicePortStats:
    """Cover ``device_port_stats`` cache/fast/normal branches."""

    def test_cache_hit(self, fake_mh):
        """Fresh cache should skip fetcher and fast-mode path."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch.object(OrgDeviceStatsExporter, "_port_stats_cache_hit", return_value=True):
            OrgDeviceStatsExporter.device_port_stats(fast=True)
        fake_mh.APIDataFetcher.assert_not_called()

    def test_fast_mode_delegates(self, fake_mh):
        """Fast mode should delegate to ``_run_fast_device_port_stats``."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch.object(OrgDeviceStatsExporter, "_port_stats_cache_hit", return_value=False),
            patch.object(OrgDeviceStatsExporter, "_run_fast_device_port_stats") as run_fast,
        ):
            OrgDeviceStatsExporter.device_port_stats(fast=True)
        run_fast.assert_called_once_with("OrgDevicePortStats.csv")
        fake_mh.APIDataFetcher.assert_not_called()

    def test_normal_mode_uses_api_fetcher(self, fake_mh):
        """Non-fast path issues single org-level paginated fetch."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch.object(OrgDeviceStatsExporter, "_port_stats_cache_hit", return_value=False):
            OrgDeviceStatsExporter.device_port_stats(fast=False)
        fake_mh.APIDataFetcher.assert_called_once()


# ---------------------------------------------------------------------------
# switch_vc_stats delegation
# ---------------------------------------------------------------------------


class TestSwitchVcStats:
    """Verify delegation to ``SwitchVcStatsService.execute``."""

    def test_delegates_to_service(self, fake_mh):
        """``switch_vc_stats`` should call the extracted service exactly once."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch("src.refactors.serial_cc.switch_vc_stats.SwitchVcStatsService") as svc:
            OrgDeviceStatsExporter.switch_vc_stats()
        svc.execute.assert_called_once_with()


# ---------------------------------------------------------------------------
# Site-loading helpers
# ---------------------------------------------------------------------------


class TestLoadPortStatsSitesFromApi:
    """Cover ``_load_port_stats_sites_from_api`` normalization + filtering."""

    def test_normalizes_and_skips_missing_id(self, fake_mh):
        """Sites lacking id should be filtered; others normalized to tuples."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fake_mh.mistapi.api.v1.orgs.sites.listOrgSites.return_value = MagicMock()
        fake_mh.mistapi.get_all.return_value = [
            {"id": "s1", "name": "Site1"},
            {"id": None, "name": "SkipMe"},  # Filtered out
            {"id": "s2"},  # Name defaults to Unknown
        ]
        result = OrgDeviceStatsExporter._load_port_stats_sites_from_api("org-1")
        assert result == [("s1", "Site1"), ("s2", "Unknown")]

    def test_empty_sites(self, fake_mh):
        """Empty API response should return empty list without raising."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fake_mh.mistapi.get_all.return_value = []
        assert OrgDeviceStatsExporter._load_port_stats_sites_from_api("org-1") == []


class TestLogFirstSiteSample:
    """Empty vs populated branches."""

    def test_populated(self, fake_mh):
        """Populated list logs first entry without raising."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        OrgDeviceStatsExporter._log_first_site_sample([("s1", "n1"), ("s2", "n2")])

    def test_empty(self, fake_mh):
        """Empty list still logs a placeholder without raising."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        OrgDeviceStatsExporter._log_first_site_sample([])


class TestLoadSitesFromCachedCsv:
    """Cover cache success + exception fallback."""

    def test_success(self, fake_mh, tmp_path):
        """Cached CSV should be parsed into tuple list."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        csv_path = tmp_path / "SiteList.csv"
        csv_path.write_text("id,name\ns1,Site1\ns2,Site2\n,SkipMe\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(csv_path)
        result = OrgDeviceStatsExporter._load_sites_from_cached_csv()
        assert result == [("s1", "Site1"), ("s2", "Site2")]

    def test_exception_returns_none(self, fake_mh):
        """Cache read failure should return None to trigger API fallback."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fake_mh.CacheUtils.check_and_generate_csv.side_effect = RuntimeError("cache oops")
        assert OrgDeviceStatsExporter._load_sites_from_cached_csv() is None


class TestLoadPortStatsSites:
    """Cover cache-hit vs API-fallback dispatch."""

    def test_cache_hit(self, fake_mh):
        """Cache returns list -> use it directly."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch.object(
            OrgDeviceStatsExporter,
            "_load_sites_from_cached_csv",
            return_value=[("s1", "n1")],
        ):
            assert OrgDeviceStatsExporter._load_port_stats_sites("org") == [("s1", "n1")]

    def test_api_fallback(self, fake_mh):
        """Cache returns None -> fall back to API loader."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch.object(OrgDeviceStatsExporter, "_load_sites_from_cached_csv", return_value=None),
            patch.object(
                OrgDeviceStatsExporter,
                "_load_port_stats_sites_from_api",
                return_value=[("s2", "n2")],
            ),
        ):
            assert OrgDeviceStatsExporter._load_port_stats_sites("org") == [("s2", "n2")]


# ---------------------------------------------------------------------------
# Fetch / retry / process helpers
# ---------------------------------------------------------------------------


class TestAttemptSitePortStatsFetch:
    """Cover list vs non-list defensive branches."""

    def test_list_annotates_rows(self, fake_mh):
        """List result should be annotated with site_id/site_name."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fake_mh.mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts.return_value = MagicMock()
        fake_mh.mistapi.get_all.return_value = [{"port": "ge-0/0/0"}, {"port": "ge-0/0/1"}]
        sem = MagicMock()
        sem.__enter__ = MagicMock(return_value=None)
        sem.__exit__ = MagicMock(return_value=None)
        result = OrgDeviceStatsExporter._attempt_site_port_stats_fetch("s1", "Site1", sem)
        assert result == [
            {"port": "ge-0/0/0", "site_id": "s1", "site_name": "Site1"},
            {"port": "ge-0/0/1", "site_id": "s1", "site_name": "Site1"},
        ]

    def test_non_list_returns_empty(self, fake_mh):
        """Non-list defensive path returns empty and logs error."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fake_mh.mistapi.get_all.return_value = {"unexpected": "dict"}
        sem = MagicMock()
        sem.__enter__ = MagicMock(return_value=None)
        sem.__exit__ = MagicMock(return_value=None)
        assert OrgDeviceStatsExporter._attempt_site_port_stats_fetch("s1", "Site1", sem) == []


class TestHandleSitePortStatsRetry:
    """Cover retries-remain vs no-more-retries branches."""

    def test_retries_remain(self, fake_mh):
        """Attempt < max should return True after sleeping."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch("src.export.org_device_stats_exporter.time.sleep") as sleep_mock:
            assert OrgDeviceStatsExporter._handle_site_port_stats_retry(0, "Site1", RuntimeError("x")) is True
        sleep_mock.assert_called_once()

    def test_no_more_retries(self, fake_mh):
        """Attempt at max returns False without sleeping."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with patch("src.export.org_device_stats_exporter.time.sleep") as sleep_mock:
            assert OrgDeviceStatsExporter._handle_site_port_stats_retry(2, "Site1", RuntimeError("x")) is False
        sleep_mock.assert_not_called()


class TestFetchSitePortStats:
    """Cover first-try success, retry-success, and final-failure branches."""

    def test_first_try_success(self, fake_mh):
        """First-try success should return rows without any retry logging path."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        sem = MagicMock()
        with patch.object(
            OrgDeviceStatsExporter,
            "_attempt_site_port_stats_fetch",
            return_value=[{"port": "x"}],
        ):
            result = OrgDeviceStatsExporter._fetch_site_port_stats(("s1", "Site1"), sem)
        assert result == [{"port": "x"}]

    def test_retry_then_success(self, fake_mh):
        """Retry that eventually succeeds should return rows and log info."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        sem = MagicMock()
        attempts = [RuntimeError("try1"), [{"port": "y"}]]

        def side_effect(*_a, **_kw):
            val = attempts.pop(0)
            if isinstance(val, Exception):
                raise val
            return val

        with (
            patch.object(OrgDeviceStatsExporter, "_attempt_site_port_stats_fetch", side_effect=side_effect),
            patch("src.export.org_device_stats_exporter.time.sleep"),
        ):
            result = OrgDeviceStatsExporter._fetch_site_port_stats(("s1", "Site1"), sem)
        assert result == [{"port": "y"}]

    def test_final_failure_returns_empty(self, fake_mh):
        """All retries failing should return empty list."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        sem = MagicMock()
        with (
            patch.object(
                OrgDeviceStatsExporter,
                "_attempt_site_port_stats_fetch",
                side_effect=RuntimeError("perma"),
            ),
            patch("src.export.org_device_stats_exporter.time.sleep"),
        ):
            result = OrgDeviceStatsExporter._fetch_site_port_stats(("s1", "Site1"), sem)
        assert result == []


class TestProcessRetryFuture:
    """Cover success, empty, and exception branches."""

    def test_success(self, fake_mh):
        """Non-empty future.result should extend retry_results."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fut = MagicMock()
        fut.result.return_value = [{"row": 1}]
        retry_futures = {fut: ("s1", "Site1")}
        retry_results: list = []
        still_failed: list = []
        OrgDeviceStatsExporter._process_retry_future(fut, retry_futures, retry_results, still_failed)
        assert retry_results == [{"row": 1}]
        assert still_failed == []

    def test_empty(self, fake_mh):
        """Empty result appends site to still_failed."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fut = MagicMock()
        fut.result.return_value = []
        retry_futures = {fut: ("s1", "Site1")}
        retry_results: list = []
        still_failed: list = []
        OrgDeviceStatsExporter._process_retry_future(fut, retry_futures, retry_results, still_failed)
        assert retry_results == []
        assert still_failed == [("s1", "Site1")]

    def test_exception(self, fake_mh):
        """Future.result raising appends site to still_failed."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fut = MagicMock()
        fut.result.side_effect = RuntimeError("boom")
        retry_futures = {fut: ("s1", "Site1")}
        retry_results: list = []
        still_failed: list = []
        OrgDeviceStatsExporter._process_retry_future(fut, retry_futures, retry_results, still_failed)
        assert retry_results == []
        assert still_failed == [("s1", "Site1")]


class TestDispatchSitePortRetries:
    """Verify pool dispatch invokes ``_process_retry_future`` per site."""

    def test_dispatch(self, fake_mh):
        """All failed sites should be dispatched and processed."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        failed_sites = [("s1", "Site1"), ("s2", "Site2")]
        with (
            patch.object(OrgDeviceStatsExporter, "_fetch_site_port_stats", return_value=[{"row": 1}]),
            patch.object(OrgDeviceStatsExporter, "_process_retry_future") as proc,
        ):
            retry_results: list = []
            still_failed: list = []
            OrgDeviceStatsExporter._dispatch_site_port_retries(
                failed_sites, MagicMock(), 2, retry_results, still_failed
            )
        assert proc.call_count == 2


class TestRetryFailedSitePortStats:
    """Cover the retry_threads guard and normal dispatch path."""

    def test_no_threads_available(self, fake_mh):
        """When computed retry_threads <= 0 the retry pool is skipped."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fake_mh.FAST_MODE_RETRY_THREADS = 0
        with patch("src.refactors.fast_mode_constants.FAST_MODE_MAX_CONCURRENT_CONNECTIONS", 1):
            recovered, still = OrgDeviceStatsExporter._retry_failed_site_port_stats([("s1", "Site1")], MagicMock())
        assert recovered == []
        assert still == [("s1", "Site1")]

    def test_normal_dispatch(self, fake_mh):
        """Positive retry_threads should dispatch via helper."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with (
            patch("src.refactors.fast_mode_constants.FAST_MODE_MAX_CONCURRENT_CONNECTIONS", 8),
            patch.object(OrgDeviceStatsExporter, "_dispatch_site_port_retries") as dispatch,
        ):
            recovered, still = OrgDeviceStatsExporter._retry_failed_site_port_stats(
                [("s1", "Site1"), ("s2", "Site2")], MagicMock()
            )
        dispatch.assert_called_once()
        assert recovered == []
        assert still == []


# ---------------------------------------------------------------------------
# Post-processing helpers
# ---------------------------------------------------------------------------


class TestFlattenSitePortResults:
    """Cover list vs non-list defensive branches."""

    def test_list_extends(self, fake_mh):
        """List payloads should be extended into combined output."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        assert OrgDeviceStatsExporter._flatten_site_port_results([[{"r": 1}], [{"r": 2}, {"r": 3}]]) == [
            {"r": 1},
            {"r": 2},
            {"r": 3},
        ]

    def test_non_list_ignored(self, fake_mh):
        """Non-list payloads should be logged and skipped."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        assert OrgDeviceStatsExporter._flatten_site_port_results([[{"r": 1}], "unexpected"]) == [{"r": 1}]


class TestSaveDevicePortStatsOutput:
    """Empty rows, sort failure, and normal export."""

    def test_empty_rows(self, fake_mh, capsys):
        """Empty rows should skip export and print a warning."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        OrgDeviceStatsExporter._save_device_port_stats_output([], "out.csv")
        assert "No port statistics" in capsys.readouterr().out
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_normal_export(self, fake_mh, capsys):
        """Rows should be sorted, flattened, escaped, and written."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        rows = [{"mac": "bb"}, {"mac": "aa"}]
        with (
            patch(
                "src.export.org_device_stats_exporter.DataProcessingUtils.flatten_nested_fields",
                return_value=rows,
            ),
            patch(
                "src.export.org_device_stats_exporter.DataProcessingUtils.escape_multiline",
                return_value=rows,
            ),
        ):
            OrgDeviceStatsExporter._save_device_port_stats_output(rows, "out.csv")
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()
        assert "port stat records exported" in capsys.readouterr().out

    def test_sort_failure_still_exports(self, fake_mh):
        """Sort failure should log and continue with unsorted rows."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        # Rows containing a value whose ``get`` blows up should trigger the except path.
        class BadRow:
            def get(self, _k, _d=""):
                raise RuntimeError("sort boom")

        rows = [BadRow()]
        with (
            patch(
                "src.export.org_device_stats_exporter.DataProcessingUtils.flatten_nested_fields",
                return_value=rows,
            ),
            patch(
                "src.export.org_device_stats_exporter.DataProcessingUtils.escape_multiline",
                return_value=rows,
            ),
        ):
            OrgDeviceStatsExporter._save_device_port_stats_output(rows, "out.csv")
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()


class TestValidateFastPortStatsStartTime:
    """Numeric ok vs non-numeric raises TypeError."""

    def test_numeric_ok(self, fake_mh):
        """Numeric start_time should return without raising."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        OrgDeviceStatsExporter._validate_fast_port_stats_start_time(1234.5)
        OrgDeviceStatsExporter._validate_fast_port_stats_start_time(1234)

    def test_non_numeric_raises(self, fake_mh):
        """Non-numeric value raises TypeError with descriptive message."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        with pytest.raises(TypeError, match="start_time must be a number"):
            OrgDeviceStatsExporter._validate_fast_port_stats_start_time("not a number")


class TestLogFastPortStatsSummary:
    """Snapshot test for summary logger."""

    def test_summary_runs(self, fake_mh, capsys):
        """Summary should print an operator-facing line."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        OrgDeviceStatsExporter._log_fast_port_stats_summary(
            [("s1", "n1"), ("s2", "n2")], [("s2", "n2")], [{"x": 1}], 1.23
        )
        assert "Fast mode" in capsys.readouterr().out


class TestRunFastDevicePortStats:
    """Orchestration test."""

    def test_orchestrates(self, fake_mh):
        """Fast-mode orchestrator should call save with flattened results."""
        from src.export.org_device_stats_exporter import OrgDeviceStatsExporter

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
        fake_mh.ConnectionPoolExecutor.execute.return_value = ([[{"row": 1}]], [])
        with (
            patch.object(
                OrgDeviceStatsExporter,
                "_load_port_stats_sites",
                return_value=[("s1", "Site1")],
            ),
            patch.object(OrgDeviceStatsExporter, "_save_device_port_stats_output") as save,
        ):
            OrgDeviceStatsExporter._run_fast_device_port_stats("out.csv")
        save.assert_called_once()
        args, _ = save.call_args
        assert args[0] == [{"row": 1}]
        assert args[1] == "out.csv"


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_module_importable():
    """Baseline sanity: module imports cleanly."""
    from src.export import org_device_stats_exporter

    assert hasattr(org_device_stats_exporter, "OrgDeviceStatsExporter")
