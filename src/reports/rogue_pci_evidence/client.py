"""Mist API client for the rogue wireless PCI evidence pack."""

from __future__ import annotations  # Enable modern annotation syntax.

import logging  # Log every Mist API action for operator traceability.
import time  # Sleep after the shared adaptive pacer returns a delay.
from typing import Any  # Type SDK responses and dependency seams.

import mistapi  # Use the supported Juniper Mist SDK for API reads.

from src.config.source_dependency_resolver import SourceDependencyResolver  # Resolve shared session helpers.

logger = logging.getLogger(__name__)  # Name the logger for this module.


class RoguePciEvidenceClient:
    """Read Mist data required by the rogue PCI evidence pack."""

    def __init__(
        self, apisession: Any, org_id: str, page_limit: int = 1000, deps: Any = SourceDependencyResolver
    ) -> None:
        """Store the Mist session, organization, page limit, and dependency seam."""
        self.apisession = apisession  # Keep the active Mist session for SDK calls.
        self.org_id = org_id  # Keep the organization identifier for org-scope reads.
        self.page_limit = page_limit  # Keep the shared page limit for list calls.
        self.deps = deps  # Keep the dependency seam patchable in tests.
        self._smoothed_delay: float | None = None  # Keep pacer state across site setting calls.

    def _paged(self, response: Any) -> list[dict[str, Any]]:
        """Return all rows from one Mist SDK response."""
        rows = mistapi.get_all(response=response, mist_session=self.apisession)  # Page through SDK responses.
        logger.debug("Mist API returned rows=%d", len(rows))  # Log the response row count.
        return list(rows)  # Return a mutable list for downstream tagging.

    def list_org_wlans(self) -> list[dict[str, Any]]:
        """Return all organization WLAN rows."""
        logger.info("Reading organization WLANs for rogue PCI evidence")  # Log before the API call.
        response = mistapi.api.v1.orgs.wlans.listOrgWlans(
            self.apisession, self.org_id, limit=self.page_limit
        )  # Read WLANs.
        rows = self._paged(response)  # Page all WLAN rows.
        logger.debug("Read organization WLAN rows=%d", len(rows))  # Log after the API call.
        return rows  # Return WLAN rows to the model.

    def list_org_sites(self) -> list[dict[str, Any]]:
        """Return all organization site rows."""
        logger.info("Reading organization sites for rogue PCI evidence")  # Log before the API call.
        response = mistapi.api.v1.orgs.sites.listOrgSites(
            self.apisession, self.org_id, limit=self.page_limit
        )  # Read sites.
        rows = self._paged(response)  # Page all site rows.
        logger.debug("Read organization site rows=%d", len(rows))  # Log after the API call.
        return rows  # Return site rows to the model and client.

    def _pace_site_setting(self) -> None:
        """Apply the shared adaptive pacer before one site setting read."""
        logger.info("Applying the shared pacer before a site setting read")  # Log before pacing.
        self._smoothed_delay, delay = self.deps.RateLimitingUtils.get_rate_limited_delay(
            self._smoothed_delay, self.apisession, self.deps._api_usage_cache
        )  # Ask the shared pacer.
        logger.debug("Shared pacer returned delay_seconds=%.3f", float(delay or 0.0))  # Log the selected delay.
        time.sleep(float(delay or 0.0))  # Sleep for the adaptive delay.

    def list_site_settings(self, sites: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Return one site setting record per site when Mist answers."""
        settings: dict[str, dict[str, Any]] = {}  # Collect successful settings by site id.
        for site in sites:  # Read each site setting separately for the cost contract.
            site_id = str(site.get("id", ""))  # Read the site id from the site row.
            if not site_id:  # Skip malformed site rows without an identifier.
                continue  # Continue with the next site row.
            self._pace_site_setting()  # Use the shared pacer before the API call.
            logger.info("Reading rogue settings for site %s", site_id)  # Log before the API call.
            response = mistapi.api.v1.sites.setting.getSiteSetting(self.apisession, site_id)  # Read the site setting.
            settings[site_id] = dict(getattr(response, "data", {}) or {})  # Store the setting payload by site id.
            logger.debug(
                "Read rogue settings for site %s keys=%d", site_id, len(settings[site_id])
            )  # Log after the call.
        return settings  # Return successful settings for row mapping.

    def list_site_rogue_aps(self, sites: list[dict[str, Any]], duration: str = "168h") -> list[dict[str, Any]]:
        """Return rogue AP rows for each site."""
        rows: list[dict[str, Any]] = []  # Collect tagged rogue AP rows across sites.
        for site in sites:  # Read each site's rogue AP insights.
            site_id = str(site.get("id", ""))  # Read the site identifier for the endpoint.
            site_name = str(site.get("name", "Unknown Site"))  # Read the site name for the output row.
            if not site_id:  # Skip malformed site rows.
                continue  # Continue with the next site row.
            logger.info("Reading rogue AP detections for site %s", site_id)  # Log before the API call.
            response = mistapi.api.v1.sites.insights.listSiteRogueAPs(
                self.apisession, site_id, duration=duration, limit=self.page_limit
            )  # Read rogue APs.
            site_rows = self._paged(response)  # Page all rogue AP rows for the site.
            for row in site_rows:  # Add site context to each detection row.
                row["site_id"] = site_id  # Preserve the site id in the evidence output.
                row["site_name"] = site_name  # Preserve the site name in the evidence output.
            rows.extend(site_rows)  # Add this site's rows to the aggregate.
            logger.debug("Read rogue AP rows=%d for site %s", len(site_rows), site_id)  # Log after the API call.
        return rows  # Return all tagged rogue AP rows.
