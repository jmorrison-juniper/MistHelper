"""The per-operator identity services of the upgrade capture portal.

Why:
    The portal serves several operators at the same time, and the site lock
    grants one site to exactly one of them. The lock identity is the pair of
    the work email address and a browser identifier (FR-073). One operator with
    two tabs on one computer is one identity and may drive two sites at once
    (FR-074). The same address on a second computer is a different identity.
    That is why the browser identifier is a first-party cookie and not a value
    derived from the address. This module owns the pair, holds the cloud
    session for each pair, and refuses a request that carries no session.

Credential modes:
    This phase supports the environment token mode only (FR-006). The process
    already holds a cloud session that an environment token created, so the
    operator supplies a work email address alone and no password. The managed
    service provider login of FR-007, which asks for an address and a password
    and may ask for a second factor, arrives with User Story 5. `CredentialMode`
    and `sign_in` already carry the second mode, so that story adds a route and
    rewrites nothing here.

Personal data:
    A work email address is personal data. This module never writes an address
    to a log record. It writes the value of `email_digest` instead, which is a
    short one-way BLAKE2s digest of the normalized address. The digest is
    stable across processes and across restarts, so an operator can join the
    records of one person without the portal publishing the address.

Credential values:
    The registry holds the operator address, the browser identifier, and a
    reference to the cloud session object. It holds no password, no API token,
    and no fragment of either (FR-009). `environment_token_present` asks only
    whether a variable is set, and never binds the value to a name. Both
    `SessionOwner` and `OperatorSession` define their own text form, so a
    record that reaches a log line shows the digest and nothing more.
"""

import functools  # Keeps the name and the docstring of a guarded route function
import hashlib  # Builds the one-way digest that replaces an address in a log record
import logging  # The stdlib logger the whole portal uses
import os  # Reads the presence of a token variable, never its value
import re  # Validates the shape of an address and of a browser identifier
import secrets  # Generates an unpredictable browser identifier
import threading  # Guards the registry, because several request threads share it
from collections.abc import Callable  # Types the route function the guard wraps
from dataclasses import dataclass, field  # Builds the two records without hand-written methods
from datetime import UTC, datetime  # Stamps every sign-in in one time zone
from enum import StrEnum  # Names the credential modes as text that a page can show
from typing import Any, Final, ParamSpec, TypeVar  # `Any` holds the session, `Final` freezes the constants

import flask  # Request, session, and cookie access
from flask import Response  # The response object the cookie writer takes

_LOGGER: Final[logging.Logger] = logging.getLogger(__name__)  # One logger for the whole module

BROWSER_ID_COOKIE: Final[str] = "browser_id"  # The first-party cookie name
BROWSER_ID_BYTES: Final[int] = 32  # 32 random bytes give 43 URL-safe characters
BROWSER_ID_MAX_AGE_SECONDS: Final[int] = 31_536_000  # 365 days keeps the value across windows
ENVIRONMENT_TOKEN_VARIABLES: Final[tuple[str, ...]] = ("MIST_APITOKEN", "MIST_API_TOKEN")  # Names only
ERROR_NOT_AUTHENTICATED: Final[str] = "not_authenticated"  # The fixed code a test asserts on
SESSION_OWNER_KEY: Final[str] = "owner_key"  # The field inside the signed browser session

_EMAIL_DIGEST_BYTES: Final[int] = 8  # 8 bytes give a 16 character digest
_MAX_EMAIL_LENGTH: Final[int] = 254  # The longest address a mail server accepts
_EMAIL_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")  # One at sign, one dot
_BROWSER_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_-]{16,128}$")  # The URL-safe shape

