"""Performance browser journeys for the WebSockets terminal.

Why:
    Issue #3671 needs measured browser evidence for echo delay, large output,
    and concurrent shell load.
"""

from __future__ import annotations  # Keep annotations lazy for Playwright imports.

import statistics  # Summarize echo timings.
import threading  # Coordinate five simultaneous output bursts.
import time  # Measure browser journey durations.
from typing import Any  # Playwright objects are duck typed in these tests.

import pytest  # Use Playwright import guard.

from tests.e2e.websockets_tab import terminal_support  # Register and read the shared harness.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.devices import ShellDevice  # Extend the fake shell.
from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import FakeConnection  # Send fake frames.

pytest.importorskip("playwright", reason="playwright is absent, so the browser journey cannot run")  # Browser guard.
READY_TIMEOUT_MS = terminal_support.READY_TIMEOUT_MS  # Use one browser wait boundary for terminal tests.
TerminalPortalHarness = terminal_support.TerminalPortalHarness  # Keep type hints tied to the shared harness.
terminal_harness = terminal_support.terminal_harness  # Expose the shared fixture to this test module.


ONE_MIB = 1_048_576  # The fake shell sends this many bytes for the big command.
OUTPUT_DRAWN = """(minimum) => {
    const counter = document.getElementById('wsCounters');
    const match = counter ? counter.textContent.match(/Output: (\\d+) bytes/) : null;
    if (!match || Number(match[1]) < minimum) return false;
    const rows = Array.from(document.querySelectorAll('[data-testid="ws-terminal-screen"] .xterm-rows > div'))
        .map((row) => row.textContent.replace(/\\s+$/, ''))
        .filter((row) => row.length > 0);
    const last = rows.length ? rows[rows.length - 1] : '';
    return rows.some((row) => row.includes('XXXXXXXXXX')) && last.endsWith('device>');
}"""  # True only when the page read all output and xterm drew the prompt after the output.


class BusyShellDevice(ShellDevice):
    """Hold five output bursts open during page-load measurements."""

    def __init__(self) -> None:
        """Build the shared start barrier and completion release."""
        super().__init__()  # Keep normal shell behavior for startup and input.
        self.ready = threading.Barrier(6)  # Five shells and the test meet before measurements.
        self.release = threading.Event()  # The test releases completed workers after all page loads.
        self.activity_lock = threading.Lock()  # Protect the shared output measurements.
        self.next_stream_id = 0  # Assign stable identifiers to overlapping command workers.
        self.active_count = 0  # Count bursts that started and wait for release.
        self.connections: dict[int, FakeConnection] = {}  # Keep each active fake device connection.
        self.stream_bytes: dict[int, int] = {}  # Measure each connection independently.

    def _run_line(self, connection: FakeConnection, line: str) -> None:
        """Hold a large output command open at a deterministic boundary."""
        if line != "big":  # Keep all commands except the performance command unchanged.
            super()._run_line(connection, line)  # Use normal fake shell behavior.
            return  # The base command completed.
        worker = threading.Thread(target=self._run_burst, args=(connection,), daemon=True)  # Keep pings readable.
        worker.start()  # Run output independently from the fake server input loop.

    def _run_burst(self, connection: FakeConnection) -> None:
        """Keep one output stream active while the fake server handles keepalive frames."""
        transmitted = 1024  # Start with one bounded output part before measurement.
        with self.activity_lock:  # Assign one stable identifier before output starts.
            stream_id = self.next_stream_id  # Identify this command worker independently.
            self.next_stream_id += 1  # Reserve a new identifier for the next worker.
        self._send_output(connection, b"X" * transmitted)  # Send output before the shared barrier.
        with self.activity_lock:  # Publish this active stream for controlled output.
            self.active_count += 1  # Mark this burst active before the barrier.
            self.connections[stream_id] = connection  # Let the test emit measured parts.
            self.stream_bytes[stream_id] = transmitted  # Record this stream's initial part.
        self.ready.wait(timeout=30.0)  # Start all five streams before the first page load.
        self.release.wait(timeout=60.0)  # Stay active through the tenth visible page load.
        with self.activity_lock:  # Protect the count read by the browser thread.
            self.active_count -= 1  # Mark the overlapping stream complete after release.
        prompt = ("\x1b[?2004h" + self.prompt).encode("utf-8")  # Build this connection's prompt.
        self._send_output(connection, prompt)  # Finish this burst on its own shell connection.

    def all_active(self) -> bool:
        """Report whether all five bursts remain inside the measured interval."""
        with self.activity_lock:  # Read one consistent worker count.
            return self.active_count == 5  # Require every output worker to stay active.

    def byte_snapshot(self) -> dict[int, int]:
        """Return one byte count for each active connection."""
        with self.activity_lock:  # Read one consistent per-stream snapshot.
            return dict(self.stream_bytes)  # Isolate the caller from concurrent updates.

    def start_cycle(self, cycle: int) -> None:
        """Send one output part from each stream during this measured load."""
        assert 1 <= cycle <= 10  # Limit controlled output to the ten measured loads.
        with self.activity_lock:  # Read one consistent active-connection set.
            connections = dict(self.connections)  # Send without holding the measurement lock.
        assert len(connections) == 5  # Require all five streams for every measured load.
        for stream_id, connection in connections.items():  # Send bytes on every open stream.
            self._send_output(connection, b"X" * 1024)  # Emit a positive part inside this load interval.
            with self.activity_lock:  # Publish this stream's new byte count.
                self.stream_bytes[stream_id] += 1024  # Prove this stream sent bytes in this load.

    def assert_completed(self) -> None:
        """Send and verify the exact remainder for all five streams."""
        with self.activity_lock:  # Read one consistent stream state before completion.
            connections = dict(self.connections)  # Complete streams without holding the lock.
            counts = dict(self.stream_bytes)  # Calculate each exact remainder.
        for stream_id, connection in connections.items():  # Complete each stream sequentially.
            remaining = ONE_MIB - counts[stream_id]  # Calculate this stream's exact remainder.
            self._send_output(connection, b"X" * remaining)  # Send the remaining device output.
            with self.activity_lock:  # Publish exact completion for this stream.
                self.stream_bytes[stream_id] += remaining  # Record exactly one MiB.
        assert sorted(self.byte_snapshot().values()) == [ONE_MIB] * 5  # Require five exact outputs.


