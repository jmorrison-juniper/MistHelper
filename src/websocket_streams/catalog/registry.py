"""The joined WebSocket stream catalog.

Why:
    Issue #3551. The page needs one payload with channels, utilities, and flag
    states. The server also needs one lookup that keeps shell utilities separate
    from other utilities.
"""

from __future__ import annotations  # Postponed annotations keep each hint import-safe.

import logging  # The portal uses standard logging for each action.

from src.websocket_streams.catalog.channels import ChannelCatalog  # Channel lookup source.
from src.websocket_streams.catalog.model import ChannelDefinition, Safety, UtilityDefinition  # Shared catalog records.
from src.websocket_streams.catalog.utilities import UtilityCatalog  # Utility lookup source.

logger = logging.getLogger(__name__)  # Keep registry log records under this module name.


class StreamCatalog:
    """Join channel and utility catalogs with the lock flags."""

    CHANGES_FLAG = "PORTAL_WS_ENABLE_CHANGES"  # Environment variable that unlocks change utilities.
    SHELL_FLAG = "PORTAL_WS_ENABLE_SHELL"  # Environment variable that unlocks shell utilities.

    def __init__(
        self, channels: ChannelCatalog, utilities: UtilityCatalog, *, changes_enabled: bool, shell_enabled: bool
    ) -> None:
        """Build one stream catalog.

        Args:
            channels: The channel catalog to read.
            utilities: The utility catalog to read.
            changes_enabled: True when the change flag is on.
            shell_enabled: True when the shell flag is on.
        """
        logger.info("Building the joined WebSocket stream catalog")  # Log before storing dependencies.
        self._channels = channels  # Keep the channel catalog for lookups.
        self._utilities = utilities  # Keep the utility catalog for lookups.
        self._changes_enabled = changes_enabled  # Store the current change lock state.
        self._shell_enabled = shell_enabled  # Store the current shell lock state.
        logger.debug(
            "Built the stream catalog with changes=%s shell=%s", changes_enabled, shell_enabled
        )  # Log flag state.

    def find(self, kind: str, key: str) -> ChannelDefinition | UtilityDefinition | None:
        """Find one entry by request kind and key.

        Args:
            kind: The request kind: channel, utility, or shell.
            key: The catalog key.

        Returns:
            The matching definition, or None.
        """
        logger.info("Finding WebSocket entry kind %s key %s", kind, key)  # Log before lookup.
        entry = self._find_entry(kind, key)  # Delegate the kind rules.
        logger.debug("WebSocket entry kind %s key %s found: %s", kind, key, entry is not None)  # Log lookup result.
        return entry  # The checker raises the public error.

    def lock_flag(self, definition: UtilityDefinition) -> str | None:
        """Return the disabled flag for one utility.

        Args:
            definition: The utility definition to check.

        Returns:
            The variable name when locked, or None when unlocked.
        """
        logger.debug("Checking the WebSocket lock for %s", definition.key)  # One catalog read checks 54 entries.
        flag = self._flag_for(definition)  # Map safety to the matching flag.
        logger.debug("WebSocket lock for %s is %s", definition.key, flag)  # Log only the variable name.
        return flag  # READ and CAPTURE return None.

    def page_payload(self) -> dict[str, object]:
        """Return the catalog payload for the page.

        Returns:
            A JSON-safe payload with no channel path template.
        """
        logger.info("Building the WebSocket catalog page payload")  # Log before payload build.
        channels = [entry.to_payload() for entry in self._channels.entries()]  # Convert channels to public form.
        utilities = [
            entry.to_payload(self.lock_flag(entry) is not None) for entry in self._utilities.entries()
        ]  # Convert utilities to public form.
        logger.debug(
            "Built the WebSocket catalog payload with %s channels and %s utilities", len(channels), len(utilities)
        )  # Log payload counts.
        return {
            "flags": self._flags_payload(),
            "channels": channels,
            "utilities": utilities,
        }  # The blueprint adds readiness and limits.

    def _find_entry(self, kind: str, key: str) -> ChannelDefinition | UtilityDefinition | None:
        """Apply the kind rules for lookup.

        Args:
            kind: The request kind.
            key: The catalog key.

        Returns:
            The matching definition, or None.
        """
        if kind == "channel":  # Channel requests use the channel catalog.
            return self._channels.get(key)  # Return channel entries only.
        utility = (
            self._utilities.get(key) if kind in {"utility", "shell"} else None
        )  # Only utility and shell kinds read utilities.
        if utility is None:  # An unknown key or kind gives no entry.
            return None  # The checker raises the public error.
        return (
            utility if (kind == "shell") == (utility.safety is Safety.SHELL) else None
        )  # Keep shells out of utility starts.

    def _flag_for(self, definition: UtilityDefinition) -> str | None:
        """Return the disabled flag for one utility definition.

        Args:
            definition: The utility definition to check.

        Returns:
            The variable name when locked, or None.
        """
        if definition.safety is Safety.CHANGE and not self._changes_enabled:  # The change flag locks change utilities.
            return self.CHANGES_FLAG  # The error payload names this variable.
        if definition.safety is Safety.SHELL and not self._shell_enabled:  # The shell flag locks shell utilities.
            return self.SHELL_FLAG  # The error payload names this variable.
        return None  # READ, CAPTURE, and enabled entries are unlocked.

    def _flags_payload(self) -> dict[str, dict[str, object]]:
        """Return the flag payload for the page.

        Returns:
            The enabled state and variable name of each flag.
        """
        return {
            "changes": {"enabled": self._changes_enabled, "variable": self.CHANGES_FLAG},
            "shell": {"enabled": self._shell_enabled, "variable": self.SHELL_FLAG},
        }  # Match the HTTP contract.