# The guard below needs a generic signature. It declares the two type variables
# here, in the form of `typing`, and not in the form of PEP 695.
# Caution: two CI gates disagree about this signature, and one form must break.
# pydocstyle 6.3.0 cannot parse a PEP 695 type parameter list. It reads
# `def name[T](...)` as a function with no docstring and reports D103, even when
# the docstring is present. CI runs pydocstyle over `src/`, so the PEP 695 form
# fails the build. Ruff asks for the opposite form through UP047, so the line
# below carries one narrow suppression. Keep both until the project replaces
# pydocstyle, and then move to PEP 695 and drop the suppression.
ViewArgs = ParamSpec("ViewArgs")  # The parameters of the route function the guard wraps
ViewResult = TypeVar("ViewResult")  # The return value of that route function


def _utc_now() -> datetime:  # One clock for every stored time in this feature
    """Return the current time in coordinated universal time.

    Why:
        Every stored time in this feature is UTC, so a comparison between two
        operators in two time zones stays correct.

    Returns:
        An aware datetime in the UTC zone.
    """
    return datetime.now(UTC)  # An aware value, so no later comparison guesses the zone


def email_digest(actor_email: str) -> str:  # The only form of an address that a log record may hold
    """Build a short one-way digest of a work email address.

    Why:
        An email address is personal data, so no log record may hold one. A
        digest lets an operator join the records of one person without the
        portal publishing the address. BLAKE2s runs one way, so the portal
        cannot recover the address from the digest.

    Args:
        actor_email: The work email address. The function normalizes the value
            first, so two spellings of one address give one digest.

    Returns:
        A 16 character lower-case hexadecimal digest.
    """
    normalized = actor_email.strip().casefold().encode("utf-8")  # One spelling for one person
    return hashlib.blake2s(normalized, digest_size=_EMAIL_DIGEST_BYTES).hexdigest()  # One way, never back


def normalize_email(raw_email: str) -> str:  # Runs before any identity reaches a lock record
    """Trim and lower-case a work email address.

    Why:
        The site lock compares two identities as text. Without one spelling,
        `Person@Example.com` and `person@example.com` would look like two
        operators, and the lock would refuse the second tab of one person.

    Args:
        raw_email: The address the operator typed.

    Returns:
        The normalized address.

    Raises:
        ValueError: If the address is empty, too long, or has no domain part.
            The message holds no part of the address, because a message may
            reach a log record.
    """
    candidate = raw_email.strip().casefold()  # One spelling for one person
    if not candidate or len(candidate) > _MAX_EMAIL_LENGTH:  # An empty or oversize value never reaches a lock
        raise ValueError("The work email address is empty or too long.")  # No part of the value in the text
    if _EMAIL_PATTERN.match(candidate) is None:  # A value with no domain part cannot name a work mailbox
        raise ValueError("The work email address has no domain part.")  # No part of the value in the text
    return candidate  # The one spelling that every later comparison uses


def environment_token_present() -> bool:  # A presence check, and never a read of the value
    """Report whether the process environment holds a cloud API token.

    Why:
        FR-006 offers two credential modes, and this phase supports the
        environment token mode alone. The sign-in page must state whether that
        mode is available. This function asks only whether a variable holds
        text. It binds no value to a name, returns no value, and logs no value.

    Returns:
        True when one of the token variable names holds a non-empty value.
    """
    return any(os.environ.get(name, "").strip() for name in ENVIRONMENT_TOKEN_VARIABLES)  # Presence alone


class CredentialMode(StrEnum):  # A StrEnum, so a page and a record hold the same text
    """The way the portal obtained the cloud session of one operator.

    Why:
        FR-006 offers the environment token and the managed service provider
        login. The registry records which mode created a session, so a later
        page names the mode instead of a guess. This phase builds the
        environment token mode alone. User Story 5 adds the provider login and
        changes no line of this enumeration.
    """

    ENVIRONMENT_TOKEN = "environment_token"  # The process environment already holds a cloud token
    PROVIDER_LOGIN = "provider_login"  # The operator supplies an address and a password in User Story 5


class CredentialUnavailableError(RuntimeError):  # A RuntimeError, so a route catches it apart from ValueError
    """The requested credential mode cannot start a cloud session.

    Why:
        The environment token mode works only when the process environment
        holds a token. A named exception lets the sign-in route answer with a
        plain sentence and with no credential detail.
    """


