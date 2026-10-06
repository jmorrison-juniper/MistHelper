"""Tests for stable menu 256 webhook identifier selection."""

from __future__ import annotations  # Keep modern annotations import-safe.

import sys  # Inject the source dependency host used by the exporter.
from unittest.mock import MagicMock, patch  # Isolate prompt, SDK, and persistence boundaries.

import pytest  # Provide fixtures and parameterized invalid choices.

from src.operations.exporting.export.org_webhook_deliveries_exporter import OrgWebhookDeliveriesExporter

_MODULE = "src.operations.exporting.export.org_webhook_deliveries_exporter"  # Keep patch targets consistent.
_WEBHOOKS = [  # Use identifiers that also prove list reorder behavior.
    {"id": "wh-a", "name": "Alpha"},
    {"id": "wh-b", "name": "Beta"},
]


@pytest.fixture
def mist_helper(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Return a source dependency host with no live Mist credentials."""
    host = MagicMock()  # Provide only the collaborators that the exporter resolves.
    host.apisession = MagicMock(name="offline-mist-session")  # Use a local session marker.
    host.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # Supply one organization.
    monkeypatch.setitem(sys.modules, "MistHelper", host)  # Activate the existing resolver test seam.
    return host  # Let each test inspect the writer and session calls.


class TestStableWebhookResolver:
    """Verify stable identifier priority and legacy one-based positions."""

    def test_exact_identifier_survives_reordered_webhooks(self) -> None:
        """Resolve the same stable identifier after the Mist list order changes."""
        reordered = list(reversed(_WEBHOOKS))  # Simulate a later response with a different order.
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice("wh-b", _WEBHOOKS) == ("wh-b", "Beta")
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice("wh-b", reordered) == ("wh-b", "Beta")

    def test_numeric_identifier_precedes_one_based_position(self) -> None:
        """Choose an exact numeric identifier before position one can capture it."""
        webhooks = [  # Put identifier 1 in the second row to expose precedence.
            {"id": "wh-a", "name": "First row"},
            {"id": "1", "name": "Numeric identifier"},
        ]
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice("1", webhooks) == (
            "1",
            "Numeric identifier",
        )  # Exact identifiers must remain stable even when they contain digits.

    def test_one_based_position_still_selects_the_displayed_row(self) -> None:
        """Preserve the existing command-line selection contract."""
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice(" 2 ", _WEBHOOKS) == ("wh-b", "Beta")

    def test_missing_name_uses_the_identifier(self) -> None:
        """Keep a stable readable result when Mist omits the webhook name."""
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice("wh-c", [{"id": "wh-c"}]) == (
            "wh-c",
            "wh-c",
        )

    @pytest.mark.parametrize("raw", ["", "unknown", "0", "-1", "abc", "3"])
    def test_invalid_identifier_or_position_is_rejected(self, raw: str) -> None:
        """Reject each invalid input before any delivery search can use it."""
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice(raw, _WEBHOOKS) is None

    def test_position_with_no_identifier_is_rejected(self) -> None:
        """Reject a displayed row that cannot produce a stable delivery search key."""
        assert OrgWebhookDeliveriesExporter._resolve_webhook_choice("1", [{"name": "Broken row"}]) is None


class TestWebhookSearchSuppression:
    """Verify invalid input stops before the delivery search."""

    @pytest.mark.parametrize("raw", ["", "unknown", "0", "-1", "abc", "3"])
    def test_invalid_selection_makes_no_delivery_search(self, mist_helper: MagicMock, raw: str) -> None:
        """List webhooks, reject the supplied choice, and make no search call."""
        with (
            patch(f"{_MODULE}.mistapi.api.v1.orgs.webhooks.listOrgWebhooks", return_value=object()),
            patch(f"{_MODULE}.mistapi.get_all", return_value=_WEBHOOKS),
            patch(f"{_MODULE}.InputUtils.safe_input", return_value=raw),
            patch(f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries") as search_call,
        ):
            OrgWebhookDeliveriesExporter.deliveries()  # Run the real list and resolver flow.
        search_call.assert_not_called()  # Invalid input must stop before the delivery endpoint.
        mist_helper.DataExporter.write_with_format_selection.assert_not_called()  # Invalid input writes nothing.

    def test_stable_identifier_reaches_delivery_search_once(self, mist_helper: MagicMock) -> None:
        """Send the selected stable identifier through the existing export flow."""
        deliveries = [{"id": "delivery-1", "webhook_id": "wh-b", "timestamp": 1}]  # Provide one result row.
        with (
            patch(f"{_MODULE}.mistapi.api.v1.orgs.webhooks.listOrgWebhooks", return_value=object()),
            patch(f"{_MODULE}.InputUtils.safe_input", return_value="wh-b"),
            patch(
                f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries",
                return_value=object(),
            ) as search_call,
            patch(f"{_MODULE}.mistapi.get_all", side_effect=[_WEBHOOKS, deliveries]),
            patch.object(OrgWebhookDeliveriesExporter, "_persist") as persist_call,
        ):
            OrgWebhookDeliveriesExporter.deliveries()  # Run the complete menu 256 selection flow.
        search_call.assert_called_once_with(mist_helper.apisession, "org-1", "wh-b")
        persist_call.assert_called_once_with(deliveries, "Beta")  # Preserve existing persistence inputs.
