"""Tests for the rogue DHCP scanner and its organization to site fan-out.

The scanner must query the organization first, then descend only into a site
that an organization-level result already named. A blind fan-out over every
site would issue three requests for each site, which trips the Mist rate limit
on a large organization. One failing site must never end the run.

Every test injects stand-in callables, so no test opens a network connection.
"""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace  # WHY: model Mist SDK response objects without a network request.
from typing import Any

import pytest

from src.operations.protection.security.rogue_dhcp.scanner import DEFAULT_WINDOW_DAYS, SECONDS_PER_DAY, RogueDhcpScanner

ROGUE_ALARM = {
    "type": "sw_rogue_dhcp_server_detected",
    "site_id": "site-a",
    "switches": ["544b8c167179"],
    "port_id": "ge-0/0/9.0",
    "timestamp": 1_700_000_000,
    "last_seen": 1_700_000_000,
}

ROGUE_EVENT = {
    "type": "SW_ROGUE_DHCP_SERVER_DETECTED",
    "site_id": "site-b",
    "mac": "aabbccddeeff",
    "port_id": "ge-0/0/3.0",
    "timestamp": 1_700_000_000,
}

UNRELATED_EVENT = {"type": "SW_DHCP_POOL_EXHAUSTED", "site_id": "site-z", "mac": "0011", "timestamp": 1}


class RecordingApi:
    """A stand-in API map that records every call and returns scripted pages."""

    def __init__(self, pages: dict[str, list[dict[str, Any]]] | None = None) -> None:
        """Store the scripted pages and prepare the call log."""
        self.pages = pages or {}
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.failing_sites: set[str] = set()

    def _handler(self, name: str) -> Callable[..., Any]:
        """Return a callable that records its call and returns the scripted page."""

        def call(_session: Any, **kwargs: Any) -> Any:
            self.calls.append((name, kwargs))
            site_id = kwargs.get("site_id")
            if site_id in self.failing_sites:
                raise RuntimeError(f"the site {site_id} refused the request")
            key = f"{name}:{kwargs.get('type') or kwargs.get('reason') or ''}"
            return self.pages.get(key, self.pages.get(name, []))

        return call

    def as_map(self) -> dict[str, Any]:
        """Return the callable map the scanner accepts."""
        names = ("org_alarms", "org_events", "site_alarms", "site_events", "marvis_actions", "org_sites")
        api: dict[str, Any] = {name: self._handler(name) for name in names}

        api["get_next"] = lambda _session, _response: None  # WHY: default test pages have no next response.
        return api

    def names_called(self) -> list[str]:
        """Return the endpoint name of every call in order."""
        return [name for name, _ in self.calls]

    def sites_called(self) -> list[str]:
        """Return every site identifier the fan-out queried."""
        return [kwargs["site_id"] for _, kwargs in self.calls if "site_id" in kwargs]


def build_scanner(api: RecordingApi, window_days: int = DEFAULT_WINDOW_DAYS) -> RogueDhcpScanner:
    """Return a scanner bound to the recording stand-in."""
    return RogueDhcpScanner(object(), "org-1", window_days=window_days, api=api.as_map())


def test_an_empty_organization_returns_no_finding() -> None:
    """An organization with no signal must return a clean, empty result."""
    api = RecordingApi()
    result = build_scanner(api).scan()
    assert result.finding_count == 0
    assert result.sites_queried == []


def test_an_empty_organization_never_queries_a_site() -> None:
    """FR-014 and SC-003. No named site means no site request at all."""
    api = RecordingApi()
    build_scanner(api).scan()
    assert api.sites_called() == []


def test_the_organization_runs_before_any_site() -> None:
    """FR-011. The organization pass must name the sites before the fan-out starts."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})
    build_scanner(api).scan()
    names = api.names_called()
    first_site_index = next(index for index, name in enumerate(names) if name.startswith("site_"))
    assert names.index("org_alarms") < first_site_index


def test_only_a_named_site_is_queried() -> None:
    """FR-014 and SC-003. The fan-out must skip a site that no result named."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})
    build_scanner(api).scan()
    assert set(api.sites_called()) == {"site-a"}