@dataclass(frozen=True, slots=True, repr=False)
class SessionOwner:  # Frozen, so a stored owner cannot change while the site lock holds it
    """The identity pair that the site lock grants a site to.

    Why:
        FR-073 forms the session owner from the work email address and a
        browser identity. FR-074 then lets one owner hold several site locks in
        several tabs. Two tabs on one computer share the browser identifier and
        count as one owner. A second computer holds a different identifier and
        counts as a different owner.

    Attributes:
        actor_email: The normalized work email address of the operator.
        browser_id: The value of the first-party `browser_id` cookie.
    """

    actor_email: str  # The normalized address, held for the lock record and for nothing else
    browser_id: str  # The cookie value that separates one computer from another

    @property
    def email_digest(self) -> str:
        """Return the short one-way digest of the email address.

        Why:
            A log record must join the work of one person without the portal
            publishing the address.

        Returns:
            The digest that `email_digest` builds.
        """
        return email_digest(self.actor_email)  # The only form of the address that a log record may hold

    @property
    def key(self) -> str:
        """Return the registry key of this owner.

        Why:
            The signed browser session carries this key. The key holds the
            digest and not the address, so the browser never carries personal
            data even though its owner could read the value.

        Returns:
            The email digest and the browser identifier, joined by a colon.
        """
        return f"{self.email_digest}:{self.browser_id}"  # A colon cannot appear in either half

    def __repr__(self) -> str:  # Replaces the dataclass form, which would print the address
        """Return a text form that holds no personal data.

        Returns:
            The class name and the email digest.
        """
        return f"SessionOwner(email_digest={self.email_digest!r})"  # A traceback shows the digest alone


@dataclass(slots=True, repr=False)
class OperatorSession:  # Mutable, so a later story can refresh the cloud session in place
    """One signed-in operator and the cloud session that serves them.

    Why:
        `MistHelper` keeps one cloud session in a module global, so a second
        login overwrites the first. This portal serves up to 10 operators at
        one time, so each owner needs a record of its own. The record holds the
        cloud session by reference. It holds no password, no API token, and no
        fragment of either (FR-009).

    Attributes:
        owner: The address and browser pair that the site lock uses.
        cloud_session: A reference to the `mistapi` session object. The portal
            passes this object to every cloud call of this operator.
        credential_mode: The mode that created the cloud session.
        created_at: The sign-in time in coordinated universal time.
    """

    owner: SessionOwner  # The pair that the site lock grants a site to
    cloud_session: Any  # A reference to the `mistapi` object, never a credential value
    credential_mode: CredentialMode  # The mode that opened the cloud session
    created_at: datetime = field(default_factory=_utc_now)  # Set once, at sign-in

    def __repr__(self) -> str:  # Replaces the dataclass form, which would print the cloud session
        """Return a text form that holds no personal data and no credential.

        Returns:
            The class name, the email digest, and the credential mode.
        """
        digest = self.owner.email_digest  # The address itself never reaches a traceback
        return f"OperatorSession(email_digest={digest!r}, mode={self.credential_mode.value!r})"  # No token


