"""Unit tests for the sign-in route module of the upgrade capture portal.

Why:
    A contract test drives the whole application and checks the documented
    status codes. These unit tests check the decisions that the route module
    makes on its own: the guard that refuses an empty password before any cloud
    call, the two credential modes of FR-006, the classifier that reads one
    cloud answer, the pending store that holds a half-finished sign-in, and the
    two records that must never print a cloud session object.

    The empty password guard needs its own test, because FR-006 lets the page
    drop the browser check while a token variable holds text. A server that
    trusts the page alone sends an empty password to the cloud and spends one
    attempt against the sign-in rate limit for an answer that is already known.

    Two guards of `runtime/identity.py` sit here as well. The organization scope
    functions decide whether a session may act on one organization, and the
    redaction helper copies a body with every credential value replaced by the
    name of its field. Both run at the function level, because a route test
    would hide which function made the decision.

    Every cloud call travels through an injected seam, so no test opens a
    socket and no test needs a cloud account. Every credential value below is
    an obviously fake string, and no test writes one into a log record.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import time  # Ages one pending record, so the expiry test needs no wait.
from collections.abc import Iterator  # Types each fixture that yields.
from typing import Any  # A cloud answer and a cloud session are both free-form.

import pytest  # The test framework.
from flask import Flask  # The smallest application that can hold the blueprint.
from flask.testing import FlaskClient  # Drives a route with no server and no browser.
from werkzeug.test import TestResponse  # The answer that the test client returns.

from src.upgrade_portal.app.routes import auth  # The module under test.
from src.upgrade_portal.runtime import identity  # The registry, the mode names, and the variable names.

# WHY: A reserved example domain, so no message can reach a real mailbox.
PROBE_EMAIL = "probe.operator@example.invalid"

# WHY: Obviously fake values. FR-009 forbids a real credential inside the suite.
PROBE_PASSWORD = "fake-password-for-tests-only"
PROBE_TOKEN = "fake-api-token-for-tests-only"
FAKE_SECRET = "fake-flask-secret-key-for-tests-only"

# WHY: Matches the URL-safe cookie shape that `identity` accepts, so a pending
# record built by hand reads the same as one that a real request created.
PROBE_BROWSER_ID = "probe-browser-Ab12_cd34-Ef56"

# WHY: The four cloud answers that the classifier must separate. Each one uses
# the wording of a real release, so a test pins behavior and not a guess.
CLOUD_SUCCESS: dict[str, Any] = {"authenticated": True}
CLOUD_TWO_FACTOR: dict[str, Any] = {"error": {"two_factor_required": True}}
CLOUD_REFUSED: dict[str, Any] = {"error": {"message": "invalid credentials"}}
CLOUD_THROTTLED: dict[str, Any] = {"error": {"message": "Too many requests"}}

# WHY: Every route test states the script header, so the route answers JSON and
# no test depends on the default `Accept` header of the test client.
SCRIPT_HEADERS = {auth.SCRIPT_HEADER: auth.SCRIPT_HEADER_VALUE}

# WHY: Two obviously fake organization identifiers. The stand-in cloud session
# names the first one and names the second one nowhere.
PERMITTED_ORG_ID = "fake-org-inside-the-scope"
OUTSIDE_ORG_ID = "fake-org-outside-the-scope"

# WHY: The code and the status that `contracts/http-api.md` fixes for an
# organization outside the scope of a session. Both are written out here, so a
# rename inside `identity` cannot make a test agree with itself.
ORG_REFUSED_CODE = "org_not_permitted"
ORG_REFUSED_STATUS = 403

# WHY: The word that the guarded view answers. A test reads it to learn whether
# the guard called the view or refused ahead of it.
VIEW_REACHED = "the guarded view ran"


class FakeCloudSession:
    """A stand-in for the `mistapi` session object.

    Why:
        The route calls one method and reads the mapping it answers. A canned
        answer reaches every branch of the classifier with no cloud account and
        no socket. The object holds no credential value of any kind.
    """

    def __init__(self, answer: dict[str, Any]) -> None:
        """Create the stand-in with one canned cloud answer.

        Why:
            Each test needs its own object, because a test reads the number of
            attempts that its own route call made.

        Args:
            answer: The mapping that every login call returns.
        """
        self.answer = dict(answer)  # A copy stops one test from editing the answer of another.
        self.attempts = 0  # Counts the login calls, so a test can prove that one call happened.

    def login_with_return(self, two_factor: str = "") -> dict[str, Any]:
        """Answer one login call.

        Why:
            The route calls this name with no argument for the first attempt,
            and with the code for the retry. One method serves both, and
            neither the code nor the password is stored here.

        Args:
            two_factor: The second factor code, which this stand-in discards.

        Returns:
            A copy of the canned cloud answer.
        """
        self.attempts += 1  # The count is the only state that a login call leaves behind.
        return dict(self.answer)  # A copy, so a caller cannot edit the canned answer.


class ScopedCloudSession(FakeCloudSession):
    """A stand-in cloud session that names the organizations it may reach.

    Why:
        `identity.session_privileges` reads a `privileges` list from the cloud
        session. `FakeCloudSession` names no list, so the scope check reads an
        unknown scope and permits every organization. A scope test needs a
        session that names a list, or it proves nothing at all.
    """

    def __init__(self, *org_ids: str) -> None:
        """Create the stand-in with one privilege record for each identifier.

        Args:
            *org_ids: The organizations that this session may reach.
        """
        super().__init__(CLOUD_SUCCESS)  # The login answer plays no part in a scope test.
        self.privileges: list[dict[str, str]] = [{"org_id": one} for one in org_ids]  # The cloud shape.


class RecordingLogin:
    """A stand-in for the callable that builds a provider cloud session.

    Why:
        The empty password test must prove that no cloud call happened at all.
        A recorder answers that question with a list, and an assertion on an
        empty list cannot pass by accident.
    """

    def __init__(self, answer: dict[str, Any]) -> None:
        """Create the recorder with one canned cloud answer.

        Why:
            The answer decides which branch the route takes after the build,
            so one test can reach the success path and another the refusal.

        Args:
            answer: The mapping that the built session returns.
        """
        self.calls: list[tuple[str, str, str]] = []  # One entry for each build, in call order.
        self.session = FakeCloudSession(answer)  # One session object, so a test reads one attempt count.

    def __call__(self, actor_email: str, password: str, host: str) -> FakeCloudSession:
        """Record one build and answer the canned session.

        Why:
            The recorded order proves that the route passes the address, the
            password, and the host in the order that the real builder expects.

        Args:
            actor_email: The address that the route passed.
            password: The password that the route passed.
            host: The cloud host that the route passed.

        Returns:
            The canned session object.
        """
        self.calls.append((actor_email, password, host))  # The whole call, so a test reads each part.
        return self.session  # Every build answers the same object, so one attempt count serves.


class RecordingTokenSession:
    """A stand-in for the callable that builds a token cloud session.

    Why:
        The environment token mode of FR-006 uses a second seam. A separate
        recorder lets one test prove that the token mode ran and that the
        provider seam stayed untouched.
    """

    def __init__(self) -> None:
        """Create the recorder with an empty call log.

        Why:
            The host list proves that the token mode also passes a host that
            the cloud catalog names.
        """
        self.hosts: list[str] = []  # One entry for each build, in call order.

    def __call__(self, host: str) -> FakeCloudSession:
        """Record one build and answer a fresh session.

        Args:
            host: The cloud host that the route passed.

        Returns:
            A session object that reports a signed-in operator.
        """
        self.hosts.append(host)  # The catalog check of the token mode is visible here.
        return FakeCloudSession(CLOUD_SUCCESS)  # The token mode never calls the login method.


class RecordingBrowserTokenSession:
    """Record the browser-token builder call without keeping a token.

    Why:
        The browser-token path may use the submitted value at the cloud boundary.
        The test proves that it reaches no durable portal record.
    """

    def __init__(self) -> None:
        """Create the recorder and one token session."""
        self.call_count = 0  # The test checks the one permitted cloud boundary.
        self.hosts: list[str] = []  # A host is safe to retain for the assertion.
        self.session = FakeCloudSession(CLOUD_SUCCESS)  # The registry holds this object by reference.

    def __call__(self, host: str, token: str) -> FakeCloudSession:
        """Build the stand-in session and discard the submitted token."""
        del token  # The recorder must never create a second token lifetime.
        self.call_count += 1  # The submitted credential must reach one builder call.
        self.hosts.append(host)  # The host stays inside the approved cloud catalog.
        return self.session  # The identity lookup and later routes use this same session.


@pytest.fixture
def auth_app() -> Iterator[Flask]:
    """Return the smallest application that can serve the sign-in blueprint.

    Why:
        A unit test checks the decisions of one module, so it needs no template
        folder, no store, and no second blueprint. A bare application also
        keeps another blueprint from changing an answer under test.

    Yields:
        The application with the sign-in blueprint registered.
    """
    app = Flask(__name__)  # A bare application, so no other blueprint can change an answer.
    app.config.update(TESTING=True, SECRET_KEY=FAKE_SECRET, WTF_CSRF_ENABLED=False)  # Test settings alone.
    app.register_blueprint(auth.auth_bp)  # The routes under test.
    auth._PENDING.clear()  # A leftover wait from an earlier test must not change a branch.
    yield app  # The test runs here.
    auth._PENDING.clear()  # The next test starts with an empty store.


@pytest.fixture
def auth_client(auth_app: Flask) -> Iterator[FlaskClient]:
    """Return a test client that keeps one session across the requests of a test.

    Why:
        A sign-in writes the signed browser session, and a later request of the
        same test reads it. The context manager holds that session open.

    Args:
        auth_app: The application from the sibling fixture.

    Yields:
        The Flask test client.
    """
    with auth_app.test_client() as client:  # The context manager holds the session open.
        yield client  # The test drives the routes through this client.


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    """Restore the process session registry after each test of this module.

    Why:
        `identity.SESSION_REGISTRY` is one store for the whole process. A test
        that signs an operator in would otherwise leave that record behind for
        every later test of the run.

    Yields:
        Nothing. The fixture exists for its restore step.
    """
    snapshot = dict(identity.SESSION_REGISTRY._sessions)  # The state before this test.
    try:  # A failed assertion must still restore the store.
        yield  # The test runs here.
    finally:  # Always, so no test leaks a signed-in operator.
        identity.SESSION_REGISTRY._sessions.clear()  # Drop whatever this test registered.
        identity.SESSION_REGISTRY._sessions.update(snapshot)  # Put the earlier state back.


@pytest.fixture
def login_seam(auth_app: Flask) -> RecordingLogin:
    """Install a recording stand-in for the provider cloud sign-in.

    Why:
        The route reads this configuration key before it reaches the cloud
        library, so the injection keeps every test offline and lets a test
        count the calls that the route made.

    Args:
        auth_app: The application from the sibling fixture.

    Returns:
        The recorder, so a test can read the calls that it received.
    """
    recorder = RecordingLogin(CLOUD_SUCCESS)  # The default answer signs the operator in.
    auth_app.config[auth.CLOUD_LOGIN_KEY] = recorder  # The route reads this seam and opens no socket.
    return recorder  # The test asserts on the recorded calls.


@pytest.fixture
def token_seam(auth_app: Flask) -> RecordingTokenSession:
    """Install a recording stand-in for the environment token cloud session.

    Why:
        The token mode of FR-006 builds its session through a second seam, so
        a test of that mode needs its own injection.

    Args:
        auth_app: The application from the sibling fixture.

    Returns:
        The recorder, so a test can read the hosts that it received.
    """
    recorder = RecordingTokenSession()  # A fresh recorder for each test.
    auth_app.config[auth.TOKEN_SESSION_KEY] = recorder  # The route reads this seam and opens no socket.
    return recorder  # The test asserts on the recorded hosts.


@pytest.fixture
def token_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Put an obviously fake cloud token into the process environment.

    Why:
        `identity.sign_in_with_environment_token` asks whether a token variable
        holds text. The fixture writes a fake value, so the token mode can
        succeed with no real credential anywhere in the run.

    Args:
        monkeypatch: The pytest helper that restores the environment after.
    """
    for name in identity.ENVIRONMENT_TOKEN_VARIABLES:  # A real environment may already hold one of them.
        monkeypatch.delenv(name, raising=False)  # An absent variable is the normal case, not a fault.
    monkeypatch.setenv(identity.ENVIRONMENT_TOKEN_VARIABLES[0], PROBE_TOKEN)  # One fake value is enough.


