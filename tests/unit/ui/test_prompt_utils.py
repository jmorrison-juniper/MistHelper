"""Unit tests for ``src.ui.prompt_utils.PromptUtils``.

Why:
    Un-omit ``src/ui/prompt_utils.py`` (issue #878 tranche 34) and drive 100%
    line + branch coverage over the 25 static prompt/selection helpers. The
    module leans on a lazy ``importlib.import_module("MistHelper")`` for live
    globals (``apisession``, ``DataExporter``, ``LAST_SELECTED_SITE_ID``);
    tests replace that lookup with a ``SimpleNamespace`` fake through
    ``patch("src.ui.prompt_utils.importlib.import_module", ...)`` -- the
    canonical pattern established by the tranche 33 exemplar.
"""

from __future__ import annotations

# WHY (#886 Phase 2): PromptUtils now emits via logging.warning instead of print, so tests capture via caplog.
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from prettytable import PrettyTable

from src.ui.prompt_utils import PromptUtils


def _make_mh(**extra):
    """Return a ``SimpleNamespace`` stand-in for the MistHelper module.

    Why:
        ``PromptUtils`` reads ``mh.apisession``, ``mh.DataExporter``, and
        ``mh.LAST_SELECTED_SITE_ID`` via a lazy ``importlib.import_module``
        call. A ``SimpleNamespace`` lets tests both read and assign
        attributes (needed for the ``LAST_SELECTED_SITE_ID`` write path).

    Args:
        **extra: Attribute overrides merged into the defaults.

    Returns:
        A ``SimpleNamespace`` populated with mock collaborators.
    """
    defaults = {
        "apisession": MagicMock(name="apisession"),
        "DataExporter": MagicMock(name="DataExporter"),
        "LAST_SELECTED_SITE_ID": None,
    }
    defaults.update(extra)
    return SimpleNamespace(**defaults)


# ---------- _filter_inventory_by_type ----------


def test_filter_inventory_by_type_all_passthrough() -> None:
    """``device_type='all'`` returns the input list unchanged."""
    inv = [{"type": "ap"}, {"type": "switch"}]
    assert PromptUtils._filter_inventory_by_type(inv, "all") is inv


def test_filter_inventory_by_type_comma_split_case_insensitive() -> None:
    """Comma-split filter matches on ``type`` case-insensitively."""
    inv = [{"type": "AP"}, {"type": "switch"}, {"type": "gateway"}]
    result = PromptUtils._filter_inventory_by_type(inv, "ap, switch")
    assert result == [{"type": "AP"}, {"type": "switch"}]


def test_filter_inventory_by_type_no_match() -> None:
    """Filter returns empty list when no rows match."""
    inv = [{"type": "ap"}]
    assert PromptUtils._filter_inventory_by_type(inv, "gateway") == []


def test_filter_inventory_by_type_missing_type_key() -> None:
    """Rows without a ``type`` key never match a non-all filter."""
    inv = [{"name": "foo"}]
    assert PromptUtils._filter_inventory_by_type(inv, "ap") == []


# ---------- _fetch_and_filter_devices ----------


def test_fetch_and_filter_devices_empty_rawdata(caplog: pytest.LogCaptureFixture) -> None:
    """Empty API response logs a warning and returns None."""
    fake_mh = _make_mh()
    fake_response = SimpleNamespace(data=[])
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.sites.devices.listSiteDevices",
            return_value=fake_response,
        ),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
        caplog.at_level(logging.WARNING),
    ):
        result = PromptUtils._fetch_and_filter_devices("site-1", "all")
    assert result is None
    assert "No devices found" in caplog.text


def test_fetch_and_filter_devices_empty_after_filter(caplog: pytest.LogCaptureFixture) -> None:
    """Empty post-filter set logs a warning and returns None."""
    fake_mh = _make_mh()
    fake_response = SimpleNamespace(data=[{"type": "ap"}])
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.sites.devices.listSiteDevices",
            return_value=fake_response,
        ),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
        caplog.at_level(logging.WARNING),
    ):
        result = PromptUtils._fetch_and_filter_devices("site-1", "gateway")
    assert result is None
    assert "No devices of type 'gateway'" in caplog.text


