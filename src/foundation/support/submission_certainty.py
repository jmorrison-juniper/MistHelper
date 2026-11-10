"""Classify response evidence for one destructive firmware submission."""

from __future__ import annotations  # Keep modern annotations available at runtime.

import json
from collections.abc import Mapping  # Read stored JSON evidence without requiring a concrete dictionary.


class SubmissionCertainty:  # Share one refusal rule across every firmware consumer.
    """Provide one refusal rule to every firmware submission consumer."""

    REFUSAL_STATUSES = frozenset({400, 401, 403, 404})  # The documented upgrade endpoint refusal statuses.
    ACCEPTED_TARGET_FIELDS = frozenset(  # Target states that prove cloud processing started.
        {"download_requested", "downloaded", "downloading", "reboot_in_progress", "rebooted", "scheduled", "upgraded"}
    )

    @classmethod
    def is_known_refusal(
        cls, raw_status: object, evidence: Mapping[str, object] | None = None
    ) -> bool:  # Require documented refusal evidence without conflicts.
        """Return whether a documented status and its evidence prove that the cloud refused the request."""
        return (  # Keep unknown or conflicting responses fail-closed.
            type(raw_status) is int  # Reject booleans and non-integer statuses.
            and raw_status in cls.REFUSAL_STATUSES  # Accept only documented upgrade endpoint statuses.
            and not cls._has_conflicting_evidence(evidence)  # A job identity or accepted target overrides refusal.
        )

    @classmethod
    def allows_settlement(
        cls,
        outcome_state: object,
        raw_status: object,
        evidence: Mapping[str, object] | None = None,
    ) -> bool:  # Protect rejected child locks.
        """Return whether an outcome state has enough evidence for lock settlement."""
        return outcome_state != "rejected" or cls.is_known_refusal(raw_status, evidence)  # Require proof for refusal.

    @staticmethod
    def response_data_is_valid(response: object, data: Mapping[str, object] | None) -> bool:
        """Require a retained response object that agrees with available raw JSON."""
        if data is None or any(not isinstance(key, str) for key in data):
            return False
        raw_text: object = getattr(response, "raw_data", "")
        if raw_text in ("", None):
            return True
        if not isinstance(raw_text, str):
            return False
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            return False
        return isinstance(parsed, Mapping) and dict(parsed) == data

    @classmethod
    def _has_conflicting_evidence(cls, value: object) -> bool:  # Find any stored evidence of an existing job.
        """Return whether a response or stored child names a job or accepted target."""
        if isinstance(value, Mapping):  # Inspect JSON objects without trusting their type annotations.
            for key, nested in value.items():  # Check every nested response and child field.
                if key in cls.ACCEPTED_TARGET_FIELDS | {"id", "upgrade_id", "accepted_targets"} and bool(
                    nested
                ):  # A retained identity or accepted target conflicts with refusal.
                    return True  # Keep the submission uncertain.
                if cls._has_conflicting_evidence(nested):  # Inspect nested site and target results.
                    return True  # Keep the submission uncertain.
        elif isinstance(value, (list, tuple)):  # Inspect each nested site result.
            return any(cls._has_conflicting_evidence(item) for item in value)  # Stop at the first conflict.
        return False  # No job identity or accepted-target evidence exists.
