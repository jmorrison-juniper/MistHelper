"""Contract tests of the lost-page notes of the site picker (issue #3438).

Why:
    The site picker reads two paged cloud lists: the site records and the
    device count of each site. A lost later page left a short site list with
    no sign. The single-site mode and the multi-site mode both showed that
    list as whole, and ``GET /api/sites`` answered it as whole.

    These tests inject a cloud reader that answers the ``DeviceRead`` shape of
    the real reader, with the reasons of a lost page. The page must then show
    one Caution note for each read that lost a page. The JSON answer must name
    the completeness of each read, and the rows must not change.
"""

from __future__ import annotations

import html
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from flask import Flask, template_rendered
from flask.testing import FlaskClient

from src.upgrade_portal.capture.devices import DeviceRead
from src.upgrade_portal.runtime import identity

SITE_PAGE_PATH = "/select/site"  # The site picker page, and the multi-site forward post.
SITES_API_PATH = "/api/sites"  # The site list with the organization in the session.
NEXT_AFTER_MULTI_SITE = "/upgrade/org/options"  # The page after a multi-site choice.
SITE_TEMPLATE = "select/sites.html"  # The template of the site picker.

MIST_READER_KEY = "MIST_READER"  # The seam of the two cloud reads.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam of the lock read.
SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The chosen organization in the signed session.
SELECTED_MODE_SESSION_KEY = "selected_upgrade_mode"  # The chosen operation mode in the signed session.
SINGLE_SITE_MODE = "single_site"  # One site uses the current workflow.
MULTI_SITE_MODE = "multi_site"  # Many sites use the organization workflow.
SCRIPT_HEADERS = {"X-Requested-With": "XMLHttpRequest"}  # A script post receives JSON.

OPERATOR_EMAIL = "lost.page.operator@example.invalid"  # A reserved domain, so no address reaches a mail server.
SITE_LIST_TEST_ID = "site-list-partial"  # The note of a site read that lost a page.
SITE_COUNT_TEST_ID = "site-count-partial"  # The note of a device count read that lost a page.
SITE_LIST_NOTE = (  # The operator reads the risk and the next step.
    "The portal did not read the complete site list. The list can leave out sites. "
    "Reload this page to read the list again."
)
SITE_COUNT_NOTE = (  # The operator reads the risk and the next step.
    "The portal did not read every device count. A site can show 0 devices when it holds devices. "
    "Reload this page to read the counts again."
)

NORTH_ID = "00000000-0000-0000-0000-000000003438"  # The first site of page one.
SOUTH_ID = "00000000-0000-0000-0000-000000003439"  # The second site of page one.
PAGE_ONE = {  # The rows of page one of each picker read.
    "listOrgSites": [{"id": NORTH_ID, "name": "North Campus"}, {"id": SOUTH_ID, "name": "South Campus"}],
    "listOrgSiteStats": [{"id": NORTH_ID, "num_devices": 4}, {"id": SOUTH_ID, "num_devices": 7}],
}
EXPECTED_ROWS = [  # The rows that the site list answers for page one. A lost page changes none of them.
    {"site_id": NORTH_ID, "name": "North Campus", "device_count": 4, "locked_by": None, "lock_state": "free"},
    {"site_id": SOUTH_ID, "name": "South Campus", "device_count": 7, "locked_by": None, "lock_state": "free"},
]


def _reason(name: str, reason: str, status: int) -> dict[str, Any]:
    """Build one partial reason entry.

    Args:
        name: The read that lost data.
        reason: The reason code.
        status: The HTTP status of the answer.

    Returns:
        The entry that the real reader builds.
    """
    return {"section": name, "reason": reason, "http_status": status}


def _whole(name: str) -> DeviceRead:
    """Answer page one of a read that is whole.

    Args:
        name: The picker read.

    Returns:
        The rows of page one and no reason.
    """
    return DeviceRead(name, [dict(row) for row in PAGE_ONE[name]], [])


def _lost(name: str) -> DeviceRead:
    """Answer page one of a read that lost page two.

    Args:
        name: The picker read.

    Returns:
        The rows of page one and the reason of the lost page.
    """
    return DeviceRead(name, [dict(row) for row in PAGE_ONE[name]], [_reason(name, "page_count_mismatch", 503)])


