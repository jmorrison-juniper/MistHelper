"""Build license balances and comparison rows from validated Mist data."""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from src.interfaces.portals.licensing_comparison.api import ApiOutcome, OrganizationDataReader

logger = logging.getLogger(__name__)


class LicenseCatalog:
    """Normalize license names and identify catalog-supported license types."""

    @staticmethod
    def index(catalog: list[Any]) -> tuple[dict[str, dict[str, Any]], set[str]]:
        """Index catalog records by normalized name and supported key."""
        index: dict[str, dict[str, Any]] = {}
        supported: set[str] = set()
        for item in catalog:
            if not isinstance(item, dict):
                continue
            for field in ("name", "type", "key"):
                value = item.get(field)
                if isinstance(value, str) and value:
                    index[value.casefold().replace("-", "_")] = item
                    supported.add(value.upper().replace("_", "-"))
        return index, supported

    @staticmethod
    def used_counts(summary: Any) -> dict[str, int]:
        """Extract only numeric license use from an organization summary."""
        if not isinstance(summary, dict) or not isinstance(summary.get("summary"), dict):
            return {}
        return {
            str(name).upper().replace("_", "-"): count
            for name, count in summary["summary"].items()
            if type(count) is int and count >= 0
        }


class BalanceCalculator:
    """Calculate purchased license balances and bundle component use."""

    @classmethod
    def calculate(
        cls,
        used_counts: dict[str, int],
        purchases: dict[str, int],
        catalog_index: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Return purchased license counts with known use and remaining balance."""
        balances: list[dict[str, Any]] = []
        for license_name, purchased_count in purchases.items():
            used_count = used_counts.get(license_name.upper().replace("_", "-"))
            catalog_item = catalog_index.get(license_name.casefold().replace("-", "_"))
            # Unknown usage stays unknown instead of becoming a false zero balance.
            balances.append(
                {
                    "license_type": license_name,
                    "purchased_count": purchased_count,
                    "used_count": used_count,
                    "remaining_count": purchased_count - used_count if used_count is not None else None,
                    "bundle_components": cls._bundle_components(catalog_item, purchased_count, used_counts),
                }
            )
        return balances

    @staticmethod
    def _bundle_components(
        catalog_item: dict[str, Any] | None,
        purchased_count: int,
        used_counts: dict[str, int],
    ) -> list[dict[str, Any]]:
        """Expand bundle parts from current catalog metadata."""
        includes = catalog_item.get("includes", []) if catalog_item else []
        if not isinstance(includes, list):
            return []
        components: list[dict[str, Any]] = []
        for component, multiplier in Counter(item for item in includes if isinstance(item, str)).items():
            # Repeated catalog entries multiply the purchased component count.
            component_name = component.upper().replace("_", "-")
            component_used = used_counts.get(component_name)
            components.append(
                {
                    "license_type": component_name,
                    "purchased_count": purchased_count * multiplier,
                    "used_count": component_used,
                    "remaining_count": (
                        purchased_count * multiplier - component_used if component_used is not None else None
                    ),
                }
            )
        return components


class ComparisonRowBuilder:
    """Combine API and session-only data into stable comparison rows."""

    def __init__(self, data_reader: OrganizationDataReader) -> None:
        """Retain the reader for the selected Mist organizations."""
        self.data_reader = data_reader

    @staticmethod
    def _request_status(outcomes: tuple[ApiOutcome, ApiOutcome, ApiOutcome]) -> str:
        """Classify complete, partial, or failed organization reads."""
        if all(outcome.succeeded for outcome in outcomes):
            return "success"
        if any(outcome.succeeded for outcome in outcomes):
            return "partial"
        return "failed"

    def _mist_row(
        self,
        organization: dict[str, str],
        purchases: dict[str, int],
        catalog_index: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Build one authorized organization row from Mist responses."""
        org_id = organization["org_id"]
        summary, site_use, inventory = self.data_reader.read_organization(org_id)
        outcomes = (summary, site_use, inventory)
        return {
            **organization,
            "request_status": self._request_status(outcomes),
            "license_summary": summary.as_dict(),
            "license_use_by_site": site_use.as_dict(),
            "inventory": inventory.as_dict(),
            "balances": (
                BalanceCalculator.calculate(LicenseCatalog.used_counts(summary.data), purchases, catalog_index)
                if summary.succeeded
                else []
            ),
        }

    @staticmethod
    def _manual_row(
        manual: dict[str, Any],
        purchases: dict[str, dict[str, int]],
        catalog_index: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Build a manual organization row without persisting operator input."""
        licenses = manual["licenses"]
        return {
            **manual,
            "request_status": "manual",
            "license_summary": {
                "operation": "manual",
                "status_code": 200,
                "data": {"summary": licenses},
                "error": None,
            },
            "license_use_by_site": {"operation": "manual", "status_code": 200, "data": [], "error": None},
            "inventory": {"operation": "manual", "status_code": 200, "data": manual["inventory"], "error": None},
            "balances": BalanceCalculator.calculate(
                LicenseCatalog.used_counts({"summary": licenses}),
                purchases.get(manual["org_id"], {}),
                catalog_index,
            ),
        }

    def build(
        self,
        selected: list[dict[str, str]],
        manual_rows: list[dict[str, Any]],
        purchases: dict[str, dict[str, int]],
        catalog_index: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build rows for selected Mist organizations and manual entries."""
        logger.info(
            "Building comparison rows for %d Mist and %d manual organizations.",
            len(selected),
            len(manual_rows),
        )
        results = [
            self._mist_row(organization, purchases.get(organization["org_id"], {}), catalog_index)
            for organization in selected
        ]
        results.extend(self._manual_row(manual, purchases, catalog_index) for manual in manual_rows)
        logger.debug("Built %d licensing comparison rows.", len(results))
        return results
