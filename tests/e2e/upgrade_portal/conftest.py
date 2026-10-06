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

    ``src/interfaces/portals/upgrade_portal/runtime/server.py`` picks the server for the platform.
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
import itertools  # Issue each stand-in cloud job its own number.
import json  # Write process-safe browser-token evidence without credential values.
import logging
import os
import signal
import socket
import subprocess
import tempfile
import threading
import time
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar, NoReturn
from urllib.parse import urlencode  # Issue #3438: the query of page one of a lost-page read.

import flask
import pytest
from flask.sessions import SecureCookieSessionInterface

from src.interfaces.portals.upgrade_portal.api.run_controls import (
    E2EFactoryOverrides,
)  # Type the complete isolated dependency set.
from src.interfaces.portals.upgrade_portal.app.config import (
    PORT_VARIABLE,
    SECRET_KEY_VARIABLE,
)  # Read child server setting names.
from src.interfaces.portals.upgrade_portal.capture.devices import (
    DeviceRead,
)  # Issue #3438: the answer of a real picker read.
from src.interfaces.portals.upgrade_portal.runtime import identity  # Build the signed test session owners.
from src.interfaces.portals.upgrade_portal.runtime.server import (
    build_server_command,
)  # Start the platform server safely.
from src.operations.execution.firmware.org_upgrade_service import OrgUpgradeResult
from src.operations.execution.firmware.upgrade_service import (
    CancelOutcome,
    UpgradeSubmission,
)  # Build stand-in site child results.
from tests.e2e.upgrade_portal.empty_site_seeds import (  # Issue #3389: the site with no device.
    EMPTY_SITE_BROWSER_ID,
    EMPTY_SITE_EMAIL,
    EMPTY_SITE_ID,
    EMPTY_SITE_NAME,
)
from tests.e2e.upgrade_portal.later_check_seeds import (  # Issue #3439: the reads that lose page two on request.
    LATER_CHECK_BROWSER_ID,
    LATER_CHECK_EMAIL,
    LATER_CHECK_HOST,
    LATER_CHECK_LIMIT,
    LATER_CHECK_LOST_BODY,
    LATER_CHECK_LOST_STATUS,
    LATER_CHECK_ORG_ID,
    LATER_CHECK_ORG_NAME,
    LATER_CHECK_PAGES,
    LATER_CHECK_SERIES,
    LATER_CHECK_TOTAL,
    LOSE_PAGE_HEADER,
    LOSE_PAGE_VALUE,
    LaterCheckSeeds,
)
from tests.e2e.upgrade_portal.lost_page_seeds import (  # Issue #3438: the organization whose reads lose page two.
    LOST_PAGE_BODY,
    LOST_PAGE_BROWSER_ID,
    LOST_PAGE_EMAIL,
    LOST_PAGE_HOST,
    LOST_PAGE_LIMIT,
    LOST_PAGE_ORG_ID,
    LOST_PAGE_ORG_NAME,
    LOST_PAGE_ROWS,
    LOST_PAGE_STATUS,
    LOST_PAGE_TOTAL,
)
from tests.e2e.upgrade_portal.org_cancel_seeds import CANCEL_AP_JOB_ID, OrgCancelSeeds  # Issue #3246: the cancel.
from tests.e2e.upgrade_portal.org_control_seeds import (  # Issue #3247: the seeds of the recovery journeys.
    CONTROLS_BROWSER_ID,
    CONTROLS_EMAIL,
    OrgControlSeeds,
)
from tests.e2e.upgrade_portal.org_ended_seeds import OrgEndedSeeds  # Issue #3367: a child job that ended first.
from tests.e2e.upgrade_portal.retry_run_seeds import (  # Issue #3292: keep retry setup off the shared site.
    FAILED_RUN_ID,
    STOPPED_RUN_ID,
    RetryRunSeeds,
)
from tests.e2e.upgrade_portal.screenshot import install_screenshot_retry  # Retry the known Chromium screenshot flake.
from tests.e2e.upgrade_portal.short_read_seeds import (  # Issue #3424: the site whose read stops early.
    SHORT_SITE_BROWSER_ID,
    SHORT_SITE_DEVICE_COUNT,
    SHORT_SITE_DIGIT,
    SHORT_SITE_EMAIL,
    SHORT_SITE_ID,
    SHORT_SITE_LABEL,
    SHORT_SITE_NAME,
    SHORT_SITE_REASON,
)
from tests.e2e.upgrade_portal.stale_run_seeds import StaleRunSeeds  # Issue #3507: the stale runs on their own site.
from tests.support.sdk_pages import HTML_TYPE, JSON_TYPE, build_sdk_answer  # Issue #3438: real SDK answers.
from tests.support.site_lock_trail import CheckoutTrailGuard  # Issue #3512: the root guard of the checkout trail.
from tests.support.upgrade_portal_e2e import (  # Build isolated resources, environments, and stores.
    RunOwnerHeaderCheck,
    allocate_resources,
    build_child_environment,
    build_e2e_overrides,
)
from tests.support.upgrade_portal_e2e.live_runs import LiveRunCheck, SiteRunReader  # Issue #3511: the run check.
from tests.support.upgrade_portal_e2e.org_operations import (  # Issue #3518: the teardown of each operation.
    OrgOperationLedger,
    OrgOperationRelease,
    OrgStartTap,
)
from tests.support.upgrade_portal_e2e.records.audit import (  # The two trail guards of the browser run.
    AuditTrailIsolation,  # Issue #3498: the checkout trail guard.
    TrailHoldCheck,  # Issue #3508: the leaked hold check of the run trail.
)

logger = logging.getLogger(__name__)

LOOPBACK_HOST = "127.0.0.1"  # Loopback only. No test reaches an outside host.

# WHY: Gunicorn and Waitress both load a target of this shape. `wsgi_capture.py`
# holds `wsgi_capture:app` and stays the production target of this portal. The
# browser tests load the target below instead, because the signed-in record must
# live inside the server process and no test process can reach that memory.
WSGI_TARGET = "tests.e2e.upgrade_portal.conftest:app"

# WHY: The root conftest changes the working directory for each test, so the
# server needs an explicit directory to find wsgi_capture.py.
REPO_ROOT = Path(__file__).parents[3]

# WHY: The parent allocates the resources. The child reads those exact values
# from its scrubbed environment and never allocates a second server identity.
CHILD_TEST_RUN_ID = os.environ.get("UPGRADE_PORTAL_E2E_RUN_ID", "")  # Empty only in the parent test process.
if CHILD_TEST_RUN_ID:  # The WSGI child must use the resources that the parent allocated.
    PARENT_ARTIFACT_DIRECTORY = None  # The child uses the artifact paths that the parent selected.
    E2E_RESOURCES = None  # The child owns no reservation socket.
    TEST_RUN_ID = CHILD_TEST_RUN_ID  # Keep record ownership equal to the expected response header.
    CAPTURE_PORT = int(os.environ[PORT_VARIABLE])  # Use the exact port that the parent passes.
    ARTIFACT_DIRECTORY = Path(os.environ["UPGRADE_PORTAL_E2E_ARTIFACT_DIRECTORY"])  # Use the parent artifact root.
    SERVER_LOG_PATH = Path(os.environ["UPGRADE_PORTAL_E2E_LOG_PATH"])  # Keep the parent-selected log path.
    SERVER_OWNER_PATH = Path(os.environ["UPGRADE_PORTAL_E2E_OWNER_PATH"])  # Keep the parent-selected owner path.
else:  # The parent test process allocates one unique server resource set.
    PARENT_ARTIFACT_DIRECTORY = tempfile.TemporaryDirectory(prefix="misthelper-upgrade-portal-")  # Auto-clean.
    E2E_RESOURCES = allocate_resources(Path(PARENT_ARTIFACT_DIRECTORY.name))  # Stay outside repository data.
    TEST_RUN_ID = E2E_RESOURCES.test_run_id  # Bind all parent expectations to the allocated owner.
    CAPTURE_PORT = E2E_RESOURCES.port  # Pass the exact reserved loopback port to the child.
    ARTIFACT_DIRECTORY = E2E_RESOURCES.artifact_directory  # Keep all artifacts under one unique directory.
    SERVER_LOG_PATH = E2E_RESOURCES.log_path  # Keep one log inside this server artifact directory.
    SERVER_OWNER_PATH = E2E_RESOURCES.process_owner_path  # Keep the owner record unique to this server.
BASE_URL = f"http://{LOOPBACK_HOST}:{CAPTURE_PORT}"  # Point every browser request at this server only.

# WHY: The settings file sits beside this module. A path load is the only way
# to read a file whose name holds a dot.
CONFIG_PATH = Path(__file__).with_name("playwright.config.py")
CONFIG_MODULE_NAME = "upgrade_portal_playwright_config"

READY_PAUSE_SECONDS = 0.5
READY_BUDGET_VARIABLE = "UPGRADE_PORTAL_E2E_READY_SECONDS"  # The optional start budget in seconds.
DEFAULT_READY_BUDGET_SECONDS = 60.0  # Issue #3516: a loaded workstation can need more than 10 seconds.
READY_TRIES = max(
    20,
    int(float(os.environ.get(READY_BUDGET_VARIABLE, str(DEFAULT_READY_BUDGET_SECONDS))) / READY_PAUSE_SECONDS),
)
PROBE_TIMEOUT_SECONDS = 0.5  # One connection attempt against a port that may hold no listener.
STOP_TIMEOUT_SECONDS = 5  # The server gets 5 seconds to stop before this fixture ends it.

# WHY: The server runs for the whole session and logs one record for each
# request. A pipe holds 64 KB on Windows, and nothing drains it while the tests
# run. A full pipe blocks the writer, so a server given a pipe stops answering
# partway through a run and every later page reports a refused connection. A
# file never blocks the writer, and the skip message reads the same file back.
# WHY: Issue #2260. A run that ends on a timeout never reaches its teardown, so
# the portal outlives it and holds the port. Every later run on that port then
# reported a stray listener, and an operator had to find the process by hand.
# This file names the portal that the current run started, so the next run can
# tell its own leftover from a portal container that an operator started.
# The wait for a stopped portal to release the port. A stop is quick on
# loopback, and these two values bound the wait at ten seconds.
RECLAIM_TRIES = 20
RECLAIM_PAUSE_SECONDS = 0.5

