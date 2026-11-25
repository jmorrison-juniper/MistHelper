"""Bind one run to the shared request ledger and hide the SDK error text.

Why:
    The shared request ledger rejects a site request when it holds no organization,
    and the CLI session never sets one. The batch worker threads cannot read a
    context variable, so the run sets the organization on the ledger itself and
    restores it afterward. Issue #4921 tracks the ledger defect, and this class goes away when it is fixed.
    The Mist SDK also prints its own error lines for a
    refused call, and a refusal such as the MSP list is an expected answer here.
    One mute keeps those lines out of the operator console for that one call.
"""

from __future__ import annotations

import logging  # Record each bind, each restore, and each mute for the operator trace.
from typing import Any  # The SDK session and its adapter have no public type.

from mistapi.__api_response import console as sdk_console  # The SDK prints its own error lines with this object.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.

MIST_URL = "https://api.mist.com/"  # Any HTTPS address works, because the adapter is mounted by scheme.


class AdmissionBinding:
    """Set the organization of the shared request ledger for one block of work."""

    def __init__(self, apisession: Any, org_id: str) -> None:
        """Store the session and the organization to bind.

        Args:
            apisession: The Mist API session of the CLI.
            org_id: The organization that the block of work reads.
        """
        self._apisession = apisession  # The session holds the mounted admission adapter.
        self._org_id = org_id  # The ledger counts the site requests of this organization.
        self._ledger: Any | None = None  # The ledger found on enter, or None when the session has none.
        self._previous: str | None = None  # The ledger organization before the bind, restored on exit.

    def __enter__(self) -> AdmissionBinding:
        """Find the ledger and set its organization.

        Returns:
            This binding, so a caller can read it in a ``with`` block.
        """
        logger.info("Binding the shared request ledger to the organization of the run")  # Log before the change.
        self._ledger = self._find_ledger()  # A session without Redis admission has no ledger.
        if self._ledger is not None:  # Only a mounted ledger needs the organization.
            self._previous = self._ledger.org_id  # Remember the earlier value for the restore.
            self._ledger.org_id = self._org_id  # A site request now has an organization to count.
        logger.debug("Request ledger bound=%s", self._ledger is not None)  # Log the result without the identifier.
        return self  # Let the caller keep the binding.

    def __exit__(self, *_exception: object) -> None:
        """Restore the earlier ledger organization, whatever ended the block."""
        if self._ledger is not None:  # Nothing to restore when no ledger was bound.
            self._ledger.org_id = self._previous  # The ledger returns to its state before the run.
        logger.debug("Request ledger restored=%s", self._ledger is not None)  # Log the result.

    def _find_ledger(self) -> Any | None:
        """Return the ledger of the mounted admission adapter, or None.

        Returns:
            The ledger object, or None when the session has no admission adapter.
        """
        inner = getattr(self._apisession, "_session", None)  # The SDK keeps its HTTP session in this attribute.
        if inner is None:  # A session with no HTTP session cannot hold an adapter.
            return None  # No ledger to bind.
        try:  # The adapter lookup raises for a scheme that has no mount.
            adapter = inner.get_adapter(MIST_URL)  # The CLI mounts the admission adapter on this scheme.
        except (AttributeError, ValueError):  # A test double or an unusual session has no adapter table.
            return None  # No ledger to bind.
        ledger = getattr(adapter, "ledger", None)  # Only the admission adapter carries a ledger.
        return ledger if hasattr(ledger, "org_id") else None  # Ignore an object that cannot hold an organization.


class SdkErrorMute(logging.Filter):
    """Hide the error text of the Mist SDK inside one block of work."""

    def __init__(self) -> None:
        """Start with no saved console level."""
        super().__init__()  # The base filter takes no name, so it matches every record.
        self._console_level = 0  # The SDK console level before the mute, restored on exit.

    def __enter__(self) -> SdkErrorMute:
        """Turn off the SDK console print and drop the SDK error records.

        Returns:
            This mute, so a caller can read it in a ``with`` block.
        """
        logger.info("Muting the error lines of the Mist SDK")  # Log before the change.
        self._console_level = sdk_console.level  # Keep the level so the exit can restore it.
        sdk_console.level = 0  # Level 0 turns off the direct print of the SDK console.
        logging.getLogger("mistapi").addFilter(self)  # The filter drops the error records of the SDK logger.
        return self  # Let the caller keep the mute.

    def __exit__(self, *_exception: object) -> None:
        """Restore the SDK console level and remove the filter, whatever ended the block."""
        logging.getLogger("mistapi").removeFilter(self)  # Error records flow again.
        sdk_console.level = self._console_level  # The console prints again at its earlier level.
        logger.debug("Restored the error lines of the Mist SDK")  # Log the result.

    def filter(self, record: logging.LogRecord) -> bool:
        """Drop a record at level error or higher.

        Args:
            record: The SDK log record.

        Returns:
            True for a record below level error, False for a record at level error or higher.
        """
        return record.levelno < logging.ERROR  # A warning or a debug line is not an error text.
