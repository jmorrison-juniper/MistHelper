"""Contract tests for the transport security controls of the upgrade capture portal.

Why:
    Four controls stand between a browser and a live firmware upgrade: the proxy
    trust boundary, the response header set, the cross-site request forgery
    token, and the session guard. A change that weakens one control leaves no
    visible mark on a page, so only a test finds it. These tests hold the exact
    contract value of each control. A test fails when a value grows weaker, and a
    test fails when a value disappears.

    Every expected value below is literal text. These tests import no constant
    from ``src.upgrade_portal.app.security``, because a test that reads the
    value it checks proves nothing. A weakened constant must break a test.

    The token rule and the session rule come from
    ``specs/1823-upgrade-capture-portal/contracts/README.md``. The status codes
    come from the same file.

    ``flask-wtf`` skips the token check when the request matches no route, so a
    request to an absent path answers 404 and never ``csrf_missing``. The
    fixtures below therefore add three probe routes to the application object
    in memory. No probe route reaches a source file.

    No test opens a socket, and no test reaches the Mist cloud.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask, Response, jsonify, render_template, request
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.runtime import identity

# ---------------------------------------------------------------------------
# The contract values. Every value below is literal, never imported.
# ---------------------------------------------------------------------------

# WHY: The policy names 'self' only. A reader compares this block against the
# response one directive at a time, so a single added source stands out.
EXPECTED_CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self'; "
    "connect-src 'self'; "
    "font-src 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "object-src 'none'"
)

# WHY: The full header set that every response must carry. A missing entry and
# a changed value both fail, because the test compares the whole pair.
EXPECTED_HEADERS: dict[str, str] = {
    "Content-Security-Policy": EXPECTED_CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-store",
}

# WHY: Each entry below defeats the policy. A future change that adds one of
# these sources must fail loudly, even when the rest of the policy still reads
# well.
FORBIDDEN_POLICY_SOURCES = (
    "'unsafe-inline'",
    "'unsafe-eval'",
    "'unsafe-hashes'",
    "*",
    "data:",
    "blob:",
    "http:",
    "https:",
)

# WHY: A directive that disappears leaves the browser on its default, which is
# wide open for that resource type. Each pair below must survive on its own.
REQUIRED_POLICY_DIRECTIVES = (
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self'",
    "connect-src 'self'",
    "font-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "object-src 'none'",
)

CSRF_MISSING_CODE = "csrf_missing"  # WHY: contracts/README.md fixes this code.
CSRF_MISSING_STATUS = 400  # WHY: contracts/README.md fixes this status.
NOT_AUTHENTICATED_CODE = "not_authenticated"  # WHY: contracts/README.md fixes this code.
NOT_AUTHENTICATED_STATUS = 401  # WHY: contracts/README.md fixes this status.

CSRF_HEADER_NAME = "X-CSRFToken"  # WHY: contracts/README.md names this header.
CSRF_FIELD_NAME = "csrf_token"  # WHY: partials/nav.html posts the token in this field.
CSRF_META_NAME = "csrf-token"  # WHY: contracts/ui-testids.md names this meta tag.

# ---------------------------------------------------------------------------
# The probe routes. These routes exist in memory for one test only.
# ---------------------------------------------------------------------------

PROBE_STATE_PATH = "/_probe/state-change"  # WHY: A real route, so the token check runs.
PROBE_TOKEN_PATH = "/_probe/token"  # WHY: Renders the real layout, so a test reads the real meta tag.
PROBE_GUARDED_PATH = "/_probe/guarded"  # WHY: Carries the real require_session guard.
PROBE_ABSENT_PATH = "/_probe/absent"  # WHY: Matches no route, so the portal answers 404.
PROBE_PEER_PATH = "/_probe/peer"  # WHY: Reports the address and the scheme that the portal read.
STATIC_ASSET_PATH = "/static/css/portal.css"  # WHY: A real file that Flask serves from the static route.

PROBE_BODY_MARKER = "probe-route-body-ran"  # WHY: Proof that the route body ran.
PROBE_CALL_LOG_KEY = "PROBE_CALL_LOG"  # WHY: The application config carries the call log to a test.
PROBE_EMAIL = "probe.operator@example.invalid"  # WHY: A reserved domain, so the address reaches no mail server.

# ---------------------------------------------------------------------------
# The proxy trust values. Every address below comes from RFC 5737, which
# reserves these ranges for documentation. No address reaches a real host.
# ---------------------------------------------------------------------------

PROXY_HOPS_VARIABLE = "CAPTURE_PROXY_HOPS"  # WHY: The operator states the trusted count here.
ALLOW_LIST_VARIABLE = "CAPTURE_ALLOWED_IPS"  # WHY: The proxy tests must clear this guard.
FORWARDED_FOR_HEADER = "X-Forwarded-For"  # WHY: The header that carries the client address.
FORWARDED_PROTO_HEADER = "X-Forwarded-Proto"  # WHY: The header that carries the scheme.
SECURE_SCHEME = "https"  # WHY: The value a proxy writes after it terminates the connection.

SOCKET_ADDRESS = "192.0.2.10"  # WHY: The address of the caller that opened the socket.
TRUE_CLIENT_ADDRESS = "203.0.113.9"  # WHY: The address that a trusted proxy wrote.
FORGED_ADDRESS = "198.51.100.4"  # WHY: The address that a caller put in the header itself.

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")  # WHY: contracts/README.md exempts a request that changes no state.

RESPONSE_KINDS = ("success", "not_found", "csrf_refusal", "guard_refusal", "static_file")

# WHY: The header test asserts this status first. A header assertion on a 500
# page would pass and prove nothing, so the status pins the response first.
EXPECTED_STATUS: dict[str, int] = {
    "success": 200,
    "not_found": 404,
    "csrf_refusal": CSRF_MISSING_STATUS,
    "guard_refusal": NOT_AUTHENTICATED_STATUS,
    "static_file": 200,
}

# WHY: A refusal must name no operator and no source file. Each fragment below
# marks a leak that a reader of the response could use.
LEAK_FRAGMENTS = ("Traceback", 'File "', ".py", "/src/", "\\src\\", "site-packages")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def probe_app(portal_app: Flask) -> Flask:
    """Add the three probe routes to the portal application.

    Why:
        The application registers only ``/healthz`` and ``/static`` at this
        phase. The token check needs a route that changes state, and the
        session guard needs a route that carries the guard. A test may not add
        a route to a source file, so the fixture adds each route to the
        application object in memory.

    Args:
        portal_app: The application from the shared contract fixture.

    Returns:
        The same application with the probe routes in place.
    """
    call_log: list[str] = []  # WHY: Records each probe body that ran during one test.
    portal_app.config[PROBE_CALL_LOG_KEY] = call_log  # WHY: The config hands the log to a test.

    def state_change() -> tuple[Response, int]:
        """Answer a request that the token check protects.

        Returns:
            The marker body and the status 200.
        """
        call_log.append("state_change")
        return jsonify({"probe": PROBE_BODY_MARKER}), 200

    def token_page() -> str:
        """Render the real layout, which holds the token meta tag.

        Returns:
            The rendered page.
        """
        return render_template("layout.html")

    def guarded_view() -> tuple[Response, int]:
        """Answer a request that passed the session guard.

        Returns:
            The marker body and the status 200.
        """
        call_log.append("guarded")
        return jsonify({"probe": PROBE_BODY_MARKER}), 200

    portal_app.add_url_rule(PROBE_STATE_PATH, "probe_state_change", state_change, methods=["GET", "POST"])
    portal_app.add_url_rule(PROBE_TOKEN_PATH, "probe_token_page", token_page, methods=["GET"])
    # WHY: The real decorator, so the test checks the shipped guard and no copy of it.
    portal_app.add_url_rule(
        PROBE_GUARDED_PATH,
        "probe_guarded",
        identity.require_session(guarded_view),
        methods=["GET"],
    )
    return portal_app


@pytest.fixture
def probe_client(probe_app: Flask) -> Iterator[FlaskClient]:
    """Return a test client that reaches the probe routes.

    Why:
        The shared ``portal_client`` fixture builds its client from the plain
        application. This client comes from the application that carries the
        probe routes, so the order of the two fixtures cannot matter.

    Args:
        probe_app: The application with the probe routes.

    Yields:
        The Flask test client. The context manager holds the session open.
    """
    with probe_app.test_client() as client:
        yield client


@pytest.fixture
def registered_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator in the process session registry.

    Why:
        The guard admits a request only when the signed browser session and the
        browser cookie both name a registered owner. The registry is a process
        global, so the fixture drops the record again. A leaked record would
        sign in a later test by accident.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())
    record = identity.OperatorSession(
        owner=owner,
        cloud_session=object(),  # WHY: A plain object stands in for the cloud session. No cloud call runs.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)
    try:
        yield owner
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # WHY: The registry outlives the test, so clear it here.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fetch_probe_response(client: FlaskClient, kind: str) -> TestResponse:
    """Return one response of the named kind.

    Args:
        client: The test client.
        kind: One name from ``RESPONSE_KINDS``.

    Returns:
        The response that the portal built.

    Raises:
        ValueError: If the name matches no kind.
    """
    if kind == "success":
        return client.get(PROBE_STATE_PATH)
    if kind == "not_found":
        return client.get(PROBE_ABSENT_PATH)
    if kind == "csrf_refusal":
        return client.post(PROBE_STATE_PATH)  # WHY: No token, so the token check refuses.
    if kind == "guard_refusal":
        return client.get(PROBE_GUARDED_PATH)  # WHY: No session, so the guard refuses.
    if kind == "static_file":
        return client.get(STATIC_ASSET_PATH)
    raise ValueError(f"The response kind {kind} is unknown.")


def read_error_code(response: TestResponse) -> str:
    """Return the ``code`` field of an error envelope.

    Why:
        ``contracts/README.md`` states that a test asserts on ``code`` and never
        on ``message``. One reader keeps every test on that rule.

    Args:
        response: The response that holds the envelope.

    Returns:
        The error code.
    """
    payload: dict[str, Any] = response.get_json()
    return str(payload["error"]["code"])


def read_meta_token(client: FlaskClient) -> str:
    """Return the token that the real layout renders into its meta tag.

    Why:
        The browser reads the token from this tag. A test that mints its own
        token would pass while the page shipped an empty tag.

    Args:
        client: The test client whose session receives the token.

    Returns:
        The token text.
    """
    page = client.get(PROBE_TOKEN_PATH)
    body = page.get_data(as_text=True)
    # WHY: The tag spans three lines in layout.html, so the pattern crosses a newline.
    match = re.search(rf'name="{CSRF_META_NAME}"[\s\S]*?content="([^"]*)"', body)
    return "" if match is None else match.group(1)


def sign_in_client(client: FlaskClient, owner: identity.SessionOwner) -> None:
    """Give one test client the session and the cookie of a registered owner.

    Why:
        The guard checks the signed session against the browser cookie. Both
        halves must agree, so this helper sets both in one place.

    Args:
        client: The test client to sign in.
        owner: The identity pair from the ``registered_owner`` fixture.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
    with client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = owner.key


