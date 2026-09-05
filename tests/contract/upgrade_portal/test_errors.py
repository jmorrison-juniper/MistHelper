"""Contract tests for the JSON error envelope and every documented status code.

Why:
    The portal drives a firmware upgrade, so an operator must read one clear
    answer from every failed call. The contract at
    ``specs/1823-upgrade-capture-portal/contracts/README.md`` allows one error
    shape and no other shape. These tests drive each error that the portal can
    produce today and check that one shape every time.

    Three routes in this module exist for the test alone. The portal registers
    no feature route yet, and the token guard of ``flask-wtf`` returns early
    when a request matches no endpoint. A post to an unknown path therefore
    answers 404 and never reaches the token check. The scaffold routes give the
    token guard and the error handlers a real endpoint to answer for. The
    scaffold adds no route to the source, and the handler under test is the
    handler that ``create_app`` registers.
"""

import re
from collections.abc import Iterator
from typing import Any, NoReturn

import pytest
from flask import Flask, Response, abort, jsonify, session
from flask.testing import FlaskClient
from flask_wtf.csrf import generate_csrf
from werkzeug.test import TestResponse

from src.upgrade_portal.app.config import ALLOWED_ADDRESSES_VARIABLE
from src.upgrade_portal.app.factory import create_app

HEALTH_PATH = "/healthz"  # Section 7 of the contract binds this path to the status 200.
UNKNOWN_PATH = "/no-such-page"  # No rule matches this path, so the router raises the 404 fault.

ABORT_RULE = "/contract-scaffold/abort/<int:status>"  # The scaffold rule that reaches one error handler.
ABORT_PATH_PREFIX = "/contract-scaffold/abort/"  # The test appends the status number to this prefix.
ECHO_PATH = "/contract-scaffold/echo"  # A real endpoint, so the token guard runs instead of returning early.
FAULT_PATH = "/contract-scaffold/fault"  # A route that raises, so the unexpected fault path runs.

ENVELOPE_KEY = "error"  # The contract wraps every error body under this one key.
REQUIRED_KEYS = frozenset({"code", "message"})  # The contract always requires these two keys.
ALLOWED_KEY_SETS = (REQUIRED_KEYS, REQUIRED_KEYS | {"details"})  # `details` is the one optional key.
CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")  # Rule 1 calls the code a fixed lower-case string.

JSON_TYPE = "application/json"  # The contract binds every JSON endpoint to this type.
CONTENT_TYPE_HEADER = "Content-Type"  # Read through the header table, because the property may answer None.
ALLOW_HEADER = "Allow"  # HTTP asks a 405 answer and an OPTIONS answer to name the allowed methods.

CSRF_HEADER = "X-CSRFToken"  # The contract names this header for the token value.
CSRF_FIELD_SETTING = "WTF_CSRF_FIELD_NAME"  # The setting that names the session key of the token.
CSRF_MISSING_CODE = "csrf_missing"  # The contract binds this code to a request with no valid token.

FORWARDED_HEADER = "X-Forwarded-For"  # A caller may send this header. The portal must not trust it.
BLOCKED_NETWORK = "10.255.255.0/24"  # The loopback address of the test client is not in this network.
ALLOWED_ADDRESS = "10.255.255.7"  # One address inside the network above, for the positive control.

FAULT_SECRET = "contract-scaffold-private-value"  # The fault text. No answer may repeat it.

# A file path, a class name, and a stack trace each name the inside of the
# portal. Rule 2 of the envelope forbids all three in the answer to the browser.
LEAK_MARKERS = (
    "Traceback",  # The first word of a Python stack trace.
    "ZeroDivisionError",  # The class name of the fault the scaffold raises.
    'File "',  # The line prefix of every stack trace frame.
    ".py",  # Any source file name.
    "site-packages",  # Any library path.
    FAULT_SECRET,  # The text of the fault itself.
)

# Every error status in the status table of the contract. The table also lists
# 200 and 202, which report success and therefore carry no envelope.
DOCUMENTED_ERROR_STATUSES = (400, 401, 403, 404, 409, 429, 500)

# The contract names a code word for these two statuses. It names a code word
# for the other statuses only inside one endpoint, so a bare abort at those
# statuses has no contract word to match.
CONTRACT_NAMED_CODES = (
    (401, "not_authenticated"),  # The Authentication section of the contract names this word.
    (429, "rate_limited"),  # Section 1 of the contract names this word for the sign-in call.
)

