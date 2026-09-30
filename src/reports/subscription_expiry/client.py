"""Mist SDK client seam for the subscription expiry report."""

from __future__ import annotations  # Keep annotations import-safe during tests.

import logging  # Record client actions for operator traceability.
from typing import Any  # Type SDK responses without importing Mist response classes.

import mistapi  # Use the project-approved Mist SDK for API calls.

from src.config import runtime_settings  # Reuse the project page-limit setting.
from src.reports.subscription_expiry.model import (
    JsiContractSource,
    LicenseSummarySource,
    LicenseUsageSource,
)

logger = logging.getLogger(__name__)  # Give this module a stable logger name.
HTTP_BAD_REQUEST = 400  # Detect the no-linked-account JSI path.


class JsiAccountNotLinkedError(RuntimeError):
    """Raised when the JSI endpoint reports no linked Juniper account."""


class SubscriptionExpiryClientError(RuntimeError):
    """Raised when a Mist API response reports an unexpected failure."""


class SubscriptionExpiryClient:
    """Wrap the Mist SDK calls used by the subscription expiry report."""

    def __init__(self, apisession: Any) -> None:
        """Store the active Mist API session."""
        self.apisession = apisession  # Keep the session explicit for tests and operation wiring.

    def fetch_license_summary(self, org_id: str) -> LicenseSummarySource:
        """Fetch and normalize the organization license summary."""
        logger.info("Fetching license summary for organization %s", org_id)  # Log before the SDK call.
        response = mistapi.api.v1.orgs.licenses.getOrgLicensesSummary(self.apisession, org_id)  # Call Mist SDK.
        payload = self._response_payload(response)  # Convert the SDK response wrapper to a plain container.
        logger.debug("Fetched license summary payload type %s", type(payload).__name__)  # Log safe result shape.
        return self._license_summary_from_payload(payload)  # Normalize the source payload.

    def fetch_license_usage_by_site(self, org_id: str) -> list[LicenseUsageSource]:
        """Fetch and normalize license usage by site."""
        logger.info("Fetching license usage by site for organization %s", org_id)  # Log before the SDK call.
        response = mistapi.api.v1.orgs.licenses.getOrgLicensesBySite(self.apisession, org_id)  # Call Mist SDK.
        payload = self._response_payload(response)  # Convert the SDK response wrapper to a plain container.
        rows = self._list_payload(payload)  # Normalize singleton or list payloads into a list.
        logger.debug("Fetched %d license usage rows", len(rows))  # Log normalized row count.
        return [self._license_usage_from_payload(row) for row in rows]  # Convert rows to source dataclasses.

    def search_jsi_assets_and_contracts(self, org_id: str) -> list[JsiContractSource]:
        """Fetch and normalize paginated JSI asset and contract rows."""
        logger.info("Searching JSI assets and contracts for organization %s", org_id)  # Log before the SDK call.
        response = mistapi.api.v1.orgs.jsi.searchOrgJsiAssetsAndContracts(
            self.apisession,
            org_id,
            limit=runtime_settings.DEFAULT_API_PAGE_LIMIT,
        )  # Call Mist SDK with the shared page size.
        self._raise_for_jsi_error(response)  # Convert expected 400 response into a clear operation signal.
        rows = mistapi.get_all(response=response, mist_session=self.apisession)  # Let mistapi handle pagination.
        logger.debug("Fetched %d JSI asset and contract rows", len(rows))  # Log normalized row count.
        return [self._jsi_contract_from_payload(row) for row in rows]  # Convert rows to source dataclasses.

    @staticmethod
    def _response_payload(response: Any) -> Any:
        """Return response.data when present, otherwise return the response itself."""
        return getattr(response, "data", response)  # Support SDK responses and plain test containers.

    @staticmethod
    def _list_payload(payload: Any) -> list[dict[str, Any]]:
        """Normalize a payload into a list of dictionaries."""
        if isinstance(payload, list):  # The usage endpoint normally returns a list.
            return [row for row in payload if isinstance(row, dict)]  # Keep only mapping rows.
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):  # Search payloads can nest rows.
            return [row for row in payload["results"] if isinstance(row, dict)]  # Keep only mapping rows.
        if isinstance(payload, dict):  # A singleton mapping can still be normalized.
            return [payload]  # Preserve the one mapping row.
        return []  # Unsupported payloads produce no source rows.

    @staticmethod
    def _license_summary_from_payload(payload: Any) -> LicenseSummarySource:
        """Build a license summary source from a plain payload."""
        source = payload if isinstance(payload, dict) else {}  # Guard against malformed SDK payloads.
        entitled = source.get("entitled") if isinstance(source.get("entitled"), dict) else {}  # Normalize map.
        licenses = source.get("licenses") if isinstance(source.get("licenses"), list) else []  # Normalize list.
        summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}  # Normalize map.
        return LicenseSummarySource(
            dict(entitled), [row for row in licenses if isinstance(row, dict)], dict(summary)
        )  # Build dataclass.

    @staticmethod
    def _license_usage_from_payload(row: dict[str, Any]) -> LicenseUsageSource:
        """Build a license usage source from one plain row."""
        usages = row.get("usages") if isinstance(row.get("usages"), dict) else {}  # Normalize usage map.
        loaded = row.get("fully_loaded") if isinstance(row.get("fully_loaded"), dict) else {}  # Normalize map.
        return LicenseUsageSource(row.get("site_id"), row.get("num_devices"), dict(usages), dict(loaded))  # Build row.

    @staticmethod
    def _jsi_contract_from_payload(row: dict[str, Any]) -> JsiContractSource:
        """Build a JSI contract source from one plain row."""
        return JsiContractSource(
            serial=row.get("serial"),  # Preserve device serial when available.
            model=row.get("model"),  # Preserve device model when available.
            status=row.get("status"),  # Preserve contract status when the API sends it.
            end_date=row.get("end_date"),  # Preserve contract end date when the API sends it.
            sku=row.get("sku"),  # Preserve SKU for future tie-breaks.
            type=row.get("type"),  # Preserve source type for future diagnostics.
            warranty_type=row.get("warranty_type"),  # Preserve Mist contract status.
            eol_time=row.get("eol_time"),  # Preserve end-of-life date source.
            eos_time=row.get("eos_time"),  # Preserve end-of-support date source.
        )

    @staticmethod
    def _raise_for_jsi_error(response: Any) -> None:
        """Raise a clear exception for the expected no-linked-account response."""
        status_code = getattr(response, "status_code", None)  # Read SDK status without requiring SDK class types.
        if status_code is None or status_code < HTTP_BAD_REQUEST:  # Successful SDK responses need no conversion.
            return  # Leave successful and plain test responses alone.
        if status_code == HTTP_BAD_REQUEST:  # Mist returns 400 when no Juniper account is linked.
            logger.warning("The JSI account is not linked for the selected organization")  # Explain the condition.
            raise JsiAccountNotLinkedError("No linked Juniper account is available for JSI contracts.")  # Signal path.
        logger.error("The JSI contract search failed with HTTP %s", status_code)  # Surface unexpected HTTP errors.
        raise SubscriptionExpiryClientError(  # Stop before pagination can hide a failed API response.
            f"The JSI contract search failed with HTTP {status_code}."
        )