class SessionRegistry:
    """The store of live cloud sessions, one record for each owner.

    Why:
        One process holds one cloud session today, so a second login overwrites
        the first. This registry gives every owner a record of its own, which
        lets the portal serve several operators at the same time (FR-005). A
        lock guards the store, because the threaded worker runs several request
        threads in one process.
    """

    def __init__(self) -> None:
        """Create an empty registry with a lock of its own."""
        self._sessions: dict[str, OperatorSession] = {}  # Owner key to record
        self._guard = threading.RLock()  # Several request threads share the store

    def register(self, session: OperatorSession) -> None:
        """Store the record of one owner, and replace an earlier record.

        Why:
            A second sign-in from the same browser must not leave two cloud
            sessions behind for one owner.

        Args:
            session: The record to store.
        """
        with self._guard:  # Hold the lock, because a second thread may register at the same moment
            self._sessions[session.owner.key] = session  # A repeat sign-in replaces the earlier record

    def get(self, owner_key: str) -> OperatorSession | None:
        """Return the record of one owner.

        Args:
            owner_key: The value that `SessionOwner.key` builds.

        Returns:
            The stored record, or None when the registry holds no such owner.
        """
        with self._guard:  # Hold the lock, because another thread may drop this owner
            return self._sessions.get(owner_key)  # An unknown key answers None and raises nothing

    def drop(self, owner_key: str) -> bool:
        """Remove the record of one owner.

        Why:
            A sign-out must remove the cloud session reference from the
            process. A cleared browser cookie alone would leave the object in
            memory.

        Args:
            owner_key: The value that `SessionOwner.key` builds.

        Returns:
            True when a record existed and this call removed it.
        """
        with self._guard:  # Hold the lock, so two sign-out calls cannot both report success
            return self._sessions.pop(owner_key, None) is not None  # Drop the cloud session reference

    def owner_count(self) -> int:
        """Return the number of owners the registry holds.

        Why:
            The health view reports the count. The count holds no personal
            data, so it is safe to show and safe to log.

        Returns:
            The number of stored records.
        """
        with self._guard:  # Hold the lock, so the count matches one moment of the store
            return len(self._sessions)  # A number alone, so the health view holds no personal data


SESSION_REGISTRY: Final[SessionRegistry] = SessionRegistry()  # One store for the whole process


def issue_browser_id() -> str:
    """Create a new browser identifier.

    Why:
        FR-073 needs a browser identity that nobody can derive from the email
        address. A derived value would make two computers look like one
        browser, and the site lock would then grant one site to two operators.
        `secrets.token_urlsafe` gives an unpredictable value instead.

    Returns:
        A URL-safe text value of 43 characters.
    """
    return secrets.token_urlsafe(BROWSER_ID_BYTES)  # Unpredictable, and never derived from the address


def read_browser_id() -> str | None:
    """Read the browser identifier from the current request.

    Why:
        The identifier reaches a Redis lock record, so a hostile cookie value
        must not pass. This function accepts the shape that `issue_browser_id`
        writes, and rejects every other value.

    Returns:
        The cookie value, or None when the cookie is absent or malformed.
    """
    value = flask.request.cookies.get(BROWSER_ID_COOKIE)  # The browser sends the value back as text
    if value is None or _BROWSER_ID_PATTERN.match(value) is None:  # A hostile value must not reach a lock
        return None  # The caller then treats the request as a first visit
    return value  # The shape matches the value that `issue_browser_id` writes


def attach_browser_id(response: Response, browser_id: str) -> Response:
    """Write the first-party `browser_id` cookie onto a response.

    Why:
        `HttpOnly` keeps page script away from the value. `SameSite=Lax` stops
        another site from driving a state change. The `Secure` flag follows the
        scheme of the request, so a TLS run keeps the cookie off plain HTTP.

    Args:
        response: The response that carries the cookie to the browser.
        browser_id: The value to write.

    Returns:
        The same response object.
    """
    response.set_cookie(
        BROWSER_ID_COOKIE,
        browser_id,
        max_age=BROWSER_ID_MAX_AGE_SECONDS,  # A stored cookie lets two windows share one value
        httponly=True,
        samesite="Lax",
        secure=flask.request.is_secure,  # A proxy must forward the scheme for this flag to appear
        path="/",
    )
    return response  # The caller returns the same object, so no second response is needed


def ensure_browser_id(response: Response) -> str:
    """Return the browser identifier, and write the cookie when it is missing.

    Why:
        FR-072 asks for an identity before the first write action, and the
        first visit carries no cookie. This call gives every response a stable
        identifier without a second round trip.

    Args:
        response: The response that carries a new cookie when one is needed.

    Returns:
        The existing identifier, or the identifier this call issued.
    """
    existing = read_browser_id()  # A second window of one browser already carries the value
    if existing is not None:  # Keep the value, so both windows count as one identity
        return existing  # No cookie write, so the maximum age keeps its original start
    fresh = issue_browser_id()  # The first visit of this browser needs a value of its own
    attach_browser_id(response, fresh)  # The browser holds the value for every later request
    _LOGGER.debug("identity: issued a new browser identifier")  # The value never reaches a record
    return fresh  # The caller uses the value at once, before the browser sends it back


