"""Coordinate authorized Mist organization comparisons for the portal."""

from __future__ import annotations

import logging
import re
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

logger = logging.getLogger(__name__)


class ManualRowValidator:
    """Validate session-only organization rows and purchased license counts."""

    _number_pattern = re.compile(r"[A-Z0-9_-]{1,32}")

    @classmethod
    def _valid_count_map(cls, value: Any) -> bool:
        """Accept maps with supported names and non-negative whole counts."""
        return isinstance(value, dict) and all(
            isinstance(key, str) and cls._number_pattern.fullmatch(key) and type(count) is int and count >= 0
            for key, count in value.items()
        )

    @classmethod
    def validate_manual_rows(
        cls,
        rows: Any,
        choices: list[dict[str, str]],
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Validate manual organization rows without making Mist requests."""
        if not isinstance(rows, list):
            return [], "Manual rows must be a list."
        names = {choice["name"].casefold() for choice in choices}
        row_ids: set[str] = set()
        clean_rows: list[dict[str, Any]] = []
        for row in rows:
            clean_row, error = cls._validate_manual_row(row, names, row_ids)
            if error:
                return [], error
            clean_rows.append(clean_row)
        return clean_rows, None

    @classmethod
    def _validate_manual_row(
        cls,
        row: Any,
        names: set[str],
        row_ids: set[str],
    ) -> tuple[dict[str, Any], str | None]:
        """Validate one manual organization and update duplicate trackers."""
        row_id, name, identity_error = cls._manual_identity(row, names, row_ids)
        if identity_error:
            return {}, identity_error
        if row_id is None or name is None:
            return {}, "Each manual row needs a valid identifier and name."
        licenses, inventory = row.get("licenses", {}), row.get("inventory", {})
        if not cls._valid_count_map(licenses) or not cls._valid_count_map(inventory):
            return {}, "Manual license and inventory counts must be non-negative whole numbers."
        row_ids.add(row_id)
        names.add(name.casefold())
        return {
            "org_id": row_id,
            "name": name,
            "source": "manual",
            "licenses": licenses,
            "inventory": inventory,
        }, None

    @staticmethod
    def _manual_identity(
        row: Any,
        names: set[str],
        row_ids: set[str],
    ) -> tuple[str | None, str | None, str | None]:
        """Validate a manual row identifier and a unique organization name."""
        if not isinstance(row, dict):
            return None, None, "Each manual row must be an object."
        row_id, name = row.get("row_id"), row.get("name")
        if not isinstance(row_id, str) or not re.fullmatch(r"manual-[A-Za-z0-9_-]{1,64}", row_id):
            return None, None, "Each manual row needs a valid row_id."
        if row_id in row_ids:
            return None, None, "Manual row identifiers must be unique."
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            return None, None, "Each manual row needs a name of 1 to 120 characters."
        normalized_name = name.strip()
        if normalized_name.casefold() in names:
            return None, None, "Manual organization names must be unique."
        return row_id, normalized_name, None

    @classmethod
    def validate_purchases(
        cls,
        purchases: Any,
        row_ids: set[str],
    ) -> tuple[dict[str, dict[str, int]], str | None]:
        """Validate purchased counts and their organization keys."""
        if not isinstance(purchases, dict):
            return {}, "Purchased amounts must be an object."
        if any(not isinstance(row_id, str) or row_id not in row_ids for row_id in purchases):
            return {}, "Purchased amounts name an organization that is not in this comparison."
        clean_purchases: dict[str, dict[str, int]] = {}
        for row_id, values in purchases.items():
            if not cls._valid_count_map(values):
                return {}, "Purchased amounts must use supported license names and non-negative whole numbers."
            clean_purchases[row_id] = values
        return clean_purchases, None


class OrganizationIdValidator:
    """Validate organization ID arrays before the service reads Mist data."""

    @staticmethod
    def validate(value: Any) -> tuple[list[str] | None, str | None]:
        """Return valid unique organization IDs or an input error."""
        if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
            return None, "Organization IDs must be a list of non-empty strings."
        if len(set(value)) != len(value):
            return None, "The organization list contains duplicate IDs."
        return value, None


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
