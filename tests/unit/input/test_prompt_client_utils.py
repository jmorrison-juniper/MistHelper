"""Unit tests for PromptClientUtils (initiative #878 / #1017 PR-1)."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.input import prompt_client_utils as mod
from src.input.prompt_client_utils import PromptClientUtils


@pytest.fixture
def mh_mocks(monkeypatch):
    """Patch every MistHelper attribute referenced by PromptClientUtils lazy imports."""
    mocks = {
        "InputUtils": MagicMock(name="InputUtils"),
        "PromptUtils": MagicMock(name="PromptUtils"),
        "ConfigUtils": MagicMock(name="ConfigUtils"),
        "apisession": MagicMock(name="apisession"),
    }
    for attr, value in mocks.items():
        monkeypatch.setattr(f"MistHelper.{attr}", value, raising=False)
    mocks["ConfigUtils"].get_cached_or_prompted_org_id.return_value = "org-1"
    return mocks


class TestNormalizeClientsResponse:
    def test_dict_with_results(self):
        resp = SimpleNamespace(data={"results": [{"mac": "abc"}]})
        assert PromptClientUtils._normalize_clients_response(resp) == [{"mac": "abc"}]

    def test_dict_missing_results_returns_empty(self):
        resp = SimpleNamespace(data={})
        assert PromptClientUtils._normalize_clients_response(resp) == []

    def test_list_data_returned_as_is(self):
        resp = SimpleNamespace(data=[{"mac": "abc"}])
        assert PromptClientUtils._normalize_clients_response(resp) == [{"mac": "abc"}]


class TestTagConnectionType:
    def test_tags_in_place(self):
        clients = [{"mac": "a"}, {"mac": "b"}]
        PromptClientUtils._tag_connection_type(clients, "Wireless")
        assert all(c["connection_type"] == "Wireless" for c in clients)

    def test_empty_list_noop(self):
        clients: list = []
        PromptClientUtils._tag_connection_type(clients, "Wireless")
        assert clients == []

    def test_none_noop(self):
        PromptClientUtils._tag_connection_type(None, "Wireless")


class TestLogCombinedClientCounts:
    def test_silent_when_both_empty(self, caplog):
        caplog.set_level(logging.INFO)
        PromptClientUtils._log_combined_client_counts([], [])
        assert "Found" not in caplog.text

    def test_logs_when_wireless_only(self, caplog):
        caplog.set_level(logging.INFO)
        PromptClientUtils._log_combined_client_counts([{"a": 1}], [])
        assert "Found 1 connected clients" in caplog.text

    def test_logs_when_none_and_list(self, caplog):
        caplog.set_level(logging.INFO)
        PromptClientUtils._log_combined_client_counts(None, [{"a": 1}])
        assert "1 wired" in caplog.text


class TestFetchAllClientsForSite:
    def test_combines_wireless_and_wired_with_tags(self, mh_mocks, monkeypatch):
        wireless_resp = SimpleNamespace(data={"results": [{"mac": "w1"}]})
        wired_resp = SimpleNamespace(data={"results": [{"mac": "d1"}]})
        fake_mistapi = SimpleNamespace(
            api=SimpleNamespace(
                v1=SimpleNamespace(
                    sites=SimpleNamespace(
                        clients=SimpleNamespace(searchSiteWirelessClients=MagicMock(return_value=wireless_resp)),
                        wired_clients=SimpleNamespace(searchSiteWiredClients=MagicMock(return_value=wired_resp)),
                    )
                )
            )
        )
        monkeypatch.setattr(mod, "mistapi", fake_mistapi)
        result = PromptClientUtils._fetch_all_clients_for_site("site-1")
        assert result == [
            {"mac": "w1", "connection_type": "Wireless"},
            {"mac": "d1", "connection_type": "Wired"},
        ]


class TestBuildClientSelectionTable:
    def test_wireless_uses_ssid(self):
        clients = [
            {"hostname": "hostA", "mac": "aa", "ip": "1.1.1.1", "connection_type": "Wireless", "ssid": "guest"},
        ]
        table, idx_map = PromptClientUtils._build_client_selection_table(clients)
        rendered = str(table)
        assert "hostA" in rendered
        assert "guest" in rendered
        assert idx_map[0] is clients[0]

    def test_wired_uses_vlan(self):
        clients = [
            {"username": "userB", "mac": "bb", "ip": "2.2.2.2", "connection_type": "Wired", "vlan_id": 42},
        ]
        table, _ = PromptClientUtils._build_client_selection_table(clients)
        rendered = str(table)
        assert "userB" in rendered
        assert "VLAN 42" in rendered

    def test_unknown_fallbacks(self):
        clients = [{"connection_type": "Wireless"}]
        table, idx_map = PromptClientUtils._build_client_selection_table(clients)
        rendered = str(table)
        assert "Unknown" in rendered
        assert idx_map[0] is clients[0]


class TestRenderClientSelectionPrompt:
    def test_prints_header_and_options(self, caplog: pytest.LogCaptureFixture) -> None:
        """Header, count, and options must be emitted through logging.warning.

        Why:
            Per #886 Phase 2 the render UI moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        clients = [{"connection_type": "Wireless", "hostname": "h", "mac": "m", "ip": "i"}]
        table, _ = PromptClientUtils._build_client_selection_table(clients)
        with caplog.at_level(logging.WARNING):
            PromptClientUtils._render_client_selection_prompt(table, 1)
        out = caplog.text
        assert "SELECT CONNECTED CLIENT" in out
        assert "Found 1 connected clients" in out
        assert "'m'" in out
        assert "'c'" in out


