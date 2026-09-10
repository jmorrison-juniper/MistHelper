"""Unit tests for the organization-scoped search exporter.

Covers specs 863, 869, 870, 872, and 873 to 879 (issues #1371, #1377, #1378,
#1379, #1380, #1381, #1382, #1383, #1385, and #1386), which are menus 230 to
234, 248 to 253, and 255.

The registered operations share one helper, so the shared behavior is tested
once and each menu entry is checked for the binding that makes it distinct.
The two filtered searches also get direct coverage of every optional filter.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of the error-path logging.
from typing import Any  # WHY: the monkeypatched fakes carry loose typing.
from unittest.mock import MagicMock  # WHY: collaborator doubles and call assertions.

import pytest  # WHY: monkeypatch and caplog fixtures.

from src.export.org_search_exporter import OrgSearchExporter
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES

# Each row maps a menu entry to the operationId, the filename prefix, and the
# SDK attribute chain that the entry must call.
MENU_BINDINGS = [
    ("devices", "searchOrgDevices", "OrgDevices", ("devices", "searchOrgDevices")),
    (
        "wireless_client_sessions",
        "searchOrgWirelessClientSessions",
        "OrgWirelessClientSessions",
        ("clients", "searchOrgWirelessClientSessions"),
    ),
    (
        "wireless_client_events",
        "searchOrgWirelessClientEvents",
        "OrgWirelessClientEvents",
        ("clients", "searchOrgWirelessClientEvents"),
    ),
    ("wan_clients", "searchOrgWanClients", "OrgWanClients", ("wan_clients", "searchOrgWanClients")),
    (
        "wan_client_events",
        "searchOrgWanClientEvents",
        "OrgWanClientEvents",
        ("wan_clients", "searchOrgWanClientEvents"),
    ),
    ("system_events", "searchOrgSystemEvents", "OrgSystemEvents", ("events", "searchOrgSystemEvents")),
    ("sites", "searchOrgSites", "OrgSitesSearch", ("sites", "searchOrgSites")),
    ("org_vars", "searchOrgVars", "OrgVars", ("vars", "searchOrgVars")),
    ("user_macs", "searchOrgUserMacs", "OrgUserMacs", ("usermacs", "searchOrgUserMacs")),
    ("mx_edges", "searchOrgMxEdges", "OrgMxEdges", ("mxedges", "searchOrgMxEdges")),
    ("psk_portal_logs", "searchOrgPskPortalLogs", "OrgPskPortalLogs", ("pskportals", "searchOrgPskPortalLogs")),
]


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire every collaborator the exporter reaches through.

    Returns a dict of mocks so each test can assert argument bindings and call
    counts. No network call and no real session is needed.
    """
    data_processing = MagicMock(name="DataProcessingUtils")  # Flatten and escape collaborator.
    data_processing.flatten_nested_fields.side_effect = lambda rows: rows  # Identity keeps the payload checkable.
    data_processing.escape_multiline.side_effect = lambda rows: rows  # Identity keeps the payload checkable.
    monkeypatch.setattr("src.export.org_search_exporter.DataProcessingUtils", data_processing, raising=True)

    mistapi_mod = MagicMock(name="mistapi")  # SDK double for every endpoint call.
    mistapi_mod.get_all.side_effect = lambda response, mist_session: response  # Pass the fake rows straight back.
    monkeypatch.setattr("src.export.org_search_exporter.mistapi", mistapi_mod, raising=True)

    data_exporter = MagicMock(name="DataExporter")  # write_with_format_selection is observed.
    apisession = MagicMock(name="apisession")  # Forwarded into every SDK call.
    config_utils = MagicMock(name="ConfigUtils")  # Supplies get_cached_or_prompted_org_id.
    config_utils.get_cached_or_prompted_org_id.return_value = "org-1"  # Default happy path.
    input_utils = MagicMock(name="InputUtils")  # Supplies the EOF-safe optional filter prompts.
    input_utils.safe_input.return_value = ""  # A blank answer keeps every optional filter unset.

    monkeypatch.setattr("MistHelper.DataExporter", data_exporter, raising=False)
    monkeypatch.setattr("MistHelper.apisession", apisession, raising=False)
    monkeypatch.setattr("MistHelper.ConfigUtils", config_utils, raising=False)
    monkeypatch.setattr("MistHelper.InputUtils", input_utils, raising=False)
    monkeypatch.setattr("MistHelper.IS_TEST_MODE", False, raising=False)  # Exercise the interactive branch.

    return {
        "DataProcessingUtils": data_processing,
        "mistapi": mistapi_mod,
        "DataExporter": data_exporter,
        "apisession": apisession,
        "ConfigUtils": config_utils,
        "InputUtils": input_utils,
    }


