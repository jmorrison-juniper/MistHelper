"""Target identifier checks for WebSocket start requests."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from collections.abc import Mapping  # Raw and checked target values use mapping interfaces.

from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldSpec,
    UtilityDefinition,
)  # Targets come from catalog entries.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Invalid targets use the request contract.
from src.mist.realtime.websocket_streams.intake.identifiers.identity_rules import (
    IdentityIdentifierRules,
)  # Targets must be Mist UUIDs.


class TargetValidator:
    """Check declared target identifiers and inject organization scope."""

    def __init__(self, org_id: str) -> None:
        """Store the trusted organization identifier."""
        self._org_id = org_id  # The request body cannot override organization scope.

    def check(self, definition: ChannelDefinition | UtilityDefinition, raw: object) -> dict[str, tuple[str, ...]]:
        """Return checked targets for one definition."""
        target_map = raw if isinstance(raw, Mapping) else {}  # Missing targets become an empty mapping.
        specs = (
            definition.identifiers if isinstance(definition, ChannelDefinition) else definition.targets
        )  # Select specs.
        unknown = set(target_map) - {field.name for field in specs}  # Refuse undeclared or raw path keys.
        if unknown:  # Name one unknown field for the page.
            raise StreamRequestError("bad_request", "The target is unknown.", {"field": sorted(unknown)[0]})
        checked: dict[str, tuple[str, ...]] = {"org_id": (self._org_id,)}  # Inject the trusted portal organization.
        checked.update({spec.name: self._values(spec, target_map.get(spec.name), definition) for spec in specs})
        return checked  # Runners receive only checked identifier values.

    def _values(
        self, spec: FieldSpec, raw: object, definition: ChannelDefinition | UtilityDefinition
    ) -> tuple[str, ...]:
        """Return checked values for one target field."""
        values = raw if isinstance(raw, list) else [raw]  # Normalize one value to a list.
        limit = self._target_limit(spec, definition)  # Read the route-specific target limit.
        if raw is None or not values or len(values) > limit:  # Enforce required and repeatable counts.
            raise StreamRequestError("bad_request", "The target count is not valid.", {"field": spec.name})
        return self._checked_values(spec, values)  # Return unique UUID text for path construction.

    @staticmethod
    def _target_limit(spec: FieldSpec, definition: ChannelDefinition | UtilityDefinition) -> int:
        """Return the permitted target count for one field."""
        repeatable = (
            isinstance(definition, ChannelDefinition) and definition.repeatable == spec.name
        )  # Read limit mode.
        return 10 if repeatable else 1  # Repeatable channel targets allow ten values.

    @staticmethod
    def _checked_values(spec: FieldSpec, values: list[object]) -> tuple[str, ...]:
        """Return unique UUID text for one target field."""
        checked = tuple(str(value) for value in values if IdentityIdentifierRules.is_uuid(value))  # Keep UUIDs only.
        if len(checked) != len(values) or len(set(checked)) != len(checked):  # Enforce shape and uniqueness.
            raise StreamRequestError("bad_request", "The target value is not valid.", {"field": spec.name})
        return checked  # The path builder receives safe UUID text.
