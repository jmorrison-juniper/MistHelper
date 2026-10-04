"""Native response-shape regression tests for organization webhook deliveries."""

from __future__ import annotations  # WHY: support the project Python type syntax.

from unittest.mock import MagicMock, patch  # WHY: isolate the native response from live cloud access.

import requests  # WHY: construct the same response type returned by the HTTP client.

from src.operations.exporting.export.org_webhook_deliveries_exporter import OrgWebhookDeliveriesExporter

_MODULE = "src.operations.exporting.export.org_webhook_deliveries_exporter"  # WHY: keep patch targets stable.


def _native_response(status_code: int) -> requests.Response:
    """Build a native requests response with the supplied status."""
    response = requests.Response()  # WHY: verify the exporter reads the real response attribute.
    response.status_code = status_code  # WHY: represent the HTTP result without a network request.
    return response  # WHY: give the test a native response object.


def test_native_http_403_does_not_report_empty_data() -> None:
    """Reject a native HTTP 403 before the SDK can page an empty body."""
    resolver = MagicMock()  # WHY: provide the exporter dependencies without live credentials.
    resolver.apisession = MagicMock()  # WHY: satisfy the SDK call contract.
    resolver.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: reach the delivery search.
    with (
        patch(f"{_MODULE}.SourceDependencyResolver", resolver),
        patch.object(
            OrgWebhookDeliveriesExporter,
            "_select_webhook_id",
            return_value=("wh-1", "Alarms"),
        ),
        patch(
            f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries",
            return_value=_native_response(403),
        ),
        patch(f"{_MODULE}.mistapi.get_all") as get_all,
        patch.object(OrgWebhookDeliveriesExporter, "_persist") as persist,
    ):
        OrgWebhookDeliveriesExporter.deliveries()  # WHY: reproduce the native forbidden-response path.
    assert get_all.call_count == 0, "A native 403 must stop before pagination."  # WHY: prove no page request ran.
    assert persist.call_count == 0, "A native 403 must never write an empty export."  # WHY: prove no file was written.


def test_native_http_500_does_not_report_empty_data() -> None:
    """Reject a native HTTP 500 before the SDK can page an empty body."""
    resolver = MagicMock()  # WHY: provide the exporter dependencies without live credentials.
    resolver.apisession = MagicMock()  # WHY: satisfy the SDK call contract.
    resolver.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: reach the delivery search.
    with (
        patch(f"{_MODULE}.SourceDependencyResolver", resolver),
        patch.object(
            OrgWebhookDeliveriesExporter,
            "_select_webhook_id",
            return_value=("wh-1", "Alarms"),
        ),
        patch(
            f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries",
            return_value=_native_response(500),
        ),
        patch(f"{_MODULE}.mistapi.get_all") as get_all,
        patch.object(OrgWebhookDeliveriesExporter, "_persist") as persist,
    ):
        OrgWebhookDeliveriesExporter.deliveries()  # WHY: reproduce the native server-error path.
    assert get_all.call_count == 0, "A native 500 must stop before pagination."  # WHY: prove no page request ran.
    assert persist.call_count == 0, "A native 500 must never write an empty export."  # WHY: prove no file was written.


def test_native_http_503_does_not_report_empty_data() -> None:
    """Reject a native HTTP 503 before the SDK can page an empty body."""
    resolver = MagicMock()  # WHY: provide the exporter dependencies without live credentials.
    resolver.apisession = MagicMock()  # WHY: satisfy the SDK call contract.
    resolver.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: reach the delivery search.
    with (
        patch(f"{_MODULE}.SourceDependencyResolver", resolver),
        patch.object(
            OrgWebhookDeliveriesExporter,
            "_select_webhook_id",
            return_value=("wh-1", "Alarms"),
        ),
        patch(
            f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries",
            return_value=_native_response(503),
        ),
        patch(f"{_MODULE}.mistapi.get_all") as get_all,
        patch.object(OrgWebhookDeliveriesExporter, "_persist") as persist,
    ):
        OrgWebhookDeliveriesExporter.deliveries()  # WHY: reproduce the native unavailable-response path.
    assert get_all.call_count == 0, "A native 503 must stop before pagination."  # WHY: prove no page request ran.
    assert persist.call_count == 0, "A native 503 must never write an empty export."  # WHY: prove no file was written.
