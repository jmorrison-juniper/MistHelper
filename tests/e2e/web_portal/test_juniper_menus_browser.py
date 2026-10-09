"""Browser tests for the Juniper RMA menus 294 to 304 in the web portal (issue #3519).

Why:
    An operator uses a menu only when the portal shows it with readable labels, the right
    controls, and output that a person can read. These tests drive a real Chromium browser through
    each step, check the result, and save a screenshot of each state for review.

Scope:
    The portal runs the real Juniper workflows against the double in juniper_browser_harness.py.
    No test reaches Juniper or Mist, no test writes to data/, and no test writes to a database.
    Screenshots go to test-artifacts/juniper-portal/, which Git ignores.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import csv  # WHY: the exports are read back to check the saved values.
import logging  # WHY: the module logger records each step of the browser checks.
import re  # WHY: the group button text is matched by pattern.
import socket  # WHY: a free port keeps a developer's own portal untouched.
import threading  # WHY: the Werkzeug server runs in a thread beside the browser.
from collections.abc import Iterator  # WHY: the fixtures are generators.
from datetime import UTC, datetime, timedelta  # WHY: the snapshot window is relative to today in UTC.
from pathlib import Path  # WHY: the workspace and the screenshot folder are paths.
from typing import Any  # WHY: the portal and the test client are loosely typed.

import pytest  # WHY: fixtures, markers, and the monkeypatch context.

pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")  # Skip without a browser.

from playwright.sync_api import Page, expect

from src.operations.exporting.juniper_rma.settings import JuniperServiceSession
from src.operations.exporting.juniper_rma.workflows.correlation import MistTicketReader
from tests.e2e.web_portal.juniper_browser_harness import (
    SCREENSHOT_DIR,
    JuniperWorld,
    juniper_menu_actions,
    sample_tickets,
)
from tests.unit.juniper_rma.fixtures import read_replies as replies
from web_portal.app import WebPortalApp

logger = logging.getLogger(__name__)  # The module logger records each browser step.

READY_TIMEOUT_MS = 15_000  # One page load or element wait must not block the suite.
RUN_TIMEOUT_MS = 60_000  # The double answers at once, so a run that takes longer has stalled.
SETTLE_MS = 500  # The accordion and the parameter fetch need a moment before a screenshot.
JUNIPER_MENUS = tuple(str(number) for number in range(294, 305))  # Menus 294 to 304 as text keys.
FINAL_STATUS_JS = (  # True when the status badge shows a final state, and false while the run still works.
    "() => /^(complete|error|failed)$/i.test((document.getElementById('statusBadge') || {}).textContent || '')"
)
PARAMETER_LOADING_HIDDEN_JS = (  # True when the parameter fetch has finished and its spinner is hidden.
    "() => { const el = document.getElementById('parameterLoading');"
    " return !el || getComputedStyle(el).display === 'none'; }"
)
LOG_WORD_BREAK_JS = (  # The word-break rule that the browser applies to the run log.
    "() => getComputedStyle(document.getElementById('logViewer')).wordBreak"
)
OPEN_MODALS_OPAQUE_JS = (  # True when no open modal is still fading, so each one paints at full opacity.
    "() => Array.from(document.querySelectorAll('.modal.show')).every(el => getComputedStyle(el).opacity === '1')"
)


def free_port() -> int:
    """Return a port that no other process holds right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:  # A probe socket that closes at once.
        probe.bind(("127.0.0.1", 0))  # Port zero asks the operating system for a free port.
        return int(probe.getsockname()[1])  # The port number that the system chose.


