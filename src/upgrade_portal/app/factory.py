"""The application factory for the upgrade capture portal.

Why:
    Two callers start this portal and neither passes an argument. The
    `wsgi_capture.py` module builds the Gunicorn target. The menu 239 launcher
    in `MistHelper.py` builds the same object. So `create_app` takes no
    argument. It reads every setting from the process environment.

    The factory imports each route module late, inside `create_app`, and treats
    an `ImportError` as survivable. The portal is built in stages, so a route
    module can arrive after the shell. A missing module writes one warning and
    the portal starts with the routes that exist.

    Two probe routes answer from the first day. The `GET /healthz` route reports
    that the process is alive and reads no store. The `GET /readyz` route reports
    that the two stores answer. The container health check needs the first route.
    The orchestrator readiness probe needs the second one.
"""

import logging  # The portal logs with the standard library only.
import threading  # Guards the readiness cache against the worker threads.
from functools import partial  # Binds one status code to the shared error handler.
from importlib import import_module  # Imports each route module late.
from importlib.metadata import PackageNotFoundError, version  # Reads the version for the health answer.
from pathlib import Path  # Builds the asset paths from the module location.
from time import monotonic, monotonic_ns  # Ages the readiness cache, and builds a fresh value for each write.
from types import ModuleType  # The return type of a late import.
from typing import Any  # The error envelope holds free-form details.

from flask import (  # The web framework surface.
    Blueprint,
    Flask,
    Response,
    current_app,
    g,
    has_app_context,
    has_request_context,
    jsonify,
    request,
)

from .config import DEFAULT_THEMES, PortalSettings, load_settings  # The settings record and the environment reader.
from .security import PortalSecurity  # The guards that arm the application.
from .wiring import install_seams  # Joins the upgrade parts into the seams the routes read.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

# The package name and the route package come from the module name, so the
# imports work whether the caller imports `src.upgrade_portal` or
# `upgrade_portal`. Gunicorn uses the first form and a test may use the second.
PACKAGE_NAME = __name__.rsplit(".", maxsplit=2)[0]  # Two levels up from `app.factory`.
ROUTES_PACKAGE = __name__.rsplit(".", maxsplit=1)[0] + ".routes"  # A sibling package of this module.

ASSET_ROOT = Path(__file__).resolve().parent / "assets"  # The templates and the static files live together.
TEMPLATE_FOLDER = str(ASSET_ROOT / "templates")  # Flask needs the folder as text.
STATIC_FOLDER = str(ASSET_ROOT / "static")  # The vendored stylesheets and scripts.

# The five route modules match the five stages of the operator journey: sign in,
# choose a site, capture the state, drive the upgrade, and review the difference.
# Comparison route module added for T-014 delta analysis and approval workflow.
BLUEPRINT_NAMES = ("auth", "select", "capture", "upgrade", "review", "comparison")  # The registration order.

# Each route module publishes its blueprint under one of these names. The first
# match wins, so a module needs no registration list of its own.
BLUEPRINT_ATTRIBUTES = ("{name}_bp", "bp", "blueprint")  # Tried in this order.

REQUEST_HANDLES = ("mist_session", "database_router", "redis_client")  # The teardown closes each one.

ERROR_CODES = {
    400: "bad_request",  # The portal could not read the request.
    401: "not_authenticated",  # The contract names this code, not `unauthorized`.
    403: "forbidden",  # A guard refused the request. `security.py` holds the one caller today.
    404: "not_found",  # No such record.
    405: "method_not_allowed",  # The path exists and refuses this method.
    409: "conflict",  # Another operator holds the site lock.
    429: "rate_limited",  # The cloud rate limit stopped the portal.
    500: "server_error",  # An unexpected fault.
}

ERROR_MESSAGES = {
    400: "The portal could not read the request.",  # A test asserts on the code, never on this text.
    401: "Sign in to continue.",  # The sign-in page is the next step.
    403: "The portal refused this request.",  # Generic. `identity.py` holds the organization sentence.
    404: "The portal found no such record.",  # A stale link or a removed record.
    405: "That path does not accept this method.",  # The `Allow` header names the methods it accepts.
    409: "Another operator holds this site.",  # The site lock is busy.
    429: "The cloud rate limit stopped the portal. Wait and try again.",  # The cloud, not the portal.
    500: "The portal met an unexpected fault.",  # The log line holds the detail, not the browser.
}

