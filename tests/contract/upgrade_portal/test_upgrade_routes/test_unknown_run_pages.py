"""Prove that each run page answers an unknown run ID with a 404 error page.

Why:
    Issue #3276. The run page, the options page, and the confirmation page read
    `load_run(run_id) or {}`. So an unknown run ID rendered an empty page with
    status 200, and the operator could not tell a mistyped link from a real run.
    Each page now renders the shared `error.html` with status 404.

Scope:
    The three page paths with an unknown run ID, with a run ID that holds
    markup, and with a run that the store holds. The stand-in store and the
    stand-in lock reader reach no ArangoDB server and no Redis server.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # The log check reads the records of the route logger.
from collections.abc import Iterator  # The signed-in client fixture yields and then cleans up.
from typing import Any  # A run record is free-form.
from urllib.parse import quote  # A run ID with markup must travel as one escaped path segment.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.
from flask.testing import FlaskClient  # The client type that drives every request.

from src.upgrade_portal.runtime import identity  # The real session guard, so the client signs in for real.
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec  # The record layer owns every field.

ORG_ID = "org-unknown-run-contract"  # One organization scope for the seeded run.
SITE_ID = "site-unknown-run-contract"  # One site scope for the seeded run and the lock read.
PROBE_EMAIL = "unknown.run.contract@example.invalid"  # A reserved address that reaches no mail service.
UNKNOWN_RUN_ID = "not-a-real-run"  # The mistyped link of the issue.
MARKUP_RUN_ID = "<img src=x onerror=alert(1)>"  # Markup with no slash, so it stays one path segment.
ESCAPED_MARKUP = "&lt;img src=x onerror=alert(1)&gt;"  # The text that Jinja writes for the markup ID.
LINE_BREAK_RUN_ID = "bad\nline"  # A decoded path segment can hold a line break.

PAGE_TEMPLATES = ("/runs/{run_id}", "/runs/{run_id}/options", "/runs/{run_id}/confirm")  # The three run pages.
NOT_FOUND_STATUS = 404  # No run holds the ID.
OK_STATUS = 200  # The page of a stored run.
RUN_NOT_FOUND_CODE = "run_not_found"  # `contracts/http-api.md` fixes this code for every run path.
SITE_LIST_LINK = 'href="/select/site"'  # The recovery link of `error.html`.
ROUTE_LOGGER = "src.upgrade_portal.app.routes.upgrade"  # The logger of the three page routes.

# A control that writes to a run must never appear on the error page (FR-003).
WRITE_CONTROLS = (
    'data-testid="upgrade-target-table"',  # The version picker of the options page.
    'data-testid="upgrade-start-button"',  # The start control of the confirmation page.
    'data-testid="stop-button"',  # The stop control of the run page.
)


class EmptyRunStore:
    """Hold the run records of one test in memory.

    Why:
        The page routes read a run through `read_run`, and the stop partial can
        write through `write_run`. This stand-in serves both and reaches no
        database server.
    """

    def __init__(self) -> None:
        """Start with no run record at all."""
        self.runs: dict[str, dict[str, Any]] = {}  # One entry for each seeded run.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return a copy of one run record, or None for an unknown run ID."""
        held = self.runs.get(run_id)  # An unknown ID reads as None, never as a fault.
        return dict(held) if held is not None else None  # A copy stops a route edit of the stored record.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Store a copy of one run record."""
        self.runs[str(run["run_id"])] = dict(run)  # Keep a complete route write inside this test.
        return True  # This stand-in never refuses a write.


@pytest.fixture
def run_store() -> EmptyRunStore:
    """Return a fresh run store with no record."""
    return EmptyRunStore()  # Each test starts with no run at all.


@pytest.fixture
def unknown_run_app(portal_app: Flask, run_store: EmptyRunStore) -> Flask:
    """Return the real portal with the run store and the lock reader replaced."""
    portal_app.config["RUN_STORE"] = run_store  # No ArangoDB server runs in a contract test.
    portal_app.config["SITE_LOCK_READER"] = lambda _org, sites: {site: None for site in sites}  # No Redis.
    return portal_app  # The shared factory already registered the real route blueprints.


@pytest.fixture
def unknown_run_client(unknown_run_app: Flask) -> Iterator[FlaskClient]:
    """Return a client that holds a signed-in operator session."""
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())  # The pair that the guard checks.
    session_record = identity.OperatorSession(  # A session with no cloud client.
        owner=owner,  # Bind the record to the browser cookie pair.
        cloud_session=object(),  # A plain object can make no cloud request.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,  # The session kind of the other page tests.
    )
    identity.SESSION_REGISTRY.register(session_record)  # The guard reads the registry on every request.
    try:  # Keep the cleanup active when an assertion fails.
        with unknown_run_app.test_client() as client:  # Hold one browser session across the requests.
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The cookie half of the guard.
            with client.session_transaction() as browser_session:  # The signed server-side session.
                browser_session[identity.SESSION_OWNER_KEY] = owner.key  # The session half of the guard.
            yield client  # Each test reads the real rendered pages.
    finally:  # The process-wide registry must not affect a later test.
        identity.SESSION_REGISTRY.drop(owner.key)  # Remove the isolated operator record.


