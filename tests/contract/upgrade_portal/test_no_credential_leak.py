"""Contract tests that prove no credential value leaves the portal.

Why:
    FR-009 states one rule: a password, a second factor code, and a cloud token
    never leave the portal. The rule has no single choke point, because a value
    can leave through a response body, a header, a cookie, a rendered page, the
    signed session, or a log record. This file drives every one of those exits
    and searches each for the exact probe values.

    ``tests/contract/upgrade_portal/test_auth.py`` proves four parts of the same
    rule: no log message, no refusal body, and no ``repr`` of a half-finished
    sign-in holds a value. It reads the log message alone, and it never inspects
    a header, a cookie, the signed session, or the pages after the sign-in. This
    file covers those exits, reads the argument list and the traced fault of
    each log record beside its message, and pins the redaction guard.

    Every probe value below is an obvious stand-in. A reader sees at once that
    no string here is a secret, and a search for the exact string proves the
    rule. No test reads the ``.env`` file, and no test prints a value it found.

Caution:
    A test in this file must never print a credential value on a failure. Each
    assertion message therefore names the exit that leaked, and never the value.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.runtime import identity

# ---------------------------------------------------------------------------
# The probe values and the contract paths
# ---------------------------------------------------------------------------

# WHY: Four obvious stand-ins. A leak check searches for these exact strings, so
# each one must be long enough that no template or log word holds it by chance.
PROBE_EMAIL = "probe.operator@example.invalid"
PROBE_PASSWORD = "fake-password-for-tests-only"
PROBE_CODE = "424242"
PROBE_TOKEN = "fake-api-token-for-tests-only"

# WHY: The three values that FR-009 keeps inside the portal. One tuple lets each
# test search for all three with one loop.
SECRETS = (PROBE_PASSWORD, PROBE_CODE, PROBE_TOKEN)

# WHY: The contract fixes each path. A test never imports the matching constant,
# because an imported constant would agree with a renamed path.
SIGNIN_PATH = "/auth/signin"
TWO_FACTOR_PATH = "/auth/twofactor"
SIGNOUT_PATH = "/auth/signout"
ORG_PATH = "/select/org"

# WHY: The cloud answers a mapping. These shapes drive the two-factor branch and
# the refusal branch, and neither shape holds a credential value.
CLOUD_SUCCESS: dict[str, Any] = {"authenticated": True}
CLOUD_TWO_FACTOR: dict[str, Any] = {"error": {"two_factor_required": True}}
CLOUD_REFUSED: dict[str, Any] = {"error": {"message": "invalid credentials"}}

# WHY: A browser form post states this header, so the route renders a page
# instead of a JSON body. The page is a separate exit and needs its own check.
BROWSER_HEADERS = {"Accept": "text/html"}

# WHY: The environment variable that the token mode reads. The test sets it to a
# stand-in with `monkeypatch`, so no real variable is read and none is changed.
TOKEN_VARIABLE = "MIST_APITOKEN"

# WHY: The field names that the redaction guard must recognize. The list is the
# rule of FR-009 written out, so a dropped name shows here as a failure.
GUARDED_FIELD_NAMES = ("password", "secret", "token", "api_token", "apikey", "authorization", "otp")

SET_COOKIE_HEADER = "Set-Cookie"
LOCATION_HEADER = "Location"


# ---------------------------------------------------------------------------
# The stand-ins for the cloud
# ---------------------------------------------------------------------------


class FakeCloudSession:
    """A stand-in for the cloud session object of the Mist library.

    Why:
        A contract test checks the answer of the portal and not the transport.
        This stub answers each login call from a script, so no test opens a
        socket and no test needs a real credential.
    """

    def __init__(self, script: list[dict[str, Any]]) -> None:
        """Create the stub with the answers it will give, in order.

        Args:
            script: One answer for each expected login call.
        """
        self.script = list(script)  # WHY: A copy stops a later edit of the caller list.

    def login_with_return(self, two_factor: str = "") -> dict[str, Any]:
        """Answer the next scripted result.

        Args:
            two_factor: The second factor code, or an empty string.

        Returns:
            The next scripted answer, or an empty mapping when the script ran out.
        """
        del two_factor  # WHY: This file proves that the code leaves no trace, so no copy is kept.
        return self.script.pop(0) if self.script else {}  # WHY: An empty answer reads as a refusal.


def token_session(host: str) -> FakeCloudSession:
    """Answer a stub cloud session for the environment token mode.

    Why:
        The token mode builds its session from the variable of the environment.
        This stub proves that the portal never carries the value onward, because
        the stub reads no token at all.

    Args:
        host: The Mist cloud that the catalog named.

    Returns:
        The stub cloud session.
    """
    del host  # WHY: The stub opens no socket, so the host changes nothing.
    return FakeCloudSession([])  # WHY: An empty script, because the token mode makes no login call.


class QuietLogin:
    """A stand-in for the cloud session builder that keeps no copy.

    Why:
        The builder call is the one expression of the portal that holds a
        password. A stub that stored the password would put the value inside
        this test process a second time, so this stub drops all three arguments
        and answers the session alone.
    """

    def __init__(self, script: list[dict[str, Any]]) -> None:
        """Create the builder with the script of its session.

        Args:
            script: One cloud answer for each expected login call.
        """
        self.session = FakeCloudSession(script)  # WHY: The retry call needs this same object.

    def __call__(self, actor_email: str, password: str, host: str) -> FakeCloudSession:
        """Answer the stub session for one sign-in attempt.

        Args:
            actor_email: The work address of the operator.
            password: The password, which this stub reads and drops.
            host: The Mist cloud that the catalog named.

        Returns:
            The stub cloud session.
        """
        del actor_email, password, host  # WHY: No copy, so this stub adds no exit of its own.
        return self.session  # WHY: The second factor retry reads the same script.


class FailingLogin:
    """A builder that raises, to drive the transport fault branch.

    Why:
        A refused socket must answer the contract envelope and must write no
        credential to the log. The fault branch has its own log line, so it
        needs its own proof.
    """

    def __call__(self, actor_email: str, password: str, host: str) -> FakeCloudSession:
        """Raise the fault that a refused socket raises.

        Args:
            actor_email: The work address of the operator.
            password: The password, which never leaves this call.
            host: The Mist cloud that the catalog named.

        Returns:
            Nothing, because this call always raises.

        Raises:
            RuntimeError: Always, with text that holds no credential.
        """
        del actor_email, password, host  # WHY: The fault path must not carry them onward.
        raise RuntimeError("connection refused")  # WHY: The route must turn this into a contract answer.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def response_surfaces(response: TestResponse) -> str:
    """Return every part of one response that could carry a value out.

    Why:
        A leak can leave in the body, in a redirect path, or in a cookie. One
        reader joins all three, so no test forgets an exit.

    Args:
        response: The response to read.

    Returns:
        The body and every header of the response, as one block of text.
    """
    parts = [response.get_data(as_text=True)]  # WHY: The body, whether it is JSON or markup.
    parts.extend(f"{name}: {value}" for name, value in response.headers.items())  # WHY: Location and Set-Cookie.
    return "\n".join(parts)


def assert_no_secret(written: str, exit_name: str) -> None:
    """Fail when one block of text holds any probe value.

    Why:
        Every test of this file ends with the same three searches. One helper
        keeps the wording of the failure the same, and it never prints the value
        that leaked.

    Args:
        written: The text to search.
        exit_name: The exit that produced the text, named for the failure.

    Raises:
        AssertionError: When the text holds a password, a code, or a token.
    """
    for secret in SECRETS:  # WHY: Three values, and one search for each.
        assert secret not in written, f"A credential value left the portal through {exit_name}."


def log_surfaces(records: list[logging.LogRecord]) -> str:
    """Return the message, the arguments, and the trace of every log record.

    Why:
        A record can carry a value in three places. `getMessage` covers the
        first, `args` holds a value that no format string consumed, and
        `exc_text` holds the traced fault. A check of the message alone would
        pass while a value sat in the other two.

    Args:
        records: The captured log records.

    Returns:
        All three parts of every record, as one block of text.
    """
    parts: list[str] = []  # WHY: One list, so the caller runs one search.
    for record in records:  # WHY: Every record, at every level.
        parts.append(record.getMessage())  # WHY: The formatted line that a reader sees.
        parts.append(repr(record.args))  # WHY: An argument that no placeholder consumed still travels.
        parts.append(str(record.exc_text or ""))  # WHY: A traced fault can hold a call argument.
    return "\n".join(parts)


def post_signin(client: FlaskClient, **fields: str) -> TestResponse:
    """Post the sign-in form with the probe pair.

    Args:
        client: The Flask test client.
        **fields: Field values that replace the probe pair.

    Returns:
        The response of the portal.
    """
    body = {"email": PROBE_EMAIL, "password": PROBE_PASSWORD}  # WHY: The probe pair of every test here.
    body.update(fields)  # WHY: One test replaces a field to drive another branch.
    return client.post(SIGNIN_PATH, json=body)


def post_signin_form(client: FlaskClient) -> TestResponse:
    """Post the sign-in form the way a browser posts it.

    Why:
        A browser form post reads a page and not a JSON body. The page and the
        redirect path are two exits that the script post never produces.

    Args:
        client: The Flask test client.

    Returns:
        The response of the portal.
    """
    body = {"email": PROBE_EMAIL, "password": PROBE_PASSWORD}  # WHY: The same probe pair, in form fields.
    return client.post(SIGNIN_PATH, data=body, headers=BROWSER_HEADERS)


def run_two_factor_journey(client: FlaskClient, app: Flask) -> list[TestResponse]:
    """Sign one operator in through the pair and the second factor.

    Why:
        The longest journey touches the most exits. Six tests below drive it, so
        one helper holds the three posts and the cloud script in one place.

    Args:
        client: The Flask test client.
        app: The portal application, which carries the injected seam.

    Returns:
        The response of each step, in order.
    """
    app.config["CLOUD_LOGIN"] = QuietLogin([CLOUD_TWO_FACTOR, CLOUD_SUCCESS])  # WHY: A pair, then a code.
    first = post_signin(client)  # WHY: The cloud asks for a second factor.
    second = client.post(TWO_FACTOR_PATH, json={"code": PROBE_CODE})  # WHY: The code finishes the sign-in.
    third = client.get(ORG_PATH)  # WHY: The first page after the sign-in is an exit as well.
    return [first, second, third]


def registered_record(client: FlaskClient) -> Any:
    """Return the session record that a successful sign-in registered.

    Args:
        client: The Flask test client that holds the signed session.

    Returns:
        The registered record, or None when the client holds no session.
    """
    with client.session_transaction() as browser_session:
        key = browser_session.get(identity.SESSION_OWNER_KEY)  # WHY: The registry key of this operator.
    return None if key is None else identity.SESSION_REGISTRY.get(str(key))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def leak_app(portal_app: Flask) -> Flask:
    """Return the portal application with the token check turned off.

    Why:
        Every post of this surface carries a token in the browser, and
        `test_security.py` already owns that coverage. This file drives the
        credential rule alone, so the token step would only add noise.

    Args:
        portal_app: The real application from the shared fixture.

    Returns:
        The application, ready for a post.
    """
    portal_app.config["WTF_CSRF_ENABLED"] = False  # WHY: `test_security.py` owns the token cover.
    return portal_app


@pytest.fixture
def leak_client(leak_app: Flask) -> Iterator[FlaskClient]:
    """Return a test client and clear the registry record it leaves behind.

    Why:
        A successful sign-in registers a record in a process global. The
        sign-out post at the end of the fixture clears it, so no record of this
        file reaches a later test.

    Args:
        leak_app: The application with the token check turned off.

    Yields:
        The Flask test client, with the session held open.
    """
    with leak_app.test_client() as client:  # WHY: The context manager holds the session across requests.
        try:
            yield client
        finally:
            client.post(SIGNOUT_PATH)  # WHY: The registry outlives the test, so clear it here.


# ---------------------------------------------------------------------------
# The response exits
# ---------------------------------------------------------------------------


def test_a_refused_signin_answers_no_credential(leak_client: FlaskClient, leak_app: Flask) -> None:
    """A refused sign-in answers no body, header, or cookie that holds a value.

    Why:
        A refusal is the answer that an attacker sees most often, because a
        wrong guess produces one every time.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
    """
    leak_app.config["CLOUD_LOGIN"] = QuietLogin([CLOUD_REFUSED])
    answer = post_signin(leak_client)
    assert_no_secret(response_surfaces(answer), "the refused sign-in answer")


def test_a_successful_signin_answers_no_credential(leak_client: FlaskClient, leak_app: Flask) -> None:
    """A successful sign-in answers no body, header, or cookie that holds a value.

    Why:
        The successful answer sets the browser cookie. A cookie travels with
        every later request, so a value inside one would leave the portal on
        every page the operator opens.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
    """
    leak_app.config["CLOUD_LOGIN"] = QuietLogin([CLOUD_SUCCESS])
    answer = post_signin(leak_client)
    assert_no_secret(response_surfaces(answer), "the successful sign-in answer")


def test_no_step_of_the_journey_answers_a_credential(leak_client: FlaskClient, leak_app: Flask) -> None:
    """No step of the sign-in journey answers a value.

    Why:
        The second factor step reads a code, and the picker page reads the
        session that both steps built. Each step is a separate exit.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
    """
    for index, answer in enumerate(run_two_factor_journey(leak_client, leak_app)):
        assert_no_secret(response_surfaces(answer), f"step {index + 1} of the sign-in journey")


def test_no_set_cookie_header_holds_a_credential(leak_client: FlaskClient, leak_app: Flask) -> None:
    """No cookie that the journey sets holds a credential value.

    Why:
        FR-073 gives the browser one first-party cookie, and that cookie holds a
        random identifier alone. A credential inside a cookie would travel on
        every request and would sit on the disk of the workstation.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
    """
    written: list[str] = []
    for answer in run_two_factor_journey(leak_client, leak_app):
        written.extend(answer.headers.getlist(SET_COOKIE_HEADER))  # WHY: A step may set more than one cookie.
    assert_no_secret("\n".join(written), "a cookie")


def test_no_redirect_path_holds_a_credential(leak_client: FlaskClient, leak_app: Flask) -> None:
    """No redirect path of the journey holds a credential value.

    Why:
        A path reaches the history of the browser, the address bar, and the
        access log of every proxy on the way. A value there survives the
        session that produced it.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
    """
    leak_app.config["CLOUD_LOGIN"] = QuietLogin([CLOUD_SUCCESS])
    answer = post_signin_form(leak_client)
    assert_no_secret(str(answer.headers.get(LOCATION_HEADER, "")), "a redirect path")


def test_the_signin_page_after_a_refusal_holds_no_credential(leak_client: FlaskClient, leak_app: Flask) -> None:
    """The sign-in page shown after a refusal holds no credential value.

    Why:
        A form that filled the password field again would put the value in the
        markup, where a browser extension and a page cache both reach it.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
    """
    leak_app.config["CLOUD_LOGIN"] = QuietLogin([CLOUD_REFUSED])
    answer = post_signin_form(leak_client)
    page = answer.get_data(as_text=True)
    assert 'data-testid="signin-error"' in page, "The refused page shows no error region, so this test proves little."
    assert_no_secret(page, "the sign-in page")


def test_the_signed_session_holds_no_credential(leak_client: FlaskClient, leak_app: Flask) -> None:
    """The signed browser session holds no credential value.

    Why:
        The session is signed and not sealed, so a reader with the cookie reads
        every field inside it. A credential there would be readable on the
        workstation, whatever the signature proves.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
    """
    run_two_factor_journey(leak_client, leak_app)
    with leak_client.session_transaction() as browser_session:
        stored = {str(name): repr(value) for name, value in browser_session.items()}
    assert_no_secret(repr(stored), "the signed browser session")


# ---------------------------------------------------------------------------
# The log exit
# ---------------------------------------------------------------------------


def test_no_log_record_holds_a_credential(
    leak_client: FlaskClient,
    leak_app: Flask,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """No log record of the journey holds a credential value.

    Why:
        A log file outlives the session, travels to a collector, and is read by
        people who never signed in. It is the exit with the longest reach.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
        caplog: The log capture of pytest.
    """
    with caplog.at_level(logging.DEBUG):  # WHY: The lowest level, so no record escapes the search.
        run_two_factor_journey(leak_client, leak_app)
    assert_no_secret(log_surfaces(caplog.records), "a log record")


def test_no_log_record_holds_the_work_address_in_plain_text(
    leak_client: FlaskClient,
    leak_app: Flask,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """No log record names the work address in plain text.

    Why:
        The address is not a credential, and FR-009 still keeps it out of the
        log. An address names a person, so a log full of addresses becomes a
        staff list that anybody with log access can read.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
        caplog: The log capture of pytest.
    """
    with caplog.at_level(logging.DEBUG):
        run_two_factor_journey(leak_client, leak_app)
    assert PROBE_EMAIL not in log_surfaces(caplog.records), "A log record names the work address in plain text."


def test_the_log_names_the_operator_by_digest(
    leak_client: FlaskClient,
    leak_app: Flask,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A log record still names the operator, through the one-way digest.

    Why:
        Without this test the check above would pass on a portal that logged
        nothing at all. The digest proves that the portal still records who
        acted, in the one form that names no person by itself.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
        caplog: The log capture of pytest.
    """
    with caplog.at_level(logging.INFO):
        run_two_factor_journey(leak_client, leak_app)
    assert identity.email_digest(PROBE_EMAIL) in log_surfaces(caplog.records), "No record names the digest."


