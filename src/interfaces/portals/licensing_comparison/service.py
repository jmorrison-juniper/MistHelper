"""Coordinate authorized Mist organization comparisons for the portal."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.interfaces.portals.licensing_comparison.api import (
    ApiOutcome,
    MistApiRequester,
    OrganizationAccess,
    OrganizationDataReader,
    ServiceContext,
)
from src.interfaces.portals.licensing_comparison.comparison import ComparisonRowBuilder, LicenseCatalog
from src.interfaces.portals.licensing_comparison.validation import ManualRowValidator, OrganizationIdValidator

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PreparedComparison:
    """Hold validated rows and access results for one comparison request."""

    selected: list[dict[str, str]]
    discovery_errors: list[ApiOutcome]
    manual_rows: list[dict[str, Any]]
    purchases: dict[str, dict[str, int]]


class ComparisonCoordinator:
    """Validate access, load catalog data, and build comparison responses."""

    def __init__(
        self,
        context: ServiceContext,
        access: OrganizationAccess,
        data_reader: OrganizationDataReader,
        row_builder: ComparisonRowBuilder,
    ) -> None:
        """Retain collaborators for one request-scoped comparison."""
        self.context = context
        self.access = access
        self.data_reader = data_reader
        self.row_builder = row_builder

    def _prepare(
        self,
        organization_ids: Any,
        manual_rows: Any,
        purchased_amounts: Any,
    ) -> tuple[PreparedComparison | None, str | None, int]:
        """Validate IDs, access, manual rows, and purchase values."""
        valid_ids, error = OrganizationIdValidator.validate(organization_ids)
        if valid_ids is None:
            return None, error or "Organization IDs must be a list of non-empty strings.", 400
        choices, discovery_errors = self.access.discover()
        allowed = {choice["org_id"]: choice for choice in choices}
        # Never trust an organization ID that the active session did not discover.
        if any(org_id not in allowed for org_id in valid_ids):
            return None, "The request includes an organization that this session cannot access.", 403
        clean_manual, error = ManualRowValidator.validate_manual_rows(manual_rows, choices)
        if error:
            return None, error, 400
        row_ids = set(valid_ids) | {row["org_id"] for row in clean_manual}
        clean_purchases, error = ManualRowValidator.validate_purchases(purchased_amounts, row_ids)
        if error:
            return None, error, 400
        selected = [allowed[org_id] for org_id in valid_ids]
        prepared = PreparedComparison(selected, discovery_errors, clean_manual, clean_purchases)
        return prepared, None, 200

    def _catalog_for_purchases(
        self,
        purchases: dict[str, dict[str, int]],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None, str | None]:
        """Load bundle metadata only when the request includes purchases."""
        if not any(purchases.values()):
            return {}, None, None
        outcome = self.data_reader.read_license_catalog()
        if not outcome.succeeded:
            return {}, outcome.as_dict(), None
        catalog_index, supported = LicenseCatalog.index(outcome.data)
        requested = {name.upper().replace("_", "-") for values in purchases.values() for name in values}
        if not requested.issubset(supported):
            return {}, None, "Purchased amounts name an unsupported license type."
        return catalog_index, None, None

    def compare(
        self,
        organization_ids: Any,
        manual_rows: Any,
        purchased_amounts: Any,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Return a comparison only after all submitted data passes validation."""
        if self.context.api_session is None:
            return None, "The Mist API session is unavailable.", 503
        logger.info("Validating a licensing comparison request.")
        prepared, error, status = self._prepare(organization_ids, manual_rows, purchased_amounts)
        if error or prepared is None:
            return None, error, status
        return self._build_response(prepared)

    def _build_response(
        self,
        prepared: PreparedComparison,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Load catalog metadata and assemble the validated comparison response."""
        catalog_index, catalog_error, error = self._catalog_for_purchases(prepared.purchases)
        if error:
            return None, error, 400
        results = self.row_builder.build(prepared.selected, prepared.manual_rows, prepared.purchases, catalog_index)
        logger.debug("Built %d rows with %d discovery errors.", len(results), len(prepared.discovery_errors))
        return (
            {
                "results": results,
                "discovery_errors": [outcome.as_dict() for outcome in prepared.discovery_errors],
                "catalog_error": catalog_error,
            },
            None,
            200,
        )


class LicensingComparisonService:
    """Expose organization discovery and comparison through focused collaborators."""

    def __init__(self, context: ServiceContext) -> None:
        """Build request services around the existing authenticated session."""
        requester = MistApiRequester(context)
        self.access = OrganizationAccess(context, requester)
        self.data_reader = OrganizationDataReader(context, requester)
        row_builder = ComparisonRowBuilder(self.data_reader)
        self.coordinator = ComparisonCoordinator(context, self.access, self.data_reader, row_builder)

    def discover_organizations(self) -> tuple[list[dict[str, str]], list[ApiOutcome]]:
        """Return organizations that the active Mist session can access."""
        return self.access.discover()

    def compare(
        self,
        organization_ids: Any,
        manual_rows: Any,
        purchased_amounts: Any,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Compare authorized Mist organizations and validated manual rows."""
        return self.coordinator.compare(organization_ids, manual_rows, purchased_amounts)
