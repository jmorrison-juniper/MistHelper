"""Scan one Mist organization for every rogue DHCP server signal in a window.

Why:
    A rogue DHCP server hands out wrong addresses, and a client then loses its
    gateway. Mist reports the fault in three places, and a NOC engineer must
    open each place for each site by hand. This scanner answers the question in
    one pass over the whole organization.

Fan-out rule:
    The scan queries the organization first, because the alarm search and the
    device event search both accept an organization identifier. It reads the
    site identifiers from those results. It then queries only a site that an
    organization-level result already named.

    Warning: a blind fan-out over every site would issue three requests for
    each site. On an organization with 200 sites that is 600 requests for a
    result that usually names 3 sites. The named-site rule holds the request
    count down and keeps the scan inside the Mist rate limit.

Marvis scope:
    The installed SDK exposes the Marvis config action search at site level
    only. No organization-level equivalent exists. The scan therefore reads a
    Marvis config action only for a site that an alarm or an event already
    named. The result states that limit, so an operator never reads the output
    as proof that no Marvis action exists at any other site.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the annotations in this module.

import logging  # WHY: log an action before each query and a summary after it.
import time  # WHY: build the scan window from the current epoch second.
from collections.abc import Callable  # WHY: a test injects stand-in callables instead of the SDK.
from dataclasses import dataclass, field, replace  # WHY: the result is a frozen record, and a row needs a rebuild.
from datetime import UTC, datetime  # WHY: stamp the run start as an ISO 8601 string.
from typing import Any  # WHY: the mistapi session and its responses are untyped.

import mistapi  # WHY: the SDK is a hard project dependency and holds every endpoint this scan reads.

from src.security.rogue_dhcp.records import (
    SOURCE_MARVIS_ACTION,
    SOURCE_ORG_ALARM,
    SOURCE_ORG_EVENT,
    SOURCE_SITE_ALARM,
    SOURCE_SITE_EVENT,
    UNKNOWN_SITE_NAME,
    RogueDhcpFinding,
    RogueDhcpFindingMerger,
    RogueDhcpRecordNormalizer,
)
from src.security.rogue_dhcp.signals import RogueDhcpSignalMatcher

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader filters by source.

DEFAULT_WINDOW_DAYS = 30  # WHY: the request asks for a 30-day lookback across the organization.
SECONDS_PER_DAY = 86400  # WHY: convert the window length into epoch seconds.
DEFAULT_PAGE_LIMIT = 1000  # WHY: one large page keeps each search to a single request where possible.

# WHY: the operator must know that the Marvis action search covers the named sites only.
MARVIS_SCOPE_NOTE = (
    "The Marvis config action search runs at site level only, so the scan read it for the named sites only."
)


@dataclass(frozen=True)
class RogueDhcpScanResult:
    """Everything one scan produced, including the counts that describe the run."""

    findings: list[RogueDhcpFinding]  # WHY: the merged rows that the report and the export both read.
    window_start: float  # WHY: the window start as epoch seconds, for the printed summary.
    window_end: float  # WHY: the window end as epoch seconds, for the printed summary.
    sites_queried: list[str] = field(default_factory=list)  # WHY: name each site the fan-out reached.
    sites_failed: list[str] = field(default_factory=list)  # WHY: name each site whose query raised.
    source_counts: dict[str, int] = field(default_factory=dict)  # WHY: report how many rows each search returned.
    marvis_scope_note: str = MARVIS_SCOPE_NOTE  # WHY: carry the scope limit into the report.

    @property
    def finding_count(self) -> int:
        """Return the merged row count.

        Returns:
            The number of rows the scan produced after the merge.
        """
        return len(self.findings)  # WHY: the caller reports this number in the summary line.


class RogueDhcpScanner:
    """Collect every rogue DHCP server signal in one organization and one window.

    Why:
        One class holds the fan-out order, the failure isolation, and the
        window arithmetic, so no caller has to repeat those rules.
    """

    def __init__(
        self,
        apisession: Any,
        org_id: str,
        window_days: int = DEFAULT_WINDOW_DAYS,
        api: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        """Store the session, the organization, the window, and the callables.

        Args:
            apisession: The live mistapi session.
            org_id: The organization the scan covers.
            window_days: The lookback length in days.
            api: A map of stand-in callables. Leave it unset to use the SDK.
        """
        self._apisession = apisession  # WHY: every endpoint call needs the live session.
        self._org_id = org_id  # WHY: the organization-level queries and every row carry this value.
        self._window_days = max(1, int(window_days))  # WHY: a window under one day would return nothing useful.
        self._api = api if api is not None else self._default_api()  # WHY: a test injects stand-ins with no network.
        self._window_end = time.time()  # WHY: fix one end time, so every query covers the identical window.
        self._window_start = self._window_end - (self._window_days * SECONDS_PER_DAY)  # WHY: derive the start.
        started = datetime.fromtimestamp(self._window_end, tz=UTC).isoformat()  # WHY: stamp the run once.
        self._normalizer = RogueDhcpRecordNormalizer(org_id, started, self._window_end)  # WHY: one shared builder.
        self._source_counts: dict[str, int] = {}  # WHY: count the rows each search contributed.

    @staticmethod
    def _default_api() -> dict[str, Callable[..., Any]]:
        """Return the real SDK callables the scan uses.

        Returns:
            A map from a short name to the mistapi function.
        """
        return {  # WHY: one map keeps every endpoint name in one readable place.
            "org_alarms": mistapi.api.v1.orgs.alarms.searchOrgAlarms,
            "org_events": mistapi.api.v1.orgs.devices.searchOrgDeviceEvents,
            "site_alarms": mistapi.api.v1.sites.alarms.searchSiteAlarms,
            "site_events": mistapi.api.v1.sites.devices.searchSiteDeviceEvents,
            "marvis_actions": mistapi.api.v1.sites.marvis_configs.searchSiteMarvisConfigActions,
            "org_sites": mistapi.api.v1.orgs.sites.listOrgSites,
            "get_all": mistapi.get_all,
        }

    def _read_pages(self, response: Any) -> list[dict[str, Any]]:
        """Follow every page of one search response.

        Args:
            response: The APIResponse the SDK returned.

        Returns:
            Every record across every page, or an empty list on a failure.
        """
        get_all = self._api.get("get_all")  # WHY: the paginator is injectable, so a test returns one page.
        if get_all is None:  # WHY: a stand-in map may omit the paginator.
            data = getattr(response, "data", None)  # WHY: fall back to the single page the response carries.
            return list(data) if isinstance(data, list) else []  # WHY: a non-list page names no record.
        records = get_all(response=response, mist_session=self._apisession)  # WHY: follow the next links.
        return list(records) if records else []  # WHY: the paginator returns None when it read nothing.

    def _search(self, name: str, source: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Run one search, follow its pages, and keep only the matching records.

        Args:
            name: The key of the callable in the API map.
            source: The source name recorded against each kept record.
            **kwargs: The query parameters for the endpoint.

        Returns:
            Every record that the matcher accepted.
        """
        logger.info("Rogue DHCP scan queries %s for source %s", name, source)  # WHY: action log before the call.
        call = self._api[name]  # WHY: a missing key is a programming fault, so let it raise here.
        response = call(self._apisession, **kwargs)  # WHY: the SDK takes the session as its first argument.
        records = self._read_pages(response)  # WHY: one search can span several pages.
        kept = [record for record in records if RogueDhcpSignalMatcher.matches(record)]  # WHY: drop every other row.
        self._source_counts[source] = self._source_counts.get(source, 0) + len(kept)  # WHY: report the contribution.
        logger.debug("Rogue DHCP scan read %s records=%d kept=%d", name, len(records), len(kept))
        return kept

    def _window_kwargs(self) -> dict[str, Any]:
        """Return the time and page parameters that every search shares.

        Returns:
            The start, the end, and the page limit.
        """
        return {  # WHY: one place builds the window, so every search covers the identical span.
            "start": int(self._window_start),
            "end": int(self._window_end),
            "limit": DEFAULT_PAGE_LIMIT,
        }

    def query_organization(self) -> list[RogueDhcpFinding]:
        """Query the organization for every rogue DHCP signal in the window.

        Returns:
            One finding for each accepted organization-level record.
        """
        logger.info("Rogue DHCP scan starts at organization level org=%s", self._org_id)  # WHY: action log.
        window = self._window_kwargs()  # WHY: build the shared parameters one time.
        findings: list[RogueDhcpFinding] = []  # WHY: gather the alarm rows and the event rows together.
        alarms = self._search(  # WHY: the alarm search names the switch and the port directly.
            "org_alarms",
            SOURCE_ORG_ALARM,
            org_id=self._org_id,
            type=RogueDhcpSignalMatcher.alarm_type_filter(),
            **window,
        )
        findings.extend(self._normalizer.from_alarm(record, SOURCE_ORG_ALARM) for record in alarms)
        for event_type in RogueDhcpSignalMatcher.event_type_filters():  # WHY: the event search takes one type.
            events = self._search(
                "org_events", SOURCE_ORG_EVENT, org_id=self._org_id, type=event_type, **window
            )  # WHY: one query for each catalog type the scan accepts.
            findings.extend(self._normalizer.from_device_event(record, SOURCE_ORG_EVENT) for record in events)
        logger.debug("Rogue DHCP organization pass produced findings=%d", len(findings))
        return findings

    def _site_alarm_findings(self, site_id: str, window: dict[str, Any]) -> list[RogueDhcpFinding]:
        """Read the site alarms for one site.

        Args:
            site_id: The site to query.
            window: The shared time and page parameters.

        Returns:
            One finding for each accepted alarm.
        """
        records = self._search(  # WHY: the site alarm search repeats the organization rule at site scope.
            "site_alarms",
            SOURCE_SITE_ALARM,
            site_id=site_id,
            type=RogueDhcpSignalMatcher.alarm_type_filter(),
            **window,
        )
        return [self._normalizer.from_alarm(record, SOURCE_SITE_ALARM) for record in records]

    def _site_event_findings(self, site_id: str, window: dict[str, Any]) -> list[RogueDhcpFinding]:
        """Read the switch events for one site.

        Args:
            site_id: The site to query.
            window: The shared time and page parameters.

        Returns:
            One finding for each accepted event.
        """
        findings: list[RogueDhcpFinding] = []  # WHY: the loop below runs one query for each catalog type.
        for event_type in RogueDhcpSignalMatcher.event_type_filters():  # WHY: the event search takes one type.
            records = self._search("site_events", SOURCE_SITE_EVENT, site_id=site_id, type=event_type, **window)
            findings.extend(self._normalizer.from_device_event(record, SOURCE_SITE_EVENT) for record in records)
        return findings

    def _site_marvis_findings(self, site_id: str, window: dict[str, Any]) -> list[RogueDhcpFinding]:
        """Read the Marvis config actions for one site.

        Args:
            site_id: The site to query.
            window: The shared time and page parameters.

        Returns:
            One finding for each accepted Marvis config action.
        """
        records = self._search(  # WHY: the reason filter asks Mist to return the rogue DHCP actions only.
            "marvis_actions",
            SOURCE_MARVIS_ACTION,
            site_id=site_id,
            reason=RogueDhcpSignalMatcher.marvis_reason_filter(),
            **window,
        )
        return [self._normalizer.from_marvis_action(record, site_id) for record in records]

    def query_site(self, site_id: str) -> list[RogueDhcpFinding]:
        """Query one site for every rogue DHCP signal in the window.

        Args:
            site_id: The site the organization-level result named.

        Returns:
            One finding for each accepted site-level record.
        """
        logger.info("Rogue DHCP scan descends into site %s", site_id)  # WHY: action log before the site pass.
        window = self._window_kwargs()  # WHY: build the shared parameters one time for the three searches.
        findings = self._site_alarm_findings(site_id, window)  # WHY: the site alarms repeat the organization rule.
        findings.extend(self._site_event_findings(site_id, window))  # WHY: the switch events name the port.
        findings.extend(self._site_marvis_findings(site_id, window))  # WHY: the Marvis actions are site scoped.
        logger.debug("Rogue DHCP site pass site=%s produced findings=%d", site_id, len(findings))
        return findings

    def resolve_site_names(self, site_ids: set[str]) -> dict[str, str]:
        """Map each site identifier to its name.

        Args:
            site_ids: The identifiers the findings named.

        Returns:
            A map from identifier to name. A missing site maps to ``unknown``.
        """
        if not site_ids:  # WHY: an empty result needs no site listing call.
            return {}
        logger.info("Rogue DHCP scan resolves site names count=%d", len(site_ids))  # WHY: action log.
        try:  # WHY: a name lookup failure must not lose the findings.
            response = self._api["org_sites"](self._apisession, org_id=self._org_id, limit=DEFAULT_PAGE_LIMIT)
            rows = self._read_pages(response)  # WHY: a large organization pages its site list.
        except Exception as error:  # WHY: keep the scan alive and report the degraded name column.
            logger.warning("Rogue DHCP scan could not read the site list, names stay unknown: %s", error)
            return {}
        names = {str(row.get("id")): str(row.get("name") or UNKNOWN_SITE_NAME) for row in rows if row.get("id")}
        logger.debug("Rogue DHCP scan resolved site names known=%d", len(names))
        return names

    @staticmethod
    def _apply_site_names(findings: list[RogueDhcpFinding], names: dict[str, str]) -> list[RogueDhcpFinding]:
        """Fill the site name column on every finding.

        Args:
            findings: The merged findings.
            names: The identifier to name map.

        Returns:
            The findings with the name column filled.
        """
        return [  # WHY: a frozen record needs a rebuild to change one column.
            replace(finding, site_name=names.get(finding.site_id, UNKNOWN_SITE_NAME)) for finding in findings
        ]

    def _fan_out(self, site_ids: set[str]) -> tuple[list[RogueDhcpFinding], list[str], list[str]]:
        """Query each named site and record every failure.

        Args:
            site_ids: The sites the organization-level pass named.

        Returns:
            The site findings, the queried sites, and the failed sites.
        """
        findings: list[RogueDhcpFinding] = []  # WHY: gather every site row before the merge.
        queried: list[str] = []  # WHY: report how many sites the fan-out reached.
        failed: list[str] = []  # WHY: report which sites returned an error.
        for index, site_id in enumerate(sorted(site_ids), start=1):  # WHY: a stable order keeps the log readable.
            logger.info("Rogue DHCP scan site %d of %d id=%s", index, len(site_ids), site_id)  # WHY: progress.
            try:  # WHY: one failing site must never end the run.
                findings.extend(self.query_site(site_id))  # WHY: collect the three site searches.
                queried.append(site_id)  # WHY: record the success for the summary.
            except Exception as error:  # WHY: record the failure and continue to the next site.
                logger.error("Rogue DHCP scan failed at site %s: %s", site_id, error)  # WHY: name the failed site.
                failed.append(site_id)  # WHY: the summary reports the failed count.
        return findings, queried, failed

    def scan(self) -> RogueDhcpScanResult:
        """Run the whole scan and return one merged result.

        Returns:
            The merged findings and the counts that describe the run.
        """
        logger.info(  # WHY: action log that states the window before any query runs.
            "Rogue DHCP scan starts org=%s window_days=%d", self._org_id, self._window_days
        )
        org_findings = self.query_organization()  # WHY: the organization pass names the affected sites.
        site_ids = {finding.site_id for finding in org_findings if finding.site_id}  # WHY: query only a named site.
        site_findings, queried, failed = self._fan_out(site_ids)  # WHY: descend into each named site.
        merged = RogueDhcpFindingMerger.merge(org_findings + site_findings)  # WHY: one row for one real event.
        named = self._apply_site_names(merged, self.resolve_site_names(site_ids))  # WHY: fill the readable name.
        logger.debug(  # WHY: result summary after the whole run.
            "Rogue DHCP scan finished rows=%d sites_queried=%d sites_failed=%d", len(named), len(queried), len(failed)
        )
        return RogueDhcpScanResult(
            findings=named,
            window_start=self._window_start,
            window_end=self._window_end,
            sites_queried=queried,
            sites_failed=failed,
            source_counts=dict(self._source_counts),
        )
