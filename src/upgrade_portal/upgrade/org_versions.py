"""Read the running version of each settled device of one multi-site operation.

Why:
    Issue #3249. The multi-site progress page shows the version that each
    device runs after the upgrade. Issue #2006 requires the running version
    from `listSiteDevicesStats`, never the configured version.

    One Mist token serves the capture portal and the operations portal, and
    the token allows 5,000 calls each hour. This module therefore reads a site
    only when a device of that site needs a reading. It reads each site at
    most one time for each refresh, for all children of that site.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each site read without a MAC address or a secret.
from collections.abc import Callable, Mapping  # Describe the reader and the stored record without concrete types.
from dataclasses import dataclass, field  # Hold the read plan and the read result as plain records.
from typing import Any  # The cloud session and the stored record hold values of mixed types.

from src.firmware.running_version import RunningFirmwareVersionResolver  # Issue #2006: the one running reader.
from src.upgrade_portal.capture.devices import normalize_device_mac  # The one MAC address rule of the portal.
from src.upgrade_portal.upgrade.gate import version_matches  # The one version check rule of FR-051.
from src.upgrade_portal.upgrade.org_devices import OrgChildDevices, StoredReadings  # The device reads of a child.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

VersionReader = Callable[[Any, str], Mapping[str, str]]  # Read the running version of each device of one site.


@dataclass(frozen=True)
class VersionReadResult:
    """Hold the readings and the final children of one refresh.

    Attributes:
        readings: The running version of each device that the refresh read.
            An empty value means that the site answered without that device.
        final_child_ids: The children that no later refresh reads again.
        sites_read: The count of site reads that the refresh made.
    """

    readings: dict[str, str]
    final_child_ids: tuple[str, ...]
    sites_read: int

    @property
    def changes(self) -> bool:
        """Report whether the operation record needs a write."""
        return bool(self.readings) or bool(self.final_child_ids)  # A refresh with no news writes nothing.


@dataclass
class ReadPlan:
    """Collect the sites that one refresh reads and the children that it closes.

    Attributes:
        wanted: The normalized MAC addresses that need a reading, for each site.
        final_sites: The sites that each final child waits for.
    """

    wanted: dict[str, set[str]] = field(default_factory=dict)
    final_sites: dict[str, set[str]] = field(default_factory=dict)

    def close_after_read(self, child_id: str) -> None:
        """Mark one final child for closing after the reads of its sites succeed."""
        self.final_sites.setdefault(child_id, set())  # A child with no needed read closes at once.

    def add(self, target: Mapping[str, str], needs_read: bool, final_child_id: str) -> None:
        """Add one readable device to the plan.

        Args:
            target: The target record of the device.
            needs_read: True when the read budget allows a read of this device now.
            final_child_id: The identity of the final child, or an empty string.
        """
        if not needs_read:  # The device holds a reading that the budget keeps.
            return  # Add no site read for this device.
        site_id = target["site_id"]  # The site read returns every device of the site.
        self.wanted.setdefault(site_id, set()).add(normalize_device_mac(target["mac"]))  # Read this device.
        if final_child_id:  # A final child closes only after the reads of its sites succeed.
            self.final_sites.setdefault(final_child_id, set()).add(site_id)  # Wait for this site.

    def final_ids(self, failed_sites: set[str]) -> tuple[str, ...]:
        """Return the final children whose every site read succeeded, in plan order."""
        return tuple(child_id for child_id, sites in self.final_sites.items() if not sites & failed_sites)


class OrgVersionRefresh:
    """Read the running versions that the device table of one operation needs."""

    RUNNING_READ_LIMIT = 2  # A running child reads one upgraded device at most two times.

    def __init__(self, reader: VersionReader) -> None:
        """Keep the site reader.

        Args:
            reader: The function that reads the running versions of one site.
        """
        self._reader = reader  # The routes inject a stand-in for the browser tests.

    @staticmethod
    def running_versions(cloud_session: Any, site_id: str) -> Mapping[str, str]:
        """Read the running version of each device of one site through the shared resolver."""
        return RunningFirmwareVersionResolver(cloud_session).fetch_site_running_versions(site_id)  # Issue #2006.

    def collect(self, cloud_session: Any, record: Mapping[str, Any]) -> VersionReadResult:
        """Read each site that the read budget allows, and report the news.

        Args:
            cloud_session: The signed cloud session of the operator.
            record: The durable operation record.

        Returns:
            The readings and the final children. The caller stores both.
        """
        logger.info("Plan the running version reads of aggregate upgrade %s", record.get("operation_id", ""))
        plan = self._plan(record)  # Decide which sites need a read before the first cloud call.
        readings, failed_sites = self._read_sites(cloud_session, plan)  # Read each needed site one time.
        result = VersionReadResult(readings, plan.final_ids(failed_sites), len(plan.wanted))  # Collect the news.
        logger.debug("Read %s site(s), %s failed", result.sites_read, len(failed_sites))  # Log the counts only.
        return result  # The routes store the readings through one write.

    def _plan(self, record: Mapping[str, Any]) -> ReadPlan:
        """Build the read plan of every child that is not closed."""
        stored = record.get("versions_final")  # The children that an earlier refresh closed.
        closed = {str(child_id) for child_id in stored} if isinstance(stored, list) else set()  # Accept a list only.
        readings = StoredReadings(record)  # The readings that earlier refreshes stored.
        plan = ReadPlan()  # Start with no site read and no final child.
        for devices in OrgChildDevices.children_of(record):  # Plan each child in plan order.
            if devices.child_id not in closed:  # A closed child never causes a read again.
                self._plan_child(plan, devices, readings)  # Add the reads of this child.
        return plan  # The caller reads each planned site.

    def _plan_child(self, plan: ReadPlan, devices: OrgChildDevices, readings: StoredReadings) -> None:
        """Add the readable devices of one child to the plan."""
        final_id = devices.child_id if devices.is_final() and devices.child_id else ""  # An empty id never closes.
        if final_id:  # No later cloud answer can change this child.
            plan.close_after_read(final_id)  # Close the child after its reads succeed.
        for target in devices.targets():  # Check each device of the child.
            if self._readable(devices, target):  # Only a device with a site and an address can have a reading.
                plan.add(target, self._needs_read(devices, target, readings, final_id), final_id)  # Apply the budget.

    @staticmethod
    def _readable(devices: OrgChildDevices, target: Mapping[str, str]) -> bool:
        """Report whether a site read can return a reading for one device."""
        if not target["site_id"] or not normalize_device_mac(target["mac"]):  # An earlier AP record names no site.
            return False  # No site read can find this device.
        return devices.wants_version(target["mac"])  # A device that did not settle needs no reading yet.

    def _needs_read(
        self, devices: OrgChildDevices, target: Mapping[str, str], readings: StoredReadings, final_id: str
    ) -> bool:
        """Apply the three read rules of the Read budget section of the specification."""
        entry = readings.entry(target["mac"])  # The reading that an earlier refresh stored.
        if entry is None:  # Rule 1: the device holds no reading yet.
            return True  # Read the device one time.
        if version_matches(target["version_target"], entry.get("version")):  # The device runs the target now.
            return False  # A match never changes, so no read can add news.
        if final_id:  # Rule 2: the child ended, and the device holds a mismatch or an empty reading.
            return True  # Read one final time before the child closes.
        state = devices.state_of(target["mac"])  # Rule 3 reads only an upgraded device of a running child.
        return state == "upgraded" and readings.reads(target["mac"]) < self.RUNNING_READ_LIMIT  # Bound the reads.

    def _read_sites(self, cloud_session: Any, plan: ReadPlan) -> tuple[dict[str, str], set[str]]:
        """Read each planned site one time and return the readings and the failed sites."""
        readings: dict[str, str] = {}  # The running version of each wanted device.
        failed_sites: set[str] = set()  # A failed site keeps its final children open.
        for site_id, macs in plan.wanted.items():  # One read serves every child of the site.
            answer = self._read_site(cloud_session, site_id)  # Read the site, or None after a failure.
            if answer is None:  # The read proves nothing, so store no reading.
                failed_sites.add(site_id)  # The next refresh reads the site again.
                continue  # Read the next site.
            readings.update({mac: answer.get(mac, "") for mac in sorted(macs)})  # An absent device reports nothing.
        return readings, failed_sites  # The caller builds the result.

    def _read_site(self, cloud_session: Any, site_id: str) -> dict[str, str] | None:
        """Read one site, and return None when the answer proves nothing."""
        logger.info("Read the running versions of site %s", site_id)  # Log before the cloud call.
        try:
            raw = self._reader(cloud_session, site_id)  # One listSiteDevicesStats read for the site.
        except Exception as error:  # Keep broad because one failed site must not stop the progress page.
            logger.warning("The running version read of site %s failed with %s", site_id, type(error).__name__)
            return None  # The next refresh reads the site again.
        answer = self._normalized(raw)  # Key each version by the normalized MAC address.
        if not answer:  # The resolver answers an empty map after a failed call, so it proves nothing.
            logger.warning("The running version read of site %s returned no device", site_id)
            return None  # The next refresh reads the site again.
        logger.debug("Site %s reports %s running version(s)", site_id, len(answer))  # Log the count only.
        return answer  # The caller copies the wanted devices.

    @staticmethod
    def _normalized(raw: object) -> dict[str, str]:
        """Key each running version by the normalized MAC address, and drop each other key."""
        if not isinstance(raw, Mapping):  # A damaged answer holds no reading.
            return {}  # The caller treats the read as failed.
        pairs = ((normalize_device_mac(key), value) for key, value in raw.items())  # A device id normalizes to "".
        return {key: str(value or "") for key, value in pairs if key}  # Keep the MAC address keys only.
