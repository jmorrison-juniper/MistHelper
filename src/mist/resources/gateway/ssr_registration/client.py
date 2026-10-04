"""Client for reading SSR registration commands from Mist."""

from __future__ import annotations  # WHY: keep annotations import-safe during bootstrap.

import logging  # WHY: record API action boundaries without exposing secrets.
from typing import Any  # WHY: mistapi sessions and responses are dynamic objects.

logger = logging.getLogger(__name__)  # WHY: let operators filter client log records by module.

REGISTRATION_PATH = "/api/v1/orgs/{org_id}/128routers/register_cmd"  # WHY: OpenAPI path for issue #3568.


class SsrRegistrationClient:
    """Read SSR registration commands for one organization."""

    def __init__(self, apisession: Any) -> None:
        """Store the authenticated Mist API session.

        Args:
            apisession: The active mistapi session from MistHelper.
        """
        self._apisession = apisession  # WHY: the session owns token, host, and transport state.

    def fetch_commands(self, org_id: str, ttl: int | None = None) -> Any:
        """Return the Mist response that holds the registration commands.

        Args:
            org_id: The organization identifier.
            ttl: Optional token lifetime in days.

        Returns:
            The response object returned by ``apisession.mist_get``.
        """
        path = REGISTRATION_PATH.format(org_id=org_id)  # WHY: the organization scopes the command read.
        query = self._build_query(ttl)  # WHY: keep optional query handling testable and small.
        logger.info("Reading SSR registration commands for org=%s", org_id)  # WHY: log before the API call.
        response = self._apisession.mist_get(path, query=query)  # WHY: the SDK lacks this operation helper.
        logger.debug("SSR registration command read returned HTTP %s", getattr(response, "status_code", None))
        return response  # WHY: the operation decides how to present status and payload.

    @staticmethod
    def _build_query(ttl: int | None) -> dict[str, str] | None:
        """Return the optional query string for the registration command read.

        Args:
            ttl: Optional token lifetime in days.

        Returns:
            The query dictionary, or ``None`` when the default lifetime is used.
        """
        if ttl is None:  # WHY: omit the query so Mist uses the documented default of 365 days.
            return None  # WHY: no query means no SDK serializes an empty value.
        return {"ttl": str(ttl)}  # WHY: Mist query values travel as strings.
