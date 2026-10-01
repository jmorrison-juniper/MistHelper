"""The WebSocket utility catalog for the Operations portal.

Why:
    Issue #3551. The portal must expose each streaming device utility that the
    installed Mist SDK supports. This module reads SDK facade signatures and
    turns the supported parameters into checked fields.
"""

from __future__ import annotations  # Postponed annotations keep each hint import-safe.

import inspect  # The SDK signatures are the source for parameter names.
import logging  # The portal uses standard logging for each action.
from collections.abc import Callable  # The field builders are small callables.
from typing import cast  # The SDK has no type information for mypy.

import mistapi.device_utils.ap as sdk_ap  # The AP facade lists AP utilities.
import mistapi.device_utils.ex as sdk_ex  # The EX facade lists switch utilities.
import mistapi.device_utils.mxedge as sdk_mxedge  # The Mist Edge facade lists captures.
import mistapi.device_utils.srx as sdk_srx  # The SRX facade lists gateway utilities.
import mistapi.device_utils.ssr as sdk_ssr  # The SSR facade lists router utilities.

from src.websocket_streams.catalog.model import FieldKind, FieldSpec, Safety, UtilityDefinition  # Catalog records.
from src.websocket_streams.catalog.sdk_annotation import SdkAnnotation  # Each enum comes from the SDK signature.
from src.websocket_streams.catalog.utility_text import UtilityText  # Plain names, sentences, and hints.

logger = logging.getLogger(__name__)  # Keep catalog log records under this module name.


