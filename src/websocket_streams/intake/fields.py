"""The check of one input value against one catalog field.

Why:
    Issue #3551. The server checks every value before it sends a request to
    Mist. A refused value raises one error with a code from the HTTP contract,
    so the blueprint turns each refusal into the same JSON answer.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # The portal uses standard logging for each action.
import re  # MAC normalization removes separators with a fixed pattern.
from collections.abc import Mapping  # Types the extra keys of a refusal.
from typing import ClassVar  # Marks the status table as one shared class value.

from src.websocket_streams.catalog.model import FieldKind, FieldSpec  # Field definitions guide each check.
from src.websocket_streams.intake.identifiers import IdentifierRules  # Shared identifier and text checks.

logger = logging.getLogger(__name__)  # Keep field check log records under this module name.


class StreamRequestError(Exception):
    """One refused request, with the code and the HTTP status of the contract.

    Attributes:
        code: The contract code, such as ``bad_request`` or ``limit_reached``.
        message: The plain reason for the operator.
        status: The HTTP status that the blueprint sends.
        extra: More keys for the JSON answer, such as ``field`` or ``live``.
    """

    STATUS_BY_CODE: ClassVar[dict[str, int]] = {
        "not_ready": 503,  # The portal holds no Mist session or no organization.
        "bad_request": 400,  # A field failed a check.
        "unknown_key": 404,  # The key names no catalog entry.
        "locked": 403,  # The flag of the safety class is off.
        "confirmation": 403,  # The typed device name does not match.
        "limit_reached": 429,  # The live sessions reached the limit.
        "not_found": 404,  # The session identifier names no session.
        "not_open": 409,  # The shell is not ready, or the session has ended.
        "session_live": 409,  # A delete request named a session that is still live.
    }

    def __init__(self, code: str, message: str, extra: Mapping[str, object] | None = None) -> None:
        """Build one refusal.

        Args:
            code: The contract code of the refusal.
            message: The plain reason for the operator.
            extra: More keys for the JSON answer, or None.
        """
        super().__init__(message)  # The exception text is the plain reason.
        self.code = code  # The page reads the code to pick its behavior.
        self.message = message  # The page shows this text.
        self.status = self.STATUS_BY_CODE.get(code, 400)  # An unknown code is a bad request.
        self.extra: dict[str, object] = dict(extra or {})  # A copy, so the caller cannot change it later.

    def to_payload(self) -> dict[str, object]:
        """Return the JSON answer of the refusal.

        Returns:
            The error text, the code, and each extra key.
        """
        payload: dict[str, object] = {"error": self.message, "code": self.code}  # The common error form.
        payload.update(self.extra)  # Such as the field name or the live session titles.
        return payload  # The blueprint sends this dictionary with the status.


class FieldValueChecker:
    """Check one raw value against one field specification."""

    def check(self, spec: FieldSpec, raw: object) -> object:
        """Return one checked JSON-safe field value.

        Args:
            spec: The catalog field specification.
            raw: The raw value from the request body.

        Returns:
            The checked value, or None for an empty optional value.

        Raises:
            StreamRequestError: The value failed the field rule.
        """
        logger.info("Checking WebSocket field %s", spec.name)  # Log before checking the field.
        if self._empty_optional(spec, raw):  # Empty optional values are omitted.
            logger.debug("Checked WebSocket field %s as empty optional", spec.name)  # Log the omission.
            return None  # The start checker drops this parameter.
        value = self._dispatch(spec, raw)  # Check the value by field kind.
        logger.debug("Checked WebSocket field %s with kind %s", spec.name, spec.kind.value)  # Log the checked kind.
        return value  # The value is safe to keep in the StartRequest.

    def _dispatch(self, spec: FieldSpec, raw: object) -> object:
        """Check a value by field kind.

        Args:
            spec: The catalog field specification.
            raw: The raw value from the request body.

        Returns:
            The checked value in JSON-safe form.
        """
        if spec.kind in {
            FieldKind.MAC_LIST,
            FieldKind.PORT_LIST,
            FieldKind.NAME_LIST,
        }:  # List kinds share list handling.
            return self._list_value(spec, raw)  # Return a list of checked strings.
        if spec.kind is FieldKind.INTEGER:  # Integer fields need range checks.
            return self._integer(spec, raw)  # Return an int in range.
        if spec.kind is FieldKind.BOOLEAN:  # Boolean fields accept bool and text.
            return self._boolean(spec, raw)  # Return a bool.
        return self._string_value(spec, raw)  # All other kinds return checked text.

    def _string_value(self, spec: FieldSpec, raw: object) -> str:
        """Check one string-like value.

        Args:
            spec: The catalog field specification.
            raw: The raw value from the request body.

        Returns:
            The checked text value.
        """
        value = raw.strip() if isinstance(raw, str) else ""  # Only text values are valid for these kinds.
        checks = {
            FieldKind.UUID: IdentifierRules.is_uuid(value),
            FieldKind.HOST: IdentifierRules.is_host(value),
            FieldKind.IP: IdentifierRules.is_ip(value),
            FieldKind.PREFIX: IdentifierRules.is_prefix(value),
            FieldKind.PORT: IdentifierRules.is_port(value),
            FieldKind.NAME: IdentifierRules.is_name(value),
            FieldKind.FILTER: IdentifierRules.is_filter(value),
            FieldKind.MAC: IdentifierRules.is_mac(value),
            FieldKind.CHOICE: value in spec.choices,
            FieldKind.VLAN: value.isdecimal() and 1 <= int(value) <= 4094,
        }  # Map each text kind to its validation result.
        if not checks.get(spec.kind, False):  # Any failed check refuses the request.
            raise self._error(spec, "The field value is not valid.")  # Give a plain refusal.
        return (
            self._normalize_mac(value) if spec.kind is FieldKind.MAC else value
        )  # MAC values use compact lowercase text.

    def _integer(self, spec: FieldSpec, raw: object) -> int:
        """Check one integer value.

        Args:
            spec: The catalog field specification.
            raw: The raw value from the request body.

        Returns:
            The checked integer value.
        """
        text = (
            str(raw).strip() if isinstance(raw, (str, int)) and not isinstance(raw, bool) else ""
        )  # Accept JSON numbers and number text.
        if not text.isdecimal():  # Only whole positive numbers are valid.
            raise self._error(spec, "The field must be a whole number.")  # Refuse non-number values.
        value = int(text)  # Convert after the decimal check.
        if (spec.minimum is not None and value < spec.minimum) or (
            spec.maximum is not None and value > spec.maximum
        ):  # Enforce the configured range.
            raise self._error(spec, "The field is outside the allowed range.")  # Refuse values outside range.
        return value  # The SDK expects an int.

    def _boolean(self, spec: FieldSpec, raw: object) -> bool:
        """Check one boolean value.

        Args:
            spec: The catalog field specification.
            raw: The raw value from the request body.

        Returns:
            The checked boolean value.
        """
        if isinstance(raw, bool):  # JSON booleans are valid.
            return raw  # Keep the boolean value.
        lowered = raw.strip().lower() if isinstance(raw, str) else ""  # Text booleans are accepted for form posts.
        if lowered in {"true", "1", "yes", "on"}:  # These values mean true.
            return True  # Return JSON-safe true.
        if lowered in {"false", "0", "no", "off"}:  # These values mean false.
            return False  # Return JSON-safe false.
        raise self._error(spec, "The field must be true or false.")  # Refuse other values.

    def _list_value(self, spec: FieldSpec, raw: object) -> list[str]:
        """Check one list field value.

        Args:
            spec: The catalog field specification.
            raw: The raw value from the request body.

        Returns:
            The checked list of text values.
        """
        values = (
            [item.strip() for item in raw.split(",")] if isinstance(raw, str) else raw
        )  # Accept comma text or a JSON list.
        if not isinstance(values, list):  # Other JSON shapes are invalid.
            raise self._error(spec, "The field must be a list.")  # Refuse a non-list value.
        checked = [
            self._list_item(spec, item) for item in values if isinstance(item, str) and item.strip()
        ]  # Check each non-empty item.
        if not 1 <= len(checked) <= 48 or len(set(checked)) != len(checked):  # Enforce size and uniqueness.
            raise self._error(spec, "The field must hold 1 to 48 unique values.")  # Refuse bad list size or duplicates.
        return checked  # The SDK receives a JSON-safe list.

    def _list_item(self, spec: FieldSpec, raw: str) -> str:
        """Check one list item.

        Args:
            spec: The catalog field specification.
            raw: One raw list item.

        Returns:
            The checked text item.
        """
        item = raw.strip()  # Normalize spaces around one item.
        if spec.kind is FieldKind.MAC_LIST and IdentifierRules.is_mac(item):  # MAC lists normalize each MAC.
            return self._normalize_mac(item)  # Return compact lowercase text.
        if spec.kind is FieldKind.PORT_LIST and IdentifierRules.is_port(item):  # Port lists keep the port name.
            return item  # Return the checked port name.
        if spec.kind is FieldKind.NAME_LIST and IdentifierRules.is_name(item):  # Name lists keep the name text.
            return item  # Return the checked name.
        raise self._error(spec, "The field list has an invalid value.")  # Refuse a bad item.

    @staticmethod
    def _empty_optional(spec: FieldSpec, raw: object) -> bool:
        """Return whether an optional value is empty.

        Args:
            spec: The catalog field specification.
            raw: The raw value from the request body.

        Returns:
            True when the optional field is empty.
        """
        return not spec.required and (raw is None or raw == "" or raw == [])  # Empty optional values are absent.

    @staticmethod
    def _normalize_mac(value: str) -> str:
        """Return a compact lowercase MAC address.

        Args:
            value: The checked MAC address.

        Returns:
            The 12-digit lowercase MAC address.
        """
        return re.sub(r"[:-]", "", value).lower()  # The SDK accepts compact lowercase MAC text.

    @staticmethod
    def _error(spec: FieldSpec, message: str) -> StreamRequestError:
        """Build a field refusal.

        Args:
            spec: The catalog field specification.
            message: The plain refusal reason.

        Returns:
            One request error.
        """
        return StreamRequestError(
            "bad_request", message, {"field": spec.name}
        )  # The field key lets the page mark the input.