# ---------------------------------------------------------------------------
# The response header set
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("kind", RESPONSE_KINDS)
def test_each_probe_response_reaches_the_expected_status(probe_client: FlaskClient, kind: str) -> None:
    """Each probe response reaches the status that the header tests rest on.

    Why:
        A header assertion against an unexpected 500 page would pass and prove
        nothing. This test pins each status first, so a later header failure
        names a header fault and never a routing fault.

    Args:
        probe_client: The test client.
        kind: The response kind under test.
    """
    response = fetch_probe_response(probe_client, kind)
    assert response.status_code == EXPECTED_STATUS[kind]


@pytest.mark.parametrize(("header", "value"), sorted(EXPECTED_HEADERS.items()))
@pytest.mark.parametrize("kind", RESPONSE_KINDS)
def test_every_response_carries_every_security_header(
    probe_client: FlaskClient,
    kind: str,
    header: str,
    value: str,
) -> None:
    """Every response carries the full header set with the exact contract value.

    Why:
        A header that appears on a page and disappears on an error page gives
        false comfort. The success page, the 404 page, the token refusal, the
        session refusal, and a static file all pass through the same hook, so
        all five must carry the same headers.

    Args:
        probe_client: The test client.
        kind: The response kind under test.
        header: The header name.
        value: The exact header value the contract requires.
    """
    response = fetch_probe_response(probe_client, kind)
    assert response.status_code == EXPECTED_STATUS[kind]
    assert response.headers.get(header) == value