def test_two_named_sites_are_both_queried() -> None:
    """FR-013. Every site an organization result named must receive its own pass."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM], "org_events": [ROGUE_EVENT]})
    build_scanner(api).scan()
    assert set(api.sites_called()) == {"site-a", "site-b"}


def test_a_failing_site_does_not_end_the_run() -> None:
    """FR-025 and SC-004. One refused site must not lose the findings of the others."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM], "org_events": [ROGUE_EVENT]})
    api.failing_sites = {"site-a"}
    result = build_scanner(api).scan()
    assert "site-a" in result.sites_failed
    assert "site-b" in result.sites_queried
    assert result.finding_count > 0


def test_the_failed_site_count_reaches_the_result() -> None:
    """FR-026. An operator must learn that the result is incomplete."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})
    api.failing_sites = {"site-a"}
    assert len(build_scanner(api).scan().sites_failed) == 1


def test_the_window_spans_thirty_days_by_default() -> None:
    """FR-003. The request asks for a 30-day lookback."""
    result = build_scanner(RecordingApi()).scan()
    assert round(result.window_end - result.window_start) == DEFAULT_WINDOW_DAYS * SECONDS_PER_DAY


def test_the_window_length_is_configurable() -> None:
    """FR-003. The window length must accept an override."""
    result = build_scanner(RecordingApi(), window_days=7).scan()
    assert round(result.window_end - result.window_start) == 7 * SECONDS_PER_DAY


def test_a_window_below_one_day_is_raised_to_one_day() -> None:
    """A zero-day window would return nothing useful, so the scanner floors it."""
    result = build_scanner(RecordingApi(), window_days=0).scan()
    assert round(result.window_end - result.window_start) == SECONDS_PER_DAY


def test_every_search_sends_the_same_window() -> None:
    """One run must cover one identical span across every endpoint."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})
    build_scanner(api).scan()
    windows = {(kwargs["start"], kwargs["end"]) for _, kwargs in api.calls if "start" in kwargs}
    assert len(windows) == 1


def test_an_unrelated_dhcp_record_never_enters_the_result() -> None:
    """FR-010. A pool fault must not reach an operator as a security finding."""
    api = RecordingApi({"org_events": [UNRELATED_EVENT]})
    assert build_scanner(api).scan().finding_count == 0


def test_the_alarm_search_sends_the_catalog_type() -> None:
    """The query must name the catalog type, or Mist returns every alarm."""
    api = RecordingApi()
    build_scanner(api).scan()
    alarm_calls = [kwargs for name, kwargs in api.calls if name == "org_alarms"]
    assert alarm_calls[0]["type"] == "sw_rogue_dhcp_server_detected"


def test_the_marvis_search_sends_the_catalog_reason() -> None:
    """The Marvis query filters server side, so it must send the exact reason."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})
    build_scanner(api).scan()
    marvis_calls = [kwargs for name, kwargs in api.calls if name == "marvis_actions"]
    assert marvis_calls[0]["reason"] == "rogue_dhcp_server_detected"


def test_the_site_pass_covers_all_three_searches() -> None:
    """FR-013. A named site receives its alarms, its switch events, and its Marvis actions."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})
    build_scanner(api).scan()
    site_names = {name for name in api.names_called() if name.startswith(("site_", "marvis"))}
    assert site_names == {"site_alarms", "site_events", "marvis_actions"}


def test_the_site_name_reaches_the_finding() -> None:
    """An engineer reads a site name faster than an identifier."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM], "org_sites": [{"id": "site-a", "name": "Denver Branch"}]})
    result = build_scanner(api).scan()
    assert result.findings[0].site_name == "Denver Branch"


def test_an_unknown_site_reads_unknown() -> None:
    """A result can name a site that the site list does not hold."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM], "org_sites": []})
    assert build_scanner(api).scan().findings[0].site_name == "unknown"