def test_fetch_and_filter_devices_happy_path() -> None:
    """Filtered list is returned when rawdata contains a matching type."""
    fake_mh = _make_mh()
    fake_response = SimpleNamespace(data=[{"type": "ap"}, {"type": "switch"}])
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.sites.devices.listSiteDevices",
            return_value=fake_response,
        ),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        result = PromptUtils._fetch_and_filter_devices("site-1", "ap")
    assert result == [{"type": "ap"}]


# ---------- _export_and_index_inventory ----------


def test_export_and_index_inventory_builds_maps_and_calls_exporter() -> None:
    """Sorts by model, flattens/escapes, exports CSV, returns table + maps."""
    fake_mh = _make_mh()
    rawdata = [
        {"name": "b-dev", "mac": "22", "model": "B", "serial": "s2", "id": "d2"},
        {"name": "a-dev", "mac": "11", "model": "A", "serial": "s1", "id": "d1"},
    ]
    with (
        patch(
            "src.ui.prompt_utils.DataProcessingUtils.flatten_nested_fields",
            side_effect=lambda x: x,
        ),
        patch(
            "src.ui.prompt_utils.DataProcessingUtils.escape_multiline",
            side_effect=lambda x: x,
        ),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        table, index_map, name_map = PromptUtils._export_and_index_inventory(rawdata, "out.csv")
    assert isinstance(table, PrettyTable)
    assert index_map[0]["name"] == "a-dev"
    assert index_map[1]["name"] == "b-dev"
    assert name_map["a-dev"]["id"] == "d1"
    assert name_map["b-dev"]["id"] == "d2"
    fake_mh.DataExporter.write_with_format_selection.assert_called_once()


# ---------- _resolve_device_selection ----------


def test_resolve_device_selection_by_valid_index_strips_dot() -> None:
    """Leading dot is stripped and a valid numeric index resolves to device id."""
    index_map = {0: {"id": "d0"}, 1: {"id": "d1"}}
    assert PromptUtils._resolve_device_selection(".1", index_map, {}) == "d1"


def test_resolve_device_selection_invalid_index_returns_none() -> None:
    """An out-of-range numeric index returns None."""
    assert PromptUtils._resolve_device_selection("9", {0: {"id": "d0"}}, {}) is None


def test_resolve_device_selection_by_name() -> None:
    """A name match returns the device id."""
    name_map = {"alpha": {"id": "d-alpha"}}
    assert PromptUtils._resolve_device_selection("alpha", {}, name_map) == "d-alpha"


def test_resolve_device_selection_name_miss_returns_none() -> None:
    """A non-matching non-numeric input returns None."""
    assert PromptUtils._resolve_device_selection("nope", {}, {}) is None


# ---------- select_device_id_from_inventory ----------


def test_select_device_id_from_inventory_nothing_matched_aborts() -> None:
    """Returns None when the fetch/filter pipeline is empty."""
    with patch.object(PromptUtils, "_fetch_and_filter_devices", return_value=None):
        assert PromptUtils.select_device_id_from_inventory("site-1") is None


def test_select_device_id_from_inventory_happy_path(caplog: pytest.LogCaptureFixture) -> None:
    """End-to-end: fetch, export, prompt, resolve returns device id."""
    fake_table = MagicMock(name="table")
    with (
        patch.object(PromptUtils, "_fetch_and_filter_devices", return_value=[{"id": "d1"}]),
        patch.object(
            PromptUtils,
            "_export_and_index_inventory",
            return_value=(fake_table, {0: {"id": "d1"}}, {"alpha": {"id": "d1"}}),
        ),
        patch("src.ui.prompt_utils.InputUtils.safe_input", return_value="0  "),
        patch.object(PromptUtils, "_resolve_device_selection", return_value="d1"),
        caplog.at_level(logging.WARNING),
    ):
        assert PromptUtils.select_device_id_from_inventory("site-1") == "d1"
    # Ensures the table render path emitted at least one log record.
    assert caplog.records  # Non-empty log captured.


# ---------- _load_site_csv_maps ----------


def test_load_site_csv_maps_reads_csv(tmp_path) -> None:
    """Returns index-to-row and name-to-row maps derived from CSV."""
    csv_path = tmp_path / "sites.csv"
    csv_path.write_text("id,name\nid-1,Alpha\nid-2,Beta\n", encoding="utf-8")
    with patch("src.ui.prompt_utils.FilePathUtils.get_csv_path", return_value=str(csv_path)):
        idx_map, name_map = PromptUtils._load_site_csv_maps("sites.csv")
    assert idx_map[0]["name"] == "Alpha"
    assert idx_map[1]["name"] == "Beta"
    assert name_map["Alpha"]["id"] == "id-1"
    assert name_map["Beta"]["id"] == "id-2"


def test_load_site_csv_maps_skips_rows_without_name(tmp_path) -> None:
    """Rows missing the ``name`` column do not appear in the name map."""
    csv_path = tmp_path / "sites.csv"
    csv_path.write_text("id,other\nid-1,x\n", encoding="utf-8")
    with patch("src.ui.prompt_utils.FilePathUtils.get_csv_path", return_value=str(csv_path)):
        _, name_map = PromptUtils._load_site_csv_maps("sites.csv")
    assert name_map == {}


# ---------- _pick_site_by_index / _pick_site_by_name ----------


def test_pick_site_by_index_invalid(caplog: pytest.LogCaptureFixture) -> None:
    """Out-of-range index logs ``Invalid index`` and returns None."""
    with caplog.at_level(logging.WARNING):
        assert PromptUtils._pick_site_by_index(9, {0: {"id": "x"}}) is None
    assert "Invalid site index" in caplog.text


def test_pick_site_by_index_valid(caplog: pytest.LogCaptureFixture) -> None:
    """Valid index returns the site id."""
    with caplog.at_level(logging.WARNING):
        result = PromptUtils._pick_site_by_index(0, {0: {"id": "id-1", "name": "Alpha"}})
    assert result == "id-1"
    assert "Selected site: Alpha" in caplog.text


def test_pick_site_by_name(caplog: pytest.LogCaptureFixture) -> None:
    """Name lookup returns site id and logs confirmation."""
    with caplog.at_level(logging.WARNING):
        result = PromptUtils._pick_site_by_name("Alpha", {"Alpha": {"id": "id-1"}})
    assert result == "id-1"
    assert "Selected site: Alpha" in caplog.text


# ---------- select_site_id_from_csv ----------


def test_select_site_id_from_csv_by_index(caplog: pytest.LogCaptureFixture) -> None:
    """Digit input picks site by index and caches to ``mh.LAST_SELECTED_SITE_ID``."""
    fake_mh = _make_mh()
    with (
        patch("src.ui.prompt_utils.CacheUtils.check_and_generate_csv"),
        patch.object(
            PromptUtils,
            "_load_site_csv_maps",
            return_value=({0: {"id": "s0", "name": "A"}}, {"A": {"id": "s0"}}),
        ),
        patch("src.ui.prompt_utils.InputUtils.safe_input", return_value="0"),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
        caplog.at_level(logging.WARNING),
    ):
        result = PromptUtils.select_site_id_from_csv()
    assert result == "s0"
    assert fake_mh.LAST_SELECTED_SITE_ID == "s0"
    assert "Available Sites" in caplog.text


def test_select_site_id_from_csv_index_invalid_keeps_last_selected_unset() -> None:
    """Invalid index returns None and leaves ``LAST_SELECTED_SITE_ID`` untouched."""
    fake_mh = _make_mh()
    with (
        patch("src.ui.prompt_utils.CacheUtils.check_and_generate_csv"),
        patch.object(
            PromptUtils,
            "_load_site_csv_maps",
            return_value=({0: {"id": "s0", "name": "A"}}, {"A": {"id": "s0"}}),
        ),
        patch("src.ui.prompt_utils.InputUtils.safe_input", return_value="99"),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        result = PromptUtils.select_site_id_from_csv()
    assert result is None
    assert fake_mh.LAST_SELECTED_SITE_ID is None


def test_select_site_id_from_csv_by_name() -> None:
    """Name input picks site by name and caches selection."""
    fake_mh = _make_mh()
    with (
        patch("src.ui.prompt_utils.CacheUtils.check_and_generate_csv"),
        patch.object(
            PromptUtils,
            "_load_site_csv_maps",
            return_value=({0: {"id": "s0", "name": "A"}}, {"A": {"id": "s0"}}),
        ),
        patch("src.ui.prompt_utils.InputUtils.safe_input", return_value="A"),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        result = PromptUtils.select_site_id_from_csv()
    assert result == "s0"
    assert fake_mh.LAST_SELECTED_SITE_ID == "s0"


def test_select_site_id_from_csv_not_found(caplog: pytest.LogCaptureFixture) -> None:
    """Unmatched input logs ``Site not found`` and returns None."""
    fake_mh = _make_mh()
    with (
        patch("src.ui.prompt_utils.CacheUtils.check_and_generate_csv"),
        patch.object(
            PromptUtils,
            "_load_site_csv_maps",
            return_value=({0: {"id": "s0", "name": "A"}}, {"A": {"id": "s0"}}),
        ),
        patch("src.ui.prompt_utils.InputUtils.safe_input", return_value="Zed"),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
        caplog.at_level(logging.WARNING),
    ):
        result = PromptUtils.select_site_id_from_csv()
    assert result is None
    assert "Site not found" in caplog.text


# ---------- select_site / select_site_with_logging ----------


def test_select_site_delegates() -> None:
    """``select_site`` forwards to ``select_site_id_from_csv``."""
    with patch.object(PromptUtils, "select_site_id_from_csv", return_value="s0") as delegated:
        assert PromptUtils.select_site() == "s0"
    delegated.assert_called_once_with()


def test_select_site_with_logging_success(caplog: pytest.LogCaptureFixture) -> None:
    """Successful selection logs the site id."""
    caplog.set_level("INFO")
    with patch.object(PromptUtils, "select_site_id_from_csv", return_value="s0"):
        assert PromptUtils.select_site_with_logging() == "s0"
    assert any("Selected site ID" in rec.message for rec in caplog.records)


def test_select_site_with_logging_none(caplog: pytest.LogCaptureFixture) -> None:
    """None return path logs the error message."""
    caplog.set_level("INFO")
    with patch.object(PromptUtils, "select_site_id_from_csv", return_value=None):
        assert PromptUtils.select_site_with_logging() is None
    assert any("No site selected" in rec.message for rec in caplog.records)


# ---------- _determine_search_scope ----------


def test_determine_search_scope_provided_site_short_circuits() -> None:
    """Non-empty ``site_id`` is returned unchanged."""
    assert PromptUtils._determine_search_scope("site-1") == "site-1"


def test_determine_search_scope_site_selected() -> None:
    """``'s'`` scope + successful site pick returns the selected site."""
    with (
        patch("src.ui.prompt_utils.InputUtils.safe_input", return_value="s"),
        patch.object(PromptUtils, "select_site", return_value="site-pick"),
    ):
        assert PromptUtils._determine_search_scope(None) == "site-pick"


def test_determine_search_scope_site_cancelled(caplog: pytest.LogCaptureFixture) -> None:
    """``'s'`` scope with cancelled site pick returns False."""
    with (
        patch("src.ui.prompt_utils.InputUtils.safe_input", return_value="s"),
        patch.object(PromptUtils, "select_site", return_value=None),
        caplog.at_level(logging.WARNING),
    ):
        assert PromptUtils._determine_search_scope(None) is False
    assert "No site selected" in caplog.text


def test_determine_search_scope_org_wide() -> None:
    """Anything other than ``'s'`` returns None (org-wide)."""
    with patch("src.ui.prompt_utils.InputUtils.safe_input", return_value="o"):
        assert PromptUtils._determine_search_scope(None) is None


# ---------- _fetch_site_wireless_clients ----------


def test_fetch_site_wireless_clients_success() -> None:
    """Tags each client with ``client_type`` + ``source_site_id`` on success."""
    fake_mh = _make_mh()
    clients = [{"mac": "11"}, {"mac": "22"}]
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.sites.clients.searchSiteWirelessClients",
            return_value="resp",
        ),
        patch("src.ui.prompt_utils.mistapi.get_all", return_value=clients),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        result = PromptUtils._fetch_site_wireless_clients("site-1")
    assert all(c["client_type"] == "wireless" for c in result)
    assert all(c["source_site_id"] == "site-1" for c in result)


def test_fetch_site_wireless_clients_get_all_none_returns_empty() -> None:
    """``get_all`` returning None is coerced to an empty list."""
    fake_mh = _make_mh()
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.sites.clients.searchSiteWirelessClients",
            return_value="resp",
        ),
        patch("src.ui.prompt_utils.mistapi.get_all", return_value=None),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        assert PromptUtils._fetch_site_wireless_clients("site-1") == []


def test_fetch_site_wireless_clients_exception_returns_empty() -> None:
    """Fetch exceptions are swallowed and yield an empty list."""
    fake_mh = _make_mh()
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.sites.clients.searchSiteWirelessClients",
            side_effect=RuntimeError("boom"),
        ),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        assert PromptUtils._fetch_site_wireless_clients("site-1") == []