# WHY: Only a portal that this fixture started carries the sign-in seam and the
# cookie key of this run. A portal left running in another window carries
# neither, so every page below the sign-in form answers 401 and every test
# skips. A whole run then reports success while it opened no page. A stray
# listener is a fault of the workstation, and the fixture names it.
STRAY_LISTENER_MESSAGE = (
    f"Another process already listens on port {CAPTURE_PORT}. "
    "The browser tests must start their own portal, because only that portal holds the sign-in seam. "
    f"This suite records every portal it starts in {SERVER_OWNER_PATH}, and that record names no live "
    "process now, so the listener belongs to something else. A portal container is the common cause. "
    f"Stop the process that holds port {CAPTURE_PORT}, or set CAPTURE_PORT to a free port, then run the "
    "tests again."
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


@dataclass(frozen=True)
class PortalStartWait:
    """Hold the result of the bounded wait for the portal child process."""

    ready: bool  # True means the port answered before the budget ended.
    elapsed_seconds: float  # The measured wait helps diagnose a near timeout.
    exit_code: int | None  # A value means the child stopped before the port answered.


# WHY: `identity.SessionOwner` checks both halves of the pair. The address is
# already in its normalized form, and the reserved `.invalid` domain can reach
# no mail host. The browser identifier holds 22 characters of the allowed set.
# Caution: issue #2615 refuses a firmware write from this reserved domain, so a
# browser test cannot complete an upgrade start. Issue #2632 records that gap.
# A reachable address here makes the whole browser suite hang, because the suite
# cannot finish a real start journey.
STAND_IN_EMAIL = "e2e.operator@example.invalid"  # Lower case, so `normalize_email` leaves it unchanged.
STAND_IN_BROWSER_ID = "e2eBrowserIdentity0001"  # Matches the browser cookie pattern that identity fixes.
BROWSER_TOKEN_VALUE = "fake-browser-token-for-playwright-only"  # The browser submits this obvious stand-in only.
BROWSER_TOKEN_NAME = "e2e-browser-token"  # The safe token name that GetSelf returns for the identity owner.
BROWSER_TOKEN_EVIDENCE_PATH = ARTIFACT_DIRECTORY / "browser-token-evidence.jsonl"  # Holds facts, never a token.

# WHY: The site lock identifies a holder by the pair of the work address and the
# browser identifier. A test of two operators therefore needs a second pair that
# differs in both halves, and the server must hold a record for it. Both values
# below are as fake as the pair above, and neither one reaches a mail host.
SECOND_EMAIL = "e2e.second.operator@example.invalid"  # A second address, already normalized.
SECOND_BROWSER_ID = "e2eBrowserIdentity0002"  # A second browser, so the pair differs in both halves.
RENEWED_BROWSER_ID = "e2eBrowserIdentity0003"  # A renewed session keeps the actor and changes the browser.
FIRMWARE_EMAIL = "e2e.operator@juniper.net"  # A reachable stand-in lets firmware-write browser tests pass the gate.
FIRMWARE_BROWSER_ID = "e2eBrowserIdentity0004"  # A separate browser identity keeps lock ownership unambiguous.


# WHY: The organization picker reads the privilege list of the cloud session,
# and the site picker reads two cloud lists. Fixed records fill all three, so a
# signed-in page renders real rows and opens no socket to the Mist cloud.
STAND_IN_ORG_ID = "11111111-1111-1111-1111-111111111111"  # The organization that the picker shows.
STAND_IN_ORG_NAME = "E2E Stand-In Organization"  # The text of the organization row.
# WHY: Issue #3910. The picker sorts the rows by name at `select.py:1065`, so
# no constant here holds a fixed row position. Each comment names the role of
# the site instead of a position.
STAND_IN_SITE_ID = "22222222-2222-2222-2222-222222222222"  # The default site of the single-site tests.
STAND_IN_SITE_NAME = "E2E Stand-In Site"  # The row text of the default site.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The extra site for organization tests.
SECOND_SITE_NAME = "E2E Second Stand-In Site"  # The row text of the extra site.
# WHY: Issue #3377. Seeded live runs and multi-site journeys hold the default
# site and the extra site, and FR-037 allows one live run for each site. The
# single-site upgrade journey of `test_upgrade.py` therefore owns the site
# below. No seed and no other module names it, so every run on it belongs to
# that journey.
JOURNEY_SITE_ID = "44444444-4444-4444-4444-444444444444"  # The site of the single-site upgrade journey.
JOURNEY_SITE_NAME = "E2E Upgrade Journey Site"  # The row text of the journey site.
STAND_IN_DEVICE_TYPES = ("ap", "gateway", "switch")  # Mirrors `select.DEVICE_TYPES`, which FR-013 fixes.
STAND_IN_VERSIONS = ("0.14.29216", "0.15.1")  # The version that runs now, then one newer version to pick.
# WHY: Issue #3244. A standalone capture names no run. The pre-check reads the
# version before the upgrade, and the post-check reads the version after it,
# so the comparison of one site shows a firmware change.
STANDALONE_ROLE_VERSIONS = {"pre": STAND_IN_VERSIONS[0], "post": STAND_IN_VERSIONS[1]}  # The version of each role.
# WHY: Issue #3249. The multi-site device table keys each row by the MAC
# address, so each site holds its own addresses. The cloud job of the access
# points lists one access point as upgraded and the other access point as
# failed, so the table shows one version match and one version mismatch.
# WHY: Issue #3932. Each name states the cloud result, because the picker
# sorts by name and the sort decides which site appears first.
UPGRADED_SITE_AP_MAC = "000000000001"  # The access point that the cloud job reports as upgraded.
FAILED_SITE_AP_MAC = "000000000101"  # The access point that the cloud job reports as failed.
# WHY: Issue #3424. The short-read site shows its devices in the same table as
# the second site, so it needs its own addresses too. Each entry gives a site
# one address digit and one name word. The second site keeps digit 1, so its
# addresses stay the same as before this map.
SITE_DEVICE_SERIES = {  # The address digit and the name word of each site with its own devices.
    SECOND_SITE_ID: (1, "Site Two"),  # The second site of issue #3249.
    SHORT_SITE_ID: (SHORT_SITE_DIGIT, SHORT_SITE_LABEL),  # The short-read site of issue #3424.
    **LATER_CHECK_SERIES,  # Issue #3439: the three sites of the later-check organization, digits 3 to 5.
}

STAND_IN_RUN_ID = "e2e-run-0001"  # The run that owns the comparison captures below.
PRE_CAPTURE_ID = "e2e-capture-pre-0001"  # The pre-check that the picker offers first.
POST_CAPTURE_ID = "e2e-capture-post-0001"  # The post-check that the picker offers second.
TIER3_CAPTURE_ID = "e2e-capture-tier3-0001"  # The complete Tier 3 capture for browser proof.
PRE_CAPTURE_STAMP = "2026-08-19T10:00:00+00:00"  # ISO 8601 in UTC, which is the stored form.
POST_CAPTURE_STAMP = "2026-08-19T10:30:00+00:00"  # Thirty minutes later, so the window is measurable.
TIER3_CAPTURE_STAMP = "2026-08-19T11:00:00+00:00"  # The newest history record.
RUN_OWNED_CAPTURE_IDS = (PRE_CAPTURE_ID, POST_CAPTURE_ID, TIER3_CAPTURE_ID)  # The seeds that the run owns.
# WHY: Issue #3360. The shipped pre-check adopter adopts only a capture that
# names no run. This seed is the one standalone pre-check of the first site. It
# starts after the seeded pre-check and before the seeded post-check, so each
# capture picker keeps its first choice and its last choice.
STANDALONE_PRE_CAPTURE_ID = "e2e-capture-standalone-0001"  # The seeded pre-check that names no run.
STANDALONE_PRE_CAPTURE_STAMP = "2026-08-19T10:15:00+00:00"  # Between the seeded pre-check and post-check.
# WHY: Issue #3378. The shipped store writes `complete` into `capture_status`
# and `verified` into `state`. Every seed now holds the shipped shape, and this
# seed keeps a separate site so its page reads the stored path after a restart.
# It sits on its own site and between the post-check and the Tier 3 capture, so
# no count, no first or last picker choice, and no pre-check adopter reads it.
STORED_POLL_CAPTURE_ID = "e2e-capture-stored-poll-0001"  # The seed in the shipped shape.
STORED_POLL_SITE_ID = "e2e-stored-poll-site"  # A site that no other journey reads.
STORED_POLL_SITE_NAME = "E2E Stored Poll Site"  # The site name of the history row.
STORED_POLL_CAPTURE_STAMP = "2026-08-19T10:45:00+00:00"  # Between the seeded post-check and the Tier 3 capture.
# `capture/store.py` names this reason for a key that the database does not hold,
# and `app/routes/capture.py` turns it into the 404 of the contract.
CAPTURE_NOT_FOUND_REASON = "capture_not_found"  # The refusal for a key that the stand-in never published.

# WHY: The panel of the capture page shows this sentence. It states that a
# stand-in reported the capture, so a person who reads a browser recording of a
# failed run never mistakes this record for the answer of a live site read.
STAND_IN_CAPTURE_MESSAGE = "The stand-in collector reported this capture and read no site."

# WHY: `review.HISTORY_ROW_DEFAULTS` fixes the eight names of a history row, and
# the page heading reads the site beside them. A stored capture holds far more,
# so the lister below copies these names alone and never the whole document.
HISTORY_ROW_NAMES = (
    "capture_id",
    "role",
    "started_at",
    "capture_status",
    "actor_email",
    "stored_size_bytes",
    "counts",
    "site_id",
    "site_name",
)

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


# WHY: Issue #2241. Every test module under this folder calls
# `pytest.importorskip("playwright.sync_api")`. A missing package therefore
# turned all 11 modules into a skip, and pytest reports a skip as a pass. The
# "E2E smoke tests" gate then reported green while it opened no page, so the
# whole browser suite covered nothing and no signal said so.
#
# Neither requirements file named the package, so a fresh worktree always hit
# this state. `requirements-dev.txt` now pins it, and this guard makes the
# regression impossible to hide: in strict mode a missing package fails
# collection instead of skipping it.
STRICT_VARIABLE = "UPGRADE_PORTAL_E2E_STRICT"  # The gate. CI sets it, and a workstation may leave it unset.
STRICT_ENABLED = "1"  # The one value that turns a skip into a failure. Any other value keeps the skip.

MISSING_PLAYWRIGHT_MESSAGE = (
    "The Playwright package is not installed, and "
    f"{STRICT_VARIABLE}={STRICT_ENABLED} forbids a skip. "
    "Every browser test would report a skip, and pytest reports a skip as a pass, "
    "so the gate would pass while it opened no page. Install the pinned packages, "
    "then download the browser:\n"
    "    pip install -r requirements-dev.txt\n"
    "    python -m playwright install chromium\n"
    "`python scripts/bootstrap_worktree.py` runs both commands for you. Issue #2241."
)


def pytest_configure(config: pytest.Config) -> None:
    """Refuse a run that would skip every browser test in strict mode.

    Why:
        A skip reads as a pass. In strict mode a missing browser package must
        stop the run, so no gate can report success over an empty suite.

    Args:
        config: The pytest configuration for this run. The guard reads no value
            from it, and the parameter exists because pytest supplies it.

    Raises:
        pytest.UsageError: If strict mode is on and Playwright is absent.
    """
    del config  # WHY: The hook signature requires the parameter, and the guard reads no setting.
    if os.environ.get(STRICT_VARIABLE) != STRICT_ENABLED:  # WHY: A workstation may still skip.
        logger.debug("The browser strict guard is off, so a missing package stays a skip")
        return  # WHY: Leave the existing skip behaviour for a workstation with no browser.
    logger.info("The browser strict guard is on, so a missing package fails the run")
    if not _playwright_is_installed():  # WHY: Ask without importing the package.
        raise pytest.UsageError(MISSING_PLAYWRIGHT_MESSAGE)  # WHY: Stop the run before it reports a pass.
    logger.debug("The Playwright package is present, so the browser suite can open a page")


def _playwright_is_installed() -> bool:
    """Report whether `playwright.sync_api` can be imported.

    Why:
        `importlib.util.find_spec` answers None for a missing submodule, but it
        raises `ModuleNotFoundError` when the parent package is absent. That is
        the exact state this guard exists to catch, so the raise must become a
        plain answer. Without this guard the run ends in an internal error and
        never prints the repair.

    Returns:
        True when the package is present.
    """
    try:  # WHY: A missing parent package raises rather than answering None.
        return importlib.util.find_spec("playwright.sync_api") is not None
    except ModuleNotFoundError:  # WHY: No `playwright` package exists at all.
        logger.debug("The playwright package is absent, so no browser test can open a page")
        return False  # WHY: Report the absence as an answer, not as an internal error.


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


def _wait_for_port(port: int, process: subprocess.Popen[bytes]) -> PortalStartWait:
    """Wait until the server answers or the child process stops.

    Args:
        port: The port to test.
        process: The portal child process.

    Returns:
        The ready state, elapsed seconds, and child exit code.
    """
    started = time.monotonic()  # Use a monotonic clock, because wall-clock changes must not alter the budget.
    logger.info("Wait up to %.1f seconds for the capture portal", READY_TRIES * READY_PAUSE_SECONDS)
    for _ in range(READY_TRIES):  # Keep each existing probe and pause until one terminal state occurs.
        if _probe_port(port):  # A listener proves that the child completed its startup.
            elapsed = time.monotonic() - started  # Measure the real startup time for the test record.
            logger.debug("The capture portal answered after %.2f seconds", elapsed)
            return PortalStartWait(True, elapsed, None)  # Report the ready state without another process read.
        exit_code = process.poll()  # Read the child state before another pause can hide an import failure.
        if exit_code is not None:  # A stopped child can never open the port later.
            elapsed = time.monotonic() - started  # State how quickly the child failed.
            logger.error("The capture portal stopped with exit code %s after %.2f seconds", exit_code, elapsed)
            return PortalStartWait(False, elapsed, exit_code)  # Preserve the exit code for the failure message.
        time.sleep(READY_PAUSE_SECONDS)  # WHY: The server is not ready yet. Wait and try again.
    elapsed = time.monotonic() - started  # Measure the complete bounded wait.
    exit_code = process.poll()  # Capture an exit that occurred during the last pause.
    logger.error("The capture portal did not answer after %.2f seconds", elapsed)
    return PortalStartWait(False, elapsed, exit_code)  # Report timeout and any final child exit.


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
    _forget_owner()  # Issue #2260: this run owns the port no longer, so the record must go.


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


def _record_owner(process: subprocess.Popen[bytes]) -> None:
    """Write the process identifier of the portal this run started.

    Why:
        Issue #2260. A run that ends on a timeout never reaches the teardown, so
        the portal outlives it and holds the port. The next run then reports a
        stray listener and every test errors. This record lets that next run
        name the owner and reclaim the port.

    Args:
        process: The portal process this run started.
    """
    try:  # An unwritable temporary folder must not stop a run that otherwise works.
        SERVER_OWNER_PATH.write_text(str(process.pid), encoding="utf-8")
    except OSError as failure:  # The next run then reports the stray listener, as it did before.
        logger.info("The portal owner record was not written. Cause: %s", failure)
        return
    logger.debug("The portal on port %s runs as process %d", CAPTURE_PORT, process.pid)


def _forget_owner() -> None:
    """Remove the owner record, because this run stopped its own portal."""
    SERVER_OWNER_PATH.unlink(missing_ok=True)  # A stopped portal owns nothing, so the record must go.
    logger.debug("The portal owner record for port %s is gone", CAPTURE_PORT)


def _recorded_owner() -> int | None:
    """Return the process identifier that an earlier run recorded.

    Returns:
        The identifier, or None when no readable record exists.
    """
    try:  # A first run on this workstation leaves no file at all.
        text = SERVER_OWNER_PATH.read_text(encoding="utf-8").strip()
    except OSError:  # No record exists, so no earlier run named an owner.
        return None
    return int(text) if text.isdigit() else None  # A damaged record names no process.


def _stop_stale_owner() -> bool:
    """Stop a portal that an earlier run of this suite left behind.

    Why:
        Issue #2260. The suite writes the identifier of every portal it starts,
        and it removes that record when it stops the portal. A record that
        survives therefore names a run that never reached its teardown.

        Warning: this function stops only a process that this suite recorded. It
        never stops a listener it did not start, because a portal container or
        another application on the port is a state of the workstation.

    Returns:
        True when the port is free again.
    """
    owner = _recorded_owner()
    if owner is None:  # This suite started no portal that survived, so the listener belongs elsewhere.
        return False
    logger.warning("An earlier run of this suite left the portal %d on port %s", owner, CAPTURE_PORT)
    try:  # The process may have already ended between the read and this call.
        os.kill(owner, signal.SIGTERM)
    except OSError as failure:  # An absent process is the state this function wants.
        logger.info("The recorded portal %d did not take the stop. Cause: %s", owner, failure)
    return _wait_for_free_port()


def _wait_for_free_port() -> bool:
    """Wait until no server answers on the port of this run.

    Returns:
        True when the port is free, or False after the last try.
    """
    for _ in range(RECLAIM_TRIES):  # A stopped process releases the port a moment later.
        if not _probe_port(CAPTURE_PORT):
            _forget_owner()  # The record named a portal that is gone, so it must go as well.
            logger.info("Port %s is free again, so this run may start its own portal", CAPTURE_PORT)
            return True
        time.sleep(RECLAIM_PAUSE_SECONDS)  # WHY: The process is still closing the socket.
    return False


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
    child = build_child_environment(os.environ)  # Remove production credentials and install connector sentinels.
    child[E2E_SESSION_VARIABLE] = E2E_SESSION_ENABLED  # Open the sign-in seam for this one process.
    child[SECRET_KEY_VARIABLE] = TEST_SECRET_KEY  # Both sides then sign and read one cookie key.
    child[PORT_VARIABLE] = str(CAPTURE_PORT)  # Give the child the exact port that this session reserved.
    child["UPGRADE_PORTAL_E2E_RUN_ID"] = TEST_RUN_ID  # Bind child records to this server.
    child["UPGRADE_PORTAL_E2E_ARTIFACT_DIRECTORY"] = str(ARTIFACT_DIRECTORY)  # Reuse the parent artifact root.
    child["UPGRADE_PORTAL_E2E_LOG_PATH"] = str(SERVER_LOG_PATH)  # Reuse the parent server log path.
    child["UPGRADE_PORTAL_E2E_OWNER_PATH"] = str(SERVER_OWNER_PATH)  # Reuse the parent process owner path.
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
    if E2E_RESOURCES is None:  # Only the parent owns the reservation socket.
        raise RuntimeError("The E2E child cannot start another E2E server.")  # Prevent nested server creation.
    E2E_RESOURCES.release_port()  # Release the reservation immediately before the child binds the same port.
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


def _fail_start(process: subprocess.Popen[bytes], wait: PortalStartWait) -> NoReturn:
    """Stop a live child and report the exact portal start failure."""
    if wait.exit_code is None:  # A live child exceeded the budget and must not outlive the run.
        _stop_server(process)  # The process runs and never answered, so it must not outlive the run.
        detail = f"The start budget ended after {wait.elapsed_seconds:.2f} seconds."  # Name the timeout.
    else:  # A stopped child needs no signal, and its exit code is the primary cause.
        detail = (  # Keep the complete cause in the pytest failure message.
            f"The child stopped with exit code {wait.exit_code} after {wait.elapsed_seconds:.2f} seconds."
        )
    _report_server_output()  # The output waits in a file, so this read cannot block.
    pytest.fail(f"{START_FAILED_MESSAGE} {detail}", pytrace=False)  # Fail setup with the measured cause.


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
    wait = _wait_for_port(CAPTURE_PORT, process)  # Stop at readiness, child exit, or the finite budget.
    if wait.ready:  # The portal answers, so a browser test may open a page.
        _record_owner(process)  # Issue #2260: the next run can then reclaim this port.
        return process
    _fail_start(process, wait)  # The helper stops a live child and raises the measured pytest failure.


AUDIT_GUARD_KEY = pytest.StashKey[str]()  # Issue #3498: the measure that the terminal summary prints.
AUDIT_GUARD_RECORD = "checkout-audit-trail-guard.json"  # Issue #3498: the record of the two counts.
HOLD_GUARD_KEY = pytest.StashKey[str]()  # Issue #3508: the measure of the run trail hold check.
HOLD_GUARD_RECORD = "run-trail-hold-guard.json"  # Issue #3508: the record of the hold check.
LIVE_RUN_KEY = pytest.StashKey[list[LiveRunCheck]]()  # Issue #3511: the check of each module, for the summary.
LIVE_RUN_RECORD = "live-run-check.jsonl"  # Issue #3511: one line of the live-run check for each module.
LIVE_RUN_STATE = SimpleNamespace(running=False, live=frozenset())  # Issue #3511: the portal flag and the last scan.


@pytest.fixture(scope="session")
def checkout_audit_trail_guard(
    request: pytest.FixtureRequest, checkout_site_lock_trail_guard: CheckoutTrailGuard | None
) -> Iterator[AuditTrailIsolation]:
    """Count the checkout audit trail before the portal starts and after it stops.

    Why:
        Issue #3498. The test portal wrote each lock action to the checkout
        trail, which is the production audit trail in the main checkout. An
        older header guard compared fixed values, so it could not see the
        leak. Issue #3501 removed that guard. This guard reads the file itself. The fixture
        `capture_portal_server` depends on it. The first count therefore runs
        before the child starts, and the second count runs after the child
        stops.

        Issue #3512. Eleven modules start the portal inside their first test,
        after the root conftest moved the trail of that test. A read of the
        lock module here then names the moved trail. So this guard reads the
        checkout trail from the root guard, which read it before the first
        move.

        Caution: the production container writes the trail of the main
        checkout. A real lock action during a run in the main checkout also
        fails this guard. Run the browser suite in a worktree.

    Args:
        request: The fixture request, which carries the run configuration.
        checkout_site_lock_trail_guard: The root guard of issue #3503, which
            holds the checkout trail.

    Yields:
        The isolation of this run. A journey reads its two trails.
    """
    # WHY: Issue #3512. The root guard read the checkout trail before the first move of the session.
    isolation = AuditTrailIsolation.for_session(ARTIFACT_DIRECTORY, checkout_site_lock_trail_guard)  # Checkout trail.
    logger.info("Count the checkout audit trail before the browser run")  # Log before the first count.
    before = isolation.count_lines(isolation.checkout_trail)  # An unreadable trail fails here, before any test.
    yield isolation  # The browser run happens here.
    after = isolation.count_lines(isolation.checkout_trail)  # The child stopped, so no write can follow.
    measure = isolation.measure(before, after)  # The sentence that states what the guard checked.
    request.config.stash[AUDIT_GUARD_KEY] = measure  # The terminal summary prints the measure.
    record = {"checkout_trail": str(isolation.checkout_trail), "before": before, "after": after, "measure": measure}
    (ARTIFACT_DIRECTORY / AUDIT_GUARD_RECORD).write_text(json.dumps(record, indent=2), encoding="utf-8")
    logger.debug("Wrote the checkout audit trail record: %s", measure)  # Log after the record write.
    isolation.require_unchanged(before, after)  # A changed count fails the run.


@pytest.fixture(scope="session")
def run_trail_hold_guard(
    request: pytest.FixtureRequest, checkout_audit_trail_guard: AuditTrailIsolation
) -> Iterator[TrailHoldCheck]:
    """Replay the site lock trail of the run after the portal stops, and fail on each leaked hold.

    Why:
        Issue #3508. The full browser run of issue #3497 ended with two site
        locks held, and the run still passed. The fixture
        `capture_portal_server` depends on this guard, so pytest tears the
        guard down after the portal stops. No write can then follow the read.

    Args:
        request: The fixture request, which carries the run configuration.
        checkout_audit_trail_guard: The isolation of this run, which names the run trail.

    Yields:
        The check of this run.
    """
    check = TrailHoldCheck(checkout_audit_trail_guard.run_trail)  # The child portal writes this trail alone.
    yield check  # The browser run happens here.
    logger.info("Replay the site lock trail of the browser run")  # Log before the replay.
    started = time.perf_counter()  # Issue #3508: the replay must stay short.
    result = check.evaluate()  # A line that the check cannot read fails here.
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)  # The cost of the replay.
    request.config.stash[HOLD_GUARD_KEY] = result.measure  # The terminal summary prints the measure.
    record: dict[str, Any] = {"run_trail": str(result.trail)}  # The trail that the check read.
    record.update({"records": result.records, "sites": result.sites})  # The two counts of the read.
    record.update({"leaks": list(result.leaks), "elapsed_ms": elapsed_ms, "measure": result.measure})  # The result.
    (ARTIFACT_DIRECTORY / HOLD_GUARD_RECORD).write_text(json.dumps(record, indent=2), encoding="utf-8")
    logger.debug("Wrote the run trail hold record: %s", result.measure)  # Log after the record write.
    result.require_no_leak()  # A leaked hold fails the run.