@pytest.fixture(scope="module")
def juniper_workspace(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Run the module in a new working folder, with the database mirror switched off.

    Why:
        DataExporter writes to a relative data folder, and the portal scans the folder that
        DATA_DIR names. Both point at this folder, so no run writes to the repository data folder.
        The standalone switch stops the mirror to ArangoDB and Redis, so no synthetic row reaches
        a live database.
    """
    workspace = tmp_path_factory.mktemp("juniper_portal")  # A new folder that no other test uses.
    (workspace / "data").mkdir()  # The output scan needs the folder before the first run, as the repository has it.
    with pytest.MonkeyPatch.context() as patch:  # Every change below reverts when the module finishes.
        patch.setenv("DATA_DIR", str(workspace / "data"))  # The portal scans and serves the same folder.
        patch.setenv("MISTHELPER_STANDALONE", "true")  # Skip the database mirror for every write.
        logger.info("Juniper browser workspace: %s", workspace)  # Record where this run writes its files.
        yield workspace  # Hand the folder to the tests.


@pytest.fixture(scope="module")
def juniper_world() -> Iterator[JuniperWorld]:
    """Return the synthetic Juniper and Mist state, and clear every override after the module."""
    world = JuniperWorld(sample_tickets(datetime.now(UTC)))  # Tickets are relative to the run time.
    yield world  # Hand the world to the tests.
    world.reset()  # Forget every override that the module set.


@pytest.fixture(autouse=True)
def _isolate_each_test(
    juniper_workspace: Path,
    juniper_world: JuniperWorld,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> Iterator[None]:
    """Work in the module workspace, run the root logger at INFO, and clear the status overrides.

    Why:
        The repository conftest moves each test into its own temporary folder. That move would send the
        exports of a run to a folder that the test never reads. This fixture runs after the move, so the
        workspace wins for the duration of the test. The monkeypatch restores the folder after the test.

        The portal reads its run log from the root logger, and pytest leaves that logger at WARNING. An
        INFO line therefore never reached the run log. The access-check PASS line, which names the reason
        for a file-less success, is one such line. The caplog fixture sets INFO for this test only.
    """
    monkeypatch.chdir(juniper_workspace)  # The relative data folder of the exporter resolves in the workspace.
    caplog.set_level(logging.INFO)  # The run log gets INFO lines, as in production, and the level reverts.
    yield  # The test runs with the workspace as its working folder and INFO logging on.
    juniper_world.reset()  # The next test starts from the clean world.


@pytest.fixture(scope="module")
def juniper_app(juniper_workspace: Path, juniper_world: JuniperWorld) -> Iterator[Any]:
    """Build the portal, with the Juniper rows bound to the real workflows and the double behind them.

    Why:
        The portal runs each menu through its real handler. Only the two places where a run
        reaches Juniper or Mist are replaced: the Juniper session and the Mist ticket source.
    """
    with pytest.MonkeyPatch.context() as patch:  # The patches revert when the module finishes.
        patch.setattr(  # Every menu that opens a Juniper session receives the double.
            JuniperServiceSession,
            "open_for_menu",
            classmethod(lambda _cls, needs_contact_email=True: juniper_world.session()),
        )
        patch.setattr(  # Menu 302 reads the Mist tickets from the world, not from the Mist API.
            MistTicketReader,
            "read",
            lambda _self: juniper_world.tickets(),
        )
        app = WebPortalApp.create_app(  # The same factory as the product, with the Juniper rows bound.
            apisession=None,
            menu_actions=juniper_menu_actions(),
            org_id="test-org-id",
        )
        app.config["TESTING"] = True  # Surface the errors of the test client.
        yield app  # Hand the application to the tests.
        WebPortalApp.shutdown_app(app)  # Stop the heartbeat and drain the pool before the patches revert.


@pytest.fixture(scope="module")
def portal_url(juniper_app: Any) -> Iterator[str]:
    """Serve the portal in this process and return its base address."""
    from werkzeug.serving import make_server  # WHY: a server that runs on Windows, unlike Gunicorn.

    port = free_port()  # A port that the developer's own services do not hold.
    server = make_server("127.0.0.1", port, juniper_app, threaded=True)  # Threaded, so a poll cannot block a run.
    thread = threading.Thread(target=server.serve_forever, daemon=True)  # The server runs beside the browser.
    thread.start()  # Begin serving requests.
    try:
        yield f"http://127.0.0.1:{port}"  # The base address for the browser.
    finally:
        server.shutdown()  # Release the port, so a later module can bind its own.
        thread.join(timeout=10)  # Wait for the server thread to finish.


def open_portal(page: Page, portal_url: str) -> None:
    """Load the operations page and wait until the menu list has loaded."""
    page.goto(f"{portal_url}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)  # Load the page.
    page.wait_for_selector(".op-item", state="attached", timeout=READY_TIMEOUT_MS)  # Wait for the menu rows.


def open_juniper_group(page: Page) -> None:
    """Expand the Juniper RMA group, the way an operator does before choosing a menu."""
    row = page.locator('.op-item[data-menu="294"]')  # One row of the group shows whether the group is open.
    if row.is_visible():  # An open group stays open, so a second click must not close it again.
        return  # Nothing to do.
    page.get_by_role("button", name=re.compile(r"^Juniper RMA")).click()  # The button text starts with the group name.
    expect(row).to_be_visible(timeout=READY_TIMEOUT_MS)  # Wait until the group shows its rows.


def select_menu(page: Page, menu: str) -> None:
    """Choose one Juniper menu, and wait until its controls have loaded."""
    open_juniper_group(page)  # The row sits in a collapsed group until the group opens.
    page.locator(f'.op-item[data-menu="{menu}"]').click()  # The row carries its menu number.
    page.wait_for_function(PARAMETER_LOADING_HIDDEN_JS, timeout=READY_TIMEOUT_MS)  # Wait for the controls.
    page.wait_for_timeout(SETTLE_MS)  # Let the form finish drawing before the test reads it.


def set_control(page: Page, name: str, value: str) -> None:
    """Type one answer into a text control, the way an operator does."""
    page.locator(f"#param-{name}").fill(value)  # Fill fires the input event that validates the form.


def choose_control(page: Page, name: str, value: str) -> None:
    """Pick one answer from a choice control, the way an operator does."""
    page.locator(f"#param-{name}").select_option(value)  # Selecting fires the change event that shows the next control.


def run_operation(page: Page) -> tuple[str, str]:
    """Start the selected menu, wait for a final status, and return the badge text and the status message."""
    run_button = page.locator('[data-testid="run-btn"]')  # The Run button of the operations page.
    expect(run_button).to_be_enabled(timeout=READY_TIMEOUT_MS)  # Run stays off until the required answers exist.
    run_button.click()  # Start the run in the portal.
    page.wait_for_function(FINAL_STATUS_JS, timeout=RUN_TIMEOUT_MS)  # Wait for Complete, Error, or Failed.
    badge = page.locator("#statusBadge").inner_text()  # The state that the operator reads first.
    message = page.locator("#statusMessage").inner_text()  # The reason, when the run did not finish cleanly.
    logger.info("Run finished with badge %s", badge)  # Record the outcome for the test log.
    return badge, message  # The caller checks both.


def output_files(page: Page) -> list[str]:
    """Return the names of the files that the finished run lists."""
    return page.locator("#outputFileList a").all_inner_texts()  # One link for each file that the run wrote.


def log_text(page: Page) -> str:
    """Return the text of the run log, the way the operator reads it."""
    return page.locator("#logViewer").inner_text()  # The visible log lines.


def capture(page: Page, name: str) -> Path:
    """Save a full-page screenshot for review, and return its path.

    Why:
        A screenshot taken during a fade shows a see-through modal, so the page behind it bleeds through
        the text. The capture therefore waits for each open modal to reach full opacity, and then waits
        for the accordion and the result panel to settle.
    """
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)  # The folder is git-ignored and created on demand.
    path = SCREENSHOT_DIR / f"{name}.png"  # One file for each step, named in run order.
    page.wait_for_function(OPEN_MODALS_OPAQUE_JS, timeout=READY_TIMEOUT_MS)  # Every open modal is fully opaque.
    page.wait_for_timeout(SETTLE_MS)  # The accordion and the result panel finish their transitions first.
    page.screenshot(path=str(path), full_page=True)  # The whole page, so a reader sees the result panel too.
    logger.info("Saved the screenshot %s", path.name)  # Record each screenshot for the test log.
    return path  # The caller may attach it to a report.


def export_rows(workspace: Path, filename: str) -> list[dict[str, str]]:
    """Read back one export of the run, so a test checks the saved values and not only the screen."""
    with (workspace / "data" / filename).open(newline="", encoding="utf-8") as handle:  # The saved CSV file.
        return list(csv.DictReader(handle))  # One dictionary for each saved row.


def open_preview(page: Page, filename: str) -> None:
    """Open the preview of one output file, the way an operator does from the result list."""
    row = page.locator("#outputFileList li", has_text=filename)  # The list item of this file.
    row.get_by_role("button", name="Preview").click()  # The Preview button sits beside the file link.
    expect(page.locator("#dataPreviewModal")).to_be_visible(timeout=READY_TIMEOUT_MS)  # The modal is open.
    expect(page.locator("#dataPreviewBody table").first).to_be_visible(timeout=READY_TIMEOUT_MS)  # The table drew.


class TestTheJuniperMenusAreReadableInTheBrowser:
    """Check each Juniper menu from the list to its result, in a real browser."""

    def test_the_juniper_group_lists_every_menu_with_its_title(self, page: Page, portal_url: str) -> None:
        """The operator finds the eleven menus under one group, each with its readable title."""
        open_portal(page, portal_url)  # Load the operations page.
        open_juniper_group(page)  # Expand the Juniper RMA group.
        group_button = page.get_by_role("button", name=re.compile(r"^Juniper RMA"))  # The group heading.
        expect(group_button).to_contain_text("(11)")  # The count of the group matches the eleven menus.
        for menu in JUNIPER_MENUS:  # Each menu must be visible in the open group.
            expect(page.locator(f'.op-item[data-menu="{menu}"]')).to_be_visible()  # A visible row can be chosen.
        expect(page.locator('.op-item[data-menu="294"]')).to_contain_text("List Juniper service requests")  # Title.
        selector = ", ".join(f'.op-item[data-menu="{menu}"]' for menu in JUNIPER_MENUS)  # One selector for the group.
        assert page.locator(selector).count() == len(JUNIPER_MENUS)  # The portal shows exactly eleven menus.
        capture(page, "01-juniper-group")  # The expanded group, for the screenshot review.

    def test_the_key_kind_shows_only_the_identifier_it_needs(self, page: Page, portal_url: str) -> None:
        """Choice 1 shows the request number, choice 2 shows the case number, and never both."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "295")  # The detail menu asks for a key kind first.
        expect(page.locator("#param-key_kind")).to_be_visible()  # The chooser is the first control.
        assert page.locator("#param-request_number").count() == 0  # No identifier before a choice is made.
        choose_control(page, "key_kind", "1")  # The operator picks a request number.
        expect(page.locator("#param-request_number")).to_be_visible()  # The request-number control appears.
        assert page.locator("#param-case_number").count() == 0  # The case-number control stays away.
        choose_control(page, "key_kind", "2")  # The operator changes the choice to a case number.
        expect(page.locator("#param-case_number")).to_be_visible()  # The case-number control appears.
        assert page.locator("#param-request_number").count() == 0  # The request-number control is removed.
        choose_control(page, "key_kind", "1")  # Return to the request number for the screenshot.
        capture(page, "02-menu-295-key-kind")  # The chooser and its revealed control.

    def test_menu_294_lists_requests_and_the_preview_shows_the_table(
        self,
        page: Page,
        portal_url: str,
        juniper_workspace: Path,
    ) -> None:
        """The request list runs with the default window, saves every column, and previews as a table."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "294")  # The list menu asks for two optional dates.
        badge, message = run_operation(page)  # Run with both dates blank, which keeps the defaults.
        assert badge == "Complete", message  # The run must finish cleanly.
        assert "JuniperRequestList.csv" in output_files(page)  # The file of this menu is listed.
        rows = export_rows(juniper_workspace, "JuniperRequestList.csv")  # The saved file, read back.
        assert len(rows) == 1  # The double holds one request.
        assert rows[0]["contactEmail"] == "pat.example@example.com"  # The export keeps the full address.
        capture(page, "03-menu-294-result")  # The log and the result list.
        open_preview(page, "JuniperRequestList.csv")  # Open the table preview from the result list.
        capture(page, "04-menu-294-preview")  # The preview table, for the readability review.

    def test_menu_298_needs_no_answer(self, page: Page, portal_url: str, juniper_workspace: Path) -> None:
        """The list of values has no question, so the form stays hidden and Run starts it at once."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "298")  # The menu asks no question.
        expect(page.locator("#parameterForm")).to_be_hidden()  # No form appears for a menu with no question.
        badge, message = run_operation(page)  # Run straight away.
        assert badge == "Complete", message  # The run must finish cleanly.
        assert "JuniperLovs.csv" in output_files(page)  # The list of values is saved.
        assert export_rows(juniper_workspace, "JuniperLovs.csv")  # The file holds rows.
        capture(page, "05-menu-298-no-controls")  # The panel with no form.

    def test_menu_304_waits_for_serial_numbers_then_saves_each_asset(
        self,
        page: Page,
        portal_url: str,
        juniper_workspace: Path,
    ) -> None:
        """Run waits for the serial numbers, and then the asset lookup saves each asset row."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "304")  # The asset lookup asks for one line of serial numbers.
        expect(page.locator("#param-serial_numbers")).to_be_visible()  # The required control is shown.
        expect(page.locator('[data-testid="run-btn"]')).to_be_disabled()  # Run waits for the required answer.
        set_control(page, "serial_numbers", "SN000000001, SN000000002")  # Two serial numbers, comma separated.
        badge, message = run_operation(page)  # Run the lookup.
        assert badge == "Complete", message  # The run must finish cleanly.
        assets = export_rows(juniper_workspace, "JuniperAssets.csv")  # The saved assets, read back.
        assert {row["serialNumber"] for row in assets} == {"SN000000001", "SN000000002"}  # Each serial, once.
        capture(page, "06-menu-304-result")  # The result of the lookup.

    def test_menu_300_refuses_a_window_outside_the_retention_rule(
        self,
        page: Page,
        portal_url: str,
    ) -> None:
        """A start date older than seven days is refused before any call, and the log says why."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "300")  # The bulk read asks for a snapshot window.
        too_old = (datetime.now(UTC).date() - timedelta(days=10)).isoformat()  # Ten days back breaks the rule.
        set_control(page, "start_date", too_old)  # The operator types the old date.
        badge, message = run_operation(page)  # The run ends, and it writes nothing.
        assert badge == "Error", message  # A rejected input is an error, not a success.
        assert "could not be read" in message  # The status names the rejection, not a generic failure.
        assert output_files(page) == []  # No file is listed, because no call was made.
        capture(page, "07-menu-300-refused")  # The rejection as the operator sees it.

    def test_menu_300_names_the_entitlement_rejection(
        self,
        page: Page,
        portal_url: str,
        juniper_world: JuniperWorld,
    ) -> None:
        """An HTTP 401 from the asset gateway is named in the status, so the operator knows the next step."""
        http_status = 401  # Juniper refuses the asset API for this app with this HTTP status.
        juniper_world.statuses["queryAssetsBulkData"] = http_status  # The double answers with that status.
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "300")  # The default window is valid, so the call is made.
        badge, message = run_operation(page)  # The call fails with 401.
        assert badge == "Error", message  # A refused read is an error.
        assert "HTTP 401" in message  # The status names the refusal, not a generic failure.
        assert output_files(page) == []  # No export is written for a refused read.
        word_break = page.evaluate(LOG_WORD_BREAK_JS)  # The wrapping rule that the browser applies to the log.
        assert word_break != "break-all"  # Regression guard: the log must wrap at word edges.
        capture(page, "08-menu-300-entitlement")  # The refusal as the operator sees it.

    def test_menu_300_names_a_gateway_failure_after_its_retries(
        self,
        page: Page,
        portal_url: str,
        juniper_world: JuniperWorld,
    ) -> None:
        """A server error that survives the gateway retries is named with its status, and no file is written."""
        http_status = 503  # Juniper is unavailable, so every retry of the call fails with this status.
        failure_text = f"Juniper gateway replied with HTTP {http_status} after 3 attempts"  # The text of the failure.
        juniper_world.failures["queryAssetsBulkData"] = failure_text  # Every retry of the call fails this way.
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "300")  # The default window is valid, so the call is made.
        badge, message = run_operation(page)  # The call fails after the retries.
        assert badge == "Error", message  # A failed read is an error.
        assert f"HTTP {http_status}" in message  # The status names the failure, not a generic one.
        assert output_files(page) == []  # No export is written for a failed read.
        capture(page, "14-menu-300-gateway-503")  # The failure as the operator sees it.

    def test_menu_300_reports_a_dropped_connection(
        self,
        page: Page,
        portal_url: str,
        juniper_world: JuniperWorld,
    ) -> None:
        """A connection that Juniper drops is named as a connection error, and no file is written."""
        juniper_world.failures["queryAssetsBulkData"] = "ConnectionError: connection dropped"  # Transport failure.
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "300")  # The default window is valid, so the call is made.
        badge, message = run_operation(page)  # The call fails before any reply arrives.
        assert badge == "Error", message  # A dropped connection is an error.
        assert "ConnectionError" in message  # The status names the connection failure.
        assert output_files(page) == []  # No export is written for a failed read.
        capture(page, "15-menu-300-connection-error")  # The failure as the operator sees it.

    def test_menu_300_reports_a_read_timeout(
        self,
        page: Page,
        portal_url: str,
        juniper_world: JuniperWorld,
    ) -> None:
        """A reply that never arrives in time is named as a read timeout, and no file is written."""
        juniper_world.failures["queryAssetsBulkData"] = "ReadTimeout: the gateway did not answer in time"  # Timed out.
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "300")  # The default window is valid, so the call is made.
        badge, message = run_operation(page)  # The call times out.
        assert badge == "Error", message  # A timeout is an error.
        assert "ReadTimeout" in message  # The status names the timeout.
        assert output_files(page) == []  # No export is written for a timed-out read.
        capture(page, "16-menu-300-read-timeout")  # The failure as the operator sees it.

    def test_menu_296_writes_the_rma_header_and_every_item(
        self,
        page: Page,
        portal_url: str,
        juniper_workspace: Path,
    ) -> None:
        """The RMA read needs the RMA and its request, and it saves one header row and one row per item."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "296")  # The RMA read asks three identifiers in order.
        set_control(page, "rma_number", replies.RMA_NUMBER)  # The RMA number of the synthetic reply.
        set_control(page, "request_number", replies.SR_NUMBER)  # The request that owns the RMA.
        badge, message = run_operation(page)  # The optional case number stays blank.
        assert badge == "Complete", message  # The run must finish cleanly.
        assert len(export_rows(juniper_workspace, "JuniperRmaDetailItems.csv")) == 2  # Two items in the reply.
        capture(page, "09-menu-296-result")  # The result of the RMA read.

    def test_menu_297_reads_every_note_of_the_request(
        self,
        page: Page,
        portal_url: str,
        juniper_workspace: Path,
    ) -> None:
        """Choosing a request number and leaving the note blank reads each distinct note once."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "297")  # The notes read asks the key, then an optional note identifier.
        choose_control(page, "key_kind", "1")  # Key the read by request number.
        set_control(page, "request_number", replies.SR_NUMBER)  # The request of the synthetic detail.
        badge, message = run_operation(page)  # The note identifier stays blank, so every note is read.
        assert badge == "Complete", message  # The run must finish cleanly.
        assert len(export_rows(juniper_workspace, "JuniperRequestNotes.csv")) == 3  # Three distinct notes.
        capture(page, "10-menu-297-result")  # The result of the notes read.

    def test_menu_303_looks_up_a_request_and_its_rma(
        self,
        page: Page,
        portal_url: str,
        juniper_workspace: Path,
    ) -> None:
        """The lookup saves the request row, and it saves each RMA item when an RMA number is given."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "303")  # The lookup asks the key, then an optional RMA number.
        choose_control(page, "key_kind", "1")  # Key the lookup by request number.
        set_control(page, "request_number", replies.SR_NUMBER)  # The request to look up.
        set_control(page, "rma_number", replies.RMA_NUMBER)  # The RMA to show with the request.
        badge, message = run_operation(page)  # Run the lookup.
        assert badge == "Complete", message  # The run must finish cleanly.
        assert export_rows(juniper_workspace, "JuniperLookupRmaItems.csv")  # The RMA items are saved.
        capture(page, "11-menu-303-result")  # The result of the lookup.

    def test_menu_302_correlates_tickets_with_requests(
        self,
        page: Page,
        portal_url: str,
        juniper_workspace: Path,
    ) -> None:
        """The correlation saves one row per ticket outcome, with a match status for each row."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "302")  # The correlation asks no question.
        badge, message = run_operation(page)  # Run the correlation over the synthetic tickets.
        assert badge == "Complete", message  # The run must finish cleanly.
        statuses = {row["matchStatus"] for row in export_rows(juniper_workspace, "JuniperCorrelation.csv")}
        assert {"matched", "unmatched"} <= statuses  # The double holds a match and a ticket with no match.
        capture(page, "12-menu-302-result")  # The result of the correlation.

    def test_menu_301_reports_that_the_access_check_passed(self, page: Page, portal_url: str) -> None:
        """The access check reads one day of requests and reports the pass with the reason it wrote no file."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "301")  # The access check asks no question.
        badge, message = run_operation(page)  # Run the one-day request.
        assert badge == "Complete", message  # A passed check is a completed run.
        assert "No file is written by this check" in message  # The completed run states why it wrote no file.
        capture(page, "13-menu-301-result")  # The result of the access check.

    @pytest.mark.xfail(
        strict=False,  # The race depends on timing, so a run may pass this check or miss it.
        reason="Known defect: a run that ends before its SSE stream opens leaves the Execution Log empty.",
    )
    def test_a_fast_run_keeps_its_log_lines_in_the_execution_log(self, page: Page, portal_url: str) -> None:
        """The Execution Log shows the PASS line of a check that ends almost at once."""
        open_portal(page, portal_url)  # Load the operations page.
        select_menu(page, "301")  # The check ends in milliseconds, which is the fast case.
        badge, message = run_operation(page)  # Run the check and wait for its final state.
        assert badge == "Complete", message  # The run itself must still complete.
        assert "PASS" in log_text(page), "The Execution Log shows no line of the fast run."  # Operator view.


class TestTheJuniperMenusInTheListingApi:
    """Check the listing and the parameter endpoints that the browser depends on, without a browser."""

    def test_the_list_api_groups_the_eleven_menus_under_juniper_rma(self, juniper_app: Any) -> None:
        """The API that feeds the menu list returns the eleven menus in one group."""
        data = juniper_app.test_client().get("/api/operations/list").get_json()  # The categorized list.
        groups = {category["name"]: category["operations"] for category in data["categories"]}  # One entry per group.
        numbers = sorted(int(operation["menu_number"]) for operation in groups["Juniper RMA"])  # The group members.
        assert numbers == list(range(294, 305))  # Exactly the eleven menus, in order.

    def test_the_parameter_api_returns_the_key_kind_with_its_identifier_controls(self, juniper_app: Any) -> None:
        """The parameter endpoint returns the chooser and the identifier control that each choice reveals."""
        data = juniper_app.test_client().get("/api/operations/parameters/295").get_json()  # The controls of 295.
        chooser = data["parameters"][0]  # The first control is the key-kind chooser.
        assert chooser["name"] == "key_kind"  # The chooser comes first, as the workflow asks it first.
        assert set(chooser["dynamic_parameters"]) == {"1", "2"}  # Both choices reveal an identifier.
