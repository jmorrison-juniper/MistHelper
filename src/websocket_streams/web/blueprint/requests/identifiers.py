"""Validate picker identifiers at the route boundary."""

from __future__ import annotations  # Keep annotations lazy.

from src.websocket_streams.intake.fields.error import StreamRequestError  # Return the shared error contract.
from src.websocket_streams.intake.identifiers.identity_rules import IdentityIdentifierRules  # Use shared UUID rules.


class IdentifierRequest:
    """Validate required and optional UUID request values."""

    @staticmethod
    def require_uuid(value: object, field: str) -> None:
        """Raise when a required identifier is invalid."""
        if not IdentityIdentifierRules.is_uuid(value):  # Apply the shared fixed UUID rule.
            raise StreamRequestError(
                "bad_request", "The identifier is not valid.", {"field": field}
            )  # Return the established field error.

    @classmethod
    def require_optional_uuid(cls, value: object, field: str) -> None:
        """Raise when a supplied optional identifier is invalid."""
        if value is not None:  # An omitted filter keeps the organization-wide picker.
            cls.require_uuid(value, field)  # Apply the same UUID rule to supplied text.
