"""Contract tests for the sign-in surface of the upgrade capture portal.

Why:
    ``specs/1823-upgrade-capture-portal/contracts/http-api.md`` section 1 fixes
    every path, every status, and every error code below. A test states each
    value as a literal and imports no constant from the module under test, so a
    rename inside the module cannot make a broken contract pass.

    No test reaches the Mist cloud. Every test injects a stand-in through the
    application configuration, so the suite opens no socket and needs no cloud
    account.

    Every credential value below is an obviously fake string. FR-009 forbids a
    real password, a real code, and a real token anywhere in the test suite.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import pytest
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.app.routes import auth
from src.upgrade_portal.runtime import identity

logger = logging.getLogger(__name__)

# WHY: An obviously fake pair. A reader sees at once that neither string is a
# secret, and a leak check can search for these exact values.
PROBE_EMAIL = "probe.operator@example.invalid"
PROBE_PASSWORD = "fake-password-for-tests-only"
PROBE_CODE = "424242"
PROBE_TOKEN = "fake-api-token-for-tests-only"

# WHY: The contract fixes each literal below. A test never imports the matching
# constant from the module under test, because that would hide a renamed path.
ROOT_PATH = "/"
SIGNIN_PATH = "/auth/signin"
TWO_FACTOR_PATH = "/auth/twofactor"
SIGNOUT_PATH = "/auth/signout"
ORG_PATH = "/select/org"

BAD_CREDENTIALS = "bad_credentials"
RATE_LIMITED = "rate_limited"
BAD_TWO_FACTOR_CODE = "bad_two_factor_code"

# WHY: The cloud answers a mapping. These three shapes cover every branch of
# the classifier, and none of them holds a credential value.
CLOUD_SUCCESS: dict[str, Any] = {"authenticated": True}
CLOUD_TWO_FACTOR: dict[str, Any] = {"error": {"two_factor_required": True}}
CLOUD_REFUSED: dict[str, Any] = {"error": {"message": "invalid credentials"}}
CLOUD_THROTTLED: dict[str, Any] = {"error": {"message": "Too many requests"}}

# WHY: A browser form post states this header. The route then answers a
# redirect instead of a JSON body, so a test of that branch must send it.
BROWSER_HEADERS = {"Accept": "text/html"}


class FakeCloudSession:
    """A stand-in for the ``mistapi`` session object.

    Why:
        A contract test checks the portal answer, not the cloud transport. This
        stub answers each login call from a script, and it records the second
        factor value of every call so a test can prove that the route passed
        the code through and stored no copy.
    """

    def __init__(self, script: list[dict[str, Any]]) -> None:
        """Create the stub with the answers it will give, in order.

        Args:
            script: One answer for each expected login call.
        """
        self.script = list(script)  # WHY: A copy stops a later edit of the caller list.
        self.factors: list[str] = []  # WHY: Records the second factor of every call.

    def login_with_return(self, two_factor: str = "") -> dict[str, Any]:
        """Answer the next scripted result.

        Args:
            two_factor: The second factor code, or an empty string.

        Returns:
            The next scripted answer, or an empty mapping when the script ran out.
        """
        self.factors.append(two_factor)  # WHY: Proves which call carried the code.
        return self.script.pop(0) if self.script else {}  # WHY: An empty answer reads as a refusal.


class RecordingLogin:
    """A stand-in for the cloud session builder.

    Why:
        The builder call is the one expression of the portal that holds a
        password. This stub records the three arguments, so a test can prove
        that the password reached the cloud call and reached nothing else.
    """

    def __init__(self, script: list[dict[str, Any]]) -> None:
        """Create the builder with the login answers it will give.

        Args:
            script: One answer for each expected login call.
        """
        self.script = list(script)  # WHY: Handed to each session this builder makes.
        self.calls: list[tuple[str, str, str]] = []  # WHY: The address, the password, and the host.
        self.session = FakeCloudSession(self.script)  # WHY: One session, so a retry finds the same object.

    def __call__(self, actor_email: str, password: str, host: str) -> FakeCloudSession:
        """Build the stub cloud session and record the arguments.

        Args:
            actor_email: The normalized work address.
            password: The value the operator typed.
            host: The Mist cloud host.

        Returns:
            The stub cloud session.
        """
        self.calls.append((actor_email, password, host))  # WHY: A test asserts on each part.
        return self.session  # WHY: The second factor retry needs this same object.


class FailingLogin:
    """A builder that raises, to prove the transport fault branch.

    Why:
        A refused socket must answer the contract envelope and never a 500
        page. This stub raises the fault that a real transport would raise.
    """

    def __init__(self, message: str) -> None:
        """Create the failing builder.

        Args:
            message: The text of the fault to raise.
        """
        self.message = message  # WHY: A throttle wording reaches a different answer.

    def __call__(self, actor_email: str, password: str, host: str) -> FakeCloudSession:
        """Raise instead of building a session.

        Args:
            actor_email: The normalized work address.
            password: The value the operator typed.
            host: The Mist cloud host.

        Returns:
            Never returns.

        Raises:
            RuntimeError: Always, with the configured text.
        """
        raise RuntimeError(self.message)  # WHY: The route must turn this into a contract answer.


@pytest.fixture
def auth_client(portal_app: Any) -> Iterator[FlaskClient]:
    """Return a test client with the token check turned off.

    Why:
        Every post of this surface carries a token in the browser. A contract
        test drives the route and not the token, and ``test_security.py``
        already owns the ``csrf_missing`` coverage, so this fixture removes
        that one step. The pending store is cleared on both sides, because it
        is a module global and a leftover record would leak across tests.

    Args:
        portal_app: The application from the shared fixture.

    Yields:
        The Flask test client.
    """
    portal_app.config["WTF_CSRF_ENABLED"] = False  # WHY: `test_security.py` owns the token coverage.
    auth._PENDING.clear()  # WHY: A module global outlives one test, so clear it before the test.
    with portal_app.test_client() as client:  # WHY: The context manager holds the session open.
        yield client
    auth._PENDING.clear()  # WHY: And clear it again, so no record reaches the next test.


@pytest.fixture
def signed_in_owner() -> Iterator[identity.SessionOwner]:
    """Register one live cloud session and remove it afterwards.

    Why:
        A test of the root path and a test of the sign-out both need an owner
        already in the registry. The registry is a module global, so the
        teardown must remove the record even when the test fails.

    Yields:
        The registered owner.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())
    record = identity.OperatorSession(
        owner=owner,
        cloud_session=FakeCloudSession([]),  # WHY: No call reaches this object in these tests.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)
    try:
        yield owner
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # WHY: The registry outlives the test, so clear it here.


def sign_in_client(client: FlaskClient, owner: identity.SessionOwner) -> None:
    """Give the test client the cookie and the session of one owner.

    Why:
        `identity.current_session` binds the signed session to the browser
        cookie, so a test must set both or the guard reads no session.

    Args:
        client: The Flask test client.
        owner: The registered owner.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
    with client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = owner.key


def read_error_code(response: TestResponse) -> str:
    """Return the error code of one refusal envelope.

    Args:
        response: The response to read.

    Returns:
        The value of the ``error.code`` field.
    """
    payload: dict[str, Any] = response.get_json()
    return str(payload["error"]["code"])


def post_signin(client: FlaskClient, **fields: str) -> TestResponse:
    """Post the sign-in form with the named fields.

    Why:
        Nine tests post this form. One helper keeps the address and the
        password in one place, so no test invents a second fake pair.

    Args:
        client: The Flask test client.
        **fields: Field values that replace the default pair.

    Returns:
        The response.
    """
    body = {"email": PROBE_EMAIL, "password": PROBE_PASSWORD}  # WHY: The default pair of every test.
    body.update(fields)  # WHY: One test changes one field and states no other.
    return client.post(SIGNIN_PATH, json=body)


def test_root_without_session_opens_the_signin_form(auth_client: FlaskClient) -> None:
    """The root path sends a caller with no session to the sign-in form."""
    response = auth_client.get(ROOT_PATH)
    assert response.status_code == 303  # WHY: See Other, so the browser reads the next page with GET.
    assert response.headers["Location"] == SIGNIN_PATH


def test_root_with_session_opens_the_organization_picker(
    auth_client: FlaskClient, signed_in_owner: identity.SessionOwner
) -> None:
    """The root path sends a signed-in caller to the organization picker."""
    sign_in_client(auth_client, signed_in_owner)
    response = auth_client.get(ROOT_PATH)
    assert response.status_code == 303
    assert response.headers["Location"] == ORG_PATH


def test_signin_page_holds_every_named_control(auth_client: FlaskClient) -> None:
    """The sign-in page carries the four identifiers of the identifier contract."""
    response = auth_client.get(SIGNIN_PATH)
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    for name in ("signin-email", "signin-password", "signin-submit", "signin-error"):
        assert f'data-testid="{name}"' in page  # WHY: `contracts/ui-testids.md` fixes each value.


def test_signin_page_needs_no_session(auth_client: FlaskClient) -> None:
    """The sign-in page answers without a session, because a session starts there."""
    response = auth_client.get(SIGNIN_PATH)
    assert response.status_code == 200
    assert "not_authenticated" not in response.get_data(as_text=True)


def test_signin_success_answers_the_organization_picker(auth_client: FlaskClient, portal_app: Any) -> None:
    """A cloud that accepts the pair sends the operator to the organization picker."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_SUCCESS])
    response = post_signin(auth_client)
    assert response.status_code == 200
    assert response.get_json() == {"next": ORG_PATH}  # WHY: The contract fixes this body exactly.


def test_signin_success_registers_the_cloud_session(auth_client: FlaskClient, portal_app: Any) -> None:
    """A successful sign-in places the cloud session in the per-operator registry."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_SUCCESS])
    before = identity.SESSION_REGISTRY.owner_count()
    post_signin(auth_client)
    assert identity.SESSION_REGISTRY.owner_count() == before + 1  # WHY: FR-005 gives each owner a record.
    auth_client.post(SIGNOUT_PATH)  # WHY: The registry is a global, so this test clears its own record.


def test_signin_passes_the_password_to_the_cloud_call(auth_client: FlaskClient, portal_app: Any) -> None:
    """The password reaches the cloud builder and reaches nothing else."""
    builder = RecordingLogin([CLOUD_SUCCESS])
    portal_app.config["CLOUD_LOGIN"] = builder
    post_signin(auth_client)
    assert builder.calls == [(PROBE_EMAIL, PROBE_PASSWORD, "api.mist.com")]  # WHY: One call, with the pair.
    auth_client.post(SIGNOUT_PATH)  # WHY: Clears the registry record that this test made.


def test_signin_two_factor_answers_the_second_factor_page(auth_client: FlaskClient, portal_app: Any) -> None:
    """A cloud that wants a code sends the operator to the second factor page."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_TWO_FACTOR])
    response = post_signin(auth_client)
    assert response.status_code == 200
    assert response.get_json() == {"next": TWO_FACTOR_PATH}  # WHY: The contract fixes this body exactly.


def test_signin_refusal_answers_bad_credentials(auth_client: FlaskClient, portal_app: Any) -> None:
    """A cloud that refuses the pair produces the fixed refusal code."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_REFUSED])
    response = post_signin(auth_client)
    assert response.status_code == 400
    assert read_error_code(response) == BAD_CREDENTIALS


def test_signin_throttle_answers_rate_limited(auth_client: FlaskClient, portal_app: Any) -> None:
    """A cloud that throttles the attempt produces the separate throttle code."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_THROTTLED])
    response = post_signin(auth_client)
    assert response.status_code == 429  # WHY: A credential refusal here would make the operator retype.
    assert read_error_code(response) == RATE_LIMITED


def test_signin_transport_fault_answers_bad_credentials(auth_client: FlaskClient, portal_app: Any) -> None:
    """A cloud call that raises answers the contract envelope and never a fault page."""
    portal_app.config["CLOUD_LOGIN"] = FailingLogin("connection refused")
    response = post_signin(auth_client)
    assert response.status_code == 400
    assert read_error_code(response) == BAD_CREDENTIALS


def test_signin_throttle_fault_answers_rate_limited(auth_client: FlaskClient, portal_app: Any) -> None:
    """A raised throttle reads as a throttle and not as a refused pair."""
    portal_app.config["CLOUD_LOGIN"] = FailingLogin("HTTP 429 too many requests")
    response = post_signin(auth_client)
    assert response.status_code == 429
    assert read_error_code(response) == RATE_LIMITED


def test_signin_without_address_answers_bad_credentials(auth_client: FlaskClient, portal_app: Any) -> None:
    """A body with no usable address never reaches the cloud."""
    builder = RecordingLogin([CLOUD_SUCCESS])
    portal_app.config["CLOUD_LOGIN"] = builder
    response = post_signin(auth_client, email="   ")
    assert response.status_code == 400
    assert read_error_code(response) == BAD_CREDENTIALS
    assert builder.calls == []  # WHY: A bad address must not send the password anywhere.


def test_signin_refuses_a_host_outside_the_catalog(auth_client: FlaskClient, portal_app: Any) -> None:
    """A host that the catalog does not hold never receives the password."""
    builder = RecordingLogin([CLOUD_SUCCESS])
    portal_app.config["CLOUD_LOGIN"] = builder
    post_signin(auth_client, host="attacker.example.invalid")
    assert builder.calls[0][2] == "api.mist.com"  # WHY: The default cloud, never the named one.
    auth_client.post(SIGNOUT_PATH)  # WHY: Clears the registry record that this test made.


def test_signin_browser_post_answers_a_redirect(auth_client: FlaskClient, portal_app: Any) -> None:
    """A browser form post reads a redirect, because it cannot read a JSON body."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_SUCCESS])
    response = auth_client.post(
        SIGNIN_PATH, data={"email": PROBE_EMAIL, "password": PROBE_PASSWORD}, headers=BROWSER_HEADERS
    )
    assert response.status_code == 303
    assert response.headers["Location"] == ORG_PATH
    auth_client.post(SIGNOUT_PATH)  # WHY: Clears the registry record that this test made.


def test_signin_browser_refusal_shows_the_form_again(auth_client: FlaskClient, portal_app: Any) -> None:
    """A refused browser post shows the form again with the reason inside it."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_REFUSED])
    response = auth_client.post(
        SIGNIN_PATH, data={"email": PROBE_EMAIL, "password": PROBE_PASSWORD}, headers=BROWSER_HEADERS
    )
    assert response.status_code == 400  # WHY: The contract status holds for both clients.
    page = response.get_data(as_text=True)
    assert 'data-testid="signin-error"' in page  # WHY: The identifier contract names this region.
    assert PROBE_PASSWORD not in page  # WHY: FR-009 keeps the password out of the markup.


def test_two_factor_page_holds_every_named_control(auth_client: FlaskClient) -> None:
    """The second factor page carries the two identifiers of the identifier contract."""
    response = auth_client.get(TWO_FACTOR_PATH)
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'data-testid="twofactor-code"' in page
    assert 'data-testid="twofactor-submit"' in page


def test_two_factor_success_answers_the_organization_picker(auth_client: FlaskClient, portal_app: Any) -> None:
    """A correct code finishes the sign-in that the pair started."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_TWO_FACTOR, CLOUD_SUCCESS])
    post_signin(auth_client)
    response = auth_client.post(TWO_FACTOR_PATH, json={"code": PROBE_CODE})
    assert response.status_code == 200
    assert response.get_json() == {"next": ORG_PATH}  # WHY: The contract fixes this body exactly.
    auth_client.post(SIGNOUT_PATH)  # WHY: Clears the registry record that this test made.


def test_two_factor_passes_the_code_to_the_cloud_call(auth_client: FlaskClient, portal_app: Any) -> None:
    """The code reaches the retry call and reaches nothing else."""
    builder = RecordingLogin([CLOUD_TWO_FACTOR, CLOUD_SUCCESS])
    portal_app.config["CLOUD_LOGIN"] = builder
    post_signin(auth_client)
    auth_client.post(TWO_FACTOR_PATH, json={"code": PROBE_CODE})
    assert builder.session.factors == ["", PROBE_CODE]  # WHY: The first call carries no code, the retry does.
    auth_client.post(SIGNOUT_PATH)  # WHY: Clears the registry record that this test made.


def test_two_factor_wrong_code_answers_the_fixed_code(auth_client: FlaskClient, portal_app: Any) -> None:
    """A refused code produces the fixed refusal code of the contract."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_TWO_FACTOR, CLOUD_REFUSED])
    post_signin(auth_client)
    response = auth_client.post(TWO_FACTOR_PATH, json={"code": "000000"})
    assert response.status_code == 400
    assert read_error_code(response) == BAD_TWO_FACTOR_CODE


def test_two_factor_keeps_the_wait_after_a_wrong_code(auth_client: FlaskClient, portal_app: Any) -> None:
    """A wrong code leaves the wait open, so the operator may read a new code."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_TWO_FACTOR, CLOUD_REFUSED, CLOUD_SUCCESS])
    post_signin(auth_client)
    auth_client.post(TWO_FACTOR_PATH, json={"code": "000000"})
    response = auth_client.post(TWO_FACTOR_PATH, json={"code": PROBE_CODE})
    assert response.status_code == 200  # WHY: A dropped wait would force the whole pair again.
    auth_client.post(SIGNOUT_PATH)  # WHY: Clears the registry record that this test made.


def test_two_factor_without_a_wait_answers_the_fixed_code(auth_client: FlaskClient) -> None:
    """A code with no open sign-in produces the same fixed refusal code."""
    response = auth_client.post(TWO_FACTOR_PATH, json={"code": PROBE_CODE})
    assert response.status_code == 400
    assert read_error_code(response) == BAD_TWO_FACTOR_CODE  # WHY: The contract names one code for this step.


def test_two_factor_with_an_empty_code_answers_the_fixed_code(auth_client: FlaskClient, portal_app: Any) -> None:
    """An empty code never reaches the cloud."""
    builder = RecordingLogin([CLOUD_TWO_FACTOR])
    portal_app.config["CLOUD_LOGIN"] = builder
    post_signin(auth_client)
    response = auth_client.post(TWO_FACTOR_PATH, json={"code": "  "})
    assert response.status_code == 400
    assert read_error_code(response) == BAD_TWO_FACTOR_CODE
    assert builder.session.factors == [""]  # WHY: Only the first call ran, so the retry never happened.


def test_signout_answers_the_signin_form(auth_client: FlaskClient, signed_in_owner: identity.SessionOwner) -> None:
    """A sign-out returns the operator to the sign-in form."""
    sign_in_client(auth_client, signed_in_owner)
    response = auth_client.post(SIGNOUT_PATH)
    assert response.status_code == 200
    assert response.get_json() == {"next": SIGNIN_PATH}  # WHY: The contract fixes this body exactly.


def test_signout_drops_the_cloud_session(auth_client: FlaskClient, signed_in_owner: identity.SessionOwner) -> None:
    """A sign-out removes the cloud session from the registry."""
    sign_in_client(auth_client, signed_in_owner)
    auth_client.post(SIGNOUT_PATH)
    assert identity.SESSION_REGISTRY.get(signed_in_owner.key) is None  # WHY: FR-009 releases the reference.


def test_signout_without_a_session_still_reports_success(auth_client: FlaskClient) -> None:
    """A sign-out on a session that is already gone still reports success."""
    response = auth_client.post(SIGNOUT_PATH)
    assert response.status_code == 200  # WHY: A stale tab must read the form, never a refusal.
    assert response.get_json() == {"next": SIGNIN_PATH}


def test_signout_drops_a_half_finished_signin(auth_client: FlaskClient, portal_app: Any) -> None:
    """A sign-out ends a wait that no code ever finished."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_TWO_FACTOR, CLOUD_SUCCESS])
    post_signin(auth_client)
    auth_client.post(SIGNOUT_PATH)
    response = auth_client.post(TWO_FACTOR_PATH, json={"code": PROBE_CODE})
    assert response.status_code == 400  # WHY: A shared workstation must not finish the login of the last user.
    assert read_error_code(response) == BAD_TWO_FACTOR_CODE


def test_token_mode_signs_the_operator_in(auth_client: FlaskClient, portal_app: Any, monkeypatch: Any) -> None:
    """The environment token mode of FR-006 reaches the organization picker."""
    monkeypatch.setenv("MIST_APITOKEN", PROBE_TOKEN)  # WHY: The identity module refuses the mode without one.
    portal_app.config["CLOUD_TOKEN_SESSION"] = lambda host: FakeCloudSession([])
    response = auth_client.post(SIGNIN_PATH, json={"email": PROBE_EMAIL, "mode": "environment_token"})
    assert response.status_code == 200
    assert response.get_json() == {"next": ORG_PATH}
    auth_client.post(SIGNOUT_PATH)  # WHY: Clears the registry record that this test made.


def test_token_mode_without_a_variable_answers_bad_credentials(
    auth_client: FlaskClient, portal_app: Any, monkeypatch: Any
) -> None:
    """The token mode refuses when no token variable holds text."""
    monkeypatch.delenv("MIST_APITOKEN", raising=False)  # WHY: The mode cannot work without a variable.
    monkeypatch.delenv("MIST_API_TOKEN", raising=False)
    portal_app.config["CLOUD_TOKEN_SESSION"] = lambda host: FakeCloudSession([])
    response = auth_client.post(SIGNIN_PATH, json={"email": PROBE_EMAIL, "mode": "environment_token"})
    assert response.status_code == 400
    assert read_error_code(response) == BAD_CREDENTIALS  # WHY: No probe learns which half was missing.


def test_no_log_record_holds_a_credential_or_an_address(
    auth_client: FlaskClient, portal_app: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """FR-009 keeps the password, the code, and the address out of every log record."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_TWO_FACTOR, CLOUD_SUCCESS])
    with caplog.at_level(logging.DEBUG):  # WHY: The lowest level, so no record escapes the check.
        post_signin(auth_client)
        auth_client.post(TWO_FACTOR_PATH, json={"code": PROBE_CODE})
    written = "\n".join(record.getMessage() for record in caplog.records)
    for secret in (PROBE_PASSWORD, PROBE_CODE, PROBE_EMAIL):
        assert secret not in written  # WHY: A digest is the only form of an address a record may hold.
    auth_client.post(SIGNOUT_PATH)  # WHY: Clears the registry record that this test made.


def test_the_log_names_the_operator_by_digest(
    auth_client: FlaskClient, portal_app: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """A log record still names the operator, through the one-way digest."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_SUCCESS])
    with caplog.at_level(logging.INFO):
        post_signin(auth_client)
    written = "\n".join(record.getMessage() for record in caplog.records)
    assert identity.email_digest(PROBE_EMAIL) in written  # WHY: A digest joins two records of one attempt.
    auth_client.post(SIGNOUT_PATH)  # WHY: Clears the registry record that this test made.


def test_no_answer_body_holds_a_credential(auth_client: FlaskClient, portal_app: Any) -> None:
    """No refusal body repeats the password or the address back to the caller."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_REFUSED])
    response = post_signin(auth_client)
    body = response.get_data(as_text=True)
    assert PROBE_PASSWORD not in body  # WHY: A message that echoes the value would place it in a browser cache.
    assert PROBE_EMAIL not in body


def test_the_pending_record_holds_no_credential(auth_client: FlaskClient, portal_app: Any) -> None:
    """The half-finished sign-in store holds no password and no code."""
    portal_app.config["CLOUD_LOGIN"] = RecordingLogin([CLOUD_TWO_FACTOR])
    post_signin(auth_client)
    written = "\n".join(repr(record) for record in auth._PENDING.values())
    assert PROBE_PASSWORD not in written  # WHY: A traceback prints this text, so it must name no credential.
    assert PROBE_EMAIL not in written
