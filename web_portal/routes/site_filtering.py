"""Shared empty-site filtering for the operations portal site pickers.

Issue #3840 hid a site that holds no hardware from the operations site picker
and from the capture portal site picker. Issue #3915 extends the same rule to
the map viewer site list. This module holds the one implementation, so the two
portal routes cannot drift apart.

The filter fails open. If the portal cannot read a device count, it hides no
site, because a missing count is not proof that a site is empty.
"""

import logging  # The module reports each Mist API read and each fault.

logger = logging.getLogger(__name__)  # Name the logger for this module, so the log states the source.


class EmptySiteFilter:
    """Hide the sites that hold no hardware from one site picker."""

    SHOW_EMPTY_VALUES = ("1", "true", "yes", "on")  # The raw values that turn the filter off.

    DEVICE_COUNT_FIELD = "num_devices"  # The site statistics record usually names one total.

    DEVICE_COUNT_PARTS = ("num_ap", "num_switch", "num_gateway")  # The per-type counts.

    def __init__(self, apisession, org_id: str) -> None:
        """Hold the Mist API session and the organization that the counts come from."""
        self.apisession = apisession  # The caller owns the session, so this class only reads it.
        self.org_id = org_id  # The organization identifier scopes the statistics read.

    @classmethod
    def read_show_empty(cls, value: str | None) -> bool:
        """Return True when the request asks for the sites that hold no hardware."""
        if value is None:  # The argument is absent, so the portal hides the empty sites.
            return False
        return value.strip().casefold() in cls.SHOW_EMPTY_VALUES  # Accept the documented raw values.

    @classmethod
    def read_site_device_count(cls, record: dict) -> int:
        """Return the device count that one site statistics record names."""
        total = record.get(cls.DEVICE_COUNT_FIELD)  # The record usually names one total.
        if isinstance(total, int):  # Trust the total when the record supplies it.
            return total
        parts = [record.get(name) for name in cls.DEVICE_COUNT_PARTS]  # Fall back to the per-type counts.
        return sum(part for part in parts if isinstance(part, int))  # Ignore an absent or odd part.

    def fetch_counts(self) -> dict[str, int]:
        """Return a site identifier to device count map, or an empty map on any fault."""
        try:
            import mistapi  # Import here, so the module loads without the SDK.

            logger.info("Reading site statistics for org %s", self.org_id)  # Log before the read.
            response = mistapi.api.v1.orgs.stats.listOrgSiteStats(self.apisession, self.org_id)
            records = response.data if hasattr(response, "data") else []  # Read the rows defensively.
        except Exception as error:  # A count fault must not hide a site.
            logger.warning(
                "Could not read site statistics for org %s: %s", self.org_id, type(error).__name__
            )  # Name the fault class, so an operator can find the failing read.
            return {}  # An empty map disables the filter, so no site disappears without proof.
        counts = {
            str(row.get("id", "")): self.read_site_device_count(row) for row in records if row.get("id")
        }  # Key the map by the site identifier that the picker rows carry.
        logger.debug("Read device counts for %d sites", len(counts))  # Log after the read.
        return counts

    @staticmethod
    def drop_empty_sites(rows: list[dict], counts: dict[str, int]) -> tuple[list[dict], int]:
        """Return the sites that hold hardware, plus the count of the hidden sites."""
        if not counts:  # No count was observed, so a zero is not proof that a site is empty.
            return rows, 0
        kept = [row for row in rows if counts.get(row.get("id", ""), 0) > 0]  # Keep a proven site.
        return kept, len(rows) - len(kept)  # Name the hidden count, so the page can explain it.

    def apply(self, rows: list[dict], show_empty: bool = False) -> tuple[list[dict], int]:
        """Return the visible site rows and the hidden count for one picker."""
        if show_empty:  # The operator asked for every site, so keep them all.
            logger.debug("The request asked for every site, so the filter hid no site.")
            return rows, 0
        counts = self.fetch_counts()  # Read the device count for each site in the organization.
        kept, hidden = self.drop_empty_sites(rows, counts)  # Hide a proven empty site.
        logger.debug("Kept %d sites and hid %d empty sites", len(kept), hidden)  # Log the result.
        return kept, hidden