SUCCESS_STATUS = 200  # The status of a call that succeeded.
BAD_REQUEST_STATUS = 400  # The status of a malformed request and of a missing token.
FORBIDDEN_STATUS = 403  # The status of a call from outside the address allow list.
NOT_FOUND_STATUS = 404  # The status of a call to a path that no rule matches.
NOT_ALLOWED_STATUS = 405  # The status of a method that the matched rule does not allow.
FAULT_STATUS = 500  # The status of an unexpected fault.

READ_METHODS = {"GET", "HEAD", "OPTIONS"}  # The methods that a read-only route always allows.


def read_content_type(response: TestResponse) -> str:
    """Read the content type of one response through the header table.

    Why:
        The `content_type` property of Werkzeug answers None when the response
        carries no such header. The header table always answers text, so a test
        may compare the value without a guard.

    Args:
        response: The response that the test client returned.

    Returns:
        The content type text, or an empty string.
    """
    return response.headers.get(CONTENT_TYPE_HEADER, "")


def read_allowed_methods(response: TestResponse) -> set[str]:
    """Read the method names from the `Allow` header of one response.

    Why:
        Werkzeug writes the methods in an order that it does not promise. A set
        lets a test check the members and ignore the order.

    Args:
        response: The response that the test client returned.

    Returns:
        The method names in upper case. The set is empty when no header exists.
    """
    header = response.headers.get(ALLOW_HEADER, "")
    return {name.strip().upper() for name in header.split(",") if name.strip()}


def assert_no_internal_detail(response: TestResponse) -> None:
    """Check that one error answer names no part of the inside of the portal.

    Why:
        Rule 2 of the envelope forbids a stack trace, a token, and a password in
        the message. A file path and a fault class name are the same kind of
        leak, because each one describes the portal to an attacker.

    Args:
        response: The response that the test client returned.
    """
    text = response.get_data(as_text=True)
    for marker in LEAK_MARKERS:  # One pass over the fixed marker list.
        assert marker not in text, f"The answer holds the internal detail {marker!r}."


def assert_error_envelope(response: TestResponse) -> dict[str, Any]:
    """Check one response against every envelope rule of the contract.

    Why:
        The contract allows one error shape and no other shape. One helper holds
        every shape rule, so each test states its own status and its own code and
        repeats no shape check. The key set comparison is exact, so an extra key
        and a missing key both fail.

    Args:
        response: The response that the test client returned.

    Returns:
        The inner error body, so the caller may read the code.
    """
    content_type = read_content_type(response)
    assert content_type.startswith(JSON_TYPE), f"The type {content_type!r} is not JSON."
    payload = response.get_json()
    assert isinstance(payload, dict), "The error answer is no JSON object."
    assert set(payload) == {ENVELOPE_KEY}, f"The top level holds {sorted(payload)}."
    body = payload[ENVELOPE_KEY]
    assert isinstance(body, dict), "The value of the error key is no JSON object."
    assert set(body) in ALLOWED_KEY_SETS, f"The envelope holds {sorted(body)}."
    code = body["code"]
    assert isinstance(code, str) and CODE_PATTERN.match(code), f"The code {code!r} is not a lower-case word."
    message = body["message"]
    assert isinstance(message, str) and message.strip(), "The message is empty."
    assert_no_internal_detail(response)
    return dict(body)


def build_valid_token(app: Flask, client: FlaskClient) -> str:
    """Put a valid token in the client session and return the header value.

    Why:
        The missing token test needs a positive control. Without one, a 400
        answer could come from a broken route instead of from the token guard.

    Args:
        app: The application that signs the token.
        client: The client whose session must hold the matching value.

    Returns:
        The token value for the `X-CSRFToken` header.
    """
    field_name: str = app.config[CSRF_FIELD_SETTING]
    with app.test_request_context():  # The token builder reads the session, so it needs a request context.
        header_value = generate_csrf()
        session_value = session[field_name]
    with client.session_transaction() as stored:  # The guard compares the header value with the session value.
        stored[field_name] = session_value
    return str(header_value)


