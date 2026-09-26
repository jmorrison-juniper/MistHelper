"""Fix the values of the short-read site that the browser journeys of issue #3424 select.

Why:
    Issue #3424. A site inventory read can stop after the first page. The
    options page then showed the devices of that page as a complete table, and
    the save planned those devices only. The devices of the lost pages stayed
    on the old firmware, and no record named them. The stand-in cloud reads
    this site short every time, so the banner and the refusal always show.

    The browser server lists this site after every other row, so no first row
    moves, and no journey that reads the first row changes. A separate
    operator selects the site. The stored site set lasts across browser
    journeys, so the separate operator keeps the short site away from every
    other journey, also when a journey of this site fails.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

from typing import Any  # A partial reason holds JSON values of mixed types.

SHORT_SITE_ID = "88888888-8888-8888-8888-888888888888"  # A site whose read stops early. No other seed uses it.
SHORT_SITE_NAME = "E2E Short Read Site"  # The text of the site row, and the name that the banner shows.
SHORT_SITE_DEVICE_COUNT = 5  # The count of the site list. The short read finds three of the five devices.
SHORT_SITE_DIGIT = 2  # The digit that gives each device of this site its own address. The second site uses 1.
SHORT_SITE_LABEL = "Short Read"  # The word in the name of each device of this site.
SHORT_SITE_EMAIL = "e2e.short.read.operator@example.invalid"  # The journeys start no firmware, so a reserved domain.
SHORT_SITE_BROWSER_ID = "e2eBrowserIdentity0007"  # A separate browser, so no other journey shares this identity.
SHORT_SITE_REASON: dict[str, Any] = {  # The partial reason that `guard_page_count` writes for a short read.
    "section": "upgrade_inventory",  # The upgrade inventory read owns the reason.
    "reason": "page_count_mismatch",  # The row count is less than the total that the cloud reported.
    "http_status": 200,  # The cloud answered the first page.
}
