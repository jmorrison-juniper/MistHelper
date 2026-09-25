"""Fix the values of the empty site that the browser journey of issue #3389 selects.

Why:
    Issue #3389. The Sites page lets an operator select a site with no device.
    The multi-site save then stops, and the refusal names that site. The
    browser server lists this site last, so no first row moves, and no journey
    that reads the first row changes.

    A separate operator selects the site. The stored site set lasts across
    browser journeys, and other journeys clear only the first two sites. The
    separate operator therefore keeps the empty site away from every other
    journey, also when this journey fails.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

EMPTY_SITE_ID = "77777777-7777-7777-7777-777777777777"  # A site that holds no device. No other seed uses it.
EMPTY_SITE_NAME = "E2E Empty Site"  # The text of the last site row, and the name that the refusal shows.
EMPTY_SITE_EMAIL = "e2e.empty.site.operator@example.invalid"  # The journey starts no firmware, so a reserved domain.
EMPTY_SITE_BROWSER_ID = "e2eBrowserIdentity0006"  # A separate browser, so no other journey shares this identity.