def _sdk_target(mistapi_mod: MagicMock, chain: tuple[str, ...]) -> MagicMock:
    """Return the SDK callable double that a menu entry is expected to call."""
    target: Any = mistapi_mod.api.v1.orgs  # Start at the organization API namespace.
    for attribute in chain:  # Walk the SDK module path for the selected endpoint.
        target = getattr(target, attribute)  # Resolve one SDK namespace or function.
    return target  # Return the function double for the test assertion.


class TestMenuBindings:
    """Each menu entry must reach its own SDK function and write its own file."""

    @pytest.mark.parametrize(("method", "operation", "prefix", "chain"), MENU_BINDINGS)
    def test_entry_calls_its_endpoint_and_persists(
        self, wired: dict[str, Any], method: str, operation: str, prefix: str, chain: tuple[str, ...]
    ) -> None:
        """The entry must call its endpoint once and write with its own operationId."""
        target = _sdk_target(wired["mistapi"], chain)
        target.return_value = [{"id": "row-1"}]

        getattr(OrgSearchExporter, method)()

        target.assert_called_once_with(wired["apisession"], "org-1")
        wired["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"id": "row-1"}],
            f"{prefix}.csv",
            api_function_name=operation,
        )

    @pytest.mark.parametrize(("method", "operation", "prefix", "chain"), MENU_BINDINGS)
    def test_entry_aborts_when_org_is_unresolved(
        self, wired: dict[str, Any], method: str, operation: str, prefix: str, chain: tuple[str, ...]
    ) -> None:
        """An unresolved organization must stop before any API call."""
        wired["ConfigUtils"].get_cached_or_prompted_org_id.return_value = None

        getattr(OrgSearchExporter, method)()

        _sdk_target(wired["mistapi"], chain).assert_not_called()
        wired["DataExporter"].write_with_format_selection.assert_not_called()


