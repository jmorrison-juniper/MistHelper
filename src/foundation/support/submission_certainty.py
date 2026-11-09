"""Classify response evidence for one destructive firmware submission."""

from __future__ import annotations  # Keep modern annotations available at runtime.


class SubmissionCertainty:  # Share one refusal rule across every firmware consumer.
    """Provide one refusal rule to every firmware submission consumer."""

    REFUSAL_STATUSES = frozenset({400, 401, 403, 404, 405, 409, 410, 413, 415, 422})  # Explicit client refusals.

    @classmethod
    def is_known_refusal(cls, raw_status: object) -> bool:  # Accept only the explicit client refusal set.
        """Return whether an integer status proves that the cloud refused the request."""
        return type(raw_status) is int and raw_status in cls.REFUSAL_STATUSES  # Reject booleans and unknown values.

    @classmethod
    def allows_settlement(cls, outcome_state: object, raw_status: object) -> bool:  # Protect rejected child locks.
        """Return whether an outcome state has enough evidence for lock settlement."""
        return outcome_state != "rejected" or cls.is_known_refusal(raw_status)  # Require proof for a refusal.