class TestHandleClientSelectionInput:
    def test_manual_returns_typed_mac(self, mh_mocks):
        mh_mocks["InputUtils"].safe_input.return_value = "aa:bb:cc:dd:ee:ff"
        result = PromptClientUtils._handle_client_selection_input("m", {})
        assert result == "aa:bb:cc:dd:ee:ff"

    def test_cancel_returns_none(self, mh_mocks):
        assert PromptClientUtils._handle_client_selection_input("c", {}) is None

    def test_non_digit_returns_none(self, mh_mocks, caplog: pytest.LogCaptureFixture) -> None:
        """Non-digit input logs the validation hint via WARNING.

        Why:
            Per #886 Phase 2 the operator hint moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        with caplog.at_level(logging.WARNING):
            assert PromptClientUtils._handle_client_selection_input("xyz", {}) is None
        assert "valid index" in caplog.text

    def test_out_of_range_returns_none(self, mh_mocks, caplog: pytest.LogCaptureFixture) -> None:
        """Out-of-range index logs the "Invalid index" WARNING.

        Why:
            Per #886 Phase 2 the operator hint moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        with caplog.at_level(logging.WARNING):
            assert PromptClientUtils._handle_client_selection_input("99", {0: {"mac": "a"}}) is None
        assert "Invalid index" in caplog.text

    def test_valid_index_returns_mac(self, mh_mocks):
        idx_map = {0: {"mac": "aa:bb", "hostname": "h", "connection_type": "Wireless"}}
        assert PromptClientUtils._handle_client_selection_input("0", idx_map) == "aa:bb"