# ---------- _fetch_site_wired_clients ----------


def test_fetch_site_wired_clients_success() -> None:
    """Tags each client with ``wired`` type + source site id."""
    fake_mh = _make_mh()
    clients = [{"mac": "aa"}]
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.sites.wired_clients.searchSiteWiredClients",
            return_value="resp",
        ),
        patch("src.ui.prompt_utils.mistapi.get_all", return_value=clients),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        result = PromptUtils._fetch_site_wired_clients("site-1")
    assert result[0]["client_type"] == "wired"
    assert result[0]["source_site_id"] == "site-1"


def test_fetch_site_wired_clients_exception_returns_empty() -> None:
    """Fetch failure yields an empty list."""
    fake_mh = _make_mh()
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.sites.wired_clients.searchSiteWiredClients",
            side_effect=RuntimeError("boom"),
        ),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        assert PromptUtils._fetch_site_wired_clients("site-1") == []


# ---------- _fetch_org_wireless_clients ----------


def test_fetch_org_wireless_clients_success() -> None:
    """Tags org wireless clients with ``client_type`` (no site tag)."""
    fake_mh = _make_mh()
    clients = [{"mac": "bb"}]
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.orgs.clients.searchOrgWirelessClients",
            return_value="resp",
        ),
        patch("src.ui.prompt_utils.mistapi.get_all", return_value=clients),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        result = PromptUtils._fetch_org_wireless_clients("org-1")
    assert result[0]["client_type"] == "wireless"
    assert "source_site_id" not in result[0]


