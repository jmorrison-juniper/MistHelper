"""Unit tests for DeviceEvents52wExporter."""

from unittest.mock import MagicMock

from src.export.device_events_52w_exporter import DeviceEvents52wExporter


def test_device_events_exporter_handles_empty_results(tmp_path, monkeypatch) -> None:
    """Exporter writes empty output when no data is returned."""
    monkeypatch.chdir(tmp_path)
    mistapi = MagicMock()
    mistapi.api.v1.orgs.devices.searchOrgDeviceEvents.return_value = MagicMock(data={"results": []})
    data_processing = MagicMock()
    data_processing.flatten_nested_fields.side_effect = lambda rows: rows
    data_processing.escape_multiline.side_effect = lambda rows: rows
    data_processing.get_unique_keys.return_value = []
    data_exporter = MagicMock()
    exporter = DeviceEvents52wExporter(
        apisession=MagicMock(),
        mistapi=mistapi,
        org_id="org-1",
        data_processing_utils=data_processing,
        data_exporter=data_exporter,
        output_format="csv",
        database_path="data/mist_data.db",
        logger=MagicMock(),
    )
    exporter.export()
    data_exporter.write_with_format_selection.assert_called_once()
