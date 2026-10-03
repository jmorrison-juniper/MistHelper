"""The coordinator for one checked WebSocket request field."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured records write through standard repository handlers.

from src.websocket_streams.catalog.model import FieldKind, FieldSpec  # Field kinds select scalar or list checks.
from src.websocket_streams.intake.fields.list_checker import ListFieldChecker  # List fields use bounded item checks.
from src.websocket_streams.intake.fields.scalar_checker import ScalarFieldChecker  # Scalar fields use typed checks.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Reuse the shared bounded JSON boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep field logs bounded and content-free.
LIST_KINDS = frozenset({FieldKind.MAC_LIST, FieldKind.PORT_LIST, FieldKind.NAME_LIST})  # Share the list dispatch set.


class FieldValueChecker:
    """Check one raw value against one field specification."""

    def __init__(self) -> None:
        """Build the typed field collaborators."""
        self._scalars = ScalarFieldChecker()  # Scalar behavior stays in its named leaf class.
        self._lists = ListFieldChecker()  # List behavior stays in its named leaf class.

    def check(self, spec: FieldSpec, raw: object) -> object:
        """Return one checked JSON-safe value."""
        logger.emit(
            logging.INFO, "intake_field_check_started", {"detail": spec.kind.value}
        )  # Log safe field type only.
        if not spec.required and (raw is None or raw == "" or raw == []):  # Empty optional values remain absent.
            logger.emit(logging.DEBUG, "intake_field_check_finished", {"status": "empty"})  # Record the safe outcome.
            return None  # The request checker omits this parameter.
        value = self._lists.check(spec, raw) if spec.kind in LIST_KINDS else self._scalars.check(spec, raw)  # Dispatch.
        logger.emit(logging.DEBUG, "intake_field_check_finished", {"status": "valid"})  # Record no raw content.
        return value  # The checked value can enter a start request.
