"""Fix the values of the lost-page organization that the browser journeys of issue #3438 read.

Why:
    Issue #3438. The site picker read each list through ``mistapi.get_all``.
    That helper adds a later page with no status check. A lost later page left
    a short site list that read as whole, and a short device count list that
    showed 0 devices for a site with devices. The picker reads of this
    organization always lose page two. The browser server answers page one
    with real SDK answer objects, and it answers page two with the HTML error
    page of a gateway. The real page walk of the portal then runs.

    A separate organization and a separate operator keep the lost pages away
    from every other journey. The stored site set lasts across browser
    journeys, so the separate operator also keeps its site set apart.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

from typing import Any  # A cloud row holds JSON values of mixed types.

LOST_PAGE_ORG_ID = "99999999-9999-9999-9999-999999999999"  # No other seed uses this organization.
LOST_PAGE_ORG_NAME = "E2E Lost Page Organization"  # The heading of the site picker.
LOST_PAGE_EMAIL = "e2e.lost.page.operator@example.invalid"  # The journeys start no firmware, so a reserved domain.
LOST_PAGE_BROWSER_ID = "e2eBrowserIdentity0008"  # A separate browser, so no other journey shares this identity.
LOST_NORTH_ID = "99999999-0000-0000-0000-000000003438"  # The first site of page one.
LOST_NORTH_NAME = "E2E Lost Page North"  # The name of the first site.
LOST_NORTH_DEVICES = 3  # The device count of the first site. The stand-in inventory holds 3 devices.
LOST_SOUTH_ID = "99999999-0000-0000-0000-000000003439"  # The second site of page one.
LOST_SOUTH_NAME = "E2E Lost Page South"  # The name of the second site.
LOST_SOUTH_DEVICES = 7  # The device count of the second site.
LOST_PAGE_TOTAL = 3  # The cloud reports three rows for each read, so a second page exists.
LOST_PAGE_LIMIT = 2  # The page size of each read. Page one holds the two rows below.
LOST_PAGE_HOST = "https://api.mist.com"  # The SDK builds the next link from the address of page one.
LOST_PAGE_STATUS = 503  # A gateway fault. The SDK adds a later page with no status check.
LOST_PAGE_BODY = b"<html><body><h1>503 Service Unavailable</h1></body></html>"  # The HTML page of a gateway.
LOST_PAGE_ROWS: dict[str, list[dict[str, Any]]] = {  # The rows of page one of each picker read, by read path.
    f"/api/v1/orgs/{LOST_PAGE_ORG_ID}/sites": [  # The path of `listOrgSites`.
        {"id": LOST_NORTH_ID, "name": LOST_NORTH_NAME},  # The first site record.
        {"id": LOST_SOUTH_ID, "name": LOST_SOUTH_NAME},  # The second site record.
    ],
    f"/api/v1/orgs/{LOST_PAGE_ORG_ID}/stats/sites": [  # The path of `listOrgSiteStats`.
        {"id": LOST_NORTH_ID, "num_devices": LOST_NORTH_DEVICES},  # The device count of the first site.
        {"id": LOST_SOUTH_ID, "num_devices": LOST_SOUTH_DEVICES},  # The device count of the second site.
    ],
}
