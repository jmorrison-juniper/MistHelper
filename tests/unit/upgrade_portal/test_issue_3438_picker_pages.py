"""Unit tests of the page walk of the site picker read (issue #3438).

Why:
    The site picker read each later page through ``mistapi.get_all``. That
    helper adds a later page with no status check. A refused page added
    nothing, and the picker showed a short site list that read as whole. The
    helper kept no reason either, so the one-minute cache kept the short list.

    These tests build the real SDK answer objects of
    ``tests/support/sdk_pages.py``. The SDK then builds each next link from
    the page headers, as it does for the live cloud. No test reaches the
    network.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from typing import Any

import pytest
from mistapi.__api_response import APIResponse

from src.upgrade_portal.app.routes import select
from src.upgrade_portal.runtime.cloud_cache import CloudReadCache
from tests.support.sdk_pages import HTML_TYPE, JSON_TYPE, PagedSession, build_sdk_answer

ORG_ID = "org-3438"  # One organization for every read of this file.
PAGE_LIMIT = 1000  # The page size that the picker asks for.
SITE_TOTAL = 1002  # Two rows more than one page holds, so the cloud sends a second page.
SITE_PATHS = {"listOrgSites": "sites", "listOrgSiteStats": "stats/sites"}  # The cloud path of each picker read.
READ_NAMES = sorted(SITE_PATHS)  # Both picker reads follow the same page rules.
SHORT_READ = "page_count_mismatch"  # The reason word of a lost later page.
READ_NOT_RUN = "read_not_run"  # The reason word of a read that cannot start.


def _sites(first: int, count: int) -> list[dict[str, Any]]:
    """Return a run of site records.

    Args:
        first: The number of the first record.
        count: The number of records.

    Returns:
        One record for each number, in order.
    """
    return [{"id": f"site-{index:04d}", "name": f"Site {index:04d}"} for index in range(first, first + count)]


FIRST_ROWS = _sites(0, PAGE_LIMIT)  # The rows of page one.
SECOND_ROWS = _sites(PAGE_LIMIT, SITE_TOTAL - PAGE_LIMIT)  # The rows of page two.


def _url(name: str, page: int) -> str:
    """Return the full address of one page of one picker read.

    Args:
        name: The picker read.
        page: The page number.

    Returns:
        The address that the SDK reads the next link from.
    """
    return f"https://api.mist.com/api/v1/orgs/{ORG_ID}/{SITE_PATHS[name]}?limit={PAGE_LIMIT}&page={page}"


def _link(name: str, page: int) -> str:
    """Return the link that the SDK builds for one later page.

    Args:
        name: The picker read.
        page: The page number.

    Returns:
        The relative link that the cloud session receives.
    """
    return f"/api/v1/orgs/{ORG_ID}/{SITE_PATHS[name]}?limit={PAGE_LIMIT}&page={page}"


def _rows_page(name: str, rows: list[dict[str, Any]], page: int) -> APIResponse:
    """Build one whole JSON page with the three page headers of the cloud.

    Args:
        name: The picker read.
        rows: The rows of the page.
        page: The page number.

    Returns:
        The SDK answer for the page.
    """
    headers = {**JSON_TYPE, "X-Page-Total": str(SITE_TOTAL), "X-Page-Limit": str(PAGE_LIMIT), "X-Page-Page": str(page)}
    return build_sdk_answer(200, json.dumps(rows).encode("utf-8"), headers, _url(name, page))  # The SDK adds the link.


def _html_error(url: str) -> APIResponse:
    """Build the HTML error page that a gateway sends for a failed call.

    Args:
        url: The address of the page.

    Returns:
        The SDK answer. The SDK cannot parse the body, so it holds no data.
    """
    return build_sdk_answer(503, b"<html><body>Service Unavailable</body></html>", HTML_TYPE, url)


def _json_error(url: str) -> APIResponse:
    """Build a JSON error page with an error status.

    Args:
        url: The address of the page.

    Returns:
        The SDK answer with the error body.
    """
    return build_sdk_answer(500, b'{"detail": "internal error"}', JSON_TYPE, url)


def _json_refusal(url: str) -> APIResponse:
    """Build a JSON refusal of a first page.

    Args:
        url: The address of the page.

    Returns:
        The SDK answer with the refusal body.
    """
    return build_sdk_answer(403, b'{"detail": "forbidden"}', JSON_TYPE, url)


def _no_status(url: str) -> APIResponse:
    """Build the answer that the SDK builds after a lost connection.

    Args:
        url: The address of the page.

    Returns:
        The SDK answer with no status and no data.
    """
    return APIResponse(response=None, url=url)


def _no_list(url: str) -> APIResponse:
    """Build a page with a success status and a body that holds no list.

    Args:
        url: The address of the page.

    Returns:
        The SDK answer with a map body.
    """
    return build_sdk_answer(200, b'{"detail": "no list"}', JSON_TYPE, url)


LOST_PAGES = [  # Each way that a later page can fail, with the status that the reason must carry.
    pytest.param(_html_error, 503, id="html-error-page"),
    pytest.param(_json_error, 500, id="json-error-page"),
    pytest.param(_no_status, 0, id="no-status"),
    pytest.param(_no_list, 200, id="no-list"),
]

FAILED_FIRST_PAGES = [  # Each way that a first page can fail, with the reason and the status.
    pytest.param(_html_error, "cloud_error_status", 503, id="html-error-page"),
    pytest.param(_json_refusal, "cloud_error_status", 403, id="json-refusal"),
    pytest.param(_no_status, "read_failed", 0, id="no-status"),
    pytest.param(_no_list, "unexpected_response_shape", 200, id="unknown-shape"),
]


def _picker_warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return the warning text that the picker module wrote.

    Args:
        caplog: The log capture of the test.

    Returns:
        The message of each warning record of the picker logger.
    """
    records = [record for record in caplog.records if record.name == select.logger.name]  # The picker logger only.
    return [record.getMessage() for record in records if record.levelno >= logging.WARNING]  # Warnings and above.


