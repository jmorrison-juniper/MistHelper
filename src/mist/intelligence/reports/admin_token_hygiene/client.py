"""Mist API client for the admin and API token hygiene report."""

from __future__ import annotations

import logging
from typing import Any

import mistapi

logger = logging.getLogger(__name__)


class AdminTokenHygieneClient:
    """Read admin, token, and setting metadata for one organization."""

    def __init__(self, apisession: Any, org_id: str) -> None:
        """Keep the Mist session and organization identifier."""
        self._apisession = apisession  # WHY: each SDK call needs the active Mist API session.
        self._org_id = org_id  # WHY: each SDK call reads one organization.

    @staticmethod
    def _status_code(response: Any) -> int:
        """Return the HTTP status code, or success for simple response doubles."""
        status_code = getattr(response, "status_code", 200)  # WHY: tests can use small response doubles.
        return status_code if isinstance(status_code, int) else 200  # WHY: non-integer mocks are not status codes.

    @classmethod
    def _raise_when_list_failed(cls, response: Any, endpoint_name: str) -> None:
        """Raise when a required list endpoint failed."""
        status_code = cls._status_code(response)  # WHY: list endpoints must fail closed on HTTP errors.
        if status_code >= 400:  # WHY: a partial or refused list cannot produce a trustworthy report.
            raise RuntimeError(f"{endpoint_name} failed with HTTP {status_code}")

    def _rows_from_response(self, response: Any) -> list[dict[str, Any]]:
        """Return response rows without logging the response body."""
        rows = mistapi.get_all(  # WHY: later pages need the same authenticated session as the first page.
            response=response,
            mist_session=self._apisession,
        )
        if isinstance(rows, list):  # WHY: the expected list shape can pass through unchanged.
            return [row for row in rows if isinstance(row, dict)]  # WHY: report rows must be mapping objects.
        data = getattr(response, "data", rows)  # WHY: some test doubles expose only a data attribute.
        if isinstance(data, list):  # WHY: list data is the normal non-paged response shape.
            return [row for row in data if isinstance(row, dict)]  # WHY: skip malformed items safely.
        return []  # WHY: an unexpected shape yields no rows without exposing sensitive fields.

    def list_admins(self) -> list[dict[str, Any]]:
        """Read organization administrators."""
        logger.info("Reading organization administrators for org %s", self._org_id)  # WHY: action log before call.
        response = mistapi.api.v1.orgs.admins.listOrgAdmins(self._apisession, self._org_id)  # WHY: SDK endpoint.
        self._raise_when_list_failed(response, "listOrgAdmins")  # WHY: admin read failures must stop the operation.
        rows = self._rows_from_response(response)  # WHY: normalize the SDK response into dictionaries.
        logger.debug("Read %d administrator rows", len(rows))  # WHY: count only, with no sensitive payload.
        return rows  # WHY: the model layer scores these raw admin dictionaries.

    def list_tokens(self) -> list[dict[str, Any]]:
        """Read organization API tokens."""
        logger.info("Reading organization API tokens for org %s", self._org_id)  # WHY: action log before call.
        response = mistapi.api.v1.orgs.apitokens.listOrgApiTokens(  # WHY: use the verified SDK function.
            self._apisession, self._org_id
        )
        self._raise_when_list_failed(response, "listOrgApiTokens")  # WHY: token read failures must stop the run.
        rows = self._rows_from_response(response)  # WHY: normalize before the model removes token keys.
        logger.debug("Read %d organization API token rows", len(rows))  # WHY: count only, never token data.
        return rows  # WHY: the model layer removes secrets before export.

    def get_settings(self) -> dict[str, Any]:
        """Read organization settings."""
        logger.info("Reading organization settings for org %s", self._org_id)  # WHY: action log before call.
        response = mistapi.api.v1.orgs.setting.getOrgSettings(self._apisession, self._org_id)  # WHY: SDK endpoint.
        if self._status_code(response) >= 400:  # WHY: settings are optional context, so the report can continue.
            logger.warning("The organization settings read returned HTTP %s", self._status_code(response))
            return {}  # WHY: missing settings become unknown context by contract.
        data = getattr(response, "data", {})  # WHY: settings return one object under the data attribute.
        settings = data if isinstance(data, dict) else {}  # WHY: the model expects a mapping.
        logger.debug("Read organization settings present=%s", bool(settings))  # WHY: no settings payload in logs.
        return settings  # WHY: password policy context is optional.
