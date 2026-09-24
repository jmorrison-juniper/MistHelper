"""Prove that a refused browser form post reads an error page, not raw JSON.

Why:
    Issue #3275. Every form post carries a security token. When the token check
    failed, `csrf_error_response` answered the JSON envelope to every client. A
    browser shows that envelope as raw text, so the operator lost the form and
    found no way back. A browser form post now reads `error.html` with a link
    back to the form. The portal script and a JSON client keep the envelope.

Scope:
    The token check runs in a `before_request` hook, before the session guard of
    any route. So each test posts to the real mode form with no session and no
    token. No test reaches the cloud, ArangoDB, or Redis.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # The log check reads the records of the security logger.
import re  # Reads the text of one element that carries a `data-testid` value.
from collections.abc import Iterator  # The signed-in client fixture yields and then cleans up.
from html.parser import HTMLParser  # Reads the attributes of each element that carries a test handle.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.
from flask.testing import FlaskClient  # The client type that drives every request.
from werkzeug.test import TestResponse  # The answer type of the test client.

from src.upgrade_portal.app import factory  # The module that owns the one negotiation rule.
from src.upgrade_portal.app.routes import auth, select  # The two route modules that read the rule.
from src.upgrade_portal.runtime import identity  # The real session registry, so one client signs in for real.

FORM_PATH = "/select/mode"  # A plain form post that `portal.js` never intercepts.
FORM_BODY = {"mode": "single_site"}  # The field that the mode form sends.
BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"  # A browser navigation.
SCRIPT_HEADERS = {"X-Requested-With": "XMLHttpRequest", "Accept": "text/html"}  # A script inside a page.
PORTAL_ORIGIN = "http://localhost"  # The host that the Flask test client names in each request.

CSRF_STATUS = 400  # The contract binds this status to a missing token, for a page and for JSON.
CSRF_MISSING_CODE = "csrf_missing"  # The contract binds this code to a missing token.
PAGE_TITLE = "The portal refused the form"  # The heading that names the refusal for a person.
BACK_LINK = "error-back-link"  # The handle of the link back to the form page.
SITE_LIST_LINK = "error-site-list-link"  # The handle of the link that every error page shows.
SIGNOUT_BUTTON = "signout-button"  # The header control that only a live session can use.
REFUSED_TOKEN = "stale-token-value-for-issue-3275"  # A token value that the page and the log must not show.
SECURITY_LOGGER = "src.upgrade_portal.app.security"  # The logger of the token check.
PROBE_EMAIL = "csrf.page.contract@example.invalid"  # A reserved address that reaches no mail service.

# Each referrer below must give no link back, and the site list link must stay (FR-004).
REFUSED_REFERRERS = {
    "another host": "http://evil.example/select/mode",  # A page of another origin.
    "two leading slashes": f"{PORTAL_ORIGIN}//evil.example/select/mode",  # A browser reads `//` as a host.
    "a backslash": f"{PORTAL_ORIGIN}/\\evil.example",  # A browser reads `/\\` as `//`.
    "no route": f"{PORTAL_ORIGIN}/no/such/page",  # The URL map serves no page here.
    "a post-only route": f"{PORTAL_ORIGIN}/auth/signout",  # The path answers `POST` only.
    "no address": "not-an-address",  # A value with no host at all.
}


class HandleAttributeReader(HTMLParser):
    """Collect the attributes of each element that carries a `data-testid` value."""

    def __init__(self) -> None:
        """Start with no element at all."""
        super().__init__()  # The base parser keeps its own buffer.
        self.by_test_id: dict[str, dict[str, str]] = {}  # One attribute map for each test handle.

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record the attributes of one element that carries a test handle."""
        values = {name: value or "" for name, value in attrs}  # The parser decodes each entity in a value.
        test_id = values.get("data-testid")  # Most elements carry no handle.
        if test_id:  # Keep only the elements that a test can name.
            self.by_test_id[test_id] = values  # A later element with the same handle replaces an earlier one.


def read_attributes(response: TestResponse) -> dict[str, dict[str, str]]:
    """Return the attribute map of each test handle in one page."""
    reader = HandleAttributeReader()  # A fresh parser for each page.
    reader.feed(response.get_data(as_text=True))  # Parse the whole page body.
    return reader.by_test_id  # The handles and their attributes.