RUN_FIELD = "run_id"  # The log field that follows one upgrade run.
SITE_FIELD = "site_id"  # The log field that names the site.
MISSING_FIELD = "-"  # The placeholder for a record that carries neither field.
HANDLER_NAME = "upgrade_portal"  # The handler name stops a duplicate on a second build.
LOG_FORMAT = (
    "%(asctime)s [%(levelname)s] %(name)s "  # The standard prefix of every record.
    "run=%(run_id)s site=%(site_id)s: %(message)s"
)

DISTRIBUTION_NAME = "misthelper"  # The installed distribution that carries the version.
UNKNOWN_VERSION = "unknown"  # The answer when no distribution is installed.
HEALTH_STATUS = 200  # The health endpoint always answers with this status.

READY_STATUS = 200  # Every store accepted a write and returned it.
NOT_READY_STATUS = 503  # At least one store did not answer.
STATUS_FIELD = "status"  # The readiness key that carries the summary word.
DATABASE_FIELD = "database"  # The readiness key that carries the document store reading.
REDIS_FIELD = "redis"  # The readiness key that carries the lock store reading.
READY_WORD = "ready"  # The summary word when every store answered.
NOT_READY_WORD = "not_ready"  # The summary word when a store did not answer.
STORE_OK = "ok"  # The reading of a store that accepted a write and returned it.
STORE_DOWN = "unreachable"  # The reading of a store that failed for any reason.
STORE_MODULE = f"{PACKAGE_NAME}.capture.store"  # The module that owns `connect_database`.
LOCK_MODULE = f"{PACKAGE_NAME}.runtime.lock"  # The module that owns `connect_lock_store`.
PROBE_COLLECTION = "upgrade_readiness"  # A scratch collection, apart from the three record collections.
PROBE_KEY = "readyz"  # One fixed key, so the probe never grows the collection.
PROBE_FIELD = "checked_at"  # The field that carries the fresh value of one probe.
PROBE_LOCK_KEY = "misthelper:readyz:probe"  # The scratch key inside the lock store namespace.
PROBE_LOCK_TTL_SECONDS = 60  # The lock store drops the scratch key when no probe renews it.
READINESS_CACHE_SECONDS = 5  # How long one readiness answer serves every caller. See `read_readiness`.
READINESS_CACHE_KEY = "answer"  # The one key of the cache below. The process holds one answer, never a set.

# WHY 12 hours: the lock renewal beat posts every 60 seconds, and a post carries
# the token. `flask-wtf` defaults this value to 3600 seconds, which is the same
# length as `LOCK_TTL_SECONDS`. The two therefore expired together, every beat
# after the first hour answered 400, and the site lock died with no renewal. A
# real cascade runs longer than one hour, because the settle gate allows 60
# minutes for each device, so the token must outlive the work. Issue #2110
# records a portal log that held 228 refusals, one each minute.
CSRF_TOKEN_SECONDS = 43200  # 12 hours. The token must outlive the longest upgrade.

THEME_ARGUMENT = "theme"  # The GET form of `partials/nav.html` sends the choice under this name.
THEME_DEFAULT = "magenta"  # The dark brand theme. An operator with no choice sees this one.
THEMES_KEY = "THEMES"  # `apply_web_config` writes the configured names under this key.
DARK_THEMES = frozenset({"magenta"})  # Every shipped theme that paints a dark page.
DARK_SCHEME = "dark"  # The `data-bs-theme` value that switches Bootstrap to its dark set.
LIGHT_SCHEME = "light"  # The `data-bs-theme` value of every other theme.


def read_version() -> str:
    """Read the version of the installed distribution.

    Why:
        A developer runs the portal from a working copy that holds no installed
        distribution. The health endpoint must still answer, so a missing
        distribution returns a plain word instead of a fault.

    Returns:
        The version text, or the word `unknown`.
    """
    try:  # A working copy often holds no installed distribution.
        return version(DISTRIBUTION_NAME)  # The normal path inside the container.
    except PackageNotFoundError:  # The distribution is not installed.
        return UNKNOWN_VERSION  # The health endpoint must still answer.


PORTAL_VERSION = read_version()  # Read once at import, because the version cannot change while the portal runs.


class RunContextFilter(logging.Filter):
    """Give every log record a run field and a site field.

    Why:
        Several operators share one log file, so a reader must follow one run
        through the noise. The format string names both fields, and a record
        without them would raise a formatting fault. This filter supplies the
        placeholder value for a record that carries neither field.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add the two context fields to one record.

        Args:
            record: The record on its way to the handler.

        Returns:
            True, because this filter drops no record.
        """
        record.__dict__.setdefault(RUN_FIELD, MISSING_FIELD)  # Keep a value the caller already set.
        record.__dict__.setdefault(SITE_FIELD, MISSING_FIELD)  # Keep a value the caller already set.
        return True  # A False answer would drop the record.