class TestFinalizeClientChoice:
    def test_prints_and_returns_mac(self, caplog: pytest.LogCaptureFixture) -> None:
        """Selection confirmation is emitted via logging.warning.

        Why:
            Per #886 Phase 2 the "Selected: ..." confirmation moved from
            ``print()`` to ``logging.warning`` so the assertion reads
            ``caplog.text``.
        """
        client = {"mac": "AA", "hostname": "host", "connection_type": "Wireless"}
        with caplog.at_level(logging.WARNING):
            assert PromptClientUtils._finalize_client_choice(0, client) == "AA"
        assert "Selected: host" in caplog.text

    def test_uses_username_fallback(self, caplog: pytest.LogCaptureFixture) -> None:
        """Username fallback still surfaces in the WARNING record.

        Why:
            Per #886 Phase 2 the confirmation moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        client = {"mac": "AA", "username": "userX", "connection_type": "Wired"}
        with caplog.at_level(logging.WARNING):
            PromptClientUtils._finalize_client_choice(1, client)
        assert "userX" in caplog.text


class TestParseClientChoice:
    @pytest.mark.parametrize("quit_word", ["q", "quit", "exit", "QUIT"])
    def test_quit_returns_none(self, quit_word, caplog: pytest.LogCaptureFixture) -> None:
        """Quit keywords emit "Exiting client selection..." via WARNING.

        Why:
            Per #886 Phase 2 the quit notice moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        with caplog.at_level(logging.WARNING):
            assert PromptClientUtils._parse_client_choice(quit_word, 5) is None
        assert "Exiting client selection" in caplog.text

    def test_non_numeric_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """Non-numeric input emits the WARNING hint.

        Why:
            Per #886 Phase 2 the validation hint moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        with caplog.at_level(logging.WARNING):
            assert PromptClientUtils._parse_client_choice("abc", 5) is None
        assert "valid number" in caplog.text

    def test_out_of_range_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        """Out-of-range numeric input emits the WARNING hint.

        Why:
            Per #886 Phase 2 the validation hint moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        with caplog.at_level(logging.WARNING):
            assert PromptClientUtils._parse_client_choice("10", 5) is None
        assert "Invalid index" in caplog.text

    def test_valid_index(self):
        assert PromptClientUtils._parse_client_choice("3", 5) == 3

    def test_zero_valid(self):
        assert PromptClientUtils._parse_client_choice("0", 5) == 0