@pytest.fixture
def no_token_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove every cloud token variable from the process environment.

    Why:
        The refusal branch of the token mode runs only while no variable holds
        text. A developer machine may hold a real value, so the test must clear
        both names first and must never read either value.

    Args:
        monkeypatch: The pytest helper that restores the environment after.
    """
    for name in identity.ENVIRONMENT_TOKEN_VARIABLES:  # Both names, because either one satisfies the check.
        monkeypatch.delenv(name, raising=False)  # An absent variable is the normal case, not a fault.


@pytest.fixture
def scoped_request(auth_app: Flask) -> Iterator[ScopedCloudSession]:
    """Sign one operator in inside a request that carries the browser cookie.

    Why:
        The scope functions read the cloud session of the current request, so a
        direct test of them still needs a request context, a browser cookie, and
        a registered record. This fixture builds all three and needs no route,
        no test client, and no socket.

    Args:
        auth_app: The application from the sibling fixture.

    Yields:
        The stand-in cloud session that names one permitted organization.
    """
    session = ScopedCloudSession(PERMITTED_ORG_ID)  # One organization, and one alone.
    headers = {"Cookie": f"{identity.BROWSER_ID_COOKIE}={PROBE_BROWSER_ID}"}  # The pair check reads it.
    with auth_app.test_request_context(auth.SIGNIN_PATH, headers=headers):  # One request, held open.
        owner = identity.build_owner(PROBE_EMAIL, PROBE_BROWSER_ID)  # The pair that the registry keys on.
        identity.sign_in(owner, session, identity.CredentialMode.ENVIRONMENT_TOKEN)  # Registry and session.
        yield session  # The test runs inside this request context.


def post_signin(client: FlaskClient, body: dict[str, str]) -> TestResponse:
    """Post one sign-in body the way the browser script does.

    Why:
        The script header decides the answer shape. One helper states it once,
        so no test repeats the negotiation rule and no test depends on the
        default `Accept` header of the test client.

    Args:
        client: The test client.
        body: The fields of the post.

    Returns:
        The answer of the route.
    """
    return client.post(auth.SIGNIN_PATH, json=body, headers=SCRIPT_HEADERS)  # JSON in, and JSON out.


def error_part(response: TestResponse, name: str) -> str:
    """Read one field out of the error envelope.

    Why:
        `contracts/README.md` fixes one envelope shape for every refusal, so
        one reader serves the code assertions and the message assertions alike.

    Args:
        response: The answer of the route.
        name: Either `code` or `message`.

    Returns:
        The field value as text.
    """
    payload: Any = response.get_json()  # The envelope that the contract fixes.
    return str(payload["error"][name])  # A missing field raises here, and that is a real failure.


def pending_record(created_at: float) -> auth.PendingSignIn:
    """Build one pending sign-in record with a chosen age.

    Why:
        The store keys on a monotonic reading, so a test that chooses the
        reading can prove the expiry rule with no wait at all.

    Args:
        created_at: The monotonic reading to store on the record.

    Returns:
        A record that holds a fake session object and no credential.
    """
    session = FakeCloudSession(CLOUD_SUCCESS)  # A stand-in object, so the record looks real.
    digest = identity.email_digest(PROBE_EMAIL)  # The only form of an address that a record may hold.
    return auth.PendingSignIn(PROBE_EMAIL, digest, session, auth.DEFAULT_CLOUD_HOST, created_at)


def test_provider_login_refuses_an_empty_password(auth_client: FlaskClient, login_seam: RecordingLogin) -> None:
    """Prove that an empty provider password never reaches the cloud.

    Why:
        FR-006 lets the page drop the browser check while a token variable
        holds text, so an empty provider post can still arrive. Each such post
        would spend one attempt against the cloud sign-in rate limit.

    Args:
        auth_client: The test client.
        login_seam: The recorder that stands in for the cloud sign-in.
    """
    answer = post_signin(auth_client, {"email": PROBE_EMAIL, "password": ""})  # The empty field.
    assert answer.status_code == auth.BAD_REQUEST_STATUS  # `contracts/http-api.md` fixes 400 here.
    assert error_part(answer, "code") == auth.BAD_CREDENTIALS  # The one code that the contract allows.
    assert login_seam.calls == []  # No build ran, so the attempt never reached the cloud.
    assert login_seam.session.attempts == 0  # No login call ran either, so no attempt was spent.


def test_provider_login_refuses_a_password_of_spaces(auth_client: FlaskClient, login_seam: RecordingLogin) -> None:
    """Prove that a password of spaces reads the same as an empty password.

    Why:
        The body reader trims each field, so a value of spaces reaches the
        guard as an empty string. A separate test pins that behavior, because
        a later edit of the reader could send the spaces to the cloud.

    Args:
        auth_client: The test client.
        login_seam: The recorder that stands in for the cloud sign-in.
    """
    answer = post_signin(auth_client, {"email": PROBE_EMAIL, "password": "   "})  # Spaces alone.
    assert answer.status_code == auth.BAD_REQUEST_STATUS  # The same refusal as an empty field.
    assert error_part(answer, "code") == auth.BAD_CREDENTIALS  # The same fixed code.
    assert login_seam.calls == []  # No build ran, so the spaces never reached the cloud.


def test_the_two_refusals_share_one_code_and_differ_in_message(
    auth_client: FlaskClient, login_seam: RecordingLogin
) -> None:
    """Prove that a missing password and a missing address name different cures.

    Why:
        The contract fixes one code for both refusals, so the message is the
        only place that can name the cure. An operator who reads the general
        sentence after an empty password checks the address instead.

    Args:
        auth_client: The test client.
        login_seam: The recorder that stands in for the cloud sign-in.
    """
    no_password = post_signin(auth_client, {"email": PROBE_EMAIL, "password": ""})  # The empty password.
    no_address = post_signin(auth_client, {"email": "", "password": PROBE_PASSWORD})  # The empty address.
    assert error_part(no_password, "code") == auth.BAD_CREDENTIALS  # One code for both refusals.
    assert error_part(no_address, "code") == auth.BAD_CREDENTIALS  # The contract allows no second code.
    assert error_part(no_password, "message") != error_part(no_address, "message")  # Two cures, two sentences.
    assert error_part(no_password, "message") == auth.MISSING_PASSWORD_MESSAGE  # The cure names the field.
    assert login_seam.calls == []  # Neither post reached the cloud.


def test_provider_login_sends_the_password_to_the_builder_once(
    auth_client: FlaskClient, login_seam: RecordingLogin
) -> None:
    """Prove that a real password reaches the cloud builder exactly once.

    Why:
        The guard must refuse an empty value and must change nothing else. A
        test that only proves the refusal would still pass after an edit that
        refused every password.

    Args:
        auth_client: The test client.
        login_seam: The recorder that stands in for the cloud sign-in.
    """
    answer = post_signin(auth_client, {"email": PROBE_EMAIL, "password": PROBE_PASSWORD})  # A full pair.
    assert answer.status_code == auth.OK_STATUS  # The cloud answered with a signed-in operator.
    assert answer.get_json() == {"next": auth.NEXT_AFTER_SIGNIN}  # The body that the contract fixes.
    assert len(login_seam.calls) == 1  # One build, and never a second attempt on one post.
    assert login_seam.calls[0] == (PROBE_EMAIL, PROBE_PASSWORD, auth.DEFAULT_CLOUD_HOST)  # Each part, in order.
    assert login_seam.session.attempts == 1  # One login call followed the build.


@pytest.mark.usefixtures("token_variable")
def test_token_mode_signs_in_with_an_empty_password(
    auth_client: FlaskClient, token_seam: RecordingTokenSession, login_seam: RecordingLogin
) -> None:
    """Prove that the token mode still works with no password at all.

    Why:
        FR-006 asks for an address alone in this mode, so the new guard must
        not reach it. This test fails if a later edit moves the guard ahead of
        the mode branch.

    Args:
        auth_client: The test client.
        token_seam: The recorder that stands in for the token cloud session.
        login_seam: The recorder that stands in for the provider cloud sign-in.
    """
    body = {"email": PROBE_EMAIL, "password": "", "mode": identity.CredentialMode.ENVIRONMENT_TOKEN.value}
    answer = post_signin(auth_client, body)  # No password, which this mode allows.
    assert answer.status_code == auth.OK_STATUS  # The token mode signed the operator in.
    assert answer.get_json() == {"next": auth.NEXT_AFTER_SIGNIN}  # The body that the contract fixes.
    assert token_seam.hosts == [auth.DEFAULT_CLOUD_HOST]  # One token session, on a catalog host.
    assert login_seam.calls == []  # The provider seam stayed untouched in this mode.


@pytest.mark.usefixtures("no_token_variable")
def test_token_mode_refuses_a_sign_in_with_no_token_variable(
    auth_client: FlaskClient, token_seam: RecordingTokenSession, login_seam: RecordingLogin
) -> None:
    """Prove that the token mode refuses when no token variable holds text.

    Why:
        The refusal must reuse the general code, so no probe can learn which
        half of the setup is missing. The route must also answer the envelope
        instead of a fault page.

    Args:
        auth_client: The test client.
        token_seam: The recorder that stands in for the token cloud session.
        login_seam: The recorder that stands in for the provider cloud sign-in.
    """
    body = {"email": PROBE_EMAIL, "password": "", "mode": identity.CredentialMode.ENVIRONMENT_TOKEN.value}
    answer = post_signin(auth_client, body)  # The mode runs, and the environment holds nothing.
    assert answer.status_code == auth.BAD_REQUEST_STATUS  # The contract fixes 400 for this refusal.
    assert error_part(answer, "code") == auth.BAD_CREDENTIALS  # The same code as a refused pair.
    assert error_part(answer, "message") == auth.BAD_CREDENTIALS_MESSAGE  # No cure names the token here.
    assert login_seam.calls == []  # The provider seam stayed untouched in this mode.
    assert token_seam.hosts == [auth.DEFAULT_CLOUD_HOST]  # The build ran before the identity check refused.


def test_browser_token_sign_in_uses_a_safe_name_and_keeps_no_token(
    auth_client: FlaskClient,
    auth_app: Flask,
) -> None:
    """A browser token creates one session with a safe GetSelf identity."""
    builder = RecordingBrowserTokenSession()
    auth_app.config["BROWSER_TOKEN_SIGNIN_ALLOWED"] = True
    auth_app.config[auth.BROWSER_TOKEN_SESSION_KEY] = builder
    auth_app.config[auth.TOKEN_IDENTITY_KEY] = lambda session: {"name": "night-shift-token"}
    body = {"mode": "browser_token", "token": PROBE_TOKEN}
    answer = post_signin(auth_client, body)
    assert answer.status_code == auth.OK_STATUS
    assert answer.get_json() == {"next": auth.NEXT_AFTER_SIGNIN}
    assert builder.call_count == 1
    assert builder.hosts == [auth.DEFAULT_CLOUD_HOST]
    record = next(iter(identity.SESSION_REGISTRY._sessions.values()))
    assert record.owner.actor_email == "night-shift-token"
    assert record.credential_mode is identity.CredentialMode.BROWSER_TOKEN
    assert PROBE_TOKEN not in repr(record)


def test_browser_token_sign_in_refuses_an_empty_value_before_the_builder(
    auth_client: FlaskClient,
    auth_app: Flask,
) -> None:
    """An empty browser-token field creates no cloud session."""
    builder = RecordingBrowserTokenSession()
    auth_app.config["BROWSER_TOKEN_SIGNIN_ALLOWED"] = True
    auth_app.config[auth.BROWSER_TOKEN_SESSION_KEY] = builder
    answer = post_signin(auth_client, {"mode": "browser_token", "token": ""})
    assert answer.status_code == auth.BAD_REQUEST_STATUS
    assert error_part(answer, "code") == auth.BAD_CREDENTIALS
    assert builder.call_count == 0


def test_browser_token_sign_in_refuses_when_startup_disallows_the_mode(
    auth_client: FlaskClient,
    auth_app: Flask,
) -> None:
    """A portal that started with an environment token refuses this mode."""
    builder = RecordingBrowserTokenSession()
    auth_app.config["BROWSER_TOKEN_SIGNIN_ALLOWED"] = False
    auth_app.config[auth.BROWSER_TOKEN_SESSION_KEY] = builder
    answer = post_signin(auth_client, {"mode": "browser_token", "token": PROBE_TOKEN})
    assert answer.status_code == auth.BAD_REQUEST_STATUS
    assert error_part(answer, "code") == auth.BAD_CREDENTIALS
    assert builder.call_count == 0


def test_sign_in_with_no_address_reaches_no_builder(auth_client: FlaskClient, login_seam: RecordingLogin) -> None:
    """Prove that a post with no address stops before the cloud call.

    Why:
        The portal cannot name an owner without an address, so the pair cannot
        pass. The refusal must also carry the general sentence, because the
        password of that post is not the fault.

    Args:
        auth_client: The test client.
        login_seam: The recorder that stands in for the cloud sign-in.
    """
    answer = post_signin(auth_client, {"email": "", "password": PROBE_PASSWORD})  # No address.
    assert answer.status_code == auth.BAD_REQUEST_STATUS  # The contract fixes 400 for a refused pair.
    assert error_part(answer, "message") == auth.BAD_CREDENTIALS_MESSAGE  # The general sentence, not the cure.
    assert login_seam.calls == []  # The password never reached the cloud.


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ({"password": PROBE_PASSWORD}, True),  # A typed value.
        ({"password": ""}, False),  # An empty field, which the page may now allow.
        ({"password": "   "}, False),  # Spaces alone, which the reader trims to nothing.
        ({"email": PROBE_EMAIL}, False),  # No password field at all.
    ],
)
def test_password_present_reads_a_json_body(auth_app: Flask, body: dict[str, str], expected: bool) -> None:
    """Prove the truth test that the guard depends on.

    Why:
        The guard is one call to this helper, so the helper carries the whole
        rule. A direct test states each shape that a script body can hold.

    Args:
        auth_app: The application from the fixture.
        body: The JSON body under test.
        expected: The answer that the helper must give.
    """
    with auth_app.test_request_context(auth.SIGNIN_PATH, json=body):  # One request, with that body.
        assert auth.password_present() is expected  # The guard reads this answer and nothing else.


def test_password_present_reads_a_plain_form_body(auth_app: Flask) -> None:
    """Prove that the truth test also serves a page without the script.

    Why:
        The sign-in page must work when the browser script does not run, so
        the reader accepts a form body as well as a JSON body.

    Args:
        auth_app: The application from the fixture.
    """
    form = {"password": PROBE_PASSWORD}  # The shape that a plain form post sends.
    with auth_app.test_request_context(auth.SIGNIN_PATH, method="POST", data=form):  # A form post.
        assert auth.password_present() is True  # The form path reads the same as the script path.


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (CLOUD_SUCCESS, auth.STATE_OK),  # The success flag wins over every other reading.
        (CLOUD_TWO_FACTOR, auth.STATE_TWO_FACTOR),  # The nested flag of the newer release.
        ({"two_factor_required": True}, auth.STATE_TWO_FACTOR),  # The flat flag of the older release.
        (CLOUD_THROTTLED, auth.STATE_RATE_LIMITED),  # A throttle, named in the reason text.
        ({"status_code": 429}, auth.STATE_RATE_LIMITED),  # A throttle, named in the transport status.
        (CLOUD_REFUSED, auth.STATE_REFUSED),  # A judged pair, which the cloud refused.
        ({}, auth.STATE_REFUSED),  # An answer that names nothing counts as a refusal.
    ],
)
def test_login_state_classifies_one_cloud_answer(result: dict[str, Any], expected: str) -> None:
    """Prove that each cloud answer reaches exactly one state.

    Why:
        Four route branches follow from this one classifier. A throttle that
        reads as a refused pair makes an operator change a correct password,
        and that locks the account.

    Args:
        result: The cloud answer under test.
        expected: The state that the classifier must report.
    """
    assert auth.login_state(result) == expected  # One reading, and never two.


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("too many requests", True),  # One wording of a throttle.
        ("rate limit reached", True),  # A second wording of the same event.
        ("http 429 from the cloud", True),  # The status inside the text.
        ("invalid credentials", False),  # A judged pair, and never a throttle.
        ("", False),  # An answer that names no reason.
    ],
)
def test_rate_limit_marked_reads_each_wording(text: str, expected: bool) -> None:
    """Prove that each throttle wording separates from a refused pair.

    Why:
        The cloud reports a throttle in its reason text and not in a flag, so
        the wordings are the whole rule.

    Args:
        text: The reason text under test, already in lower case.
        expected: The answer that the reader must give.
    """
    assert auth.rate_limit_marked(text) is expected  # A truth answer, so a caller needs no cast.


@pytest.mark.parametrize(
    "raw_host",
    [
        "",  # No host at all, which the default covers.
        "api.attacker.example.invalid",  # A host that the catalog does not name.
        "api.mist.com.attacker.example",  # A host that only starts like a real one.
    ],
)
def test_resolve_host_refuses_a_host_outside_the_catalog(raw_host: str) -> None:
    """Prove that a crafted host cannot redirect the password.

    Why:
        The host decides where the password travels. Free text here would let
        a crafted post send the password to a server that an attacker owns.

    Args:
        raw_host: The host value that the request named.
    """
    assert auth.resolve_host(raw_host) == auth.DEFAULT_CLOUD_HOST  # The safe answer, every time.


def test_resolve_host_keeps_a_host_that_the_catalog_names() -> None:
    """Prove that the check refuses no legitimate cloud.

    Why:
        A check that refused every value would also pass the test above, and
        the portal would then reach one cloud alone.
    """
    assert auth.resolve_host(auth.DEFAULT_CLOUD_HOST) == auth.DEFAULT_CLOUD_HOST  # The catalog names it.


@pytest.mark.parametrize(
    ("raw_email", "expected"),
    [
        ("Jane.Operator@Example.COM", "jane.operator@example.com"),  # One spelling, so two records join.
        ("  spaced@example.com  ", "spaced@example.com"),  # A trimmed value still reads as an address.
        ("", ""),  # An empty value, which the caller answers as a refused pair.
        ("no-at-sign", ""),  # A value that cannot name a mailbox.
        ("two@@example.com", ""),  # A value that the address pattern refuses.
    ],
)
def test_valid_email_normalizes_or_refuses(raw_email: str, expected: str) -> None:
    """Prove that a bad address answers the envelope instead of a fault page.

    Why:
        The identity module raises on a bad address, and a route must answer
        the contract envelope. This wrapper turns the exception into the empty
        value that the route already handles.

    Args:
        raw_email: The address that the operator typed.
        expected: The normalized address, or an empty string.
    """
    assert auth.valid_email(raw_email) == expected  # One spelling, or nothing at all.


def test_pending_record_hides_the_cloud_session_and_the_address() -> None:
    """Prove that a traceback cannot publish a session object or an address.

    Why:
        A debugger, a log call, and a traceback all print a record. The
        automatic form would publish the `mistapi` object, which holds
        credential state, and the address, which is personal data.
    """
    record = pending_record(time.monotonic())  # A record that holds a stand-in session object.
    printed = repr(record)  # The one form that a traceback shows.
    assert identity.email_digest(PROBE_EMAIL) in printed  # The digest names the operator.
    assert PROBE_EMAIL not in printed  # No address, because an address is personal data.
    assert "FakeCloudSession" not in printed  # No session object, because it holds credential state.


def test_login_outcome_hides_the_cloud_session() -> None:
    """Prove that the outcome record also prints no session object.

    Why:
        The same reason as the record above. This record travels through the
        route branches, so it reaches more log calls and more tracebacks.
    """
    outcome = auth.LoginOutcome(auth.STATE_OK, FakeCloudSession(CLOUD_SUCCESS))  # A live object inside.
    printed = repr(outcome)  # The one form that a traceback shows.
    assert auth.STATE_OK in printed  # The decision is safe to print.
    assert "FakeCloudSession" not in printed  # The object behind the decision is not.


def test_read_pending_forgets_a_wait_that_expired() -> None:
    """Prove that an old wait reads as absent instead of stale.

    Why:
        A cloud session object holds transport state. An abandoned wait must
        not keep one alive for the life of the worker, and a retry must never
        reach a session that the cloud already dropped.
    """
    old = pending_record(time.monotonic() - auth.PENDING_SECONDS - 1.0)  # One second past the limit.
    auth.remember_pending(PROBE_BROWSER_ID, old)  # The store accepts it, because the store checks on read.
    assert auth.read_pending(PROBE_BROWSER_ID) is None  # The read purges first, so the wait is gone.


def test_read_pending_returns_a_wait_that_is_still_open() -> None:
    """Prove that the expiry rule drops no live wait.

    Why:
        A store that dropped every record would also pass the test above, and
        no operator could ever finish a second factor step.
    """
    fresh = pending_record(time.monotonic())  # A wait that started in this moment.
    auth.remember_pending(PROBE_BROWSER_ID, fresh)  # The normal path of a second factor step.
    assert auth.read_pending(PROBE_BROWSER_ID) is fresh  # The same object, so the retry reaches the cloud.


def test_the_pending_store_holds_at_the_cap() -> None:
    """Prove that a flood of half-finished sign-ins cannot grow the process.

    Why:
        Each record holds a live cloud session object. Without the cap a
        crafted flood would raise the memory of the worker without a bound.
    """
    base = time.monotonic()  # One reading, so every record below counts as fresh.
    for index in range(auth.PENDING_LIMIT + 1):  # One record past the cap.
        auth.remember_pending(f"browser-{index:04d}-Ab12_cd34", pending_record(base + index * 0.001))
    assert len(auth._PENDING) == auth.PENDING_LIMIT  # The store never passes the cap.
    assert "browser-0000-Ab12_cd34" not in auth._PENDING  # The oldest wait went, and never the newest.
    assert f"browser-{auth.PENDING_LIMIT:04d}-Ab12_cd34" in auth._PENDING  # The newest wait stayed.


def test_a_script_request_reads_json_even_while_the_page_asks_for_html(auth_app: Flask) -> None:
    """Prove that the script header wins over the page header.

    Why:
        A script inside a browser page inherits the `Accept` header of that
        page. Without this rule the script would receive a whole page and
        would report a fault to the operator.

    Args:
        auth_app: The application from the fixture.
    """
    headers = dict(SCRIPT_HEADERS)  # The header that a script sets on its own request.
    headers["Accept"] = "text/html"  # The header that the page contributes.
    with auth_app.test_request_context(auth.SIGNIN_PATH, headers=headers):  # One request, with both.
        assert auth.wants_browser_page() is False  # The script reads JSON, whatever the page states.


def test_a_plain_form_post_reads_a_page(auth_app: Flask) -> None:
    """Prove that a browser without the script still receives a page.

    Why:
        A browser shows a JSON body as raw text, so a plain form post must
        receive the form again with the reason on it.

    Args:
        auth_app: The application from the fixture.
    """
    with auth_app.test_request_context(auth.SIGNIN_PATH, headers={"Accept": "text/html"}):  # No script header.
        assert auth.wants_browser_page() is True  # The browser reads a page.


def test_an_injected_seam_that_cannot_be_called_reads_as_unset(auth_app: Flask) -> None:
    """Prove that a wrong configuration value cannot replace the cloud builder.

    Why:
        A settings mistake would otherwise raise inside the sign-in path and
        answer a fault page. The route then falls back to the real builder,
        which is the documented behavior.

    Args:
        auth_app: The application from the fixture.
    """
    auth_app.config[auth.CLOUD_LOGIN_KEY] = "not a callable"  # A settings mistake, and not a seam.
    with auth_app.test_request_context(auth.SIGNIN_PATH):  # The seam reader needs an application context.
        assert auth.injected_seam(auth.CLOUD_LOGIN_KEY) is None  # A value that is not callable reads as unset.


@identity.require_org_scope
def guarded_probe_view(org_id: str = "") -> str:
    """Answer one probe request that the organization guard admitted.

    Why:
        The guard reads the path argument named `org_id`. A view of this shape
        lets a test call the guard on its own, with no route table, no client,
        and no second blueprint.

    Args:
        org_id: The organization that the path named, or an empty string.

    Returns:
        The fixed word that proves the guard called this function.
    """
    return VIEW_REACHED  # A refusal returns an envelope instead, so the two answers never look alike.


def refusal_parts(org_id: str) -> tuple[str, int]:
    """Read the error code and the status out of one scope refusal.

    Why:
        The refusal returns None when the request may continue, so a test that
        indexed the answer would report a confusing `TypeError`. This reader
        turns that case into a plain failure sentence.

    Args:
        org_id: The organization that the request names.

    Returns:
        The error code and the status code.

    Raises:
        AssertionError: When the scope check let the organization continue.
    """
    refusal = identity.org_scope_refusal(org_id)  # None means the request may continue.
    if refusal is None:  # A test that expected a refusal must fail with a sentence.
        raise AssertionError(f"The scope check let the organization {org_id} continue.")
    response, status = refusal  # The envelope and the status always travel together.
    payload: Any = response.get_json()  # The one envelope shape that the contract fixes.
    return str(payload["error"]["code"]), status  # The two parts that a browser script reads.


def probe_body() -> dict[str, Any]:
    """Build one body shaped like a sign-in post.

    Why:
        A shared dictionary would let one test change the body of another. A
        builder gives each test a copy of its own. The body holds one credential
        field at the top and one credential field a level down.

    Returns:
        The body, with obviously fake values throughout.
    """
    return {"email": PROBE_EMAIL, "password": PROBE_PASSWORD, "headers": {"Authorization": PROBE_TOKEN}}


@pytest.mark.usefixtures("scoped_request")
def test_the_scope_check_permits_an_organization_that_the_session_names() -> None:
    """Prove that the scope check admits an organization inside the privileges.

    Why:
        A check that refused every organization would also pass the refusal test
        below, and no operator could then reach any site at all.
    """
    assert identity.org_is_permitted(PERMITTED_ORG_ID) is True  # The privilege list names this one.


@pytest.mark.usefixtures("scoped_request")
def test_the_scope_check_refuses_an_organization_that_the_session_omits() -> None:
    """Prove that the scope check refuses an organization outside the privileges.

    Why:
        The cloud session of one operator reaches a fixed set of organizations.
        A portal that trusted the path alone would let an operator capture and
        upgrade an organization that the credential never granted.
    """
    assert identity.org_is_permitted(OUTSIDE_ORG_ID) is False  # The privilege list omits this one.


@pytest.mark.usefixtures("scoped_request")
def test_the_scope_refusal_names_the_contract_code_and_status() -> None:
    """Prove that a refusal answers 403 with the code that the contract fixes.

    Why:
        The browser script reads the code and shows the sentence that matches
        it. A second code, or a second status, would leave the operator with a
        blank page instead of a reason.
    """
    assert refusal_parts(OUTSIDE_ORG_ID) == (ORG_REFUSED_CODE, ORG_REFUSED_STATUS)  # One code, one status.


@pytest.mark.usefixtures("scoped_request")
def test_the_scope_refusal_lets_an_organization_inside_the_scope_continue() -> None:
    """Prove that the refusal builder returns nothing for a permitted organization.

    Why:
        The route calls this function before it reads anything. A builder that
        answered an envelope every time would refuse every request of every
        operator.
    """
    assert identity.org_scope_refusal(PERMITTED_ORG_ID) is None  # Nothing to refuse, so the route runs.


@pytest.mark.usefixtures("scoped_request")
def test_the_guard_refuses_a_path_that_names_an_organization_outside_the_scope() -> None:
    """Prove that the guard answers the refusal before the view runs.

    Why:
        A view that ran first would read a site, a run, or a capture of an
        organization that the credential never granted.
    """
    answer = guarded_probe_view(org_id=OUTSIDE_ORG_ID)  # Flask passes a path converter as a keyword.
    assert answer != VIEW_REACHED, "The guard let the view run for an organization outside the scope."


@pytest.mark.usefixtures("scoped_request")
def test_the_guard_admits_a_path_that_names_no_organization() -> None:
    """Prove that the guard runs a view whose path names no organization.

    Why:
        Several guarded paths name a site alone. A guard that refused every one
        of them would close the portal, and the refusal tests above would still
        pass.
    """
    assert guarded_probe_view() == VIEW_REACHED  # Nothing to check means nothing to refuse.


def test_redaction_replaces_a_credential_value_with_the_name_of_its_field() -> None:
    """Prove that a password never survives a copy of a body.

    Why:
        A caller that must record a body calls this function first. FR-009
        forbids the value in a log record, in an answer body, and in a store.
    """
    safe = identity.redact_credentials(probe_body())  # The copy that a record may hold.
    assert safe["password"] == "<password>"  # The field name in brackets, and never the value.


def test_redaction_reaches_a_credential_inside_a_nested_body() -> None:
    """Prove that the copy replaces a credential one level down as well.

    Why:
        A header map arrives inside a body. A copy that read the top level alone
        would publish the token that the header carried.
    """
    safe = identity.redact_credentials(probe_body())  # The copy that a record may hold.
    assert safe["headers"] == {"Authorization": "<Authorization>"}  # The name, and never the token.


def test_redaction_keeps_a_field_that_names_no_credential() -> None:
    """Prove that the copy drops nothing that a reader needs.

    Why:
        A copy that replaced every value would also pass the two tests above,
        and a recorded body would then name nothing at all.
    """
    safe = identity.redact_credentials(probe_body())  # The copy that a record may hold.
    assert safe["email"] == PROBE_EMAIL  # An address names no credential field, so the copy keeps it.


def test_redaction_leaves_the_body_of_the_caller_unchanged() -> None:
    """Prove that the body still holds what it held before the copy.

    Why:
        A caller records a body and then uses it. A function that edited the
        body in place would take the token away from the request that follows
        the record.
    """
    body = probe_body()  # A body of this test alone.
    identity.redact_credentials(body)  # The copy, which this test throws away.
    assert body["headers"] == {"Authorization": PROBE_TOKEN}  # The nested map is the risky one.
