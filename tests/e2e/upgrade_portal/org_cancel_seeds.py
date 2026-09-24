"""Seed the multi-site operation that the cancel outcome journey cancels.

Why:
    Issue #3246. After a cancel, the multi-site progress page shows three
    device lists for each child job. The journey needs a running access point
    job that names one rebooting access point, a running switch job, and a
    child job that the cloud refused. No safe browser journey reaches that mix,
    so the browser server writes the record at the start.

    The status stand-in answers the access point job in the nested shape of
    the real organization answer. Each site entry holds its job under the key
    "upgrade", and the second site names its access point as rebooting. The
    cancel therefore stops the first access point, and the second access point
    stays in the writing list.
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

CANCEL_OPERATION_ID = "org-run-e2e-cancel-0001"  # The running operation that the journey cancels.
CANCEL_AP_JOB_ID = "e2e-cancel-ap-job"  # The status stand-in answers this job with a reboot list.
SECOND_GATEWAY_MAC = "000000000102"  # The gateway of the second site. The cloud refused its child job.
CHILD_IDS = {  # The child job of each device family, in plan order.
    "ap": "child-e2e-cancel-ap",
    "switch": "child-e2e-cancel-switch",
    "gateway": "child-e2e-cancel-gateway",
}


class OrgCancelSeeds:
    """Build and write the operation of the cancel outcome journey."""

    @staticmethod
    def status_data(upgrade_id: str, cancelled: bool) -> dict[str, Any]:
        """Return the organization answer of the seeded access point job.

        Args:
            upgrade_id: The cloud identity of the access point job.
            cancelled: True after the journey cancelled the job.

        Returns:
            The answer in the nested shape, with the second access point rebooting.
        """
        word = "cancelled" if cancelled else "upgrading"  # A real cloud ends a cancelled job.
        first = {"id": f"{upgrade_id}-one", "status": word, "targets": {"reboot_in_progress": []}}  # It waits.
        second = {"id": f"{upgrade_id}-two", "status": word, "targets": {"reboot_in_progress": [SECOND_AP_MAC]}}
        entries = [{"site_id": FIRST_SITE_ID, "upgrade": first}, {"site_id": SECOND_SITE_ID, "upgrade": second}]
        return {"id": upgrade_id, "status": "cancelled" if cancelled else "inprogress", "upgrades": entries}

    @classmethod
    def record(cls, owner_key: str) -> dict[str, Any]:
        """Build the running operation with three child jobs.

        Args:
            owner_key: The signed owner key of the controls operator.

        Returns:
            The operation record in the state partial.
        """
        access_points = OrgControlSeeds.child(CHILD_IDS["ap"], "ap", None, "running")  # The job of both sites.
        access_points["upgrade_id"] = CANCEL_AP_JOB_ID  # The status stand-in answers this job.
        access_points["site_name"] = ", ".join(SITE_NAMES.values())  # The job serves both sites.
        access_points["target_ids"] = [FIRST_AP_MAC, SECOND_AP_MAC]  # One access point at each site.
        access_points["targets"] = [
            OrgControlSeeds.target(FIRST_AP_MAC, FIRST_SITE_ID, "ap", "E2E ap 1"),
            OrgControlSeeds.target(SECOND_AP_MAC, SECOND_SITE_ID, "ap", "E2E Site Two ap 1"),
        ]
        access_points["status_data"] = cls.status_data(CANCEL_AP_JOB_ID, False)  # The last read.
        children = [access_points, cls.switch_child(), cls.gateway_child()]  # The plan order of the build.
        record = OrgControlSeeds.operation(CANCEL_OPERATION_ID, owner_key, children)  # One operation.
        record["state"] = "partial"  # Two child jobs still run, and the cloud refused one.
        return record  # The caller writes the record to the store.

    @staticmethod
    def switch_child() -> dict[str, Any]:
        """Build the running switch child job of the first site."""
        switch = OrgControlSeeds.child(CHILD_IDS["switch"], "switch", FIRST_SITE_ID, "running")  # A live job.
        switch["site_name"] = SITE_NAMES[FIRST_SITE_ID]  # The site that the progress page names.
        switch["target_ids"] = [FIRST_SWITCH_MAC]  # The one switch of the first site.
        switch["targets"] = [OrgControlSeeds.target(FIRST_SWITCH_MAC, FIRST_SITE_ID, "switch", "E2E switch 3")]
        switch["body"] = {"device_ids": [FIRST_SWITCH_MAC], "version": NEW_VERSION, "reboot": True}  # The plan body.
        return switch  # The status read and the cancel rebuild the plan from this row.

    @staticmethod
    def gateway_child() -> dict[str, Any]:
        """Build the gateway child job of the second site, which the cloud refused."""
        gateway = OrgControlSeeds.child(CHILD_IDS["gateway"], "gateway", SECOND_SITE_ID, "rejected")  # A refusal.
        gateway["site_name"] = SITE_NAMES[SECOND_SITE_ID]  # The site that the progress page names.
        gateway["target_ids"] = [SECOND_GATEWAY_MAC]  # The one gateway of the second site.
        gateway["targets"] = [OrgControlSeeds.target(SECOND_GATEWAY_MAC, SECOND_SITE_ID, "gateway", "E2E gateway 2")]
        gateway["upgrade_id"] = None  # The cloud created no job.
        gateway["raw_status"] = 400  # A client error proves the refusal.
        gateway["error"] = "The cloud answered status 400."  # The reason that the progress page shows.
        return gateway  # The cancel has no job to stop for this child job.

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
        logger.info("Seed the multi-site cancel operation %s", CANCEL_OPERATION_ID)  # Log before the write.
        written = bool(upgrade.save_run(cls.record(owner_key)))  # The running operation.
        logger.debug("The cancel seed reports written=%s", written)  # Log after the write.
        return written  # The caller logs the result.