def test_fetch_org_wireless_clients_exception_returns_empty() -> None:
    """Fetch failure yields an empty list."""
    fake_mh = _make_mh()
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.orgs.clients.searchOrgWirelessClients",
            side_effect=RuntimeError("boom"),
        ),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        assert PromptUtils._fetch_org_wireless_clients("org-1") == []


# ---------- _fetch_org_wired_clients ----------


def test_fetch_org_wired_clients_success() -> None:
    """Tags org wired clients with ``client_type`` (no site tag)."""
    fake_mh = _make_mh()
    clients = [{"mac": "cc"}]
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients",
            return_value="resp",
        ),
        patch("src.ui.prompt_utils.mistapi.get_all", return_value=clients),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        result = PromptUtils._fetch_org_wired_clients("org-1")
    assert result[0]["client_type"] == "wired"


def test_fetch_org_wired_clients_exception_returns_empty() -> None:
    """Fetch failure yields an empty list."""
    fake_mh = _make_mh()
    with (
        patch(
            "src.ui.prompt_utils.mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients",
            side_effect=RuntimeError("boom"),
        ),
        patch("src.ui.prompt_utils.importlib.import_module", return_value=fake_mh),
    ):
        assert PromptUtils._fetch_org_wired_clients("org-1") == []


