"""Contract tests of the empty-site filter of the site picker (issue #3840).

Why:
    An organization can hold a site that carries no hardware of any type. That
    site cannot take a capture and cannot take an upgrade, so the picker row
    only adds noise. The picker now hides such a site by default, states how
    many rows it hid, and offers a link that restores them.

    The filter must never hide a site on a guess. These tests prove the three
    exemptions: the operator asked for every site, the device count read lost a
    page, or the device count read gave no record at all.
"""

from __future__ import annotations

import html
import re
from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.interfaces.portals.upgrade_portal.app.routes.select import (
    apply_empty_site_filter,
    read_show_empty,
)
from src.interfaces.portals.upgrade_portal.capture.devices import DeviceRead
from src.interfaces.portals.upgrade_portal.runtime import identity

SITE_PAGE_PATH = "/select/site"  # The site picker page.
SITES_API_PATH = "/api/sites"  # The site list with the organization in the session.

MIST_READER_KEY = "MIST_READER"  # The seam of the two cloud reads.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam of the lock read.
SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The chosen organization in the signed session.
SELECTED_MODE_SESSION_KEY = "selected_upgrade_mode"  # The chosen operation mode in the signed session.
SINGLE_SITE_MODE = "single_site"  # One site uses the current workflow.

OPERATOR_EMAIL = "empty.site.operator@example.invalid"  # A reserved domain, so no address reaches a mail server.
NOTE_TEST_ID = "empty-site-note"  # The note that states the hidden count.
TOGGLE_TEST_ID = "empty-site-toggle"  # The link that shows or hides the empty sites.
TABLE_TEST_ID = "site-table"  # The table of site rows.

STOCKED_ID = "00000000-0000-0000-0000-000000003840"  # The site that holds hardware.
BARE_ID = "00000000-0000-0000-0000-000000003841"  # The site that holds no hardware.
SITE_ROWS = [  # Both sites of the organization, in the order the cloud answers them.
    {"id": STOCKED_ID, "name": "Stocked Campus"},
    {"id": BARE_ID, "name": "Bare Campus"},
]
COUNT_ROWS = [  # One device count for each site. The bare site holds nothing.
    {"id": STOCKED_ID, "num_devices": 6},
    {"id": BARE_ID, "num_devices": 0},
]
LOST_PAGE_REASON = [  # The reason shape that the real reader builds for a lost page.
    {"section": "listOrgSiteStats", "reason": "page_count_mismatch", "http_status": 503}
]


class PickerReads:
    """Answer the two picker reads with fixed read results."""

    def __init__(self, counts: DeviceRead) -> None:
        """Keep the site answer and one device count answer.

        Args:
            counts: The answer of the device count read.
        """
        sites = DeviceRead("listOrgSites", [dict(row) for row in SITE_ROWS], [])  # The site read is always whole.
        self.answers = {"listOrgSites": sites, "listOrgSiteStats": counts}  # One answer for each read name.

    def __call__(self, name: str, **parameters: Any) -> DeviceRead:
        """Answer one read.

        Args:
            name: The read name.
            **parameters: The call parameters. The answer does not depend on them.

        Returns:
            The fixed answer of the read.
        """
        del parameters  # One fixed answer for each read name.
        return self.answers[name]  # An unknown name fails the test with a KeyError.


def _counts(rows: list[dict[str, Any]], reasons: list[dict[str, Any]] | None = None) -> DeviceRead:
    """Build one device count answer.

    Args:
        rows: The device count records.
        reasons: The partial reasons, or None when the read is whole.

    Returns:
        The answer that the real reader builds.
    """
    return DeviceRead("listOrgSiteStats", [dict(row) for row in rows], list(reasons or []))


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


def _picker_client(app: Flask, owner: identity.SessionOwner, org_id: str, counts: DeviceRead) -> FlaskClient:
    """Wire the seams and return a client that is signed in with a chosen organization.

    Args:
        app: The portal application.
        owner: The registered operator.
        org_id: The chosen organization.
        counts: The answer of the device count read.

    Returns:
        The signed-in test client.
    """
    app.config[MIST_READER_KEY] = PickerReads(counts)  # The cloud reads answer through the stand-in.
    app.config[LOCK_READER_KEY] = _free_locks  # Every site is free, and no Redis server runs.
    client = app.test_client()  # A client with its own cookie jar.
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The browser half of the identity pair.
    with client.session_transaction() as browser_session:  # The signed half of the identity pair.
        browser_session[identity.SESSION_OWNER_KEY] = owner.key  # The registered owner.
        browser_session[SELECTED_ORG_SESSION_KEY] = org_id  # The organization the operator chose.
        browser_session[SELECTED_MODE_SESSION_KEY] = SINGLE_SITE_MODE  # The single-site workflow.
    return client


def _note_text(page: str) -> str:
    """Return the plain text of the empty-site note, or an empty string when the page holds none.

    Args:
        page: The page text.

    Returns:
        The note text with collapsed white space.
    """
    pattern = rf'data-testid="{NOTE_TEST_ID}"[^>]*>(.*?)</p>'  # The note holds one paragraph of text.
    found = re.search(pattern, page, re.DOTALL)  # A missing note answers None.
    if not found:
        return ""  # The page holds no note.
    stripped = re.sub(r"<[^>]+>", " ", found.group(1))  # Drop the link markup and keep the words.
    return " ".join(html.unescape(stripped).split())  # Collapse the wrapped text.