def test_content_security_policy_matches_the_contract_exactly(probe_client: FlaskClient) -> None:
    """The policy text matches the contract character for character.

    Why:
        A weakened policy still reads well. Only the full text catches an added
        source, a dropped directive, or a reordered rule.

    Args:
        probe_client: The test client.
    """
    response = probe_client.get(PROBE_STATE_PATH)
    assert response.headers["Content-Security-Policy"] == EXPECTED_CONTENT_SECURITY_POLICY


@pytest.mark.parametrize("forbidden", FORBIDDEN_POLICY_SOURCES)
def test_content_security_policy_holds_no_unsafe_source(probe_client: FlaskClient, forbidden: str) -> None:
    """The policy names no unsafe source and no wildcard host.

    Why:
        The portal drives a firmware upgrade. One inline script source would
        let an injected script start work on a live site, so each unsafe source
        below fails on its own and names itself in the failure.

    Args:
        probe_client: The test client.
        forbidden: The source that the policy must never hold.
    """
    policy = probe_client.get(PROBE_STATE_PATH).headers["Content-Security-Policy"]
    assert forbidden not in policy


@pytest.mark.parametrize("directive", REQUIRED_POLICY_DIRECTIVES)
def test_content_security_policy_keeps_every_required_directive(
    probe_client: FlaskClient,
    directive: str,
) -> None:
    """The policy keeps each directive with its exact source.

    Why:
        A browser falls back to its own default when a directive disappears,
        and that default is wide open. Each directive therefore stands as a
        separate check, so a deletion names the lost directive.

    Args:
        probe_client: The test client.
        directive: The directive and source pair that must survive.
    """
    policy = probe_client.get(PROBE_STATE_PATH).headers["Content-Security-Policy"]
    assert directive in policy


