"""Unit tests for APIFetchUtils (issue #878 tranche 6 -- un-omit).

Covers every static method on ``src.api.api_fetch_utils``:
``organization_services`` (happy/empty/exception paths),
``_normalize_org_services`` (dict + non-dict entries with defaults),
``_fetch_single_site_setting`` (happy tags + exception -> None),
``all_site_settings`` (iteration, stop signal, failure skip),
``_gw_load_inventory`` (happy + exception),
``_gw_load_site_names`` (CSV parse + failure),
``_gw_build_work_items`` (gateway filter + missing-id skip),
``_gw_fetch_one_config`` (happy tags, empty config, exception),
``_gw_retry_one_item`` (recovery mid-loop + exhaustion),
``_gw_retry_configs`` (keeps only successes),
``_gw_collect_fast`` (delegates to ConnectionPoolExecutor),
``_gw_collect_sequential`` (serial fetch + skip None), and
``gateway_device_configs`` (inventory failure, fast, sequential branches).
"""

from __future__ import annotations

import threading
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.api.api_fetch_utils import APIFetchUtils


def _make_mh(**extra):
    """Assemble a stub MistHelper module with the attributes each method touches."""
    defaults = {
        "ConfigUtils": MagicMock(name="ConfigUtils"),
        "APICoreFetchUtils": MagicMock(name="APICoreFetchUtils"),
        "FilePathUtils": MagicMock(name="FilePathUtils"),
        "FastModeSequentialMaxRetries": SimpleNamespace(VALUE=2),
        "ConnectionPoolExecutor": MagicMock(name="ConnectionPoolExecutor"),
        "apisession": MagicMock(name="apisession"),
    }
    defaults.update(extra)
    return SimpleNamespace(**defaults)


# ---------- organization_services ----------