def scaffold_abort(status: int) -> NoReturn:
    """Raise the fault that matches one status code.

    Why:
        The factory registers one error handler for each documented status, and
        no feature route exists yet. This view reaches each registered handler
        through the same path that a feature route will use.

    Args:
        status: The status code to answer with.

    Raises:
        HTTPException: Always. The bound error handler answers the fault.
    """
    abort(status)


def scaffold_echo() -> tuple[Response, int]:
    """Answer one call that passed the token guard.

    Why:
        The token guard of `flask-wtf` returns early when a request matches no
        endpoint. The guard therefore needs one real endpoint before a test can
        read the answer for a missing token. The same rule accepts a read method
        and two state-changing methods, so one endpoint shows both answers.

    Returns:
        A small success body and the status 200.
    """
    return jsonify({"accepted": True}), SUCCESS_STATUS


def scaffold_fault() -> NoReturn:
    """Raise a fault that no handler expects.

    Why:
        The contract binds the status 500 to an unexpected fault and asks for a
        plain message. Only a real unhandled fault proves that the portal hides
        the class name, the file path, and the fault text from the browser.

    Raises:
        ZeroDivisionError: Always.
    """
    raise ZeroDivisionError(FAULT_SECRET)


@pytest.fixture
def scaffold_app(portal_app: Flask) -> Flask:
    """Add the scaffold routes to the portal application.

    Why:
        Flask refuses a new rule after the first request, so the fixture
        registers every rule before the test client sends anything.

        The fixture also stops the fault from propagating. The shared fixture
        sets test mode, and test mode raises the fault to pytest instead of
        answering the browser. A contract test must read the answer that the
        browser reads.

    Args:
        portal_app: The application from the shared conftest fixture.

    Returns:
        The same application with the scaffold routes in place.
    """
    portal_app.add_url_rule(ABORT_RULE, view_func=scaffold_abort, methods=["GET"])
    portal_app.add_url_rule(ECHO_PATH, view_func=scaffold_echo, methods=["GET", "POST", "DELETE"])
    portal_app.add_url_rule(FAULT_PATH, view_func=scaffold_fault, methods=["GET"])
    portal_app.config["PROPAGATE_EXCEPTIONS"] = False  # Read the browser answer, not the pytest fault.
    return portal_app


@pytest.fixture
def scaffold_client(scaffold_app: Flask) -> Iterator[FlaskClient]:
    """Return a test client for the application that carries the scaffold routes.

    Why:
        The context manager holds one session across the requests of one test,
        so the token control may write the session and then send the request.

    Args:
        scaffold_app: The application with the scaffold routes in place.

    Yields:
        The Flask test client.
    """
    with scaffold_app.test_client() as client:  # The context manager holds the session open.
        yield client


@pytest.fixture
def blocked_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[FlaskClient]:
    """Return a client that the network allow list refuses.

    Why:
        The allow list is the only production guard that answers 403 today. The
        fixture names a network that holds no loopback address, so every call
        from the test client arrives from outside the list. The fixture builds
        its own application, because the allow list reads the environment once
        at build time.

    Args:
        monkeypatch: The pytest helper that restores the environment afterward.

    Yields:
        The Flask test client of the guarded application.
    """
    monkeypatch.setenv(ALLOWED_ADDRESSES_VARIABLE, BLOCKED_NETWORK)
    app = create_app()  # The settings load here, so the variable must already hold the network.
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_the_health_route_answers_two_hundred_and_no_envelope(scaffold_client: FlaskClient) -> None:
    """The health route answers 200 with the documented body and no envelope.

    Why:
        The contract reserves the envelope for a failure. A success body that
        also held an `error` key would make the envelope meaningless.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.get(HEALTH_PATH)
    assert response.status_code == SUCCESS_STATUS
    assert read_content_type(response).startswith(JSON_TYPE)
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert isinstance(payload["version"], str)
    assert ENVELOPE_KEY not in payload


def test_an_unknown_path_answers_the_envelope(scaffold_client: FlaskClient) -> None:
    """A path that no rule matches answers 404 inside the envelope.

    Why:
        This is the one error that a production route raises today with no
        scaffold. It proves that the router fault reaches the JSON handler.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.get(UNKNOWN_PATH)
    assert response.status_code == NOT_FOUND_STATUS
    assert_error_envelope(response)


