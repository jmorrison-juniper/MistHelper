"""Limit firmware policy requests to validated SDK settings and catalog operations."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

import mistapi
from mistapi.__api_response import APIResponse
from mistapi.api.v1.orgs import devices, inventory, sites, ssr
from mistapi.api.v1.orgs import setting as org_setting
from mistapi.api.v1.sites import setting as site_setting
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class PolicyError(RuntimeError):
    """Report a failed policy operation without exposing a settings response."""


class PolicyResponse:
    """Validate identifiers and SDK responses before a caller uses their content."""

    @staticmethod
    def identifier(value: str) -> str:
        """Reject malformed scope identifiers before any external request."""
        try:
            return str(UUID(value))  # Validate the external identifier.
        except (ValueError, TypeError, AttributeError) as error:
            raise PolicyError("A scope identifier is not a valid UUID.") from error

    @staticmethod
    def request(call: Callable[[], APIResponse], action: str, identifier: str) -> APIResponse:
        """Check request status and redact exceptions at the request boundary."""
        logger.info("Policy request %s for %s", action, identifier)  # Record the action without its body.
        try:
            response = call()  # Delegate authentication and transport to the SDK.
        except (RequestException, RuntimeError, OSError) as error:
            logger.error("Policy request %s for %s failed: %s", action, identifier, type(error).__name__)
            raise PolicyError(f"{action} failed for {identifier}: {type(error).__name__}.") from None
        status = getattr(response, "status_code", None)  # Reject missing status rather than assuming success.
        if not isinstance(status, int) or not 200 <= status < 300:
            logger.error("Policy request %s for %s returned HTTP %s", action, identifier, status)
            raise PolicyError(f"{action} failed for {identifier}: HTTP {status}.")
        logger.debug("Policy request %s for %s returned HTTP %s", action, identifier, status)
        return response  # Callers validate the expected data shape and pagination.

    @staticmethod
    def mapping(value: Any) -> dict[str, Any]:
        """Reject unreadable settings rather than replacing them with empty settings."""
        if not isinstance(value, dict):
            raise PolicyError("The settings response is not an object.")
        return value  # Preserve the SDK object without logging its sensitive fields.

    @staticmethod
    def rows(value: Any) -> list[dict[str, Any]]:
        """Reject malformed lists before model or scope selection."""
        if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
            raise PolicyError("The list response contains an invalid record.")
        return value  # Preserve each checked record.

    @staticmethod
    def collect(
        session: mistapi.APISession, call: Callable[[], APIResponse], action: str, identifier: str
    ) -> list[dict[str, Any]]:
        """Collect checked SDK pages and refuse a repeated or failed next page."""
        records: list[dict[str, Any]] = []  # Never substitute an incomplete target list.
        seen: set[str] = set()  # Detect a repeated pagination link.
        response = PolicyResponse.request(call, action, identifier)  # Validate the first page.
        while True:
            records.extend(PolicyResponse.rows(response.data))  # Fail when any page is malformed.
            link = getattr(response, "next", None)  # A missing link means the last page.
            if not link:
                return records  # Only a complete list can reach the workflow.
            if link in seen:
                raise PolicyError("The settings target list has a repeated pagination link.")
            seen.add(link)  # Prevent an unbounded pagination loop.

            def next_page(page: APIResponse = response) -> APIResponse:
                """Bind the checked page before requesting its SDK next-page response."""
                return mistapi.get_next(session, page)

            response = PolicyResponse.request(next_page, action, identifier)


@dataclass
class PolicyApi:
    """Expose only the reads and settings writes needed by menu 305."""

    session: mistapi.APISession

    def read(self, scope: Literal["org", "site"], identifier: str) -> dict[str, Any]:
        """Read local settings without substituting an effective organization policy."""
        identifier = PolicyResponse.identifier(identifier)  # Check the scope before using it.

        def call() -> APIResponse:
            """Select the SDK settings read for the requested scope."""
            if scope == "org":
                return org_setting.getOrgSettings(self.session, identifier)
            return site_setting.getSiteSetting(self.session, identifier)

        return PolicyResponse.mapping(PolicyResponse.request(call, f"Read {scope} settings", identifier).data)

    def write(self, scope: Literal["org", "site"], identifier: str, body: dict[str, Any]) -> None:
        """Write settings only and let the workflow verify the saved state."""
        identifier = PolicyResponse.identifier(identifier)  # Check the scope before using it.

        def call() -> APIResponse:
            """Select a settings write, never a firmware execution endpoint."""
            if scope == "org":
                return org_setting.updateOrgSettings(self.session, identifier, body=body)
            return site_setting.updateSiteSettings(self.session, identifier, body=body)

        PolicyResponse.request(call, f"Write {scope} settings", identifier)  # Check every write status.

    def sites(self, org_id: str) -> list[dict[str, Any]]:
        """Read every site before confirmation, including paginated site lists."""
        org_id = PolicyResponse.identifier(org_id)  # Refuse malformed organization input.
        logger.info("Read all policy sites for %s", org_id)  # Record the complete-list action.
        result = PolicyResponse.collect(  # Check every SDK page rather than accepting partial pagination.
            self.session, lambda: sites.listOrgSites(self.session, org_id), "List organization sites", org_id
        )
        logger.debug("Read %s policy sites for %s", len(result), org_id)  # Record the examined count.
        return result  # The workflow reads each site's local settings next.

    def versions(self, org_id: str, kind: str) -> list[dict[str, Any]]:
        """Read the appropriate firmware catalog for the selected hardware type."""
        org_id = PolicyResponse.identifier(org_id)  # Validate the scope before a catalog request.
        device_type = {"ap": "ap", "switch": "switch", "juniper_srx": "gateway", "ssr": "gateway"}
        if kind not in device_type:
            raise PolicyError("The device type has no supported auto-upgrade policy.")

        def call() -> APIResponse:
            """Use the dedicated SSR catalog instead of the gateway catalog."""
            if kind == "ssr":
                return ssr.listOrgAvailableSsrVersions(self.session, org_id)
            return devices.listOrgAvailableDeviceVersions(self.session, org_id, type=device_type[kind])

        return PolicyResponse.rows(PolicyResponse.request(call, "Read firmware versions", org_id).data)

    def inventory(self, org_id: str) -> list[dict[str, Any]]:
        """Read gateway models because SSR catalog rows do not contain model names."""
        org_id = PolicyResponse.identifier(org_id)  # Check the scope before inventory access.
        return PolicyResponse.collect(
            self.session,
            lambda: inventory.getOrgInventory(self.session, org_id, type="gateway"),
            "Read gateway inventory",
            org_id,
        )
