"""Prove that a browser page view of a fault reads the error page, not raw JSON.

Why:
    Issue #3274. A browser that opened an unknown URL read the raw envelope
    ``{"error":{"code":"not_found",...}}``. The page held no portal layout and
    no link back to the site list. The registered fault handler answered
    ``json_error`` to every client. A browser page view now reads
    ``error.html``. The portal script and a JSON client keep the envelope.

Scope:
    An unknown path never reaches a route, so the session guard of a route
    never runs. Each test sends one request to the real application. Two
    scaffold routes reach the handlers that a real route reaches: one route
    aborts with a status, and one route raises a fault. No test reaches the
    cloud, ArangoDB, or Redis.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import re  # Reads the text of one element that carries a `data-testid` value.
from collections.abc import Iterator  # The client fixtures yield and then clean up.
from typing import NoReturn  # The scaffold routes never return.

import pytest  # The test framework of the project.
from flask import Flask, abort  # The application type, and the abort call of a scaffold route.
from flask.testing import FlaskClient  # The client type that drives every request.
from werkzeug.test import TestResponse  # The answer type of the test client.

from src.upgrade_portal.app import factory  # The module that owns the fault handler and the rule.
from src.upgrade_portal.app.config import ALLOWED_ADDRESSES_VARIABLE  # The variable that arms the allow list.
from src.upgrade_portal.runtime import identity  # The real session registry, so one client signs in for real.

UNKNOWN_PATH = "/unknown-upgrade-portal-route"  # The path of the issue. No route serves it.
POST_ONLY_PATH = "/auth/signout"  # A real route that answers `POST` only.
SIGN_IN_PATH = "/auth/signin"  # The public page that a blocked browser opens first.
ABORT_RULE = "/contract-scaffold-3274/abort/<int:status>"  # The scaffold rule that reaches one handler.
ABORT_PREFIX = "/contract-scaffold-3274/abort/"  # The test appends the status number to this prefix.
FAULT_PATH = "/contract-scaffold-3274/fault"  # A route that raises, so the unexpected fault path runs.

BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"  # A browser navigation.
BROWSER_HEADERS = {"Accept": BROWSER_ACCEPT}  # The headers of one page view.
HTML_TYPE = "text/html"  # A browser renders an answer of this type as a page.
JSON_TYPE = "application/json"  # The contract binds every JSON answer to this type.

NOT_FOUND_STATUS = 404  # The status of a path that no route serves.
NOT_ALLOWED_STATUS = 405  # The status of a method that the matched path refuses.
FAULT_STATUS = 500  # The status of an unexpected fault.
FORBIDDEN_STATUS = 403  # The status of a request from outside the address allow list.
BLOCKED_NETWORK = "10.255.255.0/24"  # The loopback address of the test client is not in this network.
SESSION_COOKIE = "session"  # The Flask cookie that holds the signed session and its token.

SITE_LIST_LINK = "error-site-list-link"  # The handle of the link that every error page shows.
SIGNOUT_BUTTON = "signout-button"  # The header control that only a live session can use.
PROBE_EMAIL = "unknown.url.contract@example.invalid"  # A reserved address that reaches no mail service.
PATH_MARKER = "probe-3274-path-marker"  # A unique text inside a requested path. The page must not repeat it.
FAULT_SECRET = "contract-scaffold-3274-private-value"  # The fault text. No page may repeat it.

# A fault class, a fault text, a file path, and a stack trace each name the
# inside of the portal. The page for a person must hold none of them (FR-004).
LEAK_MARKERS = ("Traceback", "ZeroDivisionError", 'File "', "site-packages", FAULT_SECRET)

# Each client below states no preference for HTML, so each one keeps the JSON
# envelope (FR-006). The two asset values are the values that a browser sends
# for a stylesheet and for an image.
JSON_CLIENTS = {
    "no accept header": {},  # The Flask test client and many tools send no header.
    "a json client": {"Accept": JSON_TYPE},  # A client that asks for JSON by name.
    "any type": {"Accept": "*/*"},  # The default value of `fetch` and of `curl`.
    "the portal script": {"X-Requested-With": "XMLHttpRequest", "Accept": BROWSER_ACCEPT},  # The script header wins.
    "a stylesheet": {"Accept": "text/css,*/*;q=0.1"},  # A browser asks for a missing stylesheet.
    "an image": {"Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"},  # A missing image.
}


def read_text(response: TestResponse, test_id: str) -> str:
    """Return the text inside the element that carries one test handle."""
    pattern = rf'data-testid="{re.escape(test_id)}"[^>]*>([^<]*)<'  # The element text up to the next tag.
    match = re.search(pattern, response.get_data(as_text=True))  # The page holds each handle once.
    assert match is not None, f"The page holds no element {test_id}."  # Name the missing handle.
    return match.group(1).strip()  # The template indents some values.


def read_methods(response: TestResponse) -> set[str]:
    """Return the method names of the `Allow` header as a set."""
    header = response.headers.get("Allow", "")  # A 405 answer must carry this header.
    return {name.strip().upper() for name in header.split(",") if name.strip()}  # Werkzeug promises no order.


def scaffold_abort(status: int) -> NoReturn:
    """Abort with one status, as a real route does when it finds no record."""
    abort(status)  # The bound fault handler answers the fault.


def scaffold_fault() -> NoReturn:
    """Raise a fault that no handler expects."""
    raise ZeroDivisionError(FAULT_SECRET)  # Only a real fault proves that the page hides its detail.


def always_wants_page() -> bool:
    """Answer that every request wants a page, so a test can prove which rule the handler reads."""
    return True  # The test replaces the rule of `factory.py` with this answer.


@pytest.fixture
def page_client(portal_app: Flask) -> Iterator[FlaskClient]:
    """Return a client with no session for the application with the scaffold routes."""
    portal_app.add_url_rule(ABORT_RULE, view_func=scaffold_abort, methods=["GET"])  # One route for each status.
    portal_app.add_url_rule(FAULT_PATH, view_func=scaffold_fault, methods=["GET"])  # The unexpected fault.
    portal_app.config["PROPAGATE_EXCEPTIONS"] = False  # Read the browser answer, not the pytest fault.
    with portal_app.test_client() as client:  # No session, like a browser that followed an old bookmark.
        yield client  # Each test reads the real answer.


@pytest.fixture
def blocked_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[FlaskClient]:
    """Return a client that the address allow list refuses."""
    monkeypatch.setenv(ALLOWED_ADDRESSES_VARIABLE, BLOCKED_NETWORK)  # No loopback address is inside this network.
    app = factory.create_app()  # The allow list reads the environment once, at build time.
    app.config.update(TESTING=True)  # The test mode of the other contract tests.
    with app.test_client() as client:  # The client sends from the loopback address.
        yield client  # Each request arrives from outside the list.


@pytest.fixture
def signed_in_client(portal_app: Flask) -> Iterator[FlaskClient]:
    """Return a client that holds a live operator session."""
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())  # The pair that the session check reads.
    session_record = identity.OperatorSession(  # A session with no cloud client.
        owner=owner,  # Bind the record to the browser cookie pair.
        cloud_session=object(),  # A plain object can make no cloud request.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,  # The session kind of the other page tests.
    )
    identity.SESSION_REGISTRY.register(session_record)  # The session check reads the registry on every request.
    try:  # Keep the cleanup active when an assertion fails.
        with portal_app.test_client() as client:  # Hold one browser session across the requests.
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The cookie half of the session.
            with client.session_transaction() as browser_session:  # The signed server-side session.
                browser_session[identity.SESSION_OWNER_KEY] = owner.key  # The session half of the pair.
            yield client  # Each test reads the real rendered page.
    finally:  # The process-wide registry must not affect a later test.
        identity.SESSION_REGISTRY.drop(owner.key)  # Remove the isolated operator record.


def test_a_page_view_of_an_unknown_path_reads_the_error_page(page_client: FlaskClient) -> None:
    """A browser page view of an unknown path reads status 404 and `error.html` (FR-001, FR-002)."""
    response = page_client.get(UNKNOWN_PATH, headers=BROWSER_HEADERS)  # The address of the issue.
    assert response.status_code == NOT_FOUND_STATUS  # The page keeps the status of the envelope.
    assert response.mimetype == HTML_TYPE  # A browser renders the answer as a page, not as raw text.
    assert read_text(response, "error-title") == factory.NO_PAGE_TITLE  # The heading names a missing page.
    assert read_text(response, "error-message") == factory.NO_PAGE_MESSAGE  # The sentence names the recovery.
    assert read_text(response, "error-status-code") == str(NOT_FOUND_STATUS)  # A support request quotes it.
    assert read_text(response, "error-code") == factory.ERROR_CODES[NOT_FOUND_STATUS]  # The stable code.
    assert read_text(response, SITE_LIST_LINK) == "Go to the site list"  # The way back that the issue asks for.


def test_a_page_with_no_session_shows_no_sign_out_control(page_client: FlaskClient) -> None:
    """A page view with no session reads a header with no sign-out control (#3275 FR-008)."""
    response = page_client.get(UNKNOWN_PATH, headers=BROWSER_HEADERS)  # No session exists.
    assert response.status_code == NOT_FOUND_STATUS  # The unknown path reaches the fault handler.
    assert response.mimetype == HTML_TYPE  # A page, so the missing control is a real header decision.
    assert f'data-testid="{SIGNOUT_BUTTON}"' not in response.get_data(as_text=True)  # Nothing to sign out of.


def test_a_signed_in_operator_keeps_the_header(signed_in_client: FlaskClient) -> None:
    """A signed-in operator reads the page with the sign-out control in the header."""
    response = signed_in_client.get(UNKNOWN_PATH, headers=BROWSER_HEADERS)  # A live session exists.
    assert response.status_code == NOT_FOUND_STATUS  # A session does not change the status.
    assert response.mimetype == HTML_TYPE  # The operator reads a page.
    assert f'data-testid="{SIGNOUT_BUTTON}"' in response.get_data(as_text=True)  # The live session can sign out.


def test_a_refused_method_reads_the_page_and_the_allow_header(page_client: FlaskClient) -> None:
    """A page view with a refused method reads status 405, the page, and the `Allow` header (FR-003)."""
    page = page_client.get(POST_ONLY_PATH, headers=BROWSER_HEADERS)  # A browser opens a post-only path.
    envelope = page_client.get(POST_ONLY_PATH)  # The same request from a client with no preference.
    assert page.status_code == NOT_ALLOWED_STATUS  # The page keeps the status of the envelope.
    assert page.mimetype == HTML_TYPE  # A browser renders the answer as a page.
    assert read_text(page, "error-code") == factory.ERROR_CODES[NOT_ALLOWED_STATUS]  # The stable code.
    assert "POST" in read_methods(page)  # HTTP requires the header to name the accepted methods.
    assert read_methods(page) == read_methods(envelope)  # The page and the envelope name the same methods.


def test_an_unexpected_fault_reads_the_page_with_no_detail(page_client: FlaskClient) -> None:
    """A page view that meets an unexpected fault reads status 500 and a page with no detail (FR-004)."""
    response = page_client.get(FAULT_PATH, headers=BROWSER_HEADERS)  # The route raises a fault.
    body = response.get_data(as_text=True)  # The whole page text.
    assert response.status_code == FAULT_STATUS  # The page keeps the status of the envelope.
    assert response.mimetype == HTML_TYPE  # A browser renders the answer as a page.
    assert read_text(response, "error-code") == factory.ERROR_CODES[FAULT_STATUS]  # The stable code.
    assert [marker for marker in LEAK_MARKERS if marker in body] == []  # Name each marker that leaked.


@pytest.mark.parametrize("status", sorted(factory.ERROR_CODES))
def test_each_bound_status_reads_the_page(page_client: FlaskClient, status: int) -> None:
    """Each status that the factory binds gives a page view the page with that status and code (FR-005)."""
    response = page_client.get(f"{ABORT_PREFIX}{status}", headers=BROWSER_HEADERS)  # The route aborts.
    assert response.status_code == status  # The page keeps the status of the envelope.
    assert response.mimetype == HTML_TYPE  # A browser renders the answer as a page.
    assert read_text(response, "error-status-code") == str(status)  # The page prints the status.
    assert read_text(response, "error-code") == factory.ERROR_CODES[status]  # The code of the envelope.


def test_a_route_that_finds_no_record_keeps_the_record_sentence(page_client: FlaskClient) -> None:
    """A 404 from a matched route keeps the record sentence, because the page itself exists."""
    response = page_client.get(f"{ABORT_PREFIX}{NOT_FOUND_STATUS}", headers=BROWSER_HEADERS)  # A route aborts.
    assert response.status_code == NOT_FOUND_STATUS  # The route answers the missing record.
    assert read_text(response, "error-message") == factory.ERROR_MESSAGES[NOT_FOUND_STATUS]  # A record sentence.
    assert read_text(response, "error-title") != factory.NO_PAGE_TITLE  # The page itself exists.


@pytest.mark.parametrize("headers", list(JSON_CLIENTS.values()), ids=list(JSON_CLIENTS))
def test_a_client_with_no_html_preference_keeps_the_envelope(page_client: FlaskClient, headers: dict[str, str]) -> None:
    """A client with no stated preference for HTML reads the same envelope as before (FR-006)."""
    response = page_client.get(UNKNOWN_PATH, headers=headers)  # The same unknown path.
    expected = factory.build_error_envelope(  # The envelope that the old handler answered.
        factory.ERROR_CODES[NOT_FOUND_STATUS],  # The stable code.
        factory.ERROR_MESSAGES[NOT_FOUND_STATUS],  # The JSON sentence stays the same.
    )
    assert response.status_code == NOT_FOUND_STATUS  # The status stays the same.
    assert response.mimetype == JSON_TYPE  # A script parses the answer.
    assert response.get_json() == expected  # The body stays the same, key for key.


def test_the_page_never_repeats_the_requested_path(page_client: FlaskClient) -> None:
    """The page prints no part of the requested path, because the path is client text (FR-008)."""
    response = page_client.get(f"/<b>{PATH_MARKER}</b>", headers=BROWSER_HEADERS)  # A path with markup.
    body = response.get_data(as_text=True)  # The whole page text.
    assert response.status_code == NOT_FOUND_STATUS  # No route serves the path.
    assert response.mimetype == HTML_TYPE  # A page, so the check reads the rendered template.
    assert PATH_MARKER not in body  # The page repeats no client text.


def test_the_fault_handler_reads_the_one_rule(page_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """The fault handler reads `wants_browser_page` of `factory.py`, the rule of the token check (FR-007)."""
    monkeypatch.setattr(factory, "wants_browser_page", always_wants_page)  # Every request now wants a page.
    response = page_client.get(UNKNOWN_PATH)  # A request with no `Accept` header, which reads JSON by default.
    assert response.status_code == NOT_FOUND_STATUS  # The status stays the same.
    assert response.mimetype == HTML_TYPE  # The handler followed the replaced rule, so it reads the one rule.


def test_a_blocked_browser_keeps_the_short_envelope(blocked_client: FlaskClient) -> None:
    """A page view from outside the allow list reads the short envelope and no session cookie (FR-009)."""
    response = blocked_client.get(SIGN_IN_PATH, headers=BROWSER_HEADERS)  # The first page view of a blocked browser.
    expected = factory.build_error_envelope(  # The envelope that the old guard answered.
        factory.ERROR_CODES[FORBIDDEN_STATUS],  # The stable code.
        factory.ERROR_MESSAGES[FORBIDDEN_STATUS],  # The generic sentence names no part of the portal.
    )
    assert response.status_code == FORBIDDEN_STATUS  # The guard keeps its status.
    assert response.mimetype == JSON_TYPE  # A blocked address never reads a page.
    assert response.get_json() == expected  # The body stays the same, key for key.
    assert blocked_client.get_cookie(SESSION_COOKIE) is None  # No token field ran, so no session cookie exists.