@pytest.mark.parametrize("status", DOCUMENTED_ERROR_STATUSES)
def test_each_documented_status_answers_the_envelope(scaffold_client: FlaskClient, status: int) -> None:
    """Every error status of the contract answers the one documented shape.

    Why:
        The status table of the contract lists seven error statuses. A handler
        that answered an HTML page for one of them would break every browser
        script that reads the code word.

    Args:
        scaffold_client: The portal test client.
        status: One error status from the contract table.
    """
    response = scaffold_client.get(f"{ABORT_PATH_PREFIX}{status}")
    assert response.status_code == status
    assert_error_envelope(response)


@pytest.mark.parametrize(("status", "code"), CONTRACT_NAMED_CODES)
def test_each_contract_named_code_matches(scaffold_client: FlaskClient, status: int, code: str) -> None:
    """The code word matches the word that the contract names for that status.

    Why:
        A browser script reads the code word and never the message. A changed
        word would break the script without any other visible sign.

    Args:
        scaffold_client: The portal test client.
        status: The status that the contract names a code word for.
        code: The code word from the contract.
    """
    response = scaffold_client.get(f"{ABORT_PATH_PREFIX}{status}")
    body = assert_error_envelope(response)
    assert body["code"] == code


def test_a_post_without_a_token_answers_csrf_missing(scaffold_client: FlaskClient) -> None:
    """A post with no token answers 400 with the code `csrf_missing`.

    Why:
        The portal starts a firmware upgrade through a post, so a forged post
        could start work on a live site. The token guard is the control that
        stops that, and the contract binds one code word to it.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.post(ECHO_PATH)
    assert response.status_code == BAD_REQUEST_STATUS
    body = assert_error_envelope(response)
    assert body["code"] == CSRF_MISSING_CODE


def test_a_delete_without_a_token_answers_csrf_missing(scaffold_client: FlaskClient) -> None:
    """A delete with no token answers 400 with the code `csrf_missing`.

    Why:
        Section 3 of the contract releases the site lock through a delete call.
        A delete changes state, so the same token rule must cover it.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.delete(ECHO_PATH)
    assert response.status_code == BAD_REQUEST_STATUS
    body = assert_error_envelope(response)
    assert body["code"] == CSRF_MISSING_CODE


def test_a_post_with_a_token_reaches_the_route(scaffold_app: Flask, scaffold_client: FlaskClient) -> None:
    """A post that carries a valid token reaches the view.

    Why:
        This is the positive control for the two token tests above. Without it,
        a broken route would produce the same 400 answer and the tests would
        still pass.

    Args:
        scaffold_app: The application that signs the token.
        scaffold_client: The portal test client.
    """
    token = build_valid_token(scaffold_app, scaffold_client)
    response = scaffold_client.post(ECHO_PATH, headers={CSRF_HEADER: token})
    assert response.status_code == SUCCESS_STATUS
    assert response.get_json() == {"accepted": True}


def test_a_get_on_the_same_route_needs_no_token(scaffold_client: FlaskClient) -> None:
    """A get on the same rule reaches the view with no token at all.

    Why:
        The contract states that a get never changes state and therefore needs
        no token. The same rule accepts both methods, so this test and the post
        test differ in the method alone.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.get(ECHO_PATH)
    assert response.status_code == SUCCESS_STATUS
    assert response.get_json() == {"accepted": True}


def test_a_post_to_an_unknown_path_answers_not_found(scaffold_client: FlaskClient) -> None:
    """A post to a path that no rule matches answers 404, not the token code.

    Why:
        The token guard returns early when a request matches no endpoint. A
        reader who expects `csrf_missing` here would report a false defect, so
        this test records the real order of the two checks.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.post(UNKNOWN_PATH)
    assert response.status_code == NOT_FOUND_STATUS
    body = assert_error_envelope(response)
    assert body["code"] != CSRF_MISSING_CODE


def test_a_blocked_address_answers_the_envelope(blocked_client: FlaskClient) -> None:
    """A call from outside the address allow list answers 403 inside the envelope.

    Why:
        This guard runs before every view, so it answers before any route code.
        A guard that answered an HTML page would break the browser script on the
        very first call of a blocked operator.

    Args:
        blocked_client: A client that the allow list refuses.
    """
    response = blocked_client.get(HEALTH_PATH)
    assert response.status_code == FORBIDDEN_STATUS
    assert_error_envelope(response)


