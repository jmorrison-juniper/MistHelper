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


class OrgEndedSeeds:
    """Build and write the operation of the ended child job journey."""

    @staticmethod
    def access_point_child() -> dict[str, Any]:
        """Build the access point job of both sites, which completed before the cancel."""
        child = OrgControlSeeds.child(ENDED_CHILD_IDS["ap"], "ap", None, "completed")  # A final state.
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
    def switch_child() -> dict[str, Any]:
        """Build the running switch job of the first site."""
        switch = OrgControlSeeds.child(ENDED_CHILD_IDS["switch"], "switch", FIRST_SITE_ID, "running")  # A live job.
        switch["site_name"] = SITE_NAMES[FIRST_SITE_ID]  # The site that the progress page names.
        switch["target_ids"] = [FIRST_SWITCH_MAC]  # The one switch of the first site.
        switch["targets"] = [OrgControlSeeds.target(FIRST_SWITCH_MAC, FIRST_SITE_ID, "switch", "E2E switch 3")]
        switch["body"] = {"device_ids": [FIRST_SWITCH_MAC], "version": NEW_VERSION, "reboot": True}  # The plan body.
        return switch  # The status read and the cancel rebuild the plan from this row.

    @classmethod
    def record(cls, owner_key: str) -> dict[str, Any]:
        """Build the running operation with one completed child job and one running child job.

        Args:
            owner_key: The signed owner key of the controls operator.

        Returns:
            The operation record in the state running.
        """
        children = [cls.access_point_child(), cls.switch_child()]  # The plan order of the build.
        record = OrgControlSeeds.operation(ENDED_OPERATION_ID, owner_key, children)  # One operation.
        record["state"] = "running"  # The switch job still runs, so the operation takes a cancel.
        return record  # The caller writes the record to the store.

    @classmethod
    def write(cls, upgrade: Any, identity: Any) -> bool:
        """Write the operation through the run store of the browser server.

        Args:
            upgrade: The upgrade route module, which owns `save_run`.
            identity: The identity module, which builds the owner key.

        Returns:
            The write result of the seed.
        """
        owner_key = identity.build_owner(CONTROLS_EMAIL, CONTROLS_BROWSER_ID).key  # The controls operator.
        logger.info("Seed the multi-site operation %s with an ended child job", ENDED_OPERATION_ID)  # Before.
        written = bool(upgrade.save_run(cls.record(owner_key)))  # The running operation.
        logger.debug("The ended child seed reports written=%s", written)  # Log after the write.
        return written  # The caller logs the result.
