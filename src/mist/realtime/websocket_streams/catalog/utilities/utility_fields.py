"""Build checked input and target fields for SDK utility functions."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import inspect  # SDK signatures define the supported parameters.
from collections.abc import Callable  # Type SDK utility callables.
from dataclasses import replace  # Reuse the shared field record with one scoped hint.

from src.mist.realtime.websocket_streams.catalog.model import FieldKind, FieldSpec  # Build immutable field records.
from src.mist.realtime.websocket_streams.catalog.sdk_annotation import (
    SdkAnnotation,
)  # Read enum values from SDK annotations.
from src.mist.realtime.websocket_streams.catalog.utility_text import UtilityText  # Build public labels and hints.


class UtilityFieldFactory:
    """Convert SDK parameters and targets into checked fields."""

    _SKIP_PARAMS = frozenset(
        {
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
    )  # Exclude transport, target, and fixed runtime parameters.
    _CHOICES = {"band": ("24", "5", "6")}  # Supply values for the SDK text band field.
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
        "max_pkt_len": (FieldKind.INTEGER, False, 64, 2048, 512),
        "band": (FieldKind.CHOICE, True, None, None, None),
    }  # Define every accepted utility input field.

    def fields(self, family: str, name: str, function: Callable[..., object]) -> tuple[FieldSpec, ...]:
        """Build operator fields from one SDK signature."""
        hints, parameters = (
            SdkAnnotation.hints(function),
            inspect.signature(function).parameters.values(),
        )  # Read annotations and parameters from the installed SDK.
        fields = [
            self.parameter(family, name, parameter, hints.get(parameter.name))
            for parameter in parameters
            if parameter.name not in self._SKIP_PARAMS and parameter.name != "port"
        ]  # Convert each operator-controlled parameter.
        if name == "remotePcap" and family in {"ex", "srx", "ssr"}:  # Wired captures select device ports.
            fields.insert(0, self.named("port_ids", True, family))  # Add the derived port list first.
        if name in {"orgRemotePcap", "siteRemotePcap"}:  # Mist Edge captures select interfaces.
            fields.insert(0, self.named("interfaces", True, family))  # Add the derived interface list first.
        return tuple(fields)  # Preserve SDK order after derived fields.

    def parameter(
        self,
        family: str,
        function_name: str,
        parameter: inspect.Parameter,
        annotation: object,
    ) -> FieldSpec:
        """Build one field from SDK parameter metadata."""
        required = parameter.default is inspect.Signature.empty  # Detect required SDK parameters.
        if function_name == "retrieveDhcpLeases" and parameter.name == "network":  # Preserve the contract override.
            required = True  # Require the network for lease retrieval.
        choices = SdkAnnotation.enum_choices(annotation)  # Read fixed values from the resolved enum.
        field = replace(
            self.named(parameter.name, required, "", choices),
            client_picker=self.client_picker_mode(family, function_name, parameter.name),
        )  # Add optional client assistance without changing the SDK field name.
        if family == "srx" and function_name == "retrieveRoutes" and parameter.name == "protocol":
            return replace(field, hint=UtilityText.hint("protocol", "srx.retrieveRoutes"))
        return field  # Preserve shared field behavior for every other parameter.

    @staticmethod
    def client_picker_mode(family: str, function_name: str, parameter_name: str) -> str | None:
        """Return only client-selector modes supported by verified associations."""
        if function_name == "releaseDhcpLeases" and parameter_name == "macs":
            return "multiple" if family == "ex" else "manual" if family in {"srx", "ssr"} else None
        if family == "ex" and function_name == "retrieveMacTable" and parameter_name == "mac_address":
            return "single"
        return None

    def named(
        self,
        name: str,
        required: bool,
        family: str,
        choices: tuple[str, ...] = (),
        utility_key: str = "",
    ) -> FieldSpec:
        """Build one field from the central contract table."""
        if name not in self._SPECS:  # Refuse an SDK parameter outside the reviewed contract.
            raise RuntimeError(f"Unknown WebSocket utility parameter {name}")  # Stop startup with exact evidence.
        kind, base_required, minimum, maximum, default = self._SPECS[name]  # Read the reviewed field settings.
        maximum = 1520 if name == "max_pkt_len" and family in {"srx", "ssr"} else maximum  # Limit gateway packets.
        return FieldSpec(
            name=name,
            label=UtilityText.label(name),
            kind=kind,
            required=required or bool(base_required),
            minimum=minimum,
            maximum=maximum,
            choices=choices or self._CHOICES.get(name, ()),
            default=default,
            hint=UtilityText.hint(name),
        )  # Return the established field payload data.

    def targets(self, family: str, name: str) -> tuple[FieldSpec, ...]:
        """Build identifier fields for one utility target."""
        site = FieldSpec("site_id", "Site", FieldKind.UUID, required=True, picker="sites")  # Select a site.
        device = FieldSpec("device_id", "Device", FieldKind.UUID, required=True, picker="devices")  # Select a device.
        mxedge = FieldSpec("mxedge_id", "Mist Edge", FieldKind.UUID, required=True, picker="mxedges")  # Select an edge.
        if family == "mxedge" and name == "orgRemotePcap":  # Organization capture needs only a Mist Edge.
            return (mxedge,)  # Preserve the organization target payload.
        return (site, mxedge) if family == "mxedge" else (site, device)  # Preserve site target payloads.
