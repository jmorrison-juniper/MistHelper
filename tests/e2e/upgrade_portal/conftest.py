"""Browser fixtures for the upgrade capture portal tests.

Why:
    A browser test drives a full operator journey through a real server. It
    finds the defects that a unit test and a contract test cannot find, such
    as a broken template or a script that fails in the browser.

    The server fixture starts its own portal and never joins one it finds.
    Only a portal that the fixture started carries the sign-in seam and the
    cookie key of this run, so a portal from another window makes every page
    answer 401. The fixture reports a skip only when the workstation can run
    no WSGI server at all.

    ``src/upgrade_portal/runtime/server.py`` picks the server for the platform.
    Gunicorn stays the server for the Linux target and for the container.
    Windows takes Waitress, because Gunicorn imports ``fcntl`` and Windows
    ships no such module.

    The Playwright settings live in ``playwright.config.py`` beside this file.
    That file name holds a dot, so no module can import it by name. This
    module loads it by path.

    The ``page`` fixture carries a portal session. Every page below the sign-in
    form calls ``identity.require_session``, so a page with no session reads
    401. A real sign-in would send a password to a live Mist tenant, which no
    test may do. This module signs a session cookie instead, and the server
    process registers the matching record at start-up. Both halves are needed,
    because ``identity.SESSION_REGISTRY`` is a dictionary inside one process
    and the test process cannot write into the memory of the server process.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import socket
import subprocess
import tempfile
import time
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path
from typing import Any

import flask
import pytest
from flask.sessions import SecureCookieSessionInterface

from src.upgrade_portal.app.config import DEFAULT_PORT, PORT_VARIABLE, SECRET_KEY_VARIABLE, read_port
from src.upgrade_portal.runtime import identity
from src.upgrade_portal.runtime.server import build_server_command

logger = logging.getLogger(__name__)

# WHY: The portal reads CAPTURE_PORT and falls back to 8056, next to the
# existing portal on port 8055. The tests read the same variable through the
# same reader, so a changed port moves the server and the browser together.
CAPTURE_PORT = read_port(PORT_VARIABLE, DEFAULT_PORT)
LOOPBACK_HOST = "127.0.0.1"  # Loopback only. No test reaches an outside host.
BASE_URL = f"http://{LOOPBACK_HOST}:{CAPTURE_PORT}"

# WHY: Gunicorn and Waitress both load a target of this shape. `wsgi_capture.py`
# holds `wsgi_capture:app` and stays the production target of this portal. The
# browser tests load the target below instead, because the signed-in record must
# live inside the server process and no test process can reach that memory.
WSGI_TARGET = "tests.e2e.upgrade_portal.conftest:app"

# WHY: The root conftest changes the working directory for each test, so the
# server needs an explicit directory to find wsgi_capture.py.
REPO_ROOT = Path(__file__).parents[3]

# WHY: The settings file sits beside this module. A path load is the only way
# to read a file whose name holds a dot.
CONFIG_PATH = Path(__file__).with_name("playwright.config.py")
CONFIG_MODULE_NAME = "upgrade_portal_playwright_config"

# WHY: 20 tries of 0.5 seconds gives the same 10-second budget as the fixture
# at tests/e2e/conftest.py:86.
READY_TRIES = 20
READY_PAUSE_SECONDS = 0.5
PROBE_TIMEOUT_SECONDS = 0.5  # One connection attempt against a port that may hold no listener.
STOP_TIMEOUT_SECONDS = 5  # The same 5-second budget as tests/e2e/conftest.py:99.

# WHY: The server runs for the whole session and logs one record for each
# request. A pipe holds 64 KB on Windows, and nothing drains it while the tests
# run. A full pipe blocks the writer, so a server given a pipe stops answering
# partway through a run and every later page reports a refused connection. A
# file never blocks the writer, and the skip message reads the same file back.
SERVER_LOG_PATH = Path(tempfile.gettempdir()) / f"upgrade_portal_e2e_{CAPTURE_PORT}.log"

# WHY: Only a portal that this fixture started carries the sign-in seam and the
# cookie key of this run. A portal left running in another window carries
# neither, so every page below the sign-in form answers 401 and every test
# skips. A whole run then reports success while it opened no page. A stray
# listener is a fault of the workstation, and the fixture names it.
STRAY_LISTENER_MESSAGE = (
    f"Another process already listens on port {CAPTURE_PORT}. "
    "The browser tests must start their own portal, because only that portal holds the sign-in seam. "
    f"Stop the process that holds port {CAPTURE_PORT}, then run the tests again."
)

# WHY: A workstation that can run no WSGI server describes the workstation and
# never the page under test, so this one state stays a skip.
NO_SERVER_MESSAGE = "No WSGI server can run on this workstation, so no browser test can open a page."

# WHY: A portal that started and never answered is a real fault, such as a
# failed import or a bound port. A skip would hide it behind a green run.
START_FAILED_MESSAGE = (
    f"The capture portal did not answer on port {CAPTURE_PORT}. Read {SERVER_LOG_PATH} for the cause."
)

# WHY: The sign-in seam at the foot of this module builds a signed-in session.
# That seam must never run in a production start, so it reads one variable that
# only `_child_environment` writes, and it writes that variable into the child
# process alone. No shipped file names this variable, so no deployment can set
# it by accident and no operator start of `wsgi_capture.py` can reach the seam.
E2E_SESSION_VARIABLE = "UPGRADE_PORTAL_E2E_SESSION"  # The gate. `_child_environment` is the only writer.
E2E_SESSION_ENABLED = "1"  # The one value that opens the gate. Any other value keeps it shut.

# WHY: The test process signs the cookie and the server process reads it back,
# so both must hold one key. A fixed test key never leaves loopback, and the
# child environment carries it, so no shipped setting and no `.env` file is read.
TEST_SECRET_KEY = "upgrade-portal-e2e-cookie-signing-key"  # A test value. No production server reads it.
COOKIE_APP_NAME = "upgrade_portal_e2e_cookie"  # Names the bare Flask object that signs, and never serves.
SESSION_COOKIE_NAME = "session"  # Flask's default name. `factory.create_app` sets no other name.

# WHY: `identity.SessionOwner` checks both halves of the pair. The address is
# already in its normalized form, and the reserved `.invalid` domain can reach
# no mail host. The browser identifier holds 22 characters of the allowed set.
STAND_IN_EMAIL = "e2e.operator@example.invalid"  # Lower case, so `normalize_email` leaves it unchanged.
STAND_IN_BROWSER_ID = "e2eBrowserIdentity0001"  # Matches the browser cookie pattern that identity fixes.

# WHY: The site lock identifies a holder by the pair of the work address and the
# browser identifier. A test of two operators therefore needs a second pair that
# differs in both halves, and the server must hold a record for it. Both values
# below are as fake as the pair above, and neither one reaches a mail host.
SECOND_EMAIL = "e2e.second.operator@example.invalid"  # A second address, already normalized.
SECOND_BROWSER_ID = "e2eBrowserIdentity0002"  # A second browser, so the pair differs in both halves.

# WHY: The organization picker reads the privilege list of the cloud session,
# and the site picker reads two cloud lists. Fixed records fill all three, so a
# signed-in page renders real rows and opens no socket to the Mist cloud.
STAND_IN_ORG_ID = "e2e-org-0001"  # The organization that the picker shows and the site list reads.
STAND_IN_ORG_NAME = "E2E Stand-In Organization"  # The text of the one organization row.
STAND_IN_SITE_ID = "e2e-site-0001"  # The site that the site picker shows and the inventory page reads.
STAND_IN_SITE_NAME = "E2E Stand-In Site"  # The text of the one site row.
STAND_IN_DEVICE_TYPES = ("ap", "gateway", "switch")  # Mirrors `select.DEVICE_TYPES`, which FR-013 fixes.
STAND_IN_VERSIONS = ("0.14.29216", "0.15.1")  # The version that runs now, then one newer version to pick.

# WHY: `select.SELECTED_ORG_KEY` names this field inside the signed session.
# The parent test process must not import the route module, because that import
# pulls the whole application into every collection. One short copy is the cost.
SELECTED_ORG_KEY = "selected_org_id"  # Mirrors `select.SELECTED_ORG_KEY`.


def _load_playwright_config() -> dict[str, str]:
    """Read the Playwright settings from the file beside this module.

    Why:
        One source holds the four settings the interface test identifier
        contract fixes. A second copy inside this module would drift.

    Returns:
        The setting names and their values.

    Raises:
        RuntimeError: If Python cannot load the settings file.
    """
    spec = importlib.util.spec_from_file_location(CONFIG_MODULE_NAME, CONFIG_PATH)
    if spec is None or spec.loader is None:  # WHY: A missing file must fail loudly, not silently.
        raise RuntimeError(f"Cannot load the Playwright settings at {CONFIG_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    settings = dict(module.PLAYWRIGHT_CONFIG)  # WHY: A copy stops a test from editing the shared table.
    settings["baseURL"] = BASE_URL  # WHY: The browser and the server must read one port, never two.
    return settings


PLAYWRIGHT_CONFIG = _load_playwright_config()


def _probe_port(port: int) -> bool:
    """Report whether a server answers on one port right now.

    Why:
        The fixture must start its own portal, so it tests the port first. A
        listener that this fixture did not start holds no sign-in seam, and the
        fixture reports that listener as a fault.

    Args:
        port: The port to test.

    Returns:
        True when a server answers.
    """
    try:  # A closed port and an absent host both raise OSError.
        with socket.create_connection((LOOPBACK_HOST, port), timeout=PROBE_TIMEOUT_SECONDS):
            return True
    except OSError:  # No server holds this port.
        return False


def _wait_for_port(port: int) -> bool:
    """Wait until the server answers on one port.

    Args:
        port: The port to test.

    Returns:
        True when the port answers, or False after the last try.
    """
    for _ in range(READY_TRIES):
        if _probe_port(port):
            return True
        time.sleep(READY_PAUSE_SECONDS)  # WHY: The server is not ready yet. Wait and try again.
    return False


def _stop_server(process: subprocess.Popen[bytes]) -> None:
    """Stop the capture portal server.

    Why:
        A server left behind holds the port and breaks the next test run.

    Args:
        process: The running server process.
    """
    logger.info("Stop the capture portal on port %s", CAPTURE_PORT)
    process.terminate()
    try:  # A server that ignores the stop request must not hold the test run.
        process.wait(timeout=STOP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:  # The polite request failed, so end the process.
        logger.warning("The capture portal did not stop in %s seconds", STOP_TIMEOUT_SECONDS)
        process.kill()


def _build_command() -> list[str] | None:
    """Build the server command for this platform.

    Why:
        A workstation without a usable server is a normal state, not a fault.
        The caller turns the empty result into a skip.

    Returns:
        The command, or None when no server can run here.
    """
    try:  # The seam raises when the platform can load no server at all.
        return build_server_command(WSGI_TARGET, CAPTURE_PORT, LOOPBACK_HOST)
    except RuntimeError as failure:  # State the cause, so the skip message stays honest.
        logger.info("No WSGI server can run on this workstation. Cause: %s", failure)
        return None


def _child_environment() -> dict[str, str]:
    """Build the environment of the server process.

    Why:
        The server needs the sign-in seam and the cookie signing key of this
        run. Both belong to the child alone. The parent environment stays
        untouched, so no later process and no other test folder reads either
        value, and a production start of the portal meets neither one.

    Returns:
        The environment variables for the server process.
    """
    child = dict(os.environ)  # Start from the parent, so the interpreter and the path still resolve.
    child[E2E_SESSION_VARIABLE] = E2E_SESSION_ENABLED  # Open the sign-in seam for this one process.
    child[SECRET_KEY_VARIABLE] = TEST_SECRET_KEY  # Both sides then sign and read one cookie key.
    return child  # `_spawn` hands this table to the new process.


def _spawn(command: list[str]) -> subprocess.Popen[bytes] | None:
    """Start the server process and send its output to a file.

    Why:
        A pipe would block the server once 64 KB of log records fill it, and
        nothing drains a pipe while the tests run. `subprocess.Popen` copies
        the file handle into the child, so the parent closes its own copy at
        once and the child keeps writing.

    Args:
        command: The command that starts the portal.

    Returns:
        The running process, or None when the process did not start.
    """
    child_env = _child_environment()  # The sign-in seam and the cookie key travel to the child alone.
    try:  # A missing interpreter, a blocked process, and an unwritable path all raise OSError.
        with SERVER_LOG_PATH.open("wb") as log:  # The child holds its own copy of this handle.
            return subprocess.Popen(command, cwd=REPO_ROOT, env=child_env, stdout=log, stderr=subprocess.STDOUT)
    except OSError as failure:  # State the cause, so the skip message stays honest.
        logger.info("The capture portal process did not start. Cause: %s", failure)
        return None


def _report_server_output() -> None:
    """Log what a server printed before it stopped.

    Why:
        A server that starts and never answers gives the reader nothing. The
        cause almost always sits in its own output, such as a bound port or a
        failed import. The output waits in a file, so this read cannot block.
    """
    try:  # A server that never reached the first write leaves no file.
        text = SERVER_LOG_PATH.read_text(encoding="utf-8", errors="replace").strip()
    except OSError as failure:  # An unreadable file must not replace the real cause.
        logger.warning("The capture portal log file could not be read. Cause: %s", failure)
        return
    if text:  # An empty file tells the reader nothing, so name only a real message.
        logger.warning("The capture portal wrote this before it stopped: %s", text)


def _start_server() -> subprocess.Popen[bytes] | None:
    """Start the capture portal and wait until it answers.

    Why:
        A browser test needs a real server, not a Flask test client. The wait
        stops a test from opening a page before the server is ready.

    Returns:
        The running server process, or None when the portal did not answer.
    """
    logger.info("Start the capture portal on port %s", CAPTURE_PORT)
    command = _build_command()
    if command is None:  # No server can run on this platform.
        return None
    process = _spawn(command)
    if process is None:  # The process did not start.
        return None
    if _wait_for_port(CAPTURE_PORT):  # The portal answers, so a browser test may open a page.
        return process
    _stop_server(process)  # The process runs and never answered, so it must not outlive the run.
    _report_server_output()  # The output waits in a file, so this read cannot block.
    return None


@pytest.fixture(scope="session")
def capture_portal_server() -> Iterator[str]:
    """Give every browser test the address of a portal this fixture started.

    Why:
        Only a portal that this fixture started holds the sign-in seam and the
        cookie key of this run. The fixture therefore starts its own portal and
        never joins one it finds. A stray listener and a portal that never
        answers are both faults, and the fixture names them. A workstation that
        can run no WSGI server is not a fault, so that one state reports a skip.

    Yields:
        The base address of the running portal.
    """
    if _probe_port(CAPTURE_PORT):  # A portal this fixture did not start holds no sign-in seam.
        pytest.fail(STRAY_LISTENER_MESSAGE, pytrace=False)
    if _build_command() is None:  # No WSGI server runs here, which describes the workstation.
        pytest.skip(NO_SERVER_MESSAGE)
    process = _start_server()
    if process is None:  # The command exists, so a portal that never answered is a real fault.
        pytest.fail(START_FAILED_MESSAGE, pytrace=False)
    yield BASE_URL
    _stop_server(process)


@pytest.fixture(scope="session")
def playwright_config() -> dict[str, str]:
    """Return the four Playwright settings for this feature.

    Why:
        A test asserts on a setting, such as the test identifier attribute.
        The fixture gives the same table the fixtures below read.

    Returns:
        The setting names and their values.
    """
    return dict(PLAYWRIGHT_CONFIG)  # WHY: A copy stops a test from editing the shared table.


@pytest.fixture(scope="session")
def base_url() -> str:
    """Return the address that every browser test opens.

    Why:
        Playwright reads this fixture to resolve a relative address, so a
        test writes ``/healthz`` and never the whole address. The value comes
        from the settings table, so one edit moves every test.

    Returns:
        The base address of the capture portal.
    """
    return PLAYWRIGHT_CONFIG["baseURL"]


@pytest.fixture(autouse=True)
def portal_test_id_attribute(request: pytest.FixtureRequest) -> None:
    """Point Playwright at the ``data-testid`` attribute.

    Why:
        The interface test identifier contract requires every test to select
        by ``data-testid`` only. This fixture makes ``get_by_test_id`` match
        that attribute. It does nothing when the Playwright plugin is absent,
        so a run without a browser still works.

    Args:
        request: The pytest request object.
    """
    if not request.config.pluginmanager.hasplugin("playwright"):  # WHY: No plugin means no browser test.
        return
    playwright_driver = request.getfixturevalue("playwright")  # WHY: Late lookup, so the plugin stays optional.
    playwright_driver.selectors.set_test_id_attribute(PLAYWRIGHT_CONFIG["testIdAttribute"])


class StandInCloudSession:  # Carries a privilege list and nothing else, so no method can open a socket
    """The cloud session that stands in for a signed-in operator.

    Why:
        `identity.OperatorSession` holds a reference to a `mistapi` object, and
        the portal passes that object to every cloud call. A real object would
        reach a live tenant, and no test may do that. This class carries the
        one field the portal reads and carries no request method at all, so a
        route that tried a cloud call would fail in the process and could not
        reach the network.

    Attributes:
        privileges: The organization records that the picker page reads.
    """

    def __init__(self) -> None:
        """Store the one privilege record that the organization picker shows."""
        self.privileges = [{"scope": "org", "org_id": STAND_IN_ORG_ID, "name": STAND_IN_ORG_NAME}]


def stand_in_cloud_read(name: str, **parameters: Any) -> list[dict[str, Any]]:
    """Answer a site read of the portal without a network call.

    Why:
        `select.default_cloud_read` calls the Mist software development kit, so
        the site picker of a signed-in page would reach a live tenant. This
        reader answers the two read names of `select.CLOUD_READS` from fixed
        records, and the page then shows real rows with no socket at all.

    Args:
        name: The read name that the route asked for.
        **parameters: The call parameters. One organization answers every call.

    Returns:
        The records of the named read, or an empty list for any other name.
    """
    del parameters  # One organization answers every call, so no parameter changes the result.
    if name == "listOrgSites":  # The name and the identifier of each site.
        return [{"id": STAND_IN_SITE_ID, "name": STAND_IN_SITE_NAME}]
    if name == "listOrgSiteStats":  # The device count of each site, read from `num_devices`.
        return [{"id": STAND_IN_SITE_ID, "num_devices": len(STAND_IN_DEVICE_TYPES)}]
    return []  # An unknown read name shows an empty list, and never a fault.


def stand_in_device(index: int, kind: str) -> dict[str, Any]:
    """Build one device record of the stand-in site.

    Args:
        index: The position of this device in the list, counted from one.
        kind: The device type, which FR-013 limits to three values.

    Returns:
        The fields that the inventory page and the device counts read.
    """
    return {
        "id": f"e2e-device-000{index}",  # The row key of the inventory page.
        "name": f"E2E {kind} {index}",  # The text that the page shows.
        "type": kind,  # `select.build_type_counts` groups the list by this field.
        "mac": f"00000000000{index}",  # A shape that reads as a hardware address.
        "model": f"E2E-{kind.upper()}",  # The model column of the inventory page.
        "serial": f"E2ESERIAL000{index}",  # The serial column of the inventory page.
        "version": "0.14.29216",  # The running firmware version that a capture records.
        "status": "connected",  # The state column, so no row reads as unknown.
        "site_id": STAND_IN_SITE_ID,  # The site that owns every stand-in device.
    }


def stand_in_device_read(**parameters: Any) -> list[dict[str, Any]]:
    """Answer the device inventory of one site without a network call.

    Why:
        `select.device_reader` falls back to the device module, which reads the
        Mist cloud. This reader answers one device of each type that FR-013
        names, so the inventory page and the three counts both hold real data.

    Args:
        **parameters: The call parameters. One site answers every call.

    Returns:
        One device record for each device type.
    """
    del parameters  # One site answers every call, so no parameter changes the result.
    return [stand_in_device(number, kind) for number, kind in enumerate(STAND_IN_DEVICE_TYPES, start=1)]


def stand_in_version_map() -> dict[str, tuple[str, ...]]:
    """Return the version list that the cloud names for each stand-in model.

    Why:
        `read_model_versions` calls the Mist software development kit, so the
        options page of a signed-in run would reach a live tenant. A fixed map
        gives every model one newer version to pick and one version that already
        runs, so the picker holds a real choice.

    Returns:
        The version list of each model of the stand-in site.
    """
    return {str(device["model"]): STAND_IN_VERSIONS for device in stand_in_device_read()}


def stand_in_options_view(session: Any, org_id: str, site_id: str) -> dict[str, Any]:
    """Answer the device rows and the version map that the options page draws.

    Why:
        `build_options_view` reads the site inventory from the cloud. This seam
        joins the stand-in inventory to the fixed version map with the shipped
        `build_version_options`, so the browser reads the rows that ship and the
        test never proves a shape that only this file builds.

    Args:
        session: The cloud session. This stand-in reads none of it.
        org_id: The organization that holds the site.
        site_id: The site under upgrade.

    Returns:
        One row for each stand-in device and the version list of each model.
    """
    del session, org_id, site_id  # One site answers every call, so no argument changes the result.
    from src.upgrade_portal.upgrade import options  # Late, so a plain collection never loads the portal.

    by_model = stand_in_version_map()
    return {"targets": options.build_version_options(stand_in_device_read(), by_model), "versions_by_model": by_model}


def stand_in_options_builder(record: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    """Widen the two fields of each browser choice into the whole target record.

    Why:
        The browser sends a device address and a version only, and the run
        driver reads a record of fifteen fields. `build_options_record` reads
        the site inventory from the cloud to fill the rest. This seam gives that
        read from the stand-in inventory and then calls the shipped builders.

    Args:
        record: The run record. The site of every stand-in run is the same one.
        body: The request body of the options call.

    Returns:
        The target list, the chosen options, and the warning sentences.
    """
    del record  # One site answers every call, so the run record changes nothing.
    from src.upgrade_portal.upgrade import options  # Late, so a plain collection never loads the portal.

    choices = body.get("targets")
    rows = [one for one in choices if isinstance(one, dict)] if isinstance(choices, list) else []
    entries = options.build_targets(stand_in_device_read(), rows)
    return {
        "targets": entries,
        "options": asdict(options.build_options(body)),
        "warnings": list(options.target_warnings(entries)),
    }


def signed_session_cookie(payload: dict[str, str]) -> str:
    """Sign a browser session payload the way the portal signs one.

    Why:
        The test must place a session cookie in the browser without a sign-in
        request, because a real sign-in would send a password to a live Mist
        tenant. Flask signs the cookie with `itsdangerous`, and a bare Flask
        object gives the same serializer while it holds no route and binds no
        port, so this function reaches nothing outside the test process.

    Args:
        payload: The fields to place inside the signed session.

    Returns:
        The signed cookie value.

    Raises:
        RuntimeError: If Flask builds no serializer, which means no key.
    """
    signer = flask.Flask(COOKIE_APP_NAME)  # A bare object. It serves nothing and binds no port.
    signer.secret_key = TEST_SECRET_KEY  # The same key that `_child_environment` gives the server.
    serializer = SecureCookieSessionInterface().get_signing_serializer(signer)  # The portal's own signer.
    if serializer is None:  # Flask answers None when the object holds no key at all.
        raise RuntimeError("Flask built no session serializer, so this run cannot sign a cookie.")
    return serializer.dumps(payload)  # The value that the browser then carries on every request.


def operator_session_cookies(email: str, browser_id: str) -> list[dict[str, str]]:
    """Build the two cookies that one signed-in browser carries.

    Why:
        `identity.current_session` reads an owner key out of the signed session
        and reads the `browser_id` cookie, and it refuses the request when the
        two disagree. A caller therefore needs both cookies, not the signed one
        alone. The organization pick travels in the same signed session, so the
        site picker finds an organization without a second page visit.

        The pair arrives as arguments, because the site lock identifies a holder
        by that pair. A test of two operators needs two pairs, and a fixed pair
        inside this function would give every browser one identity.

    Args:
        email: The work address of the operator, already normalized.
        browser_id: The browser identifier of that operator.

    Returns:
        One record for each cookie, in the shape that `add_cookies` takes.
    """
    owner = identity.build_owner(email, browser_id)  # The pair the server registered.
    payload = {identity.SESSION_OWNER_KEY: owner.key, SELECTED_ORG_KEY: STAND_IN_ORG_ID}  # No personal data.
    signed = signed_session_cookie(payload)  # The value that the portal reads back and trusts.
    session_cookie = {"name": SESSION_COOKIE_NAME, "value": signed, "url": BASE_URL}  # The signed half.
    browser_cookie = {"name": identity.BROWSER_ID_COOKIE, "value": browser_id, "url": BASE_URL}
    return [session_cookie, browser_cookie]  # Playwright installs both against the portal address.


def portal_session_cookies() -> list[dict[str, str]]:
    """Build the two cookies of the first stand-in operator.

    Why:
        Nearly every browser test drives one operator, and naming that pair at
        each call site would repeat the same two constants everywhere.

    Returns:
        One record for each cookie, in the shape that `add_cookies` takes.
    """
    return operator_session_cookies(STAND_IN_EMAIL, STAND_IN_BROWSER_ID)


def second_operator_cookies() -> list[dict[str, str]]:
    """Build the two cookies of the second stand-in operator.

    Why:
        The site lock refuses a second holder, and the refusal is a documented
        journey. A second browser context needs a pair that differs in both
        halves, because a shared cookie would read as the same operator and
        would resume the lock instead of meeting the refusal.

    Returns:
        One record for each cookie, in the shape that `add_cookies` takes.
    """
    return operator_session_cookies(SECOND_EMAIL, SECOND_BROWSER_ID)


def _register_operator(email: str, browser_id: str) -> None:
    """Place one signed-in operator record into the process registry.

    Why:
        `identity.SESSION_REGISTRY` holds a record for each operator pair, and a
        request with no record reads 401. The server process must write every
        record itself, because the registry is a dictionary inside one process.

    Args:
        email: The work address of the operator, already normalized.
        browser_id: The browser identifier of that operator.
    """
    owner = identity.build_owner(email, browser_id)  # The pair a cookie also names.
    mode = identity.CredentialMode.ENVIRONMENT_TOKEN  # The mode a token sign-in would have recorded.
    identity.SESSION_REGISTRY.register(identity.OperatorSession(owner, StandInCloudSession(), mode))


def build_stand_in_app() -> Any:
    """Build the portal with two signed-in operators and no cloud reach.

    Why:
        `identity.SESSION_REGISTRY` is a dictionary inside one process, so the
        test process cannot write a record into the server process. The server
        must register the records itself, and this function is the only place
        that does so. The two cloud seams take a stand-in as well, because a
        signed-in page reads the organization list and the site list, and both
        reads would otherwise reach a live tenant.

        The second operator exists for the site lock alone. The lock refuses a
        second holder, and a test of that refusal needs a second pair that the
        server already knows. Every other test drives the first pair.

        Warning: this function signs two operators in with no credential. The
        gate below is the only caller, and only `_child_environment` opens that
        gate. No shipped file names the gate variable, so a production start of
        `wsgi_capture.py` never loads this module and never reaches this code.

    Returns:
        The Flask application that the server process serves.
    """
    from src.upgrade_portal.app.factory import create_app  # Late, so a plain collection never builds an app.
    from src.upgrade_portal.app.routes import (
        select,  # Late as well. It owns the two cloud seams.
        upgrade,  # Late as well. It owns the two options seams.
    )

    built = create_app()  # The production application, with no change to any shipped line.
    built.config[select.MIST_READER_KEY] = stand_in_cloud_read  # The site picker then reads no network.
    built.config[select.DEVICE_READER_KEY] = stand_in_device_read  # The inventory page reads no network.
    built.config[upgrade.OPTIONS_VIEW_KEY] = stand_in_options_view  # The options page then draws every device.
    built.config[upgrade.OPTIONS_BUILDER_KEY] = stand_in_options_builder  # The save call stores a whole row.
    _register_operator(STAND_IN_EMAIL, STAND_IN_BROWSER_ID)  # The operator that every test drives.
    _register_operator(SECOND_EMAIL, SECOND_BROWSER_ID)  # The operator that meets the lock refusal.
    return built  # Waitress and Gunicorn both load this object by name.


@pytest.fixture
def page(context: Any, capture_portal_server: str) -> Iterator[Any]:
    """Open a browser page that already holds a portal session.

    Why:
        Every page below the sign-in form calls `identity.require_session`, so
        a browser test with no session reads 401 and skips. A real sign-in
        would send a password to a live Mist tenant, which no test may do. The
        fixture installs the two cookies of the session that the server
        registered at start-up, so the browser opens the pages and reaches no
        cloud at all.

        This fixture replaces the `page` fixture of `pytest-playwright`, so no
        test file changes. A run against a portal that was already listening
        keeps the 401 skips, because that server holds no stand-in record and
        signs with a different key.

    Args:
        context: The browser context that `pytest-playwright` built.
        capture_portal_server: The address of the running portal.

    Yields:
        The browser page, with both session cookies in place.
    """
    del capture_portal_server  # Requested for its start-up work alone. `base_url` carries the address.
    context.add_cookies(portal_session_cookies())  # Both cookies, against the portal address.
    opened = context.new_page()  # The page then carries the session on its first request.
    yield opened
    opened.close()  # A page left open would hold a browser target for the whole run.


@pytest.fixture
def second_operator_page(browser: Any, capture_portal_server: str) -> Iterator[Any]:
    """Open a page of a second browser that holds the second operator session.

    Why:
        The site lock identifies a holder by the pair of the work address and
        the browser identifier. Two tabs of one browser share the cookie jar, so
        they share that pair and read as one operator. A test of the refusal
        therefore needs a whole second context, which carries its own cookie jar
        and its own browser identifier.

        The context takes the portal address as its base, because a page of a
        context built here would otherwise refuse a relative path.

    Args:
        browser: The browser that `pytest-playwright` started.
        capture_portal_server: The address of the running portal.

    Yields:
        The page of the second browser, with both session cookies in place.
    """
    del capture_portal_server  # Requested for its start-up work alone.
    context = browser.new_context(base_url=BASE_URL)  # A separate cookie jar, so a separate lock identity.
    context.add_cookies(second_operator_cookies())  # The second pair, which the server also registered.
    opened = context.new_page()
    yield opened
    opened.close()
    context.close()  # The context holds a profile directory until it closes.


# WHY: The server process loads this module by name and reads `app`. That name
# exists only when the gate variable holds the enabling value, and only
# `_child_environment` writes that variable, into the child process alone. A
# normal test collection, a normal server start, and every production start
# therefore reach no stand-in session. `wsgi_capture.py` names the production
# application, and this module changes no line of it.
if os.environ.get(E2E_SESSION_VARIABLE) == E2E_SESSION_ENABLED:  # The child process alone opens this gate.
    app = build_stand_in_app()  # The signed-in portal that every browser test of this folder drives.