def test_a_whole_read_keeps_every_row_of_both_pages(caplog: pytest.LogCaptureFixture) -> None:
    """FR-001, FR-012, SC-003: a whole read keeps every row and costs one call for each later page."""
    session = PagedSession([_rows_page("listOrgSites", SECOND_ROWS, 2)])  # The cloud answers page two.
    with caplog.at_level(logging.INFO, logger=select.logger.name):  # Capture the picker log.
        read = select.collect_pages(session, _rows_page("listOrgSites", FIRST_ROWS, 1), "listOrgSites")
    assert read.section == "listOrgSites"  # The read names itself.
    assert read.records == FIRST_ROWS + SECOND_ROWS  # Every row of both pages, in cloud order.
    assert read.partial_reasons == []  # A whole read names no fault.
    assert session.links == [_link("listOrgSites", 2)]  # One call for the one later page.
    assert _picker_warnings(caplog) == []  # A whole read writes no warning.


@pytest.mark.parametrize("name", READ_NAMES)
@pytest.mark.parametrize(("lost_page", "status"), LOST_PAGES)
def test_a_lost_second_page_keeps_the_first_page_and_names_the_page(name: str, lost_page: Any, status: int) -> None:
    """FR-001: a lost later page stops the read, keeps page one, and names the status of the lost page."""
    session = PagedSession([lost_page(_url(name, 2))])  # The cloud loses page two.
    read = select.collect_pages(session, _rows_page(name, FIRST_ROWS, 1), name)  # Walk the pages.
    assert read.records == FIRST_ROWS  # The rows of page one stay.
    assert read.partial_reasons == [{"section": name, "reason": SHORT_READ, "http_status": status}]  # One reason.
    assert session.links == [_link(name, 2)]  # The walk asked for page two one time and stopped.


@pytest.mark.parametrize(("first_page", "reason", "status"), FAILED_FIRST_PAGES)
def test_a_failed_first_page_names_the_fault(first_page: Any, reason: str, status: int) -> None:
    """FR-002: a fault of the first page gives no row and one reason that names the fault."""
    session = PagedSession([])  # No later page is planned, so a page call fails the test.
    read = select.collect_pages(session, first_page(_url("listOrgSites", 1)), "listOrgSites")  # Read page one.
    assert read.records == []  # The failed page holds no row.
    assert read.partial_reasons == [{"section": "listOrgSites", "reason": reason, "http_status": status}]
    assert session.links == []  # A failed first page asks for no later page.


