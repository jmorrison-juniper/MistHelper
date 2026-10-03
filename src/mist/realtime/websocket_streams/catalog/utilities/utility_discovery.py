"""Discover supported utility definitions from Mist SDK facades."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The shared logger writes through standard logging.
from collections.abc import Callable  # Type SDK utility callables.
from typing import cast  # Narrow SDK facade metadata for mypy.

import mistapi.device_utils.ap as sdk_ap  # Provide AP utility functions.
import mistapi.device_utils.ex as sdk_ex  # Provide switch utility functions.
import mistapi.device_utils.mxedge as sdk_mxedge  # Provide Mist Edge capture functions.
import mistapi.device_utils.srx as sdk_srx  # Provide SRX utility functions.
import mistapi.device_utils.ssr as sdk_ssr  # Provide SSR utility functions.

from src.mist.realtime.websocket_streams.catalog.model import UtilityDefinition  # Build immutable utility records.
from src.mist.realtime.websocket_streams.catalog.utilities.utility_fields import (
    UtilityFieldFactory,
)  # Build target and input fields.
from src.mist.realtime.websocket_streams.catalog.utilities.utility_profile import (
    UtilityProfile,
)  # Classify utility behavior.
from src.mist.realtime.websocket_streams.catalog.utility_text import UtilityText  # Build public names and descriptions.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Apply the shared safe JSON logging boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep discovery records safe and bounded.


class UtilityDiscovery:
    """Convert supported SDK facade functions into catalog records."""

    _SKIP = frozenset(
        {
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
    )  # Exclude REST-only calls and public SDK types.
    _MODULES = (("ap", sdk_ap), ("ex", sdk_ex), ("srx", sdk_srx), ("ssr", sdk_ssr), ("mxedge", sdk_mxedge))

    def __init__(self) -> None:
        """Build the field and classification collaborators."""
        self._fields = UtilityFieldFactory()  # Centralize checked field construction.
        self._profile = UtilityProfile()  # Centralize safety and output classification.

    def entries(self) -> tuple[UtilityDefinition, ...]:
        """Return every supported utility in facade order."""
        logger.emit(logging.INFO, "catalog.discovery.start")  # Record the SDK discovery action.
        entries: list[UtilityDefinition] = []  # Keep family and SDK order stable.
        for family, module in self._MODULES:  # Read each supported device facade.
            names = cast(tuple[str, ...] | list[str], getattr(module, "__all__", ()))  # Read public SDK names.
            entries.extend(self.family_entries(family, module, names))  # Add callable utilities for this family.
        logger.emit(logging.DEBUG, "catalog.discovery.finish", {"count": len(entries)})  # Log the exact total.
        return tuple(entries)  # Freeze discovery results for callers.

    def family_entries(
        self, family: str, module: object, names: tuple[str, ...] | list[str]
    ) -> list[UtilityDefinition]:
        """Return supported utility definitions from one facade."""
        entries: list[UtilityDefinition] = []  # Keep the facade order stable.
        for name in names:  # Inspect each public SDK object once.
            candidate = getattr(module, name, None)  # Read the named public object.
            if name not in self._SKIP and callable(candidate):  # Keep supported streaming callables only.
                entries.append(self.entry(family, name, candidate))  # Convert the function to a catalog record.
        return entries  # Add this family to the full catalog.

    def entry(self, family: str, name: str, function: Callable[..., object]) -> UtilityDefinition:
        """Build one immutable utility definition."""
        fields = self._fields.fields(family, name, function)  # Convert SDK parameters to checked fields.
        safety = self._profile.safety(name)  # Classify the action before public text is built.
        return UtilityDefinition(
            f"{family}.{name}",
            family,
            name,
            UtilityText.label(name),
            UtilityText.sentence(name, safety),
            fields,
            safety,
            self._profile.output(name, safety),
            self._fields.targets(family, name),
            self._profile.scope(family, name),
        )  # Preserve every established utility field.
