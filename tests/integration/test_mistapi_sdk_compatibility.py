"""Integration smoke coverage for the MistAPI SDK compatibility audit.

These tests exercise the current MistHelper entry points with lightweight
monkeypatched SDK responses so the compatibility surface stays in one file.
"""

import csv
from types import SimpleNamespace

import MistHelper


def test_alarm_export_uses_search_org_alarms(monkeypatch):
    captured: dict[str, object] = {}

    class FakeAPIDataFetcher:
        def __init__(self, **kwargs):
            captured["kwargs"] = kwargs

        def execute(self) -> None:
            captured["executed"] = True

    monkeypatch.setattr(MistHelper, "APIDataFetcher", FakeAPIDataFetcher)
    monkeypatch.setattr(
        MistHelper.TimeUtils, "get_dynamic_lookback_hours", lambda *_args, **_kwargs: 24
    )
    monkeypatch.setattr(
        MistHelper.TimeUtils, "log_dynamic_lookback", lambda *_args, **_kwargs: None
    )

    MistHelper.OrgAlarmEventExporter.alarms()

    assert captured["executed"] is True
    kwargs = captured["kwargs"]
    assert kwargs["api_call"] is MistHelper.mistapi.api.v1.orgs.alarms.searchOrgAlarms
    assert kwargs["filename"] == "OrgAlarms.csv"
    assert kwargs["acked"] is False
    assert kwargs["duration"] == "24h"


def test_device_events_52w_paginates_and_writes_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(
        MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1"
    )
    monkeypatch.chdir(tmp_path)

    def search_stub(
        session, org_id, device_type, limit, duration, *, search_after=None
    ):
        response = SimpleNamespace()
        if not search_after:
            response.data = {
                "results": [
                    {"id": "e1", "timestamp": "2026-01-01T00:00:00Z"},
                    {"id": "e2", "timestamp": "2026-01-02T00:00:00Z"},
                ],
                "search_after": "token1",
            }
        elif search_after == "token1":
            response.data = {
                "results": [{"id": "e3", "timestamp": "2026-01-03T00:00:00Z"}],
                "search_after": None,
            }
        else:
            response.data = {"results": [], "search_after": None}
        return response

    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.orgs.devices, "searchOrgDeviceEvents", search_stub
    )

    MistHelper.OrgAlarmEventExporter.device_events_52w()

    csv_path = tmp_path / "data" / "OrgDeviceEvents_52w.csv"
    assert csv_path.exists(), f"Expected CSV at {csv_path}"

    with open(csv_path, newline="", encoding="utf-8") as file_handle:
        rows = list(csv.DictReader(file_handle))

    assert len(rows) == 3
    assert [row.get("id") for row in rows] == ["e1", "e2", "e3"]


def test_site_client_stats_export_uses_stats_endpoint(monkeypatch, tmp_path):
    monkeypatch.setattr(MistHelper.PromptUtils, "select_site", lambda: "site-1")
    monkeypatch.setattr(
        MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1"
    )
    monkeypatch.setattr(
        MistHelper.APICoreFetchUtils,
        "all_sites_with_limit",
        lambda *_args, **_kwargs: [{"id": "site-1", "name": "Site One"}],
    )
    monkeypatch.chdir(tmp_path)

    captured: dict[str, object] = {}

    def list_site_wireless_clients_stats_stub(*_args, **_kwargs):
        captured["site_id"] = _kwargs.get("site_id") or (
            _args[1] if len(_args) > 1 else None
        )
        return SimpleNamespace(
            data=[{"mac": "00:11:22:33:44:55", "hostname": "Client One"}]
        )

    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.sites.stats,
        "listSiteWirelessClientsStats",
        list_site_wireless_clients_stats_stub,
    )
    monkeypatch.setattr(
        MistHelper.mistapi, "get_all", lambda response, mist_session: response.data
    )
    monkeypatch.setattr(
        MistHelper.DataExporter,
        "save_data_to_output",
        lambda data, filename: captured.update({"data": data, "filename": filename}),
    )

    MistHelper.SiteClientExporter.clients()

    assert captured["site_id"] == "site-1"
    assert str(captured["filename"]).startswith("SiteClients_Site_One")