# ---------- _fetch_all_clients ----------


def test_fetch_all_clients_site_branch(caplog: pytest.LogCaptureFixture) -> None:
    """Site branch calls site-scoped fetchers and returns sorted combined list."""
    with (
        patch.object(
            PromptUtils,
            "_fetch_site_wireless_clients",
            return_value=[{"hostname": "b", "mac": "2"}],
        ),
        patch.object(
            PromptUtils,
            "_fetch_site_wired_clients",
            return_value=[{"hostname": "a", "mac": "1"}],
        ),
        caplog.at_level(logging.WARNING),
    ):
        result = PromptUtils._fetch_all_clients("org-1", "site-1")
    assert [c["hostname"] for c in result] == ["a", "b"]
    assert "site" in caplog.text


def test_fetch_all_clients_org_branch(caplog: pytest.LogCaptureFixture) -> None:
    """Org branch calls org-scoped fetchers when ``site_id`` is None."""
    with (
        patch.object(PromptUtils, "_fetch_org_wireless_clients", return_value=[{"hostname": "x"}]),
        patch.object(PromptUtils, "_fetch_org_wired_clients", return_value=[{"hostname": "y"}]),
        caplog.at_level(logging.WARNING),
    ):
        result = PromptUtils._fetch_all_clients("org-1", None)
    assert len(result) == 2
    assert "organization" in caplog.text