def _picker_site_ids() -> list[str]:
    """Return the key of each site that the site picker lists.

    Why:
        Issue #3511. A single-site create journey builds its run on a site that
        the picker lists. The live-run check reads the same list, so a new
        picker site joins the check with no second list to keep.

    Returns:
        The site keys, in the order of the picker.

    Raises:
        AssertionError: The stand-in site read did not answer a list of sites.
    """
    sites = stand_in_cloud_read("listOrgSites")  # The fixed site list of the stand-in organization.
    if not isinstance(sites, list):  # A real-walk read answers a device read, which names no picker site.
        raise AssertionError("The stand-in site read of issue #3511 must answer a list of sites.")
    return [str(site["id"]) for site in sites]  # The key of each picker site.


@pytest.fixture(scope="module", autouse=True)
def module_live_run_check(request: pytest.FixtureRequest) -> Iterator[None]:
    """Fail each module that leaves a new live run at a site of the picker.

    Why:
        Issue #3511. The walk of `test_capture.py` left one run live on the
        first site of the picker. Each later create call at that site answered
        409, and two tests then used the leftover run in place of their own
        run. This check reads the run history of each picker site after each
        module, and it fails the module that left a new live run.

        A module that ended before the portal started skips the check, because
        no run can exist yet. Pytest ends each module fixture before the
        session fixtures, so the last module still reads a running portal.

    Args:
        request: The fixture request, which names the module and carries the run configuration.

    Yields:
        Nothing. The check runs after the last test of the module.
    """
    yield  # The tests of the module run here.
    if not LIVE_RUN_STATE.running:  # No portal runs, so no module could leave a live run.
        return  # Nothing to check.
    before = LIVE_RUN_STATE.live  # The live runs after the previous module.
    cookies = "; ".join(f"{item['name']}={item['value']}" for item in portal_session_cookies())  # A signed read.
    logger.info("Scan the picker sites for a live run after %s", request.node.nodeid)  # Log before the scan.
    scan = SiteRunReader(BASE_URL, cookies).scan(_picker_site_ids())  # A failed read fails the module here.
    LIVE_RUN_STATE.live = scan.runs  # The next module compares against this scan, so no leak counts twice.
    check = LiveRunCheck(request.node.nodeid, before, scan)  # The decision of this module.
    with (ARTIFACT_DIRECTORY / LIVE_RUN_RECORD).open("a", encoding="utf-8") as trail:  # One line for each module.
        trail.write(json.dumps(check.record()) + "\n")  # The counts, the leaks, and the time of the scan.
    request.config.stash.setdefault(LIVE_RUN_KEY, []).append(check)  # The terminal summary adds each check.
    logger.debug("Wrote the live-run record: %s leak(s) in %s ms", len(check.leaks), scan.elapsed_ms)  # After.
    check.require_no_leak()  # A new live run fails the module.


def pytest_terminal_summary(terminalreporter: Any, config: pytest.Config) -> None:
    """Print the measure of each trail guard and of the live-run check of the browser run.

    Why:
        Issue #3498, issue #3508, and issue #3511. A guard must state what it
        checked. The fixtures `checkout_audit_trail_guard` and
        `run_trail_hold_guard` each store one sentence. The fixture
        `module_live_run_check` stores the check of each module. This hook
        prints each sentence at the end of the run.

    Args:
        terminalreporter: The reporter that writes the terminal summary.
        config: The pytest configuration for this run.
    """
    for key in (AUDIT_GUARD_KEY, HOLD_GUARD_KEY):  # The checkout trail guard, then the run trail hold check.
        measure = config.stash.get(key, "")  # Empty when no browser test started the portal.
        if measure:  # A run that started no portal has no measure to print.
            terminalreporter.write_line(measure)  # One line in the terminal summary.
    live_runs = LiveRunCheck.summary(config.stash.get(LIVE_RUN_KEY, []))  # Issue #3511: empty with no portal.
    if live_runs:  # A run that started no portal ran no live-run check.
        terminalreporter.write_line(live_runs)  # One line in the terminal summary.


@pytest.fixture(scope="session")
def capture_portal_server(
    checkout_audit_trail_guard: AuditTrailIsolation, run_trail_hold_guard: TrailHoldCheck
) -> Iterator[str]:
    """Give every browser test the address of a portal this fixture started.

    Why:
        Only a portal that this fixture started holds the sign-in seam and the
        cookie key of this run. The fixture therefore starts its own portal and
        never joins one it finds. A stray listener and a portal that never
        answers are both faults, and the fixture names them. A workstation that
        can run no WSGI server is not a fault, so that one state reports a skip.

    Args:
        checkout_audit_trail_guard: Issue #3498. The guard counts the checkout
            trail before this portal starts and after it stops.
        run_trail_hold_guard: Issue #3508. The guard replays the run trail
            after this portal stops.

    Yields:
        The base address of the running portal.
    """
    del checkout_audit_trail_guard, run_trail_hold_guard  # Requested for their teardown checks alone.
    if _probe_port(CAPTURE_PORT):  # A portal this fixture did not start holds no sign-in seam.
        # Issue #2260: an earlier run of this suite may own the port. The record
        # names that portal, so this run may reclaim the port instead of failing.
        if not _stop_stale_owner():
            pytest.fail(STRAY_LISTENER_MESSAGE, pytrace=False)
    if _build_command() is None:  # No WSGI server runs here, which describes the workstation.
        pytest.skip(NO_SERVER_MESSAGE)
    process = _start_server()
    if process is None:  # The command exists, so a portal that never answered is a real fault.
        pytest.fail(START_FAILED_MESSAGE, pytrace=False)
    LIVE_RUN_STATE.running = True  # Issue #3511: each module check may now read the portal.
    yield BASE_URL
    LIVE_RUN_STATE.running = False  # Issue #3511: no module check may read a stopped portal.
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


@pytest.fixture(scope="session")
def browser_context_args(
    pytestconfig: Any,
    playwright: Any,
    device: str | None,
    _pw_artifacts_folder: Any,
) -> dict[str, Any]:
    """Build browser settings that always name this suite's portal.

    Why:
        The Playwright plug-in caches its session settings. Another E2E folder
        can create that cache before this nested configuration loads, which
        leaves the browser on the deployment port while this suite owns a
        dynamic port. A local fixture gives this suite a separate cache key.

    Args:
        pytestconfig: The active pytest configuration.
        playwright: The Playwright controller with optional device settings.
        device: The selected browser device name, if one exists.
        _pw_artifacts_folder: The plug-in folder for retained videos.

    Returns:
        The browser context settings for this portal test session.
    """
    settings: dict[str, Any] = {}  # Start with no plug-in defaults from another E2E folder.
    if device:  # A selected device still controls its viewport and user agent.
        settings.update(playwright.devices[device])  # Copy the plug-in's selected device settings.
    settings["base_url"] = BASE_URL  # Bind relative browser paths to this suite's dynamic server port.
    if pytestconfig.getoption("--video") in {"on", "retain-on-failure"}:  # Keep requested video evidence.
        settings["record_video_dir"] = _pw_artifacts_folder.name  # Use the plug-in artifact lifecycle.
    return settings  # The Playwright context fixture copies this table for each test.


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


