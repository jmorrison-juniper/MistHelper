"""The contract test of the device type column of the history page.

Why:
    A unit test renders the template with a view model. It cannot prove that
    the real ``GET /history`` route reads the stored ``counts`` map and hands
    the words to the page. This test drives the route through the Flask test
    client, so the whole page lane is under test.

    FR-084a asks the history view to name the device types that each stored
    capture set holds. FR-084b asks the view to keep the role column beside the
    new one. Both facts appear below as a literal, because a test that imported
    a name from the module under test would agree with a rename.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.upgrade_portal.runtime import identity

SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # Matches the shared site of the other contract tests.

HISTORY_PAGE_PATH = "/history"  # Section 6 of `contracts/http-api.md` names this path.

CAPTURE_LISTER_KEY = "CAPTURE_LISTER"  # The capture list seam of `app/routes/review.py`.
RUN_LISTER_KEY = "RUN_LISTER"  # The run list seam of the same module.

PROBE_EMAIL = "history.operator@example.invalid"  # A reserved domain, so no real address appears.

OK_STATUS = 200  # Section 6 of `contracts/http-api.md` sets this status.

# The three device names of the stored `counts` map, as `data-model.md` line 183
# spells them.
GATEWAYS = "gateways"
SWITCHES = "switches"
ACCESS_POINTS = "access_points"

# The words that FR-084a asks the page to print. A live capture read one
# gateway, one switch, and six access points into one stored capture set.
MIXED_TEXT = "1 gateway, 1 switch, 6 access points"

# The text that FR-084a asks the page to print for a capture set of no device.
NO_DEVICE_TYPE = "No device type"

# The column head that the page shows, and the head that FR-084b keeps.
DEVICE_TYPE_HEAD = '<th scope="col">Device types</th>'
ROLE_HEAD = '<th scope="col">Role</th>'

# The identifier of the new cell, from `contracts/ui-testids.md`.
DEVICE_TYPE_TEST_ID = 'data-testid="history-device-type-cap-mixed"'


def capture_row(capture_id: str, **counts: int) -> dict[str, Any]:
    """Return one whole capture row, as the store lists it.

    Args:
        capture_id: The identifier of the capture.
        **counts: The device counts of the stored ``counts`` map.

    Returns:
        One capture row.
    """
    return {
        "capture_id": capture_id,
        "role": "pre",
        "started_at": "2026-07-01T09:00:00+00:00",
        "capture_status": "verified",
        "actor_email": PROBE_EMAIL,
        "stored_size_bytes": 4096,
        "site_id": SITE_ID,
        "site_name": "Test Site",
        "counts": dict(counts),
    }


@dataclass(frozen=True, slots=True)
class FakeCapturePage:
    """The capture list page that the store hands back.

    Attributes:
        captures: The rows of this page.
        total: The count of the whole history.
    """

    captures: tuple[dict[str, Any], ...] = ()
    total: int = 0


@dataclass
class CannedLister:
    """A capture list seam that answers one fixed page.

    Attributes:
        rows: The whole history, newest first.
    """

    rows: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, site_id: str, limit: int = 25, offset: int = 0) -> FakeCapturePage:
        """Return one page of the canned history.

        Args:
            site_id: The site that the route asked for.
            limit: The page size that the route asked for.
            offset: The page start that the route asked for.

        Returns:
            The page of rows and the count of the whole history.
        """
        return FakeCapturePage(captures=tuple(self.rows[offset : offset + limit]), total=len(self.rows))


@pytest.fixture
def history_app(portal_app: Flask) -> Flask:
    """Return the portal with the capture list seam replaced.

    Why:
        The route falls back to ``capture.store``, and that module imports the
        database driver. The injected seam keeps the test free of a database.

    Args:
        portal_app: The portal application.

    Returns:
        The wired application.
    """
    portal_app.config[CAPTURE_LISTER_KEY] = CannedLister(
        rows=[
            capture_row("cap-mixed", gateways=1, switches=1, access_points=6),
            capture_row("cap-empty"),
        ]
    )
    portal_app.config[RUN_LISTER_KEY] = CannedLister()
    return portal_app


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
def signed_in_client(history_app: Flask, owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a test client that holds a session and holds no lock.

    Args:
        history_app: The wired application.
        owner: The identity pair of the registered operator.

    Yields:
        The signed-in client.
    """
    with history_app.test_client() as client:  # The context manager holds the session across requests.
        client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
        with client.session_transaction() as browser_session:
            browser_session[identity.SESSION_OWNER_KEY] = owner.key
        yield client


def read_page(client: FlaskClient) -> str:
    """Return the rendered history page of one site.

    Args:
        client: The signed-in test client.

    Returns:
        The page markup.
    """
    response = client.get(f"{HISTORY_PAGE_PATH}?site_id={SITE_ID}")
    assert response.status_code == OK_STATUS
    return response.get_data(as_text=True)


def test_the_history_page_shows_the_device_type_column(signed_in_client: FlaskClient) -> None:
    """Prove the table head names the column that FR-084a asks for.

    Args:
        signed_in_client: The signed-in test client.
    """
    assert DEVICE_TYPE_HEAD in read_page(signed_in_client)


def test_the_history_page_names_every_device_type_of_a_capture(signed_in_client: FlaskClient) -> None:
    """Prove the cell names each stored device type and its count.

    Why:
        One capture reads every device type at one time. A live capture held
        one gateway, one switch, and six access points, so the cell names all
        three.

    Args:
        signed_in_client: The signed-in test client.
    """
    assert MIXED_TEXT in read_page(signed_in_client)


def test_the_history_page_never_shows_an_empty_device_type_cell(signed_in_client: FlaskClient) -> None:
    """Prove a capture set with no device shows a plain word.

    Args:
        signed_in_client: The signed-in test client.
    """
    assert NO_DEVICE_TYPE in read_page(signed_in_client)


def test_the_history_page_carries_the_device_type_identifier(signed_in_client: FlaskClient) -> None:
    """Prove the cell carries the identifier that the contract fixes.

    Args:
        signed_in_client: The signed-in test client.
    """
    assert DEVICE_TYPE_TEST_ID in read_page(signed_in_client)


def test_the_history_page_keeps_the_role_column(signed_in_client: FlaskClient) -> None:
    """Prove the new column joined the table and replaced no column.

    Why:
        FR-084b keeps the role beside the device types. The role names the
        place of the capture in one run.

    Args:
        signed_in_client: The signed-in test client.
    """
    page = read_page(signed_in_client)
    assert ROLE_HEAD in page
    assert "<td>pre</td>" in page


def test_the_history_page_keeps_the_open_control_of_every_row(signed_in_client: FlaskClient) -> None:
    """Prove every earlier identifier of the row survives the new column.

    Args:
        signed_in_client: The signed-in test client.
    """
    page = read_page(signed_in_client)
    assert 'data-testid="history-row-cap-mixed"' in page
    assert 'data-testid="history-open-cap-mixed"' in page
