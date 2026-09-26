"""Fix the values of the later-check organization that the browser journeys of issue #3439 read.

Why:
    Issue #3439. Each later site check read the site list again, and it took a
    missing site as proof that the site left the organization. A site read that
    lost a page cannot give that proof. Each later check now refuses with the
    status 503 and the code site_list_incomplete.

    The journeys need a site on page two, and a read that loses page two only
    when a journey asks for it. The cloud session of this organization answers
    both pages. A request that carries the header below loses page two. A
    journey can therefore open a page with a whole read, and then press a
    control with a lost page.

    A separate organization and a separate operator keep this switch away from
    every other journey. The stored site set lasts across browser journeys, so
    the separate operator also keeps its site set apart.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each seed write without a device address or a secret.
from typing import Any  # The cloud rows and the stored records hold JSON values of mixed types.

from tests.e2e.upgrade_portal.org_control_seeds import OrgControlSeeds  # The shared shape of a stored operation.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

LATER_CHECK_ORG_ID = "99999999-9999-9999-9999-999999993439"  # No other seed uses this organization.
LATER_CHECK_ORG_NAME = "E2E Later Check Organization"  # The heading of the site picker.
LATER_CHECK_EMAIL = "e2e.later.check.operator@example.invalid"  # The journeys write no firmware.
LATER_CHECK_BROWSER_ID = "e2eBrowserIdentity0009"  # A separate browser, so no other journey shares this identity.
LOSE_PAGE_HEADER = "X-MistHelper-E2E-Lose-Page"  # A request with this header loses page two of each site read.
LOSE_PAGE_VALUE = "1"  # The one header value that loses page two.
NORTH_ID = "99999999-0000-0000-0000-000000343901"  # The first site of page one.
NORTH_NAME = "E2E Later North"  # The name of the first site.
SOUTH_ID = "99999999-0000-0000-0000-000000343902"  # The second site of page one.
SOUTH_NAME = "E2E Later South"  # The name of the second site.
WEST_ID = "99999999-0000-0000-0000-000000343903"  # The one site of page two. A lost page loses this site.
WEST_NAME = "E2E Later West"  # The name of the site of page two.
SITE_NAMES = {NORTH_ID: NORTH_NAME, SOUTH_ID: SOUTH_NAME, WEST_ID: WEST_NAME}  # The picker names.
LATER_CHECK_SERIES = {  # The address digit and the name word of each site. Digits 1 and 2 belong to other seeds.
    NORTH_ID: (3, "Later North"),  # The inventory of the first site.
    SOUTH_ID: (4, "Later South"),  # The inventory of the second site.
    WEST_ID: (5, "Later West"),  # The inventory of the site of page two.
}
SITE_DEVICES = 3  # The stand-in inventory holds one device of each of the three types.
LATER_CHECK_TOTAL = 3  # The cloud reports three rows for each read, so a second page exists.
LATER_CHECK_LIMIT = 2  # The page size of each read. Page one holds two rows, and page two holds one row.
LATER_CHECK_HOST = "https://api.mist.com"  # The SDK builds the next link from the address of page one.
LATER_CHECK_LOST_STATUS = 503  # A gateway fault on page two.
LATER_CHECK_LOST_BODY = b"<html><body><h1>503 Service Unavailable</h1></body></html>"  # The HTML page of a gateway.
LATER_CHECK_PAGES: dict[str, tuple[list[dict[str, Any]], list[dict[str, Any]]]] = {  # The rows of both pages.
    f"/api/v1/orgs/{LATER_CHECK_ORG_ID}/sites": (  # The path of `listOrgSites`.
        [{"id": NORTH_ID, "name": NORTH_NAME}, {"id": SOUTH_ID, "name": SOUTH_NAME}],  # Page one.
        [{"id": WEST_ID, "name": WEST_NAME}],  # Page two.
    ),
    f"/api/v1/orgs/{LATER_CHECK_ORG_ID}/stats/sites": (  # The path of `listOrgSiteStats`.
        [{"id": NORTH_ID, "num_devices": SITE_DEVICES}, {"id": SOUTH_ID, "num_devices": SITE_DEVICES}],  # Page one.
        [{"id": WEST_ID, "num_devices": SITE_DEVICES}],  # Page two.
    ),
}
RETRY_OPERATION_ID = "org-run-e2e-later-check-retry-0001"  # The settled operation of the retry journey.
RETRY_CHILD_ID = "child-e2e-later-check-ap"  # The access point child job of the retry seed.
NORTH_AP_MAC = "000000000301"  # The access point of the first site. It reached the target version.
WEST_AP_MAC = "000000000501"  # The access point of the site of page two. It failed, so the retry plans it.
OLD_VERSION = "0.14.29216"  # The version that each stand-in device runs before the upgrade.
NEW_VERSION = "0.15.1"  # The target version of the seeded plan.


class LaterCheckSeeds:
    """Build and write the settled operation of the retry journey of issue #3439."""

    @staticmethod
    def access_point_child() -> dict[str, Any]:
        """Build the failed access point child job of both sites.

        Returns:
            The child job record. The access point of page two failed.
        """
        child = OrgControlSeeds.child(RETRY_CHILD_ID, "ap", None, "failed")  # The organization job of both sites.
        child["org_id"] = LATER_CHECK_ORG_ID  # The shared builder names another organization.
        child["site_name"] = f"{NORTH_NAME}, {WEST_NAME}"  # The job serves both sites.
        child["target_ids"] = [NORTH_AP_MAC, WEST_AP_MAC]  # One access point at each site.
        child["targets"] = [  # The stored targets, in the shape that the aggregate build stores.
            OrgControlSeeds.target(NORTH_AP_MAC, NORTH_ID, "ap", "E2E Later North ap 1"),  # It upgraded.
            OrgControlSeeds.target(WEST_AP_MAC, WEST_ID, "ap", "E2E Later West ap 1"),  # It failed.
        ]
        child["status_data"] = {  # The answer shape of `E2EOrgUpgradeService.status`.
            "site_upgrades": [
                {"site_id": NORTH_ID, "targets": {"upgraded": [NORTH_AP_MAC], "failed": []}},  # The first site.
                {"site_id": WEST_ID, "targets": {"upgraded": [], "failed": [WEST_AP_MAC]}},  # The site of page two.
            ]
        }
        child["error"] = "The stand-in access point job failed at one site."  # The reason of the device table.
        return child  # The caller adds the child job to the operation.

    @classmethod
    def retry_record(cls, owner_key: str) -> dict[str, Any]:
        """Build the settled operation whose retry plans the site of page two.

        Args:
            owner_key: The signed owner key of the later-check operator.

        Returns:
            The operation record in the state failed.
        """
        record = OrgControlSeeds.operation(RETRY_OPERATION_ID, owner_key, [cls.access_point_child()])  # One job.
        record["org_id"] = LATER_CHECK_ORG_ID  # The organization that the browser cookie selects.
        record["site_ids"] = [NORTH_ID, WEST_ID]  # The approved sites, in the approved order.
        record["site_names"] = {NORTH_ID: NORTH_NAME, WEST_ID: WEST_NAME}  # The device table names each site.
        record["actor_email"] = LATER_CHECK_EMAIL  # The progress page names the operator.
        record["device_versions"] = OrgControlSeeds.readings({NORTH_AP_MAC: NEW_VERSION, WEST_AP_MAC: OLD_VERSION})
        record["versions_final"] = [RETRY_CHILD_ID]  # The page reads no running version again.
        record["plan_options"] = {  # The choices of the earlier save, which the retry prefill reads.
            "selected_types": ["ap"],  # The one family of the earlier plan.
            "version_ap": NEW_VERSION,  # The access point target version.
            "strategy": "big_bang",  # One phase for every device.
            "reboot": True,  # The earlier plan asked for the reboot.
        }
        return record  # The caller writes the record to the store.

    @classmethod
    def write(cls, upgrade: Any, identity: Any) -> bool:
        """Write the settled operation through the run store of the browser server.

        Args:
            upgrade: The upgrade route module, which owns `save_run`.
            identity: The identity module, which builds the owner key.

        Returns:
            The write result of the retry seed.
        """
        owner_key = identity.build_owner(LATER_CHECK_EMAIL, LATER_CHECK_BROWSER_ID).key  # The later-check operator.
        logger.info("Seed the later-check retry operation %s", RETRY_OPERATION_ID)  # Log before the write.
        written = bool(upgrade.save_run(cls.retry_record(owner_key)))  # The settled operation.
        logger.debug("The later-check retry seed reports written=%s", written)  # Log the result after the write.
        return written  # The caller logs the result.
