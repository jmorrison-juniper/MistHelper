"""Join the channel and utility catalogs for request and page use."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The shared logger writes through standard logging.

from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog  # Supply channel definitions.
from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    Safety,
    UtilityDefinition,
)  # Type catalog records.
from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import (
    UtilityCatalog,
)  # Supply utility definitions.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Apply the shared safe JSON logging boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep catalog records in one bounded JSON format.


class StreamCatalog:
    """Join catalog discovery, lock checks, and page payloads."""

    CHANGES_FLAG = "PORTAL_WS_ENABLE_CHANGES"  # Name the environment flag for change utilities.
    SHELL_FLAG = "PORTAL_WS_ENABLE_SHELL"  # Name the environment flag for shell utilities.

    def __init__(
        self, channels: ChannelCatalog, utilities: UtilityCatalog, *, changes_enabled: bool, shell_enabled: bool
    ) -> None:
        """Store the immutable catalogs and current lock states."""
        logger.emit(logging.INFO, "catalog.stream.build.start")  # Record the bounded build action.
        self._channels, self._utilities = channels, utilities  # Keep both source catalogs for discovery.
        self._changes_enabled, self._shell_enabled = changes_enabled, shell_enabled  # Preserve both lock states.
        fields = {"status": "ready", "count": len(utilities.entries())}  # Report only bounded operational fields.
        logger.emit(logging.DEBUG, "catalog.stream.build.finish", fields)  # Record the completed build.

    def find(self, kind: str, key: str) -> ChannelDefinition | UtilityDefinition | None:
        """Find one catalog entry while keeping shell utilities separate."""
        logger.emit(logging.INFO, "catalog.stream.find.start", {"action": kind})  # Log the bounded request kind.
        entry: ChannelDefinition | UtilityDefinition | None  # Keep both catalog record types explicit for mypy.
        if kind == "channel":  # Channel requests read only the channel catalog.
            entry = self._channels.get(key)  # Find the checked channel key.
        else:
            utility = self._utilities.get(key) if kind in {"utility", "shell"} else None  # Limit utility kinds.
            matches_shell = utility is not None and (kind == "shell") == (utility.safety is Safety.SHELL)
            entry = utility if matches_shell else None  # Keep shell and non-shell starts separate.
        logger.emit(logging.DEBUG, "catalog.stream.find.finish", {"status": entry is not None})  # Log the result.
        return entry  # Let the request checker handle an unknown entry.

    def lock_flag(self, definition: UtilityDefinition) -> str | None:
        """Return the flag that currently locks one utility."""
        logger.emit(logging.INFO, "catalog.stream.lock.start", {"action": definition.safety.value})  # Log safety only.
        change_locked, shell_locked = (
            definition.safety is Safety.CHANGE and not self._changes_enabled,
            definition.safety is Safety.SHELL and not self._shell_enabled,
        )  # Check both independent enabling flags.
        flag = (
            self.CHANGES_FLAG if change_locked else self.SHELL_FLAG if shell_locked else None
        )  # Name the active flag.
        logger.emit(logging.DEBUG, "catalog.stream.lock.finish", {"status": flag is not None})  # Log lock state.
        return flag  # Preserve the existing flag result.

    def page_payload(self) -> dict[str, object]:
        """Return the JSON-safe page catalog without channel paths."""
        logger.emit(logging.INFO, "catalog.stream.payload.start")  # Record the payload build.
        channels, utilities = (
            [entry.to_payload() for entry in self._channels.entries()],
            [entry.to_payload(self.lock_flag(entry) is not None) for entry in self._utilities.entries()],
        )  # Build both public entry lists and hide channel paths.
        payload: dict[str, object] = {
            "flags": {
                "changes": {"enabled": self._changes_enabled, "variable": self.CHANGES_FLAG},
                "shell": {"enabled": self._shell_enabled, "variable": self.SHELL_FLAG},
            },
            "channels": channels,
            "utilities": utilities,
        }  # Preserve the exact page payload.
        logger.emit(
            logging.DEBUG,
            "catalog.stream.payload.finish",
            {"count": len(channels) + len(utilities), "status": "ready"},
        )  # Record the bounded completed payload.
        return payload  # Return the established page contract.