def test_organization_services_happy_path_returns_normalized_rows() -> None:
    """listOrgServices returns data -> normalized rows include name/type/description/full_config."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    fake_response = SimpleNamespace(data=[{"name": "svc-a", "type": "custom", "description": "d1"}])
    with (
        patch("src.api.api_fetch_utils.mistapi.api.v1.orgs.services.listOrgServices", return_value=fake_response),
        patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh),
    ):
        result = APIFetchUtils.organization_services()
    assert result == [
        {
            "name": "svc-a",
            "type": "custom",
            "description": "d1",
            "full_config": {"name": "svc-a", "type": "custom", "description": "d1"},
        }
    ]


def test_organization_services_empty_data_returns_empty_list() -> None:
    """Empty response data -> return [] and log a warning."""
    fake_mh = _make_mh()
    fake_response = SimpleNamespace(data=[])
    with (
        patch("src.api.api_fetch_utils.mistapi.api.v1.orgs.services.listOrgServices", return_value=fake_response),
        patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh),
    ):
        assert APIFetchUtils.organization_services() == []


def test_organization_services_missing_data_attribute_returns_empty_list() -> None:
    """Response without a ``data`` attribute -> return [] without raising."""
    fake_mh = _make_mh()
    fake_response = SimpleNamespace()
    with (
        patch("src.api.api_fetch_utils.mistapi.api.v1.orgs.services.listOrgServices", return_value=fake_response),
        patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh),
    ):
        assert APIFetchUtils.organization_services() == []


def test_organization_services_exception_returns_empty_list() -> None:
    """Any exception during the API call -> return [] (never crash)."""
    fake_mh = _make_mh()
    fake_mh.ConfigUtils.get_cached_or_prompted_org_id.side_effect = RuntimeError("boom")
    with patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh):
        assert APIFetchUtils.organization_services() == []


# ---------- _normalize_org_services ----------


def test_normalize_org_services_uses_defaults_for_missing_fields() -> None:
    """Dict entries missing name/type/description get sensible defaults."""
    result = APIFetchUtils._normalize_org_services([{}])
    assert result == [
        {
            "name": "unnamed",
            "type": "custom",
            "description": "",
            "full_config": {},
        }
    ]


def test_normalize_org_services_skips_non_dict_entries() -> None:
    """Non-dict entries in the input list are silently skipped."""
    assert APIFetchUtils._normalize_org_services(["not-a-dict", 42, None]) == []


def test_normalize_org_services_preserves_provided_fields() -> None:
    """Provided name/type/description flow through, and full_config is preserved."""
    entry = {"name": "n", "type": "t", "description": "d", "extra": "keep"}
    result = APIFetchUtils._normalize_org_services([entry])
    assert result == [{"name": "n", "type": "t", "description": "d", "full_config": entry}]


# ---------- _fetch_single_site_setting ----------


def test_fetch_single_site_setting_tags_config_with_ids() -> None:
    """Happy path: returned config is tagged with site_id/site_name."""
    fake_response = SimpleNamespace(data={"foo": "bar"})
    apisession = MagicMock()
    with patch(
        "src.api.api_fetch_utils.mistapi.api.v1.sites.setting.getSiteSetting", return_value=fake_response
    ) as api:
        config = APIFetchUtils._fetch_single_site_setting(apisession, {"id": "s1", "name": "SiteOne"})
    api.assert_called_once_with(apisession, "s1")
    assert config == {"foo": "bar", "site_id": "s1", "site_name": "SiteOne"}


def test_fetch_single_site_setting_returns_none_on_exception() -> None:
    """API failure -> return None and log a warning (no raise)."""
    apisession = MagicMock()
    with patch("src.api.api_fetch_utils.mistapi.api.v1.sites.setting.getSiteSetting", side_effect=RuntimeError("bad")):
        assert APIFetchUtils._fetch_single_site_setting(apisession, {"id": "s1"}) is None


# ---------- all_site_settings ----------


def test_all_site_settings_iterates_all_sites_and_skips_failures() -> None:
    """Iterates sites, keeps successes, drops None returns."""
    fake_mh = _make_mh()
    sites = [{"id": "s1", "name": "A"}, {"id": "s2", "name": "B"}, {"id": "s3", "name": "C"}]
    fake_mh.APICoreFetchUtils.all_sites_with_limit.return_value = sites
    fake_mh.ConfigUtils.check_stop_signal.return_value = False

    def fetcher(_apisession, site):
        return None if site["id"] == "s2" else {"site_id": site["id"], "site_name": site["name"]}

    with (
        patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh),
        patch.object(APIFetchUtils, "_fetch_single_site_setting", side_effect=fetcher),
    ):
        result = APIFetchUtils.all_site_settings(MagicMock(), "org-1")

    assert [c["site_id"] for c in result] == ["s1", "s3"]


def test_all_site_settings_stops_when_signal_set() -> None:
    """check_stop_signal True -> iteration exits early."""
    fake_mh = _make_mh()
    sites = [{"id": "s1"}, {"id": "s2"}]
    fake_mh.APICoreFetchUtils.all_sites_with_limit.return_value = sites
    fake_mh.ConfigUtils.check_stop_signal.return_value = True

    with (
        patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh),
        patch.object(APIFetchUtils, "_fetch_single_site_setting") as fetcher,
    ):
        result = APIFetchUtils.all_site_settings(MagicMock(), "org-1")

    fetcher.assert_not_called()
    assert result == []


# ---------- _gw_load_inventory ----------


def test_gw_load_inventory_happy_path_returns_paginated_devices() -> None:
    """mistapi.get_all is called with the initial response and its result returned."""
    apisession = MagicMock()
    fake_response = SimpleNamespace(data=[{"id": "d1"}])
    devices = [{"id": "d1"}, {"id": "d2"}]
    with (
        patch(
            "src.api.api_fetch_utils.mistapi.api.v1.orgs.inventory.getOrgInventory", return_value=fake_response
        ) as inv_call,
        patch("src.api.api_fetch_utils.mistapi.get_all", return_value=devices) as get_all,
    ):
        result = APIFetchUtils._gw_load_inventory(apisession, "org-1")
    inv_call.assert_called_once_with(apisession, "org-1", limit=1000)
    get_all.assert_called_once_with(response=fake_response, mist_session=apisession)
    assert result == devices


def test_gw_load_inventory_returns_none_on_exception() -> None:
    """Inventory fetch failure -> return None."""
    with patch(
        "src.api.api_fetch_utils.mistapi.api.v1.orgs.inventory.getOrgInventory", side_effect=RuntimeError("nope")
    ):
        assert APIFetchUtils._gw_load_inventory(MagicMock(), "org-1") is None


# ---------- _gw_load_site_names ----------


def test_gw_load_site_names_parses_csv_into_id_name_map(tmp_path) -> None:
    """SiteList.csv is parsed into an id -> name dict via DictReader."""
    fake_mh = _make_mh()
    csv_path = tmp_path / "SiteList.csv"
    csv_path.write_text("id,name\ns1,SiteOne\ns2,SiteTwo\n", encoding="utf-8")
    fake_mh.FilePathUtils.get_csv_path.return_value = str(csv_path)
    with patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh):
        result = APIFetchUtils._gw_load_site_names()
    assert result == {"s1": "SiteOne", "s2": "SiteTwo"}


def test_gw_load_site_names_defaults_missing_name_column(tmp_path) -> None:
    """Rows lacking a name column default to 'Unnamed Site'."""
    fake_mh = _make_mh()
    csv_path = tmp_path / "SiteList.csv"
    csv_path.write_text("id\ns1\n", encoding="utf-8")
    fake_mh.FilePathUtils.get_csv_path.return_value = str(csv_path)
    with patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh):
        result = APIFetchUtils._gw_load_site_names()
    assert result == {"s1": "Unnamed Site"}


def test_gw_load_site_names_returns_empty_on_missing_file() -> None:
    """Missing CSV -> return {} without raising."""
    fake_mh = _make_mh()
    fake_mh.FilePathUtils.get_csv_path.return_value = "/nonexistent/SiteList.csv"
    with patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh):
        assert APIFetchUtils._gw_load_site_names() == {}


# ---------- _gw_build_work_items ----------


def test_gw_build_work_items_keeps_only_gateways_with_ids() -> None:
    """Non-gateway devices, missing site_id, and missing device_id are all filtered out."""
    inventory = [
        {"type": "gateway", "id": "d1", "site_id": "s1"},
        {"type": "ap", "id": "d2", "site_id": "s2"},  # not a gateway
        {"type": "gateway", "id": "d3"},  # no site_id
        {"type": "gateway", "site_id": "s4"},  # no device id
        {"type": "gateway", "id": "d5", "site_id": "s5"},
    ]
    site_names = {"s1": "SiteOne"}
    work_items = APIFetchUtils._gw_build_work_items(inventory, site_names)
    assert work_items == [
        ("s1", "d1", "SiteOne"),
        ("s5", "d5", "Unknown"),
    ]


# ---------- _gw_fetch_one_config ----------


def test_gw_fetch_one_config_happy_path_tags_config() -> None:
    """Non-empty config is tagged with site_id/site_name and returned."""
    apisession = MagicMock()
    fake_response = SimpleNamespace(data={"foo": "bar"})
    sem = threading.Semaphore(1)
    with patch("src.api.api_fetch_utils.mistapi.api.v1.sites.devices.getSiteDevice", return_value=fake_response) as api:
        config = APIFetchUtils._gw_fetch_one_config(apisession, ("s1", "d1", "SiteOne"), sem)
    api.assert_called_once_with(apisession, "s1", "d1")
    assert config == {"foo": "bar", "site_name": "SiteOne", "site_id": "s1"}


def test_gw_fetch_one_config_empty_config_returns_none() -> None:
    """Empty response data -> return None."""
    fake_response = SimpleNamespace(data={})
    sem = threading.Semaphore(1)
    with patch("src.api.api_fetch_utils.mistapi.api.v1.sites.devices.getSiteDevice", return_value=fake_response):
        assert APIFetchUtils._gw_fetch_one_config(MagicMock(), ("s1", "d1", "SiteOne"), sem) is None


def test_gw_fetch_one_config_missing_data_attr_returns_none() -> None:
    """Response with no ``data`` attribute -> return None (getattr default is {})."""
    fake_response = SimpleNamespace()
    sem = threading.Semaphore(1)
    with patch("src.api.api_fetch_utils.mistapi.api.v1.sites.devices.getSiteDevice", return_value=fake_response):
        assert APIFetchUtils._gw_fetch_one_config(MagicMock(), ("s1", "d1", "SiteOne"), sem) is None


def test_gw_fetch_one_config_exception_returns_none() -> None:
    """Exception in API call -> return None (logged, not raised)."""
    sem = threading.Semaphore(1)
    with patch("src.api.api_fetch_utils.mistapi.api.v1.sites.devices.getSiteDevice", side_effect=RuntimeError("bad")):
        assert APIFetchUtils._gw_fetch_one_config(MagicMock(), ("s1", "d1", "SiteOne"), sem) is None


# ---------- _gw_retry_one_item ----------


def test_gw_retry_one_item_succeeds_on_second_attempt() -> None:
    """Returns the recovered config once a retry produces a non-None result."""
    sem = threading.Semaphore(1)
    results = [None, {"foo": "bar", "site_id": "s1"}]
    with (
        patch.object(APIFetchUtils, "_gw_fetch_one_config", side_effect=results) as fetch,
        patch("src.api.api_fetch_utils.time.sleep") as sleep,
    ):
        out = APIFetchUtils._gw_retry_one_item(MagicMock(), ("s1", "d1", "SiteOne"), sem, max_retries=2)
    assert out == {"foo": "bar", "site_id": "s1"}
    assert fetch.call_count == 2
    sleep.assert_called_once()


def test_gw_retry_one_item_returns_none_after_exhausting_attempts() -> None:
    """All attempts return None -> function returns None after max_retries+1 tries."""
    sem = threading.Semaphore(1)
    with (
        patch.object(APIFetchUtils, "_gw_fetch_one_config", return_value=None) as fetch,
        patch("src.api.api_fetch_utils.time.sleep") as sleep,
    ):
        out = APIFetchUtils._gw_retry_one_item(MagicMock(), ("s1", "d1", "SiteOne"), sem, max_retries=2)
    assert out is None
    assert fetch.call_count == 3  # initial + 2 retries
    assert sleep.call_count == 2  # sleep before each retry, not after last attempt


# ---------- _gw_retry_configs ----------


def test_gw_retry_configs_keeps_only_successful_retries() -> None:
    """Only recovered configs are appended to the result list."""
    fake_mh = _make_mh()
    sem = threading.Semaphore(1)
    failed_items = [("s1", "d1", "A"), ("s2", "d2", "B"), ("s3", "d3", "C")]
    recovered = [{"id": "d1"}, None, {"id": "d3"}]
    with (
        patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh),
        patch.object(APIFetchUtils, "_gw_retry_one_item", side_effect=recovered),
    ):
        out = APIFetchUtils._gw_retry_configs(MagicMock(), failed_items, sem)
    assert out == [{"id": "d1"}, {"id": "d3"}]


# ---------- _gw_collect_fast ----------


def test_gw_collect_fast_delegates_to_pool_executor() -> None:
    """Fast path routes work_items through ConnectionPoolExecutor.execute and returns successes."""
    fake_mh = _make_mh()
    successes = [{"id": "d1"}, {"id": "d2"}]
    fake_mh.ConnectionPoolExecutor.execute.return_value = (successes, [])
    work_items = [("s1", "d1", "A"), ("s2", "d2", "B")]
    with patch("src.api.api_fetch_utils.importlib.import_module", return_value=fake_mh):
        out = APIFetchUtils._gw_collect_fast(MagicMock(), work_items)
    assert out == successes
    call = fake_mh.ConnectionPoolExecutor.execute.call_args
    assert call.kwargs["work_items"] == work_items
    assert call.kwargs["batch_description"] == "gateway device configs"
    assert callable(call.kwargs["worker_function"])
    assert callable(call.kwargs["retry_function"])


# ---------- _gw_collect_sequential ----------


def test_gw_collect_sequential_fetches_each_item_and_skips_none() -> None:
    """Sequential path calls fetch per item, drops None returns, preserves ordering."""
    work_items = [("s1", "d1", "A"), ("s2", "d2", "B"), ("s3", "d3", "C")]
    results = [{"id": "d1"}, None, {"id": "d3"}]
    with patch.object(APIFetchUtils, "_gw_fetch_one_config", side_effect=results) as fetch:
        out = APIFetchUtils._gw_collect_sequential(MagicMock(), work_items)
    assert out == [{"id": "d1"}, {"id": "d3"}]
    assert fetch.call_count == 3


# ---------- gateway_device_configs ----------


def test_gateway_device_configs_returns_empty_when_inventory_fetch_fails() -> None:
    """Inventory None -> return [] without attempting any fetches."""
    with (
        patch.object(APIFetchUtils, "_gw_load_inventory", return_value=None),
        patch.object(APIFetchUtils, "_gw_build_work_items") as build,
    ):
        out = APIFetchUtils.gateway_device_configs(MagicMock(), "org-1")
    assert out == []
    build.assert_not_called()


def test_gateway_device_configs_fast_path_uses_pool_collect() -> None:
    """fast=True routes work items through _gw_collect_fast."""
    inventory = [{"type": "gateway", "id": "d1", "site_id": "s1"}]
    work_items = [("s1", "d1", "SiteOne")]
    fast_result = [{"id": "d1", "site_id": "s1"}]
    with (
        patch.object(APIFetchUtils, "_gw_load_inventory", return_value=inventory),
        patch.object(APIFetchUtils, "_gw_load_site_names", return_value={"s1": "SiteOne"}),
        patch.object(APIFetchUtils, "_gw_build_work_items", return_value=work_items),
        patch.object(APIFetchUtils, "_gw_collect_fast", return_value=fast_result) as fast,
        patch.object(APIFetchUtils, "_gw_collect_sequential") as seq,
    ):
        out = APIFetchUtils.gateway_device_configs(MagicMock(), "org-1", fast=True)
    fast.assert_called_once()
    seq.assert_not_called()
    assert out == fast_result


def test_gateway_device_configs_sequential_path_filters_none_results() -> None:
    """fast=False routes through _gw_collect_sequential and drops leftover Nones."""
    inventory = [{"type": "gateway", "id": "d1", "site_id": "s1"}]
    work_items = [("s1", "d1", "SiteOne")]
    seq_result = [{"id": "d1"}, None, {"id": "d2"}]
    with (
        patch.object(APIFetchUtils, "_gw_load_inventory", return_value=inventory),
        patch.object(APIFetchUtils, "_gw_load_site_names", return_value={"s1": "SiteOne"}),
        patch.object(APIFetchUtils, "_gw_build_work_items", return_value=work_items),
        patch.object(APIFetchUtils, "_gw_collect_sequential", return_value=seq_result) as seq,
        patch.object(APIFetchUtils, "_gw_collect_fast") as fast,
    ):
        out = APIFetchUtils.gateway_device_configs(MagicMock(), "org-1", fast=False, max_workers=8)
    fast.assert_not_called()
    seq.assert_called_once()
    assert out == [{"id": "d1"}, {"id": "d2"}]