def test_a_first_page_total_that_the_rows_do_not_reach_is_a_short_read() -> None:
    """FR-002: a count below the total in the body is a fault, and the rows that arrived stay."""
    rows = _sites(0, 2)  # Two rows arrive.
    body = json.dumps({"results": rows, "total": 5}).encode("utf-8")  # The body reports five rows.
    first = build_sdk_answer(200, body, JSON_TYPE, _url("listOrgSites", 1))  # One page with no page headers.
    read = select.collect_pages(PagedSession([]), first, "listOrgSites")  # Read the one page.
    assert read.records == rows  # The two rows stay.
    assert read.partial_reasons == [{"section": "listOrgSites", "reason": SHORT_READ, "http_status": 200}]


def test_the_log_names_the_read_and_the_reason_only(caplog: pytest.LogCaptureFixture) -> None:
    """FR-003: one warning names the read and the reason code, and it holds no site record."""
    session = PagedSession([_html_error(_url("listOrgSites", 2))])  # The cloud loses page two.
    with caplog.at_level(logging.INFO, logger=select.logger.name):  # Capture the picker log.
        select.collect_pages(session, _rows_page("listOrgSites", FIRST_ROWS, 1), "listOrgSites")
    warnings = _picker_warnings(caplog)  # The warnings of the picker logger.
    assert len(warnings) == 1  # One warning for one lost read.
    assert "listOrgSites" in warnings[0]  # The warning names the read.
    assert SHORT_READ in warnings[0]  # The warning names the reason code.
    assert "site-0" not in warnings[0]  # The warning holds no site identifier.
    assert "Site 0" not in warnings[0]  # The warning holds no site name.


class SiteReadsStandIn:
    """Answer page one of each picker read, and count each call."""

    def __init__(self) -> None:
        """Start with no call."""
        self.reads = 0  # The count of first-page calls.

    def listOrgSites(self, cloud_session: Any, org_id: str, limit: int) -> APIResponse:
        """Answer page one of the site read.

        Args:
            cloud_session: The session of the operator.
            org_id: The organization that the picker reads.
            limit: The page size that the picker asks for.

        Returns:
            A fresh page one.
        """
        return self._first_page("listOrgSites", cloud_session, org_id, limit)  # One rule for both reads.

    def listOrgSiteStats(self, cloud_session: Any, org_id: str, limit: int) -> APIResponse:
        """Answer page one of the device count read.

        Args:
            cloud_session: The session of the operator.
            org_id: The organization that the picker reads.
            limit: The page size that the picker asks for.

        Returns:
            A fresh page one.
        """
        return self._first_page("listOrgSiteStats", cloud_session, org_id, limit)  # One rule for both reads.

    def _first_page(self, name: str, cloud_session: Any, org_id: str, limit: int) -> APIResponse:
        """Count one call and answer a fresh page one.

        Args:
            name: The picker read.
            cloud_session: The session of the operator. The later pages use it.
            org_id: The organization that the picker reads.
            limit: The page size that the picker asks for.

        Returns:
            A fresh page one with a link to page two.
        """
        del cloud_session  # The later pages travel through the session, never through this call.
        assert org_id == ORG_ID  # The picker reads its own organization.
        assert limit == PAGE_LIMIT  # The picker asks for its full page size.
        self.reads += 1  # Count the call.
        return _rows_page(name, FIRST_ROWS, 1)  # A fresh page one for each call.


@pytest.fixture
def cloud(monkeypatch: pytest.MonkeyPatch) -> SiteReadsStandIn:
    """Route each picker read to a counting stand-in with a fresh cache.

    Args:
        monkeypatch: The pytest patch helper.

    Returns:
        The stand-in that counts each first-page call.
    """
    stand_in = SiteReadsStandIn()  # The cloud answers page one of each read.
    monkeypatch.setattr(select, "CLOUD_READ_CACHE", CloudReadCache(60, 8, lambda: 0.0))  # No state from a test.
    monkeypatch.setattr(select, "import_module", lambda module_name: stand_in)  # Each read resolves to the stand-in.
    return stand_in


