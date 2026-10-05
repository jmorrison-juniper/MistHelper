"""Real catalog discovery and an independent, source-backed selector oracle."""

import importlib  # Inspect installed SDK facades without invoking exported operations.
import inspect  # SDK signatures provide required parameter evidence.
import logging  # Log counts only, never target data.
from collections import Counter  # Detect duplicates without discarding inventory entries.
from importlib.metadata import version  # Record the actual installed SDK version.
from string import Formatter  # Derive channel targets from the server path, not display text.
from typing import cast  # Narrow the documented public payload without hiding type errors.

logger = logging.getLogger(__name__)  # Keep discovery records bounded.


class InventoryBuilder:
    """Build the complete installed catalog without constructing runners."""

    def build(self):
        from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog  # Real channel definitions.
        from src.mist.realtime.websocket_streams.catalog.registry.stream_catalog import (
            StreamCatalog,
        )  # Real payload builder.
        from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import (
            UtilityCatalog,
        )  # Real SDK discovery.

        logger.info("Discovering real WebSocket catalog")  # Record before SDK introspection.
        channels, utilities = ChannelCatalog(), UtilityCatalog()  # Constructors only read definitions and signatures.
        payload = StreamCatalog(
            channels, utilities, changes_enabled=False, shell_enabled=False
        ).page_payload()  # Keep locks.
        payload.update(ready=True, reason=None, limits={"max_sessions": 0})  # Isolated rendering only, never execution.
        definitions = {entry.key: entry for entry in channels.entries()} | {
            entry.key: entry for entry in utilities.entries()
        }  # Preserve both typed source record sets.
        entries = cast(list[dict[str, object]], payload["channels"]) + cast(
            list[dict[str, object]], payload["utilities"]
        )  # Narrow the real page payload's documented entry lists.
        logger.debug("Discovered %d catalog entries", len(entries))  # Prove a real denominator.
        return {
            "payload": payload,
            "definitions": definitions,
            "entries": entries,
            "sdk_version": version("mistapi"),
        }  # Actual SDK, no credentials.

    @staticmethod
    def reconcile(expected, actual):
        expected_counts, actual_counts = Counter(expected), Counter(actual)  # Do not flatten duplicates.
        differences = [
            key
            for key in expected_counts.keys() | actual_counts.keys()
            if expected_counts[key] != 1 or actual_counts[key] != 1
        ]  # Membership and duplicate drift.
        return sorted(differences)  # Public operation keys are safe failure evidence.


class OperationOracle:
    """Requirements come from server paths and SDK signatures, not descriptions."""

    _CHANNEL_CLASSES = {
        "org": {
            "org.insights.summary": "InsightsEvents",
            "org.stats.mxedges": "MxEdgesStatsEvents",
            "org.mxedges": "MxEdgesEvents",
        },
        "site": {
            "site.stats.clients": "ClientsStatsEvents",
            "site.stats.devices": "DeviceStatsEvents",
            "site.devices": "DeviceEvents",
            "site.stats.mxedges": "MxEdgesStatsEvents",
            "site.mxedges": "MxEdgesEvents",
        },
        "location": {
            "location.assets": "BleAssetsEvents",
            "location.clients": "ConnectedClientsEvents",
            "location.sdkclients": "SdkClientsEvents",
            "location.unconnected_clients": "UnconnectedClientsEvents",
            "location.discovered_assets": "DiscoveredBleAssetsEvents",
        },
    }  # Research maps source keys to installed SDK definitions, not live permission.
    _FIXED = {
        "self",
        "apisession",
        "org_id",
        "timeout",
        "on_message",
        "duration",
        "rows",
        "cols",
        "device_interfaces",
    }  # Runner-owned values.

    def __init__(self, inventory):
        self.definitions = inventory["definitions"]  # Retain actual server definitions.

    def required(self, key):
        definition = self.definitions[key]  # Fail on an unknown operation instead of guessing.
        if hasattr(definition, "path_template"):
            names = {
                name for _, name, _, _ in Formatter().parse(definition.path_template) if name
            }  # Server consumes these targets.
            return names - {"org_id"}  # The authorized portal organization is not a user picker.
        module = importlib.import_module("mistapi.device_utils." + definition.family)  # Read the installed facade.
        function = getattr(module, definition.function_name)  # Never call the utility.
        parameters = inspect.signature(function).parameters.values()  # Read independent SDK metadata.
        names = {
            parameter.name for parameter in parameters if parameter.default is inspect.Parameter.empty
        } - self._FIXED  # Required SDK inputs.
        if definition.family == "mxedge":
            names -= {"port", "mxedges", "interfaces"}  # Runner body_builder consumes these derived capture inputs.
            names.add("mxedge_id")  # Runner body_builder._mxedge requires this target.
        elif definition.function_name == "remotePcap" and "port" in names:
            names = (names - {"port"}) | {"port_ids"}  # CaptureBodyBuilder._device derives port bodies from port_ids.
        return names  # Do not grant execution permission from this result.

    def missing(self, entry):
        fields = entry.get("identifiers", entry.get("targets", [])) + entry.get(
            "fields", []
        )  # Rendered catalog requirements.
        declared = {
            field["name"] for field in fields if field["required"]
        }  # Optional controls cannot satisfy a required input.
        return self.required(entry["key"]) - declared  # Independent evidence detects missing required controls.

    def verified(self, key):
        group = key.split(".")[0]  # Identify the research mapping only, not operation safety.
        name = self._CHANNEL_CLASSES.get(group, {}).get(key)  # Diagnostic and capture channels stay unverified.
        if not name:
            return False  # Utilities are inspectable but never verified for live execution.
        module_name = {"org": "orgs", "site": "sites", "location": "location"}[group]  # Real installed SDK module.
        module = importlib.import_module("mistapi.websockets." + module_name)  # Import definitions only.
        candidate = getattr(module, name, None)  # SDK drift must not silently verify a missing class.
        if candidate is None:
            return False  # Preserve the blocker in evidence.
        signature = inspect.signature(candidate)  # Do not instantiate a client or attach authentication.
        required = {
            parameter.name
            for parameter in signature.parameters.values()
            if parameter.default is inspect.Parameter.empty
        }  # SDK targets.
        return self.required(key) <= required  # This is signature evidence only, not a safety decision.