def configure_logging() -> None:
    """Attach the portal log handler to the package logger.

    Why:
        The portal writes the run identifier and the site identifier on every
        line, and the root handler of the host process knows neither field. The
        package logger therefore owns its own handler and stops propagation.

        A test builds the application many times in one process. The name check
        stops the handler count from growing with each build.
    """
    package_logger = logging.getLogger(PACKAGE_NAME)  # Every module logger sits under this one.
    if any(handler.get_name() == HANDLER_NAME for handler in package_logger.handlers):  # Already armed.
        return  # A second build must not add a second handler.
    package_logger.addHandler(build_log_handler())  # The handler that knows the two extra fields.
    package_logger.setLevel(logging.INFO)  # Debug records stay off in normal operation.
    package_logger.propagate = False  # The root handler knows neither field and would fail to format.


def build_log_handler() -> logging.Handler:
    """Build the stream handler that writes the portal format.

    Returns:
        The handler, named and ready to attach.
    """
    handler: logging.Handler = logging.StreamHandler()  # The container reads the standard error stream.
    handler.set_name(HANDLER_NAME)  # The name lets a second build find this handler.
    handler.setFormatter(logging.Formatter(LOG_FORMAT))  # The format names both context fields.
    handler.addFilter(RunContextFilter())  # The filter supplies a value for a record without them.
    return handler  # The caller attaches it to the package logger.


