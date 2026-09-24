"""Contract tests for the multi-site section of the history page.

Why:
    Issue #3248. A multi-site upgrade had no history entry. An operator who
    closed the progress page could not find the upgrade again, because only
    the address of the job led back to it.

    These tests drive the real route and the real template through a signed-in
    client. Each test injects the three list seams, so no test reaches a
    database. The operation seam records every call, so a test proves the
    organization, the site, and the page size that reach the store.

Every value below is a literal. A test that imported a name from the module
under test would agree with a rename and would prove nothing.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.upgrade_portal.runtime import identity

HISTORY_PAGE_PATH = "/history"  # Section 6 of `contracts/http-api.md` names this path.
JOB_PAGE_PREFIX = "/upgrade/org/jobs/"  # The progress page of one multi-site operation.

CAPTURE_LISTER_KEY = "CAPTURE_LISTER"  # The capture list seam of `app/routes/review.py`.
RUN_LISTER_KEY = "RUN_LISTER"  # The run list seam of the same module.
OPERATION_LISTER_KEY = "OPERATION_LISTER"  # Issue #3248: the operation list seam of the same module.
SELECTED_ORG_KEY = "selected_org_id"  # The organization pick inside the signed session.

OK_STATUS = 200  # Every read of this module must answer this status.
DEFAULT_LIMIT = 25  # Section 6 of `contracts/http-api.md` sets this page size.

ORG_ID = "00000000-0000-0000-0000-0000000000aa"  # Matches the shared organization of the other tests.
SITE_A = "00000000-0000-0000-0000-0000000000b1"  # The first site of each operation.
SITE_B = "00000000-0000-0000-0000-0000000000b2"  # The second site of each operation.
OWNED_ID = "org-run-owned0001"  # The operation that the signed-in session started.
FOREIGN_ID = "org-run-foreign0001"  # The operation that another browser session started.
PROBE_EMAIL = "history.operations@example.invalid"  # A reserved domain, so no real address appears.
OTHER_OWNER_KEY = "owner-key-of-another-browser-session"  # The owner key of the second operator.


@dataclass(frozen=True, slots=True)
class FakeOperationPage:
    """The operation list page that the store hands back.

    Attributes:
        operations: The rows of the section.
        database_available: False when the store did not answer.
    """

    operations: tuple[dict[str, Any], ...] = ()
    database_available: bool = True


@dataclass
class RecordingOperationLister:
    """An operation list seam that records every call.

    Attributes:
        rows: The rows that each call returns.
        available: The availability flag of each answer.
        calls: One record for each call.
    """

    rows: list[dict[str, Any]] = field(default_factory=list)
    available: bool = True
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, org_id: str, site_id: str = "", limit: int = DEFAULT_LIMIT) -> FakeOperationPage:
        """Record the call and return the canned rows.

        Args:
            org_id: The organization that the route asked for.
            site_id: The site that the route asked for.
            limit: The page size that the route asked for.

        Returns:
            The page of rows.
        """
        self.calls.append({"org_id": org_id, "site_id": site_id, "limit": limit})
        return FakeOperationPage(tuple(self.rows), self.available)


def empty_list(site_id: str, limit: int = DEFAULT_LIMIT, offset: int = 0) -> list[dict[str, Any]]:
    """Return no row for the capture list and the run list.

    Args:
        site_id: The site that the route asked for.
        limit: The page size that the route asked for.
        offset: The page start that the route asked for.

    Returns:
        An empty list.
    """
    return []


def operation_row(operation_id: str, owner_key: str) -> dict[str, Any]:
    """Return one operation row, as the store projects it.

    Args:
        operation_id: The identifier of the operation.
        owner_key: The owner key of the session that started the operation.

    Returns:
        The row.
    """
    return {
        "operation_id": operation_id,
        "org_id": ORG_ID,
        "site_ids": [SITE_A, SITE_B],
        "site_names": {SITE_A: "Alpha Site", SITE_B: "Beta Site"},
        "state": "running",
        "actor_email": PROBE_EMAIL,
        "cloud_account": "noc.account@example.invalid",
        "created_at": "2026-09-24T01:02:03Z",
        "updated_at": "2026-09-24T01:05:00Z",
        "owner": owner_key,
        "families": ["switch", "ap"],
    }


@pytest.fixture
def owner() -> Iterator[identity.SessionOwner]:
    """Register one operator for the length of one test.

    Yields:
        The identity pair of the registered operator.
    """
    owner_record = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())
    record = identity.OperatorSession(
        owner=owner_record,
        cloud_session=object(),  # A plain object states no scope, so every site passes.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)
    try:
        yield owner_record
    finally:
        identity.SESSION_REGISTRY.drop(owner_record.key)  # The registry outlives the test, so clear it here.


@pytest.fixture
def operation_lister(owner: identity.SessionOwner) -> RecordingOperationLister:
    """Return the operation seam with one owned row and one foreign row.

    Args:
        owner: The identity pair of the registered operator.

    Returns:
        The seam.
    """
    return RecordingOperationLister(
        rows=[operation_row(OWNED_ID, owner.key), operation_row(FOREIGN_ID, OTHER_OWNER_KEY)]
    )


@pytest.fixture
def history_app(portal_app: Flask, operation_lister: RecordingOperationLister) -> Flask:
    """Return the portal with the three list seams replaced.

    Args:
        portal_app: The portal application.
        operation_lister: The operation seam to inject.

    Returns:
        The wired application.
    """
    portal_app.config[CAPTURE_LISTER_KEY] = empty_list
    portal_app.config[RUN_LISTER_KEY] = empty_list
    portal_app.config[OPERATION_LISTER_KEY] = operation_lister
    return portal_app


def signed_in_client(app: Flask, owner: identity.SessionOwner, org_id: str) -> FlaskClient:
    """Return a client that holds a session and, when given, a selected organization.

    Args:
        app: The wired application.
        owner: The identity pair of the registered operator.
        org_id: The selected organization, or an empty text for none.

    Returns:
        The client.
    """
    client = app.test_client()
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
    with client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = owner.key
        if org_id:
            browser_session[SELECTED_ORG_KEY] = org_id
    return client


def read_page(app: Flask, owner: identity.SessionOwner, org_id: str = ORG_ID, query: str = "") -> str:
    """Return the text of the history page.

    Args:
        app: The wired application.
        owner: The identity pair of the registered operator.
        org_id: The selected organization, or an empty text for none.
        query: The query text of the request, with no question mark.

    Returns:
        The page text.
    """
    client = signed_in_client(app, owner, org_id)
    response = client.get(HISTORY_PAGE_PATH + (f"?{query}" if query else ""))
    assert response.status_code == OK_STATUS
    return response.get_data(as_text=True)


def test_the_owner_session_gets_the_link_to_the_progress_page(history_app: Flask, owner: identity.SessionOwner) -> None:
    """The row of the owned operation links to its job page and names its sites and types."""
    text = read_page(history_app, owner)
    assert 'data-testid="history-operation-section"' in text
    assert f'data-testid="history-operation-row-{OWNED_ID}"' in text
    assert f'href="{JOB_PAGE_PREFIX}{OWNED_ID}"' in text
    assert f'data-testid="history-operation-open-{OWNED_ID}"' in text
    assert "Alpha Site, Beta Site" in text
    assert "Access points, Switches" in text


def test_another_session_gets_a_note_and_no_link(history_app: Flask, owner: identity.SessionOwner) -> None:
    """The job page refuses another session, so the foreign row carries a note in place of the link."""
    text = read_page(history_app, owner)
    assert f'data-testid="history-operation-not-owned-{FOREIGN_ID}"' in text
    assert "Another browser session started this upgrade." in text
    assert f'href="{JOB_PAGE_PREFIX}{FOREIGN_ID}"' not in text
    assert f'data-testid="history-operation-open-{FOREIGN_ID}"' not in text


def test_no_selected_organization_reads_nothing(
    history_app: Flask, owner: identity.SessionOwner, operation_lister: RecordingOperationLister
) -> None:
    """With no organization, the section asks for one and the store receives no call."""
    text = read_page(history_app, owner, org_id="")
    assert operation_lister.calls == []
    assert 'data-testid="history-operation-no-org"' in text
    assert 'data-testid="history-operation-table"' not in text


def test_a_store_outage_shows_a_plain_statement(
    history_app: Flask, owner: identity.SessionOwner, operation_lister: RecordingOperationLister
) -> None:
    """A store that does not answer makes the section say so, in place of an empty table."""
    operation_lister.available = False
    text = read_page(history_app, owner)
    assert 'data-testid="history-operation-unavailable"' in text
    assert 'data-testid="history-operation-table"' not in text


def test_the_section_forwards_the_organization_the_site_and_the_page_size(
    history_app: Flask, owner: identity.SessionOwner, operation_lister: RecordingOperationLister
) -> None:
    """The store receives the selected organization, the site of the page, and the page size."""
    read_page(history_app, owner, query=f"site_id={SITE_B}&limit=10")
    assert operation_lister.calls == [{"org_id": ORG_ID, "site_id": SITE_B, "limit": 10}]


def test_an_organization_with_no_operation_shows_the_empty_row(
    history_app: Flask, owner: identity.SessionOwner, operation_lister: RecordingOperationLister
) -> None:
    """An organization with no multi-site upgrade shows the empty row of the table."""
    operation_lister.rows = []
    text = read_page(history_app, owner)
    assert 'data-testid="history-operation-empty"' in text


def test_the_page_holds_no_owner_key(history_app: Flask, owner: identity.SessionOwner) -> None:
    """The owner key decides the link on the server and never reaches the browser."""
    text = read_page(history_app, owner)
    assert owner.key not in text
    assert OTHER_OWNER_KEY not in text