def read_text(response: TestResponse, test_id: str) -> str:
    """Return the text inside the element that carries one test handle."""
    pattern = rf'data-testid="{re.escape(test_id)}"[^>]*>([^<]*)<'  # The element text up to the next tag.
    match = re.search(pattern, response.get_data(as_text=True))  # The page holds each handle once.
    assert match is not None, f"The page holds no element {test_id}."  # Name the missing handle.
    return match.group(1).strip()  # The template indents some values.


def post_form(client: FlaskClient, headers: dict[str, str], referrer: str | None = None) -> TestResponse:
    """Post the mode form with no token and return the answer."""
    sent = dict(headers)  # Keep the caller map unchanged.
    if referrer is not None:  # A browser names the form page in this header.
        sent["Referer"] = referrer  # HTTP spells the header name with one `r`.
    return client.post(FORM_PATH, data=FORM_BODY, headers=sent)  # The token check refuses the post.


@pytest.fixture
def refusal_client(portal_app: Flask) -> FlaskClient:
    """Return a client with no session, so the token check refuses every post."""
    return portal_app.test_client()  # No session and no token, like a browser after a portal restart.


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


def test_a_browser_form_post_without_a_token_reads_the_error_page(refusal_client: FlaskClient) -> None:
    """A browser form post with no token reads status 400 and `error.html` (FR-001, FR-002, FR-008)."""
    response = post_form(refusal_client, {"Accept": BROWSER_ACCEPT})  # A navigation with no referrer.
    assert response.status_code == CSRF_STATUS  # The page keeps the contract status.
    assert response.mimetype == "text/html"  # A browser renders the answer as a page.
    assert read_text(response, "error-code") == CSRF_MISSING_CODE  # The code that a support request quotes.
    assert read_text(response, "error-status-code") == str(CSRF_STATUS)  # The status that the page prints.
    assert read_text(response, "error-title") == PAGE_TITLE  # The heading names the refusal.
    assert "Open the form again" in read_text(response, "error-message")  # The sentence names the recovery.
    attributes = read_attributes(response)  # The links of the page.
    assert attributes[SITE_LIST_LINK]["href"] == "/select/site"  # The site list link always stays.
    assert BACK_LINK not in attributes  # No referrer, so no link back.
    assert SIGNOUT_BUTTON not in attributes  # No session, so the header offers no sign-out control.


def test_a_live_session_with_a_stale_token_keeps_the_header(signed_in_client: FlaskClient) -> None:
    """A live session reads the page with the sign-out control and the link back (FR-003, FR-008)."""
    body = {**FORM_BODY, "csrf_token": REFUSED_TOKEN}  # A token that a second sign-in made stale.
    headers = {"Accept": BROWSER_ACCEPT, "Referer": f"{PORTAL_ORIGIN}{FORM_PATH}"}  # A browser form post.
    response = signed_in_client.post(FORM_PATH, data=body, headers=headers)  # The check refuses the token.
    assert response.status_code == CSRF_STATUS  # The page keeps the contract status.
    attributes = read_attributes(response)  # The controls of the page.
    assert SIGNOUT_BUTTON in attributes  # The live session can still sign out.
    assert attributes[BACK_LINK]["href"] == FORM_PATH  # The operator opens the form again.


def test_the_page_links_back_to_the_form_page(refusal_client: FlaskClient) -> None:
    """A same-origin referrer gives a link back to the form page (FR-003)."""
    response = post_form(refusal_client, {"Accept": BROWSER_ACCEPT}, f"{PORTAL_ORIGIN}{FORM_PATH}")
    assert response.status_code == CSRF_STATUS  # The page keeps the contract status.
    assert read_attributes(response)[BACK_LINK]["href"] == FORM_PATH  # The path only, never the host.