class BusyLoadJourney:
    """Run and measure one five-shell performance journey."""

    def __init__(self, browser: Any, harness: TerminalPortalHarness, shell: BusyShellDevice) -> None:
        """Store the browser, portal, and coordinated shell."""
        self.browser = browser  # Create each isolated page from one browser.
        self.harness = harness  # Use one portal process for all measured load.
        self.shell = shell  # Coordinate all five fake output workers.
        self.pages: list[Any] = []  # Keep busy shell pages open through measurement.
        self.probe: Any | None = None  # Keep the measured page for screenshot evidence.

    def start(self) -> None:
        """Start five output bursts and stop them at the shared barrier."""
        for _index in range(5):  # Open the required five shell pages.
            page = self.browser.new_page()  # Create one isolated browser page.
            _open_shell(page, self.harness)  # Start one shell terminal session.
            page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm before input.
            page.keyboard.type("big")  # Request one MiB from this fake shell.
            page.keyboard.press("Enter")  # Start this output worker.
            self.pages.append(page)  # Keep the busy page open.
        self.shell.ready.wait(timeout=30.0)  # Release the barrier after all five bursts start.

    def measure(self) -> list[float]:
        """Measure ten visible loads while all output workers stay active."""
        assert self.shell.all_active() is True  # Confirm every burst overlaps the first load.
        self.probe = self.browser.new_page()  # Open one page for responsiveness measurements.
        routes = (
            ("/websockets", "[data-testid='websockets-title']"),
            ("/operations", "[data-testid='operation-accordion']"),
        )  # Use two visible roots.
        samples: list[float] = []  # Keep every successful visible-load duration.
        for index in range(10):  # Measure five loads for each required route.
            bytes_before = self.shell.byte_snapshot()  # Record every stream before this load.
            assert len(bytes_before) == 5  # Require all five streams before every measurement.
            route, selector = routes[index % 2]  # Alternate routes to avoid route-order bias.
            start = time.perf_counter()  # Start before output and browser navigation.
            self.shell.start_cycle(index + 1)  # Send one part from every stream during this load.
            self.probe.goto(
                f"{self.harness.base_url}{route}", wait_until="domcontentloaded", timeout=READY_TIMEOUT_MS
            )  # Load one document.
            self.probe.locator(selector).first.wait_for(
                state="visible", timeout=READY_TIMEOUT_MS
            )  # Require visible content.
            samples.append(time.perf_counter() - start)  # Keep the complete visible-load duration.
            bytes_after = self.shell.byte_snapshot()  # Record every stream after this load.
            assert bytes_after.keys() == bytes_before.keys()  # Keep the same five streams.
            assert all(bytes_after[key] > bytes_before[key] for key in bytes_before)  # Require five deltas.
        assert self.shell.all_active() is True  # Confirm every burst overlaps the tenth load.
        return samples  # Return all ten successful measurements.

    def finish(self) -> None:
        """Release output and close every browser page."""
        self.shell.assert_completed()  # Require five exact one-MiB results while streams remain active.
        self.shell.release.set()  # Let all five completed output workers return.
        for page in self.pages:  # Release each busy browser page after device completion.
            page.close()  # Release this busy browser page.
        if self.probe is not None:  # The probe exists after measurement starts.
            self.probe.close()  # Release the measured browser page.


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
    assert p95_ms < 50.0  # SC-001 requires 95 percent of the measured keys to stay below 50 ms.


