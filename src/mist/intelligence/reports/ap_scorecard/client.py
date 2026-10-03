"""Mist API client for the organization access point scorecard."""

from __future__ import annotations  # WHY: keep annotations import-safe during MistHelper bootstrap.

import logging  # WHY: log before and after the Mist API read.
from collections.abc import Mapping, Sequence  # WHY: type untrusted API rows without mutating them.

import mistapi  # WHY: use the required SDK operation and pagination seam.

logger = logging.getLogger(__name__)  # WHY: let operators filter scorecard client messages.

DEFAULT_PAGE_LIMIT = 1000  # WHY: match the MistHelper default page size and the feature contract.
_HTTP_ERROR_MINIMUM = 400  # WHY: HTTP 4xx and 5xx responses cannot produce trusted rows.


class ApScorecardClient:
    """Read AP statistics for one organization."""

    def __init__(self, mist_session: object, org_id: str, page_limit: int = DEFAULT_PAGE_LIMIT) -> None:
        """Store the session, organization, and page size for AP statistics reads."""
        self._mist_session = mist_session  # WHY: all SDK calls must use the active shared session.
        self._org_id = org_id  # WHY: the org scoped endpoint needs one organization identifier.
        self._page_limit = page_limit  # WHY: tests prove that the client requests 1000 rows per page.

    def list_ap_stats(self) -> list[Mapping[str, object]]:
        """Return all AP statistics rows through the SDK pagination helper."""
        logger.info("Reading AP statistics for organization %s", self._org_id)  # WHY: log before the API call.
        response = mistapi.api.v1.orgs.stats.listOrgDevicesStats(  # WHY: use the required SDK operation.
            self._mist_session,
            self._org_id,
            type="ap",
            limit=self._page_limit,
        )
        self._raise_for_http_error(response)  # WHY: an HTTP failure must not look like an empty org.
        logger.debug("AP statistics first page response passed HTTP validation")  # WHY: summarize call result.
        logger.info("Expanding paginated AP statistics for organization %s", self._org_id)  # WHY: log pagination.
        rows = mistapi.get_all(response=response, mist_session=self._mist_session) or []  # WHY: use the seam.
        normalized = self._normalize_rows(rows)  # WHY: downstream model expects mappings only.
        logger.debug("Expanded AP statistics rows=%d", len(normalized))  # WHY: summarize pagination result.
        return normalized  # WHY: operation owns transformation and export orchestration.

    @staticmethod
    def _raise_for_http_error(response: object) -> None:
        """Raise an explicit error when the SDK response reports an HTTP failure."""
        status_code = getattr(response, "status_code", 200)  # WHY: tests use simple doubles without status codes.
        if isinstance(status_code, int) and status_code >= _HTTP_ERROR_MINIMUM:  # WHY: failure status is terminal.
            logger.error("AP statistics read failed with HTTP status %s", status_code)  # WHY: operator evidence.
            raise RuntimeError(f"AP statistics read failed with HTTP status {status_code}")  # WHY: fail clearly.

    @staticmethod
    def _normalize_rows(rows: Sequence[object]) -> list[Mapping[str, object]]:
        """Keep mapping rows and discard malformed non-mapping values."""
        logger.info("Normalizing AP statistics response rows")  # WHY: log before response cleanup.
        normalized = [row for row in rows if isinstance(row, Mapping)]  # WHY: malformed rows cannot be scored.
        dropped_count = len(rows) - len(normalized)  # WHY: operators need to know if input rows were ignored.
        if dropped_count:  # WHY: discarded rows mean the payload contained unexpected shapes.
            logger.warning("Ignored %d malformed AP statistics rows", dropped_count)  # WHY: name data loss.
        logger.debug("Normalized AP statistics rows=%d dropped=%d", len(normalized), dropped_count)  # WHY: count.
        return normalized  # WHY: return only rows that model functions can read safely.