def test_a_transport_fault_writes_no_credential_to_the_log(
    leak_client: FlaskClient,
    leak_app: Flask,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A refused cloud call writes no credential value to the log.

    Why:
        A fault path often logs the traced call, and a trace holds every
        argument of every frame. The password is an argument of the builder
        call, so this branch is the most likely place for a leak.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
        caplog: The log capture of pytest.
    """
    leak_app.config["CLOUD_LOGIN"] = FailingLogin()
    with caplog.at_level(logging.DEBUG):
        post_signin(leak_client)
    assert_no_secret(log_surfaces(caplog.records), "a log record of the fault path")


def test_the_token_mode_writes_no_token_to_the_log(
    leak_client: FlaskClient,
    leak_app: Flask,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The environment token mode writes no token to the log or the answer.

    Why:
        FR-006 offers a mode where the token is already in the environment. The
        portal reads that variable, so it must name the variable and never the
        value it holds.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
        caplog: The log capture of pytest.
        monkeypatch: The environment patcher, which restores the variable after.
    """
    monkeypatch.setenv(TOKEN_VARIABLE, PROBE_TOKEN)  # WHY: A stand-in value, so no real token is read.
    leak_app.config["CLOUD_TOKEN_SESSION"] = token_session  # WHY: The seam replaces the real cloud call.
    with caplog.at_level(logging.DEBUG):
        answer = leak_client.post(SIGNIN_PATH, json={"email": PROBE_EMAIL, "mode": "environment_token"})
    assert_no_secret(response_surfaces(answer), "the token mode answer")
    assert_no_secret(log_surfaces(caplog.records), "a log record of the token mode")


# ---------------------------------------------------------------------------
# The identity module holds no credential value
# ---------------------------------------------------------------------------


def test_the_session_record_holds_no_credential_field(leak_client: FlaskClient, leak_app: Flask) -> None:
    """No field of the registered session record holds a credential value.

    Why:
        The record lives for the whole session. A password copied into a field
        here would sit in the memory of the process until the operator signs
        out, and it would reach any dump of that process.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
    """
    run_two_factor_journey(leak_client, leak_app)
    record = registered_record(leak_client)
    assert record is not None, "The journey registered no session, so this test proves nothing."
    for field in dataclasses.fields(record):  # WHY: Reaches a field that the record hides from its own repr.
        assert_no_secret(repr(getattr(record, field.name)), f"the session field {field.name}")


def test_the_registry_holds_no_credential_value(leak_client: FlaskClient, leak_app: Flask) -> None:
    """The session registry shows no credential value in its own text form.

    Why:
        A fault page and a debug line both print a registry. The printed form
        must therefore hold no value, whatever the fields behind it hold.

    Args:
        leak_client: The test client.
        leak_app: The portal application.
    """
    run_two_factor_journey(leak_client, leak_app)
    assert_no_secret(repr(identity.SESSION_REGISTRY), "the session registry")


def test_the_environment_check_answers_presence_and_never_a_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """The environment token check answers a yes or no and never the token.

    Why:
        A reader that returned the token would put the value into a caller that
        only wanted to know whether a token exists. The answer is therefore a
        plain yes or no.

    Args:
        monkeypatch: The environment patcher, which restores the variable after.
    """
    monkeypatch.setenv(TOKEN_VARIABLE, PROBE_TOKEN)
    answer = identity.environment_token_present()
    assert answer is True, "The check found no token, so this test proves nothing."
    assert_no_secret(repr(answer), "the environment token check")


def test_the_environment_reference_names_the_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """The environment token reference names the variable and never its value.

    Why:
        FR-009 asks the portal to refer to a stored credential by its variable
        name. An operator who must fix a missing token needs the name, and the
        name alone is enough to fix it.

    Args:
        monkeypatch: The environment patcher, which restores the variable after.
    """
    monkeypatch.setenv(TOKEN_VARIABLE, PROBE_TOKEN)
    reference = identity.environment_token_reference()
    assert reference == TOKEN_VARIABLE, f"The reference named {reference} instead of the variable."
    assert_no_secret(reference, "the environment token reference")


# ---------------------------------------------------------------------------
# The redaction guard
# ---------------------------------------------------------------------------


def test_the_guard_replaces_a_password_with_its_field_name() -> None:
    """The guard replaces a password with the name of its own field."""
    guarded = identity.redact_credentials({"password": PROBE_PASSWORD})
    assert guarded == {"password": "<password>"}


def test_the_guard_keeps_a_field_that_is_no_credential() -> None:
    """The guard leaves a field that carries no credential untouched.

    Why:
        A guard that hid every field would make the redacted body useless for
        reading a fault. Only the credential fields change.
    """
    guarded = identity.redact_credentials({"org_id": "alpha", "password": PROBE_PASSWORD})
    assert guarded["org_id"] == "alpha"


def test_the_guard_reaches_a_nested_body() -> None:
    """The guard reaches a credential inside a nested body.

    Why:
        A cloud answer nests its fields. A guard that read the top level alone
        would pass a nested password straight through.
    """
    guarded = identity.redact_credentials({"outer": {"token": PROBE_TOKEN}})
    assert guarded == {"outer": {"token": "<token>"}}


def test_the_guard_leaves_the_original_body_unchanged() -> None:
    """The guard copies the body and never edits the one it was given.

    Why:
        A caller often redacts a body for a log line and then keeps using the
        real body. A guard that edited in place would break the caller.
    """
    body = {"password": PROBE_PASSWORD}
    identity.redact_credentials(body)
    assert body["password"] == PROBE_PASSWORD


@pytest.mark.parametrize("field_name", GUARDED_FIELD_NAMES)
def test_the_guard_recognizes_every_documented_field_name(field_name: str) -> None:
    """The guard recognizes each documented credential field name.

    Args:
        field_name: One credential field name of the documented list.
    """
    assert identity.is_credential_field(field_name) is True, f"The guard missed the field {field_name}."


@pytest.mark.parametrize("written", ["PASSWORD", "Password", "Api-Token", "API-KEY"])
def test_the_guard_recognizes_a_field_whatever_its_written_form(written: str) -> None:
    """The guard recognizes a credential field in upper case and in dash form.

    Why:
        A header arrives in dash form and in mixed case. A guard that matched
        the lower-case form alone would pass a header straight through.

    Args:
        written: One written form of a credential field name.
    """
    assert identity.is_credential_field(written) is True, f"The guard missed the written form {written}."


def test_the_guard_admits_a_field_that_names_no_credential() -> None:
    """The guard admits a field whose name states no credential.

    Why:
        A guard that matched too widely would hide the very fields that a
        reader needs to place a fault.
    """
    assert identity.is_credential_field("org_id") is False


def test_the_credential_reference_names_the_variable_alone() -> None:
    """The credential reference names the variable and holds no value.

    Why:
        The brackets mark the answer as a name. Without them a reader could
        mistake the answer for the value that the variable holds.
    """
    assert identity.credential_reference("MIST_APITOKEN") == "<MIST_APITOKEN>"


def test_a_caller_may_name_its_own_field_set() -> None:
    """A caller may pass its own field set, so one shared name stays readable.

    Why:
        The second factor body names its field `code`, and the error envelope
        names its field `code` as well. The wide set therefore hides the refusal
        code of an envelope. A caller that redacts an envelope passes a set of
        its own, and this test pins that escape.
    """
    envelope = {"code": "org_not_permitted", "message": "This session may not act on that organization."}
    guarded = identity.redact_credentials(envelope, frozenset({"password"}))
    assert guarded["code"] == "org_not_permitted"


def test_the_wide_set_still_guards_the_second_factor_field() -> None:
    """The default field set still hides the second factor code.

    Why:
        The escape above must not weaken the rule. A request body that names
        `code` carries the second factor, so the default set hides it.
    """
    assert identity.redact_credentials({"code": PROBE_CODE}) == {"code": "<code>"}
