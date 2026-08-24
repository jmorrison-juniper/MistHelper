"""The sign-in surface, the second factor challenge, and the sign-out route.

Why:
    FR-006 lets the operator choose between the environment API token and a
    managed service provider login. FR-007 asks for the email and the password,
    and asks for a second factor when the account needs one. FR-008 reports the
    result. FR-009 forbids a password value, a code value, or a token value in
    any log record, any store, and any answer. This module holds that whole
    journey, so no other module ever touches a credential.

Route names:
    `contracts/http-api.md` fixes every path below. The template layer and the
    browser script use the paths and not the endpoint names, so a rename of a
    function stays safe, and a change of a path does not.

Where a credential lives:
    The password reaches two expressions: the call that builds the cloud
    session, and the truth test inside `password_present`. Each expression
    discards the value at once. No local name, no session field, no cookie, no
    template value, and no log record ever holds it. The second factor code
    reaches one expression as well: the retry call. The `mistapi` session object
    keeps whatever it needs for its own transport, and this module never reads
    that state back.

Why a pending store exists:
    A second factor arrives on a later request, and the cloud needs the same
    session object that made the first attempt. The signed browser session
    cannot carry a live object, and it must never carry the password. The store
    below therefore holds the object in memory, keyed by the browser
    identifier, for a short wait. Nothing in the record is a credential value.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # The portal logs with the standard library only.
import os  # Reads a token variable by name for the environment token mode.
import threading  # Guards the pending store, because a worker pool serves the routes.
import time  # Measures the wait of a pending second factor with a monotonic clock.
from collections.abc import Callable  # Types each injected seam.
from dataclasses import dataclass  # Builds the two small records of this module.
from importlib import import_module  # Imports the cloud library late, never at load.
from typing import Any  # A cloud session and an injected seam are both free-form.

from flask import Blueprint, Response, current_app, jsonify, render_template, request  # The framework.
from jinja2 import TemplateNotFound  # Marks a template that a later module still builds.

from ...runtime import identity  # The registry, the digest, and the sign-out. No copy of them lives here.
from ..factory import json_error  # The one error envelope that the contract allows.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

auth_bp = Blueprint("auth", __name__)  # The factory looks for this exact name, so no rename is safe.

ROOT_PATH = "/"  # The entry point, which sends the operator to the right first page.
SIGNIN_PATH = "/auth/signin"  # The sign-in form, and the post that carries the pair.
TWO_FACTOR_PATH = "/auth/twofactor"  # The second factor form, and the post that carries the code.
SIGNOUT_PATH = "/auth/signout"  # The post that ends the session.
NEXT_AFTER_SIGNIN = "/select/org"  # `contracts/http-api.md` names the organization picker next.
NEXT_AFTER_SIGNOUT = SIGNIN_PATH  # A sign-out always returns the operator to the sign-in form.

EMAIL_FIELD = "email"  # The body field that carries the work address.
PASSWORD_FIELD = "password"  # nosec B105  # WHY: this names a request body field. No password value sits here.
CODE_FIELD = "code"  # The body field that carries the second factor code, read once and never stored.
HOST_FIELD = "host"  # The body field that names the Mist cloud, checked against the catalog.
MODE_FIELD = "mode"  # The body field that names the credential mode of FR-006.

SIGNIN_TEMPLATE = "auth/signin.html"  # The sign-in page.
TWO_FACTOR_TEMPLATE = "auth/twofactor.html"  # The second factor page.
FALLBACK_TEMPLATE = "layout.html"  # The shell page, shown while an auth template is still missing.

SIGNIN_TITLE = "Sign in"  # The heading and the tab text of the sign-in page.
TWO_FACTOR_TITLE = "Second factor"  # The heading and the tab text of the second factor page.
ERROR_KEY = "error_message"  # The template value that fills the `signin-error` region.

CLOUD_LOGIN_KEY = "CLOUD_LOGIN"  # A test injects one callable here and opens no socket.
TOKEN_SESSION_KEY = "CLOUD_TOKEN_SESSION"  # nosec B105  # WHY: this names a configuration key that holds a callable.

MISTAPI_MODULE = "mistapi"  # The cloud library, imported late so an import fault cannot stop the portal.
CONSOLE_LOG_LEVEL = 20  # Info level, so the library prints no debug line that could echo a credential.

PROJECT_ROOT = __name__.rsplit(".", maxsplit=4)[0]  # Four levels above `upgrade_portal.app.routes.auth` is `src`.
CLOUDS_MODULE = "auth.interactive.clouds"  # The existing catalog of the Mist clouds, reused and never copied.
CLOUDS_ATTRIBUTE = "MIST_CLOUDS"  # The name of the mapping inside that module.
DEFAULT_CLOUD_HOST = "api.mist.com"  # Global 01, which the existing interactive flow also offers first.
DEFAULT_CLOUD_LABEL = "Global 01"  # The label that goes with the default host.

BAD_CREDENTIALS = "bad_credentials"  # `contracts/http-api.md` fixes this code for a refused pair.
RATE_LIMITED = "rate_limited"  # `contracts/http-api.md` fixes this code for a throttled attempt.
BAD_TWO_FACTOR_CODE = "bad_two_factor_code"  # `contracts/http-api.md` fixes this code for a refused code.

BAD_CREDENTIALS_MESSAGE = "The portal could not sign you in. Check the address and the password, then try again."
# WHY: this value is a sentence that the sign-in page shows to the operator.
# The sentence asks for a password, and it holds no password value. The line
# carries the suppression alone, because the sentence fills the whole line.
MISSING_PASSWORD_MESSAGE = "The portal received no password. Type your password, then try again."  # nosec B105
RATE_LIMITED_MESSAGE = "The cloud refused more sign-in attempts for now. Wait a short time, then try again."
BAD_CODE_MESSAGE = "The portal could not accept that code. Read the current code, then try again."
EXPIRED_MESSAGE = "The second factor step is no longer open. Start the sign-in again."

OK_STATUS = 200  # The answer for a step that succeeded.
BAD_REQUEST_STATUS = 400  # The cloud refused the pair, or refused the code.
RATE_LIMIT_STATUS = 429  # The cloud throttled the attempt.
REDIRECT_STATUS = 303  # See Other, so the browser reads the next page with GET and never repeats the post.

BROWSER_MIME = "text/html"  # A browser form post states this type first.
SCRIPT_MIME = "application/json"  # The portal script asks for this type.
SCRIPT_HEADER = "X-Requested-With"  # A script marks its own request with this header.
SCRIPT_HEADER_VALUE = "XMLHttpRequest"  # The one value that names a script request.
LOCATION_HEADER = "Location"  # The header that carries the next page of a redirect.

STATE_OK = "ok"  # The cloud accepted the credential and the session is live.
STATE_TWO_FACTOR = "two_factor"  # The cloud accepted the pair and now asks for a code.
STATE_RATE_LIMITED = "rate_limited"  # The cloud refused to judge the attempt for now.
STATE_REFUSED = "refused"  # The cloud judged the attempt and said no.

RATE_LIMIT_MARKERS = ("too many", "rate limit", "429")  # The wordings that name a throttle in a cloud answer.
TWO_FACTOR_FIELD = "two_factor_required"  # The flag that the cloud sets when it wants a second factor.
AUTHENTICATED_FIELD = "authenticated"  # The flag that the cloud sets when the login succeeded.
STATUS_CODE_FIELD = "status_code"  # The transport status that the cloud answer may carry.
ERROR_FIELD = "error"  # The nested object that carries the reason of a refusal.
MESSAGE_FIELD = "message"  # The text inside that nested object.

PENDING_SECONDS = 300.0  # Five minutes, which is longer than any authenticator code and shorter than a shift.
PENDING_LIMIT = 64  # A cap, so a flood of half-finished logins cannot grow the process without a bound.

_PENDING_LOCK = threading.Lock()  # One lock, because two workers may reach the store in the same moment.
_PENDING: dict[str, PendingSignIn] = {}  # The half-finished logins, keyed by browser identifier.


@dataclass(frozen=True)
class PendingSignIn:
    """One half-finished sign-in that waits for a second factor.

    Why:
        The retry must reach the same cloud session object that made the first
        attempt, because that object holds the transport state of the attempt.
        A frozen record keeps a later reader from editing the pair, and the
        digest field lets every log line name the operator with no address.

        No field holds a password value, a code value, or a token value.

    Attributes:
        actor_email: The normalized work address, needed to build the owner.
        actor_digest: The one-way digest of that address, for the log records.
        cloud_session: The `mistapi` session object, held by reference.
        host: The Mist cloud that the first attempt used.
        created_at: The monotonic reading taken when the wait started.
    """

    actor_email: str  # The address, needed once more when the sign-in completes.
    actor_digest: str  # The only form of the address that a log record may hold.
    cloud_session: Any  # The live object, held by reference and never copied.
    host: str  # Names the cloud in a log line, and never changes the retry.
    created_at: float  # A monotonic reading, so a clock change cannot extend the wait.

    def __repr__(self) -> str:
        """Describe the record without the cloud session object.

        Why:
            A default repr would print the `mistapi` object, and that object
            holds credential state. A traceback, a debugger, or a log call
            would then publish it. This repr names the operator by digest.

        Returns:
            A short description that holds no credential and no address.
        """
        return f"PendingSignIn(actor={self.actor_digest}, host={self.host})"  # Digest and host, nothing more.


@dataclass(frozen=True)
class LoginOutcome:
    """The result of one attempt against the cloud.

    Why:
        The caller needs two facts: what the cloud decided, and which session
        object carries that decision. A record keeps the two together, so no
        function has to return a bare pair and no caller has to unpack one.

    Attributes:
        state: One of the four `STATE_` values of this module.
        cloud_session: The session object, or None when the attempt raised.
    """

    state: str  # One of the four `STATE_` values, and never a cloud message.
    cloud_session: Any  # The live object, or None when the call never returned one.

    def __repr__(self) -> str:
        """Describe the outcome without the cloud session object.

        Why:
            The same reason as the record above. The session object holds
            credential state, so no automatic description may print it.

        Returns:
            A short description that names the state alone.
        """
        return f"LoginOutcome(state={self.state})"  # The decision, and never the object behind it.


def injected_seam(config_key: str) -> Callable[..., Any] | None:
    """Return the callable that the application configuration holds for one seam.

    Why:
        A contract test injects a stand-in here and reaches no network. The
        injection wins over the real cloud library, so a test needs no cloud
        account and opens no socket.

    Args:
        config_key: The configuration key of the seam.

    Returns:
        The injected callable, or None when the configuration holds none.
    """
    candidate: Any = current_app.config.get(config_key)  # An unset key reads as None.
    return candidate if callable(candidate) else None  # A value that is not callable counts as unset.


def cloud_catalog() -> tuple[tuple[str, str], ...]:
    """Return the label and the host of every Mist cloud the portal offers.

    Why:
        The portal settings name no Mist cloud, and the sign-in page must offer
        one. The existing interactive flow already holds the catalog, so this
        function reads that one source instead of copying the list. A crafted
        body cannot add a host, because `resolve_host` checks against this
        answer, and a password therefore never travels to an unknown server.

    Returns:
        A pair for each cloud, or the default cloud alone when the catalog is
        unreadable.
    """
    fallback = ((DEFAULT_CLOUD_LABEL, DEFAULT_CLOUD_HOST),)  # One safe cloud is better than no sign-in at all.
    try:  # The catalog lives outside this package, so an import fault must not stop the portal.
        entries: Any = getattr(import_module(f"{PROJECT_ROOT}.{CLOUDS_MODULE}"), CLOUDS_ATTRIBUTE, {})
    except ImportError:  # Expected on a trimmed install, so this is not a fault.
        logger.warning("auth: the cloud catalog is unreadable, so the portal offers the default cloud alone")
        return fallback  # The operator can still reach the cloud that the default names.
    found = tuple((str(pair[0]), str(pair[1])) for pair in entries.values() if len(pair) >= 2)  # Label and host.
    return found or fallback  # An empty catalog reads the same as an unreadable one.


def resolve_host(raw_host: str) -> str:
    """Return a Mist cloud host that the catalog names.

    Why:
        The host decides where the password travels. Free text here would let a
        crafted post send the password to a server that the attacker owns, so
        the value must match an entry of the catalog and nothing else.

    Args:
        raw_host: The host that the request named.

    Returns:
        The named host when the catalog holds it, or the default host.
    """
    if raw_host and raw_host in {host for _, host in cloud_catalog()}:  # Membership, and never a pattern match.
        return raw_host  # The catalog names it, so the password may travel there.
    if raw_host:  # A named host that the catalog does not hold is worth a record, but the value is not.
        logger.warning("auth: the request named a cloud outside the catalog, so the portal used the default")
    return DEFAULT_CLOUD_HOST  # The safe answer for a missing value and for a refused value alike.


def environment_token_value() -> str:
    """Return the cloud token that the process environment holds.

    Why:
        FR-006 offers the environment token mode, and the cloud library needs
        the value to build a session. The value passes straight to that call
        and reaches no log record, no session field, and no answer body. The
        variable names come from the identity module, so one list serves the
        presence check and this read.

    Returns:
        The first non-empty token value, or an empty string when none is set.
    """
    for name in identity.ENVIRONMENT_TOKEN_VARIABLES:  # The names are public, and the values never are.
        value = os.environ.get(name, "").strip()  # A variable set to spaces counts as unset.
        if value:  # The first name that holds text wins, which matches the presence check.
            return value  # The caller passes this straight to the library and binds it to nothing else.
    return ""  # The identity module then refuses the sign-in and names the variables.


def default_cloud_login(actor_email: str, password: str, host: str) -> Any:
    """Build a Mist cloud session for one address and one password.

    Why:
        This is the only expression of the portal that holds a password. The
        existing interactive flow makes the same call, so the portal reuses that
        behavior instead of writing a second login path. The two token fields
        reset first, because a cached token would let the library skip the pair
        and report a success that the operator never earned.

    Args:
        actor_email: The normalized work address.
        password: The value the operator typed. It reaches this call and
            nothing else.
        host: A cloud host that `resolve_host` already checked.

    Returns:
        The `mistapi` session object, before any login attempt.
    """
    mistapi: Any = import_module(MISTAPI_MODULE)  # Late, so a missing library never stops the portal at load.
    cloud_session: Any = mistapi.APISession(  # The library owns the transport, the retry, and the cookie jar.
        email=actor_email,  # The address the operator typed, and the only identity the cloud needs.
        password=password,  # Passed straight through, so no name of this module holds the value.
        host=host,  # Checked against the catalog, so no crafted body can redirect the password.
        console_log_level=CONSOLE_LOG_LEVEL,  # Info level, so the library prints no credential debug line.
        show_cli_notif=False,  # The portal is not a terminal, so the library must print no prompt.
    )
    cloud_session._apitoken = []  # A cached token would let the library skip the pair the operator typed.
    cloud_session._apitoken_index = -1  # The index must match the empty list, or the library reads past its end.
    return cloud_session  # The caller attempts the login and owns the answer.


def default_token_session(host: str) -> Any:
    """Build a Mist cloud session from the token that the environment holds.

    Why:
        FR-006 offers this mode for an operator who already exported a token.
        The value passes straight into the library call, exactly as the password
        does above, and no name outside that call holds it.

        The build alone leaves the session with no scope. `login` is what asks
        the cloud which organizations the token reaches, and the organization
        picker reads that answer. Without this call the picker shows no row and
        the operator can go no further, whatever the token allows.

    Args:
        host: A cloud host that `resolve_host` already checked.

    Returns:
        The `mistapi` session object, already signed in.
    """
    mistapi: Any = import_module(MISTAPI_MODULE)  # Late, for the same reason as the pair login above.
    cloud_session: Any = mistapi.APISession(  # The library reads the token once and owns it from there.
        apitoken=environment_token_value(),  # Read at the call, so no name of this module holds the value.
        host=host,  # The same catalog check applies, because a token is as sensitive as a password.
        console_log_level=CONSOLE_LOG_LEVEL,  # Info level, so the library prints no credential debug line.
        show_cli_notif=False,  # The portal is not a terminal, so the library must print no prompt.
    )
    cloud_session.login()  # Fills the privilege list, which the organization picker and the scope check both read.
    return cloud_session  # The caller registers the session and owns it from there.


def attempt_login(cloud_session: Any, code: str = "") -> dict[str, Any]:
    """Run one login call against the cloud, with or without a second factor.

    Why:
        The first attempt and the retry differ by one keyword. One function
        holds both, so the caller never repeats the call and the log lines that
        surround it stay in one place.

    Args:
        cloud_session: The session object that `default_cloud_login` built.
        code: The second factor code, or an empty string for the first attempt.

    Returns:
        The cloud answer as a mapping, or an empty mapping for any other shape.
    """
    result: Any = cloud_session.login_with_return(two_factor=code) if code else cloud_session.login_with_return()
    return result if isinstance(result, dict) else {}  # A library that answers None must not raise here.


def failure_text(result: dict[str, Any]) -> str:
    """Return the lower-case reason text of one cloud answer.

    Why:
        The cloud reports a throttle in its reason text and not in a flag. This
        function reads that text so the caller can classify the answer. The
        text is read and never written to a log record, because a cloud message
        can echo the value that the operator typed.

    Args:
        result: The cloud answer.

    Returns:
        The reason text in lower case, or an empty string.
    """
    error: Any = result.get(ERROR_FIELD)  # The reason may sit inside a nested object.
    if isinstance(error, dict):  # The nested shape carries the text under its own field.
        return str(error.get(MESSAGE_FIELD, "")).lower()  # One case, so one comparison serves every wording.
    return str(error or "").lower()  # A flat reason, or an empty string when the answer names none.


def two_factor_wanted(result: dict[str, Any]) -> bool:
    """Report whether the cloud asked for a second factor.

    Why:
        The cloud sets the flag at the top level in one release and inside the
        nested error object in another. The existing interactive flow reads
        both, so this portal reads both and no release breaks the journey.

    Args:
        result: The cloud answer.

    Returns:
        True when the cloud wants a code.
    """
    error: Any = result.get(ERROR_FIELD)  # The nested shape of the newer release.
    if isinstance(error, dict) and error.get(TWO_FACTOR_FIELD):  # The nested flag wins when it is present.
        return True  # The caller then opens the second factor page.
    return bool(result.get(TWO_FACTOR_FIELD))  # The flat flag of the older release.


def rate_limit_marked(text: str) -> bool:
    """Report whether one reason text names a throttle.

    Why:
        `contracts/http-api.md` fixes a separate answer for a throttled
        attempt, so the portal must not report a throttle as a bad pair. An
        operator who reads `bad_credentials` after a throttle changes a correct
        password and locks the account.

    Args:
        text: The reason text, already in lower case.

    Returns:
        True when the text names a throttle.
    """
    return any(marker in text for marker in RATE_LIMIT_MARKERS)  # Any wording of a throttle counts as one.


def login_state(result: dict[str, Any]) -> str:
    """Classify one cloud answer into a state of this module.

    Why:
        Four route branches follow from one answer. One classifier keeps the
        reading rules in one place, so the routes stay short and two routes can
        never disagree about the same answer.

    Args:
        result: The cloud answer.

    Returns:
        One of `STATE_OK`, `STATE_TWO_FACTOR`, `STATE_RATE_LIMITED`, or
        `STATE_REFUSED`.
    """
    if result.get(AUTHENTICATED_FIELD):  # The success flag wins over every other reading.
        return STATE_OK  # The caller signs the operator in.
    if two_factor_wanted(result):  # The pair passed and the account needs a code.
        return STATE_TWO_FACTOR  # The caller opens the second factor page.
    if result.get(STATUS_CODE_FIELD) == RATE_LIMIT_STATUS or rate_limit_marked(failure_text(result)):
        return STATE_RATE_LIMITED  # The caller answers 429, so the operator waits instead of retyping.
    return STATE_REFUSED  # Every other answer is a refused pair.


def purge_pending(now: float) -> None:
    """Drop every pending sign-in that waited longer than the limit.

    Why:
        A cloud session object holds transport state, so an abandoned wait must
        not keep one alive for the life of the worker. The caller already holds
        the lock, so this function takes none and never deadlocks.

    Args:
        now: The current monotonic reading.
    """
    stale = [key for key, record in _PENDING.items() if now - record.created_at > PENDING_SECONDS]
    for key in stale:  # A second pass, because a dictionary must not change during its own walk.
        _PENDING.pop(key, None)  # A key that another worker already took is not a fault.


def remember_pending(browser_id: str, record: PendingSignIn) -> None:
    """Store one half-finished sign-in until the second factor arrives.

    Why:
        The retry needs the same cloud session object, and the signed browser
        session cannot carry a live object. The cap drops the oldest wait
        instead of the whole store, so a flood cannot cancel the sign-in of an
        operator who is still typing a code.

    Args:
        browser_id: The first-party cookie value of this browser.
        record: The pending record to store.
    """
    with _PENDING_LOCK:  # Two workers may reach the store in the same moment.
        purge_pending(record.created_at)  # An expired wait releases its session object first.
        if len(_PENDING) >= PENDING_LIMIT:  # The cap keeps the store bounded under a flood.
            _PENDING.pop(min(_PENDING, key=lambda key: _PENDING[key].created_at), None)  # The oldest wait goes.
        _PENDING[browser_id] = record  # A second attempt of one browser replaces the first.


def read_pending(browser_id: str) -> PendingSignIn | None:
    """Return the pending sign-in of one browser.

    Why:
        The read purges first, so an expired wait reads as absent and the
        operator receives the refusal instead of a retry against a dead
        session.

    Args:
        browser_id: The first-party cookie value of this browser.

    Returns:
        The pending record, or None when none is open.
    """
    with _PENDING_LOCK:  # The same lock as the writer, so no reader sees a half-written store.
        purge_pending(time.monotonic())  # An expired wait must read as absent, never as stale.
        return _PENDING.get(browser_id)  # A browser with no open wait reads as None.


def drop_pending(browser_id: str) -> None:
    """Remove the pending sign-in of one browser.

    Why:
        A completed sign-in and a sign-out both end the wait. Dropping the
        record releases the cloud session object at once, instead of leaving it
        until the wait expires.

    Args:
        browser_id: The first-party cookie value of this browser.
    """
    with _PENDING_LOCK:  # The same lock as every other access to the store.
        _PENDING.pop(browser_id, None)  # A browser with no open wait is the normal case.


def read_field(name: str) -> str:
    """Read one field out of the current request body.

    Why:
        The browser script posts a JSON body and a plain form post carries the
        same field. One reader accepts both, so the page works with the script
        and without it. The value returns to the caller and never reaches a log
        record, because this reader also serves the password and the code.

    Args:
        name: The field to read.

    Returns:
        The trimmed value, or an empty string when the body names none.
    """
    payload: Any = request.get_json(silent=True)  # A body that is not JSON reads as None, never a fault.
    if isinstance(payload, dict) and isinstance(payload.get(name), str):  # The script path.
        return str(payload[name]).strip()  # A stray space must not reach the cloud call.
    return str(request.form.get(name, "")).strip()  # The plain form path.


def valid_email(raw_email: str) -> str:
    """Return the normalized work address, or an empty string.

    Why:
        `identity.build_owner` raises on a bad address, and a route must answer
        the contract envelope instead of a 500 page. This function turns the
        exception into the empty value that the caller already handles.

    Args:
        raw_email: The address the operator typed.

    Returns:
        The normalized address, or an empty string when the value is unusable.
    """
    try:  # A blank address is a normal typing mistake, not a fault of the portal.
        return identity.normalize_email(raw_email)  # One spelling, so two log records join.
    except ValueError:  # The identity module refuses a blank value.
        return ""  # The caller answers `bad_credentials`, and no log record holds the value.


def browser_identifier() -> str:
    """Return the browser identifier of the current request.

    Why:
        The pending store and the session registry both key on this value. A
        first visit carries no cookie, so this call issues one and the caller
        writes it onto the answer.

    Returns:
        The cookie value, or a new unpredictable value.
    """
    return identity.read_browser_id() or identity.issue_browser_id()  # A missing cookie means a first visit.


def wants_browser_page() -> bool:
    """Report whether the current request asks for a page instead of JSON.

    Why:
        One post serves two clients. The portal script sends `fetch` and reads
        a JSON body. A plain form post needs a new page, because a browser
        shows a JSON body as raw text. The script header wins over the `Accept`
        header, because a script inside a browser page inherits that header.

    Returns:
        True when the request states a preference for an HTML page.
    """
    if request.headers.get(SCRIPT_HEADER, "") == SCRIPT_HEADER_VALUE:  # The script names itself.
        return False  # A script always reads JSON, whatever the page header states.
    preferred = request.accept_mimetypes.best_match((SCRIPT_MIME, BROWSER_MIME))  # None means no preference.
    return preferred == BROWSER_MIME  # Only a stated preference for HTML earns a page.


def redirect_response(path: str) -> Response:
    """Build a See Other redirect to one path.

    Why:
        `flask.redirect` answers the base werkzeug response class, which the
        strict type check refuses. A direct construction gives the same answer
        with the type that every route of this module declares.

    Args:
        path: The path the browser opens next.

    Returns:
        The redirect response.
    """
    return Response(status=REDIRECT_STATUS, headers={LOCATION_HEADER: path})  # See Other, so the browser uses GET.


def next_answer(path: str) -> Response | tuple[Response, int]:
    """Answer one successful step, as a page redirect or as a JSON body.

    Why:
        `wants_browser_page` holds the negotiation rule, and this function
        holds the two answers that follow from it. Every successful step of
        this module then reads as one line.

    Args:
        path: The path the caller opens next.

    Returns:
        The redirect to the next page, or the next path as a JSON body.
    """
    if wants_browser_page():  # A browser form post cannot read a JSON body.
        return redirect_response(path)  # The browser opens the next page itself.
    return jsonify({"next": path}), OK_STATUS  # The contract fixes this body for every script caller.


def with_browser_id(answer: Response | tuple[Response, int], browser_id: str) -> Response | tuple[Response, int]:
    """Write the first-party browser cookie onto either answer shape.

    Why:
        A first visit carries no cookie, and the pending store and the session
        registry both key on the value. The cookie must therefore travel on the
        same answer that starts the wait or ends the sign-in, or the next
        request keys on a different value and finds nothing.

    Args:
        answer: The redirect, or the body and status pair.
        browser_id: The value to write.

    Returns:
        The same answer, with the cookie attached.
    """
    carrier = answer[0] if isinstance(answer, tuple) else answer  # One shape carries the response second.
    identity.attach_browser_id(carrier, browser_id)  # The identity module owns the cookie flags.
    return answer  # The caller returns this straight to the framework.


def render_page(name: str, **context: Any) -> str:
    """Render one sign-in page, and fall back while a template is still missing.

    Why:
        Without the fallback each page path would answer a fault during the
        build of this feature. The fallback shows the portal shell instead, so
        the operator sees a page and the log names the missing template.

    Args:
        name: The template to render.
        **context: The values the template reads.

    Returns:
        The rendered page.
    """
    try:  # The template may arrive in a later stage of this phase.
        return render_template(name, **context)  # The normal path once the template lands.
    except TemplateNotFound:  # Expected while the portal grows, so this is not a fault.
        logger.warning("auth: the template %s is not built yet, so the shell page answered", name)  # No trace.
        return render_template(FALLBACK_TEMPLATE, **context)  # The shell page always exists.


def signin_context() -> dict[str, Any]:
    """Build the values that the sign-in page reads.

    Why:
        FR-006 asks the page to offer both credential modes, and the page can
        only offer the token mode when a token variable holds text. FR-011 then
        needs a cloud, because the organization list of a provider login
        belongs to one cloud. The presence check reads no token value.

    Returns:
        The template values.
    """
    return {
        "page_title": SIGNIN_TITLE,  # The heading and the tab text.
        "signed_in": False,  # The navigation partial hides every link and the sign-out button.
        "clouds": [{"label": label, "host": host} for label, host in cloud_catalog()],  # The picker rows.
        "default_host": DEFAULT_CLOUD_HOST,  # The row that the page marks as chosen.
        "token_mode_available": identity.environment_token_present(),  # Presence alone, and never a value.
    }


def two_factor_context() -> dict[str, Any]:
    """Build the values that the second factor page reads.

    Why:
        The page shows one field and one button, so it needs the heading, the
        hidden navigation, and nothing else. It must never receive the address,
        because a page value reaches the markup and a screenshot.

    Returns:
        The template values.
    """
    return {
        "page_title": TWO_FACTOR_TITLE,  # The heading and the tab text.
        "signed_in": False,  # The sign-in is half finished, so the navigation shows no link.
    }


def error_page(name: str, context: dict[str, Any], message: str, status: int) -> tuple[Response, int]:
    """Render one sign-in page again, with the refusal text inside it.

    Why:
        A browser form post cannot read a JSON body, so a refusal envelope
        would show the operator raw text instead of the form. This helper shows
        the form again with the reason, and it keeps the status that
        `contracts/http-api.md` fixes, so a script caller and a browser caller
        still agree about the outcome.

    Args:
        name: The template to render.
        context: The values of that page.
        message: The reason text, which names no credential value.
        status: The status that the contract fixes for this refusal.

    Returns:
        The rendered page and the status.
    """
    context[ERROR_KEY] = message  # The page shows this text inside its own error region.
    return Response(render_page(name, **context), mimetype=BROWSER_MIME), status  # The form, and the reason.


def credential_refusal(message: str = BAD_CREDENTIALS_MESSAGE) -> tuple[Response, int]:
    """Answer a refused address and password pair.

    Why:
        `contracts/http-api.md` fixes the code, and the message must name no
        part of the value that the operator typed. One refusal for a bad
        address and for a bad password also tells an attacker nothing about
        which half was wrong. The message still varies, exactly as
        `two_factor_refusal` varies its own message, because a pair that never
        reached the cloud needs a different cure from a pair that the cloud
        refused.

    Args:
        message: The reason text, which names a cure and no credential value.

    Returns:
        The refusal envelope and the status, or the form again and the status.
    """
    if wants_browser_page():  # A browser form post must read the form again, never a JSON body.
        return error_page(SIGNIN_TEMPLATE, signin_context(), message, BAD_REQUEST_STATUS)  # The form, and the cure.
    return json_error(BAD_REQUEST_STATUS, BAD_CREDENTIALS, message)  # The script shape, with the fixed code.


def rate_limit_refusal() -> tuple[Response, int]:
    """Answer a throttled sign-in attempt.

    Why:
        An operator who reads a credential refusal after a throttle changes a
        correct password and locks the account. The separate code and the
        separate status keep that mistake out of the journey.

    Returns:
        The refusal envelope and the status, or the form again and the status.
    """
    if wants_browser_page():  # A browser form post must read the form again, never a JSON body.
        return error_page(SIGNIN_TEMPLATE, signin_context(), RATE_LIMITED_MESSAGE, RATE_LIMIT_STATUS)
    return json_error(RATE_LIMIT_STATUS, RATE_LIMITED, RATE_LIMITED_MESSAGE)  # The contract fixes both parts.


def two_factor_refusal(message: str) -> tuple[Response, int]:
    """Answer a refused second factor code.

    Why:
        `contracts/http-api.md` fixes one code for this step, so an expired
        wait and a wrong code share it. The message differs, because the
        operator needs a different next action for each case, and
        `contracts/README.md` states that a test reads the code and not the
        message.

    Args:
        message: The next action for the operator.

    Returns:
        The refusal envelope and the status, or the page again and the status.
    """
    if wants_browser_page():  # A browser form post must read the page again, never a JSON body.
        return error_page(TWO_FACTOR_TEMPLATE, two_factor_context(), message, BAD_REQUEST_STATUS)
    return json_error(BAD_REQUEST_STATUS, BAD_TWO_FACTOR_CODE, message)  # The code stays fixed for both cases.


def password_present() -> bool:
    """Report whether the request carries a password value.

    Why:
        FR-006 lets the token mode arrive with no password, so the page marks
        the field as required only while no token variable holds text. A
        provider post can therefore still arrive empty. An empty password would
        spend one cloud attempt against the sign-in rate limit for an answer
        that is already known, so the portal must refuse it here. The truth test
        keeps the value inside this one expression, so no name ever binds it.

    Returns:
        True when the field holds text, or False when the field is empty.
    """
    return bool(read_field(PASSWORD_FIELD))  # The value dies inside this expression, and no name holds it.


def run_login(actor_email: str, host: str) -> LoginOutcome:
    """Build a cloud session and make the first login attempt.

    Why:
        The password reaches the builder call and nothing else. No name of this
        module binds it, so no traceback, no debugger frame, and no log record
        can publish it. The failure branch logs the class name of the fault and
        never the text, because a library message can echo the value.

    Args:
        actor_email: The normalized work address.
        host: A cloud host that `resolve_host` already checked.

    Returns:
        The state of the attempt, with the session object when one exists.
    """
    builder = injected_seam(CLOUD_LOGIN_KEY) or default_cloud_login  # A test injects and opens no socket.
    try:  # The library raises for a transport fault and answers a mapping for a refusal.
        cloud_session = builder(actor_email, read_field(PASSWORD_FIELD), host)  # The one use of the password.
        result = attempt_login(cloud_session)  # The first attempt, with no second factor code.
    except Exception as fault:  # A transport fault must answer the contract envelope, never a 500 page.
        state = STATE_RATE_LIMITED if rate_limit_marked(str(fault).lower()) else STATE_REFUSED
        logger.warning("auth: the cloud sign-in call failed (%s) and reads as %s", type(fault).__name__, state)
        return LoginOutcome(state, None)  # No session object survives a failed call.
    return LoginOutcome(login_state(result), cloud_session)  # The classifier owns every reading of the answer.


def start_two_factor(actor_email: str, host: str, cloud_session: Any) -> Response | tuple[Response, int]:
    """Open the second factor step for one operator.

    Why:
        The cloud accepted the pair and now wants a code. The retry must reach
        the same session object, so the object waits in the pending store and
        the browser carries only its own identifier. The store holds no
        password value and no code value.

    Args:
        actor_email: The normalized work address.
        host: The cloud that the first attempt used.
        cloud_session: The session object of that attempt.

    Returns:
        The redirect to the second factor page, or that path as a JSON body.
    """
    browser_id = browser_identifier()  # A first visit gets a value here, and the answer carries it back.
    digest = identity.email_digest(actor_email)  # The only form of the address that a log record may hold.
    record = PendingSignIn(actor_email, digest, cloud_session, host, time.monotonic())  # No credential inside.
    remember_pending(browser_id, record)  # The retry finds the same object on the next request.
    logger.info("auth: the cloud asked operator %s on cloud %s for a second factor", digest, host)  # No code.
    return with_browser_id(next_answer(TWO_FACTOR_PATH), browser_id)  # The cookie must travel with this answer.


def finish_sign_in(actor_email: str, cloud_session: Any, browser_id: str) -> Response | tuple[Response, int]:
    """Register the cloud session and open the organization picker.

    Why:
        `identity.sign_in` is the one seam that both credential modes end at,
        so this function adds no registry logic of its own. FR-011 then sends
        the operator to the searchable organization list, which the selection
        surface owns at the path that `contracts/http-api.md` fixes.

    Args:
        actor_email: The normalized work address.
        cloud_session: The session object that the cloud accepted.
        browser_id: The first-party cookie value of this browser.

    Returns:
        The redirect to the organization picker, or that path as a JSON body.
    """
    owner = identity.build_owner(actor_email, browser_id)  # `valid_email` ran first, so this never raises.
    identity.sign_in(owner, cloud_session, identity.CredentialMode.PROVIDER_LOGIN)  # The registry holds it.
    drop_pending(browser_id)  # The wait is over, so the store releases its reference at once.
    logger.info("auth: operator %s signed in, and the portal opens %s", owner.email_digest, NEXT_AFTER_SIGNIN)
    return with_browser_id(next_answer(NEXT_AFTER_SIGNIN), browser_id)  # The cookie travels with this answer.


def follow_login(actor_email: str, host: str, outcome: LoginOutcome) -> Response | tuple[Response, int]:
    """Turn one login outcome into the answer that the contract fixes.

    Why:
        Four states lead to four answers. One branch point keeps the mapping in
        one place, so the sign-in route stays short and a later state cannot
        reach two different answers.

    Args:
        actor_email: The normalized work address.
        host: The cloud that the attempt used.
        outcome: The result of the attempt.

    Returns:
        The success answer, the second factor answer, or a refusal envelope.
    """
    if outcome.state == STATE_OK:  # The cloud accepted the pair with no second factor.
        return finish_sign_in(actor_email, outcome.cloud_session, browser_identifier())  # Straight to the picker.
    if outcome.state == STATE_TWO_FACTOR:  # The pair passed and the account needs a code.
        return start_two_factor(actor_email, host, outcome.cloud_session)  # The object waits for the retry.
    if outcome.state == STATE_RATE_LIMITED:  # The cloud refused to judge the attempt for now.
        return rate_limit_refusal()  # A separate code, so the operator waits instead of retyping.
    return credential_refusal()  # Every other state is a refused pair.


def start_provider_login(actor_email: str) -> Response | tuple[Response, int]:
    """Run the managed service provider login of FR-007.

    Why:
        A log record before the call and a log record after it let an operator
        join one attempt across the two records. Both records name the operator
        by digest, and neither names the password, the code, or the answer text
        of the cloud. The guard runs before the first record, because an empty
        password never reaches the cloud and starts no attempt.

    Args:
        actor_email: The normalized work address.

    Returns:
        The success answer, the second factor answer, or a refusal envelope.
    """
    if not password_present():  # FR-006 turns the page check off, so an empty provider post can still arrive.
        logger.info("auth: a provider sign-in carried no password, so the portal refused it")  # No address needed.
        return credential_refusal(MISSING_PASSWORD_MESSAGE)  # The fixed code, and a cure that names an action.
    host = resolve_host(read_field(HOST_FIELD))  # The catalog decides where the password may travel.
    digest = identity.email_digest(actor_email)  # The only form of the address that a log record may hold.
    logger.info("auth: provider sign-in start for operator %s on cloud %s", digest, host)  # Before the call.
    outcome = run_login(actor_email, host)  # The one function that sends the password to the cloud.
    logger.info("auth: provider sign-in for operator %s reads as %s", digest, outcome.state)  # After the call.
    return follow_login(actor_email, host, outcome)  # One branch point owns the four answers.


def start_token_session(actor_email: str) -> Response | tuple[Response, int]:
    """Sign an operator in with the token that the environment holds.

    Why:
        FR-006 offers this mode beside the provider login. `identity` already
        owns the presence check and the registry write, so this function adds a
        cloud session and nothing else. FR-010 then names the organization that
        the token reaches, which the selection surface reads from that session.

    Args:
        actor_email: The normalized work address.

    Returns:
        The success answer, or the credential refusal envelope.
    """
    host = resolve_host(read_field(HOST_FIELD))  # The same catalog check, because a token is as sensitive.
    browser_id = browser_identifier()  # A first visit gets a value here, and the answer carries it back.
    owner = identity.build_owner(actor_email, browser_id)  # `valid_email` ran first, so this never raises.
    logger.info("auth: token sign-in start for operator %s on cloud %s", owner.email_digest, host)  # Before.
    builder = injected_seam(TOKEN_SESSION_KEY) or default_token_session  # A test injects and opens no socket.
    return finish_token_session(owner, builder, host, browser_id)  # The write and its refusal live together.


def finish_token_session(
    owner: identity.SessionOwner, builder: Callable[..., Any], host: str, browser_id: str
) -> Response | tuple[Response, int]:
    """Build the token session and register it, or refuse the sign-in.

    Why:
        `sign_in_with_environment_token` raises when no token variable holds
        text, and the library raises when the token is unusable. Both faults
        must answer the contract envelope and not a 500 page, so one function
        holds the call and its refusal.

    Args:
        owner: The identity pair that `build_owner` returned.
        builder: The seam that builds the cloud session.
        host: A cloud host that `resolve_host` already checked.
        browser_id: The first-party cookie value of this browser.

    Returns:
        The success answer, or the credential refusal envelope.
    """
    try:  # The identity module names the variables in its own message, and shows no value.
        identity.sign_in_with_environment_token(owner, builder(host))  # The registry holds the reference.
    except Exception as fault:  # A missing variable and a refused token both end the sign-in here.
        logger.warning("auth: the token sign-in of %s failed (%s)", owner.email_digest, type(fault).__name__)
        return credential_refusal()  # The same envelope as a refused pair, so no probe learns the difference.
    logger.info("auth: operator %s signed in with a token variable", owner.email_digest)  # No value in the log.
    return with_browser_id(next_answer(NEXT_AFTER_SIGNIN), browser_id)  # The cookie travels with this answer.


def replay_login(pending: PendingSignIn) -> str:
    """Retry one login with the second factor code that the request carries.

    Why:
        The code reaches one expression: the retry call. No name of this module
        binds it, so no traceback and no log record can publish it. The failure
        branch logs the class name of the fault and never the text.

    Args:
        pending: The record that holds the session object of the first attempt.

    Returns:
        One of the four `STATE_` values of this module.
    """
    if not read_field(CODE_FIELD):  # An empty field means the operator submitted nothing.
        return STATE_REFUSED  # The caller answers the fixed code, and no log record holds the value.
    try:  # The library raises for a transport fault and answers a mapping for a refusal.
        result = attempt_login(pending.cloud_session, read_field(CODE_FIELD))  # The one use of the code.
    except Exception as fault:  # A transport fault must answer the contract envelope, never a 500 page.
        logger.warning("auth: the second factor call failed (%s)", type(fault).__name__)  # Class name alone.
        return STATE_REFUSED  # The operator reads the fixed code and reads the current code again.
    return login_state(result)  # The classifier owns every reading of the answer.


def check_two_factor(browser_id: str, pending: PendingSignIn) -> Response | tuple[Response, int]:
    """Judge one second factor code and finish or refuse the sign-in.

    Why:
        A wrong code keeps the pending record, because an operator mistypes a
        six digit code often and a dropped record would force the whole pair
        again. The wait still expires, and the cloud still counts its own
        attempts, so the retry window stays short.

    Args:
        browser_id: The first-party cookie value of this browser.
        pending: The record of the first attempt.

    Returns:
        The success answer, or the refusal envelope.
    """
    logger.info("auth: second factor check start for operator %s", pending.actor_digest)  # Before the call.
    state = replay_login(pending)  # The one function that touches the code.
    logger.info("auth: second factor for operator %s reads as %s", pending.actor_digest, state)  # After it.
    if state != STATE_OK:  # A wrong code, an empty code, or a failed call all end here.
        return two_factor_refusal(BAD_CODE_MESSAGE)  # The record stays, so the operator may read a new code.
    return finish_sign_in(pending.actor_email, pending.cloud_session, browser_id)  # The wait is over.


@auth_bp.get(ROOT_PATH)
def root() -> Response:
    """Send the operator to the first page that suits the current session.

    Why:
        `contracts/http-api.md` fixes both answers of this path. A signed-in
        operator who opens the site root would otherwise read the sign-in form
        and believe the session was lost.

    Returns:
        The redirect to the sign-in form, or to the organization picker.
    """
    if identity.current_session() is None:  # No session, or a session that the browser cookie does not match.
        return redirect_response(SIGNIN_PATH)  # The journey starts at the form.
    return redirect_response(NEXT_AFTER_SIGNIN)  # A live session continues at the organization picker.


@auth_bp.get(SIGNIN_PATH)
def signin_page() -> str:
    """Show the sign-in form.

    Why:
        FR-006 asks the operator to choose a credential mode, and FR-007 asks
        for the address and the password of a provider login. This page carries
        both, and it needs no session because it is where a session begins.

    Returns:
        The rendered sign-in page.
    """
    return render_page(SIGNIN_TEMPLATE, **signin_context())  # The context names both modes and every cloud.


@auth_bp.post(SIGNIN_PATH)
def submit_signin() -> Response | tuple[Response, int]:
    """Sign an operator in with a credential of the chosen mode.

    Why:
        FR-006 names two modes and one route serves both, because the operator
        supplies a work address in either case. The address check runs first,
        so `build_owner` never raises inside a later branch. The password never
        appears in this function, and it never appears in a log record.

        One post serves two clients. A browser form post reads a 303 redirect
        to the path that `contracts/http-api.md` names next. Every other post
        reads the `{"next": ...}` body of that same contract.

    Returns:
        The success answer, the second factor answer, or a refusal envelope.
    """
    actor_email = valid_email(read_field(EMAIL_FIELD))  # An unusable address reads as an empty string.
    if not actor_email:  # No address means the portal cannot name an owner, so the pair cannot pass.
        logger.info("auth: a sign-in arrived with no usable address, so the portal refused it")  # No value.
        return credential_refusal()  # The same envelope as a refused pair.
    if read_field(MODE_FIELD) == identity.CredentialMode.ENVIRONMENT_TOKEN.value:  # The FR-006 mode choice.
        return start_token_session(actor_email)  # The environment already holds the credential.
    return start_provider_login(actor_email)  # The default mode, which FR-007 describes.


@auth_bp.get(TWO_FACTOR_PATH)
def two_factor_page() -> str:
    """Show the second factor form.

    Why:
        `contracts/http-api.md` answers `{"next": "/auth/twofactor"}` from the
        sign-in post, so a browser must be able to open that path with GET. The
        page needs no session, because the sign-in is still half finished and
        the registry holds nothing yet.

    Returns:
        The rendered second factor page.
    """
    return render_page(TWO_FACTOR_TEMPLATE, **two_factor_context())  # No link, and no value of the operator.


@auth_bp.post(TWO_FACTOR_PATH)
def submit_two_factor() -> Response | tuple[Response, int]:
    """Judge the second factor code and finish the sign-in.

    Why:
        FR-007 asks the portal to retry the login with the code. The retry
        needs the session object of the first attempt, which the pending store
        holds under the browser identifier. A request with no open wait reads
        the same fixed code as a wrong value, because the contract names one
        code for this step.

    Returns:
        The success answer, or the refusal envelope.
    """
    browser_id = browser_identifier()  # The pending store keys on this value, so a fresh browser finds nothing.
    pending = read_pending(browser_id)  # An expired wait reads as absent, never as stale.
    if pending is None:  # The operator never posted a pair, or the wait ran out.
        logger.info("auth: a second factor arrived with no open sign-in, so the portal refused it")  # No code.
        return two_factor_refusal(EXPIRED_MESSAGE)  # The message names the next action, the code stays fixed.
    return check_two_factor(browser_id, pending)  # The judgement and the two answers live together.


@auth_bp.post(SIGNOUT_PATH)
def submit_signout() -> Response | tuple[Response, int]:
    """End the session and return the operator to the sign-in form.

    Why:
        `identity.sign_out` already drops the cloud session from the registry
        and clears the whole browser session, so this route adds no registry
        logic. It also drops any half-finished sign-in, because a wait that
        outlived a sign-out would let the next person at a shared workstation
        complete the login of the person before them.

        The route carries no session guard. A sign-out on a session that is
        already gone must still report success, or a stale tab would show a
        refusal instead of the sign-in form.

    Returns:
        The redirect to the sign-in form, or that path as a JSON body.
    """
    drop_pending(browser_identifier())  # A half-finished login must not survive a sign-out.
    dropped = identity.sign_out()  # The identity module owns the registry drop and the session clear.
    logger.info("auth: a sign-out ran, and the cloud session drop reported %s", dropped)  # No address, no key.
    return next_answer(NEXT_AFTER_SIGNOUT)  # The contract fixes this path for both clients.
