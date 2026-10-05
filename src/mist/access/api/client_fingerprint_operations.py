"""Organization-scoped client fingerprint API operations."""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class MistSession(Protocol):
    """Minimal authenticated session contract for raw Mist requests."""

    def mist_get(self, uri: str) -> object:
        """Send one authenticated GET request."""
        ...


def countOrgClientFingerprints(mist_session: MistSession, org_id: str) -> object:
    """Read client fingerprint counts through the organization endpoint."""
    path = f"/api/v1/orgs/{org_id}/insights/fingerprints/count"
    logger.info("Reading organization client fingerprint counts")
    response = mist_session.mist_get(path)
    logger.debug("Read organization client fingerprint counts")
    return response


def searchOrgClientFingerprints(mist_session: MistSession, org_id: str) -> object:
    """Read client fingerprint records through the organization endpoint."""
    path = f"/api/v1/orgs/{org_id}/insights/fingerprints/search"
    logger.info("Reading organization client fingerprint records")
    response = mist_session.mist_get(path)
    logger.debug("Read organization client fingerprint records")
    return response
