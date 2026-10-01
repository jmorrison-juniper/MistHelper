"""Performance browser journeys for the WebSockets terminal.

Why:
    Issue #3671 needs measured browser evidence for echo delay, large output,
    and concurrent shell load.
"""

from __future__ import annotations  # Keep annotations lazy for Playwright imports.

import statistics  # Summarize echo timings.
import time  # Measure browser journey durations.
from typing import Any  # Playwright objects are duck typed in these tests.

import pytest  # Use Playwright import guard.

from tests.e2e import websockets_terminal_support as terminal_support  # Register and read the shared harness.

pytest.importorskip("playwright", reason="playwright is absent, so the browser journey cannot run")  # Browser guard.
READY_TIMEOUT_MS = terminal_support.READY_TIMEOUT_MS  # Use one browser wait boundary for terminal tests.
TerminalPortalHarness = terminal_support.TerminalPortalHarness  # Keep type hints tied to the shared harness.
terminal_harness = terminal_support.terminal_harness  # Expose the shared fixture to this test module.


def _open_shell(page: Any, harness: TerminalPortalHarness) -> None:
    """Open one terminal shell."""
    harness.open_page(page)  # Load the WebSockets page.
    harness.start_shell(page)  # Start a shell terminal session.


def test_sc001_echo_time_for_200_keys(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """SC-001: measure echo time for 200 keys."""
    _open_shell(page, terminal_harness)  # Start terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    timings: list[float] = []  # Store milliseconds for each key.
    for index in range(200):  # Measure the requested key count.
        marker = chr(97 + (index % 26))  # Use simple printable input.
        start = time.perf_counter()  # Start timing before the key.
        page.keyboard.type(marker)  # Send one key.
        terminal_harness.shell.wait_for_input(index + 1, 2.0)  # Wait until fake device receives it.
        timings.append((time.perf_counter() - start) * 1000.0)  # Store elapsed milliseconds.
    median_ms = statistics.median(timings)  # Median resists one slow browser tick.
    p95_ms = sorted(timings)[int(len(timings) * 0.95) - 1]  # Compute simple p95.
    print(f"SC-001 echo median_ms={median_ms:.2f} p95_ms={p95_ms:.2f}")  # Report measurement.
    path = terminal_harness.screenshot(page, "perf-sc001-echo.png")  # Save evidence.
    assert path.exists() is True  # The screenshot must exist.
    assert p95_ms < 500.0  # The browser E2E run allows Windows scheduler jitter but still bounds latency.


def test_sc007_one_mb_output(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """SC-007: show 1 MB of device output within 3 seconds."""
    _open_shell(page, terminal_harness)  # Start terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    start = time.perf_counter()  # Start before the command.
    page.keyboard.type("big")  # Ask fake shell for large output.
    page.keyboard.press("Enter")  # Send command.
    page.get_by_test_id("ws-terminal-status").wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Wait.
    elapsed = time.perf_counter() - start  # Measure output display time.
    print(f"SC-007 one_mb_seconds={elapsed:.2f}")  # Report measurement.
    path = terminal_harness.screenshot(page, "perf-sc007-one-mb.png")  # Save evidence.
    assert path.exists() is True  # The screenshot must exist.
    assert elapsed < 3.0  # The success criterion limits display time.


def test_sc005_five_busy_shells_with_page_loads(browser: Any, terminal_harness: TerminalPortalHarness) -> None:
    """SC-005: five busy shells keep another portal page responsive."""
    pages = []  # Keep pages open until the measurement ends.
    try:
        for _index in range(5):  # Open five shell pages.
            page = browser.new_page()  # Create one browser tab.
            _open_shell(page, terminal_harness)  # Start one shell.
            page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
            page.keyboard.type("big")  # Make the shell busy with output.
            page.keyboard.press("Enter")  # Start output.
            pages.append(page)  # Keep the tab alive.
        probe = browser.new_page()  # Open a sixth page for responsiveness.
        start = time.perf_counter()  # Start page-load timing.
        probe.goto(
            f"{terminal_harness.base_url}/websockets", wait_until="domcontentloaded", timeout=READY_TIMEOUT_MS
        )  # Load.
        probe.get_by_test_id("websockets-title").wait_for(timeout=READY_TIMEOUT_MS)  # Wait for a visible page.
        elapsed = time.perf_counter() - start  # Measure the page response time.
        print(f"SC-005 busy_shell_page_load_seconds={elapsed:.2f}")  # Report measurement.
        path = terminal_harness.screenshot(probe, "perf-sc005-busy-shells.png")  # Save evidence.
        assert path.exists() is True  # The screenshot must exist.
        assert elapsed < 2.0  # The Windows browser E2E run allows scheduler jitter but still bounds responsiveness.
        probe.close()  # Close the probe tab.
    finally:
        for page in pages:  # Clean each busy shell tab.
            page.close()  # Close browser resources.


def test_review_sc_split_256_kib_under_50_ms(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """Review 4: split a 256 KiB paste without a quadratic pause."""
    terminal_harness.open_page(page)  # Load scripts that expose the terminal test support helper.
    measurement = page.evaluate("""() => {
            const text = 'x'.repeat(256 * 1024);
            const start = performance.now();
            const parts = window.MistWebSocketTerminal.testSupport.splitText(text, 4096);
            const elapsed = performance.now() - start;
            const total = parts.reduce((sum, part) => sum + part.length, 0);
            const maxPart = Math.max(...parts.map((part) => part.length));
            return {elapsed, count: parts.length, total, maxPart};
        }""")  # Measure the browser split helper directly.
    print(
        "SC-review split_256k_ms="
        f"{measurement['elapsed']:.2f} parts={measurement['count']} max_part={measurement['maxPart']}"
    )  # Report the performance number.
    path = terminal_harness.screenshot(page, "perf-review-split-256k.png")  # Save evidence.
    assert path.exists() is True  # The screenshot must exist.
    assert measurement["elapsed"] < 50.0  # The reviewed threshold prevents a page freeze.
    assert measurement["total"] == 256 * 1024  # Splitting must preserve all text.
    assert measurement["maxPart"] <= 4096  # Each part must fit the terminal input route.