def test_sites_sle_summary_writes_output(monkeypatch, tmp_path):
    monkeypatch.setattr(
        MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1"
    )
    monkeypatch.chdir(tmp_path)

    sle_calls: list[str] = []

    def get_org_sites_sle_stub(*_args, **kwargs):
        sle_calls.append(kwargs["sle"])
        return SimpleNamespace(data=[{"site_id": f"{kwargs['sle']}-site", "score": 88}])

    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.orgs.insights,
        "getOrgSitesSle",
        get_org_sites_sle_stub,
    )
    monkeypatch.setattr(
        MistHelper.mistapi, "get_all", lambda response, mist_session: response.data
    )

    captured: dict[str, object] = {}
    monkeypatch.setattr(
        MistHelper.DataExporter,
        "save_data_to_output",
        lambda data, filename: captured.update({"data": data, "filename": filename}),
    )

    MistHelper.OrgExportUtils.sites_sle_summary()

    assert sle_calls == ["wifi", "wired", "wan"]
    assert captured["filename"] == "OrgSitesSLESummary.csv"
    assert {row["sle_type"] for row in captured["data"]} == {"wifi", "wired", "wan"}


def test_maps_and_wlan_helpers_are_covered(monkeypatch):
    map_lookup: dict[str, str] = {}
    wlan_band_lookup: dict[str, list[str]] = {}
    call_state = {"count": 0}

    def get_all_stub(*_args, **_kwargs):
        call_state["count"] += 1
        if call_state["count"] == 1:
            return [{"id": "map-1", "name": "First Floor"}]
        return [{"enabled": True, "ssid": "Corp WiFi", "band": "5"}]

    monkeypatch.setattr(MistHelper.mistapi, "get_all", get_all_stub)
    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.sites.maps,
        "listSiteMaps",
        lambda *_args, **_kwargs: SimpleNamespace(status_code=200),
    )
    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.sites.wlans,
        "listSiteWlans",
        lambda *_args, **_kwargs: SimpleNamespace(status_code=200),
    )

    # Pass apisession + page_limit to match actual signature
    MistHelper.E911BSSIDReportGenerator._fetch_site_maps(
        MistHelper.mistapi, "site-1", 1000, map_lookup
    )
    MistHelper.E911BSSIDReportGenerator._resolve_site_ssids(
        MistHelper.mistapi,  # apisession param
        "site-1",  # site_id param
        1000,  # page_limit param
        {"sitetemplate_id": "", "sitegroup_ids": []},  # site_info
        [],  # wlan_templates
        [],  # org_wlans
        wlan_band_lookup,  # wlan_band_lookup
        {},  # site_template_cache
    )

    assert map_lookup["map-1"] == "First Floor"
    assert wlan_band_lookup["site-1::band_5"] == ["Corp WiFi"]


def test_client_insights_uses_metrics_keyword(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(MistHelper.PromptUtils, "select_site", lambda: "site-1")
    monkeypatch.setattr(MistHelper.InsightMetricsUtils, "export_legacy", lambda: None)
    monkeypatch.setattr(
        MistHelper.InsightMetricsUtils, "get_by_scope", lambda scope: ["metric-one"]
    )
    monkeypatch.setattr(
        MistHelper.EnhancedSSHRunner,
        "sanitize_filename",
        lambda value: value.replace(" ", "_"),
    )

    site_response = [{"id": "site-1", "name": "Site One"}]
    client_response = [
        {"mac": "00:11:22:33:44:55", "hostname": "Client One", "last_seen": "now"}
    ]
    get_all_calls = {"count": 0}

    def get_all_stub(*_args, **_kwargs):
        get_all_calls["count"] += 1
        return site_response if get_all_calls["count"] == 1 else client_response

    monkeypatch.setattr(MistHelper.mistapi, "get_all", get_all_stub)
    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.sites,
        "listSites",
        lambda *_args, **_kwargs: object(),
        raising=False,
    )
    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.sites.stats,
        "listSiteWirelessClientsStats",
        lambda *_args, **_kwargs: object(),
    )

    captured: dict[str, object] = {}

    def get_client_insight_stub(apisession, site_id, client_mac, *, metrics):
        captured["site_id"] = site_id
        captured["client_mac"] = client_mac
        captured["metrics"] = metrics
        return SimpleNamespace(data={"value": 42})

    monkeypatch.setattr(
        MistHelper.mistapi.api.v1.sites.insights,
        "getSiteInsightMetricsForClient",
        get_client_insight_stub,
    )
    monkeypatch.setattr(
        MistHelper.DataExporter, "save_data_to_output", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: "0")

    MistHelper.SiteClientExporter.client_insights()

    assert captured["site_id"] == "site-1"
    assert captured["client_mac"] == "00:11:22:33:44:55"
    assert captured["metrics"] == "metric-one"


