"""Fail every portal record file access from an isolated E2E application."""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record the blocked file call without a path value.
from typing import Any  # File calls can carry different arguments.

logger = logging.getLogger(__name__)  # Keep trap records tied to this module.

FAILURE_MESSAGE = "E2E isolation failed: a portal record file was opened."  # Keep the contract text exact.


class PortalFileTrap:  # Block the portal record file boundary during E2E work.
    """Record and refuse every portal record file open."""

    def __init__(self) -> None:  # Start one empty safe call record.
        """Create an empty call record."""
        self.calls: list[str] = []  # Keep only safe call names.

    def __call__(self, *arguments: Any, **options: Any) -> Any:  # Block one portal file open.
        """Record and refuse one portal record file open."""
        del arguments, options  # Never retain a production path or a file value.
        logger.info("Block a portal record file open in the E2E application")  # Record the blocked action.
        self.calls.append("open")  # Keep a safe stable call name.
        logger.debug("The portal file trap recorded %s call(s)", len(self.calls))  # Report a safe count.
        raise AssertionError(FAILURE_MESSAGE)  # Fail before the file system operation.

    def open(self, *arguments: Any, **options: Any) -> Any:  # Match a file-style open method.
        """Route a file-style open call through the same trap."""
        logger.info("Route one portal file open through the E2E trap")  # Record the adapter action.
        result = self(*arguments, **options)  # Record and fail with the contract message.
        logger.debug("The portal file trap returned unexpectedly")  # This line cannot run after the failure.
        return result  # Keep the callable shape explicit for type checking.

    def assert_not_called(self) -> None:  # Verify that no file call crossed the trap.
        """Fail when any portal record file call was recorded."""
        logger.info("Check the portal record file trap")  # Record the isolation assertion.
        if self.calls:  # A call means the application crossed the isolation boundary.
            raise AssertionError(FAILURE_MESSAGE)  # Keep the contract text exact.
        logger.debug("The portal record file trap recorded zero calls")  # Confirm the safe result.