# ---------- _load_sites_cache ----------


def test_load_sites_cache_success(caplog: pytest.LogCaptureFixture) -> None:
    """Builds id-to-name mapping from ``all_sites_with_limit`` result."""
    # WHY (#886 Phase 2): PromptUtils now emits via logging.warning instead of print, so tests capture via caplog.
    with (
        patch(
            "src.ui.prompt_utils.APICoreFetchUtils.all_sites_with_limit",
            return_value=[{"id": "a", "name": "Alpha"}, {"id": "b", "name": "Beta"}],
        ),
        caplog.at_level(logging.WARNING),
    ):
        cache = PromptUtils._load_sites_cache("org-1")
    assert cache == {"a": "Alpha", "b": "Beta"}
    assert "Loading site information" in caplog.text


def test_load_sites_cache_exception_returns_empty() -> None:
    """Fetch failure yields an empty cache."""
    with patch(
        "src.ui.prompt_utils.APICoreFetchUtils.all_sites_with_limit",
        side_effect=RuntimeError("boom"),
    ):
        assert PromptUtils._load_sites_cache("org-1") == {}


# ---------- _print_client_type_summary ----------


def test_print_client_type_summary(caplog: pytest.LogCaptureFixture) -> None:
    """Prints wireless/wired counts and legend."""
    # WHY (#886 Phase 2): PromptUtils now emits via logging.warning instead of print, so tests capture via caplog.
    with caplog.at_level(logging.WARNING):
        PromptUtils._print_client_type_summary(
            [{"client_type": "wireless"}, {"client_type": "wired"}, {"client_type": "wired"}]
        )
    out = caplog.text
    assert "1 wireless" in out
    assert "2 wired" in out
    assert "[+]" in out and "[~]" in out and "[-]" in out


# ---------- _build_client_table_skeleton ----------


def test_build_client_table_skeleton_columns_and_widths() -> None:
    """Skeleton has canonical column list and configured max widths."""
    table = PromptUtils._build_client_table_skeleton()
    assert table.field_names == [
        "#",
        "Hostname",
        "MAC Address",
        "Type",
        "IP Address",
        "SSID/VLAN",
        "Site",
        "Status",
    ]
    assert table.max_width["Hostname"] == 20
    assert table.max_width["IP Address"] == 16
    assert table.max_width["SSID/VLAN"] == 15
    assert table.max_width["Site"] == 15


# ---------- _format_client_row ----------


def test_format_client_row_composes_all_cells() -> None:
    """Row contains the expected cells with truncation applied."""
    client = {
        "hostname": "x" * 30,
        "mac": "aa:bb",
        "client_type": "wirelesswireless",
        "ip": "10.0.0.1",
        "ssid": "wifi",
        "site_id": "s-1",
        "connected": True,
    }
    row = PromptUtils._format_client_row(3, client, {"s-1": "Alpha"})
    assert row[0] == 3
    assert row[1].endswith("...")  # truncated hostname
    assert row[2] == "aa:bb"
    assert row[3] == "wireless"  # 8-char cap
    assert row[4] == "10.0.0.1"
    assert row[5] == "wifi"
    assert row[6] == "Alpha"
    assert row[7] == "[+]"


