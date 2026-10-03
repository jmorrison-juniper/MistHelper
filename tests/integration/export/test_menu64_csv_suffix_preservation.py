"""Prove the advertised filename through the native menu 64 export path."""

from __future__ import annotations

import csv
import json
import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import Mock, call

import mistapi
import pytest
from mistapi.__api_response import APIResponse
from requests import Response, Session

import MistHelper
from src.config import runtime_settings
from src.db import WriteResult
from src.db.router import DatabaseRouter
from src.export import data_exporter as exporter_module
from src.export.data_exporter import DataExporter
from src.export.site_client_exporter import SiteClientExporter
from src.refactors.main_entrypoint import AppContext, MainEntrypoint
from web_portal.menu_registry import MENU_DESCRIPTIONS
from web_portal.services.data_browser import DataBrowserService
from web_portal.services.output_scan import OutputFileScanner

NATIVE_RECORDS: dict[str, list[dict[str, Any]]] = {
    "clients": [{"mac": "aabbccddeeff", "hostname": "Lab Client", "ip": "192.0.2.10", "notes": "first\nsecond"}],
    "sessions": [{"mac": "aabbccddeeff", "ssid": "Lab WLAN", "start_time": 1700000000, "vlan": 42}],
}
EXPECTED_CSV_RECORD = {
    "mac": "aabbccddeeff",
    "hostname": "Lab Client",
    "ip": "192.0.2.10",
    "notes": "first\\nsecond",
    "site_id": "controlled-site",
    "site_name": "Lab Site",
    "data_source": "client",
    "session_count": "1",
    "session_ssid": "Lab WLAN",
    "session_start_time": "1700000000",
    "session_vlan": "42",
}


@dataclass
class NativeMenu64Proof:
    """Own the counted callbacks and temporary files for one native run."""

    root: Path
    session: mistapi.APISession
    callbacks: dict[str, Mock] = field(default_factory=dict)

    @staticmethod
    def response(records: list[dict[str, Any]], uri: str) -> APIResponse:
        """Build a real SDK response without an HTTP request."""
        transport = Response()
        transport.status_code = 200
        transport.url = f"https://api.mist.invalid{uri}?limit=1000"
        transport.encoding = "utf-8"
        transport._content = json.dumps({"results": records}).encode("utf-8")
        transport.headers["Content-Type"] = "application/json"
        return APIResponse(transport, transport.url)

    def configure_sdk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Replace only transport callbacks while the real SDK functions execute."""
        client_uri = "/api/v1/sites/controlled-site/clients/search"
        session_uri = "/api/v1/sites/controlled-site/clients/sessions/search"
        responses = [
            self.response(NATIVE_RECORDS["clients"], client_uri),
            self.response(NATIVE_RECORDS["sessions"], session_uri),
        ]
        self.callbacks["sdk"] = Mock(spec=self.session.mist_get, side_effect=responses)
        self.callbacks["http"] = Mock(spec=Session.request, side_effect=AssertionError("Live HTTP is forbidden"))
        monkeypatch.setattr(self.session, "mist_get", self.callbacks["sdk"])
        monkeypatch.setattr(Session, "request", self.callbacks["http"])

    def configure_export(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Use real source helpers with a private external router."""
        router = Mock(spec=DatabaseRouter)
        router.write.return_value = WriteResult(success=True, backend="arangodb", records_written=1, records_failed=0)
        self.callbacks["router"] = router.write
        self.callbacks["input"] = Mock(spec=input, return_value="Lab Site")
        self.callbacks["csv"] = Mock(spec=DataExporter.write_to_csv, wraps=DataExporter.write_to_csv)
        self.callbacks["export"] = Mock(
            spec=DataExporter.write_with_format_selection, wraps=DataExporter.write_with_format_selection
        )
        monkeypatch.setenv("MISTHELPER_STANDALONE", "false")
        monkeypatch.setattr(exporter_module, "DB_LAYER_AVAILABLE", True)
        monkeypatch.setattr(DataExporter, "_router", router)
        monkeypatch.setattr(DataExporter, "_router_initialized", True)
        monkeypatch.setattr(MainEntrypoint, "context", AppContext(apisession=self.session, output_format="csv"))
        monkeypatch.setattr(runtime_settings, "LAST_SELECTED_SITE_ID", None)
        monkeypatch.setattr("builtins.input", self.callbacks["input"])
        monkeypatch.setattr(DataExporter, "write_to_csv", self.callbacks["csv"])
        monkeypatch.setattr(DataExporter, "write_with_format_selection", self.callbacks["export"])
        DataExporter.write_to_csv([{"id": "controlled-site", "name": "Lab Site"}], "SiteList.csv")
        assert self.callbacks["csv"].call_count == 1  # This write supplies the prompt cache, not the client output.
        self.callbacks["csv"].reset_mock()

    def run(self) -> list[str]:
        """Execute the exact menu handler and report only files that it writes."""
        entry = MistHelper.menu_actions["64"]
        assert entry.handler is SiteClientExporter.wifi_clients
        assert entry.title == MENU_DESCRIPTIONS["64"]
        self.callbacks["handler"] = Mock(spec=entry.handler, wraps=entry.handler)
        scanner = OutputFileScanner(str(self.root / "data"))
        scanner.snapshot()
        try:
            self.callbacks["handler"]()
        finally:
            outputs = scanner.changed_files()  # This call also removes the scanner's temporary write hooks.
        return outputs

    def verify_counts(self) -> None:
        """Require exact native requests, final writes, and zero live HTTP calls."""
        assert self.callbacks["handler"].call_count == 1
        self.callbacks["input"].assert_called_once_with("\nEnter site index or name: ")
        assert self.callbacks["sdk"].call_args_list == [
            call(uri="/api/v1/sites/controlled-site/clients/search", query={"limit": "1000"}),
            call(uri="/api/v1/sites/controlled-site/clients/sessions/search", query={"limit": "1000"}),
        ]
        assert self.callbacks["csv"].call_count == 1
        assert self.callbacks["export"].call_count == 1
        assert self.callbacks["router"].call_count == 1
        assert self.callbacks["http"].call_count == 0
        print("Checked 1 handler, 1 site answer, 2 SDK requests, 1 cache setup write, and 1 final CSV write.")
        print("Checked 1 final router write and 0 live HTTP requests.")


