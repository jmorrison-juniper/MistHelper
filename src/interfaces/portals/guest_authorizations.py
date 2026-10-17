"""Prepare private guest records for read-only review without cloud access.

This projection provides no route, session, storage, or SDK operation.
Callers must enforce organization, site, and WLAN access before supplying data.
Missing authorization and expiration values remain unknown.
Guest write workflows remain blocked pending license, access, and API approvals.
"""

import logging
import re
from collections.abc import Mapping
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class GuestAuthorizationReadModel:
    """Expose only masked identifiers and explicit authorization observations."""

    @classmethod
    def project(cls, record: object) -> dict[str, object]:
        """Validate one record and exclude all fields outside the review contract."""
        logger.info("Preparing a masked guest authorization record")
        if not isinstance(record, Mapping):
            logger.error("Invalid guest authorization record")
            raise ValueError("Invalid guest authorization record")
        result: dict[str, object] = {
            "masked_mac": cls._masked_mac(record.get("mac")),
            "authorized": cls._authorized(record.get("authorized")),
            "expires_at": cls._expiration(record.get("authorized_expiring_time")),
        }
        logger.debug("Prepared 1 masked guest authorization record")
        return result

    @staticmethod
    def _masked_mac(value: object) -> str:
        """Accept complete MAC formats and disclose only the last two octets."""
        pattern = r"(?:[0-9a-fA-F]{12}|[0-9a-fA-F]{2}([:-])(?:[0-9a-fA-F]{2}\1){4}[0-9a-fA-F]{2})"
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            logger.error("Invalid guest authorization MAC address")
            raise ValueError("Invalid guest authorization MAC address")
        normalized = value.replace(":", "").replace("-", "").lower()
        return f"xx:xx:xx:xx:{normalized[8:10]}:{normalized[10:12]}"

    @staticmethod
    def _authorized(value: object) -> bool | None:
        """Preserve a missing observation without treating it as authorization."""
        if value is None or isinstance(value, bool):
            return value
        logger.error("Invalid guest authorization state")
        raise ValueError("Invalid guest authorization state")

    @staticmethod
    def _expiration(value: object) -> str | None:
        """Convert a reported epoch time to UTC without inventing absent data."""
        if value is None:
            return None
        try:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ValueError("Invalid timestamp")
            return datetime.fromtimestamp(value, UTC).isoformat()
        except (ValueError, OverflowError, OSError):
            logger.error("Invalid guest authorization expiration time")
            raise ValueError("Invalid guest authorization expiration time") from None