def test_the_static_route_carries_the_full_header_set(probe_client: FlaskClient) -> None:
    """A static file answers with every security header in place.

    Why:
        Flask builds a static response through its own sender, which sets its
        own cache header. The portal hook must overwrite that header, so a
        shared workstation keeps no page and no script in its cache.

    Args:
        probe_client: The test client.
    """
    response = probe_client.get(STATIC_ASSET_PATH)
    assert response.status_code == 200
    headers = dict(response.headers)
    # WHY: The failure then names every wrong header at once, with its value.
    wrong = {name: headers.get(name) for name, value in EXPECTED_HEADERS.items() if headers.get(name) != value}
    assert wrong == {}


# ---------------------------------------------------------------------------
# The cross-site request forgery token
# ---------------------------------------------------------------------------


def test_post_without_a_token_returns_csrf_missing(probe_client: FlaskClient) -> None:
    """A state-changing request with no token receives 400 and ``csrf_missing``.

    Args:
        probe_client: The test client.
    """
    response = probe_client.post(PROBE_STATE_PATH)
    assert response.status_code == CSRF_MISSING_STATUS
    assert read_error_code(response) == CSRF_MISSING_CODE


def test_post_without_a_token_never_runs_the_route_body(probe_app: Flask, probe_client: FlaskClient) -> None:
    """The token check stops the request before the route body runs.

    Why:
        A refusal that answers 400 after the work started would still start a
        firmware upgrade. The empty call log is the only proof that the check
        runs first.

    Args:
        probe_app: The application that holds the call log.
        probe_client: The test client.
    """
    probe_client.post(PROBE_STATE_PATH)
    call_log: list[str] = probe_app.config[PROBE_CALL_LOG_KEY]
    assert call_log == []


def test_post_with_a_malformed_token_is_refused(probe_client: FlaskClient) -> None:
    """A token that carries no valid signature receives 400 and ``csrf_missing``.

    Args:
        probe_client: The test client.
    """
    response = probe_client.post(PROBE_STATE_PATH, headers={CSRF_HEADER_NAME: "this-value-is-not-a-token"})
    assert response.status_code == CSRF_MISSING_STATUS
    assert read_error_code(response) == CSRF_MISSING_CODE


def test_post_with_a_token_from_another_session_is_refused(probe_app: Flask, probe_client: FlaskClient) -> None:
    """A valid token from a second browser receives 400 and ``csrf_missing``.

    Why:
        This case is the attack the token exists to stop. The token carries a
        valid signature, so only the session binding can refuse it. A check
        that read the signature alone would pass this request.

    Args:
        probe_app: The application, which builds the second client.
        probe_client: The first client, which supplies the stolen token.
    """
    stolen_token = read_meta_token(probe_client)
    assert stolen_token != ""
    with probe_app.test_client() as second_client:
        read_meta_token(second_client)  # WHY: The second browser needs a token of its own first.
        response = second_client.post(PROBE_STATE_PATH, headers={CSRF_HEADER_NAME: stolen_token})
    assert response.status_code == CSRF_MISSING_STATUS
    assert read_error_code(response) == CSRF_MISSING_CODE


