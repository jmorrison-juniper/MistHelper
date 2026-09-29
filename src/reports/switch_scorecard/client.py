"""Mist API client for the organization switch scorecard report."""

from __future__ import annotations  # WHY: postpone annotations for Python 3.13 runtime clarity.

import logging  # WHY: log before and after the Mist API fetch.
from collections.abc import Callable  # WHY: allow tests to pass a fake fetcher factory.
from typing import Any  # WHY: Mist API and fetcher objects are dynamic.

import mistapi  # WHY: use the installed SDK operation verified in research.

from src.api.api_data_fetcher import APIDataFetcher  # WHY: reuse the menu 15 pagination path.
from src.config.source_dependency_resolver import SourceDependencyResolver  # WHY: use the shared org/session helpers.

logger = logging.getLogger(__name__)  # WHY: name this module in scorecard logs.

SWITCH_STATS_TITLE = "Org Switch Scorecard Stats:"  # WHY: fetcher logs should name this report.
SWITCH_STATS_FILENAME = "SwitchScorecardSource.csv"  # WHY: fetcher requires a filename even for raw-row use.
SWITCH_STATS_ENDPOINT = "listOrgDevicesStats"  # WHY: endpoint name is used by tests and research.


class SwitchScorecardClient:
    """Fetch switch statistics through the shared organization device stats path."""

    def __init__(
        self,
        fetcher_factory: Callable[..., APIDataFetcher] = APIDataFetcher,
        resolver: Any = SourceDependencyResolver,
    ) -> None:
        """Capture replaceable dependencies for tests."""
        self._fetcher_factory = fetcher_factory  # WHY: tests verify parameters without network calls.
        self._resolver = resolver  # WHY: tests provide a fake organization resolver.

    def list_switch_stats(self) -> list[dict[str, Any]]:
        """Return switch statistics rows for the organization."""
        logger.info("Switch scorecard resolves the organization")  # WHY: log before shared org lookup.
        org_id = str(self._resolver.ConfigUtils.get_cached_or_prompted_org_id())  # WHY: API path needs org_id.
        logger.debug("Switch scorecard resolved org=%s", org_id)  # WHY: log lookup result without secrets.
        logger.info("Switch scorecard fetches switch stats with %s", SWITCH_STATS_ENDPOINT)  # WHY: log API action.
        fetcher = self._fetcher_factory(  # WHY: reuse APIDataFetcher pagination and retry behavior.
            title=SWITCH_STATS_TITLE,
            api_call=mistapi.api.v1.orgs.stats.listOrgDevicesStats,
            filename=SWITCH_STATS_FILENAME,
            sort_key="site_id",
            type="switch",
            duration="7d",
            limit=1000,
        )
        fetcher.org_id = org_id  # WHY: call the raw fetch path after the shared org resolution.
        success = fetcher._fetch_api_data()  # WHY: reuse the existing paginated fetch without exporting source rows.
        rows = [row for row in fetcher.rawdata if isinstance(row, dict)] if success else []  # WHY: keep valid rows.
        logger.debug("Switch scorecard fetched switch stats rows=%s", len(rows))  # WHY: log API result count.
        return rows  # WHY: the model consumes raw switch dictionaries.
