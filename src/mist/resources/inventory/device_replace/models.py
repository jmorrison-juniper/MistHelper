"""Pure models for the RMA device replacement operation.

Why:
    The destructive operation needs deterministic validation before any Mist
    request can run. These classes keep selection, type checks, and request
    body construction free of network and file-system effects.
"""

from __future__ import annotations  # WHY: enable modern annotations without runtime imports.

from dataclasses import dataclass, field  # WHY: declare small immutable records for tests and operations.
from typing import Any, ClassVar  # WHY: type raw Mist rows and stable CSV column metadata.


@dataclass(frozen=True, slots=True)
class InventoryDevice:
    """One normalized Mist inventory device row."""

    device_id: str  # WHY: getSiteDevice needs the Mist device identifier for backup reads.
    mac: str  # WHY: replaceOrgDevices names the old and new devices by MAC address.
    serial: str  # WHY: serial helps the operator verify the physical replacement.
    model: str  # WHY: model helps the operator catch a wrong replacement.
    device_type: str  # WHY: Mist requires replacement within the same device type.
    site_id: str  # WHY: assigned old devices need a site for getSiteDevice.
    name: str  # WHY: operators often know the device by Mist display name.
    raw: dict[str, Any] = field(default_factory=dict)  # WHY: backup evidence preserves the source row.

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> InventoryDevice:
        """Return a normalized device from one Mist inventory row."""
        mac = cls.normalize_mac(str(row.get("mac", "")))  # WHY: selectors and API body need one MAC form.
        return cls(  # WHY: convert optional Mist values into predictable strings.
            device_id=str(row.get("id", "")),  # WHY: missing IDs fail validation later.
            mac=mac,  # WHY: store the normalized MAC once.
            serial=str(row.get("serial", "")),  # WHY: display can show an empty string safely.
            model=str(row.get("model", "")),  # WHY: display can show an empty string safely.
            device_type=str(row.get("type", "")),  # WHY: type validation compares simple strings.
            site_id=str(row.get("site_id") or ""),  # WHY: no site means the device is unassigned.
            name=str(row.get("name") or row.get("hostname") or ""),  # WHY: hostname is a useful fallback.
            raw=dict(row),  # WHY: keep the full row for backup evidence.
        )

    @staticmethod
    def normalize_mac(value: str) -> str:
        """Return a lower-case MAC address without separators."""
        clean = value.replace(":", "").replace("-", "").replace(".", "")  # WHY: Mist accepts bare MAC text.
        return clean.strip().lower()  # WHY: selectors must be case-insensitive.

    def is_unassigned(self) -> bool:
        """Return whether the device has no assigned site."""
        return not self.site_id  # WHY: replacement devices must be unassigned in inventory.

    def label(self) -> str:
        """Return a short operator label for this device."""
        display_name = self.name or "unnamed"  # WHY: an empty name should still produce a readable row.
        return (
            f"{display_name} {self.mac} {self.model} {self.device_type}"  # WHY: include fields that prevent mistakes.
        )


@dataclass(frozen=True, slots=True)
class ReplaceRequest:
    """The OpenAPI body for `replaceOrgDevices`."""

    site_id: str  # WHY: Mist needs the site that owns the old device.
    mac: str  # WHY: this is the old device MAC address.
    inventory_mac: str  # WHY: this is the unassigned replacement device MAC address.
    discard: tuple[str, ...] = ()  # WHY: an empty tuple means copy all supported configuration.

    def as_body(self) -> dict[str, object]:
        """Return the JSON body required by the Mist API."""
        return {
            "site_id": self.site_id,
            "mac": self.mac,
            "inventory_mac": self.inventory_mac,
            "discard": list(self.discard),
        }


@dataclass(frozen=True, slots=True)
class DeviceReplaceLogEntry:
    """One durable CSV row for an RMA replacement attempt."""

    COLUMNS: ClassVar[tuple[str, ...]] = (
        "timestamp",
        "org_id",
        "old_mac",
        "new_mac",
        "old_type",
        "new_type",
        "result",
        "backup_path",
        "message",
    )
    timestamp: str  # WHY: the operator needs the run time in the change record.
    org_id: str  # WHY: the row must identify the organization that changed.
    old_mac: str  # WHY: the row must name the replaced device.
    new_mac: str  # WHY: the row must name the replacement device.
    old_type: str  # WHY: the row records the type check input.
    new_type: str  # WHY: the row records the type check input.
    result: str  # WHY: result tells whether the request was sent, dry-run, cancelled, or failed.
    backup_path: str  # WHY: the row links to the configuration evidence.
    message: str  # WHY: the row carries a short operator-readable outcome.

    def as_row(self) -> dict[str, str]:
        """Return this log entry as a CSV row."""
        return {column: str(getattr(self, column)) for column in self.COLUMNS}  # WHY: csv writes flat strings.


class DeviceReplaceValidator:
    """Validate inventory selections before a destructive replacement."""

    @staticmethod
    def find_old_device(devices: list[InventoryDevice], selector: str) -> InventoryDevice:
        """Return the one old device that matches a MAC address or name."""
        normalized = InventoryDevice.normalize_mac(selector)  # WHY: support colon, dash, dot, and bare MAC input.
        named = selector.strip().lower()  # WHY: names compare case-insensitively.
        matches = [
            device for device in devices if device.mac == normalized or device.name.lower() == named
        ]  # WHY: one path.
        if not matches:  # WHY: a missing old device must stop before backup.
            raise ValueError("No inventory device matches the old device selector.")  # WHY: user-facing refusal.
        if len(matches) > 1:  # WHY: an ambiguous name can replace the wrong device.
            raise ValueError(
                "More than one inventory device matches the old device selector."
            )  # WHY: require precision.
        return matches[0]  # WHY: exactly one device can continue.

    @staticmethod
    def replacement_choices(devices: list[InventoryDevice], old_device: InventoryDevice) -> list[InventoryDevice]:
        """Return unassigned devices that match the old device type."""
        return [
            device
            for device in devices
            if device.is_unassigned() and device.device_type == old_device.device_type and device.mac != old_device.mac
        ]

    @staticmethod
    def validate_pair(old_device: InventoryDevice, new_device: InventoryDevice) -> None:
        """Raise an operator-readable error when the replacement is invalid."""
        if old_device.device_type != new_device.device_type:  # WHY: Mist replacement requires matching device types.
            message = (  # WHY: keep both types in a short operator-readable error.
                f"Replacement type mismatch: old device type {old_device.device_type}, "
                f"new device type {new_device.device_type}."
            )
            raise ValueError(message)  # WHY: state both types so the operator sees the mismatch.
        if not new_device.is_unassigned():  # WHY: Mist requires the replacement to be unassigned.
            raise ValueError("Replacement device is already assigned to a site.")  # WHY: stop before backup.
        if not old_device.site_id or not old_device.device_id:  # WHY: backup reads need site and device identifiers.
            raise ValueError(
                "Old device must have a site and device identifier before replacement."
            )  # WHY: stop safely.

    @staticmethod
    def build_request(old_device: InventoryDevice, new_device: InventoryDevice) -> ReplaceRequest:
        """Return the request body after pair validation succeeds."""
        DeviceReplaceValidator.validate_pair(
            old_device, new_device
        )  # WHY: never build a destructive body from invalid input.
        return ReplaceRequest(
            site_id=old_device.site_id, mac=old_device.mac, inventory_mac=new_device.mac
        )  # WHY: schema.
