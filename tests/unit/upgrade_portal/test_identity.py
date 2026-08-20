"""Unit tests for the identity services of the upgrade capture portal.

Why:
    The module under test holds the one rule that protects personal data in
    this feature. A work email address is personal data, so no log record and
    no traceback may hold one. Every log call passes a 16 character BLAKE2s
    digest instead, and both record classes replace the generated text form.
    A later edit could reintroduce the raw address in one line, and no other
    gate would catch it. These tests fail when that happens.

    The tests also hold the multi-tab rule of FR-073 and FR-074. One address
    plus one browser identifier is one owner. Two browsers of one person are
    two owners, so one person can drive two sites at the same time.

    No test opens a socket, a database connection, or a file. No test reads
    the ``.env`` file. Every credential value below is an obviously fake
    string.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import FrozenInstanceError
from http.cookies import Morsel, SimpleCookie
from types import SimpleNamespace

import flask
import pytest

from src.upgrade_portal.runtime import identity
from src.upgrade_portal.runtime.identity import (
    BROWSER_ID_BYTES,
    BROWSER_ID_COOKIE,
    BROWSER_ID_MAX_AGE_SECONDS,
    ENVIRONMENT_TOKEN_VARIABLES,
    ERROR_NOT_AUTHENTICATED,
    SESSION_OWNER_KEY,
    SESSION_REGISTRY,
    CredentialMode,
    CredentialUnavailableError,
    OperatorSession,
    SessionOwner,
    SessionRegistry,
    attach_browser_id,
    build_owner,
    current_owner,
    current_session,
    email_digest,
    ensure_browser_id,
    environment_token_present,
    issue_browser_id,
    normalize_email,
    not_authenticated_response,
    read_browser_id,
    require_session,
    sign_in,
    sign_in_with_environment_token,
    sign_out,
)

# WHY: The module logger takes its name from ``__name__``. A test raises the
# level of this exact logger, so caplog receives the DEBUG records too.
MODULE_LOGGER_NAME = "src.upgrade_portal.runtime.identity"

# WHY: Mixed case and a reserved example domain. The case proves the folding.
OPERATOR_EMAIL = "Jane.Operator@Example.COM"

# WHY: The one spelling that every later comparison must use.
NORMALIZED_EMAIL = "jane.operator@example.com"

# WHY: A leak test searches for this fragment alone. A partial address in a log
# record is still personal data, so the fragment is a stricter needle than the
# whole address.
EMAIL_LOCAL_PART = "jane.operator"

# WHY: A second person, so a test proves that two addresses give two digests.
SECOND_EMAIL = "sam.operator@example.com"

# WHY: Two browsers of one person. Both match the accepted URL-safe shape.
FIRST_BROWSER_ID = "first-browser-Ab12_cd34-Ef56"
SECOND_BROWSER_ID = "second-browser-Gh78_ij90-Kl12"

# WHY: An obviously fake value. FR-009 forbids a real token inside the suite.
FAKE_ENVIRONMENT_TOKEN = "fake-environment-token-for-tests-only"

# WHY: An obviously fake signing key. Flask refuses a session write without one.
FAKE_SECRET_KEY = "fake-flask-secret-key-for-tests-only"

# WHY: The shortest and the longest value the cookie pattern accepts. The two
# boundary values guard the 16 to 128 range against an off-by-one edit.
SHORTEST_BROWSER_ID = "a" * 16
LONGEST_BROWSER_ID = "b" * 128

# WHY: Values the cookie pattern must refuse. Each one is legal inside a Cookie
# header, so the browser can really send it and the module must reject it.
MALFORMED_BROWSER_IDS = (
    "",  # An empty cookie value
    "short",  # Below the 16 character floor
    "a" * 15,  # One character below the floor
    "c" * 129,  # One character above the 128 ceiling
    "has+plus+characters+here",  # A plus sign is not URL-safe here
    "has/slash/characters/here",  # A slash is not URL-safe here
    "has.dot.characters.here",  # A dot is not URL-safe here
)


def build_test_app() -> flask.Flask:
    """Build a bare Flask application for one test.

    Why:
        The module reads the request, the cookies, and the signed browser
        session. A test needs a request context for all three. Flask refuses a
        session write without a signing key, so this helper sets a fake key.
        The helper builds no route and imports no application factory, so no
        test reaches Redis or ArangoDB.

    Returns:
        An application with a fake signing key.
    """
    app = flask.Flask("upgrade_portal_identity_test")  # A fixed name, so no test depends on a file path
    app.secret_key = FAKE_SECRET_KEY  # Flask blocks a session write without a key
    return app


def cookie_header(browser_id: str) -> dict[str, str]:
    """Build the request header that carries the browser identifier.

    Args:
        browser_id: The cookie value the browser sends back.

    Returns:
        A header mapping for ``test_request_context``.
    """
    return {"Cookie": f"{BROWSER_ID_COOKIE}={browser_id}"}  # The one cookie the module reads


def read_browser_cookie(response: flask.Response) -> Morsel[str]:
    """Parse the ``browser_id`` cookie out of a response.

    Why:
        A test must read the flags of the cookie and not a substring of the
        header. The standard library parser reports each attribute by name, so
        an assertion cannot pass on an accidental match inside the value.

    Args:
        response: The response that carries the cookie.

    Returns:
        The parsed cookie.
    """
    header = response.headers.get("Set-Cookie")  # One cookie, so one header line
    assert header is not None, "The response carries no Set-Cookie header."
    jar = SimpleCookie()  # The standard library parser reports each flag by name
    jar.load(header)
    return jar[BROWSER_ID_COOKIE]


def log_haystack(caplog: pytest.LogCaptureFixture) -> str:
    """Join every part of every captured log record into one text.

    Why:
        A leak can hide in three places. It can sit in the format string, in
        the arguments, or in the formatted line. This helper joins all three,
        so one assertion covers every path a raw address could take.

    Args:
        caplog: The pytest log capture fixture.

    Returns:
        One lower-case text that holds every captured record.
    """
    parts: list[str] = [caplog.text]  # The formatted output of every record
    for record in caplog.records:
        parts.append(record.getMessage())  # The message after argument substitution
        parts.append(repr(record.args))  # The raw arguments, in case a format never ran
        parts.append(str(record.msg))  # The format string itself
    return "\n".join(parts).casefold()  # One case, so a mixed-case leak cannot hide


def assert_address_absent(caplog: pytest.LogCaptureFixture, address: str) -> None:
    """Assert that no captured log record holds a work email address.

    Why:
        This is the one security property of the module under test. The check
        looks for the whole address and for the local part alone, because a
        partial address is still personal data.

    Args:
        caplog: The pytest log capture fixture.
        address: The address that must appear nowhere.

    Raises:
        AssertionError: If any record holds the address or its local part.
    """
    haystack = log_haystack(caplog)
    assert address.casefold() not in haystack, "A log record holds the work email address."
    local_part = address.split("@", 1)[0].casefold()  # The name half is personal data on its own
    assert local_part not in haystack, "A log record holds part of the work email address."


@pytest.fixture(autouse=True)
def fresh_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give each test a registry of its own.

    Why:
        ``SESSION_REGISTRY`` is one store for the whole process. Without this
        fixture, a record from an earlier test would still answer a later
        lookup, and an owner count assertion would drift with the test order.
        The patch replaces the module attribute, and every function in the
        module reads that attribute at call time.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setattr(identity, "SESSION_REGISTRY", SessionRegistry())  # An empty store for one test


@pytest.fixture
def flask_app() -> flask.Flask:
    """Return a bare Flask application for one test.

    Returns:
        An application with a fake signing key.
    """
    return build_test_app()


@pytest.fixture
def no_environment_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove every cloud token variable from the process environment.

    Why:
        The computer that runs the suite may already hold a real token. A test
        of the absent path must not depend on that. The fixture removes the
        names and never reads a value.

    Args:
        monkeypatch: The pytest patch helper.
    """
    for name in ENVIRONMENT_TOKEN_VARIABLES:
        monkeypatch.delenv(name, raising=False)  # Absent is the expected state for these tests


