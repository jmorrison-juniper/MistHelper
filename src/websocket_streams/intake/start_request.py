"""The checked form of one start request.

Why:
    Issue #3551. The server builds a StartRequest only after every check
    passes. The runners and the session manager accept only this checked form,
    so no raw path and no unchecked value can reach Mist.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # The portal uses standard logging for each action.
from collections.abc import Mapping  # Types the checked targets and parameters.
from dataclasses import dataclass  # Each record is a frozen dataclass.
from typing import Protocol  # The device lookup is a structural interface.

from src.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldSpec,
    Safety,
    UtilityDefinition,
)  # The catalog entry types.
from src.websocket_streams.catalog.registry import StreamCatalog  # The checker reads entries and flags.
from src.websocket_streams.intake.fields import FieldValueChecker, StreamRequestError  # Field checks and refusal type.
from src.websocket_streams.intake.identifiers import IdentifierRules  # Identifier shape checks.

logger = logging.getLogger(__name__)  # Keep start request log records under this module name.


@dataclass(frozen=True, slots=True)
class StartRequest:
    """One start request after every check passed.

    Attributes:
        kind: "channel", "utility", or "shell".
        definition: The catalog entry of the request.
        targets: Each identifier name with its checked values. Only the repeatable identifier holds more than one.
        parameters: Each parameter value in its checked, JSON-safe form.
        title: The catalog name with the target labels, for the session card.
        confirmation: The typed device name for a change or shell request, or None.
        device_name: The device name that Mist reported, or None.
    """

    kind: str  # The runner kind.
    definition: ChannelDefinition | UtilityDefinition  # The catalog entry that the runner uses.
    targets: Mapping[str, tuple[str, ...]]  # Such as {"site_id": ("<uuid>",)}.
    parameters: Mapping[str, object]  # Such as {"host": "8.8.8.8", "count": 5}.
    title: str  # Such as "Device statistics - HQ".
    confirmation: str | None = None  # Only the change and shell classes need it.
    device_name: str | None = None  # The audit log names the device with this value.

    @property
    def key(self) -> str:
        """Return the catalog key of the request."""
        return self.definition.key  # The key lives on the catalog entry.

    def target(self, name: str) -> str:
        """Return the first value of one identifier.

        Args:
            name: The identifier name, such as ``site_id``.

        Returns:
            The first checked value, or an empty text when the request holds none.
        """
        values = self.targets.get(name, ())  # An absent identifier gives no values.
        return values[0] if values else ""  # The caller treats an empty text as absent.


@dataclass(frozen=True, slots=True)
class DeviceFacts:
    """The facts about one device that the start checks need.

    Attributes:
        name: The device name in Mist. The typed confirmation must match it.
        family: The utility family: ap, ex, srx, ssr, or None for another type.
    """

    name: str  # The name that the operator types to confirm.
    family: str | None  # None when the portal offers no utility for the device.


class DeviceDirectory(Protocol):
    """The lookup that gives the facts about one device."""

    def describe_device(self, site_id: str, device_id: str) -> DeviceFacts | None:
        """Return the facts about one device, or None when Mist has no such device.

        Args:
            site_id: The site of the device.
            device_id: The device identifier.
        """


class StartRequestChecker:
    """Check one start request body and build a StartRequest."""

    _TOP_KEYS = {"kind", "key", "targets", "parameters", "confirmation", "labels"}  # Only these keys are accepted.

    def __init__(self, catalog: StreamCatalog, directory: DeviceDirectory, org_id: str) -> None:
        """Build one start request checker.

        Args:
            catalog: The joined stream catalog.
            directory: The device lookup service.
            org_id: The organization identifier from portal settings.
        """
        logger.info("Building the WebSocket start request checker")  # Log before storing dependencies.
        self._catalog = catalog  # Keep the catalog for lookups and locks.
        self._directory = directory  # Keep the device lookup for utility checks.
        self._org_id = org_id  # The request body never provides the organization.
        self._fields = FieldValueChecker()  # Reuse one field checker.
        logger.debug("Built the WebSocket start request checker")  # Log that the checker is ready.

    def check(self, body: object) -> StartRequest:
        """Check a raw start request body.

        Args:
            body: The JSON body from the route.

        Returns:
            One checked start request.

        Raises:
            StreamRequestError: The request failed a contract check.
        """
        logger.info("Checking a WebSocket start request")  # Log before request validation.
        mapping = self._body(body)  # Validate the top-level shape.
        definition = self._definition(mapping)  # Resolve the catalog entry first.
        self._check_lock(definition)  # Refuse locked change and shell entries before device lookup.
        targets = self._targets(definition, mapping.get("targets", {}))  # Check each identifier target.
        parameters = self._parameters(definition, mapping.get("parameters", {}))  # Check each utility parameter.
        device = self._device(definition, targets)  # Check device family when the entry needs a device.
        confirmation = self._confirmation(
            definition, mapping.get("confirmation"), device
        )  # Check typed device name when needed.
        title = self._title(
            definition.name, targets, self._labels(mapping.get("labels")), device
        )  # Build the session title.
        request = StartRequest(
            str(mapping["kind"]), definition, targets, parameters, title, confirmation, device.name if device else None
        )  # Build the checked request.
        logger.debug("Checked WebSocket start request for %s", request.key)  # Log the catalog key only.
        return request  # The manager can start this request.

    def _body(self, body: object) -> Mapping[str, object]:
        """Check the top-level request shape.

        Args:
            body: The raw JSON body.

        Returns:
            The body as a mapping.
        """
        if not isinstance(body, Mapping):  # The route must send a JSON object.
            raise StreamRequestError("bad_request", "The request body must be an object.")  # Refuse non-object bodies.
        unknown = set(body) - self._TOP_KEYS  # Raw paths and unknown keys are not allowed.
        if unknown:  # Any unknown key is a bad request.
            raise StreamRequestError(
                "bad_request", "The request body has an unknown key.", {"field": sorted(unknown)[0]}
            )  # Name one bad key.
        if not isinstance(body.get("kind"), str) or not isinstance(
            body.get("key"), str
        ):  # Kind and key are required text.
            raise StreamRequestError(
                "bad_request", "The request needs a kind and a key."
            )  # Refuse missing identity fields.
        return body  # The caller reads checked keys.

    def _definition(self, body: Mapping[str, object]) -> ChannelDefinition | UtilityDefinition:
        """Find the requested catalog definition.

        Args:
            body: The checked request body.

        Returns:
            The catalog definition.
        """
        kind = str(body["kind"])  # The body check already proved text.
        key = str(body["key"])  # The body check already proved text.
        definition = self._catalog.find(kind, key)  # Ask the registry to apply kind rules.
        if definition is None:  # Unknown keys use the contract error code.
            raise StreamRequestError("unknown_key", "The catalog key is unknown.")  # Refuse unknown entries.
        return definition  # The request names a valid entry.

    def _check_lock(self, definition: ChannelDefinition | UtilityDefinition) -> None:
        """Refuse a locked change or shell entry.

        Args:
            definition: The catalog definition to check.
        """
        if isinstance(definition, UtilityDefinition):  # Only utilities have safety locks.
            flag = self._catalog.lock_flag(definition)  # Read the active lock flag.
            if flag is not None:  # A disabled flag refuses the request before device lookup.
                raise StreamRequestError(
                    "locked", "This stream is locked by the portal settings.", {"flag": flag}
                )  # Name the flag.

    def _targets(self, definition: ChannelDefinition | UtilityDefinition, raw: object) -> dict[str, tuple[str, ...]]:
        """Check target identifiers.

        Args:
            definition: The catalog definition.
            raw: The raw targets object.

        Returns:
            The checked target values.
        """
        target_map = raw if isinstance(raw, Mapping) else {}  # Missing targets are an empty map.
        specs = (
            definition.identifiers if isinstance(definition, ChannelDefinition) else definition.targets
        )  # Pick the target fields.
        allowed = {field.name for field in specs}  # Only declared target names are accepted.
        unknown = set(target_map) - allowed  # The body must not send org_id or raw target names.
        if unknown:  # Unknown target fields are bad requests.
            raise StreamRequestError(
                "bad_request", "The target is unknown.", {"field": sorted(unknown)[0]}
            )  # Name one bad target.
        checked: dict[str, tuple[str, ...]] = {
            "org_id": (self._org_id,)
        }  # The portal setting supplies the organization.
        checked.update(
            {field.name: self._target_values(field, target_map.get(field.name), definition) for field in specs}
        )  # Check each declared target.
        return checked  # The path builder and runner use this map.

    def _target_values(
        self, spec: FieldSpec, raw: object, definition: ChannelDefinition | UtilityDefinition
    ) -> tuple[str, ...]:
        """Check one target field.

        Args:
            spec: The target field definition.
            raw: The raw target value.
            definition: The catalog definition.

        Returns:
            The checked target values.
        """
        values = raw if isinstance(raw, list) else [raw]  # A single value is normalized to one item.
        limit = self._target_limit(spec, definition)  # Find the maximum count for this target.
        if raw is None or not values or len(values) > limit:  # Enforce required and repeatable limits.
            raise StreamRequestError(
                "bad_request", "The target count is not valid.", {"field": spec.name}
            )  # Refuse bad target counts.
        checked = tuple(
            str(value) for value in values if IdentifierRules.is_uuid(value)
        )  # Keep valid UUID values only.
        if len(checked) != len(values) or len(set(checked)) != len(checked):  # Enforce UUID shape and uniqueness.
            raise StreamRequestError(
                "bad_request", "The target value is not valid.", {"field": spec.name}
            )  # Refuse bad targets.
        return checked  # The values are safe for path building.

    @staticmethod
    def _target_limit(spec: FieldSpec, definition: ChannelDefinition | UtilityDefinition) -> int:
        """Return the maximum value count for one target.

        Args:
            spec: The target field definition.
            definition: The catalog definition.

        Returns:
            The maximum count for the target.
        """
        repeatable = (
            isinstance(definition, ChannelDefinition) and definition.repeatable == spec.name
        )  # Check the repeatable target.
        return 10 if repeatable else 1  # Repeatable channel targets allow ten values.

    def _parameters(self, definition: ChannelDefinition | UtilityDefinition, raw: object) -> dict[str, object]:
        """Check utility parameters.

        Args:
            definition: The catalog definition.
            raw: The raw parameters object.

        Returns:
            The checked parameter values.
        """
        if isinstance(definition, ChannelDefinition):  # Channels have no parameters.
            return {}  # Keep the request shape consistent.
        parameter_map = raw if isinstance(raw, Mapping) else {}  # Missing parameters are an empty map.
        specs = {field.name: field for field in definition.fields}  # Give lookup by parameter name.
        unknown = set(parameter_map) - set(specs)  # The body must not send unknown parameters.
        if unknown:  # Unknown parameter fields are bad requests.
            raise StreamRequestError(
                "bad_request", "The parameter is unknown.", {"field": sorted(unknown)[0]}
            )  # Name one bad parameter.
        return self._checked_parameters(specs, parameter_map)  # Check each declared parameter.

    def _checked_parameters(self, specs: Mapping[str, FieldSpec], values: Mapping[object, object]) -> dict[str, object]:
        """Check each declared parameter.

        Args:
            specs: The parameter specifications by name.
            values: The raw parameter values.

        Returns:
            The checked parameters that are not empty.
        """
        checked: dict[str, object] = {}  # Keep only values that the SDK should receive.
        for name, spec in specs.items():  # Check fields in catalog order.
            if spec.required and name not in values:  # Required fields must be present.
                raise StreamRequestError(
                    "bad_request", "The parameter is required.", {"field": name}
                )  # Name the missing field.
            value = self._fields.check(spec, values.get(name))  # Check and convert the field value.
            if value is not None:  # Optional empty values stay out of parameters.
                checked[name] = value  # Store a JSON-safe value.
        return checked  # The runner passes this map to the SDK.

    def _device(
        self, definition: ChannelDefinition | UtilityDefinition, targets: Mapping[str, tuple[str, ...]]
    ) -> DeviceFacts | None:
        """Check the device lookup for a device utility.

        Args:
            definition: The catalog definition.
            targets: The checked target map.

        Returns:
            The device facts, or None when no device lookup is needed.
        """
        if (
            not isinstance(definition, UtilityDefinition) or "device_id" not in targets
        ):  # Channels and Mist Edge captures need no device lookup.
            return None  # No device name or family is needed.
        device = self._directory.describe_device(
            targets["site_id"][0], targets["device_id"][0]
        )  # Read device facts from the picker service.
        if device is None:  # An unknown device is a bad request.
            raise StreamRequestError(
                "bad_request", "The device is unknown.", {"field": "device_id"}
            )  # Refuse unknown devices.
        if device.family != definition.family:  # A utility must match the device family.
            raise StreamRequestError(
                "bad_request", "The device family cannot run this utility.", {"field": "device_id"}
            )  # Refuse mismatched families.
        return device  # Confirmation and title building use these facts.

    def _confirmation(
        self, definition: ChannelDefinition | UtilityDefinition, raw: object, device: DeviceFacts | None
    ) -> str | None:
        """Check the typed device confirmation.

        Args:
            definition: The catalog definition.
            raw: The raw confirmation value.
            device: The device facts from Mist.

        Returns:
            The stripped confirmation, or None.
        """
        if not isinstance(definition, UtilityDefinition) or definition.safety not in {
            Safety.CHANGE,
            Safety.SHELL,
        }:  # Most entries need no confirmation.
            return None  # No confirmation is stored.
        typed = raw.strip() if isinstance(raw, str) else ""  # Strip outer spaces from the operator text.
        if device is None or typed != device.name:  # The text must match the Mist device name.
            raise StreamRequestError(
                "confirmation", "The confirmation does not match the device name."
            )  # Refuse wrong confirmations.
        return typed  # The checked request records the confirmation.

    @staticmethod
    def _labels(raw: object) -> dict[str, str]:
        """Return safe title labels from the request body.

        Args:
            raw: The raw labels object.

        Returns:
            The safe labels by identifier value.
        """
        labels = raw if isinstance(raw, Mapping) else {}  # Missing labels give an empty map.
        return {
            str(key): StartRequestChecker._clean_label(value)
            for key, value in labels.items()
            if StartRequestChecker._clean_label(value)
        }  # Keep printable labels only.

    @staticmethod
    def _clean_label(value: object) -> str:
        """Return one safe title label.

        Args:
            value: The raw label value.

        Returns:
            A printable label of 64 characters or fewer.
        """
        text = value if isinstance(value, str) else ""  # Labels must be text.
        printable = "".join(char for char in text if char.isprintable()).strip()  # Drop non-printable characters.
        return printable[:64]  # Keep titles bounded.

    @staticmethod
    def _title(
        name: str, targets: Mapping[str, tuple[str, ...]], labels: Mapping[str, str], device: DeviceFacts | None
    ) -> str:
        """Build the session title.

        Args:
            name: The catalog entry name.
            targets: The checked target values.
            labels: The safe labels by identifier.
            device: The device facts, or None.

        Returns:
            The title for the session card.
        """
        values = [
            value for key, group in targets.items() if key != "org_id" for value in group
        ]  # Keep target order and skip organization.
        parts = [labels.get(value, value[:8]) for value in values]  # Use labels or short identifiers.
        if device is not None and device.name not in parts:  # Device utilities should show the device name.
            parts.append(device.name)  # Add the Mist device name.
        shown = parts[:3] + (
            [f"(+{len(parts) - 3})"] if len(parts) > 3 else []
        )  # Show at most three labels and a count.
        return f"{name} - {', '.join(shown)}" if shown else name  # Organization entries have no label.