def _sign_in(monkeypatch: pytest.MonkeyPatch, pages: list[APIResponse]) -> PagedSession:
    """Sign in one operator whose cloud session answers the planned later pages.

    Args:
        monkeypatch: The pytest patch helper.
        pages: The later pages, in the order that the reads ask for them.

    Returns:
        The cloud session, so the test can read each link.
    """
    session = PagedSession(pages)  # The cloud session answers the later pages.
    operator = SimpleNamespace(owner=SimpleNamespace(key="owner-3438"), cloud_session=session)  # One operator.
    monkeypatch.setattr(select.identity, "current_session", lambda: operator)  # The signed-in record.
    return session


@pytest.mark.parametrize("name", READ_NAMES)
def test_a_whole_read_is_kept_so_a_second_view_makes_no_cloud_call(
    cloud: SiteReadsStandIn, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """FR-004, SC-003: a whole read costs one call for each page, and a second view costs none."""
    session = _sign_in(monkeypatch, [_rows_page(name, SECOND_ROWS, 2)])  # The cloud answers page two one time.
    first = select.default_cloud_read(name, org_id=ORG_ID)  # The first view walks both pages.
    second = select.default_cloud_read(name, org_id=ORG_ID)  # The second view reuses the kept read.
    assert first.records == FIRST_ROWS + SECOND_ROWS  # The first view shows every row.
    assert second.records == FIRST_ROWS + SECOND_ROWS  # The second view shows the same rows.
    assert first.partial_reasons == []  # The first view names no fault.
    assert second.partial_reasons == []  # The kept read names no fault.
    assert cloud.reads == 1  # Only the first view read page one.
    assert session.links == [_link(name, 2)]  # Only the first view read page two.


@pytest.mark.parametrize("name", READ_NAMES)
def test_a_read_that_lost_a_page_is_never_kept(
    cloud: SiteReadsStandIn, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """FR-004: the next view reads the cloud again after a lost page, and it can then read the whole list."""
    session = _sign_in(monkeypatch, [_html_error(_url(name, 2)), _rows_page(name, SECOND_ROWS, 2)])  # Lost, then whole.
    lost = select.default_cloud_read(name, org_id=ORG_ID)  # The first view loses page two.
    whole = select.default_cloud_read(name, org_id=ORG_ID)  # The second view reads the cloud again.
    assert lost.records == FIRST_ROWS  # The first view keeps page one.
    assert lost.partial_reasons == [{"section": name, "reason": SHORT_READ, "http_status": 503}]  # It names the page.
    assert whole.records == FIRST_ROWS + SECOND_ROWS  # The second view shows every row.
    assert whole.partial_reasons == []  # The second view is whole.
    assert cloud.reads == 2  # Each view read page one.
    assert session.links == [_link(name, 2), _link(name, 2)]  # Each view asked for page two.


def test_a_read_with_no_session_names_read_not_run(cloud: SiteReadsStandIn, monkeypatch: pytest.MonkeyPatch) -> None:
    """A request with no signed-in operator cannot read, so the read names that fault."""
    monkeypatch.setattr(select.identity, "current_session", lambda: None)  # No operator is signed in.
    read = select.default_cloud_read("listOrgSites", org_id=ORG_ID)  # The read cannot start.
    assert read.records == []  # No row.
    assert read.partial_reasons == [{"section": "listOrgSites", "reason": READ_NOT_RUN, "http_status": 0}]
    assert cloud.reads == 0  # No cloud call.


def test_an_unknown_read_names_read_not_run(cloud: SiteReadsStandIn, monkeypatch: pytest.MonkeyPatch) -> None:
    """A read name that no cloud call owns cannot read, so the read names that fault."""
    _sign_in(monkeypatch, [])  # One operator with no planned later page.
    read = select.default_cloud_read("listOrgWidgets", org_id=ORG_ID)  # No cloud call owns this name.
    assert read.records == []  # No row.
    assert read.partial_reasons == [{"section": "listOrgWidgets", "reason": READ_NOT_RUN, "http_status": 0}]
    assert cloud.reads == 0  # No cloud call.
