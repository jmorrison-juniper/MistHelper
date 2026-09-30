"""Prompt and lookback helpers for alert digest operations."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

import logging  # Record prompt parsing decisions for destructive safety.
import os  # Read ALERT_DIGEST_HOURS from the process environment.
import sys  # Read --dry-run from the process arguments for menu 281.

logger = logging.getLogger(__name__)  # Keep log records tied to this module.

DEFAULT_LOOKBACK_HOURS = 24  # Default to one day for a shift handover.
LOOKBACK_ENV_VAR = "ALERT_DIGEST_HOURS"  # Name the shared override for both menus.


class AlertDigestPromptResolver:
    """Resolve lookback values and destructive acknowledgement confirmation text."""

    @staticmethod
    def resolve_lookback_hours(env: dict[str, str] | None = None) -> int:
        """Return the validated alert digest lookback window."""
        logger.info("Resolving the alert digest lookback window")  # Log before reading the environment.
        source = os.environ if env is None else env  # Use the real process env unless a test injects one.
        raw_value = source.get(LOOKBACK_ENV_VAR, "").strip()  # Read and trim the optional override.
        if not raw_value:  # No override means the default applies.
            logger.debug("Using the default alert digest lookback of %d hours", DEFAULT_LOOKBACK_HOURS)  # Log result.
            return DEFAULT_LOOKBACK_HOURS  # Return the default window.
        try:
            hours = int(raw_value)  # Parse whole hours only.
        except ValueError as error:
            raise ValueError(f"{LOOKBACK_ENV_VAR} must be a positive integer hour count.") from error  # Fail closed.
        if hours <= 0:  # Zero and negative windows do not make operational sense.
            raise ValueError(f"{LOOKBACK_ENV_VAR} must be a positive integer hour count.")  # Fail closed.
        logger.debug("Using the alert digest lookback override of %d hours", hours)  # Log result.
        return hours  # Return the validated override.

    @staticmethod
    def confirmation_matches(text: str, expected_count: int) -> bool:
        """Return true when the confirmation exactly matches ACK and the count."""
        logger.info("Checking alert acknowledgement confirmation text")  # Log before parsing destructive input.
        parts = text.strip().split()  # Split the answer into word and count.
        if len(parts) != 2:  # The operator must type exactly two tokens.
            logger.debug("The acknowledgement confirmation has %d tokens", len(parts))  # Log reject reason.
            return False  # Reject malformed input.
        if parts[0] != "ACK":  # The command word is case-sensitive by contract.
            logger.debug("The acknowledgement confirmation word did not match")  # Log reject reason.
            return False  # Reject wrong command word.
        try:
            count = int(parts[1])  # Parse the displayed alarm count.
        except ValueError:
            logger.debug("The acknowledgement confirmation count was not an integer")  # Log reject reason.
            return False  # Reject a malformed count.
        matched = count == expected_count  # Require the exact displayed count.
        logger.debug("The acknowledgement confirmation matched=%s", matched)  # Log the decision.
        return matched  # Return the final safety decision.

    @staticmethod
    def dry_run_requested(arguments: list[str] | None = None) -> bool:
        """Return true when the operator requested acknowledgement dry run."""
        logger.info("Checking alert acknowledgement dry-run arguments")  # Log before reading process arguments.
        source = sys.argv[1:] if arguments is None else arguments  # Use process arguments unless a test injects them.
        requested = "--dry-run" in source  # Honor the shared destructive preview flag.
        logger.debug("Alert acknowledgement dry-run requested=%s", requested)  # Log the decision.
        return requested  # Return the dry-run mode for menu 281.