def test_the_picker_hides_a_site_that_holds_no_hardware(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """FR-001: the default page drops the bare site and keeps the stocked site."""
    client = _picker_client(portal_app, operator, fake_org_id, _counts(COUNT_ROWS))  # Both counts arrive.
    page = client.get(SITE_PAGE_PATH).get_data(as_text=True)  # Open the picker with no query argument.
    assert STOCKED_ID in page  # The site that holds hardware stays on the page.
    assert BARE_ID not in page  # The site that holds no hardware leaves the table.


def test_the_picker_states_the_hidden_count_and_offers_the_toggle(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """FR-002: the note names the hidden count, and the link restores the hidden rows."""
    client = _picker_client(portal_app, operator, fake_org_id, _counts(COUNT_ROWS))  # Both counts arrive.
    page = client.get(SITE_PAGE_PATH).get_data(as_text=True)  # Open the picker with no query argument.
    assert "hides 1 site that holds no hardware" in _note_text(page)  # The note states the hidden count.
    assert f'data-testid="{TOGGLE_TEST_ID}"' in page  # The page offers the restore link.
    assert "show_empty=1" in page  # The link carries the override argument.


def test_the_show_empty_argument_restores_every_site(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """FR-003: ``show_empty=1`` keeps every row and offers the hide link."""
    client = _picker_client(portal_app, operator, fake_org_id, _counts(COUNT_ROWS))  # Both counts arrive.
    page = client.get(f"{SITE_PAGE_PATH}?show_empty=1").get_data(as_text=True)  # Ask for every site.
    assert BARE_ID in page  # The bare site returns to the table.
    assert "Hide the sites with no hardware" in page  # The link now hides them again.


def test_a_lost_count_page_hides_no_site(portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str) -> None:
    """FR-004: an incomplete device count read makes a zero count unproven, so nothing is hidden."""
    counts = _counts(COUNT_ROWS, LOST_PAGE_REASON)  # The count read lost a later page.
    client = _picker_client(portal_app, operator, fake_org_id, counts)  # Both counts arrive, but the read is partial.
    page = client.get(SITE_PAGE_PATH).get_data(as_text=True)  # Open the picker with no query argument.
    assert BARE_ID in page  # The portal must not hide a site on an unproven zero.
    assert f'data-testid="{NOTE_TEST_ID}"' not in page  # The page hid nothing, so it states no hidden count.


def test_an_empty_count_read_hides_no_site(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """FR-005: a device count read with no record proves nothing, so nothing is hidden."""
    client = _picker_client(portal_app, operator, fake_org_id, _counts([]))  # The count read gave no record.
    page = client.get(SITE_PAGE_PATH).get_data(as_text=True)  # Open the picker with no query argument.
    assert BARE_ID in page  # Every site stays, because no count was observed.
    assert STOCKED_ID in page  # The stocked site also stays.


def test_the_site_list_api_names_the_hidden_count(
    portal_app: Flask, operator: identity.SessionOwner, fake_org_id: str
) -> None:
    """FR-006: ``GET /api/sites`` answers the hidden count and obeys ``show_empty``."""
    client = _picker_client(portal_app, operator, fake_org_id, _counts(COUNT_ROWS))  # Both counts arrive.
    hidden = client.get(SITES_API_PATH).get_json()  # The default answer hides the bare site.
    assert hidden["empty_sites_hidden"] == 1  # The body states the exact hidden count.
    assert [row["site_id"] for row in hidden["sites"]] == [STOCKED_ID]  # Only the stocked site remains.
    shown = client.get(f"{SITES_API_PATH}?show_empty=1").get_json()  # Ask for every site.
    assert shown["empty_sites_hidden"] == 0  # The override hides nothing.
    assert len(shown["sites"]) == 2  # Both sites return.


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, False),  # No argument keeps the default hide rule.
        ("", False),  # An empty argument keeps the default hide rule.
        ("0", False),  # A false value keeps the default hide rule.
        ("1", True),  # The documented true value.
        ("true", True),  # A word form of the true value.
        ("YES", True),  # The reader ignores the letter case.
        (" on ", True),  # The reader ignores the surrounding space.
        ("maybe", False),  # An unknown value keeps the default hide rule.
    ],
)
def test_read_show_empty_reads_the_documented_values(raw: str | None, expected: bool) -> None:
    """FR-007: the argument reader admits the documented true values only."""
    assert read_show_empty(raw) is expected  # The reader answers a plain boolean.


def test_apply_empty_site_filter_hides_only_a_proven_zero() -> None:
    """FR-008: the filter hides a zero row only when the count read observed a record."""
    rows = [{"site_id": STOCKED_ID, "device_count": 6}, {"site_id": BARE_ID, "device_count": 0}]
    kept, hidden = apply_empty_site_filter(list(rows), True, False, True)  # A whole, observed count read.
    assert [row["site_id"] for row in kept] == [STOCKED_ID]  # The zero row leaves.
    assert hidden == 1  # The filter states the exact hidden count.
    assert apply_empty_site_filter(list(rows), True, True, True) == (rows, 0)  # The override hides nothing.
    assert apply_empty_site_filter(list(rows), False, False, True) == (rows, 0)  # A lost page hides nothing.
    assert apply_empty_site_filter(list(rows), True, False, False) == (rows, 0)  # An unobserved count hides nothing.
