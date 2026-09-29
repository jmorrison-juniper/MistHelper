"""Mist API client for the client fingerprint census report."""

from __future__ import annotations  # WHY: keep annotations modern across supported Python versions.

import logging  # WHY: trace API calls and response sizes.
from typing import Protocol, cast  # WHY: type the SDK session seam and safe response casting.

import mistapi  # WHY: use the installed SDK paging helper for count responses.
from mistapi.api.v1.sites import insights  # WHY: SDK exposes the site-scoped fingerprint aliases here.

from src.reports.client_fingerprint_census.model import RawFingerprintCount

logger = logging.getLogger(__name__)  # WHY: name this client in the shared log stream.


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
        logger.info("Reading all client fingerprint census count rows")  # WHY: action log before pagination.
        raw_rows = mistapi.get_all(response=response, mist_session=self._mist_session)  # WHY: normalize pages.
        rows = cast(list[RawFingerprintCount], raw_rows)  # WHY: the SDK returns JSON dict rows.
        logger.debug("Read client fingerprint census count rows=%d", len(rows))  # WHY: result summary.
        return rows  # WHY: model layer owns validation and sorting.