def test_the_link_back_keeps_the_query(refusal_client: FlaskClient) -> None:
    """The link back keeps the query, so a filtered list opens with the same filter (FR-003)."""
    referrer = f"{PORTAL_ORIGIN}/select/site?search=branch&page=2"  # A site list with a filter.
    response = post_form(refusal_client, {"Accept": BROWSER_ACCEPT}, referrer)
    assert read_attributes(response)[BACK_LINK]["href"] == "/select/site?search=branch&page=2"  # Both fields.


@pytest.mark.parametrize("referrer", list(REFUSED_REFERRERS.values()), ids=list(REFUSED_REFERRERS))
def test_an_unsafe_referrer_gives_no_link_back(refusal_client: FlaskClient, referrer: str) -> None:
    """A referrer that names no safe page of this portal gives no link back (FR-004)."""
    response = post_form(refusal_client, {"Accept": BROWSER_ACCEPT}, referrer)
    assert response.status_code == CSRF_STATUS  # The refusal still answers the page.
    attributes = read_attributes(response)  # The links of the page.
    assert BACK_LINK not in attributes  # The page refuses the referrer.
    assert attributes[SITE_LIST_LINK]["href"] == "/select/site"  # The operator still has a way out.


def test_markup_in_the_referrer_stays_text(refusal_client: FlaskClient) -> None:
    """Jinja escapes the link back, so markup in the query cannot add an element (FR-007)."""
    referrer = f'{PORTAL_ORIGIN}/select/site?q="><b data-testid="injected">x</b>'  # A client can send raw markup.
    response = post_form(refusal_client, {"Accept": BROWSER_ACCEPT}, referrer)
    attributes = read_attributes(response)  # The elements of the page.
    assert "injected" not in attributes  # The markup never became an element.
    assert attributes[BACK_LINK]["href"] == '/select/site?q="><b data-testid="injected">x</b>'  # Kept as text.


def test_a_script_post_keeps_the_json_envelope(refusal_client: FlaskClient) -> None:
    """The script header wins over a browser `Accept` value (FR-005)."""
    response = post_form(refusal_client, SCRIPT_HEADERS, f"{PORTAL_ORIGIN}{FORM_PATH}")
    assert response.status_code == CSRF_STATUS  # The contract status.
    assert response.mimetype == "application/json"  # The script reads JSON, whatever the page states.
    assert response.get_json()["error"]["code"] == CSRF_MISSING_CODE  # The contract code.


@pytest.mark.parametrize("headers", [{}, {"Accept": "application/json"}, {"Accept": "*/*"}], ids=str)
def test_a_client_with_no_html_preference_keeps_the_json_envelope(
    refusal_client: FlaskClient, headers: dict[str, str]
) -> None:
    """A client that states no preference for HTML keeps the JSON envelope (FR-005)."""
    response = post_form(refusal_client, headers, f"{PORTAL_ORIGIN}{FORM_PATH}")
    assert response.status_code == CSRF_STATUS  # The contract status.
    assert response.mimetype == "application/json"  # Only a stated preference for HTML earns a page.
    assert response.get_json()["error"]["code"] == CSRF_MISSING_CODE  # The contract code.


def test_the_page_and_the_log_never_show_the_refused_token(
    refusal_client: FlaskClient, caplog: pytest.LogCaptureFixture
) -> None:
    """The page and the log name the fault class only, never the token value (FR-007)."""
    caplog.set_level(logging.INFO, logger=SECURITY_LOGGER)  # Capture the refusal line of the token check.
    body = {**FORM_BODY, "csrf_token": REFUSED_TOKEN}  # A stale token from an old session.
    response = refusal_client.post(FORM_PATH, data=body, headers={"Accept": BROWSER_ACCEPT})
    assert response.status_code == CSRF_STATUS  # The check refused the stale token.
    assert REFUSED_TOKEN not in response.get_data(as_text=True)  # The page shows no token.
    assert REFUSED_TOKEN not in caplog.text  # The log shows no token.
    assert "CSRFError" in caplog.text  # The log names the fault class.


def test_the_route_modules_read_the_one_rule() -> None:
    """The token check and both route modules read one rule (FR-006)."""
    assert auth.wants_browser_page is factory.wants_browser_page  # The sign-in routes hold no copy.
    assert select.wants_browser_page is factory.wants_browser_page  # The selection routes hold no copy.
