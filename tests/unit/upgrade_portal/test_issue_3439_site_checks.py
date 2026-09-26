"""Unit tests of the later site checks (issue #3439).

Why:
    Each later site check reads the site list again. A read that lost a page
    left out a site that exists, and the check refused that site as unknown.
    These tests pin the new rule. A missing site of a partial list raises
    ``SiteListIncompleteError``. A missing site of a whole list keeps the
    answer of today. No test reaches the network.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import pytest
from flask import Flask

from src.upgrade_portal.app.routes import org_upgrade, select
from src.upgrade_portal.capture.devices import DeviceRead

ORG_ID = "org-3439"  # One organization for every read of this file.
NORTH = "site-3439-north"  # A site of the kept page.
SOUTH = "site-3439-south"  # A second site of the kept page.
WEST = "site-3439-west"  # A site of the lost page.
EAST = "site-3439-east"  # A second site that no page holds.
KEPT_SITES = [{"id": NORTH, "name": "North"}, {"id": SOUTH, "name": "South"}]  # The rows of page one.
LOST_PAGE = [{"section": "listOrgSites", "reason": "page_count_mismatch", "http_status": 503}]  # Page two lost.
FAILED_FIRST_PAGE = [{"section": "listOrgSites", "reason": "cloud_error_status", "http_status": 503}]  # No row.
INCOMPLETE_CODE = "site_list_incomplete"  # The fixed error code of FR-001.
INCOMPLETE_MESSAGE = (  # The fixed refusal sentence of FR-002.
    "The portal did not read the complete site list, so it cannot check your site choice. Try again."
)
INCOMPLETE_TITLE = "The portal did not read the complete site list"  # The fixed page heading of FR-002.


class SiteReader:
    """Answer each cloud read by its name, and record each call.

    Why:
        The site checks read the cloud through one seam. This stand-in answers
        the site read with one fixed value, so a test sets a whole list, a
        partial list, or a failed first page. The call log proves SC-005.
    """

    def __init__(self, site_answer: Any) -> None:
        """Keep the answer of the site read.

        Args:
            site_answer: The value that the site read returns.
        """
        self.site_answer = site_answer  # The answer of each site read.
        self.calls: list[tuple[str, dict[str, Any]]] = []  # The name and the parameters of each read.

    def __call__(self, name: str, **parameters: Any) -> Any:
        """Answer one cloud read.

        Args:
            name: The name of the cloud read.
            **parameters: The call parameters.

        Returns:
            The site answer, or a whole count read with no row.
        """
        self.calls.append((name, dict(parameters)))  # A copy stops a later edit of the caller dictionary.
        if name == "listOrgSites":  # The site read that each check makes.
            return self.site_answer  # The fixed answer of this test.
        return DeviceRead(name, [], [])  # A whole count read, because a site check reads the site records only.


@pytest.fixture
def install(monkeypatch: pytest.MonkeyPatch) -> Callable[[Any], SiteReader]:
    """Return a helper that installs one site reader for the test.

    Args:
        monkeypatch: The pytest patch helper.

    Returns:
        A function that takes the site answer and returns the installed reader.
    """

    def _install(site_answer: Any) -> SiteReader:
        """Install one stand-in reader and an empty lock index.

        Args:
            site_answer: The value that the site read returns.

        Returns:
            The installed reader, so the test can read its call log.
        """
        reader = SiteReader(site_answer)  # One reader for each test.
        monkeypatch.setattr(select, "cloud_reader", lambda: reader)  # Each check reads through the stand-in.
        monkeypatch.setattr(select, "read_site_locks", lambda org_id, site_ids: {})  # No lock store is needed.
        return reader  # The test reads the call log.

    return _install  # The test calls the helper with its answer.


def _partial(records: list[dict[str, Any]]) -> DeviceRead:
    """Return a site read that lost page two.

    Args:
        records: The rows of the kept page.

    Returns:
        The read with one partial reason.
    """
    return DeviceRead("listOrgSites", records, list(LOST_PAGE))  # A copy, so no test edits the constant.


def _whole(records: list[dict[str, Any]]) -> DeviceRead:
    """Return a whole site read.

    Args:
        records: The rows of each page.

    Returns:
        The read with no partial reason.
    """
    return DeviceRead("listOrgSites", records, [])  # No reason means a whole read.


def _check_warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return the warning text that the picker module wrote.

    Args:
        caplog: The log capture of the test.

    Returns:
        The message of each warning record of the picker logger.
    """
    records = [record for record in caplog.records if record.name == select.logger.name]  # The picker logger only.
    return [record.getMessage() for record in records if record.levelno >= logging.WARNING]  # Warnings and above.


