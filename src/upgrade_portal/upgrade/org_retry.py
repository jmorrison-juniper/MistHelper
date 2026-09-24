"""Choose the devices that a retry of one multi-site operation upgrades again.

Why:
    Issue #3247. The single-site portal can retry the failed devices of a
    finished run. The multi-site portal could not, so an operator planned every
    device again by hand and could upgrade a healthy device a second time.

    This module reads the durable operation record and names the devices that
    need a second attempt. It makes no cloud call and no write. The signed
    browser cookie holds only the operation identity, because the cookie holds
    at most 4 KB and a device list of many sites can pass that limit.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each selection without a MAC address or a secret.
from collections.abc import Mapping, Sequence  # Accept each stored record without a concrete type.
from dataclasses import dataclass  # Keep one retry plan immutable.
from typing import Any  # The stored record holds JSON values of mixed types.

from src.upgrade_portal.capture.devices import normalize_device_mac  # The one MAC address rule of the portal.
from src.upgrade_portal.upgrade.org_devices import OrgDeviceRows  # The device rows of the progress page.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

RETRY_STATES = frozenset({"failed", "rejected", "not_submitted", "cancelled", "skipped"})  # No firmware landed.
MATCH_OUTCOME = "version_match"  # The device runs the requested version, so it never needs a retry.
MISMATCH_OUTCOME = "version_mismatch"  # The device runs another version, whatever its state word is.
FAMILY_ORDER = ("ap", "switch", "gateway")  # The order of the device type boxes on the options page.
PREFILL_DROPPED = frozenset({"start_time", "operation_id", "target_count"})  # Values that belong to the old plan.
DEVICE_FIELDS = ("name", "mac", "site_name", "device_type", "state")  # The fields that the pages show.


@dataclass(frozen=True, slots=True)
class OrgRetryPlan:
    """Hold the devices and the prefilled choices of one multi-site retry.

    Attributes:
        operation_id: The settled operation that the retry repeats.
        org_id: The organization of that operation.
        site_ids: The sites that hold a retry device, in the approved order.
        devices: One small row for each retry device.
        options: The earlier choices of the operator, narrowed to the retry.
    """

    operation_id: str  # The settled operation that the retry repeats.
    org_id: str  # The retry never crosses into another organization.
    site_ids: tuple[str, ...]  # The sites that the retry selects again.
    devices: tuple[dict[str, str], ...]  # The devices that the options page keeps.
    options: dict[str, Any]  # The choices that the options form shows first.

    @property
    def macs(self) -> frozenset[str]:
        """Return the normalized MAC address of each retry device."""
        found = {normalize_device_mac(device.get("mac")) for device in self.devices}  # Compare every spelling.
        found.discard("")  # A malformed address must never match a device.
        return frozenset(found)  # The narrow step reads this set.

    def to_session(self) -> dict[str, str]:
        """Return the small value that the signed cookie holds for this retry."""
        return {"operation_id": self.operation_id, "org_id": self.org_id}  # A reference only, never a device.

    @staticmethod
    def session_reference(value: object, org_id: str) -> str | None:
        """Return the operation identity of one cookie value, or None.

        Args:
            value: The value that the signed cookie holds.
            org_id: The organization that the operator selected.

        Returns:
            The operation identity, or None when the value is damaged or names another organization.
        """
        if not isinstance(value, Mapping) or value.get("org_id") != org_id:  # A retry never crosses organizations.
            return None  # The caller then plans every device.
        operation_id = value.get("operation_id")  # The durable identity of the settled operation.
        return operation_id if isinstance(operation_id, str) and operation_id else None  # Accept text only.

    @classmethod
    def empty(cls, operation_id: str, org_id: str) -> OrgRetryPlan:
        """Return a plan that holds no device, so the save plans no device."""
        return cls(operation_id, org_id, (), (), {})  # The narrow step then removes every row.

    def narrow(self, view: Mapping[str, Any]) -> dict[str, Any]:
        """Return a copy of one site view that holds the retry devices only.

        Args:
            view: The device view of one site.

        Returns:
            The same view with the other devices removed.
        """
        narrowed = dict(view)  # Keep the caller view unchanged.
        targets = view.get("targets")  # The device rows of the site.
        rows = targets if isinstance(targets, list) else []  # A damaged list holds no device.
        wanted = self.macs  # Build the set one time for every row.
        narrowed["targets"] = [  # Keep each retry device in the order of the site view.
            row for row in rows if isinstance(row, Mapping) and normalize_device_mac(row.get("mac")) in wanted
        ]
        logger.debug("The retry keeps %s of %s device(s) of one site", len(narrowed["targets"]), len(rows))
        return narrowed  # The options page and the save read this view.


class OrgRetrySelection:
    """Select the devices of one settled operation that need a second attempt."""

    @staticmethod
    def needs_retry(row: Mapping[str, Any]) -> bool:
        """Report whether one device row needs a second attempt.

        Args:
            row: One device row of the progress page.

        Returns:
            True when the device does not run the requested version and the job did not upgrade it.
        """
        outcome = str(row.get("version_outcome") or "")  # The version check of the device.
        if outcome == MATCH_OUTCOME:  # The device runs the requested version.
            return False  # A second attempt would reinstall healthy firmware.
        state = str(row.get("state") or "").strip().lower()  # The state word of the device.
        return state in RETRY_STATES or outcome == MISMATCH_OUTCOME  # No firmware landed, or the wrong one did.

    @classmethod
    def plan(cls, record: Mapping[str, Any], rows: Sequence[Mapping[str, Any]] | None = None) -> OrgRetryPlan | None:
        """Return the retry plan of one operation, or None when no device needs a retry.

        Args:
            record: The durable operation record.
            rows: The device rows, when the caller already built them.

        Returns:
            The retry plan, or None.
        """
        logger.info("Select the retry devices of aggregate upgrade %s", record.get("operation_id", ""))
        source = OrgDeviceRows(record).rows() if rows is None else rows  # Reuse the rows of the caller.
        site_ids = cls._approved_sites(record)  # The retry keeps the approved sites only.
        chosen = [row for row in source if str(row.get("site_id") or "") in site_ids and cls.needs_retry(row)]
        logger.debug("Aggregate upgrade %s holds %s retry device(s)", record.get("operation_id", ""), len(chosen))
        if not chosen:  # No device needs a second attempt.
            return None  # The page then shows no retry control.
        return OrgRetryPlan(  # Keep the plan small, so every page can build it again.
            operation_id=str(record.get("operation_id") or ""),
            org_id=str(record.get("org_id") or ""),
            site_ids=cls._retry_sites(site_ids, chosen),
            devices=tuple({field: str(row.get(field) or "") for field in DEVICE_FIELDS} for row in chosen),
            options=cls._prefill(record, chosen),
        )

    @staticmethod
    def _approved_sites(record: Mapping[str, Any]) -> tuple[str, ...]:
        """Return the approved site order of one operation."""
        listed = record.get("site_ids")  # The aggregate service keeps the approved order.
        return tuple(str(site_id) for site_id in listed if site_id) if isinstance(listed, list) else ()

    @staticmethod
    def _retry_sites(site_ids: tuple[str, ...], chosen: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
        """Return the approved sites that hold a retry device, in the approved order."""
        wanted = {str(row.get("site_id") or "") for row in chosen}  # The sites of the retry devices.
        return tuple(site_id for site_id in site_ids if site_id in wanted)  # Keep the approved order.

    @staticmethod
    def _prefill(record: Mapping[str, Any], chosen: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Return the earlier choices, narrowed to the device types of the retry."""
        stored = record.get("plan_options")  # An operation from an earlier release holds no choices.
        source: Mapping[str, Any] = stored if isinstance(stored, Mapping) else {}  # A damaged value is empty.
        options = {key: value for key, value in source.items() if key not in PREFILL_DROPPED}  # Drop the old plan.
        families = {str(row.get("device_type") or "") for row in chosen}  # The device types of the retry.
        options["selected_types"] = [family for family in FAMILY_ORDER if family in families]  # Page order.
        for row in chosen:  # Fill each missing target version from the stored device rows.
            key = f"version_{row.get('device_type')}"  # The field of one device type.
            if not str(options.get(key) or "").strip() and row.get("version_target"):  # Keep a stored choice.
                options[key] = str(row["version_target"])  # The version that the operator asked for before.
        return options  # The options form shows these values first.
