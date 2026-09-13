"""Tests for the ``searchOrgInventory`` export menu."""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.export.org_inventory_search_exporter import OrgInventorySearchExporter

MODULE = "src.export.org_inventory_search_exporter"


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire the exporter to isolated SDK, prompt, and writer doubles."""
    mistapi_mod = MagicMock(name="mistapi")
    mistapi_mod.get_all.side_effect = lambda response, mist_session: response
    monkeypatch.setattr(f"{MODULE}.mistapi", mistapi_mod)
    processor = MagicMock(name="DataProcessingUtils")
    processor.flatten_nested_fields.side_effect = lambda rows: rows
    processor.escape_multiline.side_effect = lambda rows: rows
    monkeypatch.setattr(f"{MODULE}.DataProcessingUtils", processor)
    helper = MagicMock(name="MistHelper")
    helper.apisession = MagicMock(name="apisession")
    helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1372"
    helper.InputUtils.safe_input.return_value = ""
    monkeypatch.setitem(__import__("sys").modules, "MistHelper", helper)
    return {"mistapi": mistapi_mod, "processor": processor, "helper": helper}


def test_inventory_calls_sdk_once_and_writes_rows(wired: dict[str, Any]) -> None:
    """The menu calls the endpoint once and uses the operationId for output."""
    target = wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory
    target.return_value = [{"id": "device-1", "mac": "00:11:22:33:44:55"}]

    OrgInventorySearchExporter.inventory()

    target.assert_called_once_with(wired["helper"].apisession, "org-1372")
    wired["helper"].DataExporter.write_with_format_selection.assert_called_once_with(
        [{"id": "device-1", "mac": "00:11:22:33:44:55"}],
        "OrgInventorySearch_org-1372.csv",
        api_function_name="searchOrgInventory",
    )


def test_inventory_forwards_non_empty_filters(wired: dict[str, Any]) -> None:
    """Non-empty prompts become the SDK query parameters, including integer limit."""
    values = iter(["switch", "", "", "edge", "", "", "", "", "", "connected", "", "25", "", ""])
    wired["helper"].InputUtils.safe_input.side_effect = lambda *args, **kwargs: next(values)
    target = wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory
    target.return_value = []

    OrgInventorySearchExporter.inventory()

    target.assert_called_once_with(
        wired["helper"].apisession,
        "org-1372",
        type="switch",
        name="edge",
        status="connected",
        limit=25,
    )
    wired["helper"].DataExporter.write_with_format_selection.assert_not_called()


def test_inventory_empty_org_aborts_before_prompt_or_call(wired: dict[str, Any]) -> None:
    """A cancelled organization selection does not call prompts or the SDK."""
    wired["helper"].ConfigUtils.get_cached_or_prompted_org_id.return_value = ""
    target = wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory

    OrgInventorySearchExporter.inventory()

    target.assert_not_called()
    wired["helper"].InputUtils.safe_input.assert_not_called()


def test_inventory_api_error_is_logged(wired: dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
    """An SDK failure returns to the menu and records an error."""
    wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory.side_effect = RuntimeError("boom")

    with caplog.at_level(logging.ERROR):
        OrgInventorySearchExporter.inventory()

    assert "Error fetching organization inventory search" in caplog.text