def test_the_fixed_code_sentence_and_heading() -> None:
    """FR-001, FR-002: the code, the sentence, and the heading hold the fixed text."""
    assert select.SITE_LIST_INCOMPLETE == INCOMPLETE_CODE  # A support request quotes this code.
    assert select.SITE_LIST_INCOMPLETE_MESSAGE == INCOMPLETE_MESSAGE  # The operator reads this sentence.
    assert select.SITE_LIST_INCOMPLETE_TITLE == INCOMPLETE_TITLE  # The error page shows this heading.


def test_the_error_is_not_a_bad_option_error() -> None:
    """D2: the options save answers these four classes as a bad option, so the error subclasses none of them."""
    bad_option_classes = (TypeError, ValueError, OverflowError, RuntimeError)  # The 400 classes of the save.
    assert not issubclass(select.SiteListIncompleteError, bad_option_classes)  # The 503 answer stays.
    assert issubclass(select.SiteListIncompleteError, Exception)  # The error handler can catch it.


def test_missing_sites_keeps_the_order_of_the_request() -> None:
    """FR-001: the list names each missing site in the order of the request."""
    site_list = select.SiteList([{"site_id": NORTH}, {"site_id": SOUTH}], sites_complete=False)  # Page one only.
    assert site_list.missing_sites([WEST, NORTH, EAST]) == [WEST, EAST]  # The request order, with no listed site.


def test_missing_sites_is_empty_when_the_list_holds_each_site() -> None:
    """FR-006: a partial list that holds each named site names no missing site."""
    site_list = select.SiteList([{"site_id": NORTH}, {"site_id": SOUTH}], sites_complete=False)  # Page one only.
    assert site_list.missing_sites([SOUTH, NORTH]) == []  # Each named site is on the kept page.


def test_the_raise_rule_does_not_raise_for_a_count_of_zero() -> None:
    """FR-006: a check with no missing site passes, also for a partial list."""
    assert select.SiteListIncompleteError.raise_for_missing(0, False) is None  # No raise, and no value.


def test_the_raise_rule_does_not_raise_for_a_whole_list() -> None:
    """FR-007: a whole list proves the absence, so the caller keeps the answer of today."""
    assert select.SiteListIncompleteError.raise_for_missing(2, True) is None  # No raise, and no value.


def test_the_raise_rule_raises_and_writes_one_warning(caplog: pytest.LogCaptureFixture) -> None:
    """FR-001, FR-011: a missing site of a partial list raises, and one warning names the count only."""
    with caplog.at_level(logging.INFO, logger=select.logger.name):  # Capture the picker log.
        with pytest.raises(select.SiteListIncompleteError) as caught:  # The check must raise.
            select.SiteListIncompleteError.raise_for_missing(2, False)  # Two named sites, and a lost page.
    assert caught.value.missing_count == 2  # The handler and the log read the count.
    assert str(caught.value) == INCOMPLETE_MESSAGE  # The error text is the plain sentence.
    warnings = _check_warnings(caplog)  # The warnings of the picker logger.
    assert len(warnings) == 1  # One warning for one refusal.
    assert "2" in warnings[0]  # The warning names the count of missing sites.


def test_find_site_raises_for_a_missing_site_of_a_partial_list(install: Callable[[Any], SiteReader]) -> None:
    """FR-001: a site of the lost page is not unknown, so the check raises."""
    install(_partial(KEPT_SITES))  # The site read lost page two.
    with pytest.raises(select.SiteListIncompleteError) as caught:  # The check must raise.
        select.find_site(WEST, ORG_ID)  # West sits on the lost page.
    assert caught.value.missing_count == 1  # One named site.


def test_find_site_raises_after_a_failed_first_page(install: Callable[[Any], SiteReader]) -> None:
    """Edge case: a failed first page holds no site, so each check raises."""
    install(DeviceRead("listOrgSites", [], list(FAILED_FIRST_PAGE)))  # The first page failed.
    with pytest.raises(select.SiteListIncompleteError):  # The portal cannot tell whether the site exists.
        select.find_site(NORTH, ORG_ID)  # North exists, but the read holds no row.


def test_find_site_returns_a_listed_site_of_a_partial_list(install: Callable[[Any], SiteReader]) -> None:
    """FR-006: a site of a kept page passes the check, also after a lost page."""
    install(_partial(KEPT_SITES))  # The site read lost page two.
    assert select.find_site(NORTH, ORG_ID) == {"id": NORTH, "name": "North"}  # The record of the kept page.


def test_find_site_returns_none_for_a_missing_site_of_a_whole_list(install: Callable[[Any], SiteReader]) -> None:
    """FR-007: a whole list proves that the organization does not hold the site."""
    install(_whole(KEPT_SITES))  # The site read is whole.
    assert select.find_site(WEST, ORG_ID) is None  # The answer of today.


def test_find_site_reads_a_plain_list_as_whole(install: Callable[[Any], SiteReader]) -> None:
    """FR-007: a stand-in that answers a plain list names no fault, so the answer of today stays."""
    install(list(KEPT_SITES))  # A plain list holds no partial reason.
    assert select.find_site(WEST, ORG_ID) is None  # The answer of today.


