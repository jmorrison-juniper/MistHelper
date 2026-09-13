"""Tests for the organization webhook delivery exporter."""

from __future__ import annotations  # WHY: support the project Python type syntax.

import sys  # WHY: replace the lazy MistHelper import with a local test double.
from unittest.mock import MagicMock, patch  # WHY: isolate SDK and writer calls.

import pytest  # WHY: provide fixtures and parameterized cases.

from src.export.org_webhook_deliveries_exporter import OrgWebhookDeliveriesExporter

_MODULE = "src.export.org_webhook_deliveries_exporter"  # WHY: keep patch targets consistent.
_WEBHOOKS = [{"id": "wh-1", "name": "Alarms"}, {"id": "wh-2", "name": "Audits"}]  # WHY: test two valid choices.


@pytest.fixture
def mist_helper(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Return a local MistHelper stand-in."""
    stub = MagicMock()  # WHY: expose the session, resolver, and writer used by the exporter.
    stub.apisession = MagicMock()  # WHY: the SDK receives this authenticated session.
    monkeypatch.setitem(sys.modules, "MistHelper", stub)  # WHY: satisfy the lazy module import.
    return stub  # WHY: let each test configure the shared collaborators.


class TestWebhookSelection:
    """Verify the safe one-based webhook selection."""

    @pytest.mark.parametrize("raw", ["", "x", "0", "3"])  # WHY: cover invalid input boundaries.
    def test_invalid_choices_return_none(self, raw: str) -> None:
        """Reject invalid selections before the API call."""
        assert (
            OrgWebhookDeliveriesExporter._resolve_webhook_choice(raw, _WEBHOOKS) is None
        )  # WHY: no invalid choice may pass.

    def test_valid_choice_returns_id_and_name(self) -> None:
        """Resolve the displayed webhook choice."""
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice("2", _WEBHOOKS) == (
            "wh-2",
            "Audits",
        )  # WHY: choice two maps to row two.

    def test_missing_name_uses_identifier(self) -> None:
        """Keep a valid webhook selectable when its name is absent."""
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice("1", [{"id": "wh-3"}]) == (
            "wh-3",
            "wh-3",
        )  # WHY: the identifier remains stable.


class TestWebhookExport:
    """Verify API calls and persistence."""

    def test_selection_lists_webhooks_and_uses_safe_input(self, mist_helper: MagicMock) -> None:
        """List organization webhooks before prompting."""
        with (
            patch(f"{_MODULE}.mistapi.get_all", return_value=_WEBHOOKS),
            patch(f"{_MODULE}.mistapi.api.v1.orgs.webhooks.listOrgWebhooks", return_value=object()) as list_call,
            patch(f"{_MODULE}.InputUtils.safe_input", return_value="1"),
        ):
            result = OrgWebhookDeliveriesExporter._select_webhook_id("org-1")
        assert result == ("wh-1", "Alarms")  # WHY: the first displayed webhook must resolve.
        list_call.assert_called_once_with(mist_helper.apisession, "org-1")  # WHY: list the selected organization.

    def test_persistence_uses_the_operation_id(self, mist_helper: MagicMock) -> None:
        """Pass the exact operationId to the shared writer."""
        with patch(f"{_MODULE}.DataProcessingUtils.flatten_nested_fields", side_effect=lambda rows: rows):
            with patch(f"{_MODULE}.DataProcessingUtils.escape_multiline", side_effect=lambda rows: rows):
                OrgWebhookDeliveriesExporter._persist([{"status": "success"}], "Alarm Hook")
        kwargs = mist_helper.DataExporter.write_with_format_selection.call_args.kwargs  # WHY: inspect writer routing.
        assert (
            kwargs["api_function_name"] == "searchOrgWebhooksDeliveries"
        )  # WHY: the PK strategy depends on this name.

    def test_deliveries_calls_search_once_and_persists_rows(self, mist_helper: MagicMock) -> None:
        """Run the organization delivery search for the selected webhook."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: provide the required scope.
        with (
            patch.object(OrgWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-1", "Alarms")),
            patch(
                f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries", return_value=object()
            ) as search_call,
            patch(f"{_MODULE}.mistapi.get_all", return_value=[{"id": "delivery-1"}]),
            patch.object(OrgWebhookDeliveriesExporter, "_persist") as persist_call,
        ):
            OrgWebhookDeliveriesExporter.deliveries()
        search_call.assert_called_once_with(
            mist_helper.apisession, "org-1", "wh-1"
        )  # WHY: use the selected identifiers.
        persist_call.assert_called_once_with([{"id": "delivery-1"}], "Alarms")  # WHY: pass all returned rows.

    def test_sdk_error_stays_inside_the_menu(self, mist_helper: MagicMock) -> None:
        """Log an SDK failure without raising it to the menu loop."""
        mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: reach the API call.
        with (
            patch.object(OrgWebhookDeliveriesExporter, "_select_webhook_id", return_value=("wh-1", "Alarms")),
            patch(
                f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries", side_effect=RuntimeError("boom")
            ),
        ):
            OrgWebhookDeliveriesExporter.deliveries()
        mist_helper.DataExporter.write_with_format_selection.assert_not_called()  # WHY: failed calls write nothing.


def test_existing_composite_strategy_matches_delivery_identity() -> None:
    """Keep the existing stable delivery key registration visible to this feature."""
    from src.refactors.endpoint_primary_key_strategies import (
        ENDPOINT_PRIMARY_KEY_STRATEGIES,
    )  # WHY: inspect the central catalog.

    strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["searchOrgWebhooksDeliveries"]  # WHY: the endpoint must be registered.
    assert strategy["type"] == "composite_pk"  # WHY: delivery rows are time-series records.
    assert strategy["primary_key"] == ["id", "webhook_id", "timestamp"]  # WHY: identify repeated deliveries safely.
