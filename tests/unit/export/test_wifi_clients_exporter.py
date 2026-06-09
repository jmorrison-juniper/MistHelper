"""Unit tests for src.export.wifi_clients_exporter."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

from src.export.wifi_clients_exporter import WifiClientsExporter


def _build_exporter() -> tuple[WifiClientsExporter, MagicMock, MagicMock, MagicMock]:
    """Create exporter with mocked dependencies."""
    cache_utils = MagicMock()
    org_site_exporter = MagicMock()
    prompt_utils = MagicMock()
    file_path_utils = MagicMock()
    data_processing_utils = MagicMock()
    data_exporter = MagicMock()
    mistapi_module = MagicMock()
    apisession = MagicMock()
    exporter = WifiClientsExporter(
        cache_utils=cache_utils,
        org_site_exporter=org_site_exporter,
        prompt_utils=prompt_utils,
        file_path_utils=file_path_utils,
        data_processing_utils=data_processing_utils,
        data_exporter=data_exporter,
        mistapi_module=mistapi_module,
        apisession=apisession,
    )
    return exporter, prompt_utils, mistapi_module, data_exporter


def test_execute_aborts_when_no_site_selected() -> None:
    """Exporter should return early when site selection is cancelled."""
    exporter, prompt_utils, _mistapi, data_exporter = _build_exporter()
    prompt_utils.select_site_id_from_csv.return_value = None

    exporter.execute(site_id=None)

    data_exporter.save_data_to_output.assert_not_called()


def test_execute_exports_merged_records() -> None:
    """Exporter should merge client/session data and write output."""
    exporter, _prompt_utils, mistapi_module, data_exporter = _build_exporter()
    exporter.file_path_utils.get_csv_path.return_value = "tests/fixtures/site_list.csv"
    exporter.data_processing_utils.flatten_nested_fields.side_effect = lambda value: value
    exporter.data_processing_utils.escape_multiline.side_effect = lambda value: value

    client_response = MagicMock()
    session_response = MagicMock()
    mistapi_module.api.v1.sites.clients.searchSiteWirelessClients.return_value = client_response
    mistapi_module.api.v1.sites.clients.searchSiteWirelessClientSessions.return_value = session_response
    mistapi_module.get_all.side_effect = [
        [{"mac": "aa:bb:cc:dd:ee:ff", "hostname": "client-1"}],
        [{"mac": "aa:bb:cc:dd:ee:ff", "start_time": 10}],
    ]

    os.makedirs("tests/fixtures", exist_ok=True)
    with open("tests/fixtures/site_list.csv", "w", encoding="utf-8") as file_handle:
        file_handle.write("id,name\nsite-1,Site One\n")

    exporter.execute(site_id="site-1")

    data_exporter.save_data_to_output.assert_called_once()
