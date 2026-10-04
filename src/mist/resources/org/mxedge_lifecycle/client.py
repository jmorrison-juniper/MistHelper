"""Mist SDK client for the Mist Edge lifecycle operation.

Why:
    One client class keeps all Mist API calls in one place. It logs action
    boundaries without logging secrets such as claim codes.
"""

from __future__ import annotations  # WHY: allow concise type syntax on Python 3.13.

import logging  # WHY: operators need an action trace for every Mist request.
from typing import Any  # WHY: Mist SDK responses contain dynamic JSON values.

import mistapi  # WHY: direct SDK calls are available for every required operation.

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter lifecycle API calls.


class MxEdgeLifecycleApiError(RuntimeError):
    """Raised when Mist returns an HTTP client or server error.

    Why:
        The operation writes one CSV error row when the client raises this
        exception, and tests can verify 4xx and 5xx behavior without network.
    """

    def __init__(self, status_code: int, message: str) -> None:
        """Store the HTTP status code and safe message."""
        super().__init__(f"Mist API returned HTTP {status_code}: {message}")  # WHY: operator sees status.
        self.status_code = status_code  # WHY: tests and callers can branch on class of failure.


class MxEdgeLifecycleClient:
    """Call Mist Edge lifecycle endpoints through `mistapi`.

    Why:
        The operation can be tested with a fake client while this class owns
        SDK signatures and response normalization.
    """

    def __init__(self, session: object, org_id: str) -> None:
        """Store the API session and organization identifier."""
        self.session = session  # WHY: each SDK call needs the authenticated session.
        self.org_id = org_id  # WHY: every endpoint is organization scoped.

    def claim(self, body: dict[str, Any]) -> dict[str, Any]:
        """Claim one Mist Edge into organization inventory."""
        logger.info("Claiming a Mist Edge for org %s", self.org_id)  # WHY: log before the call without the code.
        response = mistapi.api.v1.orgs.mxedges.claimOrgMxEdge(self.session, self.org_id, body)  # WHY: SDK call.
        data = self._data(response)  # WHY: normalize SDK response for callers.
        logger.debug("Mist Edge claim request finished with keys=%s", sorted(data.keys()))  # WHY: result summary.
        return data  # WHY: operation records a redacted detail.

    def assign(self, body: dict[str, Any]) -> dict[str, Any]:
        """Assign one or more Mist Edges to a site."""
        logger.info("Assigning Mist Edges for org %s", self.org_id)  # WHY: log before the call.
        response = mistapi.api.v1.orgs.mxedges.assignOrgMxEdgeToSite(self.session, self.org_id, body)  # WHY: SDK call.
        data = self._data(response)  # WHY: normalize SDK response for callers.
        logger.debug("Mist Edge assign request finished with keys=%s", sorted(data.keys()))  # WHY: result summary.
        return data  # WHY: operation records the result.

    def unassign(self, body: dict[str, Any]) -> dict[str, Any]:
        """Unassign one or more Mist Edges from a site."""
        logger.info("Unassigning Mist Edges for org %s", self.org_id)  # WHY: log before the call.
        response = mistapi.api.v1.orgs.mxedges.unassignOrgMxEdgeFromSite(self.session, self.org_id, body)  # WHY: SDK.
        data = self._data(response)  # WHY: normalize SDK response for callers.
        logger.debug("Mist Edge unassign request finished with keys=%s", sorted(data.keys()))  # WHY: result summary.
        return data  # WHY: operation records the result.

    def bounce(self, mxedge_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Bounce Mist Edge tunnel data ports."""
        logger.info("Bouncing Mist Edge data ports for org %s mxedge %s", self.org_id, mxedge_id)  # WHY: action log.
        response = mistapi.api.v1.orgs.mxedges.bounceOrgMxEdgeDataPorts(  # WHY: SDK call.
            self.session, self.org_id, mxedge_id, body
        )
        data = self._data(response)  # WHY: normalize SDK response for callers.
        logger.debug("Mist Edge port bounce request finished with keys=%s", sorted(data.keys()))  # WHY: summary.
        return data  # WHY: operation records the result.

    def upgrade(self, body: dict[str, Any]) -> dict[str, Any]:
        """Start a Mist Edge upgrade."""
        logger.info("Starting Mist Edge upgrade for org %s", self.org_id)  # WHY: log before the call.
        response = mistapi.api.v1.orgs.mxedges.upgradeOrgMxEdges(self.session, self.org_id, body)  # WHY: SDK call.
        data = self._data(response)  # WHY: normalize SDK response for callers.
        logger.debug("Mist Edge upgrade request finished with keys=%s", sorted(data.keys()))  # WHY: result summary.
        return data  # WHY: operation polls with the returned identifier when present.

    def list_upgrades(self) -> list[dict[str, Any]]:
        """List organization Mist Edge upgrades."""
        logger.info("Listing Mist Edge upgrades for org %s", self.org_id)  # WHY: log before the call.
        response = mistapi.api.v1.orgs.mxedges.listOrgMxEdgeUpgrades(self.session, self.org_id)  # WHY: SDK call.
        rows = self._rows(response)  # WHY: normalize list response for callers.
        logger.debug("Mist Edge upgrade list returned rows=%d", len(rows))  # WHY: result summary.
        return rows  # WHY: operation can find the newest matching upgrade.

    def get_upgrade(self, upgrade_id: str) -> dict[str, Any]:
        """Read one Mist Edge upgrade status."""
        logger.info("Reading Mist Edge upgrade %s for org %s", upgrade_id, self.org_id)  # WHY: log before read.
        response = mistapi.api.v1.orgs.mxedges.getOrgMxEdgeUpgrade(self.session, self.org_id, upgrade_id)  # WHY: SDK.
        data = self._data(response)  # WHY: normalize SDK response for callers.
        logger.debug("Mist Edge upgrade %s read returned keys=%s", upgrade_id, sorted(data.keys()))  # WHY: summary.
        return data  # WHY: operation evaluates terminal status.

    @staticmethod
    def _data(response: Any) -> dict[str, Any]:
        """Return a dictionary from a Mist SDK response."""
        MxEdgeLifecycleClient._raise_for_http_error(response)  # WHY: 4xx and 5xx responses must fail loudly.
        data = getattr(response, "data", response)  # WHY: SDK responses wrap JSON in `.data`.
        if isinstance(data, dict):  # WHY: most lifecycle responses are dictionaries.
            return data  # WHY: caller expects a mapping.
        return {"data": data}  # WHY: preserve non-dict responses without failing.

    @staticmethod
    def _rows(response: Any) -> list[dict[str, Any]]:
        """Return a list of dictionaries from a Mist SDK response."""
        MxEdgeLifecycleClient._raise_for_http_error(response)  # WHY: list reads must fail on HTTP errors.
        data = getattr(response, "data", response)  # WHY: SDK responses wrap JSON in `.data`.
        if isinstance(data, list):  # WHY: list endpoints usually return a list.
            return [row for row in data if isinstance(row, dict)]  # WHY: keep only JSON objects.
        if isinstance(data, dict) and isinstance(data.get("results"), list):  # WHY: some endpoints wrap rows.
            return [row for row in data["results"] if isinstance(row, dict)]  # WHY: keep only JSON objects.
        return []  # WHY: unknown shapes become an empty list for safe polling fallback.

    @staticmethod
    def _raise_for_http_error(response: Any) -> None:
        """Raise an API error when the response carries HTTP 4xx or 5xx."""
        status_code = MxEdgeLifecycleClient._status_code(response)  # WHY: SDK versions expose status differently.
        if status_code < 400:  # WHY: only client and server errors should raise.
            return  # WHY: 2xx and 3xx responses continue to normalization.
        message = MxEdgeLifecycleClient._error_message(response)  # WHY: include a safe failure detail.
        raise MxEdgeLifecycleApiError(status_code, message)  # WHY: operation records this as an error row.

    @staticmethod
    def _status_code(response: Any) -> int:
        """Return the HTTP status code from common SDK fields."""
        value = getattr(response, "status_code", None)  # WHY: requests-like responses use this field.
        if isinstance(value, int):  # WHY: integer values are valid HTTP codes.
            return value  # WHY: caller compares numeric ranges.
        value = getattr(response, "status", None)  # WHY: some SDK responses use status.
        return value if isinstance(value, int) else 200  # WHY: missing status means the SDK accepted the call.

    @staticmethod
    def _error_message(response: Any) -> str:
        """Return a safe error message from an SDK response."""
        data = getattr(response, "data", {})  # WHY: API errors usually place detail in data.
        if isinstance(data, dict):  # WHY: structured errors can name the reason.
            return str(data.get("message") or data.get("error") or data)[:200]  # WHY: keep detail bounded.
        return str(data)[:200]  # WHY: preserve non-dict error detail safely.
