"""Verify that cache failures do not hide programming errors."""

import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.operations.exporting.export import org_device_stats_exporter as exporter


@pytest.mark.parametrize(
    ("cache_method", "entry_point"),
    [
        ("_device_stats_cache_hit", "device_stats"),
        ("_port_stats_cache_hit", "device_port_stats"),
        ("_vpn_peer_stats_cache_hit", "vpn_peer_stats"),
    ],
)
class TestCacheExceptionBoundaries:
    """Check all three cache paths and their export callers."""

    def test_metadata_failure_returns_cache_miss(
        self,
        cache_method: str,
        entry_point: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A filesystem error causes a cache miss and records the error."""
        cache_file = tmp_path / "cache.csv"
        cache_file.touch()
        monkeypatch.setattr(exporter.os.path, "getmtime", MagicMock(side_effect=OSError("metadata unavailable")))
        with caplog.at_level(logging.DEBUG):
            result = getattr(exporter.OrgDeviceStatsExporter, cache_method)(str(cache_file), True)
        assert result is False
        assert "metadata unavailable" in caplog.text

    def test_unexpected_error_reaches_export_caller(
        self, cache_method: str, entry_point: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A programming error must reach the caller before a fetch can start."""
        monkeypatch.chdir(tmp_path)
        for name in ("OrgDeviceStats.csv", "OrgDevicePortStats.csv", "OrgVPNPeerStats.csv"):
            (tmp_path / name).touch()
        dependencies = MagicMock()
        dependencies.PROGRESS_EMITTER = None
        monkeypatch.setattr(exporter, "SourceDependencyResolver", dependencies)
        monkeypatch.setattr(exporter, "TimeUtils", MagicMock())
        fast_fetch = MagicMock()
        monkeypatch.setattr(exporter.OrgDeviceStatsExporter, "_run_fast_device_port_stats", fast_fetch)
        monkeypatch.setattr(exporter.os.path, "getmtime", MagicMock(side_effect=TypeError("bad metadata call")))
        with pytest.raises(TypeError, match="bad metadata call"):
            getattr(exporter.OrgDeviceStatsExporter, entry_point)(fast=True)
        dependencies.APIDataFetcher.assert_not_called()
        fast_fetch.assert_not_called()

    def test_metadata_failure_starts_export(
        self, cache_method: str, entry_point: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A filesystem error still permits the export to fetch fresh data."""
        monkeypatch.chdir(tmp_path)
        for name in ("OrgDeviceStats.csv", "OrgDevicePortStats.csv", "OrgVPNPeerStats.csv"):
            (tmp_path / name).touch()
        dependencies = MagicMock()
        dependencies.PROGRESS_EMITTER = None
        monkeypatch.setattr(exporter, "SourceDependencyResolver", dependencies)
        monkeypatch.setattr(exporter, "TimeUtils", MagicMock())
        fast_fetch = MagicMock()
        monkeypatch.setattr(exporter.OrgDeviceStatsExporter, "_run_fast_device_port_stats", fast_fetch)
        monkeypatch.setattr(exporter.os.path, "getmtime", MagicMock(side_effect=OSError("metadata unavailable")))
        getattr(exporter.OrgDeviceStatsExporter, entry_point)(fast=True)
        if entry_point == "device_port_stats":
            fast_fetch.assert_called_once_with("OrgDevicePortStats.csv")
            dependencies.APIDataFetcher.assert_not_called()
        else:
            dependencies.APIDataFetcher.return_value.execute.assert_called_once_with()
            fast_fetch.assert_not_called()
