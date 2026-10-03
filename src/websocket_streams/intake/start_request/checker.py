"""The coordinator and builders for checked WebSocket start requests."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured records write through standard repository handlers.
from collections.abc import Mapping  # Checked targets and labels use mapping interfaces.

from src.websocket_streams.catalog.model import (
    ChannelDefinition,
    Safety,
    UtilityDefinition,
)  # Definitions drive checks.
from src.websocket_streams.catalog.registry.stream_catalog import StreamCatalog  # Resolve catalog entries.
from src.websocket_streams.intake.fields.error import StreamRequestError  # Refusals use the HTTP contract.
from src.websocket_streams.intake.start_request.models import (
    DeviceDirectory,
    DeviceFacts,
    StartRequest,
)  # Stable records.
from src.websocket_streams.intake.start_request.targets import TargetValidator  # Target behavior owns UUID limits.
from src.websocket_streams.intake.start_request.validation import RequestValidator  # Body and parameter behavior.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Reuse the shared bounded JSON boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep request logs bounded and content-free.


class StartRequestChecker:
    """Check one raw body and build one immutable start request."""

    def __init__(self, catalog: StreamCatalog, directory: DeviceDirectory, org_id: str) -> None:
        """Build the named request collaborators."""
        validator = RequestValidator(catalog)  # Body, catalog, lock, and parameter checks share the catalog.
        targets = TargetValidator(org_id)  # Target checks inject the trusted organization.
        self._validator = validator  # The top-level check resolves definitions.
        self._builder = CheckedRequestBuilder(validator, targets, directory)  # The builder completes checked requests.

    def check(self, body: object) -> StartRequest:
        """Return one checked start request."""
        logger.emit(logging.INFO, "intake_request_check_started", {"action": "validate"})  # Log no request content.
        mapping = self._validator.body(body)  # Validate the top-level JSON shape.
        definition = self._validator.definition(mapping)  # Resolve the catalog entry.
        self._validator.check_lock(definition)  # Refuse disabled change and shell actions first.
        request = self._builder.build(mapping, definition)  # Check targets, parameters, device, and title.
        logger.emit(logging.DEBUG, "intake_request_check_finished", {"status": "valid"})  # Log no key or identifiers.
        return request  # The session manager receives checked data only.


class CheckedRequestBuilder:
    """Build a request after body, catalog, and lock checks."""

    def __init__(self, validator: RequestValidator, targets: TargetValidator, directory: DeviceDirectory) -> None:
        """Store the request collaborators."""
        self._validator = validator  # Parameter behavior remains in its named validator.
        self._targets = targets  # Target behavior remains in its named validator.
        self._directory = directory  # Device facts come from the picker cache.
        self._titles = RequestTitleBuilder()  # Title behavior remains isolated and bounded.

    def build(self, body: Mapping[str, object], definition: ChannelDefinition | UtilityDefinition) -> StartRequest:
        """Return one complete checked request."""
        targets, parameters, device, confirmation = self._values(body, definition)  # Check all request values.
        title = self._titles.build(definition.name, targets, body.get("labels"), device)  # Build safe session text.
        return StartRequest(
            str(body["kind"]), definition, targets, parameters, title, confirmation, device.name if device else None
        )  # Freeze the checked request data.

    def _values(
        self, body: Mapping[str, object], definition: ChannelDefinition | UtilityDefinition
    ) -> tuple[dict[str, tuple[str, ...]], dict[str, object], DeviceFacts | None, str | None]:
        """Return all checked request values."""
        targets = self._targets.check(definition, body.get("targets", {}))  # Check identifier targets.
        parameters = self._validator.parameters.check(definition, body.get("parameters", {}))  # Check utility fields.
        device = self._device(definition, targets)  # Confirm the selected device and family.
        confirmation = self._confirmation(definition, body.get("confirmation"), device)  # Check typed name.
        return targets, parameters, device, confirmation  # Keep build operations bounded.

    def _device(
        self, definition: ChannelDefinition | UtilityDefinition, targets: Mapping[str, tuple[str, ...]]
    ) -> DeviceFacts | None:
        """Return checked device facts when required."""
        if (
            not isinstance(definition, UtilityDefinition) or "device_id" not in targets
        ):  # Channels and edges skip lookup.
            return None  # No device facts are required.
        device = self._directory.describe_device(targets["site_id"][0], targets["device_id"][0])  # Use checked UUIDs.
        if device is None:  # The site does not contain the selected device.
            raise StreamRequestError("bad_request", "The device is unknown.", {"field": "device_id"})
        if device.family != definition.family:  # Utilities must match the device family.
            raise StreamRequestError(
                "bad_request", "The device family cannot run this utility.", {"field": "device_id"}
            )
        return device  # Confirmation and title behavior use the checked facts.

    @staticmethod
    def _confirmation(
        definition: ChannelDefinition | UtilityDefinition, raw: object, device: DeviceFacts | None
    ) -> str | None:
        """Return the checked typed confirmation when required."""
        needs_confirmation = isinstance(definition, UtilityDefinition) and definition.safety in {
            Safety.CHANGE,
            Safety.SHELL,
        }
        if not needs_confirmation:  # Read-only entries do not store confirmation text.
            return None  # No confirmation is required.
        typed = raw.strip() if isinstance(raw, str) else ""  # Normalize operator text.
        if device is None or typed != device.name:  # The text must match the current Mist device name.
            raise StreamRequestError("confirmation", "The confirmation does not match the device name.")
        return typed  # Store only the checked device name.


class RequestTitleBuilder:
    """Build bounded session titles from safe labels."""

    def build(
        self, name: str, targets: Mapping[str, tuple[str, ...]], raw_labels: object, device: DeviceFacts | None
    ) -> str:
        """Return one bounded session title."""
        labels = self._labels(raw_labels)  # Remove unsafe and oversized label text.
        values = [value for key, group in targets.items() if key != "org_id" for value in group]  # Keep target order.
        parts = [labels.get(value, value[:8]) for value in values]  # Use labels or short identifier prefixes.
        if device is not None and device.name not in parts:  # Device utilities should show the device name.
            parts.append(device.name)  # Add the trusted Mist name.
        shown = parts[:3] + ([f"(+{len(parts) - 3})"] if len(parts) > 3 else [])  # Bound visible title parts.
        return f"{name} - {', '.join(shown)}" if shown else name  # Organization entries need no suffix.

    def _labels(self, raw: object) -> dict[str, str]:
        """Return safe labels by identifier."""
        labels = raw if isinstance(raw, Mapping) else {}  # Missing labels become an empty mapping.
        cleaned = {str(key): self._clean(value) for key, value in labels.items()}  # Clean each optional label.
        return {key: value for key, value in cleaned.items() if value}  # Keep printable labels only.

    @staticmethod
    def _clean(value: object) -> str:
        """Return one printable label of 64 characters or fewer."""
        text = value if isinstance(value, str) else ""  # Labels must be text.
        printable = "".join(char for char in text if char.isprintable()).strip()  # Remove control characters.
        return printable[:64]  # Keep session titles bounded.