def test_a_failing_site_listing_keeps_the_findings() -> None:
    """A name lookup failure must never lose a finding."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})
    api_map = api.as_map()

    def raise_error(_session: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("the site listing refused the request")

    api_map["org_sites"] = raise_error
    scanner = RogueDhcpScanner(object(), "org-1", api=api_map)
    assert scanner.scan().finding_count == 1


def test_the_source_counts_report_each_search() -> None:
    """FR-021. The operator must see which search contributed which rows."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})
    result = build_scanner(api).scan()
    assert result.source_counts["org_alarm"] >= 1


def test_the_result_states_the_marvis_scope_limit() -> None:
    """The Marvis search is site scoped, so every run must state that limit."""
    assert "site level" in build_scanner(RecordingApi()).scan().marvis_scope_note


def test_every_finding_carries_the_organization() -> None:
    """FR-015. Each row must name the organization the scan covered."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})
    assert build_scanner(api).scan().findings[0].org_id == "org-1"


def test_a_missing_next_reader_reads_a_single_page() -> None:
    """A single page remains readable when a stand-in map omits the next-page reader."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})
    api_map = api.as_map()
    del api_map["get_next"]
    scanner = RogueDhcpScanner(object(), "org-1", api=api_map)
    assert scanner.scan().finding_count == 1


@pytest.mark.parametrize("status_code", [403, 503])
def test_failed_sdk_response_is_rejected_before_pagination(status_code: int) -> None:
    """A failed response body must not enter the scanner as evidence."""
    api = RecordingApi()  # WHY: track the endpoint calls without using Mist credentials.
    api_map = api.as_map()  # WHY: replace only the response and paginator for this case.
    failed_response = SimpleNamespace(status_code=status_code, data={"results": [ROGUE_ALARM]})  # WHY: model the issue.
    next_page_calls: list[Any] = []  # WHY: prove failed first pages stop before pagination.

    api_map["org_alarms"] = lambda _session, **_kwargs: failed_response  # WHY: return a plausible alarm with an error.
    api_map["get_next"] = lambda _session, response: next_page_calls.append(response)  # WHY: track page requests.
    scanner = RogueDhcpScanner(object(), "org-1", api=api_map)  # WHY: use the mock map and no live session.
    with pytest.raises(RuntimeError, match=f"HTTP {status_code}"):  # WHY: a failed request must stop the scan.
        scanner.query_organization()  # WHY: exercise the organization request boundary.
    assert next_page_calls == []  # WHY: no failed response can trigger pagination.


@pytest.mark.parametrize("status_code", [None, "200", True, 199, 300])
def test_invalid_sdk_response_status_is_rejected(status_code: Any) -> None:
    """A missing or malformed success status must not authorize response data."""
    api = RecordingApi()  # WHY: track endpoint calls without opening a network connection.
    api_map = api.as_map()  # WHY: replace the organization response with the test payload.
    response = SimpleNamespace(status_code=status_code, data={"results": [ROGUE_ALARM]})  # WHY: model bad status.
    api_map["org_alarms"] = lambda _session, **_kwargs: response  # WHY: return untrusted response data.
    scanner = RogueDhcpScanner(object(), "org-1", api=api_map)  # WHY: bind the scanner to mocked SDK calls.
    with pytest.raises(RuntimeError, match="rejected"):  # WHY: reject any status outside integer 2xx.
        scanner.query_organization()  # WHY: stop at the first organization response.


