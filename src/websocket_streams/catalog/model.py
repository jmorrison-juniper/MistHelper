"""The data types of the WebSockets catalog.

Why:
    Issue #3551. The catalog lists every Mist WebSocket stream that the portal
    can start. Each channel, each device utility, and each input field is one
    frozen record, so no request can change the catalog at run time. The page
    payload of a channel never holds its path, because the server builds each
    path from a catalog key and checked identifiers only.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Mapping  # Types the checked identifiers of a path build.
from dataclasses import dataclass  # Each catalog record is a frozen dataclass.
from enum import StrEnum  # Each enum value is also its JSON text.


class FieldKind(StrEnum):
    """The check that the server applies to one input value."""

    UUID = "uuid"  # A Mist identifier in the 8-4-4-4-12 hexadecimal form.
    HOST = "host"  # An IPv4 address, an IPv6 address, or a DNS name.
    IP = "ip"  # An IPv4 or IPv6 address only.
    PREFIX = "prefix"  # An IPv4 or IPv6 network in CIDR form.
    INTEGER = "integer"  # A whole number inside the minimum and the maximum.
    VLAN = "vlan"  # A VLAN number from 1 to 4094, sent to the SDK as text.
    CHOICE = "choice"  # One value from a fixed list.
    BOOLEAN = "boolean"  # A true or false value.
    MAC = "mac"  # One MAC address of 12 hexadecimal digits.
    MAC_LIST = "mac_list"  # One or more MAC addresses.
    PORT = "port"  # One Junos port name, such as ge-0/0/1.
    PORT_LIST = "port_list"  # One or more Junos port names.
    NAME = "name"  # A plain name, such as a network, a VRF, or a service.
    NAME_LIST = "name_list"  # One or more plain names.
    FILTER = "filter"  # A tcpdump capture filter from a fixed character set.


class Safety(StrEnum):
    """The safety class of one device utility."""

    READ = "read"  # The utility reads state and changes nothing.
    CAPTURE = "capture"  # The utility captures packets for 60 seconds at most.
    CHANGE = "change"  # The utility changes device state. PORTAL_WS_ENABLE_CHANGES unlocks it.
    SHELL = "shell"  # The utility opens a remote shell. PORTAL_WS_ENABLE_SHELL unlocks it.


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """One input field of a catalog entry.

    Attributes:
        name: The SDK parameter name or the identifier name, such as ``host``.
        label: The label on the page.
        kind: The check that the server applies to the value.
        required: True when the field must hold a value.
        minimum: The lowest value of an integer field.
        maximum: The highest value of an integer field.
        choices: The values of a choice field.
        default: The value that the page shows first.
        hint: One plain sentence for the operator.
        picker: The picker list that fills an identifier field, or None.
    """

    name: str  # The key of the value in the start request.
    label: str  # The text next to the input on the page.
    kind: FieldKind  # The check that the server applies.
    required: bool = False  # Most SDK parameters are optional.
    minimum: int | None = None  # Only integer fields use a range.
    maximum: int | None = None  # Only integer fields use a range.
    choices: tuple[str, ...] = ()  # Only choice fields use a list.
    default: str | int | bool | None = None  # A JSON-safe first value for the page.
    hint: str = ""  # An empty hint shows no help text.
    picker: str | None = None  # The picker name, such as "sites", "devices", or "maps".

    def to_payload(self) -> dict[str, object]:
        """Return the JSON form of the field for the page.

        Returns:
            One dictionary with every attribute in JSON-safe form.
        """
        return {
            "name": self.name,  # The key that the page sends back.
            "label": self.label,  # The text next to the input.
            "kind": self.kind.value,  # The page picks the input type from the kind.
            "required": self.required,  # The page marks a required field.
            "minimum": self.minimum,  # The page sets the input range.
            "maximum": self.maximum,  # The page sets the input range.
            "choices": list(self.choices),  # A list, because JSON has no tuple.
            "default": self.default,  # The first value of the input.
            "hint": self.hint,  # The help text under the input.
            "picker": self.picker,  # The page fills the input from this picker.
        }


@dataclass(frozen=True, slots=True)
class ChannelDefinition:
    """One subscribe channel of the Mist WebSocket API.

    Attributes:
        key: The unique catalog key, such as ``site.stats.devices``.
        scope: The group on the page: organization, site, location, or diagnostics.
        name: The plain name on the page.
        description: One plain sentence about the data.
        path_template: The channel path with named identifiers. The page never receives it.
        identifiers: The identifier fields that the path needs.
        repeatable: The one identifier that accepts up to 10 values, or None.
    """

    key: str  # The key that the page sends in a start request.
    scope: str  # The page groups the channels by this scope.
    name: str  # The title of the catalog entry.
    description: str  # The plain sentence under the title.
    path_template: str  # Such as /sites/{site_id}/stats/devices. It stays in the server.
    identifiers: tuple[FieldSpec, ...] = ()  # An organization channel takes the portal organization.
    repeatable: str | None = None  # Most channels take one value for each identifier.

    def to_payload(self) -> dict[str, object]:
        """Return the JSON form of the channel for the page, without the path.

        Returns:
            One dictionary with every attribute except the path template.
        """
        return {
            "key": self.key,  # The key that the page sends back.
            "scope": self.scope,  # The group on the page.
            "name": self.name,  # The title of the entry.
            "description": self.description,  # The plain sentence under the title.
            "identifiers": [field.to_payload() for field in self.identifiers],  # The pickers to show.
            "repeatable": self.repeatable,  # The page allows several values for this identifier.
        }

    def build_paths(self, targets: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
        """Return the channel paths for checked identifier values.

        Only the start request checker gives the targets, so each value is a
        checked identifier. The template ignores a target that it does not name.

        Args:
            targets: Each identifier name with its checked values.

        Returns:
            One path for each value of the repeatable identifier, or one path.
        """
        fixed = {name: values[0] for name, values in targets.items() if values}  # The first value of each identifier.
        repeatable = self.repeatable or ""  # An empty name matches no target.
        repeated = targets.get(repeatable, ())  # The values that each give one path.
        if not repeated:  # A channel without a repeatable value gives one path.
            return (self.path_template.format_map(fixed),)  # Fill each named identifier.
        return tuple(
            self.path_template.format_map({**fixed, repeatable: value}) for value in repeated
        )  # One path for each value of the repeatable identifier.


@dataclass(frozen=True, slots=True)
class UtilityDefinition:
    """One device utility that sends its output on a WebSocket channel.

    Attributes:
        key: The unique catalog key, such as ``ex.ping``.
        family: The device family: ap, ex, srx, ssr, or mxedge.
        function_name: The SDK facade function, such as ``ping``.
        name: The plain name on the page.
        description: One plain sentence about the utility.
        fields: The parameter fields that the operator sets.
        safety: The safety class of the utility.
        output: The view on the page: lines, screen, packets, or terminal.
        targets: The identifier fields that name the device and the site.
        scope: "site" for every utility except the organization Mist Edge capture.
    """

    key: str  # The key that the page sends in a start request.
    family: str  # The page offers the utility only for a device of this family.
    function_name: str  # The runner calls this function of the SDK family module.
    name: str  # The title of the catalog entry.
    description: str  # The plain sentence under the title.
    fields: tuple[FieldSpec, ...]  # The parameters, in the order of the SDK signature.
    safety: Safety  # The lock and the confirmation depend on this class.
    output: str  # The page picks the view from this value.
    targets: tuple[FieldSpec, ...]  # Such as the site and the device.
    scope: str = "site"  # Only the organization Mist Edge capture uses "organization".

    def to_payload(self, locked: bool) -> dict[str, object]:
        """Return the JSON form of the utility for the page.

        Args:
            locked: True when the flag of the safety class is off.

        Returns:
            One dictionary with every attribute and the lock state.
        """
        return {
            "key": self.key,  # The key that the page sends back.
            "family": self.family,  # The page filters the list by the device family.
            "name": self.name,  # The title of the entry.
            "description": self.description,  # The plain sentence under the title.
            "safety": self.safety.value,  # The page shows the safety class.
            "locked": locked,  # The page shows a lock and disables the start control.
            "output": self.output,  # The page picks the view.
            "fields": [field.to_payload() for field in self.fields],  # The parameter inputs.
            "targets": [field.to_payload() for field in self.targets],  # The identifier pickers.
            "scope": self.scope,  # An organization utility needs no site.
        }
