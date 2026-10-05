"""Immutable models for checked WebSocket start requests."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from collections.abc import Mapping  # Checked targets and parameters remain read-only interfaces.
from dataclasses import dataclass  # Request records use frozen slot dataclasses.
from typing import Protocol  # Device lookup uses a structural interface.

from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    UtilityDefinition,
)  # Requests retain catalog entries.


@dataclass(frozen=True, slots=True)
class StartRequest:
    """Hold one request after every intake check passes."""

    kind: str  # The runner type is channel, utility, or shell.
    definition: ChannelDefinition | UtilityDefinition  # The selected catalog entry drives execution.
    targets: Mapping[str, tuple[str, ...]]  # Every target contains checked UUID values.
    parameters: Mapping[str, object]  # Every parameter contains a checked JSON-safe value.
    title: str  # The bounded session title uses safe labels.
    confirmation: str | None = None  # Change and shell requests retain the checked device name.
    device_name: str | None = None  # Audit records use the Mist device name.

    @property
    def key(self) -> str:
        """Return the selected catalog key."""
        return self.definition.key  # The immutable definition owns the key.

    def target(self, name: str) -> str:
        """Return the first checked target value."""
        values = self.targets.get(name, ())  # An absent target has no values.
        return values[0] if values else ""  # Existing runners treat empty text as absent.


@dataclass(frozen=True, slots=True)
class DeviceFacts:
    """Hold the device facts required by utility intake checks."""

    name: str  # Typed confirmation must match this Mist device name.
    family: str | None  # Utility selection must match this device family.
    mac: str | None = None  # Client discovery needs the validated device MAC.


class DeviceDirectory(Protocol):
    """Describe one device for start request validation."""

    def describe_device(self, site_id: str, device_id: str) -> DeviceFacts | None:
        """Return the selected device facts or None."""
