"""The checked form of one start request.

Why:
    Issue #3551. The server builds a StartRequest only after every check
    passes. The runners and the session manager accept only this checked form,
    so no raw path and no unchecked value can reach Mist.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Mapping  # Types the checked targets and parameters.
from dataclasses import dataclass  # Each record is a frozen dataclass.
from typing import Protocol  # The device lookup is a structural interface.

from src.websocket_streams.catalog.model import ChannelDefinition, UtilityDefinition  # The catalog entry types.


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