def build_owner(actor_email: str, browser_id: str) -> SessionOwner:
    """Build the identity pair from a typed address and a cookie value.

    Why:
        Both halves of the pair need a check before the pair reaches a lock
        record. One builder keeps that check in one place.

    Args:
        actor_email: The address the operator typed.
        browser_id: The value that `read_browser_id` or `ensure_browser_id`
            returned.

    Returns:
        The identity pair.

    Raises:
        ValueError: If the browser identifier has the wrong shape, or if
            `normalize_email` rejects the address.
    """
    if _BROWSER_ID_PATTERN.match(browser_id) is None:  # Check the cookie half before the pair exists
        raise ValueError("The browser identifier has the wrong shape.")  # The value stays out of the text
    return SessionOwner(actor_email=normalize_email(actor_email), browser_id=browser_id)  # Both halves checked


def sign_in(owner: SessionOwner, cloud_session: Any, mode: CredentialMode) -> OperatorSession:
    """Register a cloud session for one owner, and mark the browser session.

    Why:
        This function is the seam that lets User Story 5 add the provider
        login. Both credential modes end here, so that story adds a route and
        changes no line of this function.

    Args:
        owner: The identity pair that `build_owner` returned.
        cloud_session: The `mistapi` session object, held by reference. The
            registry stores the reference and stores no credential value.
        mode: The credential mode that created the cloud session.

    Returns:
        The stored record.
    """
    _LOGGER.info("identity: sign-in start for operator %s in mode %s", owner.email_digest, mode.value)  # Digest
    record = OperatorSession(owner=owner, cloud_session=cloud_session, credential_mode=mode)  # By reference
    SESSION_REGISTRY.register(record)  # The record now serves every later request of this owner
    flask.session[SESSION_OWNER_KEY] = owner.key  # The signed session carries the key, never the address
    _LOGGER.debug("identity: sign-in done for operator %s", owner.email_digest)  # A pair of records to join
    return record  # The route reads `cloud_session` from the record


def sign_in_with_environment_token(owner: SessionOwner, cloud_session: Any) -> OperatorSession:
    """Sign an operator in with the cloud session that the environment created.

    Why:
        FR-006 offers this mode, and this phase supports it alone. The process
        already holds a cloud session that an environment token created, so the
        operator supplies a work email address and no password. The check below
        asks only whether a token variable holds text. It reads no value.

    Args:
        owner: The identity pair that `build_owner` returned.
        cloud_session: The `mistapi` session object, held by reference.

    Returns:
        The stored record.

    Raises:
        CredentialUnavailableError: If no token variable holds a value. The
            message names the variables and shows no value (FR-009).
    """
    if not environment_token_present():  # Ask about presence alone, and read no value
        raise CredentialUnavailableError("Set MIST_APITOKEN or MIST_API_TOKEN before you sign in.")  # Names only
    return sign_in(owner, cloud_session, CredentialMode.ENVIRONMENT_TOKEN)  # One seam for both modes


def current_session() -> OperatorSession | None:
    """Return the record of the current request, or None.

    Why:
        The guard and the site lock need one answer to the same question. The
        check also binds the signed browser session to the browser cookie, so a
        copied session fails on a computer that holds a different browser
        identifier.

    Returns:
        The stored record, or None when the request carries no valid session.
    """
    owner_key = flask.session.get(SESSION_OWNER_KEY)  # Flask signs the browser session, so nobody forges it
    if not isinstance(owner_key, str):  # An absent or damaged field means the request carries no session
        return None  # The guard then answers the refusal envelope
    record = SESSION_REGISTRY.get(owner_key)  # A worker restart empties the store, so the key may be stale
    if record is None or record.owner.browser_id != read_browser_id():  # A copied session fails this check
        return None  # A second computer holds a different cookie and gets no session
    return record  # Both the signed session and the browser cookie agree


