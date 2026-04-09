"""
Unit tests for export scaffolding (Menus 63-65)

This file contains tests that assert the 52-week exporter streams the underlying API and writes outputs.
"""

import csv
import sqlite3
from unittest.mock import MagicMock

import MistHelper


def test_device_events_52w_streams_and_writes_csv(monkeypatch, tmp_path):
    # Arrange
    monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org1")

    # Run in a temporary working directory to avoid writing to repository data/
    monkeypatch.chdir(tmp_path)

    # Stubbed paginated responses (two pages)
    def search_stub(session, org_id, device_type, limit, duration, search_after=None):
        resp = MagicMock()
        if not search_after:
            resp.data = {
                "results": [
                    {"id": "e1", "timestamp": "2026-01-01T00:00:00Z"},
                    {"id": "e2", "timestamp": "2026-01-02T00:00:00Z"},
                ],
                "search_after": "token1",
            }
        elif search_after == "token1":
            resp.data = {"results": [{"id": "e3", "timestamp": "2026-01-03T00:00:00Z"}], "search_after": None}
        else:
            resp.data = {"results": [], "search_after": None}
        return resp

    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.devices, "searchOrgDeviceEvents", search_stub)

    # Act
    MistHelper.OrgAlarmEventExporter.device_events_52w()

    # Assert file created and contains 3 rows
    csv_path = tmp_path / "data" / "OrgDeviceEvents_52w.csv"
    assert csv_path.exists(), f"Expected CSV at {csv_path}"

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    assert len(rows) == 3
    ids = [r.get("id") for r in rows]
    assert ids == ["e1", "e2", "e3"]


def test_device_events_52w_streams_and_writes_sqlite(monkeypatch, tmp_path):
    # Arrange
    monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org1")

    # Run in a temporary working directory to avoid writing to repository data/
    monkeypatch.chdir(tmp_path)

    # Stubbed paginated responses (two pages)
    def search_stub(session, org_id, device_type, limit, duration, search_after=None):
        resp = MagicMock()
        if not search_after:
            resp.data = {
                "results": [
                    {"id": "e1", "timestamp": "2026-01-01T00:00:00Z"},
                    {"id": "e2", "timestamp": "2026-01-02T00:00:00Z"},
                ],
                "search_after": "token1",
            }
        elif search_after == "token1":
            resp.data = {"results": [{"id": "e3", "timestamp": "2026-01-03T00:00:00Z"}], "search_after": None}
        else:
            resp.data = {"results": [], "search_after": None}
        return resp

    monkeypatch.setattr(MistHelper.mistapi.api.v1.orgs.devices, "searchOrgDeviceEvents", search_stub)

    # Set global OUTPUT_FORMAT to sqlite for this test
    monkeypatch.setattr(MistHelper, "OUTPUT_FORMAT", "sqlite")

    # Act
    MistHelper.OrgAlarmEventExporter.device_events_52w()

    # Assert DB created and contains 3 rows
    db_path = tmp_path / "data" / "mist_data.db"
    assert db_path.exists(), f"Expected DB at {db_path}"

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM OrgDeviceEvents_52w")
    count = cur.fetchone()[0]
    conn.close()

    assert count == 3


def test_classify_device_platform_by_model_prefix():
    assert MistHelper.SiteExportUtils._classify_device_platform("AP45") == "ap"
    assert MistHelper.SiteExportUtils._classify_device_platform("EX4100-F-12P") == "switch"
    assert MistHelper.SiteExportUtils._classify_device_platform("SRX320-POE") == "gateway"
    assert MistHelper.SiteExportUtils._classify_device_platform("UNKNOWN") == "unknown"


def test_metric_compatibility_filters_switch_metrics_for_ap():
    assert MistHelper.SiteExportUtils._metric_compatible_with_platform("switch-metrics", "ap") is False
    assert MistHelper.SiteExportUtils._metric_compatible_with_platform("switch-metrics", "switch") is True
    assert MistHelper.SiteExportUtils._metric_compatible_with_platform("switch-metrics", "unknown") is True


def test_normalize_device_mac_or_none_accepts_and_normalizes():
    assert MistHelper.SiteExportUtils._normalize_device_mac_or_none("209339051780") == "20:93:39:05:17:80"


def test_normalize_device_mac_or_none_rejects_invalid():
    assert MistHelper.SiteExportUtils._normalize_device_mac_or_none("not-a-mac") is None


def test_normalize_client_mac_or_none_accepts_and_normalizes():
    assert MistHelper.SiteClientExporter._normalize_client_mac_or_none("845733cac819") == "84:57:33:ca:c8:19"


def test_normalize_client_mac_or_none_rejects_invalid():
    assert MistHelper.SiteClientExporter._normalize_client_mac_or_none("bad-mac") is None


def test_parse_scopes_handles_csv_style_values():
    parsed = MistHelper.InsightMetricsUtils._parse_scopes("site, client, device")
    assert parsed == {"site", "client", "device"}


def test_parse_scopes_handles_brackets_and_quotes():
    parsed = MistHelper.InsightMetricsUtils._parse_scopes("['site','client']")
    assert parsed == {"site", "client"}
