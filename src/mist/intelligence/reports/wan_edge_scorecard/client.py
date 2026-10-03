"""Fetch seam for organization WAN edge gateway statistics."""

from __future__ import annotations  # Keep annotations import-safe.

import logging  # Log before and after each Mist API call.
from typing import Any  # Accept SDK response doubles in tests.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,
)  # Reuse the project runtime seams.

logger = logging.getLogger(__name__)  # Use the module name for fetch logs.


class WanEdgeGatewayStatsClient:
    """Fetch organization gateway statistics through the existing shared seam."""

    @staticmethod
    def fetch_gateway_stats(org_id: str) -> list[dict[str, Any]]:
        """Return all gateway statistics rows for the organization."""
        mh = SourceDependencyResolver  # Resolve session and SDK dependencies through the shared source seam.
        logger.info("Fetching WAN edge gateway statistics for organization %s", org_id)  # Log before SDK call.
        fetcher = mh.APIDataFetcher(  # Reuse the shared fetcher used by org device statistics exports.
            title="WAN Edge Gateway Stats:",  # Name the fetch for trace logs.
            api_call=mh.mistapi.api.v1.orgs.stats.listOrgDevicesStats,  # Reuse the existing SDK endpoint.
            filename="WanEdgeScorecardSource.csv",  # Provide a stable name for emergency-save behavior.
            sort_key="site_id",  # Keep raw rows grouped by site when the shared fetcher displays data.
            type="gateway",  # Restrict the shared endpoint to WAN gateways.
            status="all",  # Include all gateway states in the scorecard.
            fields="*",  # Request optional peer and DHCP fields when the API can return them.
            limit=1000,  # Match the existing org statistics page size.
        )
        fetcher.org_id = org_id  # Set the organization directly so the fetch-only seam does not prompt.
        fetched = fetcher._fetch_api_data()  # Reuse the existing pagination, retry, and rate-limit behavior.
        logger.debug("Fetched WAN edge gateway statistics status for organization %s: %s", org_id, fetched)  # Log.
        rows = fetcher.rawdata if fetched and isinstance(fetcher.rawdata, list) else []  # Normalize fetch result.
        logger.debug("Fetched %s WAN edge gateway statistics rows for organization %s", len(rows), org_id)  # Log count.
        return rows  # Return raw rows for pure transforms.
