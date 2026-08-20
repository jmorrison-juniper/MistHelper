"""The application factory for the upgrade capture portal.

Why:
    Two callers start this portal and neither passes an argument.
    `wsgi_capture.py` builds the Gunicorn target and the menu 238 launcher in
    `MistHelper.py` builds the same object. `create_app` therefore takes no
    argument and reads every setting from the process environment.

    The factory imports each route module late, inside `create_app`, and treats
    an `ImportError` as survivable. The portal is built in stages, so a route
    module can arrive after the shell. A missing module writes one warning and
    the portal starts with the routes that exist. `GET /healthz` answers from
    the first day, because the container health check needs it.
"""

import logging  # The portal logs with the standard library only.
from functools import partial  # Binds one status code to the shared error handler.
from importlib import import_module  # Imports each route module late.
from importlib.metadata import PackageNotFoundError, version  # Reads the version for the health answer.
from pathlib import Path  # Builds the asset paths from the module location.
from types import ModuleType  # The return type of a late import.
from typing import Any  # The error envelope holds free-form details.

from flask import Blueprint, Flask, Response, g, jsonify  # The web framework surface the factory needs.

from .config import PortalSettings, load_settings  # The settings record and the environment reader.
from .security import PortalSecurity  # The guards that arm the application.

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
BLUEPRINT_NAMES = ("auth", "select", "capture", "upgrade", "review")  # The registration order.

# Each route module publishes its blueprint under one of these names. The first
# match wins, so a module needs no registration list of its own.
BLUEPRINT_ATTRIBUTES = ("{name}_bp", "bp", "blueprint")  # Tried in this order.

REQUEST_HANDLES = ("mist_session", "database_router", "redis_client")  # The teardown closes each one.

ERROR_CODES = {
    400: "bad_request",  # The portal could not read the request.
    401: "not_authenticated",  # The contract names this code, not `unauthorized`.
    403: "forbidden",  # The session may not act on that organization or site.
    404: "not_found",  # No such record.
    405: "method_not_allowed",  # The path exists and refuses this method.
    409: "conflict",  # Another operator holds the site lock.
    429: "rate_limited",  # The cloud rate limit stopped the portal.
    500: "server_error",  # An unexpected fault.
}

ERROR_MESSAGES = {
    400: "The portal could not read the request.",  # A test asserts on the code, never on this text.
    401: "Sign in to continue.",  # The sign-in page is the next step.
    403: "This session may not act on that organization or site.",  # The scope check refused the call.
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
        portal would answer a valid envelope inside an invalid HTTP message, and
        a client could not learn which method to send instead.

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


def apply_cookie_config(app: Flask) -> None:
    """Set the session cookie rules.

    Why:
        The portal runs on plain HTTP inside the lab network, so the secure flag
        stays off. A secure cookie would never reach the browser and every
        operator would lose the session at the first page.

    Args:
        app: The application to configure.
    """
    app.config["SESSION_COOKIE_HTTPONLY"] = True  # A script cannot read the session cookie.
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # A cross-site post carries no session cookie.


def build_application(settings: PortalSettings) -> Flask:
    """Build the bare Flask object with the asset folders and the configuration.

    Args:
        settings: The settings read from the environment.

    Returns:
        The configured application, before any route or guard.
    """
    app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)  # Package assets.
    apply_portal_config(app, settings)  # The settings must land before any guard reads them.
    apply_cookie_config(app)  # The cookie rules travel with the session key.
    return app  # The caller arms the object next.


def arm_application(app: Flask, settings: PortalSettings) -> None:
    """Add the guards, the error handlers, and the routes.

    Args:
        app: The application to arm.
        settings: The settings read from the environment.
    """
    PortalSecurity().apply(app, settings)  # The guards register first, so they run before any view.
    register_error_handlers(app)  # The JSON envelope must cover a fault the guards raise.
    register_health(app)  # The container probe needs this route from the first day.
    register_teardown(app)  # Every request must release its sockets.
    register_blueprints(app)  # A route module that does not exist yet writes one warning.


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
