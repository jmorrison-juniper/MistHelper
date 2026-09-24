"""Seed the two multi-site operations that the recovery journeys open.

Why:
    Issue #3247. The retry control shows only on a settled operation, and the
    check control shows only on an operation with an uncertain child job. No
    safe browser journey reaches either state, because a real failure needs a
    real fault at a real site. The browser server writes both records at the
    start, as `conftest.py` does for the single-site seeds.

    One separate operator owns both records. A retry changes the site
    selection of its operator, so a separate operator keeps every other
    browser journey unchanged.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each seed write without a device address or a secret.
from typing import Any  # The stored records hold JSON values of mixed types.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

CONTROLS_EMAIL = "e2e.controls.operator@juniper.net"  # A reachable address, so no firmware gate refuses it.
CONTROLS_BROWSER_ID = "e2eBrowserIdentity0005"  # A separate browser, so no other journey shares this identity.
RETRY_OPERATION_ID = "org-run-e2e-retry-0001"  # The settled operation of the retry journey.
RECONCILE_OPERATION_ID = "org-run-e2e-reconcile-0001"  # The operation with two uncertain child jobs.
RECONCILE_WORD = f"RECONCILE {RECONCILE_OPERATION_ID}"  # The exact typed word of the check.
ORG_ID = "11111111-1111-1111-1111-111111111111"  # The same value as `STAND_IN_ORG_ID` in `conftest.py`.
FIRST_SITE_ID = "22222222-2222-2222-2222-222222222222"  # The same value as `STAND_IN_SITE_ID`.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The same value as `SECOND_SITE_ID`.
SITE_NAMES = {FIRST_SITE_ID: "E2E Stand-In Site", SECOND_SITE_ID: "E2E Second Stand-In Site"}  # The picker names.
OLD_VERSION = "0.14.29216"  # The version that each stand-in device runs before the upgrade.
NEW_VERSION = "0.15.1"  # The target version of each seeded plan.
FIRST_AP_MAC = "000000000001"  # The access point of the first site. It reached the target version.
FIRST_SWITCH_MAC = "000000000003"  # The switch of the first site. It failed in the retry seed.
SECOND_AP_MAC = "000000000101"  # The access point of the second site. It failed in the retry seed.
SECOND_SWITCH_MAC = "000000000103"  # The switch of the second site. The check cannot prove its outcome.
RETRY_AP_CHILD_ID = "child-e2e-retry-ap"  # The access point child job of the retry seed.
RETRY_SWITCH_CHILD_ID = "child-e2e-retry-switch"  # The switch child job of the retry seed.
FIRST_UNCERTAIN_ID = "child-e2e-switch-one"  # The uncertain switch child job of the first site.
SECOND_UNCERTAIN_ID = "child-e2e-switch-two"  # The uncertain switch child job of the second site.
SEED_TIME = "2026-09-24T01:00:00+00:00"  # A fixed moment, so each run of the suite reads the same record.
CLOUD_ACCOUNT = "e2e.operator@example.invalid"  # The Mist account label that the self-read seam answers.


class OrgControlSeeds:
    """Build and write the two operations of the recovery journeys."""

    @staticmethod
    def target(mac: str, site_id: str, family: str, name: str) -> dict[str, str]:
        """Build one stored target, in the shape that the aggregate build stores.

        Args:
            mac: The MAC address of the stand-in device.
            site_id: The site that holds the device.
            family: The device type, such as ap or switch.
            name: The device name of the stand-in inventory.

        Returns:
            The stored target record.
        """
        return {
            "mac": mac,  # The key that the retry plan and the device table read.
            "name": name,  # The same name as the stand-in inventory, so the narrowed table matches.
            "device_type": family,  # The planner family.
            "model": f"E2E-{family.upper()}",  # The same model as the stand-in inventory.
            "version_before": OLD_VERSION,  # The check refuses a device that already ran the target version.
            "version_target": NEW_VERSION,  # The version that the plan requested.
            "site_id": site_id,  # The site that the retry selects again.
        }

    @staticmethod
    def child(child_id: str, family: str, site_id: str | None, status: str) -> dict[str, Any]:
        """Build the common fields of one stored child job.

        Args:
            child_id: The durable identity of the child job.
            family: The device type of the child job.
            site_id: The site of a site child job, or None for the access point job of the organization.
            status: The stored state of the child job.

        Returns:
            The child fields that every stored child job holds.
        """
        organization = site_id is None  # The access point job of the organization serves both sites.
        return {
            "child_id": child_id,  # The key of the device rows and of the check.
            "route": "upgradeOrgDevices" if organization else "upgradeSiteDevices",  # The sanctioned route.
            "scope": "org" if organization else "site",  # The same scope words as the aggregate build.
            "org_id": ORG_ID,  # The organization boundary.
            "site_id": site_id,  # The site boundary of a site child job.
            "device_family": family,  # The family that the progress page shows.
            "upgrade_id": f"{child_id}-upgrade",  # A cloud identity. No status read uses it for these states.
            "status": status,  # A final or uncertain state, so the page never reads the cloud again.
            "raw_status": 200,  # The stand-in cloud accepted the write.
            "error": None,  # The caller sets the error text of a failed child job.
            "status_data": {},  # The caller sets the target lists.
            "cancellation": None,  # No cancellation was requested.
        }

    @staticmethod
    def operation(operation_id: str, owner_key: str, children: list[dict[str, Any]]) -> dict[str, Any]:
        """Build one durable operation of the controls operator across both sites.

        Args:
            operation_id: The identity of the operation.
            owner_key: The signed owner key of the controls operator.
            children: The stored child jobs of the operation.

        Returns:
            The operation record, with no site lock.
        """
        return {
            "_key": operation_id,  # The document store reads this key directly.
            "run_id": operation_id,  # The run store keys every record by this value.
            "operation_id": operation_id,  # The multi-site routes read this identity.
            "owner": owner_key,  # Only the controls operator can open the controls.
            "org_id": ORG_ID,  # The organization that the browser cookie selects.
            "site_ids": [FIRST_SITE_ID, SECOND_SITE_ID],  # The approved sites, in the approved order.
            "site_names": dict(SITE_NAMES),  # The device table names each site.
            "request_nonce": f"{operation_id}-nonce",  # A confirmed operation holds a nonce.
            "record_version": 0,  # The first durable version. Each later change uses compare-and-set.
            "created_at": SEED_TIME,  # The history page sorts the operations by this moment.
            "updated_at": SEED_TIME,  # The progress page shows the age of the last change.
            "state": "failed",  # The caller changes the state of the uncertain seed.
            "submission_claim_id": None,  # No request holds a live submission.
            "submission_claimed_at": None,  # No claim lease exists.
            "site_locks": {},  # No lock, so the seed never blocks another browser journey.
            "children": children,  # The child jobs in plan order.
            "device_versions": {},  # The caller stores the readings of the retry seed.
            "versions_final": [],  # The caller closes the final child jobs of the retry seed.
            "errors": [],  # The child jobs keep their own error text.
            "cancellation": {"requested": False, "results": []},  # No cancellation was requested.
            "actor_email": CONTROLS_EMAIL,  # The progress page names the operator.
            "cloud_account": CLOUD_ACCOUNT,  # The progress page names the Mist account.
        }

    @classmethod
    def retry_record(cls, owner_key: str) -> dict[str, Any]:
        """Build the settled operation of the retry journey.

        Why:
            The access point of the first site reached the target version. The
            access point of the second site and the switch of the first site
            failed. A retry therefore holds two devices at two sites.

        Args:
            owner_key: The signed owner key of the controls operator.

        Returns:
            The operation record in the state failed.
        """
        access_points = cls.child(RETRY_AP_CHILD_ID, "ap", None, "failed")  # The job of both sites.
        access_points["site_name"] = ", ".join(SITE_NAMES.values())  # The job serves both sites.
        access_points["target_ids"] = [FIRST_AP_MAC, SECOND_AP_MAC]  # One access point at each site.
        access_points["targets"] = [
            cls.target(FIRST_AP_MAC, FIRST_SITE_ID, "ap", "E2E ap 1"),
            cls.target(SECOND_AP_MAC, SECOND_SITE_ID, "ap", "E2E Site Two ap 1"),
        ]
        access_points["status_data"] = {  # The answer shape of `E2EOrgUpgradeService.status`.
            "site_upgrades": [
                {"site_id": FIRST_SITE_ID, "targets": {"upgraded": [FIRST_AP_MAC], "failed": []}},
                {"site_id": SECOND_SITE_ID, "targets": {"upgraded": [], "failed": [SECOND_AP_MAC]}},
            ]
        }
        switch = cls.retry_switch_child()  # The failed switch of the first site.
        record = cls.operation(RETRY_OPERATION_ID, owner_key, [access_points, switch])  # Both child jobs.
        record["device_versions"] = cls.readings({FIRST_AP_MAC: NEW_VERSION, SECOND_AP_MAC: OLD_VERSION})
        record["device_versions"].update(cls.readings({FIRST_SWITCH_MAC: OLD_VERSION}))  # The switch did not move.
        record["versions_final"] = [RETRY_AP_CHILD_ID, RETRY_SWITCH_CHILD_ID]  # The page reads no site again.
        record["plan_options"] = cls.plan_options()  # The retry prefill reads the earlier choices.
        return record  # The caller writes the record to the store.

    @classmethod
    def retry_switch_child(cls) -> dict[str, Any]:
        """Build the failed switch child job of the first site."""
        switch = cls.child(RETRY_SWITCH_CHILD_ID, "switch", FIRST_SITE_ID, "failed")  # A final state.
        switch["site_name"] = SITE_NAMES[FIRST_SITE_ID]  # The site that the progress page names.
        switch["target_ids"] = [FIRST_SWITCH_MAC]  # The one switch of the first site.
        switch["targets"] = [cls.target(FIRST_SWITCH_MAC, FIRST_SITE_ID, "switch", "E2E switch 3")]
        switch["status_data"] = {"targets": {"failed": [FIRST_SWITCH_MAC]}}  # The cloud lists the switch as failed.
        switch["error"] = "The stand-in switch job failed."  # The failure reason of the device table.
        return switch  # The caller adds the child job to the operation.

    @staticmethod
    def readings(versions: dict[str, str]) -> dict[str, dict[str, Any]]:
        """Build one stored running version reading for each device."""
        return {mac: {"version": version, "read_at": SEED_TIME, "reads": 1} for mac, version in versions.items()}

    @staticmethod
    def plan_options() -> dict[str, Any]:
        """Return the choices of the earlier save, which the retry prefill reads."""
        return {
            "selected_types": ["ap", "switch"],  # The two families of the earlier plan.
            "version_ap": NEW_VERSION,  # The access point target version.
            "version_switch": NEW_VERSION,  # The switch target version.
            "strategy": "big_bang",  # One phase for every device.
            "reboot": True,  # Each switch reboots after the write.
        }

    @classmethod
    def reconcile_record(cls, owner_key: str) -> dict[str, Any]:
        """Build the operation with one uncertain switch child job at each site.

        Why:
            The stand-in version reader answers the target version for the
            first site and the old version for the second site. The check
            therefore proves the first child job and leaves the second one.

        Args:
            owner_key: The signed owner key of the controls operator.

        Returns:
            The operation record in the state attention_required.
        """
        children = [
            cls.uncertain_child(FIRST_UNCERTAIN_ID, FIRST_SITE_ID, FIRST_SWITCH_MAC, "E2E switch 3"),
            cls.uncertain_child(SECOND_UNCERTAIN_ID, SECOND_SITE_ID, SECOND_SWITCH_MAC, "E2E Site Two switch 3"),
        ]
        record = cls.operation(RECONCILE_OPERATION_ID, owner_key, children)  # Both uncertain child jobs.
        record["state"] = "attention_required"  # The aggregate state of an uncertain child job.
        record["plan_options"] = cls.plan_options()  # The choices of the earlier save.
        return record  # The caller writes the record to the store.

    @classmethod
    def uncertain_child(cls, child_id: str, site_id: str, mac: str, name: str) -> dict[str, Any]:
        """Build one switch child job whose submission outcome is unknown."""
        child = cls.child(child_id, "switch", site_id, "submission_unknown")  # The portal lost the cloud answer.
        child["site_name"] = SITE_NAMES[site_id]  # The site that the check control names.
        child["target_ids"] = [mac]  # The one switch of the site.
        child["targets"] = [cls.target(mac, site_id, "switch", name)]  # The check compares this target version.
        child["raw_status"] = 0  # The portal received no cloud answer.
        child["upgrade_id"] = None  # No cloud identity exists, so no status read is safe.
        child["error"] = "The portal did not receive the cloud answer."  # The reason that the page shows.
        return child  # The caller adds the child job to the operation.

    @classmethod
    def write(cls, upgrade: Any, identity: Any) -> tuple[bool, bool]:
        """Write both operations through the run store of the browser server.

        Args:
            upgrade: The upgrade route module, which owns `save_run`.
            identity: The identity module, which builds the owner key.

        Returns:
            The write result of the retry seed and of the check seed.
        """
        owner_key = identity.build_owner(CONTROLS_EMAIL, CONTROLS_BROWSER_ID).key  # The controls operator.
        logger.info("Seed the multi-site recovery operations %s and %s", RETRY_OPERATION_ID, RECONCILE_OPERATION_ID)
        retry_written = bool(upgrade.save_run(cls.retry_record(owner_key)))  # The settled operation.
        reconcile_written = bool(upgrade.save_run(cls.reconcile_record(owner_key)))  # The uncertain operation.
        logger.debug("The recovery seeds report retry=%s reconcile=%s", retry_written, reconcile_written)
        return retry_written, reconcile_written  # The caller logs both results.
