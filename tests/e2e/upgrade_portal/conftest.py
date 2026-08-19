"""Browser fixtures for the upgrade capture portal tests.

Why:
    A browser test drives a full operator journey through a real server. It
    finds the defects that a unit test and a contract test cannot find, such
    as a broken template or a script that fails in the browser.

    The server fixture repeats the shape of the ``gunicorn_server`` fixture at
    ``tests/e2e/conftest.py:56-99``, which has no consumer today. This one
    binds to port 8056, the capture portal port, instead of a random port.

    The Playwright settings live in ``playwright.config.py`` beside this file.
    That file name holds a dot, so no module can import it by name. This
    module loads it by path.
"""

from __future__ import annotations

import importlib.util
import logging
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

# WHY: The capture portal answers on port 8056, next to the existing portal on
# port 8055. See Containerfile and compose.yml.
CAPTURE_PORT = 8056
BASE_URL = f"http://127.0.0.1:{CAPTURE_PORT}"

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
    return dict(module.PLAYWRIGHT_CONFIG)  # WHY: A copy stops a test from editing the shared table.


PLAYWRIGHT_CONFIG = _load_playwright_config()


def _gunicorn_command() -> list[str]:
    """Build the command that starts the capture portal.

    Why:
        The command repeats the shape at ``tests/e2e/conftest.py:66-81``. One
        worker and a 30-second timeout keep a test run predictable.

    Returns:
        The command and its arguments.
    """
    return [
        sys.executable,  # WHY: The same interpreter runs the tests and the server.
        "-m",
        "gunicorn",
        "--bind",
        f"127.0.0.1:{CAPTURE_PORT}",  # WHY: Loopback only. No test reaches an outside host.
        "--timeout",
        "30",
        "--workers",
        "1",  # WHY: One worker keeps the log order and the lock state simple.
        "wsgi_capture:app",  # WHY: The capture portal entry point, not wsgi:app.
    ]


def _wait_for_port(port: int) -> bool:
    """Wait until the server answers on one port.

    Args:
        port: The port to test.

    Returns:
        True when the port answers, or False after the last try.
    """
    for _ in range(READY_TRIES):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=READY_PAUSE_SECONDS):
                return True
        except OSError:  # WHY: The server is not ready yet. Wait and try again.
            time.sleep(READY_PAUSE_SECONDS)
    return False


def _stop_server(process: subprocess.Popen[bytes]) -> None:
    """Stop the capture portal server.

    Why:
        A server left behind holds port 8056 and breaks the next test run.

    Args:
        process: The running server process.
    """
    logger.info("Stop the capture portal on port %s", CAPTURE_PORT)
    process.terminate()
    process.wait(timeout=5)  # WHY: The same 5-second budget as tests/e2e/conftest.py:99.


def _start_server() -> subprocess.Popen[bytes]:
    """Start the capture portal server and wait until it answers.

    Why:
        A browser test needs a real server, not a Flask test client. The wait
        stops a test from opening a page before the server is ready.

    Returns:
        The running server process.

    Raises:
        RuntimeError: If the server does not answer on port 8056.
    """
    logger.info("Start the capture portal on port %s", CAPTURE_PORT)
    process = subprocess.Popen(_gunicorn_command(), cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not _wait_for_port(CAPTURE_PORT):
        _stop_server(process)
        raise RuntimeError(f"Gunicorn did not answer on port {CAPTURE_PORT}")
    logger.debug("The capture portal answers at %s", BASE_URL)
    return process


@pytest.fixture(scope="session")
def capture_portal_server() -> Iterator[str]:
    """Run the capture portal on port 8056 for the whole test session.

    Why:
        Every browser test needs one running server. A session scope starts
        the server once, so a suite of journeys pays the start cost one time.

    Yields:
        The base address of the running portal.
    """
    process = _start_server()
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
        from the settings file, so one edit moves every test.

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