def test_the_layout_meta_tag_carries_a_token(probe_client: FlaskClient) -> None:
    """The real layout renders a non-empty token into the ``csrf-token`` meta tag.

    Why:
        The template renders an empty tag when the security layer registers no
        token global. The page then looks correct and every request fails, so
        the tag needs a check of its own.

    Args:
        probe_client: The test client.
    """
    assert read_meta_token(probe_client) != ""


def test_post_with_the_meta_tag_token_in_the_header_succeeds(probe_client: FlaskClient) -> None:
    """A request that carries the meta tag token in ``X-CSRFToken`` reaches the route.

    Why:
        A suite that only proves refusal cannot tell a working token layer from
        one that blocks every request. This test proves the accepted path, and
        it proves it with the exact token that the browser would read.

    Args:
        probe_client: The test client.
    """
    token = read_meta_token(probe_client)
    response = probe_client.post(PROBE_STATE_PATH, headers={CSRF_HEADER_NAME: token})
    assert response.status_code == 200
    assert response.get_json() == {"probe": PROBE_BODY_MARKER}


def test_post_with_the_token_in_the_form_field_succeeds(probe_client: FlaskClient) -> None:
    """A form that posts the token in the ``csrf_token`` field reaches the route.

    Why:
        The sign-out control in ``partials/nav.html`` is a plain form, so it
        sends the token as a field and never as a header. That path needs its
        own proof.

    Args:
        probe_client: The test client.
    """
    token = read_meta_token(probe_client)
    response = probe_client.post(PROBE_STATE_PATH, data={CSRF_FIELD_NAME: token})
    assert response.status_code == 200
    assert response.get_json() == {"probe": PROBE_BODY_MARKER}


@pytest.mark.parametrize("method", SAFE_METHODS)
def test_a_safe_method_needs_no_token(probe_client: FlaskClient, method: str) -> None:
    """A request that changes no state passes with no token.

    Why:
        A token check on a read request would break every page load. The
        contract exempts a request that changes no state, so each safe method
        must reach the route.

    Args:
        probe_client: The test client.
        method: The safe method under test.
    """
    response = probe_client.open(PROBE_STATE_PATH, method=method)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# The not_authenticated guard
# ---------------------------------------------------------------------------


def test_the_guard_refuses_a_request_with_no_session(probe_client: FlaskClient) -> None:
    """A guarded route answers 401 and ``not_authenticated`` with no session.

    Args:
        probe_client: The test client.
    """
    response = probe_client.get(PROBE_GUARDED_PATH)
    assert response.status_code == NOT_AUTHENTICATED_STATUS
    assert read_error_code(response) == NOT_AUTHENTICATED_CODE


def test_the_guard_refusal_uses_the_documented_envelope(probe_client: FlaskClient) -> None:
    """The refusal holds the ``error`` envelope and nothing beside it.

    Why:
        ``contracts/README.md`` fixes one shape for every JSON error. A second
        top-level key would break every browser handler at once.

    Args:
        probe_client: The test client.
    """
    payload: dict[str, Any] = probe_client.get(PROBE_GUARDED_PATH).get_json()
    assert list(payload) == ["error"]
    assert set(payload["error"]) <= {"code", "message", "details"}


def test_the_guard_refusal_never_runs_the_route_body(probe_app: Flask, probe_client: FlaskClient) -> None:
    """The guard stops the request before the route body runs.

    Why:
        A guard that answers 401 after the route body ran would still read the
        cloud or start work. The empty call log is the only proof of the order.

    Args:
        probe_app: The application that holds the call log.
        probe_client: The test client.
    """
    probe_client.get(PROBE_GUARDED_PATH)
    call_log: list[str] = probe_app.config[PROBE_CALL_LOG_KEY]
    assert call_log == []


def test_the_guard_refusal_names_no_operator(
    probe_client: FlaskClient,
    registered_owner: identity.SessionOwner,
) -> None:
    """The refusal holds no email address and no email digest.

    Why:
        An unsigned visitor must learn nothing about the people who use the
        portal. A registered operator exists during this test, so a leak from
        the registry would show in the body.

    Args:
        probe_client: The test client, which carries no session.
        registered_owner: An operator that exists in the registry.
    """
    body = probe_client.get(PROBE_GUARDED_PATH).get_data(as_text=True)
    assert registered_owner.actor_email not in body
    assert registered_owner.email_digest not in body
    assert registered_owner.browser_id not in body
    assert "@" not in body


