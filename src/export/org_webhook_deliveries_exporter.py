"""Export organization webhook delivery search results."""

from __future__ import annotations  # WHY: support the project Python type syntax.

import logging  # WHY: record each export action for operator diagnosis.
import re  # Recognize only a safe HTTP status in an existing SDK exception contract.
from typing import Any  # WHY: Mist API rows are JSON-shaped dictionaries.

import mistapi  # WHY: call the installed Mist SDK endpoint.

from src.api.response_integrity import ResponseIntegrityChecker  # Detect the SDK's retained malformed-body signal.
from src.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)
from src.data.data_processing_utils import DataProcessingUtils  # WHY: reuse shared CSV-safe flattening.
from src.utils.input_utils import InputUtils  # WHY: handle EOF safely in SSH and container sessions.

logger = logging.getLogger(__name__)  # Use a module logger for non-exception export messages.

_OPERATION = "searchOrgWebhooksDeliveries"  # WHY: select the configured storage-key strategy.


class OrgWebhookResponseRefusal(ValueError):
    """Carry a safe validation reason without an I/O operation."""


class OrgWebhookDeliveriesExporter:
    """Export webhook deliveries for one organization webhook."""

    class ResponsePages:
        """Validate each native response before accepting the complete collection."""

        @classmethod
        def read(cls, response: object, resource: tuple[str, str, str]) -> list[dict[str, Any]] | None:
            """Return accepted rows, or report a refusal before any persistence."""
            logger.info("Reading webhook response pages for resource=%s", resource[0])
            rows: list[dict[str, Any]] = []
            visited: set[str] = set()
            page, checked = 1, 0
            while True:
                status: object = None
                try:
                    checked += 1  # Count a response decision, including a failed status or body.
                    status = getattr(response, "status_code", None)
                    cls._status(status)
                    rows.extend(cls._rows(response))
                    next_link = cls._next_link(response, visited)
                    logger.debug("Checked webhook response page=%s checked_pages=%s rows=%s", page, checked, len(rows))
                    if not next_link:
                        return rows
                    page, status = page + 1, None
                    logger.info("Reading next webhook response page=%s", page)
                    response = mistapi.get_next(mist_session=SourceDependencyResolver.apisession, response=response)
                except Exception as exception:  # Keep unreadable properties and SDK pagination errors inside the menu.
                    cls.report_refusal(exception, resource, (page, checked, status))
                    return None

        @staticmethod
        def _status(status: object) -> int:
            """Require a reliable successful HTTP status before reading the body."""
            if not isinstance(status, int) or isinstance(status, bool) or not 100 <= status < 600:
                raise OrgWebhookResponseRefusal("The HTTP status is unavailable or invalid.")
            if not 200 <= status < 300:
                raise OrgWebhookResponseRefusal(f"HTTP {status} did not confirm a successful response.")
            return status

        @staticmethod
        def _rows(response: object) -> list[dict[str, Any]]:
            """Accept only readable native list or results pages with object records."""
            body = getattr(response, "raw_data", None)
            if not isinstance(body, str) or not body.strip() or ResponseIntegrityChecker.body_failed_to_parse(response):
                raise OrgWebhookResponseRefusal("The response body is empty or unavailable, or did not parse as JSON.")
            payload = getattr(response, "data", None)
            if isinstance(payload, dict) and payload.get("error"):
                raise OrgWebhookResponseRefusal("The response body reports an API error.")
            payload = payload.get("results") if isinstance(payload, dict) else payload
            if not isinstance(payload, list):
                raise OrgWebhookResponseRefusal("The response body does not contain a record array.")
            rows: list[dict[str, Any]] = []
            for row in payload:
                if not isinstance(row, dict):
                    raise OrgWebhookResponseRefusal("The response body contains a non-object record.")
                rows.append(row)
            return rows

        @staticmethod
        def _next_link(response: object, visited: set[str]) -> str | None:
            """Reject malformed or repeated SDK links without changing a valid link."""
            next_link = getattr(response, "next", None)
            if next_link is not None and not isinstance(next_link, str):
                raise OrgWebhookResponseRefusal("The next-page link is invalid.")
            if next_link:
                if next_link in visited:
                    raise OrgWebhookResponseRefusal("The next-page link repeats an accepted request.")
                visited.add(next_link)
            return next_link

        @staticmethod
        def report_refusal(
            exception: Exception, resource: tuple[str, str, str], counts: tuple[int, int, object]
        ) -> None:
            """Report measured refusal context without raw bodies or private exception text."""
            reason = str(exception) if isinstance(exception, OrgWebhookResponseRefusal) else type(exception).__name__
            if type(exception) is RuntimeError and len(exception.args) == 1:
                message = exception.args[0]
                if isinstance(message, str) and re.fullmatch(r"HTTP [45][0-9]{2}", message):
                    reason = message  # Preserve the existing explicit HTTP exception contract without arbitrary text.
            context = [value if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) else "unavailable" for value in resource]
            status = counts[2]
            if not isinstance(status, int) or isinstance(status, bool) or not 100 <= status < 600:
                status = "unavailable"
            logger.error(
                "Error fetching organization webhook deliveries: refused resource=%s org_id=%s webhook_id=%s "
                "page=%s checked_pages=%s HTTP %s reason=%s",
                *context,
                counts[0],
                counts[1],
                status,
                reason,
                exc_info=(OrgWebhookResponseRefusal, OrgWebhookResponseRefusal(reason), exception.__traceback__),
            )

    @staticmethod
    def _resolve_webhook_choice(raw: str, webhooks: list[dict[str, Any]]) -> tuple[str, str] | None:
        """Convert a one-based operator choice into a webhook identifier and name."""
        if not raw.isdigit():  # Reject text before integer conversion can fail.
            logger.info("! Invalid webhook selection")  # Tell the operator why the prompt stopped.
            return None
        index = int(raw)  # Convert the validated one-based choice to an integer.
        if not 1 <= index <= len(webhooks):  # Reject choices outside the displayed range.
            logger.info("! Webhook selection must be between 1 and %s", len(webhooks))  # Explain the range.
            return None
        webhook = webhooks[index - 1]  # Select the requested webhook row.
        webhook_id = str(webhook.get("id", ""))  # Preserve the API identifier for the search call.
        webhook_name = str(webhook.get("name") or webhook_id or "webhook")  # Build a safe display label.
        return webhook_id, webhook_name  # Return the validated selection to the caller.

    @staticmethod
    def _select_webhook_id(org_id: str) -> tuple[str, str] | None:
        """List organization webhooks and prompt for one selection."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        resource = ("listOrgWebhooks", org_id, "selection")
        logger.info("Listing organization webhooks for org_id=%s", org_id)  # Log before the SDK call.
        try:
            response = mistapi.api.v1.orgs.webhooks.listOrgWebhooks(mh.apisession, org_id)
            webhooks = OrgWebhookDeliveriesExporter.ResponsePages.read(response, resource)
        except Exception as exception:
            OrgWebhookDeliveriesExporter.ResponsePages.report_refusal(exception, resource, (1, 0, None))
            return None
        if webhooks is None:
            return None
        logger.debug("Received %d organization webhooks", len(webhooks))  # Log the choice count.
        if not webhooks:  # Stop when the organization has no configured webhooks.
            logger.info("! No webhooks configured for this organization")  # Give the operator a clear result.
            return None
        for index, webhook in enumerate(webhooks, start=1):  # Display one-based choices for the operator.
            logger.info(
                "  %s. %s [%s]", index, webhook.get("name", "(unnamed)"), webhook.get("id", "?")
            )  # Show choices.
        raw = InputUtils.safe_input(
            "Select webhook number: ", context="org_webhook_deliveries_selection"
        )  # Prompt safely.
        return OrgWebhookDeliveriesExporter._resolve_webhook_choice(raw, webhooks)  # Validate the choice.

    @staticmethod
    def _persist(rawdata: list[Any], webhook_name: str) -> None:
        """Flatten and persist delivery rows."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        if not rawdata:  # Treat an empty search result as a valid outcome.
            logger.info("! No organization webhook delivery data found")  # Tell the operator no rows exist.
            return
        flattened = DataProcessingUtils.flatten_nested_fields(rawdata)  # Normalize nested API values.
        sanitized = DataProcessingUtils.escape_multiline(flattened)  # Keep multiline fields CSV-safe.
        safe_name = webhook_name.replace(" ", "_")  # Keep the output filename portable.
        filename = f"OrgWebhookDeliveries_{safe_name}.csv"  # Use a stable organization export filename.
        logger.info("Writing organization webhook delivery data")  # Log before the storage action.
        mh.DataExporter.write_with_format_selection(sanitized, filename, api_function_name=_OPERATION)  # Persist rows.
        logger.debug("%s persisted %d rows to %s", _OPERATION, len(rawdata), filename)  # Log the write result.
        logger.info(
            "! %d organization webhook delivery records exported to %s", len(rawdata), filename
        )  # Report success.

    @staticmethod
    def deliveries() -> None:
        """Search and export deliveries for one organization webhook."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Organization Webhook Deliveries Search:")  # Show the selected operation.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the organization context.
        if not org_id:  # Stop when the operator does not select an organization.
            return
        webhook_choice = OrgWebhookDeliveriesExporter._select_webhook_id(org_id)  # Resolve the webhook context.
        if webhook_choice is None:  # Stop when no valid webhook exists.
            return
        webhook_id, webhook_name = webhook_choice  # Unpack the selected webhook.
        try:
            logger.info("Calling %s for org_id=%s webhook_id=%s", _OPERATION, org_id, webhook_id)
            response = mistapi.api.v1.orgs.webhooks.searchOrgWebhooksDeliveries(
                mh.apisession, org_id, webhook_id
            )  # Fetch deliveries.
            rawdata = OrgWebhookDeliveriesExporter.ResponsePages.read(response, (_OPERATION, org_id, webhook_id))
            if rawdata is None:
                return
            logger.debug("%s returned %d rows", _OPERATION, len(rawdata))  # Log the response count.
            OrgWebhookDeliveriesExporter._persist(rawdata, webhook_name)  # Write the normalized result.
        except Exception as exception:  # Keep SDK failures inside the menu loop.
            OrgWebhookDeliveriesExporter.ResponsePages.report_refusal(
                exception, (_OPERATION, org_id, webhook_id), (1, 0, None)
            )