# ---------- _display_client_table ----------


def test_display_client_table_returns_index_map(caplog: pytest.LogCaptureFixture) -> None:
    """Returns a 0-based ``dict`` mapping index to client."""
    # WHY (#886 Phase 2): PromptUtils now emits via logging.warning instead of print, so tests capture via caplog.
    clients = [
        {"client_type": "wireless", "hostname": "a", "mac": "1", "connected": True},
        {"client_type": "wired", "hostname": "b", "mac": "2", "connected": True},
    ]
    with caplog.at_level(logging.WARNING):
        result = PromptUtils._display_client_table(clients, {})
    assert result == {0: clients[0], 1: clients[1]}
    assert "Found 2 clients" in caplog.text


# ---------- _get_client_site_name ----------


def test_get_client_site_name_cache_hit() -> None:
    """Returns cached name for a known site id."""
    assert PromptUtils._get_client_site_name({"site_id": "s"}, {"s": "Alpha"}) == "Alpha"


def test_get_client_site_name_fallback_to_raw_id() -> None:
    """Unknown site id falls back to the raw id."""
    assert PromptUtils._get_client_site_name({"site_id": "unknown"}, {}) == "unknown"


def test_get_client_site_name_empty_when_missing() -> None:
    """Missing site id returns empty string."""
    assert PromptUtils._get_client_site_name({}, {}) == ""


# ---------- _get_client_status ----------


def test_get_client_status_online_default_true() -> None:
    """No ``connected`` field defaults to online ``[+]``."""
    assert PromptUtils._get_client_status({}) == "[+]"


def test_get_client_status_offline() -> None:
    """``connected=False`` yields offline ``[-]``."""
    assert PromptUtils._get_client_status({"connected": False}) == "[-]"


def test_get_client_status_recently_seen_overrides() -> None:
    """``last_seen`` older than 300s overrides to ``[~]``."""
    with patch("src.ui.prompt_utils.time.time", return_value=1000):
        assert PromptUtils._get_client_status({"connected": True, "last_seen": 500}) == "[~]"


def test_get_client_status_recent_last_seen_keeps_online() -> None:
    """Fresh ``last_seen`` (<=300s) leaves status untouched."""
    with patch("src.ui.prompt_utils.time.time", return_value=1000):
        assert PromptUtils._get_client_status({"connected": True, "last_seen": 900}) == "[+]"


# ---------- _format_client_ip ----------


def test_format_client_ip_list_nonempty() -> None:
    """List IPs return the first entry."""
    assert PromptUtils._format_client_ip({"ip": ["10.0.0.1", "10.0.0.2"]}) == "10.0.0.1"


def test_format_client_ip_list_empty() -> None:
    """Empty list yields ``N/A``."""
    assert PromptUtils._format_client_ip({"ip": []}) == "N/A"


def test_format_client_ip_string_present() -> None:
    """Non-empty string returns as-is."""
    assert PromptUtils._format_client_ip({"ip": "10.0.0.5"}) == "10.0.0.5"


def test_format_client_ip_bracket_literal_treated_as_na() -> None:
    """Literal ``'[]'`` string collapses to ``N/A``."""
    assert PromptUtils._format_client_ip({"ip": "[]"}) == "N/A"


def test_format_client_ip_empty_string() -> None:
    """Empty string yields ``N/A``."""
    assert PromptUtils._format_client_ip({"ip": ""}) == "N/A"


# ---------- _format_client_ssid_vlan ----------


def test_format_client_ssid_vlan_list_nonempty() -> None:
    """List values return the first element (stringified + truncated)."""
    assert PromptUtils._format_client_ssid_vlan({"ssid": ["wifi"]}) == "wifi"


def test_format_client_ssid_vlan_list_empty() -> None:
    """Empty list yields ``N/A``."""
    assert PromptUtils._format_client_ssid_vlan({"ssid": []}) == "N/A"