class TestSelectClientMac:
    def test_no_clients_returns_none(self, mh_mocks, monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
        """Empty client list surfaces "No connected clients found" via WARNING.

        Why:
            Per #886 Phase 2 the empty-state notice moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        monkeypatch.setattr(PromptClientUtils, "_fetch_all_clients_for_site", staticmethod(lambda _s: []))
        with caplog.at_level(logging.WARNING):
            assert PromptClientUtils.select_client_mac("site-1") is None
        assert "No connected clients found" in caplog.text

    def test_happy_path_returns_selected_mac(self, mh_mocks, monkeypatch):
        clients = [{"mac": "aa", "hostname": "h", "connection_type": "Wireless"}]
        monkeypatch.setattr(PromptClientUtils, "_fetch_all_clients_for_site", staticmethod(lambda _s: list(clients)))
        mh_mocks["InputUtils"].safe_input.return_value = "0"
        assert PromptClientUtils.select_client_mac("site-1") == "aa"

    def test_exception_returns_none(self, mh_mocks, monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
        """Fetch exceptions surface via logging.exception (ERROR-level).

        Why:
            Per #886 Phase 2 the fetch-failure message moved from ``print()``
            to ``logging.exception`` so the assertion reads ``caplog.text``.
        """

        def raise_err(_s):
            raise RuntimeError("boom")

        monkeypatch.setattr(PromptClientUtils, "_fetch_all_clients_for_site", staticmethod(raise_err))
        with caplog.at_level(logging.ERROR):
            assert PromptClientUtils.select_client_mac("site-1") is None
        assert "Error fetching clients" in caplog.text


class TestSelectClient:
    def test_cancelled_scope_returns_none_tuple(self, mh_mocks):
        mh_mocks["PromptUtils"]._determine_search_scope.return_value = False
        assert PromptClientUtils.select_client() == (None, None, None)

    def test_success_returns_flow_result(self, mh_mocks, monkeypatch):
        mh_mocks["PromptUtils"]._determine_search_scope.return_value = "site-1"
        monkeypatch.setattr(
            PromptClientUtils,
            "_run_client_selection_flow",
            staticmethod(lambda _o, _s: ("mac", "type", "site")),
        )
        assert PromptClientUtils.select_client("site-1") == ("mac", "type", "site")

    def test_exception_returns_none_tuple(self, mh_mocks, monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
        """Selection-flow exceptions surface via logging.error.

        Why:
            Per #886 Phase 2 the operator-visible error moved from ``print()``
            to ``logging.error`` so the assertion reads ``caplog.text``.
        """
        mh_mocks["PromptUtils"]._determine_search_scope.return_value = "site-1"

        def raise_err(_o, _s):
            raise RuntimeError("boom")

        monkeypatch.setattr(PromptClientUtils, "_run_client_selection_flow", staticmethod(raise_err))
        with caplog.at_level(logging.ERROR):
            assert PromptClientUtils.select_client("site-1") == (None, None, None)
        assert "Error searching for clients" in caplog.text


class TestRunClientSelectionFlow:
    def test_empty_clients_returns_none_tuple(self, mh_mocks, caplog: pytest.LogCaptureFixture) -> None:
        """Empty-client-set surfaces "No clients found." via WARNING.

        Why:
            Per #886 Phase 2 the empty-state notice moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        mh_mocks["PromptUtils"]._fetch_all_clients.return_value = []
        with caplog.at_level(logging.WARNING):
            assert PromptClientUtils._run_client_selection_flow("org-1", "site-1") == (None, None, None)
        assert "No clients found" in caplog.text

    def test_populated_flow_delegates_to_prompt_utils(self, mh_mocks):
        mh_mocks["PromptUtils"]._fetch_all_clients.return_value = [{"mac": "aa"}]
        mh_mocks["PromptUtils"]._load_sites_cache.return_value = {"site-1": "Site"}
        mh_mocks["PromptUtils"]._handle_client_selection.return_value = ("aa", "wired", "site-1")
        assert PromptClientUtils._run_client_selection_flow("org-1", "site-1") == ("aa", "wired", "site-1")
        mh_mocks["PromptUtils"]._display_client_table.assert_called_once()


class TestSelectSiteAndDeviceIds:
    def test_returns_supplied_ids_untouched(self, mh_mocks):
        assert PromptClientUtils.select_site_and_device_ids("s", "d") == ("s", "d")
        mh_mocks["PromptUtils"].select_site_id_from_csv.assert_not_called()

    def test_prompts_for_site_when_missing(self, mh_mocks):
        mh_mocks["PromptUtils"].select_site_id_from_csv.return_value = "s2"
        mh_mocks["PromptUtils"].select_device_id_from_inventory.return_value = "d2"
        assert PromptClientUtils.select_site_and_device_ids(None, None) == ("s2", "d2")

    def test_no_site_returns_none_pair(self, mh_mocks, caplog: pytest.LogCaptureFixture) -> None:
        """Missing-site path emits "No site selected." via WARNING.

        Why:
            Per #886 Phase 2 the notice moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        mh_mocks["PromptUtils"].select_site_id_from_csv.return_value = None
        with caplog.at_level(logging.WARNING):
            assert PromptClientUtils.select_site_and_device_ids(None, None) == (None, None)
        assert "No site selected" in caplog.text

    def test_no_device_returns_none_pair(self, mh_mocks, caplog: pytest.LogCaptureFixture) -> None:
        """Missing-device path emits "No device selected." via WARNING.

        Why:
            Per #886 Phase 2 the notice moved from ``print()`` to
            ``logging.warning`` so the assertion reads ``caplog.text``.
        """
        mh_mocks["PromptUtils"].select_device_id_from_inventory.return_value = None
        with caplog.at_level(logging.WARNING):
            assert PromptClientUtils.select_site_and_device_ids("s", None) == (None, None)
        assert "No device selected" in caplog.text