def test_an_allowed_address_reaches_the_route(blocked_client: FlaskClient) -> None:
    """A call from inside the address allow list reaches the route.

    Why:
        This is the positive control for the test above. Without it, a guard
        that refused every call would still pass the blocked test.

        The address arrives as the socket address, not as a header. A header
        would prove nothing here, because the portal is meant to ignore one.

    Args:
        blocked_client: The client of the guarded application.
    """
    response = blocked_client.get(HEALTH_PATH, environ_base={"REMOTE_ADDR": ALLOWED_ADDRESS})
    assert response.status_code == SUCCESS_STATUS


def test_a_forwarded_header_cannot_pass_the_address_allow_list(blocked_client: FlaskClient) -> None:
    """A forwarded header naming an allowed address still answers 403.

    Why:
        A forwarded header is text that any caller can send. The portal names
        no trusted proxy by default, so it must read the socket address and
        ignore the header. A portal that read the header would let any caller
        on the network name its own address and walk through the allow list.

    Args:
        blocked_client: A client whose socket address the allow list refuses.
    """
    response = blocked_client.get(HEALTH_PATH, headers={FORWARDED_HEADER: ALLOWED_ADDRESS})
    assert response.status_code == FORBIDDEN_STATUS
    assert_error_envelope(response)


def test_an_unexpected_fault_answers_a_plain_five_hundred(scaffold_client: FlaskClient) -> None:
    """An unhandled fault answers 500 with a plain message and no stack trace.

    Why:
        The contract asks the 500 message to stay plain. A default Flask answer
        would carry the fault text, and a debug answer would carry the whole
        stack trace with every file path of the host.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.get(FAULT_PATH)
    assert response.status_code == FAULT_STATUS
    body = assert_error_envelope(response)
    assert FAULT_SECRET not in body["message"]
    assert "ZeroDivisionError" not in body["message"]


def test_a_head_request_on_the_health_route_answers_two_hundred(scaffold_client: FlaskClient) -> None:
    """A head request on the health route answers 200 with no body.

    Why:
        The container probe may send a head request instead of a get request.
        HTTP asks for the same status and the same content type as the get
        answer, with an empty body.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.head(HEALTH_PATH)
    assert response.status_code == SUCCESS_STATUS
    assert read_content_type(response).startswith(JSON_TYPE)
    assert response.get_data() == b""


def test_a_head_request_on_an_unknown_path_declares_json(scaffold_client: FlaskClient) -> None:
    """A head request on an unknown path answers a 404 that declares JSON.

    Why:
        HTTP strips the body of a head answer, so the envelope itself cannot
        appear. The status and the declared type must still match the get
        answer, or a client would read the two methods differently.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.head(UNKNOWN_PATH)
    assert response.status_code == NOT_FOUND_STATUS
    assert read_content_type(response).startswith(JSON_TYPE)
    assert response.get_data() == b""


def test_an_options_request_lists_the_read_methods(scaffold_client: FlaskClient) -> None:
    """An options request on the health route names the read methods only.

    Why:
        The health route reads no state, so it must not advertise a method that
        changes state. An advertised post would invite a call that the router
        then refuses.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.options(HEALTH_PATH)
    assert response.status_code == SUCCESS_STATUS
    allowed = read_allowed_methods(response)
    assert READ_METHODS <= allowed
    assert "POST" not in allowed


def test_an_options_request_needs_no_token(scaffold_client: FlaskClient) -> None:
    """An options request reaches the router with no token.

    Why:
        A browser sends an options request before some calls, and the browser
        cannot add the token to that request. A token check on this method would
        block the call that follows it.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.options(ECHO_PATH)
    assert response.status_code == SUCCESS_STATUS
    assert "POST" in read_allowed_methods(response)


def test_a_wrong_method_answers_four_hundred_five(scaffold_client: FlaskClient) -> None:
    """A method that the matched rule refuses answers 405 and names the methods.

    Why:
        The status table of the contract lists no 405, so this test states no
        envelope rule for it. The `Allow` header is the part that HTTP itself
        requires, and a JSON envelope must not cost the caller that header.

    Args:
        scaffold_client: The portal test client.
    """
    response = scaffold_client.post(HEALTH_PATH)
    assert response.status_code == NOT_ALLOWED_STATUS
    assert READ_METHODS <= read_allowed_methods(response)