def current_owner() -> SessionOwner | None:
    """Return the identity pair of the current request, or None.

    Why:
        The site lock stores `actor_email` and `browser_id` together. This
        helper hands the lock module the pair, so the lock module needs no
        reach into the registry.

    Returns:
        The identity pair, or None when the request carries no valid session.
    """
    record = current_session()  # One question, one answer, for the guard and for the lock
    return None if record is None else record.owner  # The lock module needs the pair alone


def sign_out() -> bool:
    """Drop the cloud session of the current request.

    Why:
        A sign-out must remove the cloud session reference from the process. A
        cleared browser session alone would leave the object in memory for the
        life of the worker.

    Returns:
        True when a record existed and the registry dropped it.
    """
    owner_key = flask.session.pop(SESSION_OWNER_KEY, None)  # Clear the browser half first
    if not isinstance(owner_key, str):  # A request with no session has nothing to drop
        return False  # The route still answers with the sign-in page
    _LOGGER.info("identity: sign-out start for operator %s", owner_key.split(":", 1)[0])  # Digest half only
    dropped = SESSION_REGISTRY.drop(owner_key)  # Remove the cloud session reference from the process
    _LOGGER.debug("identity: sign-out done, dropped a record %s", dropped)  # A boolean holds no personal data
    return dropped  # False means a worker restart had already emptied the store


def not_authenticated_response() -> tuple[Response, int]:
    """Build the `not_authenticated` error envelope.

    Why:
        `contracts/README.md:31-39` fixes one shape for every JSON error, and a
        test asserts on `code` and never on `message`. This function builds the
        envelope here and imports no application module, because the
        application factory imports the route modules that apply the guard.

    Returns:
        The JSON response and the status code 401.
    """
    payload = {"error": {"code": ERROR_NOT_AUTHENTICATED, "message": "Sign in before you continue."}}  # One shape
    return flask.jsonify(payload), 401  # The status and the code always travel together


def _refusal_for_request() -> tuple[Response, int] | None:
    """Return the refusal envelope when the request carries no session.

    Why:
        The guard below stays short when the decision lives in a function of
        its own, and a test can then call the decision without a decorator.

    Returns:
        The `not_authenticated` envelope, or None when a session exists.
    """
    if current_session() is not None:  # A valid pair of session and cookie answers the question
        return None  # The route function may run
    # The endpoint name is our own text, so the record stays ASCII.
    _LOGGER.info("identity: refused a request with no session for endpoint %s", flask.request.endpoint)
    return not_authenticated_response()  # The one envelope that every guarded route answers with


def require_session(  # noqa: UP047  # WHY: pydocstyle 6.3.0 fails on PEP 695, and CI runs it.
    view: Callable[ViewArgs, ViewResult],
) -> Callable[ViewArgs, ViewResult | tuple[Response, int]]:
    """Refuse a request that carries no signed-in session.

    Why:
        `contracts/README.md:49-54` asks for a session on every endpoint except
        the sign-in pages. One decorator keeps that rule in one place, so a new
        route cannot forget it.

    Args:
        view: The route function to guard.

    Returns:
        A function that answers `401 not_authenticated` when no session exists,
        and that calls the route function when a session exists.
    """

    @functools.wraps(view)
    def guarded(*args: ViewArgs.args, **kwargs: ViewArgs.kwargs) -> ViewResult | tuple[Response, int]:
        """Answer the request when a session exists, and refuse it otherwise."""
        refusal = _refusal_for_request()  # Ask once, before the route function runs
        return view(*args, **kwargs) if refusal is None else refusal  # The route never sees a refused request

    return guarded  # `functools.wraps` keeps the name, so Flask registers the original endpoint
