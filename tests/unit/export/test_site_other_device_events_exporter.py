"""Tests for the site other-device event exporter."""

from __future__ import annotations  # WHY: keep annotations compatible with the project target.

import importlib  # WHY: patch the lazy MistHelper lookup used by the exporter.
from typing import Any  # WHY: type the test stand-in without binding to MistHelper internals.
from unittest.mock import MagicMock, patch  # WHY: isolate the test from Mist Cloud and disk.

import mistapi  # WHY: patch the SDK operation and pagination helper.

from src.export.site_other_device_events_exporter import SiteOtherDeviceEventsExporter
from src.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES


def _fake_mist_helper() -> Any:
    """Return the collaborators used by the exporter."""
    module = MagicMock()  # WHY: provide the shared helpers without importing the CLI entrypoint.
    module.apisession = MagicMock()  # WHY: verify the SDK receives the authenticated session.
    return module  # WHY: let each test patch the lazy import with one stand-in.


def test_primary_key_strategy_uses_mac_and_timestamp() -> None:
    """The endpoint has a stable composite event key for repeatable upserts."""
    strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["searchSiteOtherDeviceEvents"]  # WHY: read the endpoint catalog entry.
    assert strategy["type"] == "composite_pk"  # WHY: event rows need a multi-field key.
    assert strategy["primary_key"] == ["mac", "timestamp"]  # WHY: prevent duplicate rows on repeat runs.


def test_empty_results_do_not_write_an_export() -> None:
    """An empty response reports no data and skips the writer."""
    fake_mh = _fake_mist_helper()  # WHY: provide the lazy module dependency.
    with patch.object(importlib, "import_module", return_value=fake_mh):  # WHY: isolate the persistence helper.
        SiteOtherDeviceEventsExporter._persist_events([], "Branch")  # WHY: exercise the empty-response branch.
    fake_mh.DataExporter.write_with_format_selection.assert_not_called()  # WHY: empty responses need no file.


def test_persistence_routes_flattened_rows_and_operation_name() -> None:
    """Non-empty results use the shared writer and operationId."""
    fake_mh = _fake_mist_helper()  # WHY: capture the write call without touching disk.
    rows = [{"mac": "aa:bb", "metadata": {"vendor": "Juniper"}}]  # WHY: exercise nested-field flattening.
    with patch.object(importlib, "import_module", return_value=fake_mh):  # WHY: isolate MistHelper imports.
        SiteOtherDeviceEventsExporter._persist_events(rows, "Head Office")  # WHY: write one representative site export.
    args, kwargs = fake_mh.DataExporter.write_with_format_selection.call_args  # WHY: inspect the writer contract.
    assert args[1] == "SiteOtherDeviceEvents_Head_Office.csv"  # WHY: spaces must not reach the filename.
    assert kwargs["api_function_name"] == "searchSiteOtherDeviceEvents"  # WHY: select the endpoint PK strategy.
    assert args[0][0]["metadata_vendor"] == "Juniper"  # WHY: nested values must become tabular fields.


def test_menu_entry_resolves_site_calls_sdk_and_persists_rows() -> None:
    """The menu entry passes the selected site to the SDK and persistence path."""
    fake_mh = _fake_mist_helper()  # WHY: provide the session and site resolver.
    fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-1", "Branch")  # WHY: select one site.
    rows = [{"mac": "aa:bb", "timestamp": "2026-09-09T00:00:00Z"}]  # WHY: represent one API event.
    with (
        patch.object(importlib, "import_module", return_value=fake_mh),  # WHY: isolate shared CLI globals.
        patch.object(
            mistapi.api.v1.sites.otherdevices,
            "searchSiteOtherDeviceEvents",
            return_value=MagicMock(),
        ) as search_spy,  # WHY: avoid Mist Cloud and verify the SDK arguments.
        patch.object(mistapi, "get_all", return_value=rows),  # WHY: return deterministic paged data.
        patch.object(SiteOtherDeviceEventsExporter, "_persist_events") as persist_spy,  # WHY: verify the handoff.
    ):
        SiteOtherDeviceEventsExporter.other_device_events()  # WHY: exercise the complete menu path.
    search_spy.assert_called_once_with(fake_mh.apisession, "site-1")  # WHY: verify SDK arguments.
    persist_spy.assert_called_once_with(rows, "Branch")  # WHY: preserve the rows and friendly site name.


def test_sdk_failure_is_logged_without_raising() -> None:
    """An SDK failure stays inside the menu operation."""
    fake_mh = _fake_mist_helper()  # WHY: provide the shared collaborators.
    fake_mh.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-1", "Branch")  # WHY: reach the SDK call.
    with (
        patch.object(importlib, "import_module", return_value=fake_mh),  # WHY: isolate shared CLI globals.
        patch.object(
            mistapi.api.v1.sites.otherdevices,
            "searchSiteOtherDeviceEvents",
            side_effect=RuntimeError("gateway timeout"),
        ),  # WHY: simulate a transport failure.
    ):
        SiteOtherDeviceEventsExporter.other_device_events()  # WHY: verify the error handler keeps the menu alive.