def test_sdk_response_without_status_is_rejected() -> None:
    """A response object without a status cannot prove that the request succeeded."""
    api = RecordingApi()  # WHY: keep this test isolated from the Mist service.
    api_map = api.as_map()  # WHY: replace the organization response with a statusless object.
    response = SimpleNamespace(data={"results": [ROGUE_ALARM]})  # WHY: model a response without transport evidence.
    api_map["org_alarms"] = lambda _session, **_kwargs: response  # WHY: return the statusless response.
    scanner = RogueDhcpScanner(object(), "org-1", api=api_map)  # WHY: use only the stand-in API map.
    with pytest.raises(RuntimeError, match="invalid status type NoneType"):  # WHY: missing status must fail closed.
        scanner.query_organization()  # WHY: exercise the status validation boundary.


def test_successful_sdk_response_reaches_pagination() -> None:
    """A successful response must keep the existing finding behavior."""
    api = RecordingApi()  # WHY: keep the scanner test independent of a live organization.
    api_map = api.as_map()  # WHY: use the shared mock paginator.
    successful_response = SimpleNamespace(status_code=200, data={"results": [ROGUE_ALARM]})  # WHY: model HTTP success.
    api_map["org_alarms"] = lambda _session, **_kwargs: successful_response  # WHY: return one valid SDK response.
    scanner = RogueDhcpScanner(object(), "org-1", api=api_map)  # WHY: bind the mock response to the scanner.
    findings = scanner.query_organization()  # WHY: exercise the successful organization response.
    assert len(findings) == 1  # WHY: valid data must still produce one finding.
    assert findings[0].source == "org_alarm"  # WHY: preserve the normal source label.


def test_failed_later_sdk_page_is_rejected_before_its_records_are_returned() -> None:
    """A later HTTP 503 body must not enter the scan after a successful first page."""
    api = RecordingApi()  # WHY: use no network-backed endpoint calls.
    api_map = api.as_map()  # WHY: replace one response and the next-page callback.
    first_page = SimpleNamespace(status_code=200, data={"results": []}, next="/alarms?page=2")  # WHY: model page one.
    failed_page = SimpleNamespace(status_code=503, data={"results": [ROGUE_ALARM]}, next=None)  # WHY: model page two.
    next_page_calls: list[Any] = []  # WHY: confirm the later page was requested exactly once.

    def read_next(_session: Any, response: Any) -> Any:  # WHY: return the failed page without a live HTTP call.
        next_page_calls.append(response)  # WHY: track the successful response used to request the next page.
        return failed_page  # WHY: model a 503 response with a valid-looking alarm body.

    api_map["org_alarms"] = lambda _session, **_kwargs: first_page  # WHY: the initial request succeeds.
    api_map["get_next"] = read_next  # WHY: the fake next request returns the 503 page.
    scanner = RogueDhcpScanner(object(), "org-1", api=api_map)  # WHY: exercise only mocked SDK behavior.
    with pytest.raises(RuntimeError, match="HTTP 503"):  # WHY: reject the later error response.
        scanner.query_organization()  # WHY: exercise the organization paging path.
    assert len(next_page_calls) == 1  # WHY: prove the later response triggered status validation.


def test_successful_later_sdk_page_contributes_records() -> None:
    """A later successful page must preserve the scanner's paginated result behavior."""
    api = RecordingApi()  # WHY: keep the case independent of the Mist service.
    api_map = api.as_map()  # WHY: inject two local page responses.
    first_page = SimpleNamespace(status_code=200, data={"results": []}, next="/alarms?page=2")  # WHY: model page one.
    later_page = SimpleNamespace(status_code=200, data={"results": [ROGUE_ALARM]}, next=None)  # WHY: model page two.
    api_map["get_next"] = lambda _session, _response: later_page  # WHY: return a successful page without a request.
    scanner = RogueDhcpScanner(object(), "org-1", api=api_map)  # WHY: use only local test responses.
    records = scanner._read_pages(first_page, "org_alarms")  # WHY: verify both successful pages are collected.
    assert records == [ROGUE_ALARM]  # WHY: preserve the later valid record.