class TestSharedBehavior:
    """Cover the branches of the shared helper once."""

    def test_empty_result_writes_nothing(self, wired: dict[str, Any]) -> None:
        """An empty search must report the fact and skip the export."""
        wired["mistapi"].api.v1.orgs.events.searchOrgSystemEvents.return_value = []

        OrgSearchExporter.system_events()

        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_api_error_is_logged_and_does_not_raise(
        self, wired: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """An SDK failure must surface in the log rather than crash the menu."""
        wired["mistapi"].api.v1.orgs.events.searchOrgSystemEvents.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.ERROR):
            OrgSearchExporter.system_events()

        assert "Error fetching system event for org" in caplog.text
        wired["DataExporter"].write_with_format_selection.assert_not_called()

    def test_rows_are_flattened_and_escaped_before_the_write(self, wired: dict[str, Any]) -> None:
        """The persist step must run both CSV-safety helpers on the payload."""
        rows = [{"id": "row-1", "nested": {"a": 1}}]
        wired["mistapi"].api.v1.orgs.events.searchOrgSystemEvents.return_value = rows

        OrgSearchExporter.system_events()

        wired["DataProcessingUtils"].flatten_nested_fields.assert_called_once_with(rows)
        wired["DataProcessingUtils"].escape_multiline.assert_called_once_with(rows)

    def test_pagination_helper_receives_the_response(self, wired: dict[str, Any]) -> None:
        """Every search must page through get_all rather than read one page."""
        wired["mistapi"].api.v1.orgs.events.searchOrgSystemEvents.return_value = [{"id": "row-1"}]

        OrgSearchExporter.system_events()

        wired["mistapi"].get_all.assert_called_once_with(response=[{"id": "row-1"}], mist_session=wired["apisession"])

    def test_org_vars_strategy_uses_response_fields(self) -> None:
        """The variable strategy must use fields returned by the endpoint."""
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["searchOrgVars"]  # Read the centralized database strategy.
        assert strategy["type"] == "composite_pk"  # Require an upsert key for repeated variable exports.
        assert strategy["primary_key"] == ["site_id", "var", "src"]  # Match the documented response fields.

    def test_org_vars_menu_is_registered_as_safe(self) -> None:
        """Menu 250 must route to organization variable export as a safe operation."""
        import MistHelper  # Import the runtime menu registry under test.
        from src.utils.operation_registry import OperationRegistry  # Read the safety classification.

        action, description = MistHelper.menu_actions["250"]  # Read the menu dispatch tuple.
        assert action is OrgSearchExporter.org_vars  # Require the new menu to call the exporter.
        assert "searchOrgVars" in description  # Expose the operation identifier to operators.
        assert OperationRegistry.get("250")["category"] == "safe"  # Keep the read-only operation automated.

    def test_device_search_has_a_composite_primary_key(self) -> None:
        """Device search rows must use the existing id and MAC key pair."""
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["searchOrgDevices"]  # Read the catalog entry used by persistence.

        assert strategy["type"] == "composite_pk"  # Require update-safe device search storage.
        assert strategy["primary_key"] == ["id", "mac"]  # Require stable uniqueness for repeated exports.

    def test_user_macs_menu_is_registered_as_safe(self) -> None:
        """Menu 251 must route to the user MAC export as a safe operation."""
        import MistHelper  # Import the runtime menu registry under test.
        from src.utils.operation_registry import OperationRegistry  # Read the safety classification.

        action, description = MistHelper.menu_actions["251"]  # Read the menu dispatch tuple for issue #1380.
        assert action is OrgSearchExporter.user_macs  # Require the new menu to call the exporter.
        assert "searchOrgUserMacs" in description  # Expose the operation identifier to operators.
        assert OperationRegistry.get("251")["category"] == "safe"  # Keep the read-only operation automated.