def test_e911_report_runs_with_stubbed_maps_and_wlans(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1"
    )
    monkeypatch.setattr(
        MistHelper.E911BSSIDReportGenerator,
        "_load_checkpoint",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        MistHelper.E911BSSIDReportGenerator, "_clear_checkpoint", lambda: None
    )

    org_data = {
        "sites": {
            "site-1": {
                "name": "Site One",
                "address": "1 Main St",
                "sitegroup_ids": [],
                "sitetemplate_id": "",
            }
        },
        "aps": {
            "aa:bb:cc:dd:ee:ff": {
                "name": "AP One",
                "site_id": "site-1",
                "map_id": "map-1",
            }
        },
        "wlan_templates": [],
        "org_wlans": [],
        "site_template_cache": {},
        "radio_macs": [
            {
                "mac": "aa:bb:cc:dd:ee:ff",
                "radio_mac": ["11:22:33:44:55:66"],
            }
        ],
        "radio_bands": {"11:22:33:44:55:66": {"band": "5 GHz", "band_key": "band_5"}},
    }

    monkeypatch.setattr(
        MistHelper.E911BSSIDReportGenerator,
        "_fetch_org_bulk_data",
        lambda *_args, **_kwargs: org_data,
    )

    def fetch_site_maps(
        apisession, site_id, page_limit, map_lookup
    ):  # Added apisession, page_limit params
        map_lookup["map-1"] = "First Floor"  # Populate lookup table for test assertion

    # Stub accepts full method signature including apisession + page_limit
    def resolve_site_ssids(
        apisession,
        site_id,
        page_limit,
        site_info,
        wlan_templates,
        org_wlans,
        wlan_band_lookup,
        site_template_cache,
    ):
        wlan_band_lookup[f"{site_id}::band_5"] = ["Corp WiFi"]

    monkeypatch.setattr(
        MistHelper.E911BSSIDReportGenerator, "_fetch_site_maps", fetch_site_maps
    )
    monkeypatch.setattr(
        MistHelper.E911BSSIDReportGenerator, "_resolve_site_ssids", resolve_site_ssids
    )

    captured: dict[str, object] = {}

    def write_with_format_selection_stub(*, data, filename_or_table, api_function_name):
        captured["data"] = data
        captured["filename"] = filename_or_table
        captured["api_function_name"] = api_function_name

    monkeypatch.setattr(
        MistHelper.DataExporter,
        "write_with_format_selection",
        write_with_format_selection_stub,
    )

    MistHelper.E911BSSIDReportGenerator.execute(  # Call with all 5 required keyword arguments
        apisession=MistHelper.mistapi,  # Mist API session object
        page_limit=1000,  # Default page limit for API calls
        org_id="org-1",  # Test org ID from fixtures
        safe_input_fn=lambda: "Y",  # Mock user confirmation (press Y)
        write_data_fn=lambda *a, **k: None,  # Mock data export (no-op for test)
    )

    assert captured["api_function_name"] == "generateE911BSSIDReport"
    assert str(captured["filename"]).startswith("E911_BSSID_Report_")
    assert captured["data"][0]["Site Name"] == "Site One"
    assert captured["data"][0]["Map Name"] == "First Floor"
    assert captured["data"][0]["SSIDs on Band"] == "Corp WiFi"
