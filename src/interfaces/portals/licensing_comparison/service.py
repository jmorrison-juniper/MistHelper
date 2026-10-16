"""Read and compare Mist license data without storing operator input."""

from __future__ import annotations

import json
import logging
import re
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass
from functools import partial
from typing import Any

import mistapi.api.v1.const.license_types as license_types_api
import mistapi.api.v1.msps.orgs as msp_orgs_api
import mistapi.api.v1.orgs.inventory as inventory_api
import mistapi.api.v1.orgs.licenses as licenses_api
import mistapi.api.v1.self.self as self_api

from src.foundation.runtime.config import runtime_settings
from src.foundation.support.utils.rate_limiting import RateLimitingUtils

logger = logging.getLogger(__name__)
SOURCE_ATTRIBUTION = (
    "MistOrgLicensingComparison by jmorrison-juniper is licensed under "
    "CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)."
)


@dataclass(frozen=True, slots=True)
class ServiceContext:
    """Hold the existing portal session and organization settings."""

    api_session: object | None
    organization_id: str | None
    organization_name: str | None
    api_usage_cache: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ApiOutcome:
    """Keep Mist status, data, and failure state distinct."""

    operation: str
    status_code: int | None
    data: Any = None
    error: str | None = None
    has_more: bool = False

    @property
    def succeeded(self) -> bool:
        """Report only a completed HTTP 2xx response as success."""
        return self.status_code is not None and 200 <= self.status_code < 300 and self.error is None

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible response record."""
        return asdict(self)


class LicensingComparisonService:
    """Discover authorized organizations and build request-scoped comparisons."""

    _number_pattern = re.compile(r"[A-Z0-9_-]{1,32}")

    def __init__(self, context: ServiceContext) -> None:
        """Store the portal-owned Mist session and rate-limit state."""
        self.context = context
        self._smoothed_delay: float | None = None

    def _pace(self) -> None:
        """Apply the shared Mist request pacing policy before each SDK call."""
        self._smoothed_delay, delay = RateLimitingUtils.get_rate_limited_delay(
            self._smoothed_delay,
            self.context.api_session,
            self.context.api_usage_cache,
        )
        if delay > 0:
            time.sleep(delay)

    def _request(self, operation: str, target: str, request_call: Callable[[], Any]) -> ApiOutcome:
        """Call one SDK method and retry one HTTP 429 response."""
        if self.context.api_session is None:
            return ApiOutcome(operation, None, error="The Mist API session is unavailable.")
        for attempt in range(2):
            self._pace()
            logger.info("Reading Mist data with %s for %s.", operation, target)
            try:
                response = request_call()
            except Exception as error:
                logger.error("Mist request %s for %s failed with %s.", operation, target, type(error).__name__)
                return ApiOutcome(operation, None, error=f"{operation} could not reach Mist.")
            status = getattr(response, "status_code", None)
            if type(status) is not int:
                return ApiOutcome(operation, None, error=f"{operation} returned no valid HTTP status.")
            if status == 429 and attempt == 0:
                logger.warning("Mist limited %s for %s. Waiting 60 seconds before one retry.", operation, target)
                time.sleep(60)
                continue
            if not 200 <= status < 300:
                logger.error("Mist request %s for %s returned HTTP %d.", operation, target, status)
                return ApiOutcome(operation, status, error=f"{operation} returned HTTP {status}.")
            logger.debug("Mist request %s for %s succeeded with HTTP %d.", operation, target, status)
            return ApiOutcome(
                operation,
                status,
                getattr(response, "data", None),
                has_more=bool(getattr(response, "next", None)),
            )
        return ApiOutcome(operation, 429, error=f"{operation} still returned HTTP 429 after one retry.")

    @staticmethod
    def _choice(org_id: Any, name: Any, source: str) -> dict[str, str] | None:
        """Build a valid organization choice from a Mist response row."""
        if not isinstance(org_id, str) or not org_id.strip():
            return None
        return {"org_id": org_id, "name": name if isinstance(name, str) and name else org_id, "source": source}

    def _msp_organizations(self, msp_id: str) -> tuple[list[dict[str, str]], list[ApiOutcome]]:
        """Read organizations only from an MSP grant in the shared session."""
        result = self._request(
            "listMspOrgs",
            msp_id,
            lambda: msp_orgs_api.listMspOrgs(self.context.api_session, msp_id),
        )
        if not result.succeeded:
            return [], [result]
        if not isinstance(result.data, list):
            return [], [
                ApiOutcome("listMspOrgs", result.status_code, error="Mist returned an invalid organization list.")
            ]
        choices = [
            choice
            for row in result.data
            if isinstance(row, dict)
            for choice in [self._choice(row.get("id"), row.get("name"), "msp")]
            if choice is not None
        ]
        return choices, []

    @staticmethod
    def _granted_msp_ids(privileges: Any) -> list[str] | None:
        """Return valid MSP grants or report an invalid grant shape."""
        if not isinstance(privileges, list):
            return None
        return sorted(
            {
                row["msp_id"]
                for row in privileges
                if isinstance(row, dict) and isinstance(row.get("msp_id"), str) and row["msp_id"]
            }
        )

    def discover_organizations(self) -> tuple[list[dict[str, str]], list[ApiOutcome]]:
        """Return direct and MSP organizations visible to the current session."""
        profile = self._request("getSelf", "active session", lambda: self_api.getSelf(self.context.api_session))
        if not profile.succeeded:
            return [], [profile]
        if not isinstance(profile.data, dict):
            return [], [ApiOutcome("getSelf", profile.status_code, error="Mist returned an invalid profile.")]
        choices: dict[str, dict[str, str]] = {}
        direct = self._choice(self.context.organization_id, self.context.organization_name, "direct")
        if direct is not None:
            choices[direct["org_id"]] = direct
        msp_ids = self._granted_msp_ids(profile.data.get("privileges", []))
        if msp_ids is None:
            return list(choices.values()), [
                ApiOutcome("getSelf", profile.status_code, error="Mist returned invalid access grants.")
            ]
        errors: list[ApiOutcome] = []
        for msp_id in msp_ids:
            msp_choices, msp_errors = self._msp_organizations(msp_id)
            errors.extend(msp_errors)
            for choice in msp_choices:
                choices.setdefault(choice["org_id"], choice)
        logger.debug("Discovered %d accessible organizations with %d errors.", len(choices), len(errors))
        return list(choices.values()), errors

    @classmethod
    def _valid_count_map(cls, value: Any) -> bool:
        """Accept only license or inventory maps with non-negative whole counts."""
        return isinstance(value, dict) and all(
            isinstance(key, str) and cls._number_pattern.fullmatch(key) and type(count) is int and count >= 0
            for key, count in value.items()
        )

    @classmethod
    def _validate_manual_rows(cls, rows: Any, choices: list[dict[str, str]]) -> tuple[list[dict[str, Any]], str | None]:
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
    def _validate_purchases(cls, purchases: Any, row_ids: set[str]) -> tuple[dict[str, dict[str, int]], str | None]:
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

    @staticmethod
    def _catalog_index(catalog: list[Any]) -> tuple[dict[str, dict[str, Any]], set[str]]:
        """Index license catalog records by normalized name and key."""
        index: dict[str, dict[str, Any]] = {}
        supported: set[str] = set()
        for item in catalog:
            if not isinstance(item, dict):
                continue
            for field in ("name", "type", "key"):
                value = item.get(field)
                if isinstance(value, str) and value:
                    token = value.casefold().replace("-", "_")
                    index[token] = item
                    supported.add(value.upper().replace("_", "-"))
        return index, supported

    @staticmethod
    def _used_counts(summary: Any) -> dict[str, int]:
        """Extract only numeric license use from an organization summary."""
        if not isinstance(summary, dict):
            return {}
        usage = summary.get("summary", {})
        if not isinstance(usage, dict):
            return {}
        return {
            str(name).upper().replace("_", "-"): count
            for name, count in usage.items()
            if type(count) is int and count >= 0
        }

    @classmethod
    def _balances(
        cls,
        used_counts: dict[str, int],
        purchases: dict[str, int],
        catalog_index: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Calculate each purchased license balance and any catalog bundle parts."""
        balances: list[dict[str, Any]] = []
        for license_name, purchased_count in purchases.items():
            used_count = used_counts.get(license_name.upper().replace("_", "-"))
            catalog_item = catalog_index.get(license_name.casefold().replace("-", "_"))
            balances.append(
                {
                    "license_type": license_name,
                    "purchased_count": purchased_count,
                    "used_count": used_count,
                    "remaining_count": purchased_count - used_count if used_count is not None else None,
                    "bundle_components": cls._bundle_components(
                        catalog_item,
                        purchased_count,
                        used_counts,
                    ),
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

    def _read_license_catalog(self) -> ApiOutcome:
        """Read bundle definitions from the installed Mist API catalog."""
        result = self._request(
            "listLicenseTypes", "license catalog", lambda: license_types_api.listLicenseTypes(self.context.api_session)
        )
        if result.succeeded and not isinstance(result.data, list):
            return ApiOutcome("listLicenseTypes", result.status_code, error="Mist returned an invalid license catalog.")
        return result

    def _compare_organization(
        self,
        organization: dict[str, str],
        purchases: dict[str, int],
        catalog_index: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Read summary, site use, and inventory for one authorized organization."""
        org_id = organization["org_id"]
        summary, site_use, inventory = self._organization_data(org_id)
        return {
            **organization,
            "request_status": self._request_status((summary, site_use, inventory)),
            "license_summary": summary.as_dict(),
            "license_use_by_site": site_use.as_dict(),
            "inventory": inventory.as_dict(),
            "balances": (
                self._balances(self._used_counts(summary.data), purchases, catalog_index) if summary.succeeded else []
            ),
        }

    def _organization_data(self, org_id: str) -> tuple[ApiOutcome, ApiOutcome, ApiOutcome]:
        """Read and validate the three Mist data groups for one organization."""
        summary = self._request(
            "getOrgLicensesSummary",
            org_id,
            lambda: licenses_api.getOrgLicensesSummary(self.context.api_session, org_id),
        )
        site_use = self._request(
            "getOrgLicensesBySite",
            org_id,
            lambda: licenses_api.getOrgLicensesBySite(self.context.api_session, org_id),
        )
        inventory = self._read_inventory(org_id)
        if site_use.succeeded and not isinstance(site_use.data, list):
            site_use = ApiOutcome(
                "getOrgLicensesBySite",
                site_use.status_code,
                error="Mist returned invalid site license use.",
            )
        if inventory.succeeded and not isinstance(inventory.data, list):
            inventory = ApiOutcome(
                "getOrgInventory",
                inventory.status_code,
                error="Mist returned invalid inventory.",
            )
        return summary, site_use, inventory

    @staticmethod
    def _request_status(outcomes: tuple[ApiOutcome, ApiOutcome, ApiOutcome]) -> str:
        """Classify complete, partial, or failed organization reads."""
        if all(outcome.succeeded for outcome in outcomes):
            return "success"
        if any(outcome.succeeded for outcome in outcomes):
            return "partial"
        return "failed"

    def _inventory_page(self, org_id: str, page_size: int, page_number: int) -> ApiOutcome:
        """Read one explicit page through the installed Mist SDK."""
        request_call: Callable[[], Any] = partial(
            inventory_api.getOrgInventory,
            self.context.api_session,
            org_id,
            limit=page_size,
            page=page_number,
        )
        return self._request(
            "getOrgInventory",
            org_id,
            request_call,
        )

    def _read_inventory(self, org_id: str) -> ApiOutcome:
        """Read every SDK inventory page in order and preserve page failures."""
        page_size = int(runtime_settings.DEFAULT_API_PAGE_LIMIT)  # Use the shared Mist page limit.
        page_number = 1  # Page numbering starts at one in the Mist API.
        records: list[Any] = []  # Keep earlier pages visible if a later request fails.
        while True:  # Continue only while Mist indicates more inventory.
            result = self._inventory_page(org_id, page_size, page_number)
            if not result.succeeded:
                return ApiOutcome(
                    result.operation,
                    result.status_code,
                    records,
                    f"{result.error} Inventory data may be incomplete.",
                )
            if not isinstance(result.data, list):
                return ApiOutcome(
                    "getOrgInventory",
                    result.status_code,
                    records,
                    "Mist returned invalid inventory data.",
                )
            records.extend(result.data)  # Preserve each validated page in API order.
            if not result.has_more and len(result.data) < page_size:
                return ApiOutcome("getOrgInventory", result.status_code, records)
            page_number += 1  # Request the next page after a full page or a Mist next link.

    @staticmethod
    def _validate_organization_ids(
        organization_ids: Any,
    ) -> tuple[list[str] | None, str | None]:
        """Return valid organization IDs or an input error."""
        if not isinstance(organization_ids, list) or any(
            not isinstance(value, str) or not value for value in organization_ids
        ):
            return None, "Organization IDs must be a list of non-empty strings."
        if len(set(organization_ids)) != len(organization_ids):
            return None, "The organization list contains duplicate IDs."
        return organization_ids, None

    def _select_authorized_organizations(
        self,
        organization_ids: list[str],
    ) -> tuple[list[dict[str, str]], list[dict[str, str]], list[ApiOutcome], str | None]:
        """Resolve requested organizations only from session-discovered access."""
        choices, errors = self.discover_organizations()
        allowed = {choice["org_id"]: choice for choice in choices}
        if any(org_id not in allowed for org_id in organization_ids):
            return choices, [], errors, "The request includes an organization that this session cannot access."
        selected = [allowed[org_id] for org_id in organization_ids]
        return choices, selected, errors, None

    def _comparison_inputs(
        self,
        organization_ids: list[str],
        manual_rows: Any,
        purchased_amounts: Any,
        choices: list[dict[str, str]],
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]], str | None]:
        """Validate manual rows and purchase amounts before reading license data."""
        clean_manual, manual_error = self._validate_manual_rows(manual_rows, choices)
        if manual_error:
            return [], {}, manual_error
        row_ids = set(organization_ids) | {row["org_id"] for row in clean_manual}
        clean_purchases, purchase_error = self._validate_purchases(purchased_amounts, row_ids)
        return clean_manual, clean_purchases, purchase_error

    def _catalog_for_purchases(
        self,
        purchases: dict[str, dict[str, int]],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None, str | None]:
        """Load current bundle metadata and reject unknown license names."""
        if not any(purchases.values()):
            return {}, None, None
        result = self._read_license_catalog()
        if not result.succeeded:
            return {}, result.as_dict(), None
        catalog_index, supported = self._catalog_index(result.data)
        requested_names = {name.upper().replace("_", "-") for values in purchases.values() for name in values}
        if not requested_names.issubset(supported):
            return {}, None, "Purchased amounts name an unsupported license type."
        return catalog_index, None, None

    def _manual_result(
        self,
        manual: dict[str, Any],
        purchases: dict[str, dict[str, int]],
        catalog_index: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Build the result shape for one operator-entered organization."""
        used_counts = {name.upper().replace("_", "-"): count for name, count in manual["licenses"].items()}
        return {
            **manual,
            "request_status": "manual",
            "license_summary": {
                "operation": "manual",
                "status_code": 200,
                "data": {"summary": manual["licenses"]},
                "error": None,
            },
            "license_use_by_site": {"operation": "manual", "status_code": 200, "data": [], "error": None},
            "inventory": {
                "operation": "manual",
                "status_code": 200,
                "data": manual["inventory"],
                "error": None,
            },
            "balances": self._balances(
                used_counts,
                purchases.get(manual["org_id"], {}),
                catalog_index,
            ),
        }

    def _comparison_results(
        self,
        selected: list[dict[str, str]],
        manual_rows: list[dict[str, Any]],
        purchases: dict[str, dict[str, int]],
        catalog_index: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Combine Mist organization rows and session-only manual rows."""
        results = [
            self._compare_organization(
                organization,
                purchases.get(organization["org_id"], {}),
                catalog_index,
            )
            for organization in selected
        ]
        results.extend(self._manual_result(manual, purchases, catalog_index) for manual in manual_rows)
        return results

    def compare(
        self,
        organization_ids: Any,
        manual_rows: Any,
        purchased_amounts: Any,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Validate the request and compare only server-authorized organizations."""
        if self.context.api_session is None:
            return None, "The Mist API session is unavailable.", 503
        valid_organization_ids, validation_error = self._validate_organization_ids(organization_ids)
        if validation_error:
            return None, validation_error, 400
        if valid_organization_ids is None:
            return None, "Organization IDs must be a list of non-empty strings.", 400
        choices, selected, discovery_errors, access_error = self._select_authorized_organizations(
            valid_organization_ids
        )
        if access_error:
            return None, access_error, 403
        clean_manual, clean_purchases, input_error = self._comparison_inputs(
            valid_organization_ids,
            manual_rows,
            purchased_amounts,
            choices,
        )
        if input_error:
            return None, input_error, 400
        catalog_index, catalog_error, catalog_validation_error = self._catalog_for_purchases(clean_purchases)
        if catalog_validation_error:
            return None, catalog_validation_error, 400
        results = self._comparison_results(selected, clean_manual, clean_purchases, catalog_index)
        logger.debug(
            "Built %d comparison rows with %d access discovery errors.",
            len(results),
            len(discovery_errors),
        )
        return (
            {
                "results": results,
                "discovery_errors": [error.as_dict() for error in discovery_errors],
                "catalog_error": catalog_error,
            },
            None,
            200,
        )

    @staticmethod
    def _safe_cell(value: Any) -> Any:
        """Neutralize spreadsheet formula markers in text cells."""
        if not isinstance(value, str):
            return value
        if value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    @classmethod
    def export_rows(cls, payload: Any) -> tuple[list[dict[str, Any]], str | None]:
        """Build CSV rows from a validated comparison response."""
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list) or not payload["results"]:
            return [], "The comparison has no exportable rows."
        rows: list[dict[str, Any]] = []
        for result in payload["results"]:
            row = cls._export_row(result)
            if row is None:
                return [], "Each comparison row must include an organization name."
            rows.append(row)
        return rows, None

    @classmethod
    def _export_row(cls, result: Any) -> dict[str, Any] | None:
        """Build one CSV row or reject a missing organization name."""
        if not isinstance(result, dict) or not isinstance(result.get("name"), str):
            return None
        return {
            "organization": cls._safe_cell(result["name"]),
            "organization_id": cls._safe_cell(result.get("org_id", "")),
            "source": cls._safe_cell(result.get("source", "")),
            "source_attribution": SOURCE_ATTRIBUTION,
            "request_status": cls._safe_cell(result.get("request_status", "unavailable")),
            "license_summary": cls._json_cell(result.get("license_summary", "")),
            "license_use_by_site": cls._json_cell(result.get("license_use_by_site", "")),
            "inventory": cls._json_cell(result.get("inventory", "")),
            "balances": cls._json_cell(result.get("balances", "")),
        }

    @classmethod
    def _json_cell(cls, value: Any) -> Any:
        """Serialize nested data with stable keys and formula-safe text."""
        serialized = json.dumps(value, ensure_ascii=True, sort_keys=True)
        return cls._safe_cell(serialized)