class TestMxEdgeSearch:
    """Cover the organization MxEdge search filters and export binding."""

    def test_mx_edges_forwards_optional_filters(self, wired: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
        """The menu entry must convert and forward every entered filter to the SDK."""
        target = wired["mistapi"].api.v1.orgs.mxedges.searchOrgMxEdges
        target.return_value = [{"id": "edge-1"}]
        answers = iter(  # One answer per prompt, in the order of the installed SDK signature.
            [
                "edge-host",  # hostname, which the staged branch did not ask for.
                "edge-1",  # mxedge_id
                "",  # mxcluster_id, left blank on purpose.
                "SSR",  # model
                "",  # distro, left blank on purpose.
                "1.2.3",  # tunterm_version
                "site-1",  # site_id
                "true",  # stats, which must reach the SDK as a boolean.
                "25",  # limit, which must reach the SDK as an integer.
                "-1d",  # start
                "",  # end, left blank on purpose.
                "7d",  # duration
                "-last_seen",  # sort
                "",  # search_after, left blank on purpose.
            ]
        )
        wired["InputUtils"].safe_input.side_effect = lambda *args, **kwargs: next(answers)

        OrgSearchExporter.mx_edges()

        target.assert_called_once_with(
            wired["apisession"],
            "org-1",
            hostname="edge-host",
            mxedge_id="edge-1",
            model="SSR",
            tunterm_version="1.2.3",
            site_id="site-1",
            stats=True,
            limit=25,
            start="-1d",
            duration="7d",
            sort="-last_seen",
        )
        wired["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"id": "edge-1"}],
            "OrgMxEdges.csv",
            api_function_name="searchOrgMxEdges",
        )

    def test_mx_edges_asks_for_the_hostname_filter(self, wired: dict[str, Any]) -> None:
        """The SDK accepts a hostname, so the operator must be able to supply one."""
        wired["mistapi"].api.v1.orgs.mxedges.searchOrgMxEdges.return_value = [{"id": "edge-1"}]

        OrgSearchExporter.mx_edges()

        contexts = [call.kwargs["context"] for call in wired["InputUtils"].safe_input.call_args_list]
        assert "org_search_exporter.searchOrgMxEdges.hostname" in contexts  # Require the missing prompt.

    def test_mx_edges_with_empty_filters_uses_sdk_defaults(
        self, wired: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """EOF-safe empty answers must still run one unfiltered organization search."""
        target = wired["mistapi"].api.v1.orgs.mxedges.searchOrgMxEdges
        target.return_value = [{"id": "edge-1"}]
        monkeypatch.setattr(
            "MistHelper.InputUtils",
            MagicMock(safe_input=MagicMock(return_value="")),
            raising=False,
        )

        OrgSearchExporter.mx_edges()

        target.assert_called_once_with(wired["apisession"], "org-1")

    def test_mx_edges_menu_is_registered_as_safe(self) -> None:
        """Menu 253 must route to the MxEdge export as a safe operation."""
        import MistHelper  # Import the runtime menu registry under test.
        from src.utils.operation_registry import OperationRegistry  # Read the safety classification.

        action, description = MistHelper.menu_actions["253"]  # Read the menu dispatch tuple.
        assert action is OrgSearchExporter.mx_edges  # Require the new menu to call the exporter.
        assert "searchOrgMxEdges" in description  # Expose the operation identifier to operators.
        assert OperationRegistry.get("253")["category"] == "safe"  # Keep the read-only operation automated.

    def test_mx_edge_strategy_uses_the_id_and_mac_pair(self) -> None:
        """MxEdge rows must upsert on the identifier and the MAC address."""
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["searchOrgMxEdges"]  # Read the catalog entry.

        assert strategy["type"] == "composite_pk"  # Require update-safe MxEdge storage.
        assert strategy["primary_key"] == ["id", "mac"]  # Require stable uniqueness for repeated exports.


class TestUserMacSearch:
    """Cover the organization user MAC search filters and export binding."""

    def test_user_macs_forwards_optional_filters(self, wired: dict[str, Any]) -> None:
        """The menu entry must convert and forward every entered filter to the SDK."""
        target = wired["mistapi"].api.v1.orgs.usermacs.searchOrgUserMacs
        target.return_value = [{"id": "mac-1"}]
        answers = iter(["5684dae9ac8b", "byod, flr1", "50", "-timestamp"])  # One answer per prompt.
        wired["InputUtils"].safe_input.side_effect = lambda *args, **kwargs: next(answers)

        OrgSearchExporter.user_macs()

        target.assert_called_once_with(
            wired["apisession"],
            "org-1",
            mac="5684dae9ac8b",
            labels=["byod", "flr1"],
            limit=50,
            sort="-timestamp",
        )
        wired["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"id": "mac-1"}],
            "OrgUserMacs.csv",
            api_function_name="searchOrgUserMacs",
        )

    def test_user_macs_asks_for_the_documented_filters(self, wired: dict[str, Any]) -> None:
        """The prompts must match the optional parameters of the installed SDK."""
        wired["mistapi"].api.v1.orgs.usermacs.searchOrgUserMacs.return_value = [{"id": "mac-1"}]

        OrgSearchExporter.user_macs()

        contexts = [call.kwargs["context"] for call in wired["InputUtils"].safe_input.call_args_list]
        assert contexts == [  # Require the exact prompt set and the exact prompt order.
            "org_search_exporter.searchOrgUserMacs.mac",
            "org_search_exporter.searchOrgUserMacs.labels",
            "org_search_exporter.searchOrgUserMacs.limit",
            "org_search_exporter.searchOrgUserMacs.sort",
        ]

    def test_user_macs_never_asks_for_a_page_number(self, wired: dict[str, Any]) -> None:
        """mistapi.get_all owns the page walk, so a page filter must not exist."""
        wired["mistapi"].api.v1.orgs.usermacs.searchOrgUserMacs.return_value = [{"id": "mac-1"}]

        OrgSearchExporter.user_macs()

        contexts = [call.kwargs["context"] for call in wired["InputUtils"].safe_input.call_args_list]
        assert "org_search_exporter.searchOrgUserMacs.page" not in contexts  # No duplicate pagination.

    def test_user_macs_omits_blank_filters(self, wired: dict[str, Any]) -> None:
        """A blank answer must leave the SDK default in place."""
        target = wired["mistapi"].api.v1.orgs.usermacs.searchOrgUserMacs
        target.return_value = [{"id": "mac-1"}]
        answers = iter(["", "  ", "", "  "])  # Blank and whitespace answers must both be dropped.
        wired["InputUtils"].safe_input.side_effect = lambda *args, **kwargs: next(answers)

        OrgSearchExporter.user_macs()

        target.assert_called_once_with(wired["apisession"], "org-1")

    def test_user_macs_partial_filters_reach_the_sdk(self, wired: dict[str, Any]) -> None:
        """Only the filters that the operator supplied may reach the SDK call."""
        target = wired["mistapi"].api.v1.orgs.usermacs.searchOrgUserMacs
        target.return_value = [{"id": "mac-1"}]
        answers = iter(["5684dae9", "", "", ""])  # Supply the MAC filter only.
        wired["InputUtils"].safe_input.side_effect = lambda *args, **kwargs: next(answers)

        OrgSearchExporter.user_macs()

        target.assert_called_once_with(wired["apisession"], "org-1", mac="5684dae9")

    def test_user_macs_drops_a_single_label(self, wired: dict[str, Any]) -> None:
        """One label must still reach the SDK as a list, because the SDK declares a list."""
        target = wired["mistapi"].api.v1.orgs.usermacs.searchOrgUserMacs
        target.return_value = [{"id": "mac-1"}]
        answers = iter(["", "byod", "", ""])  # Supply the label filter only.
        wired["InputUtils"].safe_input.side_effect = lambda *args, **kwargs: next(answers)

        OrgSearchExporter.user_macs()

        target.assert_called_once_with(wired["apisession"], "org-1", labels=["byod"])

    def test_user_macs_ignores_an_invalid_limit(self, wired: dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
        """Text that is not a number must not reach the SDK as a page size."""
        target = wired["mistapi"].api.v1.orgs.usermacs.searchOrgUserMacs
        target.return_value = [{"id": "mac-1"}]
        answers = iter(["", "", "many", ""])  # Supply an unusable limit only.
        wired["InputUtils"].safe_input.side_effect = lambda *args, **kwargs: next(answers)

        with caplog.at_level(logging.WARNING):
            OrgSearchExporter.user_macs()

        target.assert_called_once_with(wired["apisession"], "org-1")
        assert "Ignoring the invalid searchOrgUserMacs limit value: many" in caplog.text

    def test_user_macs_asks_for_no_filter_before_the_org_is_resolved(self, wired: dict[str, Any]) -> None:
        """An unresolved organization must stop before the first prompt."""
        wired["ConfigUtils"].get_cached_or_prompted_org_id.return_value = None

        OrgSearchExporter.user_macs()

        wired["InputUtils"].safe_input.assert_not_called()  # No prompt runs without an organization.

    def test_user_mac_strategy_uses_the_id_and_mac_pair(self) -> None:
        """User MAC rows must upsert on the identifier and the MAC address."""
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["searchOrgUserMacs"]  # Read the catalog entry.

        assert strategy["type"] == "composite_pk"  # Require update-safe user MAC storage.
        assert strategy["primary_key"] == ["id", "mac"]  # Require stable uniqueness for repeated exports.


class TestUnattendedSweep:
    """A `safe` menu must run under --test without reading stdin. See issue #1765."""

    @pytest.mark.parametrize(
        ("method", "chain"),
        [
            ("user_macs", ("usermacs", "searchOrgUserMacs")),
            ("mx_edges", ("mxedges", "searchOrgMxEdges")),
        ],
    )
    def test_test_mode_skips_every_filter_prompt(
        self, wired: dict[str, Any], monkeypatch: pytest.MonkeyPatch, method: str, chain: tuple[str, ...]
    ) -> None:
        """Test mode must run one unfiltered search and never block on a prompt."""
        monkeypatch.setattr("MistHelper.IS_TEST_MODE", True, raising=False)  # Simulate the --test sweep.
        target = _sdk_target(wired["mistapi"], chain)
        target.return_value = [{"id": "row-1"}]

        getattr(OrgSearchExporter, method)()

        wired["InputUtils"].safe_input.assert_not_called()  # No stdin read during the sweep.
        target.assert_called_once_with(wired["apisession"], "org-1")  # The SDK defaults still apply.
