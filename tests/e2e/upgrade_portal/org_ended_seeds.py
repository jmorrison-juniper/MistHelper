"""Seed the multi-site operation whose access point job ended before the cancel.

Why:
    Issue #3367. A cancel of a running operation sent a cancel request to each
    child job, also to a child job that already ended. The cancel then listed
    each upgraded access point as a cancelled device. The journey needs a
    running operation with one completed access point job and one running
    switch job. No safe browser journey reaches that mix, so the browser
    server writes the record at the start.

    The completed job holds an upgrade identifier. A cancel request for it
    would reach the stand-in cloud, so only the stored result can prove that
    the portal sent none.

    Issue #3371. After the same cancel, the operation read completed. The
    journey of that issue needs a second operation of the same shape. Each
    operation needs its own child job identifiers, because the stand-in cloud
    keeps one state for each upgrade identifier. A shared identifier lets the
    first cancel stop the job of the other operation.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each seed write without a device address or a secret.
from typing import Any  # The stored records hold JSON values of mixed types.

from tests.e2e.upgrade_portal.org_control_seeds import (
    CONTROLS_BROWSER_ID,
    CONTROLS_EMAIL,
    FIRST_AP_MAC,
    FIRST_SITE_ID,
    FIRST_SWITCH_MAC,
    NEW_VERSION,
    SECOND_AP_MAC,
    SECOND_SITE_ID,
    SITE_NAMES,
    OrgControlSeeds,
)

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

ENDED_OPERATION_ID = "org-run-e2e-ended-0001"  # The running operation that the journey cancels.
ENDED_CHILD_IDS = {  # The child job of each device family, in plan order.
    "ap": "child-e2e-ended-ap",
    "switch": "child-e2e-ended-switch",
}
MIXED_OPERATION_ID = "org-run-e2e-mixed-0001"  # Issue #3371: the operation whose state the journey reads.
MIXED_CHILD_IDS = {  # The child job of each device family, with identifiers of their own.
    "ap": "child-e2e-mixed-ap",
    "switch": "child-e2e-mixed-switch",
}
SEEDED_OPERATIONS = (  # Each operation and its child job identifiers.
    (ENDED_OPERATION_ID, ENDED_CHILD_IDS),
    (MIXED_OPERATION_ID, MIXED_CHILD_IDS),
)


class OrgEndedSeeds:
    """Build and write the operations of the ended child job journeys."""

    @staticmethod
    def access_point_child(child_id: str) -> dict[str, Any]:
        """Build the access point job of both sites, which completed before the cancel."""
        child = OrgControlSeeds.child(child_id, "ap", None, "completed")  # A final state.
        child["site_name"] = ", ".join(SITE_NAMES.values())  # The job serves both sites.
        child["target_ids"] = [FIRST_AP_MAC, SECOND_AP_MAC]  # One access point at each site.
        child["targets"] = [
            OrgControlSeeds.target(FIRST_AP_MAC, FIRST_SITE_ID, "ap", "E2E ap 1"),
            OrgControlSeeds.target(SECOND_AP_MAC, SECOND_SITE_ID, "ap", "E2E Site Two ap 1"),
        ]
        upgraded = [FIRST_AP_MAC, SECOND_AP_MAC]  # Each access point runs the new firmware.
        child["status_data"] = {"status": "completed", "targets": {"total": 2, "upgraded": upgraded, "failed": []}}
        return child  # The service never reads a final child job again.

    @staticmethod
    def switch_child(child_id: str) -> dict[str, Any]:
        """Build the running switch job of the first site."""
        switch = OrgControlSeeds.child(child_id, "switch", FIRST_SITE_ID, "running")  # A live job.
        switch["site_name"] = SITE_NAMES[FIRST_SITE_ID]  # The site that the progress page names.
        switch["target_ids"] = [FIRST_SWITCH_MAC]  # The one switch of the first site.
        switch["targets"] = [OrgControlSeeds.target(FIRST_SWITCH_MAC, FIRST_SITE_ID, "switch", "E2E switch 3")]
        switch["body"] = {"device_ids": [FIRST_SWITCH_MAC], "version": NEW_VERSION, "reboot": True}  # The plan body.
        return switch  # The status read and the cancel rebuild the plan from this row.

    @classmethod
    def record(cls, owner_key: str, operation_id: str, child_ids: dict[str, str]) -> dict[str, Any]:
        """Build the running operation with one completed child job and one running child job.

        Args:
            owner_key: The signed owner key of the controls operator.
            operation_id: The identifier of the operation.
            child_ids: The child job identifier of each device family, "ap" and "switch".

        Returns:
            The operation record in the state running.
        """
        children = [cls.access_point_child(child_ids["ap"]), cls.switch_child(child_ids["switch"])]  # Plan order.
        record = OrgControlSeeds.operation(operation_id, owner_key, children)  # One operation.
        record["state"] = "running"  # The switch job still runs, so the operation takes a cancel.
        return record  # The caller writes the record to the store.

    @classmethod
    def write(cls, upgrade: Any, identity: Any) -> bool:
        """Write each operation through the run store of the browser server.

        Args:
            upgrade: The upgrade route module, which owns `save_run`.
            identity: The identity module, which builds the owner key.

        Returns:
            True when the store accepted every operation.
        """
        owner_key = identity.build_owner(CONTROLS_EMAIL, CONTROLS_BROWSER_ID).key  # The controls operator.
        results = []  # One write result for each operation.
        for operation_id, child_ids in SEEDED_OPERATIONS:  # Each journey cancels its own operation.
            logger.info("Seed the multi-site operation %s with an ended child job", operation_id)  # Before.
            results.append(bool(upgrade.save_run(cls.record(owner_key, operation_id, child_ids))))  # One write.
        written = all(results)  # A missing seed fails its journey, so the caller logs one result.
        logger.debug("The ended child seeds report written=%s", written)  # Log after the writes.
        return written  # The caller logs the result.
