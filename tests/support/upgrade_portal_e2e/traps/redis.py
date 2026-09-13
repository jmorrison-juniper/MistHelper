"""Fail every Redis connector call from an isolated E2E application."""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record the blocked connector call without a connection value.
from typing import Any  # Connector calls can carry different arguments.

logger = logging.getLogger(__name__)  # Keep trap records tied to this module.

FAILURE_MESSAGE = "E2E isolation failed: a Redis connector was called."  # Keep the contract text exact.


class RedisConnectorTrap:  # Block the lock store boundary during E2E work.
    """Record and refuse every Redis connector call."""

    def __init__(self) -> None:  # Start one empty safe call record.
        """Create an empty call record."""
        self.calls: list[str] = []  # Keep only safe call names.

    def __call__(self, *arguments: Any, **options: Any) -> Any:  # Block one connector construction.
        """Record and refuse one connector call."""
        del arguments, options  # Never retain a connection string or a credential.
        logger.info("Block a Redis connector call in the E2E application")  # Record the blocked action.
        self.calls.append("connect")  # Keep a safe stable call name.
        logger.debug("The Redis trap recorded %s call(s)", len(self.calls))  # Report a safe count.
        raise AssertionError(FAILURE_MESSAGE)  # Fail before any network attempt.

    def assert_not_called(self) -> None:  # Verify that no connector call crossed the trap.
        """Fail when any Redis connector call was recorded."""
        logger.info("Check the Redis connector trap")  # Record the isolation assertion.
        if self.calls:  # A call means the application crossed the isolation boundary.
            raise AssertionError(FAILURE_MESSAGE)  # Keep the contract text exact.
        logger.debug("The Redis connector trap recorded zero calls")  # Confirm the safe result.