def test_the_guard_refusal_names_no_file_and_no_traceback(probe_client: FlaskClient) -> None:
    """The refusal holds no stack trace and no file path.

    Why:
        A stack trace names the package layout and the Python version, which
        helps an attacker pick a known fault. The refusal must stay short.

    Args:
        probe_client: The test client.
    """
    body = probe_client.get(PROBE_GUARDED_PATH).get_data(as_text=True)
    for fragment in LEAK_FRAGMENTS:
        assert fragment not in body


def test_the_guard_admits_a_signed_in_session(
    probe_app: Flask,
    probe_client: FlaskClient,
    registered_owner: identity.SessionOwner,
) -> None:
    """A request with a valid session and cookie reaches the route body.

    Why:
        A guard that refuses every request would pass every refusal test above
        and would still be broken. This test proves that the admitted path
        works and that the route body really ran.

    Args:
        probe_app: The application that holds the call log.
        probe_client: The test client.
        registered_owner: The operator that the client signs in as.
    """
    sign_in_client(probe_client, registered_owner)
    response = probe_client.get(PROBE_GUARDED_PATH)
    assert response.status_code == 200
    assert response.get_json() == {"probe": PROBE_BODY_MARKER}
    call_log: list[str] = probe_app.config[PROBE_CALL_LOG_KEY]
    assert call_log == ["guarded"]


def test_the_guard_refuses_a_session_without_the_browser_cookie(
    probe_client: FlaskClient,
    registered_owner: identity.SessionOwner,
) -> None:
    """A signed session that arrives from another browser receives 401.

    Why:
        FR-073 binds the session to the browser identity. A copied session
        cookie must not sign in a second computer, so the guard needs both
        halves of the pair.

    Args:
        probe_client: The test client, which sets no browser cookie.
        registered_owner: The operator that the session names.
    """
    with probe_client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = registered_owner.key
    response = probe_client.get(PROBE_GUARDED_PATH)
    assert response.status_code == NOT_AUTHENTICATED_STATUS
    assert read_error_code(response) == NOT_AUTHENTICATED_CODE


# ---------------------------------------------------------------------------
# The proxy trust boundary
# ---------------------------------------------------------------------------


def build_peer_client(monkeypatch: pytest.MonkeyPatch, trusted_hops: int) -> FlaskClient:
    """Return a client of a portal that trusts the named count of proxies.

    Why:
        The trusted count reaches the portal through the environment, and the
        portal reads it once while it builds. A test therefore needs its own
        application for each count, which the shared fixtures cannot give.

        The helper clears the address allow list. A leftover value would refuse
        the request before it reached the probe route, and the test would then
        pass for the wrong reason.

    Args:
        monkeypatch: The pytest patch helper, which restores the environment.
        trusted_hops: The count of proxies the portal must trust.

    Returns:
        A test client of the built portal, with one probe route in place.
    """
    factory = pytest.importorskip(  # WHY: The factory arrives at task T027, as in conftest.
        "src.upgrade_portal.app.factory",
        reason="The capture portal application factory is not built yet.",
    )
    monkeypatch.setenv(PROXY_HOPS_VARIABLE, str(trusted_hops))
    monkeypatch.delenv(ALLOW_LIST_VARIABLE, raising=False)  # WHY: The allow list must not refuse the probe.

    def report_peer() -> Response:
        """Report the address and the scheme that the portal read.

        Returns:
            The client address and the secure flag as JSON.
        """
        return jsonify({"address": request.remote_addr or "", "secure": request.is_secure})

    app = factory.create_app()
    app.config.update(TESTING=True)  # WHY: Test mode reports the real exception instead of a 500 page.
    app.add_url_rule(PROBE_PEER_PATH, "probe_peer", report_peer, methods=["GET"])
    return app.test_client()


def read_peer(client: FlaskClient, **kwargs: Any) -> dict[str, Any]:
    """Call the probe route and return what the portal read.

    Args:
        client: The client of a portal built by ``build_peer_client``.
        **kwargs: The headers and the environment values for the call.

    Returns:
        The address and the secure flag that the portal reported.
    """
    response = client.get(PROBE_PEER_PATH, **kwargs)
    assert response.status_code == 200  # WHY: A refusal would carry no address, so pin the status first.
    payload: dict[str, Any] = response.get_json()
    return payload


