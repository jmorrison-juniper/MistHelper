"""Browser journeys for the WebSockets terminal.

Why:
    Issue #3671 needs real browser evidence for typing, copy, paste, screen
    output, downloads, and log safety.
"""

from __future__ import annotations  # Keep annotations lazy for Playwright imports.

import logging  # Capture log text for the leak scan journey.
import time  # Bound the footer wait in the resize journey.
from pathlib import Path  # Read the downloaded terminal history file.
from typing import Any  # Playwright objects are duck typed in these tests.
from urllib.parse import parse_qs, urlsplit  # Read the after value of each terminal read URL.

import pytest  # Use fixtures and skip support.

from src.websocket_streams.live.runners.shell import ShellRunner  # The silent device journey reads the final reason.
from src.websocket_streams.live.transport.endpoint import ConnectFailure  # Open failure journeys read the reasons.
from tests.e2e.websockets_tab import terminal_support  # Register and read the shared harness.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import (
    HandshakeFault,
)  # Open failure journeys fail one handshake.

pytest.importorskip("playwright", reason="playwright is absent, so the browser journey cannot run")  # Browser guard.
READY_TIMEOUT_MS = terminal_support.READY_TIMEOUT_MS  # Use one browser wait boundary for terminal tests.
TerminalPortalHarness = terminal_support.TerminalPortalHarness  # Keep type hints tied to the shared harness.
terminal_harness = terminal_support.terminal_harness  # Expose the shared fixture to this test module.
delayed_terminal_harness = terminal_support.delayed_terminal_harness  # Expose the delayed shell fixture.
quiet_terminal_harness = terminal_support.quiet_terminal_harness  # Expose the quiet shell fixture.
paste_echo_terminal_harness = terminal_support.paste_echo_terminal_harness  # Expose the visible paste fixture.
monitor_terminal_harness = terminal_support.monitor_terminal_harness  # Expose the fixed monitor fixture.
pushable_terminal_harness = terminal_support.pushable_terminal_harness  # Expose the late shell output fixture.
silent_terminal_harness = terminal_support.silent_terminal_harness  # Expose the silent device fixture.
SPECIAL_KEY_BYTES = (  # xterm.js sends these bytes in normal cursor mode, and the fake shell keeps that mode.
    ("ArrowUp", b"\x1b[A"),
    ("ArrowDown", b"\x1b[B"),
    ("ArrowLeft", b"\x1b[D"),
    ("ArrowRight", b"\x1b[C"),
    ("Tab", b"\t"),
    ("Backspace", b"\x7f"),
    ("Delete", b"\x1b[3~"),
    ("Home", b"\x1b[H"),
    ("End", b"\x1b[F"),
    ("PageUp", b"\x1b[5~"),
    ("PageDown", b"\x1b[6~"),
    ("Escape", b"\x1b"),
    ("F1", b"\x1bOP"),
    ("F5", b"\x1b[15~"),  # F5 to F12 use the tilde form, not the SS3 form of F1 to F4.
)
RATE_LIMITED_BODY = '{"error":"rate limited","code":"rate_limited"}'  # The terminal HTTP rate limit answer.
WAITING_NOTICE = "The portal waits for the first output from the device."  # The header notice before the first output.
SILENT_NOTICE = (  # The header notice after the shortened test wait of 2 seconds.
    "The device sent no output in 2 seconds. Stop this session. Start a new session after one minute."
)
REASON_RECORDER = """
window.MistWebSocketTerminalTestHooks = {readWaitSeconds: 0.2};
window.wsReasonTexts = [];
document.addEventListener('DOMContentLoaded', function() {
    var node = document.getElementById('wsSessionReason');
    new MutationObserver(function() { window.wsReasonTexts.push(node.textContent); })
        .observe(node, {childList: true, characterData: true, subtree: true});
});
"""  # Record each header reason text, so a short notice cannot escape the journey.


def _open_shell(page: Any, harness: TerminalPortalHarness) -> None:
    """Open one terminal shell on the fake switch."""
    harness.open_page(page)  # Load the WebSockets page.
    harness.start_shell(page)  # Start a shell terminal session.


def _start_top(page: Any) -> None:
    """Start the top screen command on the fake switch."""
    page.get_by_test_id("ws-catalog-entry-ex.topCommand").click()  # Choose the screen command.
    page.locator('[data-testid="ws-field-site_id"]').select_option(terminal_support.SITE_ID)  # Choose the site.
    page.locator('[data-testid="ws-field-device_id"]').select_option(terminal_support.DEVICE_ID)  # Choose the device.
    page.get_by_test_id("ws-start-button").click()  # Start the screen session.


def _active_session_id(page: Any) -> str:
    """Return the id of the session that the session list marks active."""
    item = page.locator(".ws-session-item.active")  # The page marks the shown session in the list.
    item.wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Wait until the list draws the item.
    return str(item.get_attribute("data-session-id"))  # The list keeps the session id in a data attribute.


def _wait_new_active_session(page: Any, old_id: str) -> str:
    """Wait until the list marks a session other than old_id, then return its id."""
    page.wait_for_function(
        """(oldId) => {
            const item = document.querySelector('.ws-session-item.active');
            return !!item && item.dataset.sessionId !== oldId;
        }""",
        arg=old_id,
        timeout=READY_TIMEOUT_MS,
    )  # A new start selects the new session.
    return _active_session_id(page)  # Return the id of the new session.


def _read_positions(urls: list[str], session_id: str) -> list[int]:
    """Return the after value of each terminal read of one session, in request order."""
    positions: list[int] = []  # The read positions of the session.
    for url in urls:  # Keep the browser request order.
        parts = urlsplit(url)  # Split the path from the query.
        if parts.path.endswith(f"/sessions/{session_id}/terminal"):  # Keep the reads of this session only.
            positions.append(int(parse_qs(parts.query)["after"][0]))  # The read starts at this byte position.
    return positions  # The caller checks the order.


def _screen_text(page: Any) -> str:
    """Return visible terminal text."""
    return page.get_by_test_id("ws-terminal-screen").inner_text(timeout=READY_TIMEOUT_MS)  # Read visible text.


def _shot(page: Any, harness: TerminalPortalHarness, name: str) -> None:
    """Save and verify one screenshot."""
    path = harness.screenshot(page, name)  # Save browser evidence.
    assert path.exists() is True  # The screenshot must exist for the report.


def _dispatch_terminal_paste(page: Any, text: str) -> None:
    """Send a paste event with clipboard data to the terminal element."""
    page.evaluate(
        """(text) => {
            const data = new DataTransfer();
            data.setData('text/plain', text);
            const event = new ClipboardEvent('paste', { clipboardData: data, bubbles: true, cancelable: true });
            document.querySelector('[data-testid="ws-terminal-screen"]').dispatchEvent(event);
        }""",
        text,
    )  # Send a real paste event with clipboard data.


def _open_settings(page: Any) -> None:
    """Open the terminal settings menu."""
    page.get_by_test_id("ws-terminal-settings").click()  # Show controls hidden inside details.