@pytest.fixture
def fake_environment_token(monkeypatch: pytest.MonkeyPatch) -> str:
    """Set one obviously fake cloud token variable.

    Why:
        The environment token mode reports availability from the presence of a
        variable. A test needs that presence without a real credential.

    Args:
        monkeypatch: The pytest patch helper.

    Returns:
        The fake token value the fixture set.
    """
    for name in ENVIRONMENT_TOKEN_VARIABLES:
        monkeypatch.delenv(name, raising=False)  # Start from a known empty state
    monkeypatch.setenv(ENVIRONMENT_TOKEN_VARIABLES[0], FAKE_ENVIRONMENT_TOKEN)  # One name holds a fake value
    return FAKE_ENVIRONMENT_TOKEN


# --------------------------------------------------------------------------
# normalize_email
# --------------------------------------------------------------------------


def test_normalize_email_folds_the_case() -> None:
    """Prove that the normalizer lowers every letter of an address.

    Why:
        The site lock compares two identities as text. Two spellings of one
        address would look like two operators and would block the second tab.
    """
    assert normalize_email(OPERATOR_EMAIL) == NORMALIZED_EMAIL


def test_normalize_email_trims_surrounding_whitespace() -> None:
    """Prove that the normalizer removes whitespace around an address.

    Why:
        An operator who pastes an address often carries a leading space or a
        trailing newline. The lock must treat that value as the same person.
    """
    assert normalize_email(f" \t{OPERATOR_EMAIL}\n ") == NORMALIZED_EMAIL


def test_normalize_email_is_idempotent() -> None:
    """Prove that a second pass over a normalized address changes nothing.

    Why:
        Several call sites normalize an address. A second pass must not shift
        the value, because the site lock stores the result as a key.
    """
    once = normalize_email(OPERATOR_EMAIL)
    assert normalize_email(once) == once


def test_two_spellings_of_one_address_give_one_digest() -> None:
    """Prove that case and whitespace never split one person into two.

    Why:
        FR-074 lets one person hold two site locks. A digest that changed with
        the spelling would break that rule and would block the second tab.
    """
    padded_upper = f"  {OPERATOR_EMAIL}  "
    assert email_digest(padded_upper) == email_digest(NORMALIZED_EMAIL)
    assert email_digest(normalize_email(padded_upper)) == email_digest(NORMALIZED_EMAIL)


@pytest.mark.parametrize(
    "raw_email",
    [
        "",  # An empty value
        "   ",  # Whitespace alone, which strips to empty
        "\t\n",  # Other whitespace, which also strips to empty
    ],
)
def test_normalize_email_refuses_an_empty_value(raw_email: str) -> None:
    """Prove that an empty address never reaches a lock record.

    Args:
        raw_email: The empty or whitespace value under test.
    """
    with pytest.raises(ValueError, match="empty or too long"):
        normalize_email(raw_email)


def test_normalize_email_refuses_an_oversize_value() -> None:
    """Prove that an address above the mail server limit fails.

    Why:
        The address becomes part of a lock record and part of a registry key.
        An unbounded value would let one request grow both stores.
    """
    oversize = f"{'a' * 245}@example.com"  # 257 characters, above the 254 limit
    assert len(oversize) > 254
    with pytest.raises(ValueError, match="empty or too long"):
        normalize_email(oversize)


@pytest.mark.parametrize(
    "raw_email",
    [
        "operator-without-any-domain",  # No at sign at all
        "operator@localhost",  # A domain with no dot
        "operator@@example.com",  # Two at signs
        "jane doe@example.com",  # An inner space
        "@example.com",  # No name half
        "operator@",  # No domain half
    ],
)
def test_normalize_email_refuses_a_value_with_no_domain_part(raw_email: str) -> None:
    """Prove that a value that cannot name a work mailbox fails.

    Args:
        raw_email: The malformed address under test.
    """
    with pytest.raises(ValueError):
        normalize_email(raw_email)


def test_normalize_email_error_message_holds_no_part_of_the_address() -> None:
    """Prove that a rejection message never publishes personal data.

    Why:
        An error message often reaches a log record and reaches the operator
        page. A message that echoed the input would leak the address through
        the failure path instead of the success path.
    """
    with pytest.raises(ValueError) as no_domain:
        normalize_email(OPERATOR_EMAIL.replace("@Example.COM", ""))
    assert EMAIL_LOCAL_PART not in str(no_domain.value).casefold()

    with pytest.raises(ValueError) as oversize:
        normalize_email(f"{EMAIL_LOCAL_PART}{'a' * 250}@example.com")
    assert EMAIL_LOCAL_PART not in str(oversize.value).casefold()


# --------------------------------------------------------------------------
# email_digest
# --------------------------------------------------------------------------


def test_email_digest_is_16_characters() -> None:
    """Prove the digest length that every log record and every key expects.

    Why:
        The registry key joins the digest and the browser identifier. A longer
        digest would change every stored key and would strand every session.
    """
    assert len(email_digest(NORMALIZED_EMAIL)) == 16


def test_email_digest_is_lower_case_hexadecimal() -> None:
    """Prove that the digest holds hexadecimal characters alone.

    Why:
        The digest travels inside a registry key and inside a log record. A
        colon inside the digest would split the key at the wrong place.
    """
    digest = email_digest(NORMALIZED_EMAIL)
    assert all(character in "0123456789abcdef" for character in digest)


