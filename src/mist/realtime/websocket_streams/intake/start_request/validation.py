"""Body, catalog, lock, and parameter checks for start requests."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from collections.abc import Mapping  # Request bodies and parameters use mapping interfaces.

from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldSpec,
    UtilityDefinition,
)  # Catalog models define checks.
from src.mist.realtime.websocket_streams.catalog.registry.stream_catalog import (
    StreamCatalog,
)  # Enforce kind and lock rules.
from src.mist.realtime.websocket_streams.intake.fields.checker import (
    FieldValueChecker,
)  # Parameter values use shared field checks.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Validation failures use the request contract.


class RequestValidator:
    """Check request shape, catalog identity, locks, and parameters."""

    TOP_KEYS = frozenset({"kind", "key", "targets", "parameters", "confirmation", "labels"})  # Bound accepted input.

    def __init__(self, catalog: StreamCatalog) -> None:
        """Store the catalog and field checker."""
        self._catalog = catalog  # Definitions and flags come from one joined catalog.
        self.parameters = ParameterValidator()  # Parameter behavior stays in its named collaborator.

    def body(self, body: object) -> Mapping[str, object]:
        """Return one checked request body mapping."""
        if not isinstance(body, Mapping):  # The route must send a JSON object.
            raise StreamRequestError("bad_request", "The request body must be an object.")
        unknown = set(body) - self.TOP_KEYS  # Raw paths and unknown keys are not accepted.
        if unknown:  # Name one bad key for the page.
            raise StreamRequestError(
                "bad_request", "The request body has an unknown key.", {"field": sorted(unknown)[0]}
            )
        if not isinstance(body.get("kind"), str) or not isinstance(body.get("key"), str):  # Identity fields are text.
            raise StreamRequestError("bad_request", "The request needs a kind and a key.")
        return body  # Later checks read only accepted keys.

    def definition(self, body: Mapping[str, object]) -> ChannelDefinition | UtilityDefinition:
        """Return the selected catalog definition."""
        definition = self._catalog.find(str(body["kind"]), str(body["key"]))  # Apply catalog kind rules.
        if definition is None:  # Unknown entries use the stable contract code.
            raise StreamRequestError("unknown_key", "The catalog key is unknown.")
        return definition  # The request names one valid catalog entry.

    def check_lock(self, definition: ChannelDefinition | UtilityDefinition) -> None:
        """Refuse one locked utility definition."""
        flag = (
            self._catalog.lock_flag(definition) if isinstance(definition, UtilityDefinition) else None
        )  # Read utility lock.
        if flag is not None:  # Refuse before device lookup or parameter work.
            raise StreamRequestError("locked", "This stream is locked by the portal settings.", {"flag": flag})


class ParameterValidator:
    """Check declared utility parameter values."""

    def __init__(self) -> None:
        """Build the shared field value checker."""
        self._fields = FieldValueChecker()  # Parameter values use one stateless coordinator.

    def check(self, definition: ChannelDefinition | UtilityDefinition, raw: object) -> dict[str, object]:
        """Return checked utility parameters."""
        if isinstance(definition, ChannelDefinition):  # Channels do not accept utility parameters.
            return {}  # Keep the checked request shape consistent.
        values = raw if isinstance(raw, Mapping) else {}  # Missing parameters become an empty mapping.
        specs = {field.name: field for field in definition.fields}  # Index declared fields by stable name.
        unknown = set(values) - set(specs)  # Refuse undeclared parameter names.
        if unknown:  # Name one bad field for the page.
            raise StreamRequestError("bad_request", "The parameter is unknown.", {"field": sorted(unknown)[0]})
        return self._checked(specs, values)  # Convert each declared value.

    def _checked(self, specs: Mapping[str, FieldSpec], values: Mapping[object, object]) -> dict[str, object]:
        """Return present checked parameter values."""
        checked: dict[str, object] = {}  # Omit empty optional values.
        for name, spec in specs.items():  # Preserve catalog field order.
            if spec.required and name not in values:  # Required fields must be present.
                raise StreamRequestError("bad_request", "The parameter is required.", {"field": name})
            value = self._fields.check(spec, values.get(name))  # Check and normalize the raw value.
            if value is not None:  # Optional empty values stay absent.
                checked[name] = value  # Store a JSON-safe value.
        return checked  # The runner receives only checked parameters.
