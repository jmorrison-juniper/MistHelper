"""Validate HTTP status values before an exporter reads an SDK payload."""

from __future__ import annotations

import logging
from typing import Any

_HTTP_OK = 200
_HTTP_ERROR_MIN = 400
_HTTP_SUCCESS_MAX = _HTTP_ERROR_MIN - 100
logger = logging.getLogger(__name__)


def http_failure(response: Any, operation: str) -> bool:
    """Return whether an SDK response does not prove a successful request."""
    status = getattr(response, "status_code", None)
    if not isinstance(status, int):
        logger.debug("%s returned no integer status, so the normal path continues", operation)
        return False
    if _HTTP_OK <= status < _HTTP_SUCCESS_MAX:
        logger.debug("%s returned HTTP %d, which is a success", operation, status)
        return False
    url = getattr(response, "url", None) or "the requested path"
    logger.error("%s returned HTTP %d from %s", operation, status, url)
    logger.info("! Error fetching %s: HTTP %s from %s", operation, status, url)
    return True