def _failed(name: str) -> DeviceRead:
    """Answer a read whose first page failed.

    Args:
        name: The picker read.

    Returns:
        No row and the reason of the failed first page.
    """
    return DeviceRead(name, [], [_reason(name, "cloud_error_status", 503)])


class PickerReads:
    """Answer the two picker reads with fixed read results."""

    def __init__(self, sites: DeviceRead, counts: DeviceRead) -> None:
        """Keep one answer for each read.

        Args:
            sites: The answer of the site read.
            counts: The answer of the device count read.
        """
        self.answers = {"listOrgSites": sites, "listOrgSiteStats": counts}  # One answer for each read name.
        self.calls: list[str] = []  # The read names, in call order.

    def __call__(self, name: str, **parameters: Any) -> DeviceRead:
        """Answer one read and record its name.

        Args:
            name: The read name.
            **parameters: The call parameters. The answer does not depend on them.

        Returns:
            The fixed answer of the read.
        """
        del parameters  # One fixed answer for each read name.
        self.calls.append(name)  # Record the call order.
        return self.answers[name]  # An unknown name fails the test with a KeyError.


def _free_locks(org_id: str, site_ids: list[str]) -> dict[str, str | None]:
    """Answer that every site is free.

    Args:
        org_id: The organization of the sites.
        site_ids: The sites that the route asked about.

    Returns:
        One free entry for each site.
    """
    del org_id  # Every site of every organization is free.
    return {site_id: None for site_id in site_ids}  # One entry for each site, as the real reader answers.


