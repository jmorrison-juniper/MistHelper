"""Mist API client for the client fingerprint census report."""

from __future__ import annotations  # WHY: keep annotations modern across supported Python versions.

import logging  # WHY: trace API calls and response sizes.
from typing import Any, Protocol, cast  # WHY: type the SDK session seam and response status checks.

import mistapi  # WHY: use the installed SDK paging helper for count responses.
from mistapi.api.v1.sites import insights  # WHY: SDK exposes the site-scoped fingerprint aliases here.

from src.reports.client_fingerprint_census.model import RawFingerprintCount

logger = logging.getLogger(__name__)  # WHY: name this client in the shared log stream.

_HTTP_OK = 200  # WHY: old response doubles without a status keep the legacy success behavior.
_HTTP_ERROR_MIN = 400  # WHY: HTTP 4xx and 5xx statuses mean the census payload is not trustworthy.


class MistSession(Protocol):
    """Minimal Mist session protocol used by this client."""


class ClientFingerprintCensusClient:
    """Read client fingerprint census data from Mist."""

    def __init__(self, mist_session: MistSession) -> None:
        """Store the Mist session used by the SDK."""
        self._mist_session = mist_session  # WHY: each report run uses the shared authenticated session.

    def count(self, site_id: str, distinct: str) -> list[RawFingerprintCount]:
        """Return raw count rows for one site and distinct field."""
        logger.info("Calling client fingerprint census count for site %s", site_id)  # WHY: action log before API.
        response = insights.countSiteClientFingerprints(  # WHY: SDK alias matches the site-scoped OpenAPI path.
            self._mist_session,
            site_id,
            distinct=distinct,
            limit=100,
        )
        logger.debug("Client fingerprint census count call returned response=%s", type(response).__name__)
        self._raise_for_http_error(response, site_id)  # WHY: never convert a cloud error into an empty census.
        logger.info("Reading all client fingerprint census count rows")  # WHY: action log before pagination.
        raw_rows = mistapi.get_all(response=response, mist_session=self._mist_session)  # WHY: normalize pages.
        rows = cast(list[RawFingerprintCount], raw_rows)  # WHY: the SDK returns JSON dict rows.
        logger.debug("Read client fingerprint census count rows=%d", len(rows))  # WHY: result summary.
        return rows  # WHY: model layer owns validation and sorting.

    @staticmethod
    def _response_status_code(response: Any) -> int:
        """Return the HTTP status when the SDK response exposes one."""
        status_code = getattr(response, "status_code", _HTTP_OK)  # WHY: simple test doubles may omit status.
        if isinstance(status_code, int):  # WHY: non-integer mock attributes are not useful HTTP statuses.
            return status_code  # WHY: caller compares the actual HTTP status.
        return _HTTP_OK  # WHY: an invalid status type should not break legacy response doubles.

    @classmethod
    def _raise_for_http_error(cls, response: Any, site_id: str) -> None:
        """Raise when the cloud returns an HTTP error response."""
        logger.info("Checking client fingerprint census HTTP status")  # WHY: action log before status gate.
        status_code = cls._response_status_code(response)  # WHY: normalize SDK and test response shapes.
        if status_code < _HTTP_ERROR_MIN:  # WHY: success statuses can continue to pagination.
            logger.debug("Client fingerprint census HTTP status=%d", status_code)  # WHY: success summary.
            return  # WHY: no error handling is needed for successful responses.
        logger.error("Client fingerprint census failed for site %s with HTTP %d", site_id, status_code)
        raise RuntimeError(f"Client fingerprint census failed with HTTP {status_code}")  # WHY: stop bad exports.
