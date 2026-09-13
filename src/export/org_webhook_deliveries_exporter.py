"""Export organization webhook delivery search results."""

from __future__ import annotations  # WHY: support the project Python type syntax.

import importlib  # WHY: avoid a circular import during MistHelper startup.
import logging  # WHY: record each export action for operator diagnosis.
from typing import Any  # WHY: Mist API rows are JSON-shaped dictionaries.

import mistapi  # WHY: call the installed Mist SDK endpoint.

from src.data.data_processing_utils import DataProcessingUtils  # WHY: reuse shared CSV-safe flattening.
from src.utils.input_utils import InputUtils  # WHY: handle EOF safely in SSH and container sessions.

_OPERATION = "searchOrgWebhooksDeliveries"  # WHY: select the configured storage-key strategy.


class OrgWebhookDeliveriesExporter:
    """Export webhook deliveries for one organization webhook."""

    @staticmethod
    def _resolve_webhook_choice(raw: str, webhooks: list[dict[str, Any]]) -> tuple[str, str] | None:
        """Convert a one-based operator choice into a webhook identifier and name."""
        if not raw.isdigit():  # Reject text before integer conversion can fail.
            logging.info("! Invalid webhook selection")  # Tell the operator why the prompt stopped.
            return None
        index = int(raw)  # Convert the validated one-based choice to an integer.
        if not 1 <= index <= len(webhooks):  # Reject choices outside the displayed range.
            logging.info("! Webhook selection must be between 1 and %s", len(webhooks))  # Explain the range.
            return None
        webhook = webhooks[index - 1]  # Select the requested webhook row.
        webhook_id = str(webhook.get("id", ""))  # Preserve the API identifier for the search call.
        webhook_name = str(webhook.get("name") or webhook_id or "webhook")  # Build a safe display label.
        return webhook_id, webhook_name  # Return the validated selection to the caller.

    @staticmethod
    def _select_webhook_id(org_id: str) -> tuple[str, str] | None:
        """List organization webhooks and prompt for one selection."""
        mh = importlib.import_module("MistHelper")  # WHY: read the live authenticated session.
        logging.info("Listing organization webhooks for org_id=%s", org_id)  # Log before the SDK call.
        response = mistapi.api.v1.orgs.webhooks.listOrgWebhooks(mh.apisession, org_id)  # Fetch choices.
        webhooks = mistapi.get_all(response=response, mist_session=mh.apisession)  # Read all webhook pages.
        logging.debug("Received %d organization webhooks", len(webhooks))  # Log the choice count.
        if not webhooks:  # Stop when the organization has no configured webhooks.
            logging.info("! No webhooks configured for this organization")  # Give the operator a clear result.
            return None
        for index, webhook in enumerate(webhooks, start=1):  # Display one-based choices for the operator.
            logging.info(
                "  %s. %s [%s]", index, webhook.get("name", "(unnamed)"), webhook.get("id", "?")
            )  # Show choices.
        raw = InputUtils.safe_input(
            "Select webhook number: ", context="org_webhook_deliveries_selection"
        )  # Prompt safely.
        return OrgWebhookDeliveriesExporter._resolve_webhook_choice(raw, webhooks)  # Validate the choice.

    @staticmethod
    def _persist(rawdata: list[Any], webhook_name: str) -> None:
        """Flatten and persist delivery rows."""
        mh = importlib.import_module("MistHelper")  # WHY: read the shared writer without a startup cycle.
        if not rawdata:  # Treat an empty search result as a valid outcome.
            logging.info("! No organization webhook delivery data found")  # Tell the operator no rows exist.
            return
        flattened = DataProcessingUtils.flatten_nested_fields(rawdata)  # Normalize nested API values.
        sanitized = DataProcessingUtils.escape_multiline(flattened)  # Keep multiline fields CSV-safe.
        safe_name = webhook_name.replace(" ", "_")  # Keep the output filename portable.
        filename = f"OrgWebhookDeliveries_{safe_name}.csv"  # Use a stable organization export filename.
        logging.info("Writing organization webhook delivery data")  # Log before the storage action.
        mh.DataExporter.write_with_format_selection(sanitized, filename, api_function_name=_OPERATION)  # Persist rows.
        logging.debug("%s persisted %d rows to %s", _OPERATION, len(rawdata), filename)  # Log the write result.
        logging.info(
            "! %d organization webhook delivery records exported to %s", len(rawdata), filename
        )  # Report success.

    @staticmethod
    def deliveries() -> None:
        """Search and export deliveries for one organization webhook."""
        mh = importlib.import_module("MistHelper")  # WHY: read the shared organization resolver and session.
        logging.info("Organization Webhook Deliveries Search:")  # Show the selected operation.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the organization context.
        if not org_id:  # Stop when the operator does not select an organization.
            return
        webhook_choice = OrgWebhookDeliveriesExporter._select_webhook_id(org_id)  # Resolve the webhook context.
        if webhook_choice is None:  # Stop when no valid webhook exists.
            return
        webhook_id, webhook_name = webhook_choice  # Unpack the selected webhook.
        try:
            logging.info(
                "Calling %s for org_id=%s webhook_id=%s", _OPERATION, org_id, webhook_id
            )  # Log before API call.
            response = mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries(
                mh.apisession, org_id, webhook_id
            )  # Fetch deliveries.
            rawdata = mistapi.get_all(response=response, mist_session=mh.apisession)  # Page through all results.
            logging.debug("%s returned %d rows", _OPERATION, len(rawdata))  # Log the response count.
            OrgWebhookDeliveriesExporter._persist(rawdata, webhook_name)  # Write the normalized result.
        except Exception as exception:  # Keep SDK failures inside the menu loop.
            logging.error("Error fetching organization webhook deliveries: %s", exception)  # Record failure context.
            logging.info("! Error fetching organization webhook delivery data: %s", exception)  # Tell the operator.
