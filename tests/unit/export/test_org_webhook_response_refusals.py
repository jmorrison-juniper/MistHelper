"""Regression tests for organization webhook delivery response handling."""

from __future__ import annotations  # WHY: support the project Python type syntax.

from typing import Any  # WHY: keep the response fixture compatible with SDK doubles.
from unittest.mock import MagicMock, patch  # WHY: isolate API and persistence boundaries.

import pytest  # WHY: provide fixtures and parameterized response cases.

from src.operations.exporting.export.org_webhook_deliveries_exporter import OrgWebhookDeliveriesExporter

_MODULE = "src.operations.exporting.export.org_webhook_deliveries_exporter"  # WHY: keep patch targets stable.


@pytest.fixture
def fake_mh() -> Any:
    """Return the resolver collaborators required by the exporter."""
    module = MagicMock()  # WHY: expose the session, configuration, and writer used by the exporter.
    module.apisession = MagicMock()  # WHY: the SDK call must receive an authenticated session.
    module.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: reach delivery search.
    return module  # WHY: each test controls the shared resolver without loading MistHelper.py.


class TestOrganizationWebhookResponseHandling:
    """Verify that HTTP responses control pagination and persistence."""

    @pytest.mark.parametrize("status_code", [403, 404, 503])  # WHY: cover authorization and server refusals.
    def test_http_failure_is_rejected_before_pagination(
        self,
        fake_mh: Any,
        caplog: pytest.LogCaptureFixture,
        status_code: int,
    ) -> None:
        """Reject failed cloud responses instead of reporting empty data."""
        response = MagicMock(status_code=status_code)  # WHY: model the SDK response status directly.
        with (
            patch(
                f"{_MODULE}.SourceDependencyResolver",
                fake_mh,
            ),
            patch.object(
                OrgWebhookDeliveriesExporter,
                "_select_webhook_id",
                return_value=("wh-1", "Alarms"),
            ),
            patch(
                f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries",
                return_value=response,
            ),
            patch(f"{_MODULE}.mistapi.get_all") as get_all,
            patch.object(OrgWebhookDeliveriesExporter, "_persist") as persist,
            caplog.at_level("ERROR"),
        ):
            OrgWebhookDeliveriesExporter.deliveries()  # WHY: exercise the menu entry point and its refusal guard.
        get_all.assert_not_called()  # WHY: failed responses must not enter pagination.
        persist.assert_not_called()  # WHY: failed responses must not reach output backends.
        assert f"HTTP {status_code}" in caplog.text  # WHY: operators need the exact cloud status.
        assert "organization webhook deliveries" in caplog.text  # WHY: identify the rejected operation.

    def test_successful_response_reaches_persistence(self, fake_mh: Any) -> None:
        """Pass a successful response to pagination and persistence."""
        response = MagicMock(status_code=200)  # WHY: model a native successful SDK response.
        rows = [{"id": "delivery-1"}]  # WHY: one row proves the result is not treated as empty.
        with (
            patch(f"{_MODULE}.SourceDependencyResolver", fake_mh),
            patch.object(
                OrgWebhookDeliveriesExporter,
                "_select_webhook_id",
                return_value=("wh-1", "Alarms"),
            ),
            patch(
                f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries",
                return_value=response,
            ),
            patch(f"{_MODULE}.mistapi.get_all", return_value=rows) as get_all,
            patch.object(OrgWebhookDeliveriesExporter, "_persist") as persist,
        ):
            OrgWebhookDeliveriesExporter.deliveries()  # WHY: exercise the successful response path.
        get_all.assert_called_once_with(response=response, mist_session=fake_mh.apisession)  # WHY: page valid data.
        persist.assert_called_once_with(rows, "Alarms")  # WHY: preserve rows and the selected webhook name.

    def test_successful_empty_response_stays_a_valid_no_data_result(self, fake_mh: Any) -> None:
        """Allow a successful empty response to produce the standard no-data notice."""
        response = MagicMock(status_code=200)  # WHY: an empty result is valid only for a successful response.
        with (
            patch(f"{_MODULE}.SourceDependencyResolver", fake_mh),
            patch.object(
                OrgWebhookDeliveriesExporter,
                "_select_webhook_id",
                return_value=("wh-1", "Alarms"),
            ),
            patch(
                f"{_MODULE}.mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries",
                return_value=response,
            ),
            patch(f"{_MODULE}.mistapi.get_all", return_value=[]),
            patch.object(OrgWebhookDeliveriesExporter, "_persist") as persist,
        ):
            OrgWebhookDeliveriesExporter.deliveries()  # WHY: exercise the valid empty-result path.
        persist.assert_called_once_with([], "Alarms")  # WHY: let the existing persistence notice handle no rows.
