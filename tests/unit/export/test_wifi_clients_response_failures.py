"""Regression tests for failed and malformed WiFi API responses."""

from __future__ import annotations  # WHY: keep annotations compatible with the project typing configuration.

import logging  # WHY: capture the repository-standard failure messages.
from pathlib import Path  # WHY: create isolated SiteList and output paths.
from types import SimpleNamespace  # WHY: model the native response fields without network access.
from unittest.mock import MagicMock  # WHY: isolate API endpoints and pagination calls.

import pytest  # WHY: parameterize the four reported failure contracts.

from src.export.wifi_clients_exporter import WifiClientsExporter  # WHY: exercise the production WiFi exporter.


def _build_exporter(site_list_path: Path) -> tuple[WifiClientsExporter, MagicMock, MagicMock]:
    """Build an exporter with isolated dependencies for response failure tests."""
    mistapi_module = MagicMock()  # WHY: control endpoint and pagination calls without live Mist access.
    endpoint = MagicMock()  # WHY: return one controlled response for the first WiFi request.
    mistapi_module.api.v1.sites.clients.searchSiteWirelessClients = endpoint  # WHY: bind the client endpoint path.
    mistapi_module.api.v1.sites.clients.searchSiteWirelessClientSessions = (
        MagicMock()
    )  # WHY: keep the second endpoint inert.
    exporter = WifiClientsExporter(
        cache_utils=MagicMock(),  # WHY: avoid cache writes in this focused response test.
        org_site_exporter=MagicMock(),  # WHY: avoid organization discovery in this focused response test.
        prompt_utils=MagicMock(),  # WHY: site_id is supplied directly.
        file_path_utils=MagicMock(),  # WHY: control the SiteList path without filesystem coupling.
        data_processing_utils=MagicMock(),  # WHY: response rejection occurs before row processing.
        data_exporter=MagicMock(),  # WHY: verify no export call occurs on failure.
        mistapi_module=mistapi_module,  # WHY: inject the controlled SDK boundary.
        apisession=MagicMock(),  # WHY: no authenticated network session is needed.
    )
    exporter.file_path_utils.get_csv_path.return_value = str(site_list_path)  # WHY: resolve the known site name.
    return exporter, endpoint, mistapi_module


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (SimpleNamespace(status_code=200, raw_data="", data={}), "empty body"),  # WHY: reproduce HTTP 200 with no body.
        (
            SimpleNamespace(status_code=200, raw_data="not JSON", data={}),
            "malformed body",
        ),  # WHY: reproduce swallowed JSON parsing failure.
        (SimpleNamespace(status_code=403, raw_data='{"error":"denied"}', data={"error": "denied"}), "HTTP 403"),
        (SimpleNamespace(status_code=503, raw_data='{"error":"down"}', data={"error": "down"}), "HTTP 503"),
    ],
)
def test_failed_wifi_response_does_not_write_empty_placeholder(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    response: SimpleNamespace,
    message: str,
) -> None:
    """Failed WiFi responses must report failure and skip the valid-empty placeholder."""
    site_list_path = tmp_path / "SiteList.csv"  # WHY: provide the site-name lookup required by execute().
    site_list_path.write_text("id,name\nsite-1,Lab Site\n", encoding="utf-8")  # WHY: keep the fixture deterministic.
    exporter, endpoint, mistapi_module = _build_exporter(site_list_path)  # WHY: isolate this response contract.
    endpoint.return_value = response  # WHY: inject the controlled native-shaped response.
    output_path = tmp_path / "SiteWiFiClients.CSV"  # WHY: detect the forbidden placeholder artifact.
    exporter.file_path_utils.get_csv_path.side_effect = [  # WHY: separate lookup and output paths.
        str(site_list_path),
        str(output_path),
    ]

    with caplog.at_level(logging.ERROR, logger="src.export.wifi_clients_exporter"):
        exporter.execute(site_id="site-1")  # WHY: exercise the real top-level failure path.

    assert not output_path.exists(), message  # WHY: failed responses must not create success-shaped output.
    mistapi_module.get_all.assert_not_called()  # WHY: pagination must not process an untrusted response.
    assert any(  # WHY: failure stays visible to the operator.
        "Failed to fetch WiFi data" in record.getMessage() for record in caplog.records
    )


def test_valid_empty_wifi_response_keeps_placeholder_behavior(tmp_path: Path) -> None:
    """A valid empty JSON response must keep the existing no-data behavior."""
    site_list_path = tmp_path / "SiteList.csv"  # WHY: provide the site-name lookup required by execute().
    site_list_path.write_text("id,name\nsite-1,Lab Site\n", encoding="utf-8")  # WHY: keep the fixture deterministic.
    exporter, endpoint, mistapi_module = _build_exporter(site_list_path)  # WHY: isolate the valid-empty contract.
    endpoint.return_value = SimpleNamespace(  # WHY: model a parsed empty answer.
        status_code=200,
        raw_data="[]",
        data=[],
    )
    mistapi_module.get_all.return_value = []  # WHY: both WiFi datasets are empty after pagination.
    output_path = tmp_path / "SiteWiFiClients.CSV"  # WHY: verify the existing placeholder remains supported.
    exporter.file_path_utils.get_csv_path.side_effect = [  # WHY: separate lookup and output paths.
        str(site_list_path),
        str(output_path),
    ]

    exporter.execute(site_id="site-1")  # WHY: exercise the unchanged valid-empty path.

    assert output_path.exists()  # WHY: valid empty results must still create the no-data placeholder.
    assert (  # WHY: preserve the sentinel message for valid empty results.
        "No WiFi clients or sessions found" in output_path.read_text(encoding="utf-8")
    )
