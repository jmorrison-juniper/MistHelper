"""Read Mist license data through the portal's existing authenticated session."""

from __future__ import annotations

import logging
import time
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


@dataclass(frozen=True, slots=True)
class ServiceContext:
    """Hold the portal session and the organization settings for one request."""

    api_session: object | None
    organization_id: str | None
    organization_name: str | None
    api_usage_cache: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ApiOutcome:
    """Keep Mist status, response data, and failure state distinct."""

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


class MistApiRequester:
    """Apply shared request pacing and report explicit Mist API outcomes."""

    def __init__(self, context: ServiceContext) -> None:
        """Retain the portal session and its shared rate-limit state."""
        self.context = context
        self._smoothed_delay: float | None = None

    def _pace(self) -> None:
        """Apply shared request pacing before the SDK sends a request."""
        self._smoothed_delay, delay = RateLimitingUtils.get_rate_limited_delay(
            self._smoothed_delay,
            self.context.api_session,
            self.context.api_usage_cache,
        )
        if delay > 0:
            time.sleep(delay)

    def request(self, operation: str, target: str, request_call: Callable[[], Any]) -> ApiOutcome:
        """Retry one rate-limited request and return its final outcome."""
        if self.context.api_session is None:
            return ApiOutcome(operation, None, error="The Mist API session is unavailable.")
        for attempt in range(2):
            outcome = self._request_once(operation, target, request_call)
            if outcome.status_code != 429 or attempt != 0:
                return outcome
            logger.warning("Mist limited %s for %s. Waiting 60 seconds before one retry.", operation, target)
            time.sleep(60)
        return ApiOutcome(operation, 429, error=f"{operation} still returned HTTP 429 after one retry.")

    def _request_once(self, operation: str, target: str, request_call: Callable[[], Any]) -> ApiOutcome:
        """Send one SDK request and classify its response or exception."""
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


class OrganizationAccess:
    """Discover direct and MSP organizations visible to the active session."""

    def __init__(self, context: ServiceContext, requester: MistApiRequester) -> None:
        """Reuse the request-scoped session and API requester."""
        self.context = context
        self.requester = requester

    @staticmethod
    def _choice(org_id: Any, name: Any, source: str) -> dict[str, str] | None:
        """Build a valid organization choice from a Mist response row."""
        if not isinstance(org_id, str) or not org_id.strip():
            return None
        return {"org_id": org_id, "name": name if isinstance(name, str) and name else org_id, "source": source}

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

    def _msp_organizations(self, msp_id: str) -> tuple[list[dict[str, str]], list[ApiOutcome]]:
        """Read organizations only from an MSP grant in the shared session."""
        outcome = self.requester.request(
            "listMspOrgs",
            msp_id,
            lambda: msp_orgs_api.listMspOrgs(self.context.api_session, msp_id),
        )
        if not outcome.succeeded:
            return [], [outcome]
        if not isinstance(outcome.data, list):
            error = ApiOutcome("listMspOrgs", outcome.status_code, error="Mist returned an invalid organization list.")
            return [], [error]
        choices = [
            choice
            for row in outcome.data
            if isinstance(row, dict)
            for choice in [self._choice(row.get("id"), row.get("name"), "msp")]
            if choice is not None
        ]
        return choices, []

    def discover(self) -> tuple[list[dict[str, str]], list[ApiOutcome]]:
        """Return unique direct and MSP organizations available to the session."""
        profile_call = partial(self_api.getSelf, self.context.api_session)
        profile = self.requester.request("getSelf", "active session", profile_call)
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


class OrganizationDataReader:
    """Read license catalog, license use, and paginated inventory data."""

    def __init__(self, context: ServiceContext, requester: MistApiRequester) -> None:
        """Reuse the active session and the shared request pacing policy."""
        self.context = context
        self.requester = requester

    def read_license_catalog(self) -> ApiOutcome:
        """Read bundle definitions from the installed Mist API catalog."""
        result = self.requester.request(
            "listLicenseTypes",
            "license catalog",
            lambda: license_types_api.listLicenseTypes(self.context.api_session),
        )
        if result.succeeded and not isinstance(result.data, list):
            return ApiOutcome("listLicenseTypes", result.status_code, error="Mist returned an invalid license catalog.")
        return result

    def _inventory_page(self, org_id: str, page_size: int, page_number: int) -> ApiOutcome:
        """Read one explicit page through the installed Mist SDK."""
        request_call: Callable[[], Any] = partial(
            inventory_api.getOrgInventory,
            self.context.api_session,
            org_id,
            limit=page_size,
            page=page_number,
        )
        return self.requester.request("getOrgInventory", org_id, request_call)

    def read_inventory(self, org_id: str) -> ApiOutcome:
        """Read inventory pages in order and preserve partial data on failure."""
        page_size = int(runtime_settings.DEFAULT_API_PAGE_LIMIT)
        page_number = 1
        records: list[Any] = []
        while True:
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
            records.extend(result.data)
            if not result.has_more and len(result.data) < page_size:
                return ApiOutcome("getOrgInventory", result.status_code, records)
            page_number += 1

    def read_organization(self, org_id: str) -> tuple[ApiOutcome, ApiOutcome, ApiOutcome]:
        """Read and validate the three Mist data groups for one organization."""
        summary = self.requester.request(
            "getOrgLicensesSummary",
            org_id,
            lambda: licenses_api.getOrgLicensesSummary(self.context.api_session, org_id),
        )
        site_use = self.requester.request(
            "getOrgLicensesBySite",
            org_id,
            lambda: licenses_api.getOrgLicensesBySite(self.context.api_session, org_id),
        )
        inventory = self.read_inventory(org_id)
        if site_use.succeeded and not isinstance(site_use.data, list):
            site_use = ApiOutcome(
                "getOrgLicensesBySite",
                site_use.status_code,
                error="Mist returned invalid site license use.",
            )
        if inventory.succeeded and not isinstance(inventory.data, list):
            inventory = ApiOutcome("getOrgInventory", inventory.status_code, error="Mist returned invalid inventory.")
        return summary, site_use, inventory
