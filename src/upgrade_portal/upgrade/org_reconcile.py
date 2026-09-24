"""Prove the outcome of each uncertain child job of one multi-site operation.

Why:
    Issue #3247. A child job can end in an uncertain state. The portal then
    does not know whether the cloud accepted the write. The single-site
    portal reconciles such a run from the running versions of its devices.
    The multi-site portal could not, so an uncertain child blocked the
    operation until its lease ended.

    This module reads the durable operation record and the running versions
    that the caller read. It decides one verdict for each uncertain child. It
    makes no cloud call and no write.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each verdict without a MAC address or a secret.
from collections.abc import Mapping  # Accept each stored record without a concrete type.
from dataclasses import dataclass  # Keep one uncertain child immutable.
from typing import Any  # The stored record holds JSON values of mixed types.

from src.upgrade_portal.capture.devices import normalize_device_mac  # The one MAC address rule of the portal.
from src.upgrade_portal.upgrade.gate import version_matches  # The one version check rule of FR-051.
from src.upgrade_portal.upgrade.org_devices import OrgChildDevices  # The stored targets of one child.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

UNCERTAIN_STATES = frozenset({"submission_unknown", "unknown"})  # The child states that a check can settle.
CHECK_ADVICE = "Check the Mist dashboard before you act on this child job."  # The next step of an operator.
REINSTALL_NOTE = "A device ran the target version before the upgrade, so the reading proves nothing."  # Reinstall.


@dataclass(frozen=True, slots=True)
class OrgUncertainChild:
    """Hold one uncertain child job and its stored devices.

    Attributes:
        child_id: The durable identity of the child job.
        site_name: The site name that the progress page shows.
        device_family: The device type of the child job.
        targets: The stored target records of the child job.
        evidence: The result of the last check, or None.
    """

    child_id: str  # The durable identity of the child job.
    site_name: str  # The site name that the progress page shows.
    device_family: str  # The device type of the child job.
    targets: tuple[dict[str, str], ...]  # The stored target records of the child job.
    evidence: Mapping[str, Any] | None  # The result of the last check.

    def view(self) -> dict[str, Any]:
        """Return the values that the progress page shows for this child job."""
        summary = str(self.evidence.get("summary") or "") if self.evidence is not None else ""  # The last check.
        return {  # The page shows one row for each uncertain child job.
            "child_id": self.child_id,
            "site_name": self.site_name,
            "device_family": self.device_family,
            "device_count": len(self.targets),
            "evidence": summary,
        }


class OrgReconcileCheck:
    """Decide one verdict for each uncertain child job of one operation."""

    def __init__(self, record: Mapping[str, Any]) -> None:
        """Keep the uncertain child jobs of one operation record.

        Args:
            record: The durable operation record.
        """
        self._children = self._uncertain(record)  # Read the child jobs one time.

    @staticmethod
    def _uncertain(record: Mapping[str, Any]) -> tuple[OrgUncertainChild, ...]:
        """Return each uncertain child job in plan order."""
        found: list[OrgUncertainChild] = []  # The uncertain child jobs, in plan order.
        for devices, child in OrgReconcileCheck._rows(record):  # Read each valid child row.
            if devices.state not in UNCERTAIN_STATES:  # A settled child job needs no check.
                continue  # Read the next child job.
            evidence = child.get("reconciliation")  # The result of an earlier check.
            found.append(  # Keep the stored targets for the verdict.
                OrgUncertainChild(
                    child_id=devices.child_id,
                    site_name=devices.site_name,
                    device_family=str(child.get("device_family") or ""),
                    targets=tuple(devices.targets()),
                    evidence=evidence if isinstance(evidence, Mapping) else None,
                )
            )
        return tuple(found)  # The caller reads this tuple many times.

    @staticmethod
    def _rows(record: Mapping[str, Any]) -> list[tuple[OrgChildDevices, Mapping[str, Any]]]:
        """Return each valid child row with its device reader."""
        entries = record.get("children")  # The aggregate service keeps every child in plan order.
        rows = entries if isinstance(entries, list) else []  # A damaged record holds no child.
        return [(OrgChildDevices(child), child) for child in rows if isinstance(child, Mapping)]  # Skip damage.

    def children(self) -> tuple[OrgUncertainChild, ...]:
        """Return each uncertain child job in plan order."""
        return self._children  # The tuple is immutable, so the caller cannot change it.

    def site_ids(self) -> list[str]:
        """Return each site that holds a device of an uncertain child job, in plan order."""
        ordered = [target["site_id"] for child in self._children for target in child.targets if target["site_id"]]
        return list(dict.fromkeys(ordered))  # Read each site one time.

    def readings(self, site_answers: Mapping[str, Mapping[str, str] | None]) -> dict[str, str]:
        """Return the running version of each device of an uncertain child job.

        Args:
            site_answers: The running versions of each site, or None for a failed site read.

        Returns:
            One reading for each device of a site that answered. An absent device reads as empty text.
        """
        readings: dict[str, str] = {}  # The readings that the check and the record keep.
        for child in self._children:  # Read only the devices of an uncertain child job.
            for target in child.targets:  # Each device has one site.
                answer = site_answers.get(target["site_id"])  # The answer of the device site.
                mac = normalize_device_mac(target["mac"])  # The key of the stored readings.
                if answer is not None and mac:  # A failed site read proves nothing.
                    readings[mac] = str(answer.get(mac) or "")  # An absent device reports no version.
        return readings  # The caller stores these readings.

    def verdicts(self, readings: Mapping[str, str]) -> list[dict[str, Any]]:
        """Return one verdict for each uncertain child job.

        Args:
            readings: The running version of each device, keyed by the normalized MAC address.

        Returns:
            One verdict for each uncertain child job, in plan order.
        """
        found = [self._verdict(child, readings) for child in self._children]  # One verdict for each child.
        logger.debug("The check proves %s of %s child job(s)", sum(1 for one in found if one["proven"]), len(found))
        return found  # The service stores each verdict.

    @classmethod
    def _verdict(cls, child: OrgUncertainChild, readings: Mapping[str, str]) -> dict[str, Any]:
        """Return the verdict of one uncertain child job."""
        values = [readings.get(normalize_device_mac(target["mac"]), "") for target in child.targets]  # One each.
        total = len(child.targets)  # The devices of the child job.
        matched = sum(1 for target, value in zip(child.targets, values, strict=True) if cls._matches(target, value))
        unread = sum(1 for value in values if not value)  # A device with no reading proves nothing.
        reinstall = sum(1 for target in child.targets if cls._matches(target, target["version_before"]))
        proven = total > 0 and matched == total and reinstall == 0  # Every device moved to the target version.
        return {  # The service stores these values beside the child job.
            "child_id": child.child_id,
            "proven": proven,
            "matched": matched,
            "total": total,
            "unread": unread,
            "summary": cls._summary(proven, (matched, total, unread, reinstall)),
        }

    @staticmethod
    def _matches(target: Mapping[str, str], version: str) -> bool:
        """Report whether one version equals the target version of one device."""
        return version_matches(target["version_target"], version)  # The rule of the version check column.

    @staticmethod
    def _summary(proven: bool, counts: tuple[int, int, int, int]) -> str:
        """Return the sentences that explain one verdict to the operator."""
        matched, total, unread, reinstall = counts  # The four counts of the verdict.
        if total == 0:  # A child job with no device proves nothing.
            return "The child job names no device. The portal cannot prove its outcome."
        found = f"{matched} of {total} devices run the target version."  # The first sentence of each summary.
        if proven:  # Every device moved to the target version.
            return f"{found} The portal marks this child job completed."
        if reinstall:  # A device ran the target version before the write, so the reading proves nothing.
            return f"{found} {REINSTALL_NOTE} {CHECK_ADVICE}"
        if unread:  # A device gave no reading.
            return f"{found} The portal could not read {unread} of the {total} devices. {CHECK_ADVICE}"
        return f"{found} {CHECK_ADVICE}"  # A device runs another version.