def test_no_trusted_proxy_ignores_the_forwarded_address(monkeypatch: pytest.MonkeyPatch) -> None:
    """A portal that trusts no proxy reads the socket address, never the header.

    Why:
        A forwarded header is text that any caller can send. A portal that read
        the header with no proxy in front of it would let a caller name its own
        address and walk through the network allow list.

    Args:
        monkeypatch: The pytest patch helper.
    """
    client = build_peer_client(monkeypatch, 0)
    peer = read_peer(
        client,
        headers={FORWARDED_FOR_HEADER: FORGED_ADDRESS},
        environ_base={"REMOTE_ADDR": SOCKET_ADDRESS},
    )
    assert peer["address"] == SOCKET_ADDRESS


def test_one_trusted_proxy_reads_the_forwarded_address(monkeypatch: pytest.MonkeyPatch) -> None:
    """A portal behind one proxy reads the address that the proxy wrote.

    Why:
        Behind a proxy the socket address belongs to the proxy, not to the
        client. Every client would then share one address, and the allow list
        would either admit every client or refuse every client.

    Args:
        monkeypatch: The pytest patch helper.
    """
    client = build_peer_client(monkeypatch, 1)
    peer = read_peer(
        client,
        headers={FORWARDED_FOR_HEADER: TRUE_CLIENT_ADDRESS},
        environ_base={"REMOTE_ADDR": SOCKET_ADDRESS},
    )
    assert peer["address"] == TRUE_CLIENT_ADDRESS


def test_a_prepended_forged_entry_cannot_move_the_trusted_position(monkeypatch: pytest.MonkeyPatch) -> None:
    """A forged first entry leaves the trusted entry in place.

    Why:
        A caller can prepend any entry to the forwarded header, so the proxy
        appends the true address to whatever arrived. The portal must count the
        entries from the right and read the entry that the outermost trusted
        proxy wrote. A portal that read the first entry would take the forged
        one every time.

    Args:
        monkeypatch: The pytest patch helper.
    """
    client = build_peer_client(monkeypatch, 1)
    forwarded_chain = f"{FORGED_ADDRESS}, {TRUE_CLIENT_ADDRESS}"  # WHY: The proxy appended the true address.
    peer = read_peer(
        client,
        headers={FORWARDED_FOR_HEADER: forwarded_chain},
        environ_base={"REMOTE_ADDR": SOCKET_ADDRESS},
    )
    assert peer["address"] == TRUE_CLIENT_ADDRESS


def test_a_trusted_proxy_with_no_header_keeps_the_socket_address(monkeypatch: pytest.MonkeyPatch) -> None:
    """A request that carries no forwarded header keeps the socket address.

    Why:
        This is the positive control for the trusted path. A portal that blanked
        the address when the header was absent would refuse every such request,
        and the tests above would still pass.

    Args:
        monkeypatch: The pytest patch helper.
    """
    client = build_peer_client(monkeypatch, 1)
    peer = read_peer(client, environ_base={"REMOTE_ADDR": SOCKET_ADDRESS})
    assert peer["address"] == SOCKET_ADDRESS


def test_no_trusted_proxy_ignores_the_forwarded_scheme(monkeypatch: pytest.MonkeyPatch) -> None:
    """A portal that trusts no proxy reads the request as plain text.

    Why:
        The scheme decides whether a cookie carries the ``Secure`` flag. A
        portal that believed a forwarded scheme with no proxy in front of it
        would set that flag on a plain connection, and the browser would then
        withhold the cookie on every later request.

    Args:
        monkeypatch: The pytest patch helper.
    """
    client = build_peer_client(monkeypatch, 0)
    peer = read_peer(client, headers={FORWARDED_PROTO_HEADER: SECURE_SCHEME})
    assert peer["secure"] is False


def test_one_trusted_proxy_reads_the_forwarded_scheme(monkeypatch: pytest.MonkeyPatch) -> None:
    """A portal behind one proxy reads a terminated connection as secure.

    Why:
        A proxy that terminates the connection speaks plain text to the portal.
        The portal would then read every request as plain text and would drop
        the ``Secure`` flag from the browser cookie, which would send that
        cookie over any later plain connection.

    Args:
        monkeypatch: The pytest patch helper.
    """
    client = build_peer_client(monkeypatch, 1)
    peer = read_peer(client, headers={FORWARDED_PROTO_HEADER: SECURE_SCHEME})
    assert peer["secure"] is True
