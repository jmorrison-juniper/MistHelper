"""Checks for scalar WebSocket request fields."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured records write through standard repository handlers.

from src.websocket_streams.catalog.model import FieldKind, FieldSpec  # Catalog fields select each scalar rule.
from src.websocket_streams.intake.fields.error import StreamRequestError  # Failed checks use the request contract.
from src.websocket_streams.intake.identifiers.identity_rules import IdentityIdentifierRules  # UUID and MAC checks.
from src.websocket_streams.intake.identifiers.network_rules import (
    NetworkIdentifierRules,
)  # Network text has strict checks.
from src.websocket_streams.intake.identifiers.text_rules import (
    TextIdentifierRules,
)  # Plain identifiers have strict checks.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Reuse the shared bounded JSON boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep scalar logs bounded and content-free.


class ScalarFieldChecker:
    """Check integer, boolean, and text field values."""

    def check(self, spec: FieldSpec, raw: object) -> object:
        """Return one checked scalar value."""
        if spec.kind is FieldKind.INTEGER:  # Integer fields use numeric range rules.
            return self._integer(spec, raw)  # Return one checked integer.
        if spec.kind is FieldKind.BOOLEAN:  # Boolean fields accept JSON and form values.
            return self._boolean(spec, raw)  # Return one checked boolean.
        return self._text(spec, raw)  # Other scalar fields return checked text.

    def _text(self, spec: FieldSpec, raw: object) -> str:
        """Check one text field."""
        value = raw.strip() if isinstance(raw, str) else ""  # Refuse non-text values for text fields.
        valid = {
            FieldKind.UUID: IdentityIdentifierRules.is_uuid(value),
            FieldKind.HOST: NetworkIdentifierRules.is_host(value),
            FieldKind.IP: NetworkIdentifierRules.is_ip(value),
            FieldKind.PREFIX: NetworkIdentifierRules.is_prefix(value),
            FieldKind.PORT: TextIdentifierRules.is_port(value),
            FieldKind.NAME: TextIdentifierRules.is_name(value),
            FieldKind.FILTER: TextIdentifierRules.is_filter(value),
            FieldKind.MAC: IdentityIdentifierRules.is_mac(value),
            FieldKind.CHOICE: value in spec.choices,
            FieldKind.VLAN: value.isdecimal() and 1 <= int(value) <= 4094,
        }.get(
            spec.kind, False
        )  # Select the exact validation result for the field kind.
        if not valid:  # Any false result refuses the field.
            raise StreamRequestError("bad_request", "The field value is not valid.", {"field": spec.name})
        return (
            IdentityIdentifierRules.normalize_mac(value) if spec.kind is FieldKind.MAC else value
        )  # Normalize MAC text.

    def _integer(self, spec: FieldSpec, raw: object) -> int:
        """Check one whole number and its configured range."""
        text = (
            str(raw).strip() if isinstance(raw, (str, int)) and not isinstance(raw, bool) else ""
        )  # Normalize valid types.
        if not text.isdecimal():  # Whole positive numbers use decimal text only.
            raise StreamRequestError("bad_request", "The field must be a whole number.", {"field": spec.name})
        value = int(text)  # Convert only after the shape check.
        below = spec.minimum is not None and value < spec.minimum  # Check the optional lower bound.
        above = spec.maximum is not None and value > spec.maximum  # Check the optional upper bound.
        if below or above:  # Either range failure refuses the value.
            raise StreamRequestError("bad_request", "The field is outside the allowed range.", {"field": spec.name})
        return value  # The SDK receives an integer.

    def _boolean(self, spec: FieldSpec, raw: object) -> bool:
        """Check one JSON or form boolean."""
        if isinstance(raw, bool):  # Preserve a JSON boolean without text conversion.
            return raw  # The value is already safe.
        lowered = raw.strip().lower() if isinstance(raw, str) else ""  # Normalize form text.
        if lowered in {"true", "1", "yes", "on"}:  # These form values mean true.
            return True  # Return a JSON-safe boolean.
        if lowered in {"false", "0", "no", "off"}:  # These form values mean false.
            return False  # Return a JSON-safe boolean.
        logger.emit(logging.WARNING, "intake_field_refused", {"code": "bad_request", "detail": spec.kind.value})
        raise StreamRequestError("bad_request", "The field must be true or false.", {"field": spec.name})