def test_format_client_ssid_vlan_bracket_literal() -> None:
    """String literal ``'[]'`` collapses to ``N/A``."""
    assert PromptUtils._format_client_ssid_vlan({"ssid": "[]"}) == "N/A"


def test_format_client_ssid_vlan_string_truncates() -> None:
    """String longer than 15 chars is truncated with ellipsis."""
    result = PromptUtils._format_client_ssid_vlan({"ssid": "x" * 30})
    assert result.endswith("...")
    assert len(result) == 15


def test_format_client_ssid_vlan_missing_field() -> None:
    """Missing SSID/VLAN keys collapse to ``N/A``."""
    assert PromptUtils._format_client_ssid_vlan({}) == "N/A"


# ---------- _truncate_string ----------


def test_truncate_string_over_max() -> None:
    """Strings over max_length are truncated with an ellipsis."""
    assert PromptUtils._truncate_string("abcdefghij", 6) == "abc..."


def test_truncate_string_under_max() -> None:
    """Strings within max_length are returned unchanged."""
    assert PromptUtils._truncate_string("abc", 10) == "abc"


# ---------- _handle_client_selection ----------


def test_handle_client_selection_quit_returns_triple_none() -> None:
    """``PromptClientUtils._parse_client_choice`` returning None aborts."""
    with (
        patch("src.ui.prompt_utils.InputUtils.safe_input", return_value="q"),
        patch(
            "src.ui.prompt_utils.PromptClientUtils._parse_client_choice",
            return_value=None,
        ),
    ):
        assert PromptUtils._handle_client_selection([{}], {}, None) == (
            None,
            None,
            None,
        )


def test_handle_client_selection_valid_index() -> None:
    """Valid parsed index delegates to ``_extract_selected_client``."""
    clients = [{"mac": "aa", "client_type": "wireless", "site_id": "s-1"}]
    with (
        patch("src.ui.prompt_utils.InputUtils.safe_input", return_value="0"),
        patch("src.ui.prompt_utils.PromptClientUtils._parse_client_choice", return_value=0),
        patch.object(
            PromptUtils,
            "_extract_selected_client",
            return_value=("aa", "wireless", "s-1"),
        ) as extract,
    ):
        result = PromptUtils._handle_client_selection(clients, {"s-1": "Alpha"}, None)
    assert result == ("aa", "wireless", "s-1")
    extract.assert_called_once_with(clients[0], {"s-1": "Alpha"}, None)


# ---------- _extract_selected_client ----------


def test_extract_selected_client_site_in_cache_prints_site(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Known site prints resolved site name."""
    # WHY (#886 Phase 2): PromptUtils now emits via logging.warning instead of print, so tests capture via caplog.
    client = {"mac": "aa", "client_type": "wireless", "site_id": "s-1", "hostname": "h"}
    with caplog.at_level(logging.WARNING):
        result = PromptUtils._extract_selected_client(client, {"s-1": "Alpha"}, None)
    assert result == ("aa", "wireless", "s-1")
    assert "Site: Alpha" in caplog.text


def test_extract_selected_client_site_not_in_cache_skips_site_line(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unknown site skips the ``Site:`` line but still returns the id."""
    # WHY (#886 Phase 2): PromptUtils now emits via logging.warning instead of print, so tests capture via caplog.
    client = {"mac": "bb", "client_type": "wired", "site_id": "unknown", "name": "n"}
    with caplog.at_level(logging.WARNING):
        result = PromptUtils._extract_selected_client(client, {}, None)
    assert result == ("bb", "wired", "unknown")
    assert "Site:" not in caplog.text


def test_extract_selected_client_defaults_to_default_site_id() -> None:
    """Missing site_id falls back to ``default_site_id``."""
    client = {"mac": "cc", "client_type": "wired"}
    result = PromptUtils._extract_selected_client(client, {}, "site-default")
    assert result == ("cc", "wired", "site-default")


def test_extract_selected_client_empty_site_becomes_empty_string() -> None:
    """None ``default_site_id`` with no client site yields empty string."""
    client = {"mac": "dd", "client_type": "wired"}
    result = PromptUtils._extract_selected_client(client, {}, None)
    assert result == ("dd", "wired", "")
