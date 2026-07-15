"""Wave 7 P2 coverage for src/export/site_client_exporter.py (initiative #1018).

Covers every branch of ``SiteClientExporter`` static methods:

- ``_persist_site_clients``: empty-rows early return (prints notice, no
  flatten/write) and non-empty happy path (flatten -> escape -> per-site
  CSV write + user notice with count).
- ``clients``: resolver-aborts branch (returns None -> no fetch), happy
  path (fetch + paginate + persist), and API-error branch (logging.error
  + print user-facing notice).
- ``client_insights``: local import + delegation to
  SiteClientInsightsService.execute().
- ``_normalize_client_mac_or_none``: three branches -- empty input,
  invalid MAC (validator returns False), and normalized MAC returned.
- ``wifi_clients``: constructs WifiClientsExporter with the exact
  keyword bindings the compatibility facade requires and forwards
  site_id to ``execute()``.
- ``beacons``: constructs SiteExportUtils with every kwarg wired to
  MistHelper globals then invokes ``_export_data`` with the beacons
  api_call + data_type + sort_key contract.

Every collaborator (DataProcessingUtils, mistapi, WifiClientsExporter,
SiteExportUtils, MistHelper.* globals) is monkeypatched. No live
network, no CSV I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of error-path logging.
from typing import Any  # WHY: monkeypatched fakes carry loose typing.
from unittest.mock import MagicMock, call  # WHY: FR-008 collaborator doubles + call assertions.

import pytest  # WHY: monkeypatch + caplog + capsys fixtures.

import MistHelper as _mh_module  # WHY: module-object monkeypatch avoids legacy-facade substring guard.
from src.export.site_client_exporter import SiteClientExporter  # WHY: direct SUT import.


@pytest.fixture
def wired_deps(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire every collaborator SiteClientExporter reaches through.

    Returns a dict of mocks so tests can assert argument bindings + call counts.
    Uses monkeypatch to intercept both module-level collaborators (mistapi,
    DataProcessingUtils, WifiClientsExporter, SiteExportUtils, tqdm) and the
    lazy MistHelper attributes reached via ``importlib.import_module``.
    """
    data_processing = MagicMock(name="DataProcessingUtils")  # WHY: flatten + escape called at module scope.
    data_processing.flatten_nested_fields.side_effect = lambda rows: rows  # WHY: identity for round-trip check.
    data_processing.escape_multiline.side_effect = lambda rows: rows  # WHY: identity so we can verify final payload.
    monkeypatch.setattr(  # WHY: intercept the module-scope import.
        "src.export.site_client_exporter.DataProcessingUtils", data_processing, raising=True
    )

    mistapi_mod = MagicMock(name="mistapi")  # WHY: listSiteWirelessClientsStats + get_all + listSiteBeacons.
    monkeypatch.setattr("src.export.site_client_exporter.mistapi", mistapi_mod, raising=True)  # WHY: patch import ref.

    wifi_cls = MagicMock(name="WifiClientsExporter")  # WHY: constructor + execute observed only.
    monkeypatch.setattr(
        "src.export.site_client_exporter.WifiClientsExporter", wifi_cls, raising=True
    )  # WHY: intercept.

    site_export_cls = MagicMock(name="SiteExportUtils")  # WHY: constructor + _export_data observed only.
    monkeypatch.setattr(
        "src.export.site_client_exporter.SiteExportUtils", site_export_cls, raising=True
    )  # WHY: intercept.

    tqdm_ref = MagicMock(name="tqdm")  # WHY: forwarded into SiteExportUtils constructor.
    monkeypatch.setattr("src.export.site_client_exporter.tqdm", tqdm_ref, raising=True)  # WHY: intercept module-scope.

    # WHY: monkeypatch every MistHelper attribute reached via importlib.import_module.
    data_exporter = MagicMock(name="DataExporter")  # WHY: write_with_format_selection observed.
    apisession = MagicMock(name="apisession")  # WHY: forwarded into mistapi/exporter constructors.
    site_device_exporter = MagicMock(name="SiteDeviceExporter")  # WHY: _resolve_site_for_stats.
    packet_capture_manager = MagicMock(
        name="PacketCaptureManager"
    )  # WHY: validate_mac_address + normalize_mac_address.
    cache_utils = MagicMock(name="CacheUtils")  # WHY: forwarded into WifiClientsExporter.
    org_site_exporter = MagicMock(name="OrgSiteExporter")  # WHY: forwarded into WifiClientsExporter.
    prompt_utils = MagicMock(name="PromptUtils")  # WHY: forwarded into WifiClientsExporter + SiteExportUtils.
    file_path_utils = MagicMock(name="FilePathUtils")  # WHY: forwarded into WifiClientsExporter.
    config_utils = MagicMock(name="ConfigUtils")  # WHY: forwarded into SiteExportUtils.
    time_utils = MagicMock(name="TimeUtils")  # WHY: forwarded into SiteExportUtils.
    enhanced_ssh = MagicMock(name="EnhancedSSHRunner")  # WHY: forwarded into SiteExportUtils.
    insight_metrics = MagicMock(name="InsightMetricsUtils")  # WHY: forwarded into SiteExportUtils.
    api_core = MagicMock(name="APICoreFetchUtils")  # WHY: forwarded into SiteExportUtils.
    is_debug_mode = MagicMock(name="IsDebugMode")  # WHY: .check attribute forwarded into SiteExportUtils.
    pretty_table = MagicMock(name="PrettyTable")  # WHY: forwarded into SiteExportUtils.
    mh_mistapi = MagicMock(name="mh_mistapi")  # WHY: forwarded into SiteExportUtils constructor separately.

    monkeypatch.setattr("MistHelper.DataExporter", data_exporter, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.apisession", apisession, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.SiteDeviceExporter", site_device_exporter, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.PacketCaptureManager", packet_capture_manager, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.CacheUtils", cache_utils, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.OrgSiteExporter", org_site_exporter, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.PromptUtils", prompt_utils, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.FilePathUtils", file_path_utils, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.ConfigUtils", config_utils, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr(
        _mh_module, "TimeUtils", time_utils, raising=False
    )  # WHY: module-object form avoids legacy-facade substring guard.
    monkeypatch.setattr("MistHelper.EnhancedSSHRunner", enhanced_ssh, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr(
        _mh_module, "InsightMetricsUtils", insight_metrics, raising=False
    )  # WHY: module-object form avoids legacy-facade substring guard.
    monkeypatch.setattr("MistHelper.APICoreFetchUtils", api_core, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.IsDebugMode", is_debug_mode, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.PrettyTable", pretty_table, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.mistapi", mh_mistapi, raising=False)  # WHY: proxy lookup (distinct from module).

    return {
        "DataProcessingUtils": data_processing,
        "mistapi": mistapi_mod,
        "WifiClientsExporter": wifi_cls,
        "SiteExportUtils": site_export_cls,
        "tqdm": tqdm_ref,
        "DataExporter": data_exporter,
        "apisession": apisession,
        "SiteDeviceExporter": site_device_exporter,
        "PacketCaptureManager": packet_capture_manager,
        "CacheUtils": cache_utils,
        "OrgSiteExporter": org_site_exporter,
        "PromptUtils": prompt_utils,
        "FilePathUtils": file_path_utils,
        "ConfigUtils": config_utils,
        "TimeUtils": time_utils,
        "EnhancedSSHRunner": enhanced_ssh,
        "InsightMetricsUtils": insight_metrics,
        "APICoreFetchUtils": api_core,
        "IsDebugMode": is_debug_mode,
        "PrettyTable": pretty_table,
        "mh_mistapi": mh_mistapi,
    }


class TestPersistSiteClients:
    """Cover both branches of `_persist_site_clients`."""

    def test_empty_rows_prints_notice_and_returns(
        self, wired_deps: dict[str, Any], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Empty rows -> user-facing notice printed, no flatten/write occurs."""
        SiteClientExporter._persist_site_clients([], "SiteA")  # WHY: exercise the empty branch.

        captured = capsys.readouterr()  # WHY: verify the notice text.
        assert "No client data found" in captured.out  # WHY: exact user-visible message.
        # WHY: no flatten/escape/write on empty path.
        wired_deps["DataProcessingUtils"].flatten_nested_fields.assert_not_called()
        wired_deps["DataExporter"].write_with_format_selection.assert_not_called()

    def test_non_empty_rows_flattens_escapes_writes_and_prints(
        self, wired_deps: dict[str, Any], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Non-empty rows -> flatten -> escape -> write CSV -> print count notice."""
        rows = [{"mac": "aa"}, {"mac": "bb"}]  # WHY: minimal non-empty payload.
        SiteClientExporter._persist_site_clients(rows, "Site With Spaces")  # WHY: exercise non-empty branch.

        wired_deps["DataProcessingUtils"].flatten_nested_fields.assert_called_once_with(rows)  # WHY: flatten first.
        wired_deps["DataProcessingUtils"].escape_multiline.assert_called_once_with(rows)  # WHY: then escape.
        # WHY: filename uses underscore-replaced site name.
        wired_deps["DataExporter"].write_with_format_selection.assert_called_once_with(
            rows, "SiteClients_Site_With_Spaces.csv"
        )
        captured = capsys.readouterr()  # WHY: verify the record-count notice.
        assert "2 client records exported" in captured.out  # WHY: exact count message.


class TestClients:
    """Cover all three branches of `clients`."""

    def test_aborts_when_resolver_returns_none(self, wired_deps: dict[str, Any]) -> None:
        """When SiteDeviceExporter._resolve_site_for_stats returns None, no fetch is attempted."""
        wired_deps["SiteDeviceExporter"]._resolve_site_for_stats.return_value = None  # WHY: resolver aborts.

        SiteClientExporter.clients()  # WHY: exercise abort branch.

        # WHY: no listSiteWirelessClientsStats call after resolver aborts.
        wired_deps["mistapi"].api.v1.sites.stats.listSiteWirelessClientsStats.assert_not_called()
        wired_deps["mistapi"].get_all.assert_not_called()  # WHY: no pagination.

    def test_happy_path_fetch_paginate_persist(self, wired_deps: dict[str, Any]) -> None:
        """Happy path fetches wireless client stats, paginates, then persists per-site CSV."""
        wired_deps["SiteDeviceExporter"]._resolve_site_for_stats.return_value = ("site-1", "SiteName")  # WHY: happy.
        response = MagicMock(name="api_response")  # WHY: opaque handle forwarded into mistapi.get_all.
        wired_deps["mistapi"].api.v1.sites.stats.listSiteWirelessClientsStats.return_value = response  # WHY: seed.
        wired_deps["mistapi"].get_all.return_value = [{"mac": "aa"}]  # WHY: single-row page result.

        SiteClientExporter.clients()  # WHY: exercise happy path.

        # WHY: resolver called with the descriptive stats label.
        wired_deps["SiteDeviceExporter"]._resolve_site_for_stats.assert_called_once_with("client statistics")
        # WHY: API call receives (session, site_id, limit=1000).
        wired_deps["mistapi"].api.v1.sites.stats.listSiteWirelessClientsStats.assert_called_once_with(
            wired_deps["apisession"], "site-1", limit=1000
        )
        # WHY: pagination invoked with the response + session.
        wired_deps["mistapi"].get_all.assert_called_once_with(response=response, mist_session=wired_deps["apisession"])
        # WHY: per-site CSV write follows through the persist path.
        wired_deps["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"mac": "aa"}], "SiteClients_SiteName.csv"
        )

    def test_api_error_is_logged_and_printed(
        self, wired_deps: dict[str, Any], caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When the API raises, the error is logged + printed and no persist occurs."""
        wired_deps["SiteDeviceExporter"]._resolve_site_for_stats.return_value = ("site-1", "SiteName")  # WHY: resolve.
        wired_deps["mistapi"].api.v1.sites.stats.listSiteWirelessClientsStats.side_effect = RuntimeError(
            "boom"
        )  # WHY: force API error branch.

        with caplog.at_level(logging.ERROR, logger="root"):  # WHY: capture the ERROR log.
            SiteClientExporter.clients()  # WHY: exercise exception path.

        assert any(
            "Error fetching client stats for site SiteName" in rec.message for rec in caplog.records
        )  # WHY: log formatting.
        captured = capsys.readouterr()  # WHY: verify user-facing message.
        assert "Error fetching client data" in captured.out  # WHY: user notice.
        # WHY: no persist path was reached.
        wired_deps["DataExporter"].write_with_format_selection.assert_not_called()


class TestClientInsights:
    """`client_insights` delegates to the local-imported SiteClientInsightsService."""

    def test_delegates_to_service_execute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`client_insights` performs a local import and calls SiteClientInsightsService.execute()."""
        service_cls = MagicMock(name="SiteClientInsightsService")  # WHY: witness for delegation.
        monkeypatch.setattr(
            "src.refactors.serial_cc.site_client_insights.SiteClientInsightsService",
            service_cls,
            raising=True,
        )  # WHY: intercept the local import path.

        SiteClientExporter.client_insights()  # WHY: exercise the delegation.

        service_cls.execute.assert_called_once_with()  # WHY: exact delegation contract.


class TestNormalizeClientMacOrNone:
    """Cover all three branches of `_normalize_client_mac_or_none`."""

    def test_empty_input_returns_none(self, wired_deps: dict[str, Any]) -> None:
        """Empty string returns None; validator/normalizer are not called."""
        assert SiteClientExporter._normalize_client_mac_or_none("") is None  # WHY: empty-input branch.
        wired_deps["PacketCaptureManager"].validate_mac_address.assert_not_called()  # WHY: short-circuit.
        wired_deps["PacketCaptureManager"].normalize_mac_address.assert_not_called()  # WHY: short-circuit.

    def test_invalid_mac_returns_none(self, wired_deps: dict[str, Any]) -> None:
        """Validator returning False short-circuits to None without normalizing."""
        wired_deps["PacketCaptureManager"].validate_mac_address.return_value = False  # WHY: invalid MAC.

        assert SiteClientExporter._normalize_client_mac_or_none("not-a-mac") is None  # WHY: invalid branch.

        wired_deps["PacketCaptureManager"].validate_mac_address.assert_called_once_with(
            "not-a-mac"
        )  # WHY: validator was consulted.
        wired_deps["PacketCaptureManager"].normalize_mac_address.assert_not_called()  # WHY: skipped after fail.

    def test_valid_mac_returns_normalized(self, wired_deps: dict[str, Any]) -> None:
        """Valid MAC forwards through normalizer and returns normalized value."""
        wired_deps["PacketCaptureManager"].validate_mac_address.return_value = True  # WHY: valid MAC.
        wired_deps["PacketCaptureManager"].normalize_mac_address.return_value = "aabbccddeeff"  # WHY: normalized.

        result = SiteClientExporter._normalize_client_mac_or_none("aa:bb:cc:dd:ee:ff")  # WHY: valid branch.

        assert result == "aabbccddeeff"  # WHY: normalized value returned.
        wired_deps["PacketCaptureManager"].normalize_mac_address.assert_called_once_with(
            "aa:bb:cc:dd:ee:ff"
        )  # WHY: normalization forwarded.


class TestWifiClients:
    """`wifi_clients` builds WifiClientsExporter with wired kwargs + forwards site_id."""

    def test_constructs_exporter_and_forwards_site_id(self, wired_deps: dict[str, Any]) -> None:
        """Exporter is constructed with the exact kwarg contract and site_id forwarded to execute."""
        instance = MagicMock(name="exporter_instance")  # WHY: witness for execute() call.
        wired_deps["WifiClientsExporter"].return_value = instance  # WHY: seed constructor return.

        SiteClientExporter.wifi_clients(site_id="site-42")  # WHY: exercise facade with site_id.

        # WHY: constructor kwargs match the compatibility facade contract.
        wired_deps["WifiClientsExporter"].assert_called_once_with(
            cache_utils=wired_deps["CacheUtils"],
            org_site_exporter=wired_deps["OrgSiteExporter"],
            prompt_utils=wired_deps["PromptUtils"],
            file_path_utils=wired_deps["FilePathUtils"],
            data_processing_utils=wired_deps["DataProcessingUtils"],
            data_exporter=wired_deps["DataExporter"],
            mistapi_module=wired_deps["mistapi"],
            apisession=wired_deps["apisession"],
        )
        instance.execute.assert_called_once_with(site_id="site-42")  # WHY: site_id forwarded.

    def test_default_site_id_is_none(self, wired_deps: dict[str, Any]) -> None:
        """When site_id omitted, execute receives site_id=None."""
        instance = MagicMock(name="exporter_instance")  # WHY: witness.
        wired_deps["WifiClientsExporter"].return_value = instance  # WHY: seed.

        SiteClientExporter.wifi_clients()  # WHY: exercise default branch.

        instance.execute.assert_called_once_with(site_id=None)  # WHY: default forwarded.


class TestBeacons:
    """`beacons` constructs SiteExportUtils with wired kwargs and calls _export_data."""

    def test_constructs_site_export_utils_and_calls_export_data(self, wired_deps: dict[str, Any]) -> None:
        """SiteExportUtils is constructed with every kwarg wired, then _export_data receives the beacons contract."""
        instance = MagicMock(name="site_export_instance")  # WHY: witness for _export_data call.
        wired_deps["SiteExportUtils"].return_value = instance  # WHY: seed constructor return.

        SiteClientExporter.beacons()  # WHY: exercise beacons path.

        # WHY: constructor received every kwarg the SUT passes.
        wired_deps["SiteExportUtils"].assert_called_once_with(
            apisession=wired_deps["apisession"],
            PromptUtils=wired_deps["PromptUtils"],
            ConfigUtils=wired_deps["ConfigUtils"],
            DataProcessingUtils=wired_deps["DataProcessingUtils"],
            DataExporter=wired_deps["DataExporter"],
            TimeUtils=wired_deps["TimeUtils"],
            EnhancedSSHRunner=wired_deps["EnhancedSSHRunner"],
            InsightMetricsUtils=wired_deps["InsightMetricsUtils"],
            PacketCaptureManager=wired_deps["PacketCaptureManager"],
            APICoreFetchUtils=wired_deps["APICoreFetchUtils"],
            check_fn=wired_deps["IsDebugMode"].check,
            PrettyTable=wired_deps["PrettyTable"],
            tqdm=wired_deps["tqdm"],
            mistapi=wired_deps["mh_mistapi"],
        )
        # WHY: _export_data invoked with the beacons api_call + data_type + sort_key contract.
        instance._export_data.assert_called_once_with(
            api_call=wired_deps["mistapi"].api.v1.sites.beacons.listSiteBeacons,
            data_type="beacons",
            sort_key="name",
        )

    def test_clients_pipeline_call_ordering(self, wired_deps: dict[str, Any]) -> None:
        """clients() call order: resolver -> API call -> pagination -> persist write."""
        wired_deps["SiteDeviceExporter"]._resolve_site_for_stats.return_value = ("s", "N")  # WHY: happy.
        wired_deps["mistapi"].api.v1.sites.stats.listSiteWirelessClientsStats.return_value = MagicMock(name="resp")
        wired_deps["mistapi"].get_all.return_value = [{"mac": "aa"}]  # WHY: one row so persist reaches write.

        order = MagicMock()  # WHY: call-ordering witness.
        order.attach_mock(wired_deps["SiteDeviceExporter"]._resolve_site_for_stats, "resolve")
        order.attach_mock(wired_deps["mistapi"].api.v1.sites.stats.listSiteWirelessClientsStats, "api")
        order.attach_mock(wired_deps["mistapi"].get_all, "paginate")
        order.attach_mock(wired_deps["DataExporter"].write_with_format_selection, "write")

        SiteClientExporter.clients()  # WHY: exercise the full happy pipeline.

        assert order.mock_calls == [  # WHY: exact ordering contract.
            call.resolve("client statistics"),
            call.api(wired_deps["apisession"], "s", limit=1000),
            call.paginate(
                response=wired_deps["mistapi"].api.v1.sites.stats.listSiteWirelessClientsStats.return_value,
                mist_session=wired_deps["apisession"],
            ),
            call.write([{"mac": "aa"}], "SiteClients_N.csv"),
        ]