def test_find_site_reads_the_site_list_one_time(install: Callable[[Any], SiteReader]) -> None:
    """FR-010, SC-005: the check makes the same one site read as before the change."""
    reader = install(_partial(KEPT_SITES))  # The site read lost page two.
    select.find_site(NORTH, ORG_ID)  # A listed site, so the check passes.
    assert reader.calls == [("listOrgSites", {"org_id": ORG_ID})]  # One read, with the same parameters.


def test_selected_rows_raises_for_a_missing_site_of_a_partial_list(install: Callable[[Any], SiteReader]) -> None:
    """FR-001: a selected site of the lost page is not unknown, so the plan steps raise."""
    install(_partial(KEPT_SITES))  # The site read lost page two.
    with pytest.raises(select.SiteListIncompleteError) as caught:  # The check must raise.
        org_upgrade.selected_rows(ORG_ID, [NORTH, WEST, EAST])  # West and East are not in the list.
    assert caught.value.missing_count == 2  # Two named sites are missing.


def test_selected_rows_keeps_the_order_of_the_selection(install: Callable[[Any], SiteReader]) -> None:
    """FR-006: the rows of the kept page pass in the order of the selection, also after a lost page."""
    install(_partial(KEPT_SITES))  # The site read lost page two.
    rows = org_upgrade.selected_rows(ORG_ID, [SOUTH, NORTH])  # Both sites sit on the kept page.
    assert [row["site_id"] for row in rows] == [SOUTH, NORTH]  # The order of the selection.


def test_selected_rows_returns_no_row_for_a_missing_site_of_a_whole_list(
    install: Callable[[Any], SiteReader],
) -> None:
    """FR-007: a whole list keeps the empty answer, so the plan steps keep the refusal of today."""
    install(_whole(KEPT_SITES))  # The site read is whole.
    assert org_upgrade.selected_rows(ORG_ID, [NORTH, WEST]) == []  # The answer of today.


def test_selected_rows_reads_each_list_one_time(install: Callable[[Any], SiteReader]) -> None:
    """FR-010, SC-005: the plan steps make the same two reads as before the change."""
    reader = install(_partial(KEPT_SITES))  # The site read lost page two.
    org_upgrade.selected_rows(ORG_ID, [NORTH])  # A listed site, so the check passes.
    names = sorted(name for name, _parameters in reader.calls)  # The read names, in a fixed order.
    assert names == ["listOrgSiteStats", "listOrgSites"]  # One site read and one count read.


def _refusal_summary(chosen: list[str]) -> tuple[int, Any, str] | None:
    """Return the status, the body, and the page path of one site set refusal.

    Why:
        One value holds the whole refusal, so a test compares the status, the
        envelope, and the page path in one assert. A choice that passes reads
        as None, and the compare then fails with the full value.

    Args:
        chosen: The chosen site identifiers.

    Returns:
        The status, the JSON body, and the page path, or None for a choice that passes.
    """
    with Flask(__name__).app_context():  # The envelope needs an application context.
        refused = select.site_set_refusal(ORG_ID, chosen)  # Check the choice against the site read.
        if refused is None:  # The choice passed.
            return None  # The compare of the caller shows the missing refusal.
        (response, status), page_path = refused  # The envelope pair and the page that corrects the choice.
        return status, response.get_json(), page_path  # Read the body inside the context.


def test_the_site_set_refusal_names_a_partial_list(install: Callable[[Any], SiteReader]) -> None:
    """FR-001, FR-005: a chosen site of the lost page gets the 503 envelope and the site picker path."""
    install(_partial(KEPT_SITES))  # The site read lost page two.
    envelope = {"error": {"code": INCOMPLETE_CODE, "message": INCOMPLETE_MESSAGE}}  # FR-001 and FR-002.
    summary = _refusal_summary([NORTH, WEST])  # West sits on the lost page.
    assert summary == (503, envelope, select.SITE_PAGE_PATH)  # A retry repeats the choice on the site picker.


def test_the_site_set_refusal_keeps_the_404_of_a_whole_list(install: Callable[[Any], SiteReader]) -> None:
    """FR-007: a whole list keeps the 404 answer and the site picker path."""
    install(_whole(KEPT_SITES))  # The site read is whole.
    envelope = {"error": {"code": select.SITE_NOT_FOUND, "message": select.SITE_NOT_FOUND_MESSAGE}}  # Today.
    summary = _refusal_summary([WEST])  # The organization does not hold West.
    assert summary == (404, envelope, select.SITE_PAGE_PATH)  # The site picker corrects the choice.


def test_the_site_set_refusal_passes_listed_sites_of_a_partial_list(install: Callable[[Any], SiteReader]) -> None:
    """FR-006: a choice of kept sites passes, also after a lost page."""
    install(_partial(KEPT_SITES))  # The site read lost page two.
    assert _refusal_summary([SOUTH, NORTH]) is None  # Each chosen site is listed, so the choice passes.