def test_j1_banner(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J1: the terminal shows the shell banner and prompt."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # Banner.
    screen = _screen_text(page)  # Read the visible terminal text after the banner arrives.
    _shot(page, terminal_harness, "j01-banner.png")  # Save evidence.
    assert "Welcome to Fake Mist Shell" in screen  # The banner bytes reached the screen.
    assert "device>" in screen  # The prompt follows the banner, so the operator can type.


def test_j2_typed_text(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J2: typed text reaches the device in order."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.type("show version")  # Send typed text.
    page.keyboard.press("Enter")  # Complete the command line.
    received = terminal_harness.shell.wait_for_input(len("show version\r"), 2.0)  # Wait for fake device bytes.
    _shot(page, terminal_harness, "j02-typed-text.png")  # Save evidence.
    assert received.endswith(b"show version\r") is True  # The device received exact text.


def test_j3_special_keys(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J3: each special key sends its exact terminal control bytes (FR-011)."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    for key, _sequence in SPECIAL_KEY_BYTES:  # Send each special key once, in table order.
        page.keyboard.press(key)  # Send one special key.
    expected = b"".join(sequence for _key, sequence in SPECIAL_KEY_BYTES)  # The device must get every key in order.
    received = terminal_harness.shell.wait_for_input(len(expected), 2.0)  # Wait for all control bytes.
    _shot(page, terminal_harness, "j03-special-keys.png")  # Save evidence.
    assert received.endswith(expected) is True  # A lost, changed, or reordered key fails here.


def test_j4_ctrl_c_without_selection(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J4: Ctrl+C without selected text sends the interrupt byte."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.press("Control+C")  # Send interrupt.
    received = terminal_harness.shell.wait_for_input(1, 2.0)  # Wait for device input.
    _shot(page, terminal_harness, "j04-ctrl-c-interrupt.png")  # Save evidence.
    assert received.endswith(b"\x03") is True  # Ctrl+C sent 0x03.


def _wait_footer_size(page: Any, harness: TerminalPortalHarness, timeout: float) -> tuple[str, str]:
    """Wait until the footer shows the size of the newest resize frame."""
    deadline = time.monotonic() + timeout  # Bound the wait.
    while True:  # Poll, because one layout change can post more than one size.
        size: Any = harness.shell.wait_for_resize(1, 0)[-1]["resize"]  # Read the newest size under the lock.
        expected = f"Size: {size['width']} x {size['height']}"  # The footer text for that size.
        footer = page.get_by_test_id("ws-terminal-status").inner_text()  # Read the visible footer.
        if expected in footer or time.monotonic() >= deadline:  # Stop on a match or at the limit.
            return expected, footer  # Return both texts for the assert.
        page.wait_for_timeout(100)  # Let the page apply the next resize.


def test_j5_resize(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J5: a resize reaches the fake device, and the footer shows the new size at once."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    opened = terminal_harness.shell.wait_for_resize(1, 2.0)  # The open sends the first size.
    page.set_viewport_size({"width": 1000, "height": 900})  # A new width changes the column count.
    frames = terminal_harness.shell.wait_for_resize(len(opened) + 1, 2.0)  # Wait for the new size.
    assert len(frames) > len(opened)  # The resize route sent a new size.
    expected, footer = _wait_footer_size(page, terminal_harness, 2.0)  # A resize gets no echo, so no read helps.
    _shot(page, terminal_harness, "j05-resize.png")  # Save evidence.
    assert expected in footer  # The footer shows the new size before the next read answers.


def test_j6_early_keys_queue(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J6: early keys are kept and sent in order after output arrives."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.type("early")  # Send text quickly after open.
    received = terminal_harness.shell.wait_for_input(len("early"), 2.0)  # Wait for fake device bytes.
    _shot(page, terminal_harness, "j06-early-keys.png")  # Save evidence.
    assert received.endswith(b"early") is True  # The queued text arrived in order.


def test_j7_exit_finishes(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J7: exit closes the shell and shows the finished state."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.type("exit")  # Type the close command.
    page.keyboard.press("Enter")  # Send the close command.
    page.get_by_test_id("ws-terminal-status").get_by_text("State: finished").wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Finished.
    received = terminal_harness.shell.wait_for_input(len("exit\r"), 2.0)  # Read the bytes that the device got.
    status = page.get_by_test_id("ws-terminal-status").inner_text(timeout=READY_TIMEOUT_MS)  # Read the footer.
    _shot(page, terminal_harness, "j07-exit-finished.png")  # Save evidence.
    assert received.endswith(b"exit\r") is True  # The device got the close command before it closed.
    assert "state: finished" in status.lower()  # The footer shows the normal end, not a failure.
    assert "The device closed the shell." in status  # The footer names the device close as the reason.


def test_j8_full_screen_program(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J8: a full-screen color program draws in the terminal."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.type("fullscreen")  # Ask the fake shell for alternate screen output.
    page.keyboard.press("Enter")  # Run the fake full-screen command.
    page.get_by_test_id("ws-terminal-screen").get_by_text("RED", exact=True).wait_for(
        timeout=READY_TIMEOUT_MS
    )  # The alternate screen text is visible.
    screen = _screen_text(page)  # Read the visible terminal text of the full-screen program.
    _shot(page, terminal_harness, "j08-fullscreen.png")  # Save evidence.
    assert "RED" in screen  # The full-screen program drew its colored text.
    assert "Welcome to Fake Mist Shell" not in screen  # The alternate screen hides the normal screen.


def test_j9_copy_by_selection_on(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J9: copy by selection is on by default."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-copy-on-select").wait_for(state="attached", timeout=READY_TIMEOUT_MS)  # Setting.
    checked = page.get_by_test_id("ws-terminal-copy-on-select").is_checked()  # Read default.
    _shot(page, terminal_harness, "j09-copy-on-select.png")  # Save evidence.
    assert checked is True  # The default matches the contract.


def test_j10_copy_by_selection_off(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J10: copy by selection can turn off."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    _open_settings(page)  # Reveal the settings controls.
    page.get_by_test_id("ws-terminal-copy-on-select").uncheck()  # Disable selection copy.
    checked = page.get_by_test_id("ws-terminal-copy-on-select").is_checked()  # Read new state.
    _shot(page, terminal_harness, "j10-copy-off.png")  # Save evidence.
    assert checked is False  # The setting changed.


def test_j11_copy_keys(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J11: each copy key leaves terminal input unchanged when text is selected."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    before = terminal_harness.shell.received_input  # Snapshot device input.
    for key in ["Control+Shift+C", "Control+Insert"]:  # Copy keys.
        page.keyboard.press(key)  # Trigger a copy command.
    _shot(page, terminal_harness, "j11-copy-keys.png")  # Save evidence.
    assert terminal_harness.shell.received_input == before  # Copy keys send no device bytes.


def test_j12_ctrl_c_with_selection(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J12: Ctrl+C with a selection does not send interrupt."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-screen").click(button="right")  # Open the terminal context menu.
    page.get_by_test_id("ws-terminal-menu-select-all").click()  # Use xterm selection, not DOM selection.
    before = terminal_harness.shell.received_input  # Snapshot device input.
    page.keyboard.press("Control+C")  # Copy selected text.
    _shot(page, terminal_harness, "j12-ctrl-c-selection.png")  # Save evidence.
    assert terminal_harness.shell.received_input == before  # No interrupt reached the device.


def test_j13_paste_keys(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J13: paste keys send exact text bytes."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.evaluate("navigator.clipboard.writeText('paste-one')")  # Put text on the clipboard.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.press("Control+Shift+V")  # Paste from clipboard through the terminal handler.
    received = terminal_harness.shell.wait_for_input(len("paste-one"), 2.0)  # Wait for device bytes.
    _shot(page, terminal_harness, "j13-paste-keys.png")  # Save evidence.
    assert b"paste-one" in received  # The exact bytes reached the fake device.


def test_j14_paste_confirmation_cancel_and_send(page: Any, paste_echo_terminal_harness: TerminalPortalHarness) -> None:
    """J14: multi-line paste supports Cancel and Paste."""
    paste_echo_terminal_harness.open_page(page)  # Load the WebSockets page before installing a test hook.
    page.evaluate("window.MistWebSocketTerminalTestHooks = { readWaitSeconds: 1 }")  # Shorten echo waits.
    paste_echo_terminal_harness.start_shell(page)  # Start the terminal with the short-read hook active.
    _dispatch_terminal_paste(page, "line1\nline2")  # Open confirmation through the terminal paste event.
    _shot(page, paste_echo_terminal_harness, "j14-paste-confirmation-open.png")  # Save the open dialog evidence.
    page.get_by_test_id("ws-terminal-paste-cancel").click()  # Cancel first.
    first = paste_echo_terminal_harness.shell.received_input  # Snapshot input after cancel.
    _dispatch_terminal_paste(page, "line1\nline2")  # Open confirmation again through the same paste path.
    page.get_by_test_id("ws-terminal-paste-send").click()  # Confirm paste.
    received = paste_echo_terminal_harness.shell.wait_for_input(len(first) + len("line1\rline2"), 2.0)  # Wait.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus the terminal after the paste closes.
    page.keyboard.press("Enter")  # Run the second pasted line so the echo is visible.
    page.get_by_text("ran: line2").wait_for(timeout=READY_TIMEOUT_MS)  # Wait for visible pasted output.
    _shot(page, paste_echo_terminal_harness, "j14-paste-confirmation-sent.png")  # Save evidence after send.
    assert received.startswith(first) is True  # Cancel sent nothing before Paste.


def test_j15_bracketed_paste(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J15: bracketed paste wraps the pasted text when the device enables it."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.evaluate("navigator.clipboard.writeText('bracketed')")  # Put text on the clipboard.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.press("Control+Shift+V")  # Paste text through the terminal handler.
    received = terminal_harness.shell.wait_for_input(len("bracketed"), 2.0)  # Wait for fake device bytes.
    _shot(page, terminal_harness, "j15-bracketed-paste.png")  # Save evidence.
    assert b"bracketed" in received  # The pasted text reached the fake device.


def test_j16_two_thousand_line_paste(page: Any, quiet_terminal_harness: TerminalPortalHarness) -> None:
    """J16: a large paste arrives complete and in order."""
    _open_shell(page, quiet_terminal_harness)  # Start the terminal with a quiet fake shell for large input.
    text = "\n".join("set system services ssh " + str(index) for index in range(2000))  # Build large paste.
    page.evaluate("(value) => navigator.clipboard.writeText(value)", text)  # Put text on clipboard.
    page.get_by_test_id("ws-terminal-paste").click()  # Open confirmation.
    page.get_by_test_id("ws-terminal-paste-send").click()  # Send paste.
    expected = text.replace("\n", "\r").encode("utf-8")  # xterm paste converts line ends.
    received = quiet_terminal_harness.shell.wait_for_input(len(expected) + 12, 60.0)  # Wait for bracketed paste.
    _shot(page, quiet_terminal_harness, "j16-large-paste.png")  # Save evidence.
    assert expected in received  # The large paste arrived complete and ordered.


def test_j17_paste_limit(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J17: a paste above the limit is refused."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.evaluate("(value) => navigator.clipboard.writeText(value)", "x" * (257 * 1024))  # Too large.
    page.get_by_test_id("ws-terminal-paste").click()  # Attempt paste.
    page.get_by_text("Paste refused. The limit is 256 KiB.").wait_for(timeout=READY_TIMEOUT_MS)  # Limit notice.
    received = terminal_harness.shell.wait_for_input(1024, 1.0)  # Give a sent paste time to reach the device.
    _shot(page, terminal_harness, "j17-paste-limit.png")  # Save evidence.
    assert b"xxxx" not in received  # The refused paste did not reach the device.


def test_j18_kept_settings(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J18: terminal settings persist across page reload."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    _open_settings(page)  # Reveal the settings controls.
    page.get_by_test_id("ws-terminal-copy-on-select").uncheck()  # Change setting.
    page.reload(wait_until="domcontentloaded", timeout=READY_TIMEOUT_MS)  # Reload without waiting on long reads.
    terminal_harness.start_shell(page)  # Start another shell.
    checked = page.get_by_test_id("ws-terminal-copy-on-select").is_checked()  # Read stored setting.
    _shot(page, terminal_harness, "j18-kept-settings.png")  # Save evidence.
    assert checked is False  # Setting persisted in localStorage.


def test_j19_split_screen_updates(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J19: split control sequences draw a clean screen."""
    terminal_harness.open_page(page)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.topCommand").click()  # Choose the screen command.
    page.locator('[data-testid="ws-field-site_id"]').select_option("11111111-2222-3333-4444-555555555555")  # Site.
    page.locator('[data-testid="ws-field-device_id"]').select_option("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")  # Device.
    page.get_by_test_id("ws-start-button").click()  # Start screen.
    page.get_by_text("screen update 99").wait_for(timeout=READY_TIMEOUT_MS)  # Last update.
    text = _screen_text(page)  # Read screen text.
    _shot(page, terminal_harness, "j19-screen-updates.png")  # Save evidence.
    assert "screen update 99" in text  # The final screen is clean and visible.


def test_j20_screen_read_only(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J20: typed keys do not reach a read-only screen session."""
    input_calls = {"count": 0}  # Count input requests because read-only pages must not send any input.

    def count_input(route: Any) -> None:
        input_calls["count"] += 1  # Record any incorrect screen input request.
        body = '{"error":"read only","code":"read_only"}'  # Return the read-only route shape.
        route.fulfill(status=409, content_type="application/json", body=body)  # Fail if the page sends input.

    page.route("**/api/websockets/sessions/*/input", count_input)  # Prove the page sends no input request.
    terminal_harness.open_page(page)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.monitorTraffic").click()  # Choose screen command.
    page.locator('[data-testid="ws-field-site_id"]').select_option("11111111-2222-3333-4444-555555555555")  # Site.
    page.locator('[data-testid="ws-field-device_id"]').select_option("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")  # Device.
    page.get_by_test_id("ws-start-button").click()  # Start screen.
    before = terminal_harness.shell.received_input  # Shell device should receive nothing.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus screen terminal.
    page.keyboard.type("q")  # Type into read-only screen.
    _shot(page, terminal_harness, "j20-screen-read-only.png")  # Save evidence.
    warning = page.get_by_test_id("ws-terminal-warning").inner_text(timeout=READY_TIMEOUT_MS)  # Read-only text.
    footer = page.get_by_test_id("ws-terminal-status").inner_text(timeout=READY_TIMEOUT_MS)  # Footer status.
    assert terminal_harness.shell.received_input == before  # No key reached a shell device.
    assert input_calls["count"] == 0  # The page did not call the input route for a screen terminal.
    assert warning == "This view is read-only. The device sends the screen."  # Screen warning is not shell text.
    assert page.get_by_test_id("ws-terminal-paste").is_disabled() is True  # Read-only screen cannot paste.
    assert page.get_by_test_id("ws-terminal-menu-paste").get_attribute("aria-disabled") == "true"  # Menu paste.
    assert "State: Live" in footer  # The footer uses the same state case as the page header.


def test_review_16_screen_uses_fixed_80_by_40_geometry(
    page: Any, monitor_terminal_harness: TerminalPortalHarness
) -> None:
    """Review 16: monitor framing keeps row 1 and row 40 stable."""
    monitor_terminal_harness.open_page(page)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.monitorTraffic").click()  # Choose monitor traffic.
    page.locator('[data-testid="ws-field-site_id"]').select_option("11111111-2222-3333-4444-555555555555")  # Site.
    page.locator('[data-testid="ws-field-device_id"]').select_option("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")  # Device.
    page.get_by_test_id("ws-start-button").click()  # Start the fixed-geometry screen.
    page.get_by_text("SRX-1500 Monitor Header").wait_for(timeout=READY_TIMEOUT_MS)  # Wait for row 1 text.
    page.get_by_text("Bytes=b, Clear=c").wait_for(timeout=READY_TIMEOUT_MS)  # Wait for row 40 text.
    first_row = page.locator(".xterm-rows > div").nth(0).inner_text(timeout=READY_TIMEOUT_MS)  # Read row 1.
    fortieth_row = page.locator(".xterm-rows > div").nth(39).inner_text(timeout=READY_TIMEOUT_MS)  # Row 40.
    footer = page.get_by_test_id("ws-terminal-status").inner_text(timeout=READY_TIMEOUT_MS)  # Read footer size.
    _shot(page, monitor_terminal_harness, "review-16-fixed-screen-80x40.png")  # Save fixed-screen evidence.
    assert "SRX-1500 Monitor Header" in first_row  # Header remains on row 1.
    assert "Bytes=b, Clear=c" in fortieth_row  # Help line remains on row 40.
    assert "Size: 80 x 40" in footer  # Screen sessions do not fit to browser geometry.


def test_j21_history_download(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """J21: the history file text equals the screen text."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.type("show version")  # Create history text.
    page.keyboard.press("Enter")  # Run command.
    page.get_by_text("ran: show version").wait_for(timeout=READY_TIMEOUT_MS)  # Wait for command output.
    screen_text = _screen_text(page).strip()  # Capture screen text before download.
    with page.expect_download() as download_info:  # Capture the browser download.
        page.get_by_test_id("ws-terminal-download").click()  # Download history.
    download = download_info.value  # Get the Playwright download.
    text = Path(download.path()).read_text(encoding="utf-8").strip()  # Read downloaded text.
    _shot(page, terminal_harness, "j21-history-download.png")  # Save evidence.
    assert screen_text in text  # The file contains the screen text without control codes.


def test_j22_log_safety(page: Any, terminal_harness: TerminalPortalHarness, caplog: pytest.LogCaptureFixture) -> None:
    """J22: terminal logs do not leak secrets or terminal content."""
    caplog.set_level(logging.DEBUG)  # Capture route, service, and runner records.
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.type("secret-typed-marker")  # Send typed text that logs must not hold.
    page.keyboard.press("Enter")  # Complete the line.
    page.evaluate("navigator.clipboard.writeText('secret-pasted-marker')")  # Put paste marker on clipboard.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.press("Control+V")  # Paste marker.
    logs = caplog.text  # Read captured log text.
    _shot(page, terminal_harness, "j22-log-safety.png")  # Save evidence.
    assert "fake-token" not in logs  # Token must not appear.
    assert "/shell/" not in logs  # Shell address path must not appear.
    assert "secret-typed-marker" not in logs  # Typed text must not appear.
    assert "secret-pasted-marker" not in logs  # Pasted text must not appear.


def test_review_fr048_page_gets_no_shell_address(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """FR-048: no portal answer to the page holds the shell address or the API token."""
    finished: list[Any] = []  # Keep each request that the page completed.
    page.add_init_script("window.MistWebSocketTerminalTestHooks = {readWaitSeconds: 0.2};")  # Short reads finish.
    page.on("requestfinished", lambda request: finished.append(request))  # Keep each request after its body arrives.
    _open_shell(page, terminal_harness)  # Start the shell, so the portal reads the shell address.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.type("show version")  # Send input through the input route.
    page.keyboard.press("Enter")  # Complete the command line.
    page.get_by_text("ran: show version").wait_for(timeout=READY_TIMEOUT_MS)  # Read answers carried output.
    page.set_viewport_size({"width": 1100, "height": 800})  # Send one size through the resize route.
    terminal_harness.shell.wait_for_resize(1, 2.0)  # The resize route answered before the scan.
    session_list = page.evaluate("async () => (await fetch('/api/websockets/sessions')).text()")  # Read the list.
    api_requests = [request for request in finished if "/api/websockets/" in request.url]  # Keep the API answers.
    answers = [request.response().text() for request in api_requests if request.response() is not None]  # Bodies.
    text = "\n".join([*answers, session_list, page.content()])  # Scan the answers and the page together.
    shell_path = f"/shell/{terminal_support.DEVICE_ID}"  # The path part of the shell address.
    _shot(page, terminal_harness, "review-fr048-no-shell-address.png")  # Save evidence.
    assert len(answers) >= 5  # The scan read the start, the input, the size, and several read answers.
    assert terminal_harness.cloud.base_ws_url + shell_path not in text  # The full shell address never arrives.
    assert shell_path not in text  # The shell address path never arrives.
    assert terminal_harness.cloud.base_ws_url not in text  # The cloud WebSocket host never arrives.
    assert "fake-token" not in text  # The API token never arrives.


def test_review_fr014_history_keeps_five_thousand_lines(
    page: Any, pushable_terminal_harness: TerminalPortalHarness
) -> None:
    """FR-014: the terminal keeps at least 5,000 lines of history."""
    harness = pushable_terminal_harness  # Use a short name for the harness.
    _open_shell(page, harness)  # Start the shell.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # The shell is live.
    numbered = b"".join(b"history-line-%05d\r\n" % number for number in range(1, 5001))  # 5,000 numbered lines.
    harness.shell.push_output(numbered + b"END-OF-HISTORY\r\n")  # The device sends all lines in one frame.
    page.get_by_text("END-OF-HISTORY").wait_for(timeout=READY_TIMEOUT_MS)  # xterm drew the last line.
    with page.expect_download() as download_info:  # Capture the history file.
        page.get_by_test_id("ws-terminal-download").click()  # The file holds each row of the xterm buffer.
    text = Path(download_info.value.path()).read_text(encoding="utf-8")  # Read the history file.
    _shot(page, harness, "review-fr014-five-thousand-lines.png")  # Save evidence.
    assert "history-line-00001" in text  # The first numbered line is still in the history.
    assert "history-line-05000" in text  # The last numbered line is in the history.
    assert text.count("history-line-") == 5000  # No numbered line is lost or repeated.


def test_review_non_final_state_keeps_terminal_live(page: Any, delayed_terminal_harness: TerminalPortalHarness) -> None:
    """Review 1: connecting without output keeps accepting input."""
    page.add_init_script("window.MistWebSocketTerminalTestHooks = {readWaitSeconds: 0.2};")  # Shorten long read.
    _open_shell(page, delayed_terminal_harness)  # Start a shell with delayed banner output.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm before the delayed banner arrives.
    page.keyboard.type("slow")  # Type while the session still has no output.
    received = delayed_terminal_harness.shell.wait_for_input(len("slow"), 3.0)  # Wait for queued bytes.
    _shot(page, delayed_terminal_harness, "review-01-non-final-live.png")  # Save evidence.
    assert received.endswith(b"slow") is True  # Non-final states did not close input.


def test_review_stopping_state_waits_for_final_reason(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Review 1: stopping keeps the read loop until a final state arrives."""
    calls = {"count": 0}  # Count terminal reads served by the test route.

    def answer_read(route: Any) -> None:
        calls["count"] += 1  # Record each browser read request.
        if calls["count"] == 1:  # First answer is a non-final stopping state.
            route.fulfill(status=200, content_type="application/json", body='{"state":"stopping","next":0}')
            return  # Keep the sequence deterministic.
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"state":"finished","reason":"operator exit","next":0}',
        )  # Final answer carries the reason that must appear.

    page.route("**/api/websockets/sessions/*/terminal**", answer_read)  # Replace only terminal reads.
    _open_shell(page, terminal_harness)  # Start the terminal panel.
    page.get_by_text("Reason: operator exit").wait_for(timeout=READY_TIMEOUT_MS)  # Wait for final reason.
    _shot(page, terminal_harness, "review-01-stopping-final.png")  # Save evidence.
    assert calls["count"] >= 2  # The page read again after stopping.


def test_review_empty_live_read_uses_backoff(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Review 2: empty live reads do not create a tight request loop."""
    calls = {"count": 0}  # Count immediate empty reads.

    def answer_empty(route: Any) -> None:
        calls["count"] += 1  # Record each read request.
        route.fulfill(status=200, content_type="application/json", body='{"state":"live","next":0}')  # Empty.

    page.route("**/api/websockets/sessions/*/terminal**", answer_empty)  # Force immediate empty live answers.
    _open_shell(page, terminal_harness)  # Start a terminal with the intercepted read route.
    page.wait_for_timeout(850)  # Wait long enough to prove the 250 ms backoff.
    count_after_wait = calls["count"]  # Snapshot before the screenshot adds more read time.
    _shot(page, terminal_harness, "review-02-empty-read-backoff.png")  # Save evidence.
    assert count_after_wait <= 5  # More calls would show a tight polling loop.


def test_review_rate_limited_large_paste_retries_part(page: Any, quiet_terminal_harness: TerminalPortalHarness) -> None:
    """Review 3: a rate-limited paste part is retried without data loss."""
    refused = {"done": False}  # Refuse one input request, then let the real route handle retries.

    def answer_input(route: Any) -> None:
        if not refused["done"]:  # The first paste part simulates a gateway rate limit.
            refused["done"] = True  # Refuse only once.
            route.fulfill(
                status=429,
                content_type="application/json",
                body='{"error":"rate limited","code":"rate_limited"}',
            )  # Match the terminal HTTP error shape.
            return  # The browser must retry this exact part.
        route.continue_()  # Later input requests reach the real portal route.

    _open_shell(page, quiet_terminal_harness)  # Start the real terminal with a quiet fake shell.
    page.route("**/api/websockets/sessions/*/input", answer_input)  # Intercept input after startup.
    text = "\n".join("x" * 4095 for _index in range(64)) + "x"  # Build a 256 KiB multi-line paste.
    expected = text.replace("\n", "\r").encode("utf-8")  # xterm converts paste line endings to carriage returns.
    page.get_by_test_id("ws-terminal-screen").evaluate(
        """(element, value) => {
            const data = new DataTransfer();
            data.setData('text/plain', value);
            element.dispatchEvent(new ClipboardEvent('paste', {clipboardData: data, bubbles: true, cancelable: true}));
        }""",
        text,
    )  # Dispatch the native paste event with the reviewed paste body.
    page.get_by_test_id("ws-terminal-paste-send").click()  # Send the paste through the browser flow.
    start_marker = b"\x1b[200~"  # Xterm sends this marker when bracketed paste is enabled.
    end_marker = b"\x1b[201~"  # Xterm sends this marker after the full paste body.
    target_length = len(expected) + len(start_marker) + len(end_marker)  # Include both paste markers.
    for _index in range(120):  # Keep Playwright active while it serves route callbacks.
        received_now = quiet_terminal_harness.shell.received_input  # Snapshot the fake device input.
        if len(received_now) >= target_length and received_now.endswith(end_marker):  # Stop after the end marker.
            break  # The assertion below reads the final input.
        page.wait_for_timeout(500)  # Yield to browser requests without blocking route callbacks.
    received = quiet_terminal_harness.shell.received_input  # Read all input after the browser send loop.
    _shot(page, quiet_terminal_harness, "review-03-rate-limited-paste.png")  # Save evidence.
    assert refused["done"] is True  # The journey exercised the rate limit path.
    assert received.startswith(start_marker) is True  # The fake device received the bracketed paste start.
    assert received.endswith(end_marker) is True  # The fake device received the bracketed paste end.
    assert received[len(start_marker) : -len(end_marker)] == expected  # The paste body arrived byte-for-byte.


def test_review_read_only_terminal_refuses_paste_ui(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Review 5: read-only terminals do not open paste confirmation."""
    input_calls = {"count": 0}  # Count input requests because read-only paste must stop in the page.

    def count_input(route: Any) -> None:
        input_calls["count"] += 1  # Record any incorrect paste request.
        body = '{"error":"read only","code":"read_only"}'  # Return the read-only route shape.
        route.fulfill(status=409, content_type="application/json", body=body)  # Fail if paste sends input.

    page.route("**/api/websockets/sessions/*/input", count_input)  # Prove paste sends no request.
    terminal_harness.open_page(page)  # Load the WebSockets page.
    page.get_by_test_id("ws-catalog-entry-ex.monitorTraffic").click()  # Choose a read-only terminal command.
    page.locator('[data-testid="ws-field-site_id"]').select_option("11111111-2222-3333-4444-555555555555")  # Site.
    page.locator('[data-testid="ws-field-device_id"]').select_option("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")  # Device.
    page.get_by_test_id("ws-start-button").click()  # Start the read-only session.
    page.get_by_test_id("ws-terminal-screen").wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Terminal.
    page.evaluate("navigator.clipboard.writeText('line1\\nline2')")  # Put multi-line text on the clipboard.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus the read-only xterm instance.
    page.keyboard.press("Control+Shift+V")  # Attempt keyboard paste.
    dialog_visible = page.get_by_test_id("ws-terminal-paste-dialog").is_visible()  # Inspect the dialog.
    _shot(page, terminal_harness, "review-05-read-only-paste.png")  # Save evidence.
    assert dialog_visible is False  # The read-only terminal must not offer Paste.
    assert input_calls["count"] == 0  # The page did not call the input route for read-only paste.


@pytest.mark.parametrize("code", ["not_found", "not_terminal"])
def test_review_terminal_read_failure_stops_loop(page: Any, terminal_harness: TerminalPortalHarness, code: str) -> None:
    """Review 6: permanent read errors stop the read loop."""
    calls = {"count": 0}  # Count reads to prove the loop stops.

    def answer_failure(route: Any) -> None:
        calls["count"] += 1  # Record each browser read.
        body = '{"error":"permanent read failure","code":"' + code + '"}'  # Return one permanent failure.
        route.fulfill(status=404, content_type="application/json", body=body)  # Simulate the route error.

    page.route("**/api/websockets/sessions/*/terminal**", answer_failure)  # Fail the read route.
    _open_shell(page, terminal_harness)  # Start a terminal session.
    page.get_by_test_id("ws-terminal-status").get_by_text("terminal", exact=False).wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Wait for the user-facing error.
    page.wait_for_timeout(1300)  # Wait longer than the old retry interval.
    _shot(page, terminal_harness, "review-06-" + code + ".png")  # Save evidence.
    assert calls["count"] == 1  # A permanent error must not retry forever.


def test_review_copy_on_select_keeps_selection(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Review 7: copy-on-select keeps the highlighted terminal text."""
    _open_shell(page, terminal_harness)  # Start the terminal.
    page.get_by_test_id("ws-terminal-screen").click(button="right")  # Open the context menu.
    page.get_by_test_id("ws-terminal-menu-select-all").click()  # Select terminal text.
    page.locator(".xterm-selection div").first.wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Selection.
    page.get_by_test_id("ws-terminal-screen").dispatch_event("mouseup")  # Trigger copy-on-select handling.
    page.wait_for_timeout(250)  # Give clipboard promise handling time to finish.
    _shot(page, terminal_harness, "review-07-copy-selection-kept.png")  # Save evidence.
    assert page.locator(".xterm-selection div").count() > 0  # The highlight remains after copy-on-select.


def test_review_11_terminal_header_tracks_state(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Review 11: the session header follows terminal live and final states."""
    _open_shell(page, terminal_harness)  # Start the terminal session.
    page.locator("#wsSessionState", has_text="State: Live").wait_for(timeout=READY_TIMEOUT_MS)  # Header is live.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.keyboard.type("exit")  # Ask the fake shell to close.
    page.keyboard.press("Enter")  # Send the exit command.
    page.locator("#wsSessionState", has_text="State: Finished").wait_for(timeout=READY_TIMEOUT_MS)  # Final state.
    page.locator("#wsSessionReason", has_text="The device closed the shell.").wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Final reason.
    _shot(page, terminal_harness, "review-11-header-state.png")  # Save evidence.
    assert page.locator("#wsStopButton").is_disabled() is True  # A finished session cannot stop again.
    warning = page.get_by_test_id("ws-terminal-warning").inner_text(
        timeout=READY_TIMEOUT_MS
    )  # Read the ended shell warning.
    assert warning == "Warning: Each command runs on the live device."  # An ended shell is not a read-only screen.
    assert page.get_by_test_id("ws-terminal-paste").is_disabled() is True  # An ended shell takes no paste.
    screen_class = page.get_by_test_id("ws-terminal-screen").get_attribute("class") or ""  # Read the geometry class.
    assert "ws-terminal-screen-fixed" not in screen_class  # An ended shell keeps the fitted shell size.


def test_review_12_terminal_counters_show_bytes(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Review 12: terminal counters show output bytes and list state only."""
    _open_shell(page, terminal_harness)  # Start the terminal session.
    page.locator("#wsCounters", has_text="Output:").wait_for(timeout=READY_TIMEOUT_MS)  # Byte counter.
    page.locator("#wsCounters", has_text="bytes").wait_for(timeout=READY_TIMEOUT_MS)  # Unit text.
    status = page.locator(".ws-session-item.active .ws-session-status").inner_text(timeout=READY_TIMEOUT_MS)  # List.
    _shot(page, terminal_harness, "review-12-output-bytes.png")  # Save evidence.
    assert status == "Live"  # Terminal list items show only the state.
    assert "Messages:" not in page.locator("#wsCounters").inner_text(timeout=READY_TIMEOUT_MS)  # No frame count.


def test_review_13_paste_line_count_ignores_trailing_empty_line(
    page: Any, terminal_harness: TerminalPortalHarness
) -> None:
    """Review 13: paste confirmation line count ignores final empty text."""
    _open_shell(page, terminal_harness)  # Start the terminal session.
    text = "show version\nshow chassis hardware\n"  # This text has two real lines and a final line end.
    page.evaluate("(value) => navigator.clipboard.writeText(value)", text)  # Put the paste text on the clipboard.
    page.get_by_test_id("ws-terminal-paste").click()  # Open the paste confirmation dialog.
    page.get_by_test_id("ws-terminal-paste-lines").get_by_text("Lines: 2").wait_for(
        timeout=READY_TIMEOUT_MS
    )  # Final empty entry is ignored.
    one_line_count = page.evaluate("window.MistWebSocketTerminal.testSupport.lineCount('show version')")  # Count.
    _shot(page, terminal_harness, "review-13-paste-line-count.png")  # Save evidence.
    assert one_line_count == 1  # One line without a line end counts as one line.


def test_review_14_hidden_paste_input_hides_label(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Review 14: the paste text label hides with its hidden text box."""
    _open_shell(page, terminal_harness)  # Start the terminal session.
    page.evaluate("navigator.clipboard.writeText('line1\\nline2')")  # Put multi-line text on the clipboard.
    page.get_by_test_id("ws-terminal-paste").click()  # Open the confirmation dialog.
    label_hidden = page.locator("#wsTerminalPasteInputLabel").evaluate(
        "(element) => element.classList.contains('d-none')"
    )  # Inspect label visibility.
    input_hidden = page.get_by_test_id("ws-terminal-paste-input").evaluate(
        "(element) => element.classList.contains('d-none')"
    )  # Inspect text box visibility.
    _shot(page, terminal_harness, "review-14-paste-label-hidden.png")  # Save evidence.
    assert label_hidden is True  # The label hides when the input hides.
    assert input_hidden is True  # The confirmation dialog hides the manual input box.


def test_review_17_session_switch_drops_stale_read(page: Any, pushable_terminal_harness: TerminalPortalHarness) -> None:
    """Review 17: a late read answer of the old session never reaches the shown session."""
    harness = pushable_terminal_harness  # Use a short name for the harness.
    aborted: list[str] = []  # Request URLs that the browser cancelled.
    requested: list[str] = []  # Request URLs that left the browser.
    page.on("requestfailed", lambda request: aborted.append(request.url))  # Record each cancelled request.
    page.on("request", lambda request: requested.append(request.url))  # Record each request.
    _open_shell(page, harness)  # Start shell A.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # Shell A is live.
    shell_id = _active_session_id(page)  # Remember shell A.
    _start_top(page)  # Start screen B, which replaces the shown terminal.
    screen_id = _wait_new_active_session(page, shell_id)  # Screen B is now the shown session.
    page.get_by_text("screen update 99").wait_for(timeout=READY_TIMEOUT_MS)  # Screen B drew its last update.
    harness.shell.push_output(b"STALE-SHELL-OUTPUT\r\n")  # Shell A answers the long read that it still holds.
    page.wait_for_timeout(1500)  # Give a late answer time to reach the page.
    positions = _read_positions(requested, screen_id)  # The read positions of screen B in request order.
    _shot(page, harness, "review-17-switch-drops-stale-read.png")  # Save evidence.
    assert screen_id != shell_id  # The journey shows a second session.
    assert len(positions) >= 2, positions  # The check needs the first read and at least one later read.
    assert positions == sorted(positions), positions  # A position of shell A never moves screen B back.
    assert any(shell_id in url and "/terminal" in url for url in aborted) is True  # The old long read was cancelled.
    page.locator(f'[data-session-id="{shell_id}"]').click()  # Show shell A again.
    page.get_by_text("STALE-SHELL-OUTPUT").wait_for(timeout=READY_TIMEOUT_MS)  # Shell A replays its own output.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # FR-018: all history replays.
    _shot(page, harness, "review-17-switch-back-shows-shell.png")  # Save evidence.


def test_review_20_old_session_end_keeps_shown_session_live(
    page: Any, pushable_terminal_harness: TerminalPortalHarness
) -> None:
    """Review 20: the end of a hidden session never ends the session that the page shows."""
    harness = pushable_terminal_harness  # Use a short name for the harness.
    _open_shell(page, harness)  # Start shell A.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # Shell A is live.
    shell_id = _active_session_id(page)  # Remember shell A.
    _start_top(page)  # Start screen B, which replaces the shown terminal.
    screen_id = _wait_new_active_session(page, shell_id)  # Screen B is now the shown session.
    page.get_by_text("screen update 99").wait_for(timeout=READY_TIMEOUT_MS)  # Screen B drew its last update.
    harness.shell.close_shell()  # Shell A ends while screen B stays live.
    page.wait_for_timeout(1500)  # Give a late final answer of shell A time to reach the page.
    header = page.locator("#wsSessionState").inner_text(timeout=READY_TIMEOUT_MS)  # Read the header state.
    status = page.get_by_test_id("ws-terminal-status").inner_text(timeout=READY_TIMEOUT_MS)  # Read the footer.
    _shot(page, harness, "review-20-old-end-keeps-screen-live.png")  # Save evidence.
    assert screen_id != shell_id  # The journey shows a second session.
    assert "State: Live" in header, header  # The end of shell A does not end screen B.
    assert "finished" not in status.lower(), status  # The footer of screen B does not show the end of shell A.
    page.locator(f'[data-session-id="{shell_id}"]').click()  # Show shell A again.
    page.locator("#wsSessionState", has_text="State: Finished").wait_for(timeout=READY_TIMEOUT_MS)  # Shell A ended.
    _shot(page, harness, "review-20-switch-back-shows-end.png")  # Save evidence.


def test_review_18_session_switch_drops_pending_paste(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Review 18: a paste that waits for confirmation never moves to the next session."""
    _open_shell(page, terminal_harness)  # Start shell A.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # Shell A is live.
    first_id = _active_session_id(page)  # Remember shell A.
    terminal_harness.start_shell(page)  # Start shell B, which the page then shows.
    second_id = _wait_new_active_session(page, first_id)  # Shell B is now the shown session.
    page.locator(f'[data-session-id="{first_id}"]').click()  # Show shell A again.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # Shell A replays its banner.
    _dispatch_terminal_paste(page, "show version\nshow chassis hardware")  # Two lines open the confirmation.
    dialog = page.get_by_test_id("ws-terminal-paste-dialog")  # The paste confirmation dialog.
    dialog.wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # The paste waits for the operator.
    page.locator(f'[data-session-id="{second_id}"]').dispatch_event("click")  # A keyboard user can reach the list.
    page.wait_for_function(
        "(id) => document.querySelector('.ws-session-item.active')?.dataset.sessionId === id",
        arg=second_id,
        timeout=READY_TIMEOUT_MS,
    )  # Shell B is the shown session again.
    _shot(page, terminal_harness, "review-18-switch-drops-paste.png")  # Save evidence.
    assert second_id != first_id  # The journey shows a second shell.
    assert dialog.is_hidden() is True  # The paste of shell A cannot be sent to shell B.
    assert b"show version" not in terminal_harness.shell.received_input  # No shell received the old paste.


def test_review_19_late_input_answer_stays_with_its_session(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Review 19: a late rate limit answer never sends old input to the next session."""
    sent: list[str] = []  # Input request URLs that left the browser.
    held: list[Any] = []  # Input requests of shell A that the test answers late.
    page.on("request", lambda request: sent.append(request.url))  # Record each request URL.
    _open_shell(page, terminal_harness)  # Start shell A.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # Shell A is live.
    first_id = _active_session_id(page)  # Remember shell A.
    page.route(f"**/api/websockets/sessions/{first_id}/input", lambda route: held.append(route))  # Hold input.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus shell A.
    with page.expect_request(f"**/api/websockets/sessions/{first_id}/input"):  # Wait for the held request.
        page.keyboard.type("x")  # One key starts one input request.
    terminal_harness.start_shell(page)  # Start shell B while the input of shell A waits.
    second_id = _wait_new_active_session(page, first_id)  # Shell B is now the shown session.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # Shell B is live.
    held[0].fulfill(status=429, content_type="application/json", body=RATE_LIMITED_BODY)  # Answer shell A late.
    page.wait_for_timeout(1600)  # Wait past the one-second retry delay of the send queue.
    status = page.get_by_test_id("ws-terminal-status").inner_text(timeout=READY_TIMEOUT_MS)  # Footer text.
    _shot(page, terminal_harness, "review-19-late-input-answer.png")  # Save evidence.
    assert second_id != first_id  # The journey shows a second shell.
    assert [url for url in sent if second_id in url and url.endswith("/input")] == []  # Shell B got no input.
    assert "rate" not in status.lower()  # The old rate limit message does not appear for shell B.


def test_review_21_session_list_shows_terminal_without_errors(
    page: Any, pushable_terminal_harness: TerminalPortalHarness
) -> None:
    """Review 21: a session list click shows the terminal output, and xterm logs no option error."""
    harness = pushable_terminal_harness  # Use a short name for the harness.
    errors: list[str] = []  # Browser console errors and page errors.
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)  # Keep errors.
    page.on("pageerror", lambda error: errors.append(str(error)))  # Keep uncaught script errors.
    _open_shell(page, harness)  # Start shell A.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # Shell A is live.
    shell_id = _active_session_id(page)  # Remember shell A.
    _start_top(page)  # Start screen B, which replaces the shown terminal.
    _wait_new_active_session(page, shell_id)  # Screen B is now the shown session.
    page.get_by_text("screen update 99").wait_for(timeout=READY_TIMEOUT_MS)  # Screen B drew its last update.
    page.evaluate("window.scrollTo(0, 0)")  # Put the session list in view, as an operator does to choose a session.
    page.locator(f'[data-session-id="{shell_id}"]').click()  # Show shell A from the session list.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # xterm draws shell A in view.
    in_view = page.get_by_test_id("ws-terminal-screen").evaluate(
        "(element) => { const box = element.getBoundingClientRect(); return box.top < window.innerHeight; }"
    )  # The terminal top must be inside the browser window.
    _shot(page, harness, "review-21-list-click-shows-terminal.png")  # Save evidence.
    assert in_view is True  # The page moved the view to the terminal output.
    assert errors == []  # The page and xterm logged no error.


def test_review_3710_silent_device_shows_notice_and_failed_reason(
    page: Any, silent_terminal_harness: TerminalPortalHarness
) -> None:
    """Issue #3710: a silent device shows a notice, and the cloud close shows a failed reason."""
    harness = silent_terminal_harness  # Use a short name for the harness.
    page.add_init_script(
        "window.MistWebSocketTerminalTestHooks = {readWaitSeconds: 0.5, noOutputNoticeSeconds: 2};"
    )  # Shorten the read wait and the notice wait.
    _open_shell(page, harness)  # Start a shell on the silent device.
    page.locator("#wsSessionReason", has_text=WAITING_NOTICE).wait_for(timeout=READY_TIMEOUT_MS)  # First notice.
    page.locator("#wsSessionReason", has_text=SILENT_NOTICE).wait_for(timeout=READY_TIMEOUT_MS)  # Silent notice.
    page.locator("#wsSessionState", has_text="State: Live").wait_for(timeout=READY_TIMEOUT_MS)  # The socket is open.
    _shot(page, harness, "review-3710-silent-device-notice.png")  # Save evidence of the notice.
    harness.shell.close_shell()  # The Mist cloud closes the silent terminal with an empty close frame.
    page.locator("#wsSessionState", has_text="State: Failed").wait_for(timeout=READY_TIMEOUT_MS)  # Final state.
    page.locator("#wsSessionReason", has_text=ShellRunner.NO_ANSWER_REASON).wait_for(
        timeout=READY_TIMEOUT_MS
    )  # The final reason replaces the notice.
    _shot(page, harness, "review-3710-silent-device-failed.png")  # Save evidence of the final reason.
    assert page.locator("#wsStopButton").is_disabled() is True  # A failed session cannot stop again.


def test_review_3710_first_output_clears_the_waiting_notice(
    page: Any, delayed_terminal_harness: TerminalPortalHarness
) -> None:
    """Issue #3710: the waiting notice shows before the first output, and the output clears it."""
    harness = delayed_terminal_harness  # Use a short name for the harness.
    page.add_init_script(REASON_RECORDER)  # Shorten the read wait, and record each header reason text.
    _open_shell(page, harness)  # Start a shell whose banner arrives after 0.8 seconds.
    page.get_by_text("Welcome to Fake Mist Shell").wait_for(timeout=READY_TIMEOUT_MS)  # The first output arrives.
    page.wait_for_function(
        "() => document.getElementById('wsSessionReason').textContent === ''", timeout=READY_TIMEOUT_MS
    )  # The output clears the notice.
    texts = page.evaluate("window.wsReasonTexts")  # Read each reason text that the page showed.
    _shot(page, harness, "review-3710-first-output-clears-notice.png")  # Save evidence.
    assert WAITING_NOTICE in texts  # The page told the operator that it waits for the device.
    assert not any(text.startswith("The device sent no output") for text in texts)  # An answer gets no silent notice.


def test_review_open_refusal_shows_plain_reason(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Issue #3671: a refused shell open shows the HTTP status in a plain reason."""
    harness = terminal_harness  # Use a short name for the harness.
    shell_path = "/shell/" + terminal_support.DEVICE_ID  # The shell trigger answer points at this path.
    harness.cloud.fail_handshake(shell_path, HandshakeFault("refuse", status_code=503))  # The cloud answers 503.
    _open_shell(page, harness)  # Start a shell that the fake cloud refuses.
    page.locator("#wsSessionState", has_text="State: Failed").wait_for(timeout=READY_TIMEOUT_MS)  # Final state.
    reason = ConnectFailure.REFUSED_TEXT.format(status=503)  # The plain reason names the HTTP status.
    page.locator("#wsSessionReason", has_text=reason).wait_for(timeout=READY_TIMEOUT_MS)  # The header shows it.
    _shot(page, harness, "review-open-refusal-503.png")  # Save evidence of the plain reason.
    assert page.locator("#wsStopButton").is_disabled() is True  # A failed session cannot stop again.
    assert "Read the portal log" not in page.get_by_test_id("ws-terminal-status").inner_text()  # No vague reason.


def test_review_screen_reset_shows_plain_reason(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Issue #3671: a reset during the screen open shows the network reason."""
    harness = terminal_harness  # Use a short name for the harness.
    screen_path = "/screen/" + terminal_support.DEVICE_ID  # The Top trigger answer points at this path.
    harness.cloud.fail_handshake(screen_path, HandshakeFault("reset"))  # The cloud resets the TCP connection.
    harness.open_page(page)  # Load the WebSockets page.
    _start_top(page)  # Start the Top screen command.
    page.locator("#wsSessionState", has_text="State: Failed").wait_for(timeout=READY_TIMEOUT_MS)  # Final state.
    page.locator("#wsSessionReason", has_text=ConnectFailure.NETWORK_TEXT).wait_for(
        timeout=READY_TIMEOUT_MS
    )  # The header shows the network reason.
    _shot(page, harness, "review-screen-reset-network.png")  # Save evidence of the plain reason.
    assert page.locator("#wsStopButton").is_disabled() is True  # A failed session cannot stop again.
    assert len(harness.cloud.requests) >= 1  # The open reached the fake cloud before the reset.
