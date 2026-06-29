"""Deferred address write-back stub (1003-site-address-audit).

This release is READ-ONLY: it audits and reports address discrepancies but never
writes back to a Mist site record. ``AddressCorrector`` documents the future
write-back surface (OQ-003) and intentionally raises ``NotImplementedError`` on
every method. It is NOT imported into the menu and performs no Mist writes.
"""

from __future__ import annotations  # PEP 604 union syntax on Python 3.13.

import logging  # Action logging before/after every operation (project NON-NEGOTIABLE).
from typing import Any  # Loose typing for the future address payload.


class AddressCorrector:
    """Inert placeholder for the deferred site-address write-back feature."""

    def apply_correction(self, site_id: str, address: dict[str, Any]) -> None:
        """Future: push a corrected address to a Mist site. Disabled in this release."""
        logging.info("apply_correction invoked for site %s (feature disabled)", site_id)  # Action-log attempt.
        raise NotImplementedError("Address write-back is not enabled in this release.")  # Deferred surface.
