"""
Unit tests for export scaffolding (Menus 63-65)

This file contains tests that assert the 52-week exporter streams the underlying API and writes outputs.
"""

import csv
import pytest
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
