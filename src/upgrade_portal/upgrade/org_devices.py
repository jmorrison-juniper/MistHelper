"""Build one device row for each device of one multi-site operation.

Why:
    Issue #3249. The single-site progress page shows one row for each device.
    Each row shows the state, the versions, the version check, and the failure
    reason. The multi-site page showed one row for each child job, with counts
    only. An operator therefore could not see which device failed.

    This module reads the durable operation record and the cloud answers that
    the aggregate service stores in that record. The module keeps no state, and
    it makes no cloud call. `org_versions.py` decides which sites need a
    running version read.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each row build without a MAC address or a secret.
from collections.abc import Mapping  # Accept each stored record without a concrete type.
from typing import Any  # The stored record holds JSON values of mixed types.

from src.upgrade_portal.capture.devices import normalize_device_mac  # The one MAC address rule of the portal.
from src.upgrade_portal.upgrade.gate import version_outcome  # The one version check rule of FR-051.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

LISTED_FAILURE = "The cloud lists this device as failed."  # The reason when the failed child holds no error text.


class CloudTargetLists:
    """Index the MAC addresses that each target list of one cloud answer names."""

    PRIORITY = (  # The cloud target lists in priority order, with the word that the row shows.
        ("failed", "failed"),
        ("upgraded", "upgraded"),
        ("skipped", "skipped"),
        ("rebooted", "rebooted"),
        ("reboot_in_progress", "rebooting"),
        ("downloaded", "downloaded"),
        ("downloading", "downloading"),
        ("download_requested", "download requested"),
        ("scheduled", "scheduled"),
    )

    def __init__(self, status_data: object) -> None:
        """Index every list of one stored cloud answer.

        Args:
            status_data: The cloud answer that the aggregate service stores in one child.
        """
        self._members = self._index(status_data)  # One set of normalized MAC addresses for each list.

    def word_of(self, mac: object) -> str:
        """Return the state word of the first list that names one device.

        Args:
            mac: The MAC address of the device, in any spelling.

        Returns:
            The state word, or an empty string when no list names the device.
        """
        key = normalize_device_mac(mac)  # Compare every spelling in one form.
        if not key:  # A malformed address matches no list, and never every list.
            return ""  # The caller treats the device as unlisted.
        for list_name, word in self.PRIORITY:  # The first match wins, so failed wins over upgraded.
            if key in self._members[list_name]:  # This list names the device.
                return word  # Show the word of the most serious list.
        return ""  # No list names the device yet.

    @classmethod
    def _index(cls, status_data: object) -> dict[str, frozenset[str]]:
        """Return one set of normalized MAC addresses for each list name."""
        members: dict[str, set[str]] = {list_name: set() for list_name, _ in cls.PRIORITY}  # Start empty.
        for target_map in cls._target_maps(status_data):  # Read each place that can hold a list.
            for list_name, macs in members.items():  # Join the same list from every place.
                macs.update(cls._list_keys(target_map.get(list_name)))  # Add the normalized addresses.
        return {list_name: frozenset(macs) for list_name, macs in members.items()}  # Freeze the index.

    @staticmethod
    def _list_keys(values: object) -> set[str]:
        """Return the normalized MAC addresses of one list, without an empty key."""
        if not isinstance(values, list | tuple):  # A missing or damaged list names no device.
            return set()  # Add nothing to the index.
        keys = {normalize_device_mac(value) for value in values}  # Normalize each spelling.
        keys.discard("")  # An empty key would match every malformed address.
        return keys  # The caller joins these keys into the index.

    @staticmethod
    def _target_maps(status_data: object) -> list[Mapping[str, Any]]:
        """Return each mapping of one cloud answer that can hold a target list."""
        if not isinstance(status_data, Mapping):  # A child with no read holds no list.
            return []  # The index stays empty.
        maps: list[Mapping[str, Any]] = [status_data]  # A site child keeps its reboot list at the root.
        root_targets = status_data.get("targets")  # A site answer keeps its lists under one key.
        if isinstance(root_targets, Mapping):  # Read the root lists when they exist.
            maps.append(root_targets)  # Keep the root lists.
        entries = status_data.get("site_upgrades", status_data.get("upgrades", []))  # The site entries of an AP job.
        for entry in entries if isinstance(entries, list) else []:  # Read each site entry of the AP job.
            targets = CloudTargetLists._entry_targets(entry)  # The lists of one site, or None.
            if targets is not None:  # Keep only a readable list mapping.
                maps.append(targets)  # Join this site into the index.
        return maps  # The caller reads each list name from each mapping.

    @staticmethod
    def _entry_targets(entry: object) -> Mapping[str, Any] | None:
        """Return the target lists of one site entry of an access point job, or None."""
        if not isinstance(entry, Mapping):  # A damaged entry holds no list.
            return None  # The caller skips the entry.
        upgrade = entry.get("upgrade")  # The reference answer nests each site job under this key.
        nested = upgrade if isinstance(upgrade, Mapping) else entry  # Another answer keeps the lists on the entry.
        targets = nested.get("targets")  # The lists of one site job.
        return targets if isinstance(targets, Mapping) else None  # A damaged list mapping names no device.


class StoredReadings:
    """Read the running version readings that one operation record stores."""

    def __init__(self, record: Mapping[str, Any]) -> None:
        """Keep the reading map of one operation record.

        Args:
            record: The durable operation record.
        """
        stored = record.get("device_versions")  # The aggregate service writes this map.
        self._entries: Mapping[str, Any] = stored if isinstance(stored, Mapping) else {}  # A damaged map is empty.

    def entry(self, mac: object) -> Mapping[str, Any] | None:
        """Return the stored reading of one device, or None when no reading exists."""
        value = self._entries.get(normalize_device_mac(mac))  # The store keys each reading by the normalized MAC.
        return value if isinstance(value, Mapping) else None  # A damaged entry counts as no reading.

    def version(self, mac: object) -> str:
        """Return the stored running version of one device, or an empty string."""
        entry = self.entry(mac)  # Read the stored reading once.
        return str(entry.get("version") or "") if entry is not None else ""  # An absent reading shows no version.

    def reads(self, mac: object) -> int:
        """Return the count of reads of one device, or zero when the count is damaged."""
        entry = self.entry(mac)  # Read the stored reading once.
        count = entry.get("reads") if entry is not None else 0  # The aggregate service counts each read.
        return count if type(count) is int else 0  # A count that is not a whole number restarts at zero.


class OrgChildDevices:
    """Read the devices of one aggregate child and the state of each device."""

    WAITING_STATES = frozenset({"accepted", "partial", "running", "read_unknown", "submission_claimed"})  # Runs.
    PROBLEM_STATES = frozenset({"failed", "rejected", "submission_unknown", "not_submitted", "unknown"})  # Faults.
    ENDED_STATES = frozenset({"completed", "failed", "cancelled"})  # The job ran, so each device wants a reading.
    FINAL_STATES = frozenset({"cancelled", "completed", "failed", "rejected"})  # No later answer changes the child.
    SETTLED_WORDS = frozenset({"failed", "upgraded", "skipped"})  # The device left the job while the child runs.
    TARGET_FIELDS = ("mac", "name", "device_type", "model", "version_before", "version_target", "site_id")

    def __init__(self, child: Mapping[str, Any]) -> None:
        """Keep one child row and index the cloud lists that name its devices.

        Args:
            child: One durable child row of the operation record.
        """
        self._child = child  # Keep the row for the target and error reads.
        self.child_id = str(child.get("child_id") or "")  # An empty identity never matches a stored final id.
        self.site_id = str(child.get("site_id") or "")  # The access point child names no site.
        self.site_name = str(child.get("site_name") or "")  # The access point child joins every site name.
        self.state = str(child.get("status") or "unknown").strip().lower()  # The service state of the child.
        self._lists = CloudTargetLists(child.get("status_data"))  # The cloud lists of the latest read.

    @classmethod
    def children_of(cls, record: Mapping[str, Any]) -> list[OrgChildDevices]:
        """Return one reader for each valid child row of one operation record."""
        entries = record.get("children")  # The aggregate service keeps every child in plan order.
        if not isinstance(entries, list):  # A damaged record holds no readable child.
            return []  # The page shows the empty table row.
        return [cls(child) for child in entries if isinstance(child, Mapping)]  # Skip a damaged row only.

    def targets(self) -> list[dict[str, str]]:
        """Return one target record for each device of the child.

        Returns:
            The stored target records, or records built from the MAC addresses
            when the child comes from an earlier release.
        """
        stored = self._child.get("targets")  # Issue #3249: every new child stores its target records.
        if isinstance(stored, list) and stored:  # Use the full records when they exist.
            return [self._stored_target(entry) for entry in stored if isinstance(entry, Mapping)]  # Copy each one.
        macs = self._child.get("target_ids")  # An earlier access point child stores MAC addresses only.
        return [self._fallback_target(mac) for mac in macs] if isinstance(macs, list) else []  # Build each row.

    def state_of(self, mac: object) -> str:
        """Return the state word of one device."""
        listed = self._lists.word_of(mac)  # A cloud list is the most exact source.
        if listed:  # The cloud names the state of this device.
            return listed  # Show the word of that list.
        return "pending" if self.state in self.WAITING_STATES else self.state  # Otherwise follow the child.

    def failure_of(self, mac: object) -> str:
        """Return the failure reason of one device, or an empty string."""
        listed = self._lists.word_of(mac)  # Read the list word once.
        error = str(self._child.get("error") or "")  # The child error names the fault of the whole job.
        if listed == "failed":  # The cloud names this device as failed.
            return error or LISTED_FAILURE  # A fault needs words even when the child holds no error.
        if not listed and self.state in self.PROBLEM_STATES:  # The whole child failed before the device moved.
            return error  # The child error is the only known reason.
        return ""  # A device that moved without a fault shows no reason.

    def wants_version(self, mac: object) -> bool:
        """Report whether one device needs a running version reading."""
        if self.state in self.ENDED_STATES:  # The job ran, so each device shows the version it runs now.
            return True  # A device that did not move shows its old version as a mismatch.
        return self._lists.word_of(mac) in self.SETTLED_WORDS  # A running child reads a settled device only.

    def is_final(self) -> bool:
        """Report whether no later cloud answer can change the child."""
        return self.state in self.FINAL_STATES  # One read after this state completes the readings.

    def _stored_target(self, entry: Mapping[str, Any]) -> dict[str, str]:
        """Copy one stored target record into text values."""
        record = {name: str(entry.get(name) or "") for name in self.TARGET_FIELDS}  # Keep only known fields.
        record["site_id"] = record["site_id"] or self.site_id  # A site child names the site of each device.
        return record  # The row builder reads these fields.

    def _fallback_target(self, mac: object) -> dict[str, str]:
        """Build one target record from a MAC address and the stored request body."""
        record = dict.fromkeys(self.TARGET_FIELDS, "")  # An earlier record keeps no name and no old version.
        record["mac"] = str(mac or "")  # Show the address that the child stored.
        record["device_type"] = str(self._child.get("device_family") or "")  # The child names one family.
        record["version_target"] = self._body_version()  # The request body names the requested version.
        record["site_id"] = self.site_id  # An access point child names no site, so no read can find the device.
        return record  # The row builder reads these fields.

    def _body_version(self) -> str:
        """Return the requested version from the stored request body, or an empty string."""
        body = self._child.get("body")  # The aggregate service stores the exact request.
        if not isinstance(body, Mapping):  # A child with no body names no version.
            return ""  # The version check then waits.
        versions = body.get("versions")  # The organization route sends a list of version records.
        first = versions[0] if isinstance(versions, list) and versions else None  # The AP child sends one record.
        return str(first.get("version") or "") if isinstance(first, Mapping) else str(body.get("version") or "")


class OrgDeviceRows:
    """Build one public row for each device of one aggregate operation."""

    def __init__(self, record: Mapping[str, Any]) -> None:
        """Keep one operation record and its stored readings.

        Args:
            record: The durable operation record.
        """
        self._record = record  # The rows read the children and the site names.
        self._readings = StoredReadings(record)  # The running version of each device after the upgrade.
        names = record.get("site_names")  # The aggregate service stores the approved site names.
        self._site_names: Mapping[str, Any] = names if isinstance(names, Mapping) else {}  # A damaged map is empty.

    def rows(self) -> list[dict[str, str]]:
        """Return one row for each target of each child, in plan order."""
        logger.info("Build the device rows of aggregate upgrade %s", self._record.get("operation_id", ""))
        children = OrgChildDevices.children_of(self._record)  # Read each child once.
        rows = [self._row(devices, target) for devices in children for target in devices.targets()]  # One row each.
        logger.debug("The aggregate upgrade holds %s device row(s)", len(rows))  # Log the count, not the addresses.
        return rows  # The page and the poll show the same rows.

    def _row(self, devices: OrgChildDevices, target: Mapping[str, str]) -> dict[str, str]:
        """Build the public row of one device."""
        mac = target["mac"]  # The row keeps the address that the child stored.
        after = self._readings.version(mac)  # Issue #2006: the running version, never the configured version.
        return {  # The single-site table shows the same fields, with the site added.
            "child_id": devices.child_id,  # The child job that holds the device.
            "site_id": target["site_id"],  # The site of the device.
            "site_name": self._site_name(devices, target["site_id"]),  # The name that the operator chose.
            "name": target["name"],  # The device name at submission time.
            "mac": mac,  # The device address.
            "device_type": target["device_type"],  # The device family.
            "state": devices.state_of(mac),  # The state from the cloud lists.
            "version_before": target["version_before"],  # The version before the upgrade.
            "version_target": target["version_target"],  # The version that the operator requested.
            "version_after": after,  # The running version after the upgrade.
            "version_outcome": version_outcome(target["version_target"], after),  # The FR-051 check token.
            "failure_reason": devices.failure_of(mac),  # The reason of a failed device.
        }

    def _site_name(self, devices: OrgChildDevices, site_id: str) -> str:
        """Return the site name of one device."""
        named = self._site_names.get(site_id) if site_id else None  # The record keeps the approved names.
        if named:  # The operator chose this site by this name.
            return str(named)  # Show the approved name.
        if not site_id or site_id == devices.site_id:  # A site child names its one site.
            return devices.site_name  # Show the child name for an earlier record.
        return site_id  # The AP child joins every name, so show the identifier instead of a wrong name.