@pytest.fixture
def operator() -> Iterator[identity.SessionOwner]:
    """Register one operator whose cloud session states no organization scope.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(OPERATOR_EMAIL, identity.issue_browser_id())  # One operator with a new browser.
    record = identity.OperatorSession(
        owner=owner,
        cloud_session=object(),  # A plain object states no scope, so every organization passes.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)  # The guard admits a registered owner only.
    try:
        yield owner
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # The registry outlives the test, so clear it here.


def _picker_client(app: Flask, owner: identity.SessionOwner, org_id: str, reads: PickerReads, mode: str) -> FlaskClient:
    """Wire the seams and return a client that is signed in with a chosen organization and mode.

    Args:
        app: The portal application.
        owner: The registered operator.
        org_id: The chosen organization.
        reads: The stand-in of the two cloud reads.
        mode: The chosen operation mode.

    Returns:
        The signed-in test client.
    """
    app.config[MIST_READER_KEY] = reads  # The cloud reads answer through the stand-in.
    app.config[LOCK_READER_KEY] = _free_locks  # Every site is free, and no Redis server runs.
    client = app.test_client()  # A client with its own cookie jar.
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The browser half of the identity pair.
    with client.session_transaction() as browser_session:  # The signed half of the identity pair.
        browser_session[identity.SESSION_OWNER_KEY] = owner.key  # The registered owner.
        browser_session[SELECTED_ORG_SESSION_KEY] = org_id  # The organization the operator chose.
        browser_session[SELECTED_MODE_SESSION_KEY] = mode  # The operation mode the operator chose.
    return client


def _open_picker(app: Flask, client: FlaskClient) -> tuple[str, dict[str, Any]]:
    """Open the site picker, and return the page and the values that the route gave the template.

    Args:
        app: The portal application.
        client: The signed-in test client.

    Returns:
        The page text and the template values of the site picker.
    """
    seen: dict[str, dict[str, Any]] = {}  # The values of each rendered template, by template name.

    def record(sender: Flask, template: Any, context: dict[str, Any], **extra: Any) -> None:
        """Keep the values of one rendered template."""
        del sender, extra  # Only the template name and its values matter.
        seen[str(template.name)] = dict(context)  # A copy, so a later render cannot change it.

    with template_rendered.connected_to(record, app):  # Listen to this application only.
        answer = client.get(SITE_PAGE_PATH)  # Open the site picker.
    assert answer.status_code == 200  # The picker opens after a lost page.
    return answer.get_data(as_text=True), seen.get(SITE_TEMPLATE, {})


def _note_text(page: str, test_id: str) -> str:
    """Return the plain text of one Caution note, or an empty string when the page holds none.

    Args:
        page: The page text.
        test_id: The test identifier of the note.

    Returns:
        The note text with collapsed white space.
    """
    pattern = rf'<div class="flash-item flash-warning" role="status" data-testid="{test_id}">\s*<span>(.*?)</span>'
    found = re.search(pattern, page, re.DOTALL)  # A note holds one span of text.
    return " ".join(html.unescape(found.group(1)).split()) if found else ""  # Collapse the wrapped text.


def test_the_single_site_picker_names_a_lost_site_page(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """FR-005: a lost page of the site read shows one Caution note above the table."""
    reads = PickerReads(_lost("listOrgSites"), _whole("listOrgSiteStats"))  # The site read lost page two.
    client = _picker_client(portal_app, operator, fake_org_id, reads, SINGLE_SITE_MODE)  # The single-site mode.
    page, _values = _open_picker(portal_app, client)  # Open the picker.
    assert _note_text(page, SITE_LIST_TEST_ID) == SITE_LIST_NOTE  # The note states the risk and the next step.
    assert f'data-testid="{SITE_COUNT_TEST_ID}"' not in page  # The device count read is whole.
    assert page.index(f'data-testid="{SITE_LIST_TEST_ID}"') < page.index('data-testid="site-table"')  # Above.
    assert f'data-testid="site-row-{NORTH_ID}"' in page  # The rows of page one still show.
    assert f'data-testid="site-row-{SOUTH_ID}"' in page
    assert reads.calls == ["listOrgSites", "listOrgSiteStats"]  # The read order does not change.


def test_the_single_site_picker_names_a_lost_count_page(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """FR-006: a lost page of the device count read shows the second Caution note."""
    reads = PickerReads(_whole("listOrgSites"), _lost("listOrgSiteStats"))  # The count read lost page two.
    client = _picker_client(portal_app, operator, fake_org_id, reads, SINGLE_SITE_MODE)  # The single-site mode.
    page, _values = _open_picker(portal_app, client)  # Open the picker.
    assert _note_text(page, SITE_COUNT_TEST_ID) == SITE_COUNT_NOTE  # The note states the risk and the next step.
    assert f'data-testid="{SITE_LIST_TEST_ID}"' not in page  # The site read is whole.
    assert page.index(f'data-testid="{SITE_COUNT_TEST_ID}"') < page.index('data-testid="site-table"')  # Above.


def test_the_single_site_picker_shows_no_note_after_two_whole_reads(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """FR-005, FR-006: two whole reads show no note, and the route passes two false flags."""
    reads = PickerReads(_whole("listOrgSites"), _whole("listOrgSiteStats"))  # Both reads are whole.
    client = _picker_client(portal_app, operator, fake_org_id, reads, SINGLE_SITE_MODE)  # The single-site mode.
    page, values = _open_picker(portal_app, client)  # Open the picker.
    assert values.get("site_list_partial", "absent") is False  # The route names a whole site read.
    assert values.get("site_count_partial", "absent") is False  # The route names a whole device count read.
    assert f'data-testid="{SITE_LIST_TEST_ID}"' not in page  # No site list note.
    assert f'data-testid="{SITE_COUNT_TEST_ID}"' not in page  # No device count note.


def test_a_failed_first_page_shows_the_site_note_above_an_empty_table(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """Edge case: a failed first page shows the site list note, and the table holds no row."""
    reads = PickerReads(_failed("listOrgSites"), _whole("listOrgSiteStats"))  # The site read failed at page one.
    client = _picker_client(portal_app, operator, fake_org_id, reads, SINGLE_SITE_MODE)  # The single-site mode.
    page, _values = _open_picker(portal_app, client)  # Open the picker.
    assert _note_text(page, SITE_LIST_TEST_ID) == SITE_LIST_NOTE  # An empty list with no note misleads.
    assert 'data-testid="site-row-' not in page  # The table holds no row.


def test_the_multi_site_picker_names_both_lost_pages_above_the_form(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """FR-007: the multi-site picker shows both notes above the check boxes."""
    reads = PickerReads(_lost("listOrgSites"), _lost("listOrgSiteStats"))  # Both reads lost page two.
    client = _picker_client(portal_app, operator, fake_org_id, reads, MULTI_SITE_MODE)  # The multi-site mode.
    page, _values = _open_picker(portal_app, client)  # Open the picker.
    form_at = page.index('data-testid="multi-site-form"')  # The form that holds the check boxes.
    assert _note_text(page, SITE_LIST_TEST_ID) == SITE_LIST_NOTE  # The site list note.
    assert _note_text(page, SITE_COUNT_TEST_ID) == SITE_COUNT_NOTE  # The device count note.
    assert page.index(f'data-testid="{SITE_LIST_TEST_ID}"') < form_at  # Above the check boxes.
    assert page.index(f'data-testid="{SITE_COUNT_TEST_ID}"') < form_at  # Above the check boxes.


def test_a_site_of_the_first_page_still_moves_forward_after_a_lost_page(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """US2: the note does not block a site of page one, so the forward post still works."""
    reads = PickerReads(_lost("listOrgSites"), _whole("listOrgSiteStats"))  # The site read lost page two.
    client = _picker_client(portal_app, operator, fake_org_id, reads, MULTI_SITE_MODE)  # The multi-site mode.
    page, _values = _open_picker(portal_app, client)  # The operator reads the note first.
    assert _note_text(page, SITE_LIST_TEST_ID) == SITE_LIST_NOTE  # The note shows above the check boxes.
    portal_app.config["WTF_CSRF_ENABLED"] = False  # The token check has its own tests, and this post has no token.
    answer = client.post(SITE_PAGE_PATH, json={"site_ids": [NORTH_ID]}, headers=SCRIPT_HEADERS)  # Select one site.
    assert answer.status_code == 200  # The portal accepts a site of page one.
    assert answer.get_json() == {"next": NEXT_AFTER_MULTI_SITE}  # The next step is the options page.


def _site_list_path(path_kind: str, org_id: str) -> str:
    """Return one of the two paths of the site list.

    Args:
        path_kind: "session" or "path".
        org_id: The organization of the path form.

    Returns:
        The request path.
    """
    return SITES_API_PATH if path_kind == "session" else f"/api/orgs/{org_id}/sites"


@dataclass(frozen=True)
class ListCase:
    """One case of the site list matrix.

    Attributes:
        sites: The builder of the site read answer.
        counts: The builder of the device count read answer.
        sites_whole: The expected value of `site_list_complete`.
        counts_whole: The expected value of `device_counts_complete`.
    """

    sites: Callable[[str], DeviceRead]
    counts: Callable[[str], DeviceRead]
    sites_whole: bool
    counts_whole: bool


LIST_CASES = [  # Each read alone loses a page, and then neither read loses one.
    pytest.param(ListCase(_lost, _whole, False, True), id="lost-site-page"),
    pytest.param(ListCase(_whole, _lost, True, False), id="lost-count-page"),
    pytest.param(ListCase(_whole, _whole, True, True), id="two-whole-reads"),
]


@pytest.mark.parametrize("path_kind", ["session", "path"])
@pytest.mark.parametrize("case", LIST_CASES)
def test_the_site_list_answer_names_the_completeness_of_each_read(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str, path_kind: str, case: ListCase
) -> None:
    """FR-008: both paths name the completeness of each read, and the rows do not change."""
    reads = PickerReads(case.sites("listOrgSites"), case.counts("listOrgSiteStats"))  # One case of the matrix.
    client = _picker_client(portal_app, operator, fake_org_id, reads, SINGLE_SITE_MODE)  # A signed-in client.
    answer = client.get(_site_list_path(path_kind, fake_org_id))  # Read the site list.
    body = answer.get_json()  # The JSON answer.
    assert answer.status_code == 200  # A lost page is not a refusal.
    assert set(body) == {"sites", "site_list_complete", "device_counts_complete"}  # The three fields.
    assert body["site_list_complete"] is case.sites_whole  # The completeness of the site read.
    assert body["device_counts_complete"] is case.counts_whole  # The completeness of the device count read.
    assert body["sites"] == EXPECTED_ROWS  # The rows do not change.