class UtilityCatalog:
    """Hold the Mist device utility definitions."""

    _SKIP = {
        "clearBpduError",
        "clearDot1xSessions",
        "clearLearnedMac",
        "clearMacTable",
        "clearHitCount",
        "interactiveShell",
        "ShellSession",
        "Node",
        "RouteProtocol",
        "TracerouteProtocol",
        "SessionWithUrl",
    }
    _SKIP_PARAMS = {
        "apisession",
        "site_id",
        "device_id",
        "org_id",
        "timeout",
        "on_message",
        "device_interfaces",
        "duration",
        "rows",
        "cols",
    }
    _MODULES = (("ap", sdk_ap), ("ex", sdk_ex), ("srx", sdk_srx), ("ssr", sdk_ssr), ("mxedge", sdk_mxedge))
    _CHOICES = {
        "band": ("24", "5", "6"),
    }  # The SDK types the band as text. Each enum parameter reads its values from the SDK signature.
    _SPECS = {
        "host": (FieldKind.HOST, True, None, None, None),
        "count": (FieldKind.INTEGER, False, 1, 100, 5),
        "node": (FieldKind.CHOICE, False, None, None, None),
        "size": (FieldKind.INTEGER, False, 1, 65000, None),
        "vrf": (FieldKind.NAME, False, None, None, None),
        "network": (FieldKind.NAME, False, None, None, None),
        "service_name": (FieldKind.NAME, False, None, None, None),
        "ssid": (FieldKind.NAME, False, None, None, None),
        "route_type": (FieldKind.NAME, False, None, None, None),
        "ip": (FieldKind.IP, False, None, None, None),
        "neighbor": (FieldKind.IP, False, None, None, None),
        "prefix": (FieldKind.PREFIX, False, None, None, None),
        "port_id": (FieldKind.PORT, False, None, None, None),
        "port_ids": (FieldKind.PORT_LIST, True, None, None, None),
        "macs": (FieldKind.MAC_LIST, False, None, None, None),
        "mac_address": (FieldKind.MAC, False, None, None, None),
        "ap_mac": (FieldKind.MAC, False, None, None, None),
        "vlan_id": (FieldKind.VLAN, False, 1, 4094, None),
        "self_originate": (FieldKind.BOOLEAN, False, None, None, None),
        "protocol": (FieldKind.CHOICE, False, None, None, None),
        "service_ids": (FieldKind.NAME_LIST, False, None, None, None),
        "interfaces": (FieldKind.NAME_LIST, True, None, None, None),
        "tcpdump_expression": (FieldKind.FILTER, False, None, 256, None),
        "num_packets": (FieldKind.INTEGER, False, 1, 10000, 1024),
        "max_pkt_len": (FieldKind.INTEGER, False, 64, 1536, 512),
        "band": (FieldKind.CHOICE, True, None, None, None),
    }

    def __init__(self) -> None:
        """Build the utility lookup table."""
        logger.info("Building the WebSocket utility catalog")  # Log before building the catalog.
        self._entries = tuple(self._build_all_entries())  # Read the SDK once at startup.
        self._by_key = {entry.key: entry for entry in self._entries}  # Give constant-time lookup by key.
        logger.debug("Built %s WebSocket utility entries", len(self._entries))  # Log the catalog size.

    def entries(self) -> tuple[UtilityDefinition, ...]:
        """Return all utility definitions in SDK order.

        Returns:
            The immutable utility records.
        """
        logger.info("Reading the WebSocket utility catalog")  # Log before returning the catalog.
        logger.debug("Read %s WebSocket utility entries", len(self._entries))  # Log the result count.
        return self._entries  # The tuple prevents caller changes.

    def get(self, key: str) -> UtilityDefinition | None:
        """Return one utility definition.

        Args:
            key: The catalog key to find.

        Returns:
            The utility definition, or None when the key is unknown.
        """
        logger.info("Finding WebSocket utility key %s", key)  # Log before lookup.
        entry = self._by_key.get(key)  # Read the immutable lookup table.
        logger.debug("WebSocket utility key %s found: %s", key, entry is not None)  # Log lookup result.
        return entry  # The caller handles an unknown key.

    @classmethod
    def _build_all_entries(cls) -> list[UtilityDefinition]:
        """Build every utility definition from the SDK facades.

        Returns:
            The utility definitions in family order.
        """
        entries: list[UtilityDefinition] = []  # Keep the records in page order.
        for family, module in cls._MODULES:  # Each SDK facade is one family group.
            names = cast(tuple[str, ...] | list[str], getattr(module, "__all__", ()))  # Read the public SDK names.
            entries.extend(cls._build_family(family, module, names))  # Add each supported function.
        return entries  # The caller freezes the list as a tuple.

    @classmethod
    def _build_family(cls, family: str, module: object, names: tuple[str, ...] | list[str]) -> list[UtilityDefinition]:
        """Build the definitions for one SDK facade.

        Args:
            family: The device family of the facade.
            module: The SDK facade module.
            names: The public names from ``__all__``.

        Returns:
            The supported utility definitions for the family.
        """
        entries: list[UtilityDefinition] = []  # Keep only callable stream functions.
        for name in names:  # The SDK order becomes the catalog order.
            candidate = getattr(module, name, None)  # Read the public object from the facade.
            if name not in cls._SKIP and callable(candidate):  # Skip non-stream types and REST-only calls.
                entries.append(cls._build_entry(family, name, candidate))  # Convert one SDK function.
        return entries  # The caller adds the family entries to the catalog.

    @classmethod
    def _build_entry(cls, family: str, name: str, func: Callable[..., object]) -> UtilityDefinition:
        """Build one utility definition from one SDK function.

        Args:
            family: The device family of the function.
            name: The SDK function name.
            func: The SDK callable.

        Returns:
            One utility definition.
        """
        fields = cls._fields_for(family, name, func)  # Convert SDK parameters to fields.
        safety = cls._safety(name)  # Classify the action before building the record.
        output = cls._output(name, safety)  # Pick the page view for the stream.
        targets = cls._targets_for(family, name)  # Pick the identifiers that start the utility.
        scope = (
            "organization" if family == "mxedge" and name == "orgRemotePcap" else "site"
        )  # Only one capture is organization scoped.
        return UtilityDefinition(
            f"{family}.{name}",
            family,
            name,
            UtilityText.label(name),
            UtilityText.sentence(name, safety),
            fields,
            safety,
            output,
            targets,
            scope,
        )  # Return the frozen record.

    @classmethod
    def _fields_for(cls, family: str, name: str, func: Callable[..., object]) -> tuple[FieldSpec, ...]:
        """Build fields for one SDK function.

        Args:
            family: The device family of the function.
            name: The SDK function name.
            func: The SDK callable. Its signature and annotations name the fields.

        Returns:
            The checked parameter fields.
        """
        hints = SdkAnnotation.hints(func)  # One parameter name can use a different enum in each function.
        fields = [
            cls._field_for(name, parameter, hints.get(parameter.name))
            for parameter in inspect.signature(func).parameters.values()
            if parameter.name not in cls._SKIP_PARAMS and parameter.name != "port"
        ]  # Convert each operator parameter.
        if name == "remotePcap" and family in {"ex", "srx", "ssr"}:  # Wired device captures take selected ports.
            fields.insert(0, cls._field_named("port_ids", True, family))  # Add the derived capture field.
        if name in {"orgRemotePcap", "siteRemotePcap"}:  # Mist Edge captures take interfaces.
            fields.insert(0, cls._field_named("interfaces", True, family))  # Add the derived capture field.
        if cls._safety(name) is Safety.CAPTURE:
            fields.append(
                FieldSpec(
                    "duration",
                    "Duration (seconds)",
                    FieldKind.INTEGER,
                    required=True,
                    minimum=60,
                    maximum=3600,
                    default=60,
                    hint="The capture can end earlier when it reaches the packet limit.",
                )
            )
        return tuple(fields)  # Return fields in SDK order with derived fields first.

    @classmethod
    def _field_for(cls, function_name: str, parameter: inspect.Parameter, annotation: object) -> FieldSpec:
        """Build one field for one SDK parameter.

        Args:
            function_name: The SDK function name that owns the parameter.
            parameter: The SDK parameter metadata.
            annotation: The resolved SDK annotation of the parameter, or None.

        Returns:
            One field specification.
        """
        required = parameter.default is inspect.Signature.empty  # A missing default means the SDK requires the value.
        if (
            function_name == "retrieveDhcpLeases" and parameter.name == "network"
        ):  # The contract makes this field required.
            required = True  # The SDK also requires this value.
        choices = SdkAnnotation.enum_choices(annotation)  # An SDK enum gives the only accepted values.
        return cls._field_named(parameter.name, required, "", choices)  # Use the shared field table.

    @classmethod
    def _field_named(cls, name: str, required: bool, family: str, choices: tuple[str, ...] = ()) -> FieldSpec:
        """Build one field from the contract field table.

        Args:
            name: The SDK parameter name or derived field name.
            required: True when the request must hold this field.
            family: The device family that can change a range.
            choices: The SDK enum values. An empty tuple uses the choice table.

        Returns:
            One field specification.

        Raises:
            RuntimeError: The SDK exposed a parameter outside the contract table.
        """
        if name not in cls._SPECS:  # The contract forbids guessed field kinds.
            raise RuntimeError(f"Unknown WebSocket utility parameter {name}")  # Stop startup with evidence.
        kind, base_required, minimum, maximum, default = cls._SPECS[name]  # Read the field contract.
        maximum = (
            1520 if name == "max_pkt_len" and family in {"srx", "ssr"} else maximum
        )  # Gateways use the lower packet length.
        return FieldSpec(
            name=name,
            label=UtilityText.label(name),
            kind=kind,
            required=required or bool(base_required),
            minimum=minimum,
            maximum=maximum,
            choices=choices or cls._CHOICES.get(name, ()),
            default=default,
            hint=UtilityText.hint(name),
        )  # Return the checked field.

    @staticmethod
    def _targets_for(family: str, name: str) -> tuple[FieldSpec, ...]:
        """Build target fields for one utility.

        Args:
            family: The device family of the utility.
            name: The SDK function name.

        Returns:
            The identifier fields that name the target.
        """
        site = FieldSpec(
            "site_id", "Site", FieldKind.UUID, required=True, picker="sites"
        )  # Site utilities need a site picker.
        device = FieldSpec(
            "device_id", "Device", FieldKind.UUID, required=True, picker="devices"
        )  # Device utilities need a device picker.
        mxedge = FieldSpec(
            "mxedge_id", "Mist Edge", FieldKind.UUID, required=True, picker="mxedges"
        )  # Mist Edge captures need a Mist Edge picker.
        return (
            (mxedge,)
            if family == "mxedge" and name == "orgRemotePcap"
            else ((site, mxedge) if family == "mxedge" else (site, device))
        )  # Return the target shape.

    @staticmethod
    def _safety(name: str) -> Safety:
        """Return the safety class of one utility.

        Args:
            name: The SDK function name.

        Returns:
            The safety class for the catalog.
        """
        if name in {"createShellSession"}:  # Shell sessions give device CLI access.
            return Safety.SHELL  # The shell flag locks this entry.
        if "Pcap" in name:  # Remote capture utilities collect packets.
            return Safety.CAPTURE  # Capture entries use the packet view.
        if name in {
            "releaseDhcpLeases",
            "bouncePort",
            "cableTest",
            "clearSessions",
        }:  # These utilities interrupt device state.
            return Safety.CHANGE  # The change flag locks this entry.
        return Safety.READ  # All other entries read state only.

    @staticmethod
    def _output(name: str, safety: Safety) -> str:
        """Return the output view of one utility.

        Args:
            name: The SDK function name.
            safety: The safety class of the utility.

        Returns:
            The page output view.
        """
        if safety is Safety.SHELL:  # A shell needs a terminal view.
            return "terminal"  # The page shows an input line for this view.
        if safety is Safety.CAPTURE:  # A capture sends packet records.
            return "packets"  # The page shows packet summaries.
        return "screen" if name in {"topCommand", "monitorTraffic"} else "lines"  # Screen utilities replace the view.
