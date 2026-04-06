"""
Unit tests for export scaffolding (Menus 63-65)

This file contains tests that assert the 52-week exports call the underlying API and write outputs.
"""

from unittest.mock import MagicMock

import MistHelper


def test_device_events_52w_writes_csv(monkeypatch):
    # Arrange
    monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org1")
    sample_events = [{"id": "e1", "timestamp": "2026-01-01T00:00:00Z"}]

    # Patch the search API and mistapi.get_all
    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.orgs.devices,
        "searchOrgDeviceEvents",
        lambda session, org_id, device_type, limit, duration: MagicMock(),
    )
    monkeypatch.setattr(MistHelper.mistapi, "get_all", lambda response, mist_session: sample_events)

    recorded = {}

    def fake_save(data, filename, api_function_name=None):
        recorded["filename"] = filename
        recorded["count"] = len(data)

    monkeypatch.setattr(MistHelper.DataExporter, "save_data_to_output", fake_save)

    # Act
    MistHelper.OrgAlarmEventExporter.device_events_52w()

    # Assert
    assert recorded.get("filename") == "OrgDeviceEvents_52w.csv"
    assert recorded.get("count") == 1