def test_later_sdk_page_with_invalid_results_is_rejected() -> None:
    """A successful status cannot authorize a malformed later page body."""
    api = RecordingApi()  # WHY: keep the malformed response local.
    api_map = api.as_map()  # WHY: inject the second page without network calls.
    first_page = SimpleNamespace(status_code=200, data={"results": []}, next="/alarms?page=2")  # WHY: model page one.
    invalid_page = SimpleNamespace(status_code=200, data={"results": "not-a-list"}, next=None)  # WHY: bad body shape.
    api_map["get_next"] = lambda _session, _response: invalid_page  # WHY: return malformed content locally.
    scanner = RogueDhcpScanner(object(), "org-1", api=api_map)  # WHY: use no Mist credentials.
    with pytest.raises(RuntimeError, match="page body type dict"):  # WHY: malformed results cannot appear clean.
        scanner._read_pages(first_page, "org_alarms")  # WHY: validate body shape for the later page.


def test_failed_site_response_is_reported_as_a_site_failure() -> None:
    """A failed site response must not add its body to the scan result."""
    api = RecordingApi({"org_alarms": [ROGUE_ALARM]})  # WHY: name one site through a successful organization alarm.
    api_map = api.as_map()  # WHY: preserve normal mock behavior for all other requests.
    failed_response = SimpleNamespace(status_code=503, data={"results": [ROGUE_ALARM]})  # WHY: model site failure.
    api_map["site_alarms"] = lambda _session, **_kwargs: failed_response  # WHY: return the failed site response.
    scanner = RogueDhcpScanner(object(), "org-1", api=api_map)  # WHY: use no live credentials.
    result = scanner.scan()  # WHY: exercise the normal site fan-out and failure report.
    assert result.sites_failed == ["site-a"]  # WHY: the failed site must be visible to the operator.
    assert "site_alarm" not in result.source_counts  # WHY: failed data cannot contribute alarm rows.


@pytest.mark.parametrize("window_days", [1, 7, 30, 90])
def test_the_window_never_ends_before_it_starts(window_days: int) -> None:
    """A window whose end precedes its start would return nothing."""
    result = build_scanner(RecordingApi(), window_days=window_days).scan()
    assert result.window_end > result.window_start


class TestTheDefaultApiMapMatchesTheInstalledSdk:
    """Prove that every endpoint the scanner names exists in the installed mistapi package.

    A stand-in map hides a typo in an endpoint path, because no test would ever
    reach the real attribute. These tests read the real map, so a rename in the
    SDK fails here instead of failing on a live organization.
    """

    @staticmethod
    def _default_map() -> dict[str, Any]:
        """Return the real callable map the scanner builds when no stand-in is given."""
        return RogueDhcpScanner._default_api()

    def test_the_map_holds_every_name_the_scan_calls(self) -> None:
        """A missing key would raise only during a live run, so pin the whole set here."""
        expected = {"org_alarms", "org_events", "site_alarms", "site_events", "marvis_actions", "org_sites", "get_next"}
        assert set(self._default_map()) == expected

    def test_every_entry_is_callable(self) -> None:
        """A wrong attribute path would yield a module, not a function."""
        assert all(callable(value) for value in self._default_map().values())

    def test_the_endpoints_carry_the_documented_names(self) -> None:
        """The SDK function names must match the Mist operation identifiers the plan cites."""
        api = self._default_map()
        assert api["org_alarms"].__name__ == "searchOrgAlarms"
        assert api["org_events"].__name__ == "searchOrgDeviceEvents"
        assert api["site_alarms"].__name__ == "searchSiteAlarms"
        assert api["site_events"].__name__ == "searchSiteDeviceEvents"
        assert api["marvis_actions"].__name__ == "searchSiteMarvisConfigActions"

    def test_a_scanner_built_without_a_stand_in_uses_the_real_map(self) -> None:
        """The production path must reach the SDK, not an empty map."""
        scanner = RogueDhcpScanner(object(), "org-1")
        assert callable(scanner._api["org_alarms"])