def test_email_digest_is_stable_across_calls() -> None:
    """Prove that two calls with one address give one digest.

    Why:
        An operator joins the records of one person by the digest. A digest
        with a random salt would break every historical record.
    """
    first = email_digest(NORMALIZED_EMAIL)
    second = email_digest(NORMALIZED_EMAIL)
    assert first == second


def test_email_digest_differs_for_two_addresses() -> None:
    """Prove that two people never share one digest.

    Why:
        The registry key holds the digest. A shared digest would let one
        operator read the cloud session of another operator.
    """
    assert email_digest(NORMALIZED_EMAIL) != email_digest(SECOND_EMAIL)


def test_email_digest_holds_no_part_of_the_address() -> None:
    """Prove that the digest publishes no fragment of the address.

    Why:
        The digest replaces the address in every log record. A digest that
        carried the name half would defeat the whole design.
    """
    digest = email_digest(NORMALIZED_EMAIL)
    assert EMAIL_LOCAL_PART not in digest
    assert "example.com" not in digest


# --------------------------------------------------------------------------
# environment_token_present
# --------------------------------------------------------------------------


@pytest.mark.parametrize("variable_name", ENVIRONMENT_TOKEN_VARIABLES)
def test_environment_token_present_accepts_each_variable_name(
    variable_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove that either supported variable name reports availability.

    Why:
        The project uses two spellings of the token variable. The sign-in page
        must offer the environment mode for both spellings.

    Args:
        variable_name: One supported variable name.
        monkeypatch: The pytest patch helper.
    """
    for name in ENVIRONMENT_TOKEN_VARIABLES:
        monkeypatch.delenv(name, raising=False)  # Start from a known empty state
    monkeypatch.setenv(variable_name, FAKE_ENVIRONMENT_TOKEN)
    assert environment_token_present() is True


@pytest.mark.usefixtures("no_environment_token")
def test_environment_token_present_reports_false_when_no_variable_is_set() -> None:
    """Prove that an empty environment reports no token.

    Why:
        The sign-in page must hide the environment mode when the process holds
        no token. A wrong answer would send the operator into a failed sign-in.
    """
    assert environment_token_present() is False


@pytest.mark.parametrize("blank_value", ["", "   ", "\t\n"])
def test_environment_token_present_ignores_a_blank_value(
    blank_value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove that a variable set to whitespace reports no token.

    Why:
        A shell script that exports an empty variable is common. That state
        cannot start a cloud session, so the portal must call it absent.

    Args:
        blank_value: The blank value under test.
        monkeypatch: The pytest patch helper.
    """
    for name in ENVIRONMENT_TOKEN_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(ENVIRONMENT_TOKEN_VARIABLES[0], blank_value)
    assert environment_token_present() is False


def test_environment_token_present_returns_a_plain_bool_and_no_token_value(
    fake_environment_token: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Prove that the presence check never returns or logs a token value.

    Why:
        FR-009 forbids the portal from holding a credential value. This
        function must answer a yes or no question. A return of the token text,
        or a truthy string, would carry the credential into the caller.

    Args:
        fake_environment_token: The fake token the fixture set.
        caplog: The pytest log capture fixture.
    """
    caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)
    answer = environment_token_present()
    assert answer is True  # The exact singleton, so no truthy token text passes
    assert type(answer) is bool  # A str subclass would also be truthy
    assert fake_environment_token not in repr(answer)
    assert fake_environment_token.casefold() not in log_haystack(caplog)


def test_environment_token_variables_name_both_spellings() -> None:
    """Prove that the module names both supported variable spellings.

    Why:
        The refusal message names these variables to the operator. A rename
        would leave the operator with instructions that do not work.
    """
    assert ENVIRONMENT_TOKEN_VARIABLES == ("MIST_APITOKEN", "MIST_API_TOKEN")


# --------------------------------------------------------------------------
# SessionOwner and OperatorSession text forms
# --------------------------------------------------------------------------


def owner_for_tests(browser_id: str = FIRST_BROWSER_ID) -> SessionOwner:
    """Build one identity pair without a request context.

    Args:
        browser_id: The browser half of the pair.

    Returns:
        The identity pair for the shared test address.
    """
    return SessionOwner(actor_email=NORMALIZED_EMAIL, browser_id=browser_id)


def test_session_owner_key_joins_the_digest_and_the_browser_id() -> None:
    """Prove the registry key shape that every lookup depends on.

    Why:
        The signed browser session carries this key, and the sign-out log
        splits it at the colon. A different shape would leak the browser half
        into a log record.
    """
    owner = owner_for_tests()
    assert owner.key == f"{email_digest(NORMALIZED_EMAIL)}:{FIRST_BROWSER_ID}"
    assert owner.key.split(":", 1)[0] == owner.email_digest


def test_session_owner_key_holds_no_part_of_the_address() -> None:
    """Prove that the browser never carries personal data.

    Why:
        The operator can read the signed session cookie of the browser. The
        signature stops an edit, but it does not hide the content.
    """
    assert EMAIL_LOCAL_PART not in owner_for_tests().key.casefold()


def test_session_owner_repr_shows_the_digest_and_no_address() -> None:
    """Prove that a traceback of the owner record holds no personal data.

    Why:
        A crash prints every local value. The generated dataclass text form
        would print the address, so the class replaces it.
    """
    owner = owner_for_tests()
    text = repr(owner)
    assert owner.email_digest in text
    assert EMAIL_LOCAL_PART not in text.casefold()
    assert NORMALIZED_EMAIL not in text


def test_session_owner_str_shows_the_digest_and_no_address() -> None:
    """Prove that the plain text form of the owner holds no personal data.

    Why:
        Many log calls pass a record through ``%s``, which asks for ``str``.
        A class that replaced only ``__repr__`` would still leak through this
        path if it also defined a separate ``__str__``.
    """
    owner = owner_for_tests()
    text = str(owner)
    assert owner.email_digest in text
    assert EMAIL_LOCAL_PART not in text.casefold()


def test_session_owner_f_string_shows_the_digest_and_no_address() -> None:
    """Prove that string interpolation of the owner holds no personal data.

    Why:
        An f-string calls ``__format__``, which is a third path into the text
        form. A developer reaches for this path most often.
    """
    owner = owner_for_tests()
    text = f"{owner}"
    assert owner.email_digest in text
    assert EMAIL_LOCAL_PART not in text.casefold()


def test_session_owner_is_frozen(fake_mist_session: SimpleNamespace) -> None:
    """Prove that a stored owner cannot change while the site lock holds it.

    Why:
        The site lock grants a site to one owner. An edit of the address after
        the grant would move the lock to a different person.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    owner = owner_for_tests()
    assert fake_mist_session is not None  # The fixture proves the offline setup ran
    with pytest.raises(FrozenInstanceError):
        owner.actor_email = SECOND_EMAIL  # type: ignore[misc]


def operator_session_for_tests(fake_mist_session: SimpleNamespace) -> OperatorSession:
    """Build one operator record without a request context.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.

    Returns:
        The record for the shared test address.
    """
    return OperatorSession(
        owner=owner_for_tests(),
        cloud_session=fake_mist_session,
        credential_mode=CredentialMode.ENVIRONMENT_TOKEN,
    )


def test_operator_session_repr_shows_the_digest_and_no_address(
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a traceback of the operator record holds no personal data.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    record = operator_session_for_tests(fake_mist_session)
    text = repr(record)
    assert record.owner.email_digest in text
    assert EMAIL_LOCAL_PART not in text.casefold()
    assert NORMALIZED_EMAIL not in text


def test_operator_session_str_and_f_string_hold_no_address(
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that both other text paths of the record hold no personal data.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    record = operator_session_for_tests(fake_mist_session)
    for text in (str(record), f"{record}"):
        assert record.owner.email_digest in text
        assert EMAIL_LOCAL_PART not in text.casefold()


def test_operator_session_repr_holds_no_credential_value(
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that the record text form never prints the cloud token.

    Why:
        The record holds the cloud session by reference, and that object holds
        a token attribute. The generated dataclass text form would print the
        whole object, so the class replaces it.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    record = operator_session_for_tests(fake_mist_session)
    text = repr(record)
    assert fake_mist_session.apitoken not in text
    assert fake_mist_session.email not in text
    assert CredentialMode.ENVIRONMENT_TOKEN.value in text  # The mode alone is safe to print


def test_operator_session_records_the_credential_mode_and_a_utc_time(
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that the record stamps the sign-in in one time zone.

    Why:
        Two operators in two time zones compare their records. A naive time
        would make that comparison guess the zone.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    record = operator_session_for_tests(fake_mist_session)
    assert record.credential_mode is CredentialMode.ENVIRONMENT_TOKEN
    assert record.created_at.tzinfo is not None
    assert record.created_at.utcoffset() is not None


def test_credential_mode_holds_both_modes() -> None:
    """Prove that the enumeration already names the second credential mode.

    Why:
        User Story 5 adds the managed service provider login. The enumeration
        carries that mode now, so the later story adds a route alone.
    """
    assert CredentialMode.ENVIRONMENT_TOKEN.value == "environment_token"
    assert CredentialMode.PROVIDER_LOGIN.value == "provider_login"


# --------------------------------------------------------------------------
# SessionRegistry
# --------------------------------------------------------------------------


def test_module_registry_is_a_session_registry() -> None:
    """Prove that the module publishes one process wide store.

    Why:
        Every function in the module reads this attribute. A test that patched
        a different name would prove nothing.
    """
    assert isinstance(identity.SESSION_REGISTRY, SessionRegistry)
    assert isinstance(SESSION_REGISTRY, SessionRegistry)


def test_registry_starts_empty() -> None:
    """Prove that a new registry holds no owner."""
    assert SessionRegistry().owner_count() == 0


def test_registry_registers_and_returns_a_record(fake_mist_session: SimpleNamespace) -> None:
    """Prove the store and read path of one owner.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    registry = SessionRegistry()
    record = operator_session_for_tests(fake_mist_session)
    registry.register(record)
    assert registry.get(record.owner.key) is record
    assert registry.owner_count() == 1


def test_registry_returns_none_for_an_unknown_key() -> None:
    """Prove that a miss answers None and raises nothing.

    Why:
        A worker restart empties the store while a browser still holds the
        key. The guard must answer the refusal envelope, not a server error.
    """
    assert SessionRegistry().get("0123456789abcdef:no-such-browser-id") is None


def test_registry_drop_removes_a_record_and_reports_true(
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a sign-out removes the cloud session reference.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    registry = SessionRegistry()
    record = operator_session_for_tests(fake_mist_session)
    registry.register(record)
    assert registry.drop(record.owner.key) is True
    assert registry.get(record.owner.key) is None
    assert registry.owner_count() == 0


def test_registry_drop_reports_false_for_an_unknown_key() -> None:
    """Prove that a second sign-out reports no removal.

    Why:
        Two sign-out calls must not both report success. An audit record that
        counted two removals would misstate the history.
    """
    assert SessionRegistry().drop("0123456789abcdef:no-such-browser-id") is False


def test_registry_replaces_the_record_of_one_owner(
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a repeat sign-in leaves one record for one owner.

    Why:
        Two cloud sessions for one browser would leak the first object for the
        life of the worker.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    registry = SessionRegistry()
    first = operator_session_for_tests(fake_mist_session)
    second = operator_session_for_tests(fake_mist_session)
    registry.register(first)
    registry.register(second)
    assert registry.owner_count() == 1
    assert registry.get(first.owner.key) is second


def test_two_browsers_of_one_email_are_two_sessions(
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove the multi-tab rule of FR-073 and FR-074.

    Why:
        One person on two computers is two owners, so that person can hold two
        site locks at the same time. A registry keyed by the address alone
        would overwrite the first record and would strand the first computer.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    first_owner = SessionOwner(actor_email=NORMALIZED_EMAIL, browser_id=FIRST_BROWSER_ID)
    second_owner = SessionOwner(actor_email=NORMALIZED_EMAIL, browser_id=SECOND_BROWSER_ID)
    assert first_owner.email_digest == second_owner.email_digest  # One person
    assert first_owner.key != second_owner.key  # Two identities

    registry = SessionRegistry()
    registry.register(
        OperatorSession(
            owner=first_owner,
            cloud_session=fake_mist_session,
            credential_mode=CredentialMode.ENVIRONMENT_TOKEN,
        )
    )
    registry.register(
        OperatorSession(
            owner=second_owner,
            cloud_session=fake_mist_session,
            credential_mode=CredentialMode.ENVIRONMENT_TOKEN,
        )
    )
    assert registry.owner_count() == 2
    first_record = registry.get(first_owner.key)
    second_record = registry.get(second_owner.key)
    assert first_record is not None
    assert second_record is not None
    assert first_record is not second_record


def test_dropping_one_browser_keeps_the_other_browser(
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a sign-out on one computer leaves the other computer alone.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    registry = SessionRegistry()
    first_owner = SessionOwner(actor_email=NORMALIZED_EMAIL, browser_id=FIRST_BROWSER_ID)
    second_owner = SessionOwner(actor_email=NORMALIZED_EMAIL, browser_id=SECOND_BROWSER_ID)
    for owner in (first_owner, second_owner):
        registry.register(
            OperatorSession(
                owner=owner,
                cloud_session=fake_mist_session,
                credential_mode=CredentialMode.ENVIRONMENT_TOKEN,
            )
        )
    assert registry.drop(first_owner.key) is True
    assert registry.get(second_owner.key) is not None
    assert registry.owner_count() == 1


def test_registry_keeps_every_record_under_concurrent_writes(
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that the lock protects the store from a lost write.

    Why:
        The portal runs a threaded worker, so several request threads register
        at the same moment. A store without a lock can lose a record.

    Args:
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    registry = SessionRegistry()
    writer_count = 8
    start = threading.Barrier(writer_count)  # Every thread writes at one moment

    def register_one(index: int) -> None:
        """Register one owner after every thread reaches the barrier.

        Args:
            index: The number of this writer thread.
        """
        start.wait()
        owner = SessionOwner(actor_email=NORMALIZED_EMAIL, browser_id=f"browser-{index:012d}-abc")
        registry.register(
            OperatorSession(
                owner=owner,
                cloud_session=fake_mist_session,
                credential_mode=CredentialMode.ENVIRONMENT_TOKEN,
            )
        )

    threads = [threading.Thread(target=register_one, args=(index,)) for index in range(writer_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert registry.owner_count() == writer_count


# --------------------------------------------------------------------------
# issue_browser_id
# --------------------------------------------------------------------------


def test_issue_browser_id_returns_a_url_safe_value_of_43_characters() -> None:
    """Prove the length and the alphabet of a fresh browser identifier.

    Why:
        The value travels in a cookie and reaches a Redis lock key. A value
        with a colon or a slash would break the key or the header.
    """
    value = issue_browser_id()
    assert len(value) == 43  # 32 random bytes give 43 URL-safe characters
    assert BROWSER_ID_BYTES == 32
    assert all(character.isalnum() or character in "-_" for character in value)


def test_issue_browser_id_returns_a_different_value_each_call() -> None:
    """Prove that the identifier is unpredictable.

    Why:
        A derived or repeated value would make two computers look like one
        browser, and the site lock would grant one site to two operators.
    """
    values = {issue_browser_id() for _ in range(20)}
    assert len(values) == 20


def test_a_fresh_identifier_passes_the_cookie_check(flask_app: flask.Flask) -> None:
    """Prove that the writer and the reader agree on one shape.

    Why:
        A reader that refused the value the writer produced would issue a new
        cookie on every request, and the site lock would never hold.

    Args:
        flask_app: The bare test application.
    """
    fresh = issue_browser_id()
    with flask_app.test_request_context("/", headers=cookie_header(fresh)):
        assert read_browser_id() == fresh


# --------------------------------------------------------------------------
# read_browser_id
# --------------------------------------------------------------------------


def test_read_browser_id_returns_the_cookie_value(flask_app: flask.Flask) -> None:
    """Prove the plain read path of the first-party cookie.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        assert read_browser_id() == FIRST_BROWSER_ID


def test_read_browser_id_returns_none_when_the_cookie_is_absent(flask_app: flask.Flask) -> None:
    """Prove that a first visit reports no identifier.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/"):
        assert read_browser_id() is None


@pytest.mark.parametrize("bad_value", MALFORMED_BROWSER_IDS)
def test_read_browser_id_refuses_a_malformed_cookie_value(
    bad_value: str,
    flask_app: flask.Flask,
) -> None:
    """Prove that a hostile cookie value never reaches a lock key.

    Why:
        The operator controls the cookie. A value with a slash or an unbounded
        length would reach a Redis key and could collide with another key.

    Args:
        bad_value: The malformed cookie value under test.
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/", headers=cookie_header(bad_value)):
        assert read_browser_id() is None


@pytest.mark.parametrize("good_value", [SHORTEST_BROWSER_ID, LONGEST_BROWSER_ID])
def test_read_browser_id_accepts_both_length_boundaries(
    good_value: str,
    flask_app: flask.Flask,
) -> None:
    """Prove that the accepted length range holds both of its ends.

    Why:
        An off-by-one edit of the pattern would refuse a value the writer
        already gave to a browser, and that browser would lose its identity.

    Args:
        good_value: The boundary value under test.
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/", headers=cookie_header(good_value)):
        assert read_browser_id() == good_value


# --------------------------------------------------------------------------
# attach_browser_id
# --------------------------------------------------------------------------


def test_attach_browser_id_writes_the_first_party_cookie(flask_app: flask.Flask) -> None:
    """Prove every attribute of the cookie the portal writes.

    Why:
        ``HttpOnly`` keeps page script away from the value. ``SameSite=Lax``
        stops another site from driving a state change. A stored maximum age
        lets two windows share one identity.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/"):
        response = flask.Response()
        returned = attach_browser_id(response, FIRST_BROWSER_ID)
        assert returned is response  # The caller returns the same object
        cookie = read_browser_cookie(response)

    assert cookie.value == FIRST_BROWSER_ID
    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Lax"
    assert cookie["path"] == "/"
    assert cookie["max-age"] == str(BROWSER_ID_MAX_AGE_SECONDS)
    assert BROWSER_ID_MAX_AGE_SECONDS == 31_536_000  # 365 days


def test_attach_browser_id_sets_secure_under_https(flask_app: flask.Flask) -> None:
    """Prove that a TLS request keeps the cookie off plain HTTP.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("https://portal.example.com/"):
        assert flask.request.is_secure is True
        response = flask.Response()
        attach_browser_id(response, FIRST_BROWSER_ID)
        cookie = read_browser_cookie(response)

    assert cookie["secure"] is True


def test_attach_browser_id_omits_secure_under_http(flask_app: flask.Flask) -> None:
    """Prove that a plain HTTP run still receives a usable cookie.

    Why:
        The portal runs behind a plain HTTP port in a laboratory. A cookie
        marked ``Secure`` there would never return, and the operator would lose
        an identity on every request.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("http://portal.example.com/"):
        assert flask.request.is_secure is False
        response = flask.Response()
        attach_browser_id(response, FIRST_BROWSER_ID)
        cookie = read_browser_cookie(response)

    assert cookie["secure"] == ""  # The parser reports an absent flag as empty text


def test_attach_browser_id_writes_no_identifier_to_a_log_record(
    flask_app: flask.Flask,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Prove that the cookie writer logs no cookie value.

    Args:
        flask_app: The bare test application.
        caplog: The pytest log capture fixture.
    """
    caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)
    with flask_app.test_request_context("/"):
        attach_browser_id(flask.Response(), FIRST_BROWSER_ID)
    assert FIRST_BROWSER_ID.casefold() not in log_haystack(caplog)


# --------------------------------------------------------------------------
# ensure_browser_id
# --------------------------------------------------------------------------


def test_ensure_browser_id_keeps_an_existing_cookie_value(flask_app: flask.Flask) -> None:
    """Prove that a second window of one browser keeps one identity.

    Why:
        A rewrite would restart the maximum age on every request, and two
        windows could then hold two identifiers.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        response = flask.Response()
        assert ensure_browser_id(response) == FIRST_BROWSER_ID
        assert "Set-Cookie" not in response.headers  # No rewrite, so the age keeps its start


def test_ensure_browser_id_issues_a_value_when_the_cookie_is_absent(
    flask_app: flask.Flask,
) -> None:
    """Prove that a first visit receives an identity without a second trip.

    Why:
        FR-072 asks for an identity before the first write action. The caller
        uses the returned value at once, before the browser sends it back.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/"):
        response = flask.Response()
        issued = ensure_browser_id(response)
        cookie = read_browser_cookie(response)

    assert len(issued) == 43
    assert cookie.value == issued


@pytest.mark.parametrize("bad_value", MALFORMED_BROWSER_IDS)
def test_ensure_browser_id_replaces_a_malformed_cookie_value(
    bad_value: str,
    flask_app: flask.Flask,
) -> None:
    """Prove that a hostile cookie never survives into a lock key.

    Args:
        bad_value: The malformed cookie value under test.
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/", headers=cookie_header(bad_value)):
        response = flask.Response()
        issued = ensure_browser_id(response)
        cookie = read_browser_cookie(response)

    assert issued != bad_value
    assert cookie.value == issued
    assert len(issued) == 43


def test_ensure_browser_id_writes_no_identifier_to_a_log_record(
    flask_app: flask.Flask,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Prove that the debug record names the event and not the value.

    Why:
        A cookie value that reached a log record would let a reader of the log
        take over the identity of that browser.

    Args:
        flask_app: The bare test application.
        caplog: The pytest log capture fixture.
    """
    caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)
    with flask_app.test_request_context("/"):
        issued = ensure_browser_id(flask.Response())

    haystack = log_haystack(caplog)
    assert "issued a new browser identifier" in haystack  # The record ran, so the check is not vacuous
    assert issued.casefold() not in haystack


# --------------------------------------------------------------------------
# build_owner
# --------------------------------------------------------------------------


def test_build_owner_normalizes_the_address() -> None:
    """Prove that the builder applies one spelling before the pair exists.

    Why:
        Both halves need a check in one place. A route that skipped the check
        would place an unchecked value into a Redis lock key.
    """
    owner = build_owner(f"  {OPERATOR_EMAIL} ", FIRST_BROWSER_ID)
    assert owner.actor_email == NORMALIZED_EMAIL
    assert owner.browser_id == FIRST_BROWSER_ID


@pytest.mark.parametrize("bad_value", MALFORMED_BROWSER_IDS)
def test_build_owner_refuses_a_malformed_browser_id(bad_value: str) -> None:
    """Prove that the builder checks the cookie half.

    Args:
        bad_value: The malformed browser identifier under test.
    """
    with pytest.raises(ValueError, match="browser identifier"):
        build_owner(NORMALIZED_EMAIL, bad_value)


def test_build_owner_refuses_a_malformed_address() -> None:
    """Prove that the builder checks the address half."""
    with pytest.raises(ValueError):
        build_owner("operator-without-any-domain", FIRST_BROWSER_ID)


def test_build_owner_error_messages_hold_no_personal_data() -> None:
    """Prove that neither rejection publishes the input.

    Why:
        A route logs the failure of a sign-in. A message that echoed the
        address or the cookie would leak both through the failure path.
    """
    with pytest.raises(ValueError) as browser_error:
        build_owner(NORMALIZED_EMAIL, "short")
    assert "short" not in str(browser_error.value)

    with pytest.raises(ValueError) as address_error:
        build_owner(f"{EMAIL_LOCAL_PART}-no-domain", FIRST_BROWSER_ID)
    assert EMAIL_LOCAL_PART not in str(address_error.value).casefold()


# --------------------------------------------------------------------------
# sign_in and sign_in_with_environment_token
# --------------------------------------------------------------------------


def test_sign_in_registers_the_record_and_marks_the_browser_session(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a sign-in fills both halves of the session state.

    Why:
        The registry holds the cloud session, and the signed browser session
        holds the key. A request needs both halves to pass the guard.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        record = sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)
        assert flask.session[SESSION_OWNER_KEY] == owner.key
        assert identity.SESSION_REGISTRY.get(owner.key) is record

    assert record.cloud_session is fake_mist_session  # Held by reference, never copied
    assert record.credential_mode is CredentialMode.ENVIRONMENT_TOKEN


def test_sign_in_writes_the_browser_session_key_and_not_the_address(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that the browser never carries the address of its operator.

    Why:
        The operator can read the signed session cookie. The signature stops
        an edit, but it does not hide the content.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)
        stored = flask.session[SESSION_OWNER_KEY]

    assert isinstance(stored, str)
    assert EMAIL_LOCAL_PART not in stored.casefold()
    assert stored.startswith(email_digest(NORMALIZED_EMAIL))


def test_sign_in_writes_the_digest_and_no_address_to_the_log(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Prove the one security property of the sign-in path.

    Why:
        The sign-in path is the only place that holds the typed address. A
        single ``%s`` on the owner instead of the digest would publish the
        address to every log reader.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
        caplog: The pytest log capture fixture.
    """
    caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)

    haystack = log_haystack(caplog)
    assert owner.email_digest in haystack  # The records ran, so the check is not vacuous
    assert_address_absent(caplog, OPERATOR_EMAIL)
    assert fake_mist_session.apitoken not in haystack  # No credential value either


def test_sign_in_with_environment_token_registers_the_record(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
    fake_environment_token: str,
) -> None:
    """Prove the supported credential mode of this phase.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
        fake_environment_token: The fake token the fixture set.
    """
    assert fake_environment_token == FAKE_ENVIRONMENT_TOKEN
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        record = sign_in_with_environment_token(owner, fake_mist_session)
        assert identity.SESSION_REGISTRY.get(owner.key) is record

    assert record.credential_mode is CredentialMode.ENVIRONMENT_TOKEN


@pytest.mark.usefixtures("no_environment_token")
def test_sign_in_with_environment_token_refuses_an_empty_environment(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that the mode refuses to run without a token variable.

    Why:
        A registered record without a working cloud session would fail on the
        first cloud call, far from the cause. The named error lets the sign-in
        route answer with one plain sentence.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        with pytest.raises(CredentialUnavailableError) as error:
            sign_in_with_environment_token(owner, fake_mist_session)
        assert identity.SESSION_REGISTRY.owner_count() == 0  # No half-built record survives

    message = str(error.value)
    for name in ENVIRONMENT_TOKEN_VARIABLES:
        assert name in message  # The operator needs the variable names
    assert FAKE_ENVIRONMENT_TOKEN not in message  # And never a value


def test_credential_unavailable_error_is_a_runtime_error() -> None:
    """Prove that a route can catch this error apart from a value error.

    Why:
        A bad address raises ``ValueError`` and a missing token raises this
        error. The two need different answers on the sign-in page.
    """
    assert issubclass(CredentialUnavailableError, RuntimeError)
    assert not issubclass(CredentialUnavailableError, ValueError)


@pytest.mark.usefixtures("no_environment_token")
def test_sign_in_with_environment_token_refusal_writes_no_address_to_the_log(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Prove that the failure path also holds the address back.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
        caplog: The pytest log capture fixture.
    """
    caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        with pytest.raises(CredentialUnavailableError):
            sign_in_with_environment_token(owner, fake_mist_session)

    assert_address_absent(caplog, OPERATOR_EMAIL)


# --------------------------------------------------------------------------
# current_session and current_owner
# --------------------------------------------------------------------------


def test_current_session_returns_the_record_of_a_signed_in_request(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a matching session and cookie answer the record.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        record = sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)
        assert current_session() is record
        assert current_owner() == owner


def test_current_session_returns_none_without_a_browser_session(
    flask_app: flask.Flask,
) -> None:
    """Prove that a request with no signed session carries no record.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        assert current_session() is None
        assert current_owner() is None


def test_current_session_returns_none_after_a_worker_restart(
    flask_app: flask.Flask,
) -> None:
    """Prove that a stale key answers None instead of a server error.

    Why:
        A worker restart empties the registry while the browser still holds a
        valid signed session. The guard must refuse that request calmly.

    Args:
        flask_app: The bare test application.
    """
    stale_key = f"{email_digest(NORMALIZED_EMAIL)}:{FIRST_BROWSER_ID}"
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        flask.session[SESSION_OWNER_KEY] = stale_key  # The store holds no such record
        assert current_session() is None


def test_current_session_refuses_a_session_copied_to_another_browser(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a copied session fails on a second computer.

    Why:
        The signed session alone would let a stolen cookie drive an upgrade
        from any computer. The check binds the session to the browser half of
        the identity pair.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)

    with flask_app.test_request_context("/", headers=cookie_header(SECOND_BROWSER_ID)):
        flask.session[SESSION_OWNER_KEY] = owner.key  # The thief carries the signed session
        assert current_session() is None  # But not the browser cookie of the owner


def test_current_session_refuses_a_request_with_no_browser_cookie(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a cleared cookie ends the session of that browser.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)

    with flask_app.test_request_context("/"):
        flask.session[SESSION_OWNER_KEY] = owner.key
        assert current_session() is None


def test_current_session_refuses_a_damaged_session_field(flask_app: flask.Flask) -> None:
    """Prove that a session field of the wrong type answers None.

    Why:
        A later version of the portal could write a different shape into the
        signed session. The guard must refuse that request instead of raising.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        flask.session[SESSION_OWNER_KEY] = 12345  # Not the text the module writes
        assert current_session() is None
        assert current_owner() is None


def test_two_browsers_of_one_operator_hold_two_live_sessions(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove the multi-tab rule end to end through the request path.

    Why:
        FR-074 lets one person drive two sites at the same time. Each browser
        must read back its own record, not the record of the other browser.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    records = {}
    for browser_id in (FIRST_BROWSER_ID, SECOND_BROWSER_ID):
        with flask_app.test_request_context("/", headers=cookie_header(browser_id)):
            owner = build_owner(OPERATOR_EMAIL, browser_id)
            records[browser_id] = sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)

    assert identity.SESSION_REGISTRY.owner_count() == 2
    for browser_id in (FIRST_BROWSER_ID, SECOND_BROWSER_ID):
        with flask_app.test_request_context("/", headers=cookie_header(browser_id)):
            flask.session[SESSION_OWNER_KEY] = records[browser_id].owner.key
            assert current_session() is records[browser_id]


# --------------------------------------------------------------------------
# sign_out
# --------------------------------------------------------------------------


def test_sign_out_drops_the_record_and_clears_the_browser_session(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a sign-out removes both halves of the session state.

    Why:
        A cleared cookie alone would leave the cloud session object in memory
        for the life of the worker.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)
        assert sign_out() is True
        assert SESSION_OWNER_KEY not in flask.session
        assert identity.SESSION_REGISTRY.get(owner.key) is None
        assert current_session() is None


def test_sign_out_reports_false_without_a_session(flask_app: flask.Flask) -> None:
    """Prove that a request with no session has nothing to drop.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/"):
        assert sign_out() is False


def test_sign_out_reports_false_after_a_worker_restart(flask_app: flask.Flask) -> None:
    """Prove that a stale key reports no removal.

    Why:
        The return value tells the route whether a cloud session really left
        the process. A false report would misstate the audit history.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        flask.session[SESSION_OWNER_KEY] = f"{email_digest(NORMALIZED_EMAIL)}:{FIRST_BROWSER_ID}"
        assert sign_out() is False


def test_sign_out_leaves_the_session_of_a_second_browser(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a sign-out on one computer keeps the other computer signed in.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    owners = {}
    for browser_id in (FIRST_BROWSER_ID, SECOND_BROWSER_ID):
        with flask_app.test_request_context("/", headers=cookie_header(browser_id)):
            owners[browser_id] = build_owner(OPERATOR_EMAIL, browser_id)
            sign_in(owners[browser_id], fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)

    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        flask.session[SESSION_OWNER_KEY] = owners[FIRST_BROWSER_ID].key
        assert sign_out() is True

    assert identity.SESSION_REGISTRY.owner_count() == 1
    assert identity.SESSION_REGISTRY.get(owners[SECOND_BROWSER_ID].key) is not None


def test_sign_out_writes_the_digest_and_no_address_to_the_log(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Prove the security property of the sign-out path.

    Why:
        The sign-out log splits the registry key at the colon and keeps the
        digest half. An edit that logged the whole key would publish the
        browser identifier, and an edit that logged the owner would publish
        the address.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
        caplog: The pytest log capture fixture.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)
        caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)
        caplog.clear()  # Drop the sign-in records, so this check covers the sign-out alone
        sign_out()

    haystack = log_haystack(caplog)
    assert owner.email_digest in haystack  # The records ran, so the check is not vacuous
    assert_address_absent(caplog, OPERATOR_EMAIL)
    assert FIRST_BROWSER_ID.casefold() not in haystack  # The digest half alone


# --------------------------------------------------------------------------
# not_authenticated_response
# --------------------------------------------------------------------------


def test_not_authenticated_response_holds_the_fixed_code_and_status(
    flask_app: flask.Flask,
) -> None:
    """Prove the one error envelope that every guarded route answers with.

    Why:
        The contract fixes one shape for every JSON error. A test asserts on
        ``code`` and never on ``message``, because the message may change for
        Simplified Technical English at any time.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/"):
        response, status = not_authenticated_response()
        payload = response.get_json()

    assert status == 401
    assert ERROR_NOT_AUTHENTICATED == "not_authenticated"
    assert payload["error"]["code"] == ERROR_NOT_AUTHENTICATED
    assert isinstance(payload["error"]["message"], str)


def test_not_authenticated_response_holds_no_personal_data(
    flask_app: flask.Flask,
) -> None:
    """Prove that the refusal envelope names no operator.

    Why:
        The envelope reaches an unauthenticated caller. Any identity detail
        there would tell that caller who holds the portal.

    Args:
        flask_app: The bare test application.
    """
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        response, _ = not_authenticated_response()
        body = response.get_data(as_text=True)

    assert EMAIL_LOCAL_PART not in body.casefold()
    assert FIRST_BROWSER_ID not in body


# --------------------------------------------------------------------------
# require_session
# --------------------------------------------------------------------------


def sample_route() -> str:
    """Return a fixed body for the guard tests.

    Why:
        The guard tests need a route function with a known name, a known
        docstring, and a known return value.

    Returns:
        A fixed body.
    """
    return "the route ran"


def test_require_session_runs_the_route_with_a_session(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
) -> None:
    """Prove that a signed-in request reaches the route function.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
    """
    guarded = require_session(sample_route)
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)
        assert guarded() == "the route ran"


def test_require_session_refuses_a_request_with_no_session(flask_app: flask.Flask) -> None:
    """Prove that an unauthenticated request receives the fixed envelope.

    Why:
        The contract asks for a session on every endpoint except the sign-in
        pages. One decorator keeps that rule in one place.

    Args:
        flask_app: The bare test application.
    """
    calls: list[str] = []

    def counted_route() -> str:
        """Record one call and return a body.

        Returns:
            A fixed body.
        """
        calls.append("ran")
        return "the route ran"

    guarded = require_session(counted_route)
    with flask_app.test_request_context("/"):
        result = guarded()
        assert isinstance(result, tuple)
        response, status = result
        payload = response.get_json()

    assert status == 401
    assert payload["error"]["code"] == ERROR_NOT_AUTHENTICATED
    assert calls == []  # The route never saw the refused request


def test_require_session_keeps_the_name_and_the_docstring() -> None:
    """Prove that the guard preserves the identity of the route function.

    Why:
        Flask registers an endpoint under the name of the view function. A
        guard that lost the name would register every guarded route under one
        endpoint, and the second registration would fail.
    """
    guarded = require_session(sample_route)
    assert guarded.__name__ == "sample_route"
    assert guarded.__doc__ == sample_route.__doc__
    assert guarded.__module__ == sample_route.__module__


def test_require_session_registers_two_routes_under_two_endpoints(
    flask_app: flask.Flask,
) -> None:
    """Prove that Flask accepts two guarded routes in one application.

    Why:
        This is the failure that a lost function name really produces. A test
        on ``__name__`` alone could pass while the registration still broke.

    Args:
        flask_app: The bare test application.
    """

    def first_view() -> str:
        """Return the body of the first route.

        Returns:
            A fixed body.
        """
        return "first"

    def second_view() -> str:
        """Return the body of the second route.

        Returns:
            A fixed body.
        """
        return "second"

    flask_app.add_url_rule("/first", view_func=require_session(first_view))
    flask_app.add_url_rule("/second", view_func=require_session(second_view))
    assert "first_view" in flask_app.view_functions
    assert "second_view" in flask_app.view_functions


def test_require_session_refusal_writes_no_address_to_the_log(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Prove that the refusal record names the endpoint and no operator.

    Why:
        A refused request is the most common record in the log. A leak there
        would repeat on every scan of the portal.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
        caplog: The pytest log capture fixture.
    """
    guarded = require_session(sample_route)
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        sign_in(owner, fake_mist_session, CredentialMode.ENVIRONMENT_TOKEN)

    caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)
    with flask_app.test_request_context("/", headers=cookie_header(SECOND_BROWSER_ID)):
        flask.session[SESSION_OWNER_KEY] = owner.key  # A copied session from another computer
        result = guarded()
        assert isinstance(result, tuple)

    haystack = log_haystack(caplog)
    assert "refused a request with no session" in haystack  # The record ran, so the check is not vacuous
    assert_address_absent(caplog, OPERATOR_EMAIL)


# --------------------------------------------------------------------------
# The full leak sweep
# --------------------------------------------------------------------------


def test_no_public_function_writes_the_address_to_a_log_record(
    flask_app: flask.Flask,
    fake_mist_session: SimpleNamespace,
    fake_environment_token: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Drive every logging path once and prove that no record holds an address.

    Why:
        A per-function test can miss a new log call in a function it does not
        cover. This sweep drives the whole module in one capture, so a leak in
        any path fails here even before a reader adds a test for that path.

    Args:
        flask_app: The bare test application.
        fake_mist_session: The fake cloud session from the shared conftest.
        fake_environment_token: The fake token the fixture set.
        caplog: The pytest log capture fixture.
    """
    caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)
    guarded = require_session(sample_route)

    with flask_app.test_request_context("/"):
        ensure_browser_id(flask.Response())  # The first visit path
        guarded()  # The refusal path

    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        owner = build_owner(OPERATOR_EMAIL, FIRST_BROWSER_ID)
        sign_in_with_environment_token(owner, fake_mist_session)  # The sign-in path
        current_session()  # The lookup path
        current_owner()
        guarded()  # The allowed path
        sign_out()  # The sign-out path

    haystack = log_haystack(caplog)
    assert owner.email_digest in haystack  # Records really ran, so the sweep is not vacuous
    assert_address_absent(caplog, OPERATOR_EMAIL)
    assert fake_environment_token.casefold() not in haystack  # No credential value either
    assert FIRST_BROWSER_ID.casefold() not in haystack  # No browser identifier either