class StandInCloudSession:  # Carries a privilege list and a narrow read, so every other call still fails fast
    """The cloud session that stands in for a signed-in operator.

    Why:
        `identity.OperatorSession` holds a reference to a `mistapi` object, and
        the portal passes that object to every cloud call. A real object would
        reach a live tenant, and no test may do that. This class carries the
        one field the site picker reads and the one read the inventory page's
        stale-firmware check needs. Every other call still finds no method and
        fails in the process, so it could not reach the network either.

    Attributes:
        privileges: The organization records that the picker page reads.
    """

    def __init__(self) -> None:
        """Store the one privilege record that the organization picker shows."""
        self.privileges = [{"scope": "org", "org_id": STAND_IN_ORG_ID, "name": STAND_IN_ORG_NAME}]
        self._MAX_429_RETRIES = 0  # The destructive write guard requires no SDK retry.
        self._session = SimpleNamespace(adapters={})  # The transport layer has no retrying adapter.

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Answer the one read the inventory page's stale-firmware check needs.

        Why:
            `select.inventory_rows_with_targets` reads
            `listSiteAvailableDeviceVersions` for every stand-in device model,
            so the site inventory page raised `AttributeError` before this
            method existed (issue #2172). The answer reuses `STAND_IN_VERSIONS`,
            the same version pair `stand_in_version_map` already publishes for
            the options page, so both pages agree on one fixed answer.

        Args:
            uri: The request path. Only the device-versions path answers rows.
            query: The query parameters. `model` names the row the answer carries.

        Returns:
            An object with the one `data` attribute that `_rows` reads.

        Raises:
            AssertionError: When the call is not the one this stand-in answers,
                so an unexpected cloud call still fails in the process and
                still cannot reach the network.
        """
        if not uri.endswith("/devices/versions"):
            raise AssertionError(f"StandInCloudSession.mist_get answers no read for {uri!r}.")
        model = str((query or {}).get("model", ""))
        rows = [{"model": model, "version": version} for version in STAND_IN_VERSIONS]
        return SimpleNamespace(data=rows)


def record_browser_token_evidence(event: str, **fields: Any) -> None:
    """Record browser-token evidence without writing the token value.

    Why:
        The browser-token test process cannot read the server process memory.
        A small JSON Lines file proves that the server-side stand-in saw the
        expected boundary calls. The file carries no credential value.

    Args:
        event: The event name that the test later reads.
        **fields: Safe fields that contain no credential value.
    """
    logger.info("Record browser-token evidence for %s", event)  # Log the action with no token value.
    row = {"event": event, "run_id": TEST_RUN_ID, **fields}  # Join only safe fields for the test process.
    BROWSER_TOKEN_EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)  # The child may start before a writer.
    with BROWSER_TOKEN_EVIDENCE_PATH.open("a", encoding="utf-8") as handle:  # Append so each call survives.
        handle.write(json.dumps(row, sort_keys=True) + "\n")  # JSON Lines lets the test read partial evidence.
    logger.debug("Recorded browser-token evidence for %s", event)  # Confirm the write without details.


class BrowserTokenCloudSession(StandInCloudSession):
    """The cloud session that a browser-token sign-in creates.

    Why:
        The session proves that the submitted browser token reached the cloud
        boundary, and that a later Mist-backed page used the same session
        object. It records only safe facts in the evidence file.
    """

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Answer one Mist read and record that the browser-token session was used.

        Why:
            The inventory page calls this method for available firmware
            versions. Recording that call proves that a page below sign-in used
            the token-built session, without writing the token value.

        Args:
            uri: The request path. Only the device-versions path answers rows.
            query: The query parameters. The model is safe to record.

        Returns:
            An object with the data rows that the inventory route reads.
        """
        model = str((query or {}).get("model", ""))  # A model is not a credential and helps prove the request.
        record_browser_token_evidence("mist_get", uri=uri, model=model)  # The evidence names the safe Mist read.
        return super().mist_get(uri, query)  # Reuse the same deterministic answer as the cookie session.


def stand_in_browser_token_session(host: str, token: str) -> BrowserTokenCloudSession:
    """Build the browser-token cloud session and keep no token value.

    Why:
        The real builder would send the token to the Mist cloud. This stand-in
        accepts one fake token, records that the cloud boundary ran, and returns
        a session that answers only the reads this suite permits.

    Args:
        host: The Mist cloud host that the sign-in route checked.
        token: The submitted browser token. This function discards it.

    Returns:
        The stand-in cloud session for the signed-in browser.

    Raises:
        ValueError: If the browser sends an invalid stand-in token.
    """
    accepted = token == BROWSER_TOKEN_VALUE  # Compare once, then discard the submitted value.
    record_browser_token_evidence("browser_token_session", accepted=accepted, host=host)  # Store no token.
    del token  # End the local token lifetime before any later code can use it.
    if not accepted:  # A wrong value follows the same refusal route as a bad cloud token.
        raise ValueError("The browser token stand-in refused the submitted value.")
    return BrowserTokenCloudSession()  # The token-built session now serves the browser journey.


def stand_in_token_identity(session: Any) -> dict[str, str]:
    """Return the safe token identity for a browser-token cloud session.

    Why:
        The real identity read would call `getSelf` in the Mist cloud. This
        stand-in proves that the identity step ran and returns a safe token
        name that can become the browser owner.

    Args:
        session: The token-built cloud session. The value proves the sequence.

    Returns:
        The safe identity record that the route reads.
    """
    assert isinstance(session, BrowserTokenCloudSession)  # The identity read must follow the token builder.
    record_browser_token_evidence("token_identity", name=BROWSER_TOKEN_NAME)  # The name is safe to store.
    return {"name": BROWSER_TOKEN_NAME}  # `identity.build_token_owner` accepts this token-name shape.


class LostPageCloudSession(StandInCloudSession):
    """The cloud session of the lost-page operator of issue #3438.

    Why:
        The picker reads of this operator run the real page walk of
        `select.default_cloud_read`. This session answers page one of each
        picker read with a real SDK answer object, so the SDK builds the next
        link from the page headers. Page two answers the HTML error page of a
        gateway, so the walk loses that page. Every other read keeps the
        answers of the parent class, so no call reaches the network.

    Attributes:
        privileges: The one organization that the picker of this operator shows.
    """

    def __init__(self) -> None:
        """Store the privilege record of the lost-page organization."""
        super().__init__()  # Keep the retry settings that the destructive write guard reads.
        self.privileges = [{"scope": "org", "org_id": LOST_PAGE_ORG_ID, "name": LOST_PAGE_ORG_NAME}]  # One org.

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> Any:
        """Answer page one of a picker read, or lose page two.

        Args:
            uri: The request path, or the next link that the SDK built.
            query: The query of page one. A next link carries its own query.

        Returns:
            The SDK answer of the page, or the answer of the parent class for any other read.
        """
        path = uri.split("?", 1)[0]  # The read path without the query of a next link.
        if path not in LOST_PAGE_ROWS:  # Any other read keeps the fixed answers of the parent class.
            return super().mist_get(uri, query)
        logger.info("Answer one page of the lost-page read %s", path)  # Log before the answer.
        if "page=" in uri:  # The SDK asks for page two, and a gateway fault loses it.
            return build_sdk_answer(LOST_PAGE_STATUS, LOST_PAGE_BODY, HTML_TYPE, f"{LOST_PAGE_HOST}{uri}")
        page_headers = {"X-Page-Total": str(LOST_PAGE_TOTAL), "X-Page-Limit": str(LOST_PAGE_LIMIT)}  # 2 pages.
        headers = {**JSON_TYPE, **page_headers, "X-Page-Page": "1"}  # The SDK reads all three page headers.
        body = json.dumps(LOST_PAGE_ROWS[path]).encode("utf-8")  # The rows of page one.
        address = f"{LOST_PAGE_HOST}{path}?{urlencode(query or {})}"  # The SDK adds the page to this address.
        return build_sdk_answer(200, body, headers, address)  # Page one, with a next link to page two.


class LaterCheckCloudSession(StandInCloudSession):
    """The cloud session of the later-check operator of issue #3439.

    Why:
        The site reads of this operator run the real page walk of
        `select.default_cloud_read`. This session answers both pages of each
        site read with a real SDK answer object, so the SDK builds the next
        link from the page headers. A request that carries the lose-page
        header loses page two, so a journey chooses the moment of the fault.
        Every other read keeps the answers of the parent class, so no call
        reaches the network.

    Attributes:
        privileges: The one organization that the picker of this operator shows.
    """

    def __init__(self) -> None:
        """Store the privilege record of the later-check organization."""
        super().__init__()  # Keep the retry settings that the destructive write guard reads.
        self.privileges = [{"scope": "org", "org_id": LATER_CHECK_ORG_ID, "name": LATER_CHECK_ORG_NAME}]  # One org.

    @staticmethod
    def lose_page_requested() -> bool:
        """Report whether the current request asks the site reads to lose page two.

        Returns:
            True when the browser request carries the lose-page header.
        """
        if not flask.has_request_context():  # A capture thread reads outside a request, so it keeps page two.
            return False  # Only a journey request can ask for the fault.
        return flask.request.headers.get(LOSE_PAGE_HEADER, "") == LOSE_PAGE_VALUE  # The journey set the header.

    @staticmethod
    def page_answer(rows: list[dict[str, Any]], page_number: int, address: str) -> Any:
        """Build the SDK answer of one whole page of a site read.

        Args:
            rows: The rows of the page.
            page_number: The number of the page, counted from one.
            address: The full request address. The SDK builds the next link from it.

        Returns:
            The SDK answer of the page.
        """
        page_headers = {"X-Page-Total": str(LATER_CHECK_TOTAL), "X-Page-Limit": str(LATER_CHECK_LIMIT)}  # 2 pages.
        headers = {**JSON_TYPE, **page_headers, "X-Page-Page": str(page_number)}  # The SDK reads all three.
        body = json.dumps(rows).encode("utf-8")  # The rows of the page.
        return build_sdk_answer(200, body, headers, address)  # Page one links to page two. Page two links to none.

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> Any:
        """Answer one page of a site read, and lose page two when the journey asks.

        Args:
            uri: The request path, or the next link that the SDK built.
            query: The query of page one. A next link carries its own query.

        Returns:
            The SDK answer of the page, or the answer of the parent class for any other read.
        """
        path = uri.split("?", 1)[0]  # The read path without the query of a next link.
        if path not in LATER_CHECK_PAGES:  # Any other read keeps the fixed answers of the parent class.
            return super().mist_get(uri, query)
        logger.info("Answer one page of the later-check read %s", path)  # Log before the answer.
        page_one, page_two = LATER_CHECK_PAGES[path]  # The rows of both pages of this read.
        if "page=" not in uri:  # Page one. The SDK adds the page number to this address for page two.
            return self.page_answer(page_one, 1, f"{LATER_CHECK_HOST}{path}?{urlencode(query or {})}")
        address = f"{LATER_CHECK_HOST}{uri}"  # The SDK sends the page-two address as a path only.
        if self.lose_page_requested():  # The journey asks for a gateway fault on page two.
            logger.debug("The later-check read %s loses page two", path)  # Log the fault before the answer.
            return build_sdk_answer(LATER_CHECK_LOST_STATUS, LATER_CHECK_LOST_BODY, HTML_TYPE, address)
        return self.page_answer(page_two, 2, address)  # The whole page two.


class E2EOrgUpgradeService:
    """Return deterministic organization job results to the browser server."""

    @staticmethod
    def submit(cloud_session: Any, org_id: str, body: dict[str, object]) -> OrgUpgradeResult:
        """Return one accepted organization job with a new identifier."""
        chosen = sorted(body["site_ids"])  # The picker sorts by name, so the request order is immaterial (#3216).
        assert chosen == sorted([STAND_IN_SITE_ID, SECOND_SITE_ID])  # Every organization journey picks both sites.
        upgrade_id = StandInJobIds.org_job()  # A real cloud gives each job its own identifier.
        return OrgUpgradeResult(org_id, upgrade_id, 200, {"id": upgrade_id}, None)  # A valid accepted answer.

    @staticmethod
    def status(cloud_session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Return progress for both selected sites, or the end state of a cancelled job."""
        if upgrade_id == CANCEL_AP_JOB_ID:  # Issue #3246: the seeded job names one rebooting access point.
            answer = OrgCancelSeeds.status_data(upgrade_id, CancelledJobs.holds(upgrade_id))  # The nested shape.
            return OrgUpgradeResult(org_id, upgrade_id, 200, answer, None)  # A valid answer of the stand-in cloud.
        state = "cancelled" if CancelledJobs.holds(upgrade_id) else "inprogress"  # A real cloud ends a cancelled job.
        site_state = "cancelled" if state == "cancelled" else "running"  # Each site follows the job.
        return OrgUpgradeResult(
            org_id,
            upgrade_id,
            200,
            {
                "id": upgrade_id,
                "status": state,
                "site_upgrades": [
                    {
                        "site_id": STAND_IN_SITE_ID,
                        "id": "55555555-5555-5555-5555-555555555555",
                        "status": site_state,
                        "targets": {"total": 2, "upgraded": [UPGRADED_SITE_AP_MAC], "failed": []},  # Issue #3249.
                    },
                    {
                        "site_id": SECOND_SITE_ID,
                        "id": "66666666-6666-6666-6666-666666666666",
                        "status": site_state,
                        "targets": {"total": 2, "upgraded": [], "failed": [FAILED_SITE_AP_MAC]},  # Issue #3249.
                    },
                ],
            },
            None,
        )

    @staticmethod
    def cancel(cloud_session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Return one accepted cancellation, and end the job for every later status read."""
        CancelledJobs.add(upgrade_id)  # The next read reports the end, so the sites go back (issue #3220).
        return OrgUpgradeResult(org_id, upgrade_id, 200, {}, None)


class CancelledJobs:
    """Remember each stand-in job that a browser test cancelled.

    Why:
        Issue #3220. The portal now keeps the site locks of a multi-site
        operation until each child reaches a final state. A stand-in that
        reported a running job forever would therefore hold both stand-in
        sites for the rest of the browser session, and every later single-site
        test would meet a site lock. A real cloud reports a cancelled job as
        cancelled, so this stand-in does the same.
    """

    _identifiers: ClassVar[set[str]] = set()  # The cancelled job identifiers of this server process.
    _guard: ClassVar[threading.Lock] = threading.Lock()  # The server answers requests on several threads.

    @classmethod
    def add(cls, upgrade_id: str) -> None:
        """Record one cancelled job."""
        with cls._guard:  # One writer at a time keeps the set whole.
            cls._identifiers.add(str(upgrade_id))  # Later reads see the end state.

    @classmethod
    def holds(cls, upgrade_id: str) -> bool:
        """Return true when a browser test cancelled this job."""
        with cls._guard:  # A reader waits for a writer.
            return str(upgrade_id) in cls._identifiers  # The job ended on a cancel.


class StandInJobIds:
    """Give each stand-in cloud job a new identifier, as a real cloud does.

    Why:
        `CancelledJobs` keys the end state by the job identifier. The stand-in
        once gave every switch child job the identifier "switch-job". A cancel
        in one browser test then ended the switch job of each later test, and
        the later test read "cancelled" before it cancelled anything. The
        journey of issue #3245 cancels two operations, so it showed the fault.
    """

    _numbers: ClassVar[itertools.count[int]] = itertools.count(1)  # The next free number of this server process.
    _guard: ClassVar[threading.Lock] = threading.Lock()  # The server answers requests on several threads.

    @classmethod
    def _next(cls) -> int:
        """Return the next free number of this server process."""
        with cls._guard:  # One caller at a time keeps each number unique.
            return next(cls._numbers)  # Each call takes a new number.

    @classmethod
    def org_job(cls) -> str:
        """Return a new organization job identifier in the shape of a cloud answer."""
        return f"44444444-4444-4444-4444-{cls._next():012d}"  # The five groups of a real identifier.

    @classmethod
    def child_job(cls, device_type: str) -> str:
        """Return a new site child job identifier that names the device family.

        Args:
            device_type: The device family of the child job, such as "switch".

        Returns:
            The identifier, such as "switch-job-7".
        """
        return f"{device_type}-job-{cls._next()}"  # The family keeps the identifier clear in a screenshot.


class E2EDeviceUpgradeService:
    """Return deterministic site child results without a Mist call."""

    ACCEPTED_STATUS = (200, 202)  # Match the production service contract.

    @staticmethod
    def invoke_upgrade(cloud_session: Any, plan: Any) -> UpgradeSubmission:
        """Accept one site child with a new job identifier."""
        del cloud_session  # The stand-in reads no credential.
        return UpgradeSubmission(
            StandInJobIds.child_job(plan.targets[0].device_type),  # A cancel of one job never ends a later job.
            plan.scope,
            tuple(target.mac for target in plan.targets),
            (),
            202,
        )

    @staticmethod
    def read_upgrade_status(
        cloud_session: Any,
        scope: str,
        identifier: str,
        upgrade_id: str,
        family: Any,
    ) -> dict[str, Any]:
        """Return one running child status, or the end state of a cancelled child."""
        del cloud_session, scope, identifier, family  # The fixed answer needs no request value.
        return {
            "upgrade_id": upgrade_id,
            "raw_status": 200,
            "status": "cancelled" if CancelledJobs.holds(upgrade_id) else "running",  # A cancel ends the child.
            "status_known": True,
            "targets": {},
        }

    @staticmethod
    def cancel_upgrade(cloud_session: Any, plan: Any, upgrade_id: str, status: Any) -> CancelOutcome:
        """Accept one site child cancellation, and end the child for every later status read."""
        del cloud_session, status  # The fixed answer needs the plan targets only.
        CancelledJobs.add(upgrade_id)  # The next read reports the end, so the sites go back (issue #3220).
        return CancelOutcome(
            tuple(target.mac for target in plan.targets),
            (),
            (),
            "The stand-in accepted the cancellation.",
        )


def stand_in_cloud_read(name: str, **parameters: Any) -> list[dict[str, Any]] | DeviceRead:
    """Answer a site read of the portal without a network call.

    Why:
        `select.default_cloud_read` calls the Mist software development kit, so
        the site picker of a signed-in page would reach a live tenant. This
        reader answers the two read names of `select.CLOUD_READS` from fixed
        records, and the page then shows real rows with no socket at all.

        Issue #3438. The lost-page organization runs the real read of
        `select.default_cloud_read` instead. The cloud session of its operator
        answers page one and loses page two, so the page walk and the two
        notes of the picker run as they do for the live cloud.

        Issue #3439. The later-check organization runs the real read too. Its
        session loses page two only for a request with the lose-page header.
        The portal keeps a whole read for one minute, so that request clears
        the kept reads first. A kept read would hide the lost page.

    Args:
        name: The read name that the route asked for.
        **parameters: The call parameters. Only the two real-walk organizations change the result.

    Returns:
        The records of the named read, or an empty list for any other name.
        A real-walk organization gets the records and the partial reasons.
    """
    if parameters.get("org_id") in (LOST_PAGE_ORG_ID, LATER_CHECK_ORG_ID):  # Issues #3438 and #3439: real walks.
        from src.interfaces.portals.upgrade_portal.app.routes import (
            select,
        )  # Late, so the module holds the seam of the child server.

        if LaterCheckCloudSession.lose_page_requested():  # Issue #3439: a kept whole read would hide the lost page.
            logger.info("Clear the kept cloud reads, so the read of %s loses page two", name)  # Log before the clear.
            select.CLOUD_READ_CACHE.clear()  # The next read reaches the session, which loses page two.
        logger.info("Run the real page walk of %s for a real-walk organization", name)  # Log before the read.
        read = select.default_cloud_read(name, **parameters)  # The real walk over the session of the operator.
        logger.debug("The real-walk read %s holds %s record(s)", name, len(read.records))  # Log the count only.
        return read  # The records and the partial reasons of the read.
    del parameters  # Every other organization answers the fixed records below.
    if name == "listOrgSites":  # The name and the identifier of each site.
        return [
            {"id": STAND_IN_SITE_ID, "name": STAND_IN_SITE_NAME},  # The default site of the single-site tests.
            {"id": SECOND_SITE_ID, "name": SECOND_SITE_NAME},  # The extra site that the multi-site journeys add.
            {"id": JOURNEY_SITE_ID, "name": JOURNEY_SITE_NAME},  # Issue #3377: the site of the upgrade journey.
            {"id": EMPTY_SITE_ID, "name": EMPTY_SITE_NAME},  # Issue #3389: the site that holds no device.
            {"id": SHORT_SITE_ID, "name": SHORT_SITE_NAME},  # Issue #3424: the site whose read stops early.
        ]
    if name == "listOrgSiteStats":  # The device count of each site, read from `num_devices`.
        return [
            {"id": STAND_IN_SITE_ID, "num_devices": len(STAND_IN_DEVICE_TYPES)},  # One device of each type.
            {"id": SECOND_SITE_ID, "num_devices": len(STAND_IN_DEVICE_TYPES)},  # One device of each type.
            {"id": JOURNEY_SITE_ID, "num_devices": len(STAND_IN_DEVICE_TYPES)},  # One device of each type.
            {"id": EMPTY_SITE_ID, "num_devices": 0},  # Issue #3389: the picker shows zero devices.
            {"id": SHORT_SITE_ID, "num_devices": SHORT_SITE_DEVICE_COUNT},  # Issue #3424: more than the read finds.
        ]
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
        "ip": f"192.0.2.{index}",  # A documentation-range address for the inventory address column.
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


def stand_in_site_devices(site_id: str) -> list[dict[str, Any]]:
    """Answer the device inventory of one named stand-in site.

    Why:
        Issue #3249. The multi-site device table shows one row for each device,
        and each row keys its test identifier by the MAC address. Two sites
        with the same addresses would give two rows the same identifier. The
        second site therefore holds its own addresses and its own identifiers.
        Issue #3424: the short-read site holds its own addresses too.

    Args:
        site_id: The site whose inventory the caller reads.

    Returns:
        One device record for each device type of the named site. The empty
        site of issue #3389 holds no device.
    """
    if site_id == EMPTY_SITE_ID:  # Issue #3389: the site that the picker shows with zero devices.
        return []  # The inventory read of the site finds no device.
    devices = stand_in_device_read()  # The first site keeps the inventory of every single-site test.
    series = SITE_DEVICE_SERIES.get(site_id)  # The address digit and the name word of a site with its own devices.
    if series is None:  # Only the second site and the short-read site need other addresses.
        return devices  # Keep the first site unchanged.
    digit, label = series  # One digit for the addresses, and one word for the names.
    return [
        {
            **device,  # Keep the type, the model, the version, and the state of the first-site device.
            "id": f"e2e-device-0{digit}0{number}",  # A row key that no other site holds.
            "name": f"E2E {label} {device['type']} {number}",  # A name that no other site holds.
            "mac": f"000000000{digit}0{number}",  # An address that no other site holds.
            "serial": f"E2ESERIAL0{digit}0{number}",  # A serial number that no other site holds.
            "ip": f"192.0.2.{digit}0{number}",  # A documentation-range address that no other site holds.
            "site_id": site_id,  # The site that owns this device.
        }
        for number, device in enumerate(devices, start=1)
    ]


def stand_in_running_versions(cloud_session: Any, site_id: str) -> dict[str, str]:
    """Answer the running version of each device of one stand-in site.

    Why:
        Issue #3249. The multi-site device table reads the version after the
        upgrade through `RunningFirmwareVersionResolver`, which calls the Mist
        cloud. This reader answers fixed values. The first site runs the new
        version, and the second site still runs the old version.

    Args:
        cloud_session: The cloud session. This stand-in reads none of it.
        site_id: The site whose devices the caller reads.

    Returns:
        The running version of each device, keyed by the MAC address.
    """
    del cloud_session  # The stand-in reads no credential.
    version = STAND_IN_VERSIONS[1] if site_id == STAND_IN_SITE_ID else STAND_IN_VERSIONS[0]  # New, then old.
    return {str(device["mac"]): version for device in stand_in_site_devices(site_id)}  # One reading each.


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


def stand_in_view_of(devices: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the options view of one stand-in inventory with the shipped helpers.

    Why:
        Issue #3377. Each type control of the options page draws its versions
        from the `type_selections` field, so a view without it gives each
        control the empty prompt only. This helper calls the two shipped
        helpers in the shipped order, so the browser reads the view shape that
        ships. Issue #3424: the shipped view also answers `partial_reasons`,
        and a complete read answers an empty list there.

    Args:
        devices: The inventory of one stand-in site.

    Returns:
        The device rows, the version list of each model, the version selection
        of each device type, and no partial reason.
    """
    from src.interfaces.portals.upgrade_portal.upgrade import (
        options,
    )  # Late, so a plain collection never loads the portal.

    logger.info("Build the stand-in options view of %s device(s)", len(devices))  # Record the build before it runs.
    by_model = stand_in_version_map()  # Every stand-in model offers the same two versions.
    type_selections = options.TypedVersionSelector().select(devices, by_model)  # The shipped default of each type.
    rows = options.build_version_options(devices, by_model, type_selections)  # The shipped rows use the same pick.
    logger.debug("The stand-in options view holds %s row(s) and %s type(s)", len(rows), len(type_selections))
    return {
        "targets": rows,  # One row for each device.
        "versions_by_model": {name: list(items) for name, items in by_model.items()},  # The shipped list shape.
        "type_selections": type_selections,  # The candidates of each type control.
        "partial_reasons": [],  # Issue #3424: a complete read, so the page shows no Caution banner.
    }


def stand_in_site_view(site_id: str, devices: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the options view of one named site, with the gap of a short read.

    Why:
        Issue #3424. The shipped read of the short-read site keeps the rows of
        the first page and one partial reason. This view gives the same shape,
        so each options page shows the Caution banner for that site only.

    Args:
        site_id: The site under upgrade.
        devices: The inventory rows that the read of the site kept.

    Returns:
        The view of `stand_in_view_of`. The short-read site also holds one
        partial reason.
    """
    view = stand_in_view_of(devices)  # The shipped rows of the devices that the read kept.
    if site_id == SHORT_SITE_ID:  # Only the short-read site lost the rows of a later page.
        logger.info("The stand-in view of site %s reports a short read", site_id)  # Record the gap before it ships.
        view["partial_reasons"] = [dict(SHORT_SITE_REASON)]  # A detached copy, so no page changes the seed.
    logger.debug("The stand-in view of site %s holds %s reason(s)", site_id, len(view["partial_reasons"]))
    return view  # The options page draws the rows and reads the reasons.


def stand_in_options_view(session: Any, org_id: str, site_id: str) -> dict[str, Any]:
    """Answer the device rows and the version map that the options page draws.

    Why:
        `build_options_view` reads the site inventory from the cloud. This seam
        answers the stand-in inventory through `stand_in_view_of`, which calls
        the shipped helpers. The browser therefore reads the rows that ship and
        the test never proves a shape that only this file builds.
        Issue #3424: a run of the short-read site reads that site, so its page
        shows the Caution banner. Every other run reads the first site.

    Args:
        session: The cloud session. This stand-in reads none of it.
        org_id: The organization that holds the site.
        site_id: The site under upgrade.

    Returns:
        The device rows, the version list of each model, the version selection
        of each device type, and the partial reasons of the read.
    """
    del session, org_id  # One organization answers every call.
    short = site_id == SHORT_SITE_ID  # Only the short-read site holds its own inventory in a single-site run.
    devices = stand_in_site_devices(site_id) if short else stand_in_device_read()  # The first site serves the rest.
    return stand_in_site_view(site_id, devices)  # The short-read site also reports its gap.


def stand_in_org_options_view(session: Any, org_id: str, site_id: str) -> dict[str, Any]:
    """Answer the device rows of one named site for the multi-site options page.

    Why:
        Issue #3249. `stand_in_options_view` answers one site for most calls,
        so each selected site showed the same MAC addresses. This view reads the
        inventory of the named site through `stand_in_site_view`.

    Args:
        session: The cloud session. This stand-in reads none of it.
        org_id: The organization that holds the site.
        site_id: The site under upgrade.

    Returns:
        The device rows of the named site, the version list of each model, the
        version selection of each device type, and the partial reasons.
    """
    del session, org_id  # One organization answers every call.
    return stand_in_site_view(site_id, stand_in_site_devices(site_id))  # The inventory and the gap of the site.


def stand_in_options_builder(
    record: dict[str, Any],
    body: dict[str, Any],
    devices: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Widen the two fields of each browser choice into the whole target record.

    Why:
        The browser sends a device address and a version only, and the run
        driver reads a record of fifteen fields. `build_options_record` reads
        the site inventory from the cloud to fill the rest. This seam gives that
        read from the stand-in inventory and then calls the shipped builders.

    Args:
        record: The run record. Issue #3424: the builder reads its site only.
        body: The request body of the options call.
        devices: The inventory of the named site, or None for the first site.
            Issue #3249: a multi-site call names the inventory of its site.

    Returns:
        The target list, the chosen options, and the warning sentences. An
        empty mapping when the named site holds no device, as the shipped
        `build_options_record` answers.

    Raises:
        PartialInventoryError: Issue #3424. The read of the short-read site
            stops after the first page, as the shipped builder refuses it.
    """
    from src.interfaces.portals.upgrade_portal.upgrade import (
        options,
    )  # Late, so a plain collection never loads the portal.

    site_id = str(record.get("site_id") or "")  # Issue #3424: only the site of the record changes the result.
    if site_id == SHORT_SITE_ID:  # The shipped builder refuses a read that stopped after the first page.
        logger.info("The stand-in builder refuses the short read of site %s", site_id)  # Record the refusal.
        raise options.PartialInventoryError(site_id, [dict(SHORT_SITE_REASON)])  # The shipped refusal and reason.
    if devices is not None and not devices:  # Issue #3389: the shipped rule for a site with no device.
        return {}  # The route then names the site in its refusal.
    choices = body.get("targets")
    rows = [one for one in choices if isinstance(one, dict)] if isinstance(choices, list) else []
    inventory = stand_in_device_read() if devices is None else devices  # A single-site run reads the first site.
    entries = options.build_targets(inventory, rows)
    return {
        "targets": entries,
        "options": asdict(options.build_options(body)),
        "warnings": list(options.target_warnings(entries)),
    }


def stand_in_capture_runner(job: dict[str, Any]) -> None:
    """Report one capture as read and verified, and reach no cloud.

    Why:
        The shipped collector reads a live tenant, which no browser test may do.
        The confirm page opens its gate only after a pre-check capture verifies,
        and `capture.record_status` is the one writer that learns of that event.
        This seam reports through that same writer, so the run record gains its
        pre-check field by the shipped path and never by a test shortcut.

        Issue #3243. The shipped collector also stores a capture that names no
        run. The multi-site gate reads that stored capture, so this seam stores
        one in the process-owned capture store before it reports the end state.

        Issue #3244. The multi-site watch takes a post-check capture of each
        site after the last phase ends. That capture names no run either, and
        the compare page reads it, so this seam stores it with the new version.

    Args:
        job: The capture job. This seam reads the key, the tier, the run, the
            role, and the site.
    """
    from src.interfaces.portals.upgrade_portal.app.routes import (
        capture,
    )  # Late, so a plain collection never loads the portal.

    tier = int(job.get("tier", capture.TIER_STANDARD))  # The tier that the operator chose.
    role = str(job.get("role") or "")  # The pre-check or the post-check.
    if not job.get("run_id") and role in STANDALONE_ROLE_VERSIONS:  # A standalone capture stores its own capture.
        logger.info("The stand-in capture runner stores the standalone %s capture %s", role, job["capture_id"])
        stored = stand_in_capture(  # The same shape as each seeded capture, for the named site.
            str(job["capture_id"]), role, STANDALONE_ROLE_VERSIONS[role], stand_in_stamp(), site_id=str(job["site_id"])
        )
        flask.current_app.config["CAPTURE_STORE"].write_capture({**stored, "run_id": "", "tier": tier})
        logger.debug("The stand-in capture runner stored one standalone %s capture", role)  # Log after the write.
    opened = capture.section_map(tier)  # One state for each section name.
    read = {name: capture.SECTION_DONE if state != capture.SECTION_SKIPPED else state for name, state in opened.items()}
    capture.record_status(
        str(job["capture_id"]),
        state=capture.STATE_VERIFIED,
        percent=capture.WHOLE_PERCENT,
        sections=read,  # A skipped section stays skipped, because this seam read no section at all.
        verified=True,
        message=STAND_IN_CAPTURE_MESSAGE,
    )


def stand_in_stamp() -> str:
    """Return the current moment in ISO 8601 with a UTC offset.

    Why:
        Issue #3243. A standalone pre-check that the browser starts must sort
        after each seeded capture, so the gate reads the newest capture.

    Returns:
        The current moment, such as `2026-09-18T01:02:03+00:00`.
    """
    from datetime import UTC, datetime  # Late, so the import list of this module stays unchanged.

    return datetime.now(UTC).isoformat(timespec="seconds")  # A whole second is enough for the order.


def stand_in_run_launcher(record: dict[str, Any]) -> None:
    """Take one started run and drive no device at all.

    Why:
        `install_seams` binds the shipped driver, which opens threads, reads the
        Mist cloud, and writes firmware to hardware. A browser test may do none
        of those. The start route writes the state `upgrade_submitting` and
        stores the record before it calls this seam, so the run still reads as
        started and the progress poll still answers.

    Args:
        record: The run record, already in the state `upgrade_submitting`.
    """
    logger.info("The stand-in launcher took the run %s and sent nothing", record.get("run_id", ""))


def stand_in_stop_runner(run_id: str) -> None:
    """Take one stop request and cancel nothing at any cloud.

    Why:
        The shipped cancel work calls the Mist cloud once for each device that
        has not started, and a browser test may send no such call. FR-038f
        forbids a claim of a cancel that never happened, and the route builds
        three empty lists when this seam answers None, so the operator reads
        only what the portal did do.

    Args:
        run_id: The run key.
    """
    logger.info("The stand-in stop runner took the run %s and cancelled nothing", run_id)


def stand_in_client(index: int, device_mac: str) -> dict[str, Any]:
    """Build one wireless client record that hangs off one device.

    Why:
        The comparison reports a client return rate, and a rate needs a client
        on each side of the pair. The client names its device, because the
        comparison also reports the clients that moved to another device.

    Args:
        index: The number of this client. It fills the address and the name.
        device_mac: The address of the device that holds this client.

    Returns:
        One client record, in the shape that the capture stores.
    """
    return {"mac": f"aabbcc00000{index}", "hostname": f"e2e-client-{index}", "device_mac": device_mac}


def stand_in_capture(
    capture_id: str, role: str, version: str, started_at: str, site_id: str = STAND_IN_SITE_ID
) -> dict[str, Any]:
    """Build one stored capture of the stand-in site.

    Why:
        The comparison journey and the history journey both need a stored
        capture, and no browser test can write one. The device map comes from
        the shipped `build_device_index`, so the test proves the stored shape
        and never a shape that this file alone builds. Issue #3492: the count
        map comes from the shipped `build_counts` for the same reason.

    Args:
        capture_id: The business key that the picker publishes.
        role: `pre` for the first capture. `post` for the second.
        version: The firmware version that every device reports.
        started_at: The start stamp, in ISO 8601 with a UTC offset.
        site_id: The site that the capture reads. Issue #3243: a multi-site
            pre-check names the second site too.

    Returns:
        One capture document, ready for the comparison and for the history.
    """
    from src.interfaces.portals.upgrade_portal.capture import (
        devices,
    )  # Late, so a plain collection never loads the portal.

    records = [{**device, "version": version} for device in stand_in_site_devices(site_id)]  # The site inventory.
    logger.info("Build seed statistics for capture %s with inventory=%d", capture_id, len(records))
    statistics = [  # Running fields must come from statistics, not configured inventory.
        {
            "mac": record["mac"],
            "version": version,
            "status": "connected",
            "ip": record["ip"],
            "uptime": 3600,
        }
        for record in records
    ]
    logger.debug("Built seed statistics. Checked inventory=%d statistics=%d", len(records), len(statistics))
    logger.info("Build the seed device index with inventory=%d statistics=%d", len(records), len(statistics))
    index = devices.build_device_index(records, statistics)
    logger.debug("Built the seed device index. Checked statistics=%d index=%d", len(statistics), len(index))
    clients = [stand_in_client(number, str(one["mac"])) for number, one in enumerate(records, start=1)]  # Radios.
    site_name = SECOND_SITE_NAME if site_id == SECOND_SITE_ID else STAND_IN_SITE_NAME  # The name of the site row.
    capture: dict[str, Any] = {  # The stored shape. Issue #3492: the count map follows below.
        "capture_id": capture_id,
        "run_id": STAND_IN_RUN_ID,
        "org_id": STAND_IN_ORG_ID,
        "org_name": STAND_IN_ORG_NAME,
        "site_id": site_id,
        "site_name": site_name,
        "role": role,
        "ordinal": 1 if role == "pre" else 2,
        "capture_status": "complete",  # The content status that the shipped writer stores for a whole capture.
        "state": "verified",  # The lifecycle state that the shipped writer stores after the read-back.
        "actor_email": STAND_IN_EMAIL,
        "schema_version": 1,
        "tier": 2,
        "started_at": started_at,
        "finished_at": started_at,
        "duration_seconds": 1.0,
        "stored_size_bytes": 4096,
        "device_index": index,
        "devices": records,
        "clients": {"wired": [], "wireless": clients, "guest": []},
        "counts": {},  # Issue #3492: `stand_in_counts` fills this map below, so the key order stays the same.
        "partial_reasons": [],
    }
    capture["counts"] = stand_in_counts(capture)  # Issue #3492: the nine counts of a real capture.
    return capture  # One capture document with the count map of the shipped builder.


def stand_in_counts(capture: dict[str, Any]) -> dict[str, int]:
    """Build the count map of one seed capture with the shipped builder.

    Why:
        Issue #3492. A real capture holds the nine counts of `build_counts`,
        and three of them count the devices of each type. A count map written
        by hand held three keys only, so each seed row of the history read
        "No device type". The function reads the builder through the module
        name at call time, so a direct test can replace the builder.

    Args:
        capture: One seed capture with its device index, its device records,
            and its client lists.

    Returns:
        The nine counts that a real capture of the same lists holds.
    """
    from src.interfaces.portals.upgrade_portal.capture import (
        assembly,
    )  # Late, so a plain collection never loads the portal.

    logger.info("Build the count map of the seed capture %s", capture["capture_id"])  # Log before the build.
    sections = assembly.CaptureSections(  # The three parts of a capture that the builder reads.
        device_index=capture["device_index"],  # The joined type and state of each device.
        devices=capture["devices"],  # The device records of the site.
        clients=capture["clients"],  # The wired, the wireless, and the guest client lists.
    )
    counts = assembly.build_counts(sections)  # The shipped writer of the count map of a real capture.
    logger.debug("The seed capture %s holds the counts %s", capture["capture_id"], counts)  # Log after the build.
    return counts  # The caller stores the map in the capture document.


def stand_in_tier3_capture() -> dict[str, Any]:
    """Build one verified Tier 3 capture for the browser tests.

    Why:
        The browser must show each stored Tier 3 section. Contract tests cannot
        prove that the browser renders the rows or downloads the same rows.

    Returns:
        One capture with populated, empty, and unavailable Tier 3 sections.
    """
    capture = stand_in_capture(TIER3_CAPTURE_ID, "pre", STAND_IN_VERSIONS[0], TIER3_CAPTURE_STAMP)
    switch_mac = str(capture["devices"][1]["mac"])
    ap_mac = str(capture["devices"][0]["mac"])
    capture["tier"] = 3
    capture["clients"]["guest"] = [
        {
            "mac": "aabbcc000099",
            "hostname": "e2e-guest-1",
            "username": "guest@example.invalid",
            "device_mac": ap_mac,
            "device_name": "e2e-ap-1",
            "ssid": "guest-wifi",
        }
    ]
    capture["counts"] = stand_in_counts(capture)  # Issue #3492: the count map now counts the guest client too.
    capture["capture_status"] = "partial"  # The failed BGP read makes the stored content incomplete.
    capture["extras"] = {
        "switch_ports": [{"mac": switch_mac, "port_id": "ge-0/0/1", "up": True, "speed": 1000}],
        "poe": [{"mac": switch_mac, "port_id": "ge-0/0/1", "poe_on": True, "power_draw": 4.5}],
        "radios": [{"mac": ap_mac, "band": "5", "channel": 36, "power": 12}],
        "tunnels": [],
        "bgp_peers": [],
        "alarms": [],
    }
    capture["partial_reasons"] = [{"section": "bgp_peers", "reason": "cloud_call_failed", "http_status": 0}]
    return capture


def stand_in_standalone_precheck() -> dict[str, Any]:
    """Build the one seeded pre-check of the first site that names no run.

    Why:
        Issue #3360. The shipped pre-check adopter adopts only a verified
        pre-check that names no run. The run `e2e-run-0001` owns every other
        seed, so the first site needs this seed for a ready row on the
        multi-site pre-check card.

    Returns:
        One verified standalone pre-check of the first stand-in site.
    """
    capture = stand_in_capture(  # The same shape as each seeded capture of the first site.
        STANDALONE_PRE_CAPTURE_ID, "pre", STAND_IN_VERSIONS[0], STANDALONE_PRE_CAPTURE_STAMP
    )
    capture["run_id"] = ""  # A standalone pre-check names no run, which is the rule of the shipped reader.
    capture["capture_status"] = "partial"  # Issue #3375: adoption must use lifecycle state, not content completeness.
    capture["partial_reasons"] = [{"section": "bgp_peers", "reason": "cloud_call_failed", "http_status": 0}]
    return capture  # The index stores it before the Tier 3 capture.


def stand_in_shipped_shape_capture() -> dict[str, Any]:
    """Build the one seed that holds both status words of the shipped store.

    Why:
        Issue #3378. The status endpoint reads a stored capture after a restart.
        It used to copy the content word into the lifecycle word, and the page
        polls until the lifecycle word ends. This seed holds `complete` and
        `verified`, which the shipped store writes, so a journey proves that the
        page stops.

    Returns:
        One stored capture on its own site, in the shipped shape.
    """
    capture = stand_in_capture(  # The same device map and client rows as every other seed.
        STORED_POLL_CAPTURE_ID, "pre", STAND_IN_VERSIONS[0], STORED_POLL_CAPTURE_STAMP, STORED_POLL_SITE_ID
    )
    capture["site_name"] = STORED_POLL_SITE_NAME  # The history row names the site of this seed.
    capture["run_id"] = ""  # No run owns this seed, so no run page reads it.
    capture["capture_status"] = "complete"  # The content word that `resolve_status` writes.
    capture["state"] = "verified"  # The lifecycle word that the store writes after the read-back.
    return capture  # The index stores it between the post-check and the Tier 3 capture.


def stand_in_capture_index() -> dict[str, dict[str, Any]]:
    """Build all stored captures of the stand-in site.

    Why:
        Two captures prove comparison behavior. The Tier 3 capture proves the
        browser tables and the two exports with stored section data.

        Issue #3360. The standalone pre-check is the one seed that the
        pre-check adopter may adopt. The index holds it before the Tier 3
        capture. A stand-in that ignores the run therefore adopts the Tier 3
        capture, and the multi-site pre-check journey reports that defect.

        Issue #3378. The seed in the shipped shape sits on its own site,
        between the post-check and the Tier 3 capture. The first entry and the
        last entry of the index therefore stay the same.

    Returns:
        One capture document for each identifier that the picker publishes.
    """
    before = stand_in_capture(PRE_CAPTURE_ID, "pre", STAND_IN_VERSIONS[0], PRE_CAPTURE_STAMP)
    standalone = stand_in_standalone_precheck()  # Issue #3360: the one seed that the adopter may adopt.
    after = stand_in_capture(POST_CAPTURE_ID, "post", STAND_IN_VERSIONS[1], POST_CAPTURE_STAMP)
    shipped = stand_in_shipped_shape_capture()  # Issue #3378: the seed that reads the stored status path.
    tier3 = stand_in_tier3_capture()
    return {  # The store order follows the start times, and the Tier 3 capture comes last.
        PRE_CAPTURE_ID: before,
        STANDALONE_PRE_CAPTURE_ID: standalone,
        POST_CAPTURE_ID: after,
        STORED_POLL_CAPTURE_ID: shipped,
        TIER3_CAPTURE_ID: tier3,
    }


def stand_in_capture_lister(site_id: str = "", limit: int = 0, offset: int = 0) -> list[dict[str, Any]]:
    """Answer the history rows of the stand-in site, and reach no database.

    Why:
        `list_captures` reads ArangoDB, so the history page and both capture
        pickers stay empty on a workstation with no database. This seam answers
        the small row that the contract fixes, which is never the whole capture.

    Args:
        site_id: The site to narrow to. An empty value reads every site.
        limit: The page size. One page holds both rows, so this changes nothing.
        offset: The page start. One page holds both rows, so this changes nothing.

    Returns:
        One row for each stored capture, newest first.
    """
    del limit, offset  # Two rows fit in every page size the routes ask for.
    if site_id and site_id != STAND_IN_SITE_ID:  # A second site holds no stored capture.
        return []
    stored = stand_in_capture_index().values()
    return [{name: one[name] for name in HISTORY_ROW_NAMES} for one in stored][::-1]


@dataclass(frozen=True, slots=True)
class StandInCaptureLoad:
    """One stored capture read, in the shape that the real store answers with.

    Why:
        `capture/store.py` answers every read with a record that holds the
        document, a flag that reports whether the document may join a
        comparison, and a refusal reason. Two route modules read the one
        `CAPTURE_LOADER` seam. `app/routes/review.py` also accepts a bare
        document, but `app/routes/capture.py` reads the three names below and
        refuses every other shape.

        A stand-in that answers a bare document therefore makes
        `GET /api/captures/<capture_id>` answer 500 for a capture that the
        status route calls verified. This record carries the three names, so
        both route modules read the stand-in the way they read the store.

    Attributes:
        capture: The stored document, or None when no document carries the key.
        comparable: True when the capture may join a comparison.
        reason: The refusal code, or an empty string after a clean read.
    """

    capture: dict[str, Any] | None
    comparable: bool
    reason: str


def stand_in_capture_loader(capture_id: str) -> StandInCaptureLoad:
    """Answer one stored capture, and reach no database.

    Why:
        `load_capture_for_comparison` reads ArangoDB, so a workstation with no
        database can compare nothing and can read no capture back. This seam
        answers the record shape of the store, so the comparison route and the
        capture read route both accept it.

    Args:
        capture_id: The business key that the picker published.

    Returns:
        The stored capture, or a refusal when no capture carries that key.
    """
    document = stand_in_capture_index().get(capture_id)  # None for every key the stand-in never published.
    if document is None:  # The store answers the same reason, and the route turns it into a 404.
        return StandInCaptureLoad(None, False, CAPTURE_NOT_FOUND_REASON)
    return StandInCaptureLoad(document, True, "")  # Both stand-in captures carry the verified state.


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


def operator_session_cookies(email: str, browser_id: str, org_id: str = STAND_IN_ORG_ID) -> list[dict[str, str]]:
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
        org_id: The organization that the signed session selects. Issue #3438:
            the lost-page operator selects the lost-page organization.

    Returns:
        One record for each cookie, in the shape that `add_cookies` takes.
    """
    logger.info("Build the session cookies of one stand-in operator")  # Log before the build, with no identity.
    owner = identity.build_owner(email, browser_id)  # The pair the server registered.
    payload = {identity.SESSION_OWNER_KEY: owner.key, SELECTED_ORG_KEY: org_id}  # No personal data.
    signed = signed_session_cookie(payload)  # The value that the portal reads back and trusts.
    session_cookie = {"name": SESSION_COOKIE_NAME, "value": signed, "url": BASE_URL}  # The signed half.
    browser_cookie = {"name": identity.BROWSER_ID_COOKIE, "value": browser_id, "url": BASE_URL}  # The other half.
    logger.debug("Built two session cookies for organization %s", org_id)  # Log the count and the organization.
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


def firmware_operator_cookies() -> list[dict[str, str]]:
    """Build the two cookies of the firmware-write stand-in operator.

    Why:
        Issue #2615 refuses reserved domains before firmware moves. Most
        browser tests use a reserved address to prove that read-only pages do
        not need a real mailbox. A browser flow that starts firmware needs this
        reachable stand-in, so it tests the confirmed write path and not the
        refusal path.

    Returns:
        One record for each cookie, in the shape that `add_cookies` takes.
    """
    return operator_session_cookies(FIRMWARE_EMAIL, FIRMWARE_BROWSER_ID)  # The write gate accepts this address.


def controls_operator_cookies() -> list[dict[str, str]]:
    """Build the two cookies of the operator that owns the recovery seeds.

    Why:
        Issue #3247. A retry changes the site selection of its operator. A
        separate operator keeps that change away from every other journey.

    Returns:
        One record for each cookie, in the shape that `add_cookies` takes.
    """
    return operator_session_cookies(CONTROLS_EMAIL, CONTROLS_BROWSER_ID)  # The owner of both recovery seeds.


@pytest.fixture
def browser_token_value() -> str:
    """Return the fake browser token that the server stand-in accepts.

    Why:
        The value is an obvious fake, and the test must submit the same value
        that the isolated server accepts. A fixture keeps the test independent
        from a live secret source.

    Returns:
        The fake browser-token value for this suite.
    """
    return BROWSER_TOKEN_VALUE  # The route stand-in accepts this fake value only.


@pytest.fixture
def browser_token_evidence_path() -> Path:
    """Return the file that records browser-token stand-in events.

    Why:
        The server process writes this file, and the test process reads it.
        The file records only safe facts and never the submitted token value.

    Returns:
        The evidence file path for this E2E server.
    """
    return BROWSER_TOKEN_EVIDENCE_PATH  # The parent and child resolve the same artifact path.


@pytest.fixture
def browser_token_server_log_path() -> Path:
    """Return the log file of the isolated browser-test server.

    Why:
        The browser-token journey must prove that the submitted token does not
        reach the portal log.

    Returns:
        The server log path for this E2E server.
    """
    return SERVER_LOG_PATH  # The child writes its log to this file.


def _register_operator(email: str, browser_id: str, cloud_session: StandInCloudSession | None = None) -> None:
    """Place one signed-in operator record into the process registry.

    Why:
        `identity.SESSION_REGISTRY` holds a record for each operator pair, and a
        request with no record reads 401. The server process must write every
        record itself, because the registry is a dictionary inside one process.

    Args:
        email: The work address of the operator, already normalized.
        browser_id: The browser identifier of that operator.
        cloud_session: The cloud session of the operator. No value gives the
            stand-in session of the first organization. Issue #3438: the
            lost-page operator carries its own session.
    """
    logger.info("Register one stand-in operator in the process registry")  # Log before the write, no identity.
    owner = identity.build_owner(email, browser_id)  # The pair a cookie also names.
    mode = identity.CredentialMode.ENVIRONMENT_TOKEN  # The mode a token sign-in would have recorded.
    session = cloud_session or StandInCloudSession()  # The first organization, unless the caller names a session.
    identity.SESSION_REGISTRY.register(identity.OperatorSession(owner, session, mode))  # One record per pair.
    logger.debug("Registered one operator with a %s", type(session).__name__)  # Log the session class only.


PREPARED_RUN_ID = "e2e-prepared-run-0001"  # The seeded run that proves the confirmation link works.
START_READY_RUN_ID = "e2e-start-ready-run-0001"  # The seeded run that proves the firmware start call.
BULK_RETRY_RUN_ID = "e2e-bulk-retry-run-0001"
BULK_RETRY_SITE_ID = "55555555-5555-5555-5555-555555555555"
LIFECYCLE_RUN_ID = "e2e-lifecycle-run-0001"
LIFECYCLE_SITE_ID = "66666666-6666-6666-6666-666666666666"
PREPARED_SITE_ID = "e2e-confirm-site"  # A separate site keeps this live run from blocking other E2E journeys.
START_READY_SITE_ID = "e2e-start-site"  # A separate site keeps the start proof from changing another test.


def _prepared_run_record() -> dict[str, Any]:
    """Build one prepared run that exposes the confirmation navigation."""
    return {
        "run_id": PREPARED_RUN_ID,
        "site_id": PREPARED_SITE_ID,
        "org_id": STAND_IN_ORG_ID,
        "state": "awaiting_confirmation",
        "message": "The stand-in plan is ready for final review.",
        "pre_capture_id": "e2e-pre-capture-0001",
        "targets": [
            {
                "device_id": "e2e-gateway-0001",
                "name": "E2E gateway",
                "model": "SRX-1500",
                "type": "gateway",
                "current_version": "23.4R2-S5.5",
                "target_version": "23.4R2-S6.1",
            }
        ],
        "options": {"strategy": "big_bang", "reboot": True},
    }


def _start_ready_run_record() -> dict[str, Any]:
    """Build one prepared run that the start journey can mutate."""
    record = _prepared_run_record()  # Reuse the validated ready-run shape for the start-only fixture.
    record["run_id"] = START_READY_RUN_ID  # Give the start test its own record so order cannot change another test.
    record["site_id"] = START_READY_SITE_ID  # Give the start test its own site so no live-run guard hides the path.
    record["message"] = "The stand-in plan is ready for a measured firmware start."  # State the test purpose.
    return record  # Return a mutable copy that the start route may advance.


def _bulk_retry_run_record() -> dict[str, Any]:
    """Build one isolated failed source for atomic bulk retry."""
    return {
        "run_id": BULK_RETRY_RUN_ID,
        "site_id": BULK_RETRY_SITE_ID,
        "site_name": "Bulk retry site",
        "org_id": STAND_IN_ORG_ID,
        "org_name": "E2E organization",
        "state": "failed",
        "updated_at": "2026-09-11T13:00:00+00:00",
        "targets": [{"device_id": "e2e-bulk-target", "target_version": "1.2.3"}],
        "options": {"strategy": "big_bang", "reboot": True},
        "tier": 2,
    }


def _lifecycle_run_record() -> dict[str, Any]:
    """Build one stale pre-cloud run for browser lifecycle tests."""
    return {
        "run_id": LIFECYCLE_RUN_ID,
        "site_id": LIFECYCLE_SITE_ID,
        "site_name": "Lifecycle test site",
        "org_id": STAND_IN_ORG_ID,
        "org_name": "E2E organization",
        "state": "awaiting_confirmation",
        "updated_at": "2026-09-01T10:00:00+00:00",
        "targets": [],
        "options": {},
    }


def _seed_fixture_runs(built: Any, upgrade: Any) -> None:
    """Write the failed and prepared browser fixtures without delaying server start.

    A cold store can take longer to initialize than the fixture's port wait. The
    background thread lets the portal bind first; each test waits for its seeded
    run before it asserts the related control.
    """
    logger.info(
        "Seeding browser fixture runs %s, %s, %s, and %s",
        FAILED_RUN_ID,
        STOPPED_RUN_ID,
        PREPARED_RUN_ID,
        START_READY_RUN_ID,
    )
    writer = threading.Thread(target=_write_fixture_runs, args=(built, upgrade), daemon=True)
    writer.start()
    logger.debug("The browser fixture run seed runs on its own thread")


def _write_fixture_runs(built: Any, upgrade: Any) -> None:
    """Write each seeded run record, and report a refusal instead of raising."""
    logger.info("Write the seeded run records of the browser server")  # Log before the writes.
    try:  # A refusal must not stop the server, so each related test reports the missing state.
        with built.app_context():  # The store reads the application settings.
            failed_written = upgrade.save_run(RetryRunSeeds.failed_record(STAND_IN_ORG_ID))  # The retry journey run.
            stopped_written = upgrade.save_run(RetryRunSeeds.stopped_record(STAND_IN_ORG_ID))  # The fresh attempt.
            prepared_written = upgrade.save_run(_prepared_run_record())  # The run of the confirmation link.
            start_ready_written = upgrade.save_run(_start_ready_run_record())  # The run of the firmware start.
            stale_written = StaleRunSeeds.write(upgrade, STAND_IN_ORG_ID)  # Issue #3507: on the stale site.
            bulk_retry_written = upgrade.save_run(_bulk_retry_run_record())  # The source of the bulk retry.
            lifecycle_written = upgrade.save_run(_lifecycle_run_record())  # The run of the lifecycle tests.
            org_controls_written = OrgControlSeeds.write(upgrade, identity)  # Issue #3247: two operations.
            org_cancel_written = OrgCancelSeeds.write(upgrade, identity)  # Issue #3246: the running operation.
            org_ended_written = OrgEndedSeeds.write(upgrade, identity)  # Issue #3367: one child job ended first.
            later_check_written = LaterCheckSeeds.write(upgrade, identity)  # Issue #3439: the retry of page two.
    except Exception as failure:  # Any store fault ends the writes, and the warning names the cause.
        logger.warning(
            "The browser fixture runs did not write. Related tests will report the missing state. Cause: %s",
            failure,
        )
        return  # The server keeps running with the records that the store accepted.
    logger.info(
        (
            "Browser fixture run seeds reported failed=%s stopped=%s prepared=%s "
            "start_ready=%s stale=%s bulk_retry=%s lifecycle=%s org_controls=%s "
            "org_cancel=%s org_ended=%s later_check=%s"
        ),
        failed_written,
        stopped_written,
        prepared_written,
        start_ready_written,
        stale_written,
        bulk_retry_written,
        lifecycle_written,
        org_controls_written,
        org_cancel_written,
        org_ended_written,
        later_check_written,
    )


def _reset_cached_state() -> None:  # Clear each process cache before isolated construction.
    """Reset every storage and readiness cache before E2E application construction."""
    logger.info("Reset the E2E storage and readiness caches")  # Record the reset before it starts.
    from src.interfaces.portals.upgrade_portal.app import (
        factory,
        wiring,
    )  # Load reset functions without constructing an application.
    from src.interfaces.portals.upgrade_portal.capture import (
        store as capture_store,
    )  # Own the cached ArangoDB connection.
    from src.interfaces.portals.upgrade_portal.runtime import lock  # Own the cached Redis connection.

    wiring.reset_storage_bootstrap()  # Prevent an earlier production bootstrap state from crossing into E2E.
    factory.reset_readiness_cache()  # Prevent an earlier readiness result from crossing into E2E.
    capture_store.reset_connection()  # Drop any cached document store handle before the stores install.
    lock.reset_connection()  # Drop any cached lock store handle before the stores install.
    logger.debug("Reset the E2E storage and readiness caches")  # Confirm the complete reset.


def _build_factory_overrides() -> E2EFactoryOverrides:  # Assemble one complete isolated dependency value.
    """Build the complete process-owned dependency set for one E2E server."""
    logger.info("Build the E2E factory override set")  # Record construction before any route exists.
    seams = {  # Name each existing stand-in that the support builder must install.
        "captures": stand_in_capture_index().values(),  # Seed each process-owned capture of the stand-in site.
        "capture_runner": stand_in_capture_runner,  # Complete captures without a cloud call.
        "run_launcher": stand_in_run_launcher,  # Accept a run without firmware work.
        "stop_runner": stand_in_stop_runner,  # Accept a stop without a cloud call.
        "options_builder": stand_in_options_builder,  # Build options from stand-in inventory.
        "options_view": stand_in_options_view,  # Render options from stand-in inventory.
        "versions_reader": lambda *_arguments: stand_in_version_map(),  # Return fixed firmware versions.
        "cloud_reader": stand_in_cloud_read,  # Read fixed organization and site rows.
        "device_reader": stand_in_device_read,  # Read fixed device rows.
        "cloud_scripts": {
            "reconciliation": {
                "value": [
                    {
                        "target_id": "e2e-target-one",
                        "stored_stop_result": "cancel_accepted",
                        "task_id": "e2e-task-one",
                        "task_state": "final",
                        "write_state": "not_writing",
                        "driver_state": "stopped",
                        "sources": ["stored", "cloud_task", "device", "driver"],
                        "observed_at": "2026-09-11T14:00:00+00:00",
                        "is_complete": True,
                        "has_conflict": False,
                    }
                ]
            }
        },
    }
    overrides = build_e2e_overrides(TEST_RUN_ID, seams)  # Create all stores before the factory call.
    logger.debug("Built the complete E2E factory override set")  # Confirm construction without record values.
    return overrides  # The factory validates this value before blueprint registration.


def build_stand_in_app() -> Any:  # Build one fully isolated browser test application.
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
    from src.interfaces.portals.upgrade_portal.app.factory import (
        create_app,
    )  # Late, so a plain collection never builds an app.
    from src.interfaces.portals.upgrade_portal.app.routes import upgrade  # Own the seeded run write helper.
    from src.interfaces.portals.upgrade_portal.runtime import (
        lock,
    )  # Issue #3512: the module that names the checkout trail.

    _reset_cached_state()  # Clear each cached production handle before the override set installs.
    # WHY: Issue #3498. The site lock writes each lock action to the checkout
    # trail, which is the production audit trail in the main checkout. This
    # child moves the trail into the artifact directory of its run before any
    # route exists. The history page reads the same trail, so the audit log
    # of this portal shows the lock actions of this run alone.
    # Issue #3512: the child runs no pytest fixture, so no move applies before
    # this read. The parent reads the same path from the root guard.
    checkout_trail = lock.audit_trail_path()  # The lock module still names the checkout trail here.
    AuditTrailIsolation(ARTIFACT_DIRECTORY, checkout_trail).place()  # The move stays for the whole life of the child.
    overrides = _build_factory_overrides()  # Build every required process-owned dependency before routes.
    built = create_app(overrides)  # Validate and install overrides before blueprint registration.
    from src.interfaces.portals.upgrade_portal.app.routes import org_upgrade
    from src.interfaces.portals.upgrade_portal.app.routes import upgrade as upgrade_routes

    # WHY: Issue #2615 reads the Mist account before a firmware write. The
    # browser suite must open no socket at all, so this seam answers a fixed
    # label. Without it the route would call the real software development kit.
    built.config[upgrade_routes.SELF_READER_KEY] = lambda _session: {"email": STAND_IN_EMAIL}

    built.config[org_upgrade.SERVICE_CONFIG_KEY] = E2EOrgUpgradeService
    built.config[org_upgrade.OPTIONS_VIEW_CONFIG_KEY] = stand_in_org_options_view  # Issue #3249: one inventory each.
    built.config[org_upgrade.OPTIONS_BUILDER_CONFIG_KEY] = lambda cloud_session, org_id, site_id, body: (
        stand_in_options_builder({"site_id": site_id}, body, stand_in_site_devices(site_id))  # The named site only.
    )
    # WHY: Issue #3249. The device table reads the running version of each
    # device. This seam answers fixed versions, so the browser suite opens no
    # socket to the Mist cloud.
    built.config[org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY] = stand_in_running_versions
    # WHY: Issue #3245. The submission reads the uptime of each device before
    # the first write, and each page read starts the phase watch. The default
    # anchor read calls the Mist cloud, and the Mist trap counters would record
    # that call. The scripted starter moves the watch one step for each page
    # read, so a journey sees each phase end and starts no thread.
    from tests.support.org_cascade_seams import CascadeSeamStandIn, ScriptedCascadeStarter

    CascadeSeamStandIn().install(built.config)  # The anchor read reaches no cloud.
    built.config[org_upgrade.CASCADE_STARTER_CONFIG_KEY] = ScriptedCascadeStarter()  # One step for each read.
    from src.operations.execution.firmware.aggregate_upgrade_service import AggregateUpgradeService

    built.config[org_upgrade.AGGREGATE_SERVICE_CONFIG_KEY] = AggregateUpgradeService(
        E2EOrgUpgradeService,
        E2EDeviceUpgradeService,
    )
    built.config[org_upgrade.WRITES_ENABLED_CONFIG_KEY] = True
    built.config["CLOUD_BROWSER_TOKEN_SESSION"] = stand_in_browser_token_session  # Replace the live token builder.
    built.config["CLOUD_TOKEN_IDENTITY"] = stand_in_token_identity  # Replace the live GetSelf identity read.
    _register_operator(STAND_IN_EMAIL, STAND_IN_BROWSER_ID)  # The operator that every test drives.
    _register_operator(SECOND_EMAIL, SECOND_BROWSER_ID)  # The operator that meets the lock refusal.
    _register_operator(STAND_IN_EMAIL, RENEWED_BROWSER_ID)  # The renewed session keeps the durable actor.
    _register_operator(FIRMWARE_EMAIL, FIRMWARE_BROWSER_ID)  # The operator that may start firmware writes.
    _register_operator(CONTROLS_EMAIL, CONTROLS_BROWSER_ID)  # Issue #3247: the owner of the recovery seeds.
    _register_operator(EMPTY_SITE_EMAIL, EMPTY_SITE_BROWSER_ID)  # Issue #3389: the operator of the empty site.
    _register_operator(SHORT_SITE_EMAIL, SHORT_SITE_BROWSER_ID)  # Issue #3424: the operator of the short-read site.
    _register_operator(LOST_PAGE_EMAIL, LOST_PAGE_BROWSER_ID, LostPageCloudSession())  # Issue #3438: lost pages.
    _register_operator(LATER_CHECK_EMAIL, LATER_CHECK_BROWSER_ID, LaterCheckCloudSession())  # Issue #3439.
    _seed_fixture_runs(built, upgrade)  # Browser-only states that no safe page journey can create.
    return built  # Waitress and Gunicorn both load this object by name.


# WHY: Issue #3501. The run owner header is the one test header of the test
# portal. Each page fixture refuses a health read that names no run or another
# run, because a stray portal on the same address holds the records of another
# run. The direct tests in tests/unit/upgrade_portal/test_e2e_run_owner_header.py
# prove that the check can fail.
OWNER_CHECK = RunOwnerHeaderCheck(TEST_RUN_ID)  # One check for each run, built once.


@pytest.fixture(scope="session")
def e2e_test_run_id() -> str:
    """Return the owner identifier that every isolated response must contain."""
    return TEST_RUN_ID


@pytest.fixture
def renewed_operator_cookie_records() -> list[dict[str, str]]:
    """Return a new browser session for the first durable actor."""
    return operator_session_cookies(STAND_IN_EMAIL, RENEWED_BROWSER_ID)


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
    opened = install_screenshot_retry(context.new_page())  # Route every full-page evidence call through one retry.
    isolation_response = opened.goto("/healthz")  # Reject a wrong server before one workflow assertion.
    assert isolation_response is not None and isolation_response.ok  # Prove the test reaches the isolated app.
    OWNER_CHECK.require(isolation_response.headers)  # Refuse a portal of another run.
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
    opened = install_screenshot_retry(context.new_page())
    isolation_response = opened.goto("/healthz")  # Reject a wrong server before one workflow assertion.
    assert isolation_response is not None and isolation_response.ok  # Prove the test reaches the isolated app.
    OWNER_CHECK.require(isolation_response.headers)  # Refuse a portal of another run.
    yield opened
    opened.close()
    context.close()  # The context holds a profile directory until it closes.


@pytest.fixture
def org_operation_ledger(context: Any) -> Iterator[OrgOperationLedger]:
    """Record each multi-site operation that the browser context of one test starts.

    Why:
        Issue #3518. A journey that failed before its cancel left the operation
        live, and the operation held both stand-in sites. A route of the
        context fetches the answer of each Start request of each tab, before
        the page gets it. The teardown of `firmware_operator_page` then ends
        each recorded operation, also when the page never reached the progress
        page. A route turns off the HTTP cache of the context, so only the
        tests that take this fixture pay that cost.

    Args:
        context: The browser context that `pytest-playwright` built.

    Yields:
        The ledger of the context.
    """
    ledger = OrgOperationLedger()  # One ledger for one test.
    tap = OrgStartTap(ledger)  # The tap reads each Start answer before a page gets it.
    context.route(OrgStartTap.ROUTE, tap.pass_start)  # Each tab of the context sends its Start request through it.
    yield ledger  # The page fixture and the teardown journey read the ledger.
    context.unroute(OrgStartTap.ROUTE, tap.pass_start)  # The tap reads nothing after the test.


@pytest.fixture
def firmware_operator_page(
    context: Any, capture_portal_server: str, org_operation_ledger: OrgOperationLedger
) -> Iterator[Any]:
    """Open a browser page that can start a firmware write.

    Why:
        Issue #2615 intentionally refuses the default reserved E2E address for
        firmware writes. This fixture keeps the default reserved session for
        read-only paths and gives write-path tests one registered reachable
        address.

        Issue #3518. Each multi-site journey starts its operation with this
        page. After the test, the fixture ends each operation that is still
        live, so a failed step cannot leave both stand-in sites held.

    Args:
        context: The browser context that `pytest-playwright` built.
        capture_portal_server: The address of the running portal.
        org_operation_ledger: The ledger of each operation that the context started.

    Yields:
        The browser page, with the firmware-write session cookies in place.
    """
    del capture_portal_server  # Requested for its start-up work alone. `base_url` carries the address.
    context.add_cookies(firmware_operator_cookies())  # Both cookies, against the portal address.
    opened = install_screenshot_retry(context.new_page())  # The page then carries the session on its first request.
    isolation_response = opened.goto("/healthz")  # Reject a wrong server before one workflow assertion.
    assert isolation_response is not None and isolation_response.ok  # Prove the test reaches the isolated app.
    OWNER_CHECK.require(isolation_response.headers)  # Refuse a shared, live, or stray server.
    yield opened  # The test uses the reachable operator only where it starts firmware.
    try:  # Close the page also when the teardown fails.
        OrgOperationRelease.end_for(opened, org_operation_ledger)  # Issue #3518: end each live operation.
    finally:  # A page left open would hold a browser target for the whole run.
        opened.close()  # Close the page of the test.


@pytest.fixture
def controls_operator_page(context: Any, capture_portal_server: str) -> Iterator[Any]:
    """Open a browser page of the operator that owns the recovery seeds.

    Why:
        Issue #3247. The retry and the check open only for the owner of an
        operation. The server writes both seeds for this operator.

    Args:
        context: The browser context that `pytest-playwright` built.
        capture_portal_server: The address of the running portal.

    Yields:
        The browser page, with the session cookies of the controls operator.
    """
    del capture_portal_server  # Requested for its start-up work alone. `base_url` carries the address.
    context.add_cookies(controls_operator_cookies())  # Both cookies, against the portal address.
    opened = install_screenshot_retry(context.new_page())  # The page then carries the session on its first request.
    isolation_response = opened.goto("/healthz")  # Reject a wrong server before one workflow assertion.
    assert isolation_response is not None and isolation_response.ok  # Prove the test reaches the isolated app.
    OWNER_CHECK.require(isolation_response.headers)  # Refuse a shared, live, or stray server.
    yield opened  # The test drives the recovery controls of the seeded operations.
    opened.close()  # A page left open would hold a browser target for the whole run.


@pytest.fixture
def empty_site_operator_page(context: Any, capture_portal_server: str) -> Iterator[Any]:
    """Open a browser page of the operator that selects the empty site.

    Why:
        Issue #3389. The stored site set lasts across journeys. A separate
        operator keeps the empty site out of the site set of every other
        journey, also when the journey fails.

    Args:
        context: The browser context that `pytest-playwright` built.
        capture_portal_server: The address of the running portal.

    Yields:
        The browser page, with the session cookies of the empty-site operator.
    """
    del capture_portal_server  # Requested for its start-up work alone. `base_url` carries the address.
    context.add_cookies(operator_session_cookies(EMPTY_SITE_EMAIL, EMPTY_SITE_BROWSER_ID))  # The separate pair.
    opened = install_screenshot_retry(context.new_page())  # The page then carries the session on its first request.
    isolation_response = opened.goto("/healthz")  # Reject a wrong server before one workflow assertion.
    assert isolation_response is not None and isolation_response.ok  # Prove the test reaches the isolated app.
    OWNER_CHECK.require(isolation_response.headers)  # Refuse a shared, live, or stray server.
    yield opened  # The test selects the empty site and then clears it.
    opened.close()  # A page left open would hold a browser target for the whole run.


@pytest.fixture
def short_read_operator_page(context: Any, capture_portal_server: str) -> Iterator[Any]:
    """Open a browser page of the operator that selects the short-read site.

    Why:
        Issue #3424. The stored site set lasts across journeys. A separate
        operator keeps the short-read site out of the site set of every other
        journey, also when the journey fails.

    Args:
        context: The browser context that `pytest-playwright` built.
        capture_portal_server: The address of the running portal.

    Yields:
        The browser page, with the session cookies of the short-read operator.
    """
    del capture_portal_server  # Requested for its start-up work alone. `base_url` carries the address.
    context.add_cookies(operator_session_cookies(SHORT_SITE_EMAIL, SHORT_SITE_BROWSER_ID))  # The separate pair.
    opened = install_screenshot_retry(context.new_page())  # The page then carries the session on its first request.
    isolation_response = opened.goto("/healthz")  # Reject a wrong server before one workflow assertion.
    assert isolation_response is not None and isolation_response.ok  # Prove the test reaches the isolated app.
    OWNER_CHECK.require(isolation_response.headers)  # Refuse a shared, live, or stray server.
    yield opened  # The test selects the short-read site and then clears it.
    opened.close()  # A page left open would hold a browser target for the whole run.


@pytest.fixture
def lost_page_operator_page(context: Any, capture_portal_server: str) -> Iterator[Any]:
    """Open a browser page of the operator whose picker reads lose page two.

    Why:
        Issue #3438. The cloud session of this operator answers page one of
        each picker read and loses page two. A separate operator and a separate
        organization keep the lost pages and the stored site set of this
        operator away from every other journey, also when the journey fails.

    Args:
        context: The browser context that `pytest-playwright` built.
        capture_portal_server: The address of the running portal.

    Yields:
        The browser page, with the session cookies of the lost-page operator.
    """
    del capture_portal_server  # Requested for its start-up work alone. `base_url` carries the address.
    cookies = operator_session_cookies(LOST_PAGE_EMAIL, LOST_PAGE_BROWSER_ID, LOST_PAGE_ORG_ID)  # A separate pair.
    context.add_cookies(cookies)  # The session selects the lost-page organization.
    opened = install_screenshot_retry(context.new_page())  # The page then carries the session on its first request.
    isolation_response = opened.goto("/healthz")  # Reject a wrong server before one workflow assertion.
    assert isolation_response is not None and isolation_response.ok  # Prove the test reaches the isolated app.
    OWNER_CHECK.require(isolation_response.headers)  # Refuse a shared, live, or stray server.
    yield opened  # The test reads the picker of the lost-page organization.
    opened.close()  # A page left open would hold a browser target for the whole run.


@pytest.fixture
def later_check_operator_page(context: Any, capture_portal_server: str) -> Iterator[Any]:
    """Open a browser page of the operator whose site reads lose page two on request.

    Why:
        Issue #3439. A later site check must refuse with the status 503 when
        the site read lost a page. The cloud session of this operator loses
        page two only for a request with the lose-page header. A separate
        operator and a separate organization keep that switch and the stored
        site set of this operator away from every other journey.

    Args:
        context: The browser context that `pytest-playwright` built.
        capture_portal_server: The address of the running portal.

    Yields:
        The browser page, with the session cookies of the later-check operator.
    """
    del capture_portal_server  # Requested for its start-up work alone. `base_url` carries the address.
    cookies = operator_session_cookies(LATER_CHECK_EMAIL, LATER_CHECK_BROWSER_ID, LATER_CHECK_ORG_ID)  # A new pair.
    context.add_cookies(cookies)  # The session selects the later-check organization.
    opened = install_screenshot_retry(context.new_page())  # The page then carries the session on its first request.
    isolation_response = opened.goto("/healthz")  # Reject a wrong server before one workflow assertion.
    assert isolation_response is not None and isolation_response.ok  # Prove the test reaches the isolated app.
    OWNER_CHECK.require(isolation_response.headers)  # Refuse a shared, live, or stray server.
    yield opened  # The test switches the lost page on and off with the request header.
    opened.close()  # A page left open would hold a browser target for the whole run.


@pytest.fixture
def signed_out_page(browser: Any, capture_portal_server: str) -> Iterator[Any]:
    """Open a page with no preloaded portal session.

    Why:
        Browser-token sign-in must start from the real form. The default
        `page` fixture already carries a signed cookie, so this fixture creates
        a separate clean browser context for that journey.

    Args:
        browser: The browser that `pytest-playwright` started.
        capture_portal_server: The address of the running portal.

    Yields:
        The page of a browser context that holds no portal session.
    """
    del capture_portal_server  # Requested for its start-up work alone.
    context = browser.new_context(base_url=BASE_URL)  # A clean cookie jar starts the real sign-in journey.
    opened = install_screenshot_retry(context.new_page())  # The page carries no session cookie on its first request.
    yield opened  # The caller drives the complete sign-in path through the browser.
    opened.close()  # A page left open would hold a browser target for the whole run.
    context.close()  # The context holds a profile directory until it closes.


# WHY: The server process loads this module by name and reads `app`. That name
# exists only when the gate variable holds the enabling value, and only
# `_child_environment` writes that variable, into the child process alone. A
# normal test collection, a normal server start, and every production start
# therefore reach no stand-in session. `wsgi_capture.py` names the production
# application, and this module changes no line of it.
if os.environ.get(E2E_SESSION_VARIABLE) == E2E_SESSION_ENABLED:  # The child process alone opens this gate.
    app = build_stand_in_app()  # The signed-in portal that every browser test of this folder drives.