def build_error_envelope(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the one error shape that every JSON endpoint returns.

    Why:
        The contract allows one shape and no other. One builder keeps every
        handler on that shape. A test asserts on `code` and never on `message`,
        so the code stays a fixed lower-case word.

    Args:
        code: The fixed lower-case error code.
        message: One plain sentence for the operator.
        details: Optional extra facts. The value holds no credential.

    Returns:
        The envelope, ready for `jsonify`.
    """
    body: dict[str, Any] = {"code": code, "message": message}  # The two keys the contract always requires.
    if details is not None:  # The third key is optional.
        body["details"] = details  # An empty dict is still a caller choice, so test against None.
    return {"error": body}  # The contract wraps the body under one key.


def json_error(status: int, code: str | None = None, message: str | None = None) -> tuple[Response, int]:
    """Build one JSON error response.

    Args:
        status: The HTTP status code.
        code: The error code. The status supplies the default.
        message: The sentence for the operator. The status supplies the default.

    Returns:
        The response body and the status code.
    """
    chosen_code = code or ERROR_CODES.get(status, ERROR_CODES[500])  # An unknown status reads as a fault.
    chosen_message = message or ERROR_MESSAGES.get(status, ERROR_MESSAGES[500])  # The matching sentence.
    return jsonify(build_error_envelope(chosen_code, chosen_message)), status  # The one shape, every time.


def handle_error(status: int, error: Exception) -> tuple[Response, int]:
    """Answer one fault with the bound status code.

    Why:
        `functools.partial` binds the status to this function for each code. A
        closure built inside a loop would capture the loop variable instead, and
        every handler would then answer with the last status.

    Args:
        status: The HTTP status code to answer with.
        error: The fault that Flask caught.

    Returns:
        The error envelope and the status code.
    """
    logger.info(
        "The portal answered the status %s after the fault %s.",  # The class name only, never the message.
        status,
        type(error).__name__,
    )
    response, code = json_error(status)  # The status supplies the code and the sentence.
    copy_allow_header(error, response)  # A 405 answer must still name the methods the path accepts.
    return response, code


def copy_allow_header(error: Exception, response: Response) -> None:
    """Copy the `Allow` header from a refused-method fault onto the answer.

    Why:
        HTTP requires a 405 answer to name the methods that the path accepts.
        Werkzeug builds that header for its own HTML page, and the JSON envelope
        is a fresh response that inherits none of it. Without this copy the
        portal would answer a valid envelope inside an invalid HTTP message. A
        client could not then learn which method to send instead.

    Args:
        error: The fault that Flask caught.
        response: The envelope answer on its way to the caller.
    """
    methods = getattr(error, "valid_methods", None)  # Werkzeug sets this on a refused-method fault only.
    if methods:  # Every other fault carries no method list at all.
        response.headers["Allow"] = ", ".join(methods)  # The header that HTTP requires on a 405 answer.


def register_error_handlers(app: Flask) -> None:
    """Register one JSON handler for each documented status code.

    Args:
        app: The application to fit the handlers to.
    """
    for status in ERROR_CODES:  # One handler for each documented status.
        app.register_error_handler(status, partial(handle_error, status))  # `partial` binds the status.


def register_health(app: Flask) -> None:
    """Register the health endpoint.

    Why:
        The container probe calls this endpoint many times each minute. The
        endpoint therefore reads no database and holds no session, so a database
        fault never stops the container from starting.

    Args:
        app: The application to add the route to.
    """

    @app.get("/healthz")  # The container probe calls this path.
    def healthz() -> tuple[Response, int]:
        """Report that the portal process answers.

        Returns:
            The status word and the portal version.
        """
        return jsonify({"status": "ok", "version": PORTAL_VERSION}), HEALTH_STATUS  # No database call.


def probe_stamp() -> str:
    """Build one fresh value for a scratch write.

    Why:
        A read-back proves a write only when the written value differs from the
        value of the last probe. A fixed value would match a stale document and
        would report the store ready after every write had failed.

    Returns:
        The monotonic clock reading as text.
    """
    return str(monotonic_ns())  # The monotonic clock never repeats and never steps backward.


def verify_document_write(database: Any) -> bool:
    """Write one scratch document and read the same key back.

    Why:
        A check that only opens a connection reports ready while every write
        fails. See `specs/1823-upgrade-capture-portal/quickstart.md` section 12
        and issue #1824. The probe therefore writes a value and reads it back.

        The probe uses one scratch collection and one fixed key. The readiness
        traffic never grows the stored data. It never mixes with the capture
        records or the run records.

    Args:
        database: The open document store handle from `connect_database`.

    Returns:
        True when the read-back returned the value that the probe wrote.
    """
    if not database.has_collection(PROBE_COLLECTION):  # The first probe against a fresh database.
        database.create_collection(PROBE_COLLECTION)  # A scratch collection of its own.
    collection = database.collection(PROBE_COLLECTION)  # The handle for the write and the read.
    stamp = probe_stamp()  # A fresh value, so a stale document cannot pass the check.
    document = {"_key": PROBE_KEY, PROBE_FIELD: stamp}  # One key, written again by each probe.
    collection.insert(document, overwrite_mode="replace")  # The write the check must prove.
    found = collection.get(PROBE_KEY)  # The read-back that proves the write landed.
    return bool(found is not None and found.get(PROBE_FIELD) == stamp)  # A stale value reads as a failure.


def verify_lock_write(client: Any) -> bool:
    """Write one scratch key into the lock store and read it back.

    Why:
        A ping proves that the socket answers. The portal writes the site lock
        into this store, so the probe writes a key as well. A read-only replica
        answers a ping and refuses every write. The site lock would then fail for
        every operator while the probe reported the store ready.

    Args:
        client: The open lock store client from `connect_lock_store`.

    Returns:
        True when the read-back returned the value that the probe wrote.
    """
    stamp = probe_stamp()  # A fresh value, so a stale key cannot pass the check.
    client.set(PROBE_LOCK_KEY, stamp, ex=PROBE_LOCK_TTL_SECONDS)  # The expiry clears the key on its own.
    return bool(client.get(PROBE_LOCK_KEY) == stamp)  # The client decodes the answer, so compare text.


def probe_document_store() -> str:
    """Report whether the document store accepts a write and returns it.

    Why:
        This function catches every fault, because a probe that raises turns a
        readiness check into a 500 answer. The connection helper owns the socket
        and sets a ten-second request bound. This function opens no socket of its
        own. No probe holds a worker thread longer than that bound.

    Returns:
        The word `ok`, or the word `unreachable` for any failure.
    """
    try:  # No fault may leave this function.
        store = import_module(STORE_MODULE)  # Late, so a missing dependency cannot stop the portal starting.
        database = store.connect_database()  # The helper answers None for a store that did not open.
        if database is None:  # Standalone mode, or the server did not answer.
            return STORE_DOWN  # Name the store, never the host.
        return STORE_OK if verify_document_write(database) else STORE_DOWN  # The write must land.
    except Exception as fault:  # A readiness check must answer, whatever the store did.
        logger.warning(
            "The readiness probe could not verify the document store: %s.",  # The class name only.
            type(fault).__name__,
        )
        return STORE_DOWN  # The body names this store, so the operator knows where to look.


def probe_lock_store() -> str:
    """Report whether the lock store accepts a write and returns it.

    Why:
        This function catches every fault, for the same reason as the document
        store probe. The connection helper sets a one-second connect timeout
        and a two-second command timeout, so this probe opens no socket itself.

    Returns:
        The word `ok`, or the word `unreachable` for any failure.
    """
    try:  # No fault may leave this function.
        lock = import_module(LOCK_MODULE)  # Late, so a missing dependency cannot stop the portal starting.
        client = lock.connect_lock_store()  # The helper answers None for a store that did not open.
        if client is None:  # The lock store did not answer, or the last failure is still inside the cooldown.
            return STORE_DOWN  # Name the store, never the host.
        return STORE_OK if verify_lock_write(client) else STORE_DOWN  # The write must land.
    except Exception as fault:  # A readiness check must answer, whatever the store did.
        logger.warning(
            "The readiness probe could not verify the lock store: %s.",  # The class name only.
            type(fault).__name__,
        )
        return STORE_DOWN  # The body names this store, so the operator knows where to look.


def probe_readiness() -> tuple[dict[str, str], int]:
    """Probe both stores and build the readiness answer.

    Why:
        An operator who reads the words `not_ready` with no further detail
        learns nothing. The body therefore carries one reading for each store,
        so the operator knows which store to repair.

        This is the uncached form. It writes to both stores on every call, so
        no route may call it directly. The `read_readiness` function is the entry
        point that the endpoint uses. It bounds how often this function runs.

    Returns:
        The readiness body and the HTTP status code.
    """
    database_state = probe_document_store()  # The document store holds every capture and every run.
    lock_state = probe_lock_store()  # The lock store holds the site lock.
    ready = database_state == STORE_OK and lock_state == STORE_OK  # Ready means every store answered.
    body = {
        STATUS_FIELD: READY_WORD if ready else NOT_READY_WORD,  # The summary word the contract names.
        DATABASE_FIELD: database_state,  # The reading of the document store.
        REDIS_FIELD: lock_state,  # The reading of the lock store.
    }
    return body, READY_STATUS if ready else NOT_READY_STATUS  # One failed store answers 503.


# WHAT: the one readiness answer of this process, and the monotonic second the
#       portal obtained it.
# WHY:  a dict, not two module names, because a function that rebinds a module
#       name needs the `global` statement and a function that mutates a
#       container needs nothing. The lock guards the pair below, so two threads
#       cannot probe the stores at the same moment.
_readiness_cache: dict[str, tuple[float, dict[str, str], int]] = {}
_readiness_lock = threading.Lock()


def reset_readiness_cache() -> None:
    """Drop the cached readiness answer.

    Why:
        The cache lives for the life of the process. A test that installs a
        stand-in store would otherwise read the answer that an earlier test
        obtained. The `register_readiness` function calls this for each new
        application. A test calls it to force a fresh probe.
    """
    with _readiness_lock:  # A caller may reset while another thread reads.
        _readiness_cache.clear()  # The next call probes both stores again.


def read_readiness() -> tuple[dict[str, str], int]:
    """Answer from the cache, or probe both stores and cache the answer.

    Why:
        `GET /readyz` carries no session guard, because an orchestrator probe
        cannot sign in. Without a bound, every request that reaches the port
        drives one document store write and one lock store write. A caller can
        then load both stores at the rate it can open sockets.

        The bound is a short cache, not an address list and not the removal of
        the write probe. The write probe must stay. A read-only replica answers
        a ping and refuses every write. The site lock would then fail for
        every operator while the probe reported the store ready.

        The window is shorter than the interval an orchestrator uses, so a
        genuine probe always finds the entry expired and always does real work.
        The container ships no health check of its own. The two store
        containers in `compose.yml` probe every 10 seconds. So 5 seconds sits
        below the shortest interval this repository states. A flood collapses
        to one probe pair for each window.

        The lock also removes a thundering herd. While one thread probes, the
        others wait and then read the value it wrote, so four worker threads
        drive one probe pair instead of four.

    Returns:
        The readiness body and the HTTP status code.
    """
    with _readiness_lock:  # One probe at a time, for the herd as much as for the entry.
        cached = _readiness_cache.get(READINESS_CACHE_KEY)  # None before the first probe.
        if cached is not None and monotonic() - cached[0] < READINESS_CACHE_SECONDS:
            return dict(cached[1]), cached[2]  # A copy, so no caller can edit the stored answer.
        body, status = probe_readiness()  # The stores answer, or the probe reports them down.
        # The stamp comes after the probe, never before. A thread that waited
        # behind a slow probe would otherwise read a stamp older than its own
        # wait and probe again, which is the herd this lock removes.
        _readiness_cache[READINESS_CACHE_KEY] = (monotonic(), body, status)
        return dict(body), status  # A copy, for the same reason as above.


def register_readiness(app: Flask) -> None:
    """Register the readiness endpoint.

    Why:
        `GET /healthz` reports that the process is alive. `GET /readyz` reports
        that the dependencies answer. An orchestrator needs both, because a
        process that lives but cannot reach its stores must leave the load
        balancer without a restart.

        The body carries no host name, no password, and no connection string.
        The `store._safe_host` helper exists because a connection string holds a
        password. The safest body is the one that names no host at all. The two
        fixed words `ok` and `unreachable` name the store, never the address.

        The readiness cache lives for the life of the process, so a new
        application must not inherit the answer of an earlier one. A new
        application means new settings and possibly new store addresses, and an
        answer obtained under the old settings would describe the wrong stores.

    Args:
        app: The application to add the route to.
    """
    reset_readiness_cache()  # A new application starts with no answer of its own.

    @app.get("/readyz")  # The orchestrator readiness probe calls this path.
    def readyz() -> tuple[Response, int]:
        """Report whether both stores accept a write and return it.

        Returns:
            The readiness body and the status code.
        """
        body, status = read_readiness()  # Neither probe raises, so this view never answers a 500.
        return jsonify(body), status  # A flat object, never the error envelope.


def register_teardown(app: Flask) -> None:
    """Register the handler that closes the per-request handles.

    Why:
        A request may open a cloud session, a database router, or a Redis
        client. Each one holds a socket. Without this handler the sockets pile
        up under load and the portal runs out of file handles.

    Args:
        app: The application to add the handler to.
    """

    @app.teardown_appcontext  # The hook runs after the response leaves, on success and on fault.
    def close_context(error: BaseException | None) -> None:
        """Close every handle the request left behind.

        Args:
            error: The fault that ended the request, or None.
        """
        for name in REQUEST_HANDLES:  # One pass over the fixed handle list.
            close_handle(name, g.pop(name, None))  # `pop` clears the slot, so a later read finds nothing.
        if error is not None:  # The request ended with a fault.
            logger.debug("The request context closed after the fault %s.", type(error).__name__)  # Trace only.


def close_handle(name: str, handle: object | None) -> None:
    """Close one request handle and swallow a close fault.

    Why:
        The teardown runs while a request already failed. A second fault inside
        the teardown would hide the first one, so this function reports the
        close fault and continues.

    Args:
        name: The name of the handle, for the log line.
        handle: The object to close, or None.
    """
    closer = getattr(handle, "close", None)  # A None handle and an open one take the same path.
    if not callable(closer):  # The slot was empty, or the object closes itself.
        return  # Nothing to do.
    try:  # The socket may already be broken.
        closer()  # The object releases its socket.
    except Exception:  # A close fault must not hide the fault that ended the request.
        logger.warning("The portal could not close the handle %s.", name)  # Report and continue.


def import_route_module(name: str) -> ModuleType | None:
    """Import one route module and survive a module that does not exist yet.

    Why:
        The portal grows in stages. A route module that Phase 3 has not written
        must not stop the shell from starting.

    Args:
        name: The module name inside the routes package.

    Returns:
        The module, or None when the import failed.
    """
    try:  # The module may not exist yet.
        return import_module(f"{ROUTES_PACKAGE}.{name}")  # The late import keeps the shell startable.
    except ImportError as fault:  # A missing module is expected while the portal grows.
        logger.warning(
            "The portal could not import the route module %s: %s.",  # Expected while the portal grows.
            name,
            fault,
        )
        return None  # The caller skips this blueprint and registers the rest.


def find_blueprint(module: ModuleType, name: str) -> Blueprint | None:
    """Find the blueprint object inside one route module.

    Args:
        module: The imported route module.
        name: The module name, used to build the first candidate.

    Returns:
        The blueprint, or None when the module publishes none.
    """
    for pattern in BLUEPRINT_ATTRIBUTES:  # The first match wins.
        candidate = getattr(module, pattern.format(name=name), None)  # A missing name reads as None.
        if isinstance(candidate, Blueprint):  # Guard against a name that holds something else.
            return candidate  # The first known name that holds a blueprint wins.
    return None  # The module publishes no blueprint under any known name.


def register_one_blueprint(app: Flask, name: str) -> None:
    """Import one route module and register its blueprint.

    Args:
        app: The application to register the blueprint on.
        name: The module name inside the routes package.
    """
    module = import_route_module(name)  # A module that does not exist yet returns None.
    if module is None:  # The import failed and already wrote a warning.
        return  # Skip this stage and keep the portal running.
    blueprint = find_blueprint(module, name)  # Look under each known attribute name.
    if blueprint is None:  # The module imported but published nothing.
        logger.warning(
            "The route module %s holds no blueprint. The portal skipped it.",  # A build fault, not a stage gap.
            name,
        )
        return  # Skip this stage and keep the portal running.
    app.register_blueprint(blueprint)  # The blueprint carries its own URL prefix.


def register_blueprints(app: Flask) -> None:
    """Register every route module that exists today.

    Args:
        app: The application to register the blueprints on.
    """
    for name in BLUEPRINT_NAMES:  # The five stages of the operator journey.
        register_one_blueprint(app, name)  # A missing module writes a warning and does not stop the loop.


def apply_portal_config(app: Flask, settings: PortalSettings) -> None:
    """Copy the portal settings into the Flask configuration.

    Why:
        A route module reads the poll rate and the theme list from
        `current_app.config`, so the module needs no import of this factory.

    Args:
        app: The application to configure.
        settings: The settings read from the environment.
    """
    app.config["SECRET_KEY"] = settings.web.secret_key  # Flask signs the session cookie with this key.
    app.config["PORTAL_SETTINGS"] = settings  # The whole frozen record, for a route that needs more.
    app.config["POLL_INTERVAL_SECONDS"] = settings.web.poll_interval_seconds  # The page reads this value.
    app.config["THEMES"] = list(settings.web.themes)  # A list, because a template iterates it.
    app.config["BROWSER_TOKEN_SIGNIN_ALLOWED"] = not settings.web.environment_token_present
    app.config["WTF_CSRF_TIME_LIMIT"] = CSRF_TOKEN_SECONDS  # The beat must outlive the lock it renews.


def apply_cookie_config(app: Flask, settings: PortalSettings) -> None:
    """Set the session cookie rules.

    Why:
        A session cookie carries the identity that the site lock grants a site
        to. A cookie that leaves the browser in clear text hands a site to
        whoever reads the wire.

        The `Secure` flag follows the trusted proxy count and nothing else.
        That count already decides whether the portal reads the forwarded
        scheme, so one setting drives both and the two can never disagree. A
        portal behind a terminating proxy answers on HTTPS and marks the
        cookie. A direct listener on plain HTTP inside the lab network leaves
        the flag off. A marked cookie would never reach the browser. Every
        operator would then lose the session at the first page.

    Args:
        app: The application to configure.
        settings: The settings that carry the trusted proxy count.
    """
    behind_proxy = settings.proxy.trusted_hops > 0  # The same count that drives `ProxyFix(x_proto=...)`.
    app.config["SESSION_COOKIE_HTTPONLY"] = True  # A script cannot read the session cookie.
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # A cross-site post carries no session cookie.
    app.config["SESSION_COOKIE_SECURE"] = behind_proxy  # A terminating proxy answers on HTTPS.
    logger.info("The session cookie carries the secure flag: %s.", behind_proxy)  # State the reading once.


def build_application(settings: PortalSettings) -> Flask:
    """Build the bare Flask object with the asset folders and the configuration.

    Args:
        settings: The settings read from the environment.

    Returns:
        The configured application, before any route or guard.
    """
    app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)  # Package assets.
    apply_portal_config(app, settings)  # The settings must land before any guard reads them.
    apply_cookie_config(app, settings)  # The cookie rules travel with the session key.
    return app  # The caller arms the object next.


def allowed_themes() -> tuple[str, ...]:
    """Return the theme names that this portal offers.

    Why:
        The operator names the themes with `CAPTURE_THEMES`. The `read_themes`
        function drops any name that a file path must not carry. The
        `apply_web_config` function then writes the checked names to the
        application. A second hard coded list here would ignore the setting. A
        theme the operator added would show in the picker and then refuse to
        load.

    Returns:
        The configured names, or the shipped names outside an application.
    """
    if has_app_context():  # A render outside an application reaches no configuration.
        names = current_app.config.get(THEMES_KEY)  # Written by `apply_web_config`, already checked.
        if names:  # An empty list would leave the operator with no theme at all.
            return tuple(names)
    return DEFAULT_THEMES  # The two stylesheets that the portal ships.


def default_theme() -> str:
    """Return the theme name that a request with no choice reads.

    Why:
        An operator names the themes with `CAPTURE_THEMES` and may leave the
        brand theme out. The `THEME_DEFAULT` name would then point to a
        stylesheet that this portal refuses to serve. Every page would fall back
        inside the template instead. This read stays inside the configured list,
        so the Python answer and the template answer always agree.

    Returns:
        The brand theme when the portal offers it, or the first offered name.
    """
    names = allowed_themes()  # Already checked by `read_themes`, and never empty.
    if THEME_DEFAULT in names:  # The normal deployment ships the brand theme.
        return THEME_DEFAULT
    return names[0]  # An operator dropped the brand theme, so the first name wins.


def theme_scheme(name: str) -> str:
    """Return the Bootstrap color scheme of one theme.

    Why:
        Bootstrap draws its own controls, its form fields, and its vendored
        control graphics from the `data-bs-theme` attribute. A theme file
        changes the portal colors alone. A Bootstrap selection list would then
        stay white on a near black page. The `layout.html` template writes this
        answer onto the html element. That write switches those controls with
        the theme.

    Args:
        name: The theme name that the request resolved to.

    Returns:
        The word `dark` for a dark theme, or the word `light`.
    """
    if name in DARK_THEMES:  # A dark theme needs the dark control set as well.
        return DARK_SCHEME
    return LIGHT_SCHEME  # Every other theme keeps the light control set.


def chosen_theme() -> str:
    """Return the theme name of the current request.

    Why:
        The theme picker in `partials/nav.html` is a GET form, because the
        content security policy blocks an inline script. The form reloads the
        page with `?theme=<name>`, so something must read that argument back.
        Without this read the picker changes nothing and a second theme stays
        unreachable.

    Returns:
        The name the operator picked, or the default name for any other value.
    """
    if not has_request_context():  # A render outside a request carries no argument at all.
        return default_theme()
    asked = request.args.get(THEME_ARGUMENT, "")  # Operator input, so no path may come from it.
    if asked in allowed_themes():  # A configured name only. `layout.html` repeats this guard.
        return asked
    return default_theme()  # An unknown name reads as the default, never as a file path.


def register_theme_context(app: Flask) -> None:
    """Give every template the theme name, the theme list, and the color scheme.

    Why:
        One processor serves every page, so no route can forget the group and
        render a picker that does nothing. A route that passes its own `theme`
        still wins, because Flask applies the explicit context last.

    Args:
        app: The application to add the processor to.
    """

    @app.context_processor
    def theme_context() -> dict[str, Any]:
        """Answer the three names that `layout.html` and `partials/nav.html` read.

        Returns:
            The chosen theme name, the list of allowed names, and the Bootstrap
            color scheme of the chosen theme.
        """
        # The list comes from the configuration, which `read_themes` already
        # checked. Operator request input never reaches `themes`, because the
        # templates test the chosen name against this list.
        name = chosen_theme()
        return {THEME_ARGUMENT: name, "themes": list(allowed_themes()), "theme_scheme": theme_scheme(name)}


def arm_application(app: Flask, settings: PortalSettings) -> None:
    """Add the guards, the error handlers, the routes, and the seams.

    Why:
        The seams register last, because `install_seams` fills a gap with
        `setdefault` and must never replace a value that an earlier caller chose.

    Args:
        app: The application to arm.
        settings: The settings read from the environment.
    """
    PortalSecurity().apply(app, settings)  # The guards register first, so they run before any view.
    register_error_handlers(app)  # The JSON envelope must cover a fault the guards raise.
    register_health(app)  # The container probe needs this route from the first day.
    register_readiness(app)  # The orchestrator readiness probe needs the store reading.
    register_teardown(app)  # Every request must release its sockets.
    register_theme_context(app)  # Without this the theme picker of the navigation changes nothing.
    register_blueprints(app)  # A route module that does not exist yet writes one warning.
    install_seams(app)  # Without this the confirmed run reads no launcher and sends nothing.


def create_app() -> Flask:
    """Build the upgrade capture portal application.

    Why:
        This function takes no argument, because `wsgi_capture.py` and the menu
        238 launcher both call it with an empty argument list. Every setting
        comes from the process environment inside `load_settings`.

    Returns:
        The application, ready for Gunicorn or for the development server.
    """
    configure_logging()  # The log format must be in place before the first record.
    settings = load_settings()  # The environment is the only source of a setting.
    app = build_application(settings)  # The bare object with the configuration.
    arm_application(app, settings)  # The guards, the handlers, and the routes.
    logger.info(
        "The upgrade capture portal is ready for the port %s.",  # The first line of a healthy start.
        settings.web.port,
    )
    return app  # Gunicorn reads this object from `wsgi_capture:app`.
