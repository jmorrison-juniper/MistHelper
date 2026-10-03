"""Checks for list WebSocket request fields."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from src.websocket_streams.catalog.model import FieldKind, FieldSpec  # Catalog fields select each list rule.
from src.websocket_streams.intake.fields.error import StreamRequestError  # Failed checks use the request contract.
from src.websocket_streams.intake.identifiers.identity_rules import (
    IdentityIdentifierRules,
)  # MAC items use identity checks.
from src.websocket_streams.intake.identifiers.text_rules import (
    TextIdentifierRules,
)  # List items use safe identifier rules.


class ListFieldChecker:
    """Check bounded, unique list field values."""

    def check(self, spec: FieldSpec, raw: object) -> list[str]:
        """Return one checked list."""
        values = (
            [item.strip() for item in raw.split(",")] if isinstance(raw, str) else raw
        )  # Accept form or JSON lists.
        if not isinstance(values, list):  # Other JSON shapes are invalid.
            raise StreamRequestError("bad_request", "The field must be a list.", {"field": spec.name})
        checked = [
            self._item(spec, item) for item in values if isinstance(item, str) and item.strip()
        ]  # Check text items.
        valid_size = 1 <= len(checked) <= 48  # Bound the request and downstream SDK work.
        if not valid_size or len(set(checked)) != len(checked):  # Duplicate or oversized lists are invalid.
            raise StreamRequestError("bad_request", "The field must hold 1 to 48 unique values.", {"field": spec.name})
        return checked  # The SDK receives a JSON-safe list.

    def _item(self, spec: FieldSpec, raw: str) -> str:
        """Return one checked list item."""
        item = raw.strip()  # Remove form spacing around one item.
        if spec.kind is FieldKind.MAC_LIST and IdentityIdentifierRules.is_mac(
            item
        ):  # MAC lists normalize each address.
            return IdentityIdentifierRules.normalize_mac(item)  # Return compact lowercase text.
        if spec.kind is FieldKind.PORT_LIST and TextIdentifierRules.is_port(item):  # Port lists keep checked names.
            return item  # Preserve the Junos port name.
        if spec.kind is FieldKind.NAME_LIST and TextIdentifierRules.is_name(item):  # Name lists keep safe plain text.
            return item  # Preserve the checked name.
        raise StreamRequestError("bad_request", "The field list has an invalid value.", {"field": spec.name})
