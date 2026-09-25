"""Test doubles for the multi-site phase watch of issue #3245.

Why:
    The walk tests, the view tests, and the contract tests need the same
    operation record and the same versioned store. One module holds both, so
    every test reads one record shape.

Scope:
    The store answers the two calls that the watch sends: ``read_run`` and
    ``compare_and_set_run``. The record builder writes the child job fields
    that ``src/firmware/aggregate_upgrade_service.py`` stores. It holds no
    phase rule. Every rule lives in ``src/upgrade_portal/upgrade/org_cascade``.
    Issue #3244 adds the site plan fields and a stand-in post-check taker.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Mapping
from copy import deepcopy
from typing import Any

from src.upgrade_portal.upgrade.org_cascade.record import OrgPhaseWatch
from src.upgrade_portal.upgrade.org_postcheck import PostCheckResult, PostCheckSite
from tests.support.rehearsal.harness import ORG_ID
from tests.support.rehearsal.script import TYPE_ACCESS_POINT, DeviceScript, FleetScript

logger = logging.getLogger(__name__)  # The store logs under this module.

# WHY: Two obviously fake sites. Each family spreads over both sites, so a test
# proves the read of many sites and the read of one site.
SITE_IDS: tuple[str, str] = (
    "00000000-0000-0000-0000-00000000a245",
    "00000000-0000-0000-0000-00000000b245",
)  # The plan spans two sites.

# WHY: One fixed operation key. The registry keys each thread by this value.
OPERATION_ID: str = "org-run-00000000000000000000000000003245"  # The record uses one fixed key.

# WHY: The key of the one access point child job in a status map.
AP_CHILD_KEY: str = "ap"  # The status map names the access point child job.

# WHY: Issue #3244. The post-check rows show a readable name for each site.
SITE_NAMES: dict[str, str] = {SITE_IDS[0]: "Alpha site", SITE_IDS[1]: "Bravo site"}  # One name for each site.

# WHY: Issue #3244. The compare link of each site names its pre-check key.
PRE_CAPTURE_KEYS: dict[str, str] = {
    SITE_IDS[0]: "cap-" + "a" * 32 + "-01",
    SITE_IDS[1]: "cap-" + "b" * 32 + "-01",
}  # One fixed pre-check key for each site.

# WHY: The progress text of a verified capture, as the collector writes it.
VERIFIED_TEXT: str = "The portal read the capture back and the record matches."  # The collector sentence.


class StandInPostCheckTaker:
    """Take each post-check capture in memory, and record each call (issue #3244).

    Attributes:
        mode: The post-check mode that the stage reads.
        taken: The site, the capture key, and the tier of each capture, in order.
        on_take: A test hook that runs inside each capture.
    """

    def __init__(self, mode: str = "automatic", faults: Mapping[str, Any] | None = None) -> None:
        """Keep the mode and the scripted fault of each site.

        Args:
            mode: The post-check mode, ``automatic`` or ``manual``.
            faults: For each site, an exception to raise or a failure text to answer.
        """
        self.mode = mode  # The stage holds each site in the manual mode.
        self.taken: list[tuple[str, str, int]] = []  # The record of each capture.
        self.on_take: Callable[[PostCheckSite], None] | None = None  # A test reads the store during a capture.
        self._faults = dict(faults or {})  # The scripted end of each failing site.
        self._count = 0  # The count of the capture keys so far.

    def new_capture_id(self) -> str:
        """Return a new fake capture key with the post-check ordinal."""
        self._count += 1  # Each capture gets its own key.
        return f"cap-{self._count:032x}-02"  # The shape of a real run-less key.

    def take(self, site: PostCheckSite, capture_id: str) -> PostCheckResult:
        """Record the capture, and answer its scripted end."""
        logger.info("Test taker captures site %s as %s", site.site_id, capture_id)  # The action, before it happens.
        self.taken.append((site.site_id, capture_id, site.tier))  # A test reads the order and the tier.
        if self.on_take is not None:  # A test inspects the store during the capture.
            self.on_take(site)  # The hook runs before the capture ends.
        fault = self._faults.get(site.site_id)  # The scripted end of this site, or None.
        if isinstance(fault, BaseException):  # The test asks for a fault inside the capture.
            raise fault  # The stage must turn the fault into a failed row.
        if fault is not None:  # The test asks for a capture that did not verify.
            return PostCheckResult(capture_id, False, str(fault))  # The failure text of the capture.
        return PostCheckResult(capture_id, True, VERIFIED_TEXT)  # The capture verified.


class VersionedStore:
    """Hold operation records with the compare-and-set of the run store.

    Attributes:
        writes: The count of writes that the store took.
        conflicts: The count of the next writes that must meet a conflict.
    """

    def __init__(self, *records: Mapping[str, Any]) -> None:
        """Keep a detached copy of each record.

        Args:
            *records: The operation records. Each one holds ``operation_id``.
        """
        self._records = {str(row["operation_id"]): deepcopy(dict(row)) for row in records}  # One copy for each key.
        self._guard = threading.Lock()  # The walk thread and the test thread read at the same time.
        self.writes = 0  # The count of accepted writes, which the budget tests read.
        self.conflicts = 0  # A test raises this value to make the next writes meet a conflict.
        self.watch_history: list[dict[str, Any]] = []  # The watch fields of each accepted write, in order.
        self._phase_writes: list[list[dict[str, Any]]] = []  # The phase entries of each accepted write, in order.

    def phase_history(self, name: str) -> list[dict[str, Any]]:
        """Return the entry of one phase in each accepted write, in the write order."""
        with self._guard:  # The walk thread can write at this moment.
            return [
                dict(row) for rows in self._phase_writes for row in rows if row.get("name") == name
            ]  # The caller reads copies.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return a detached copy of one record, or None when the key is absent."""
        with self._guard:  # One reader or writer at a time.
            held = self._records.get(run_id)  # The current version of the record.
            return deepcopy(held) if held is not None else None  # A copy leaves the stored record safe.

    def compare_and_set_run(self, run_id: str, expected_version: int, replacement: dict[str, Any]) -> bool:
        """Replace one record only when its version matches, as the real store does."""
        with self._guard:  # The comparison and the replacement form one action.
            held = self._records.get(run_id)  # An absent record cannot match.
            if self.conflicts > 0 and held is not None:  # The test asked for a write by another process.
                self.conflicts -= 1  # Spend one of the asked conflicts.
                held["record_version"] = int(held.get("record_version") or 0) + 1  # Another writer moved on.
                return False  # The caller must read the record again.
            if held is None or held.get("record_version") != expected_version:  # A stale caller.
                return False  # The caller must read the current record.
            self._records[run_id] = deepcopy(replacement)  # Store a detached copy.
            self.writes += 1  # Count the accepted write.
            self.watch_history.append(deepcopy(dict(replacement.get("phase_watch") or {})))  # The watch of this write.
            self._phase_writes.append(deepcopy(list(replacement.get("phases") or [])))  # The phases of this write.
            return True  # The record now holds the replacement.

    def cancel(self, run_id: str) -> None:
        """Write the cancellation request, as the cancel route does."""
        logger.info("Test store writes the cancellation request of %s", run_id)  # The action, before it happens.
        with self._guard:  # The walk thread can read at this moment.
            held = self._records[run_id]  # The test names a record that exists.
            held["cancellation"] = {"requested": True, "results": []}  # The field that the walk reads.
            held["record_version"] = int(held.get("record_version") or 0) + 1  # The route advances the version.


class OrgRecordBuilder:
    """Build one multi-site operation record from a fleet script."""

    @staticmethod
    def target(script: DeviceScript, site_id: str) -> dict[str, Any]:
        """Return one stored target in the shape of ``_target_record``."""
        return {
            "mac": script.mac,  # The address that the gate joins against a statistics record.
            "name": script.mac,  # The plan needs a name, and the address is the honest one here.
            "device_type": script.device_type,  # The family that sorts the device into one phase.
            "model": script.model,  # The value that the shipped classifier reads.
            "version_before": script.version_before,  # One half of the reboot proof.
            "version_target": script.version_after,  # The version that the reconcile step proves.
            "site_id": site_id,  # The site of the device.
        }

    @staticmethod
    def child(family: str, site_id: str | None, targets: list[dict[str, Any]], status: str) -> dict[str, Any]:
        """Return one stored child job with its targets and its state."""
        return {
            "child_id": f"child-{family}-{targets[0]['mac']}",  # A stable local identity.
            "scope": "org" if site_id is None else "site",  # The access point child job reads the organization.
            "org_id": ORG_ID,  # The parent organization.
            "site_id": site_id,  # The site of a site child job, or None.
            "device_family": family,  # The family of the child job.
            "upgrade_id": f"upgrade-{family}-{targets[0]['mac']}",  # The cloud identity after the submission.
            "status": status,  # The stored child state.
            "body": {},  # The request body. A test adds a start time.
            "targets": targets,  # The devices of the child job.
        }

    @staticmethod
    def children(fleet: FleetScript, statuses: Mapping[str, str]) -> list[dict[str, Any]]:
        """Return one child job for each gateway and switch, and one child job for every access point."""
        rows: list[dict[str, Any]] = []  # The child jobs in the plan order.
        for index, script in enumerate(fleet.scripts):  # The fleet order is gateways, switches, access points.
            site_id = SITE_IDS[index % 2]  # Spread each family over both sites.
            if script.device_type != TYPE_ACCESS_POINT:  # A site child job holds one device here.
                state = statuses.get(script.mac, "accepted")  # The cloud accepts a device by default.
                rows.append(  # The record includes this site child job.
                    OrgRecordBuilder.child(
                        script.device_type, site_id, [OrgRecordBuilder.target(script, site_id)], state
                    )
                )
        aps = [
            (index, script) for index, script in enumerate(fleet.scripts) if script.device_type == TYPE_ACCESS_POINT
        ]  # The access points share one child job.
        if aps:  # The service sends every access point in one organization child job.
            targets = [OrgRecordBuilder.target(script, SITE_IDS[index % 2]) for index, script in aps]  # Both sites.
            rows.append(  # The record includes the access point child job.
                OrgRecordBuilder.child(TYPE_ACCESS_POINT, None, targets, statuses.get(AP_CHILD_KEY, "accepted"))
            )
        return rows  # The children field of the record.

    @staticmethod
    def build(
        fleet: FleetScript, statuses: Mapping[str, str] | None = None, start_time: int | None = None
    ) -> dict[str, Any]:
        """Return one prepared operation record with the watch fields and the anchors.

        Args:
            fleet: The scripts of the devices.
            statuses: The child state for each device address, or for ``ap``.
            start_time: The scheduled start in epoch seconds, or None for an immediate start.

        Returns:
            The record that the submission leaves before the watch starts.
        """
        children = OrgRecordBuilder.children(fleet, statuses or {})  # The child jobs of the plan.
        for child in children if start_time is not None else ():  # Every child job holds the same start time.
            child["body"]["start_time"] = start_time  # The cloud field that schedules the upgrade.
        record = {
            "_key": OPERATION_ID,
            "run_id": OPERATION_ID,
            "operation_id": OPERATION_ID,
            "org_id": ORG_ID,
        }  # The record keeps one identity.
        record.update({"state": "running", "record_version": 1, "children": children})  # After the submission.
        record["cancellation"] = {"requested": False, "results": []}  # No cancellation yet.
        anchors = {  # The watch needs one anchor per device.
            script.mac: {"uptime_before": script.uptime_before, "last_seen_before": None} for script in fleet.scripts
        }
        return OrgPhaseWatch.prepared(record, anchors, "")  # The fields that the submission stores.

    @staticmethod
    def with_site_plan(record: dict[str, Any], tiers: tuple[int, int] = (2, 2)) -> dict[str, Any]:
        """Add the site fields that the start route stores, for the post-check stage (issue #3244).

        Args:
            record: The record that ``build`` returned.
            tiers: The pre-check tier of each site, in the order of ``SITE_IDS``.

        Returns:
            The same record with the site order, the site names, and the pre-check rows.
        """
        record["site_ids"] = list(SITE_IDS)  # The plan order of the sites.
        record["site_names"] = dict(SITE_NAMES)  # The readable name of each site.
        record["pre_captures"] = [
            {"site_id": site, "site_name": SITE_NAMES[site], "capture_id": PRE_CAPTURE_KEYS[site], "tier": tier}
            for site, tier in zip(SITE_IDS, tiers, strict=True)
        ]  # One verified pre-check capture for each site.
        return record  # The caller stores the record.