@pytest.fixture
def native_proof(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[NativeMenu64Proof]:
    """Isolate the real SDK session from credentials and production resources."""
    for name in tuple(os.environ):
        if name.startswith("MIST_"):
            monkeypatch.delenv(name)
    session = mistapi.APISession(show_cli_notif=False)
    proof = NativeMenu64Proof(tmp_path, session)
    proof.configure_sdk(monkeypatch)
    proof.configure_export(monkeypatch)
    try:
        yield proof
    finally:
        session._session.close()


class TestNativeMenu64CsvSuffix:
    """Hold the exact advertised filename and complete merged record contract."""

    def test_native_handler_writes_the_advertised_filename(
        self, native_proof: NativeMenu64Proof, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The real handler, SDK functions, and local writer must agree on one name."""
        with caplog.at_level(logging.INFO):
            outputs = native_proof.run()
        native_proof.verify_counts()
        print("Actual native output filenames:", json.dumps(outputs))
        assert len(outputs) == 1
        destination = native_proof.root / "data" / outputs[0]
        assert "! WiFi data exported to SiteWiFiClients.CSV" in caplog.text
        assert MistHelper.menu_actions["64"].title.endswith("SiteWiFiClients.CSV")
        with destination.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            records = list(reader)
            assert reader.fieldnames == sorted(records[0])
        self.verify_record_and_metadata(records, native_proof, outputs[0])
        assert outputs == ["SiteWiFiClients.CSV"]
        assert not (destination.parent / "SiteWiFiClients.CSV.csv").exists()
        self.verify_browser_record(destination)

    @staticmethod
    def verify_record_and_metadata(
        records: list[dict[str, str]], proof: NativeMenu64Proof, actual_filename: str
    ) -> None:
        """Check every merged field and the router's unchanged endpoint metadata."""
        assert records == [EXPECTED_CSV_RECORD]
        exported = proof.callbacks["export"].call_args
        assert exported.args[1] == "SiteWiFiClients.CSV"
        assert exported.kwargs == {"api_function_name": "listSiteWirelessClientsStats"}
        proof.callbacks["csv"].assert_called_once_with(exported.args[0], actual_filename, fieldnames=None)
        proof.callbacks["router"].assert_called_once_with(exported.args[0], "listSiteWirelessClientsStats")
        print("Checked 1 complete merged CSV record and unchanged endpoint metadata.")

    @staticmethod
    def verify_browser_record(destination: Path) -> None:
        """Preview the complete native client record through the shipped browser service."""
        browser = DataBrowserService(str(destination.parent))
        assert {entry["name"] for entry in browser.list_files()} == {"SiteList.csv", "SiteWiFiClients.CSV"}
        assert browser.resolve_safe_path(destination.name) == str(destination.resolve())
        assert browser.read_column_names(destination.name) == sorted(EXPECTED_CSV_RECORD)
        preview = browser.preview_file(destination.name, 1, 25, "")
        assert preview["total_rows"] == 1
        assert len(preview["rows"]) == 1
        assert dict(zip(preview["columns"], preview["rows"][0], strict=True)) == EXPECTED_CSV_RECORD
        print("Checked 1 native browser preview record and 11 columns.")
