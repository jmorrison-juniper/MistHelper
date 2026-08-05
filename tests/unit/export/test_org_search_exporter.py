"""Unit tests for the organization-scoped search exporter.

Covers specs 874 to 879 (issues #1379, #1382, #1383, #1385 and #1386), which are
menus 230 to 234.

The five operations share one helper, so the shared behavior is tested once and
each menu entry is checked for the binding that makes it distinct.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of the error-path logging.
from typing import Any  # WHY: the monkeypatched fakes carry loose typing.
from unittest.mock import MagicMock  # WHY: collaborator doubles and call assertions.

import pytest  # WHY: monkeypatch and caplog fixtures.

from src.export.org_search_exporter import OrgSearchExporter

# Each row maps a menu entry to the operationId, the filename prefix, and the
# SDK attribute chain that the entry must call.
MENU_BINDINGS = [
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

    monkeypatch.setattr("MistHelper.DataExporter", data_exporter, raising=False)
    monkeypatch.setattr("MistHelper.apisession", apisession, raising=False)
    monkeypatch.setattr("MistHelper.ConfigUtils", config_utils, raising=False)

    return {
        "DataProcessingUtils": data_processing,
        "mistapi": mistapi_mod,
        "DataExporter": data_exporter,
        "apisession": apisession,
        "ConfigUtils": config_utils,
    }


def _sdk_target(mistapi_mod: MagicMock, chain: tuple[str, str]) -> MagicMock:
    """Return the SDK callable double that a menu entry is expected to call."""
    module_attribute, function_name = chain  # Split the module and the function halves.
    module = getattr(mistapi_mod.api.v1.orgs, module_attribute)  # Walk to the SDK submodule double.
    return getattr(module, function_name)  # Return the function double itself.


class TestMenuBindings:
    """Each menu entry must reach its own SDK function and write its own file."""

    @pytest.mark.parametrize(("method", "operation", "prefix", "chain"), MENU_BINDINGS)
    def test_entry_calls_its_endpoint_and_persists(
        self, wired: dict[str, Any], method: str, operation: str, prefix: str, chain: tuple[str, str]
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
        self, wired: dict[str, Any], method: str, operation: str, prefix: str, chain: tuple[str, str]
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