def seed_run(store: EmptyRunStore) -> str:
    """Write one run record into the store and return its ID."""
    spec = RunSpec(ORG_ID, "Contract organization", SITE_ID, "Contract site", PROBE_EMAIL, "browser-contract")
    record = RunRecordBuilder().build(spec)  # The record layer supplies every field and every default.
    record["state"] = "pre_capture_done"  # A run that has passed the pre-check stage.
    store.write_run(record)  # The page routes read this record through the seam.
    return str(record["run_id"])  # Every page path carries this ID.


def page_path(template: str, run_id: str) -> str:
    """Build one page path with the run ID as one escaped path segment."""
    return template.format(run_id=quote(run_id, safe=""))  # The browser sends an escaped segment too.


@pytest.mark.parametrize("template", PAGE_TEMPLATES)
def test_an_unknown_run_answers_the_error_page(unknown_run_client: FlaskClient, template: str) -> None:
    """An unknown run ID answers 404 with the shared HTML error page (FR-001, FR-002)."""
    answer = unknown_run_client.get(page_path(template, UNKNOWN_RUN_ID))  # The mistyped link of the issue.
    page = answer.get_data(as_text=True)  # The whole rendered page.
    assert answer.status_code == NOT_FOUND_STATUS  # A mistyped link is not a real run.
    assert answer.mimetype == "text/html"  # A person reads a page, not the JSON envelope.
    assert 'data-testid="error-message"' in page  # `error.html` rendered, and not an empty run page.
    assert UNKNOWN_RUN_ID in page  # The page names the run ID that the operator opened.
    assert RUN_NOT_FOUND_CODE in page  # A support request can quote the stable code.
    assert SITE_LIST_LINK in page  # The operator has a way back to the site list.


@pytest.mark.parametrize("template", PAGE_TEMPLATES)
def test_the_error_page_shows_no_write_control(unknown_run_client: FlaskClient, template: str) -> None:
    """The error page offers no control that can write to a run (FR-003)."""
    page = unknown_run_client.get(page_path(template, UNKNOWN_RUN_ID)).get_data(as_text=True)  # The error page.
    for control in WRITE_CONTROLS:  # Each control that writes to a run.
        assert control not in page  # An unknown run has nothing to pick, to start, or to stop.


@pytest.mark.parametrize("template", PAGE_TEMPLATES)
def test_a_run_id_with_markup_shows_as_text(unknown_run_client: FlaskClient, template: str) -> None:
    """Jinja escapes the run ID, so markup in a link shows as text (FR-004)."""
    answer = unknown_run_client.get(page_path(template, MARKUP_RUN_ID))  # A crafted link with markup.
    page = answer.get_data(as_text=True)  # The whole rendered page.
    assert answer.status_code == NOT_FOUND_STATUS  # The markup ID is an unknown run too.
    assert ESCAPED_MARKUP in page  # The operator reads the ID as text.
    assert MARKUP_RUN_ID not in page  # No browser can run the markup.


@pytest.mark.parametrize("template", PAGE_TEMPLATES)
def test_a_stored_run_keeps_its_page(unknown_run_client: FlaskClient, run_store: EmptyRunStore, template: str) -> None:
    """A run that the store holds keeps status 200 and its own page (FR-005)."""
    run_id = seed_run(run_store)  # A real record, so the page has a run to show.
    answer = unknown_run_client.get(page_path(template, run_id))  # The same page path as a real link.
    page = answer.get_data(as_text=True)  # The whole rendered page.
    assert answer.status_code == OK_STATUS  # A stored run is never refused.
    assert 'data-testid="error-message"' not in page  # The run page, not the error page.
    assert run_id in page  # The page names the run it shows.


def test_the_log_line_of_an_unknown_run_holds_ascii_only(
    unknown_run_client: FlaskClient, caplog: pytest.LogCaptureFixture
) -> None:
    """A line break in the run ID cannot write a second log line (FR-007)."""
    with caplog.at_level(logging.INFO, logger=ROUTE_LOGGER):  # Capture the records of the page route.
        answer = unknown_run_client.get(page_path(PAGE_TEMPLATES[0], LINE_BREAK_RUN_ID))  # A decoded line break.
    assert answer.status_code == NOT_FOUND_STATUS  # The ID with a line break is an unknown run.
    messages = [record.getMessage() for record in caplog.records if record.name == ROUTE_LOGGER]  # Route lines.
    refusals = [message for message in messages if "found no run" in message]  # The line of the unknown run.
    assert len(refusals) == 1  # The route writes exactly one line for the unknown run.
    assert "\n" not in refusals[0]  # The line break stays escaped inside the one line.
    assert refusals[0].isascii()  # The project writes ASCII log lines only.
