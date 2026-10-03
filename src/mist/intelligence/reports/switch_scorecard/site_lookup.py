"""Shared site-name lookup for device scorecard reports."""

from __future__ import annotations  # WHY: keep annotations import-safe during MistHelper startup.

import logging  # WHY: log the site lookup API action before and after the read.
from collections.abc import Mapping  # WHY: type the untrusted site rows from Mist.
from typing import Any  # WHY: Mist site rows can contain dynamic JSON values.

from src.mist.access.api.api_core_fetch_utils import (
    APICoreFetchUtils,
)  # WHY: reuse the existing paginated site fetch helper.

logger = logging.getLogger(__name__)  # WHY: name this helper in report logs.


class SiteNameLookup:
    """Build a site ID to site name map for scorecard enrichment."""

    @staticmethod
    def fetch(org_id: str) -> dict[str, str]:
        """Fetch organization sites and return a site ID to name lookup."""
        logger.info("Fetching site names for organization %s", org_id)  # WHY: log before the Mist API read.
        sites = APICoreFetchUtils.all_sites_with_limit(org_id)  # WHY: reuse the shared paginated listOrgSites path.
        lookup = SiteNameLookup.from_rows(sites)  # WHY: keep API fetch separate from row normalization.
        logger.debug("Fetched %d site names for organization %s", len(lookup), org_id)  # WHY: summarize the result.
        return lookup  # WHY: report builders use this to fill site_name cells.

    @staticmethod
    def from_rows(sites: list[dict[str, Any]] | list[Mapping[str, Any]]) -> dict[str, str]:
        """Return a lookup from Mist site rows."""
        lookup: dict[str, str] = {}  # WHY: collect only rows with a stable site identifier.
        for site in sites:  # WHY: inspect each returned site row once.
            site_id = str(site.get("id") or "").strip()  # WHY: the API site ID is the lookup key.
            site_name = str(site.get("name") or site_id).strip()  # WHY: site ID is safer than an empty name.
            if site_id:  # WHY: rows without IDs cannot enrich device statistics rows.
                lookup[site_id] = site_name  # WHY: later rows with the same ID replace stale names.
        return lookup  # WHY: callers need an empty map instead of a special failure value.