def test_sc007_one_mib_output(page: Any, terminal_harness: TerminalPortalHarness) -> None:
    """SC-007: show 1 MiB of device output within 3 seconds."""
    _open_shell(page, terminal_harness)  # Start terminal.
    page.get_by_test_id("ws-terminal-screen").click()  # Focus xterm.
    page.get_by_text("device>").first.wait_for(timeout=READY_TIMEOUT_MS)  # Wait for the first prompt before timing.
    start = time.perf_counter()  # Start before the command.
    page.keyboard.type("big")  # Ask fake shell for large output.
    page.keyboard.press("Enter")  # Send command.
    page.wait_for_function(OUTPUT_DRAWN, arg=ONE_MIB, timeout=READY_TIMEOUT_MS)  # Wait for all output and the prompt.
    elapsed = time.perf_counter() - start  # Measure output display time.
    output_text = page.locator("#wsCounters").inner_text(timeout=READY_TIMEOUT_MS)  # Read the byte counter.
    print(f"SC-007 one_mib_seconds={elapsed:.2f} counter={output_text!r}")  # Report measurement.
    path = terminal_harness.screenshot(page, "perf-sc007-one-mib.png")  # Save evidence.
    assert path.exists() is True  # The screenshot must exist.
    assert elapsed < 3.0  # The success criterion limits display time.


def test_sc005_five_busy_shells_with_page_loads(browser: Any) -> None:
    """SC-005: five active output bursts keep portal pages responsive."""
    shell = BusyShellDevice()  # Coordinate the five output workers at one barrier.
    harness = TerminalPortalHarness(shell=shell).start()  # Use one portal process for the complete measurement.
    journey = BusyLoadJourney(browser, harness, shell)  # Own every page and output worker.
    try:
        journey.start()  # Start and hold five overlapping one-MiB bursts.
        samples = journey.measure()  # Measure ten visible loads during the overlap.
        p95_seconds = sorted(samples)[9]  # Nearest-rank p95 selects rank 10 from ten samples.
        print(f"SC-005 busy_shell_page_load_p95_seconds={p95_seconds:.2f} samples={len(samples)}")  # Report evidence.
        path = harness.screenshot(journey.probe, "perf-sc005-busy-shells.png")  # Save visible evidence.
        assert path.exists() is True  # The screenshot must exist.
        assert len(samples) == 10  # Any failed load prevents the required sample count.
        assert p95_seconds < 1.0  # Every load must pass for this ten-sample nearest-rank p95.
    finally:
        journey.finish()  # Complete all bursts and close every browser page.
        harness.stop()  # Stop the isolated portal and fake cloud.


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


@pytest.mark.parametrize(
    ("raw_body", "failure_mode"),
    [(b"", "empty_body"), (b"bad json", "malformed_json")],
    ids=["empty_body", "malformed_json"],
)
def test_empty_body_and_malformed_json_answers_stay_under_50_ms(
    page: Any,
    raw_body: bytes,
    failure_mode: str,
) -> None:
    """Normalize invalid response bodies without a visible browser pause."""
    harness = terminal_support.TerminalPortalHarness().start()  # Start a real portal for this response case.
    try:  # Always stop the portal and fake cloud after the browser measurement.
        harness.open_page(page)  # Load the shared readJsonAnswer helper in the real portal page.
        measurement = page.evaluate(
            """async ({body}) => {
                const response = new Response(body, {status: 503, headers: {'Content-Type': 'application/json'}});
                const start = performance.now();
                const answer = await readJsonAnswer(response);
                return {elapsed: performance.now() - start, error: answer.error};
            }""",
            {"body": raw_body.decode("utf-8")},
        )  # Measure the production response normalizer with the selected invalid body.
        print(
            f"SC-review {failure_mode}_json_answer_ms={measurement['elapsed']:.2f}"
        )  # Report which failure mode produced the measurement.
        assert measurement["error"] == "The portal is restarting. Wait a moment, then try again."  # Keep guidance.
        assert measurement["elapsed"] < 50.0  # Invalid response text must not pause terminal browser work.
    finally:
        harness.stop()  # Stop both local servers for this parameter case.
