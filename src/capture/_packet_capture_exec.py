"""Site capture execution, monitor, and download cluster.

Extracted from :mod:`src.capture.packet_capture` to keep
``PacketCaptureManager`` slim. Owns the four subclusters:

* Site capture kickoff (``_execute_site_capture`` and its response handlers)
* Loop-mode helpers (``_attempt_loop_capture``, banners, readiness checks)
* Completion polling (``_wait_for_capture_completion`` and status inspection)
* Stream monitoring and PCAP polling/download

Callers instantiate :class:`PacketCaptureExec` directly so the parent binds
an instance on itself as ``self._exec``; ``__getattr__`` delegates lookups
that miss on the wrapper back to the manager so shared state
(``self.mist_session``, ``self._download_manager``,
``self.websocket_manager``, ``self._export_capture_info_to_csv``) remains
transparent.
"""

from __future__ import annotations  # WHY: postponed evaluation for consistency with parent

import logging  # WHY: audit trail for capture lifecycle events
from collections.abc import Callable  # WHY: type hint for list-captures callbacks
from typing import Any, cast  # WHY: opaque manager plus typed cast for untyped SDK returns

from src.capture.packet_capture_download import PacketCaptureDownloadManager  # WHY: shared parser/downloader
from src.capture.site_capture_loop import SiteCaptureLoopRunner  # WHY: shared loop-runner


def _pc() -> Any:
    """Return the ``packet_capture`` module for test-patchable name lookup.

    Helpers route ``mistapi``/``time``/``_get_*`` calls through this accessor so
    unit tests patching ``src.capture.packet_capture.<name>`` intercept them
    without needing per-helper patches. Deferred import breaks the
    packet_capture <-> helper import cycle.
    """
    from src.capture import packet_capture as _pc_mod  # pylint: disable=import-outside-toplevel

    return _pc_mod  # WHY: attribute lookup on returned module resolves patches at call time


class PacketCaptureExec:
    """Wrapper class holding the extracted exec/monitor/download methods."""

    def __init__(self, manager: Any) -> None:
        """Store the parent manager for delegate lookups."""
        self._mm = manager  # WHY: enable __getattr__ delegation back to PacketCaptureManager

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to the wrapped manager."""
        mm = self.__dict__.get("_mm")  # WHY: guard against half-initialized instances
        if mm is None:  # WHY: only trips during broken init; avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(mm, name)  # WHY: transparent proxy to the parent manager

    # ------------------------------------------------------------------ exec
    def execute_site_capture(self, site_id: str, payload: dict[str, Any]) -> None:
        """Execute site-level packet capture via API."""
        try:  # WHY: broad guard so unexpected failures do not crash the CLI
            print(f"\n> Starting packet capture for site {site_id}...")  # WHY: user progress banner
            logging.info("Initiating site capture with payload: %s", payload)  # WHY: audit request
            response = _pc().mistapi.api.v1.sites.pcaps.startSitePacketCapture(  # WHY: start capture
                self.mist_session, site_id, payload
            )
            self._dispatch_start_response(site_id, response)  # WHY: branch on success/failure
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: user-friendly error
            print(f"\n! Error starting capture: {error}")  # WHY: surface error to user
            logging.exception("Exception in _execute_site_capture: %s", error)  # WHY: full traceback

    def _dispatch_start_response(self, site_id: str, response: Any) -> None:
        """Branch on HTTP 200 (success) vs error paths for a start response."""
        if response.status_code == 200:  # WHY: happy path first
            self._handle_start_success(site_id, response.data)  # WHY: delegate success branch
            return  # WHY: do not fall through to error handling
        self._handle_start_error(response)  # WHY: consolidated error reporting

    def _handle_start_success(self, site_id: str, result: dict[str, Any]) -> None:
        """Display start-of-capture details and route to pcap/stream monitoring."""
        capture_id = result.get("id", "unknown")  # WHY: capture id for status polling
        capture_format = result.get("format", "unknown")  # WHY: format drives monitor path
        print("\n* Capture started successfully!")  # WHY: user confirmation banner
        print(f"  Capture ID: {capture_id}")  # WHY: expose id so user can trace
        print(f"  Format: {capture_format}")  # WHY: expose format so user knows expected flow
        print(f"  Duration: {result.get('duration', 0)} seconds")  # WHY: show capture window
        print(f"  Expires: {result.get('expiry', 'unknown')}")  # WHY: show expiry hint
        logging.info("Site capture started: capture_id=%s, format=%s", capture_id, capture_format)  # WHY: audit
        self._route_monitor(site_id, capture_id, capture_format, result)  # WHY: format-dependent path
        self._export_capture_info_to_csv(result, "site", site_id)  # WHY: persist metadata to CSV

    def _route_monitor(self, site_id: str, capture_id: str, capture_format: str, result: dict[str, Any]) -> None:
        """Route to pcap wait+download or WebSocket stream subscription."""
        if capture_format == "pcap":  # WHY: pcap route downloads a file after capture
            print("\n> Waiting for PCAP file to be ready...")  # WHY: keep user informed
            print("  This may take a few moments after capture completes.")  # WHY: expectation set
            self._wait_and_download_pcap(site_id, capture_id, result.get("duration", 600))  # WHY: pcap flow
            return  # WHY: do not also start stream
        if capture_format == "stream":  # WHY: stream route subscribes to WebSocket
            self._subscribe_to_site_capture_stream(site_id, capture_id)  # WHY: real-time stream

    @staticmethod
    def _handle_start_error(response: Any) -> None:
        """Display error information for a failed capture start response."""
        error_details = (
            response.data if hasattr(response, "data") else "No error details available"
        )  # WHY: safe extract
        if PacketCaptureExec._is_recording_conflict(response.status_code, error_details):  # WHY: special-case UX
            print("\n! Capture already in progress on this AP")  # WHY: explicit conflict message
            print("  Only one capture per AP is allowed at a time")  # WHY: educate user
            print("  Wait for the existing capture to complete or check the Mist portal to stop it")  # WHY: remediate
            logging.error("Capture conflict: Recording already in progress on AP")  # WHY: audit conflict
            return  # WHY: do not print generic error over specialized one
        print(f"\n! Failed to start capture: {response.status_code}")  # WHY: generic failure
        print(f"  Error details: {error_details}")  # WHY: surface API detail
        logging.error("Capture failed: %s - %s", response.status_code, error_details)  # WHY: audit failure

    @staticmethod
    def _is_recording_conflict(status: int, details: Any) -> bool:
        """Return True when the error is a Mist 'Recording already in progress' conflict."""
        if status != 400:  # WHY: conflict only manifests as HTTP 400
            return False  # WHY: not a conflict
        if not isinstance(details, dict):  # WHY: guard non-dict payloads
            return False  # WHY: no structured detail to inspect
        return "Recording already in progress" in details.get("detail", "")  # WHY: string match Mist message

    # ------------------------------------------------------------ loop mode
    def fetch_completed_pcaps(self, site_id: str, iteration: int) -> list[dict[str, Any]]:
        """Fetch completed PCAPs from the API for the last 24 hours."""

        def list_fn() -> Any:
            """Local closure calling listSitePacketCaptures with a 1-day window."""
            return _pc().mistapi.api.v1.sites.pcaps.listSitePacketCaptures(  # WHY: 1d window covers recent captures
                self.mist_session, site_id, duration="1d", limit=100
            )

        return cast(  # WHY: helper returns list[dict] via untyped SDK path
            list[dict[str, Any]],
            self._download_manager.fetch_completed_pcaps(list_fn, iteration),  # WHY: delegate to shared helper
        )

    def attempt_loop_capture(self, site_id: str, payload: dict[str, Any], iteration: int) -> float | None:
        """Attempt to start a new capture and return the capture start time."""
        print("\n  Starting new packet capture...")  # WHY: user status
        logging.info("Loop iteration %s: Starting new capture with payload: %s", iteration, payload)  # WHY: audit
        response = self._loop_start_call(site_id, payload, iteration)  # WHY: isolated API call w/ error handling
        if response is None:  # WHY: caller signal that the API call failed
            return None  # WHY: skip this iteration
        if response.status_code != 200:  # WHY: non-200 means capture did not start
            self._log_loop_start_failure(response, iteration)  # WHY: pretty-print + audit
            return None  # WHY: signal caller to retry next loop
        return self._loop_start_success(site_id, response.data, iteration)  # WHY: parse ok payload

    def _loop_start_call(self, site_id: str, payload: dict[str, Any], iteration: int) -> Any | None:
        """Wrapped startSitePacketCapture call that traps exceptions."""
        try:  # WHY: catch API/network faults so the loop keeps running
            return _pc().mistapi.api.v1.sites.pcaps.startSitePacketCapture(  # WHY: start new capture
                self.mist_session, site_id, payload
            )
        except Exception as capture_error:  # pylint: disable=broad-exception-caught  # WHY: log-and-continue
            print(f"  Error starting capture: {capture_error}")  # WHY: surface to user
            logging.exception("Exception starting capture: %s", capture_error)  # WHY: full traceback
            del iteration  # WHY: kept in signature for consistency with the ok path
            return None  # WHY: signal failure to caller

    @staticmethod
    def _log_loop_start_failure(response: Any, iteration: int) -> None:
        """Format and log a failed loop-mode capture start response."""
        error_details = response.data if hasattr(response, "data") else "No error details"  # WHY: safe extract
        print(f"  Failed to start capture: HTTP {response.status_code}")  # WHY: user-facing status
        print(f"    Error: {error_details}")  # WHY: expose API detail
        logging.error(  # WHY: audit trail for failed iteration
            "Loop iteration %s capture failed: %s - %s", iteration, response.status_code, error_details
        )
        if PacketCaptureExec._is_recording_conflict(response.status_code, error_details):  # WHY: extra hint
            print("    Capture conflict detected - will retry next loop")  # WHY: reassure user loop continues

    def _loop_start_success(self, site_id: str, result: dict[str, Any], iteration: int) -> float:
        """Print + audit + persist a successful loop-mode start and return start time."""
        capture_id = result.get("id", "unknown")  # WHY: id used for tracing
        duration = result.get("duration", 600)  # WHY: display expected duration
        print("  Capture started successfully!")  # WHY: user confirmation
        print(f"    Capture ID: {capture_id}")  # WHY: expose id
        print(f"    Duration: {duration} seconds")  # WHY: expose duration
        logging.info("Loop iteration %s: Capture started - ID=%s", iteration, capture_id)  # WHY: audit
        self._export_capture_info_to_csv(result, "site", site_id)  # WHY: persist metadata
        now: float = _pc().time.time()  # WHY: caller uses this as last_capture_time
        return now

    def execute_site_capture_loop(self, site_id: str, payload: dict[str, Any]) -> None:
        """Execute site-level packet captures in continuous loop mode."""
        runner = SiteCaptureLoopRunner(manager=self._mm)  # WHY: runner needs the manager for delegates
        try:  # WHY: any loop-level failure should not crash the CLI
            runner.run(site_id, payload)  # WHY: shared runner encapsulates the loop
        except Exception as loop_error:  # pylint: disable=broad-exception-caught  # WHY: broad safety net
            print(f"\n! Unexpected error in capture loop: {loop_error}")  # WHY: surface to user
            logging.exception("Exception in capture loop: %s", loop_error)  # WHY: full traceback

    @staticmethod
    def print_loop_banner(payload: dict[str, Any]) -> None:
        """Print the continuous capture mode startup banner."""
        print(f"\n{'=' * 80}\n CONTINUOUS CAPTURE MODE ACTIVE\n{'=' * 80}")  # WHY: visual mode banner
        print("  Press Ctrl+C to stop and exit gracefully")  # WHY: expose exit method
        print(f"  Capture duration: {payload.get('duration', 60)} seconds")  # WHY: expose configured duration
        print(f"  Strategy: Download existing PCAPs, then start new captures\n{'=' * 80}\n")  # WHY: explain

    @staticmethod
    def check_capture_readiness(last_capture_time: float | None, min_interval: int) -> float:
        """Determine if enough time has elapsed to start a new capture."""
        print("\n[Step 3/3] Checking if ready to start new capture...")  # WHY: user status
        if last_capture_time is None:  # WHY: first iteration always ready
            print("  First capture of this session - starting now")  # WHY: reassure user
            return 0  # WHY: no wait
        now: float = _pc().time.time()  # WHY: bind to float so downstream math stays typed
        elapsed = now - last_capture_time  # WHY: seconds since last capture
        if elapsed >= min_interval:  # WHY: interval satisfied
            print(f"  {elapsed:.0f}s elapsed since last capture (>= {min_interval}s) - ready")  # WHY: status
            return 0  # WHY: no wait
        wait_time: float = min_interval - elapsed  # WHY: remaining wait
        print(f"  Only {elapsed:.0f}s elapsed - waiting {wait_time:.0f}s more...")  # WHY: user status
        return wait_time  # WHY: caller sleeps this long

    @staticmethod
    def calc_loop_sleep(wait_time: float, loop_duration: float) -> float:
        """Calculate sleep time before next loop iteration."""
        if wait_time > 0:  # WHY: honor an explicit wait first
            return wait_time  # WHY: user asked to wait
        if loop_duration < 30:  # WHY: fast iteration; nudge to 30s cadence
            return 30 - loop_duration  # WHY: brings total iteration >= 30s
        return 10  # WHY: default backoff for slow iterations

    # ----------------------------------------------------- status polling
    def check_capture_status(
        self,
        captures: list[dict[str, Any]],
        capture_id: str,
        expected_duration: int,
        progress: tuple[float, int],
    ) -> bool | None:
        """Check if a specific capture has completed."""
        elapsed, poll_attempt = progress  # WHY: unpack progress tuple for readability
        match = self._find_capture_record(captures, capture_id)  # WHY: locate our capture row
        if match is None:  # WHY: not seen in this poll
            return self._report_not_found(capture_id, elapsed)  # WHY: log + return False
        return self._classify_capture_state(match, capture_id, expected_duration, elapsed, poll_attempt)  # WHY: check

    @staticmethod
    def _find_capture_record(captures: list[dict[str, Any]], capture_id: str) -> dict[str, Any] | None:
        """Return the matching capture record from a list, or None if absent."""
        for capture in captures:  # WHY: linear scan is fine for ~10s of captures
            if not isinstance(capture, dict):  # WHY: guard malformed payloads
                continue  # WHY: skip and keep looking
            if capture.get("id") == capture_id:  # WHY: match by id
                return capture  # WHY: return the matching record
        return None  # WHY: no match found

    def _classify_capture_state(
        self,
        capture: dict[str, Any],
        capture_id: str,
        expected_duration: int,
        elapsed: float,
        poll_attempt: int,
    ) -> bool | None:
        """Return True if the capture is complete, else None (still running)."""
        enabled = capture.get("enabled", True)  # WHY: Mist sets enabled=False when capture finishes
        timestamp = capture.get("timestamp", 0)  # WHY: capture start epoch
        time_running = _pc().time.time() - timestamp if timestamp else elapsed  # WHY: fall back to local elapsed
        if not enabled:  # WHY: primary completion signal
            logging.debug("Capture %s completed (enabled=False)", capture_id)  # WHY: audit
            return True  # WHY: complete
        if time_running >= expected_duration:  # WHY: secondary signal (duration reached)
            logging.debug("Capture %s completed (duration reached)", capture_id)  # WHY: audit
            return True  # WHY: complete
        self._report_in_progress(capture_id, expected_duration, time_running, poll_attempt)  # WHY: status line
        return None  # WHY: still running

    @staticmethod
    def _report_in_progress(capture_id: str, expected_duration: int, time_running: float, poll_attempt: int) -> None:
        """Print an in-progress status update every 5 polls."""
        remaining = int(expected_duration - time_running)  # WHY: countdown value
        if poll_attempt % 5 == 0:  # WHY: throttle console output
            print(f"  ...capture in progress (~{remaining}s remaining)", end="\r")  # WHY: single-line update
        logging.debug("Capture %s still running (%ss remaining)", capture_id, remaining)  # WHY: audit

    @staticmethod
    def _report_not_found(capture_id: str, elapsed: float) -> bool:
        """Log 'not found' at debug or warning level based on elapsed time."""
        if elapsed < 10:  # WHY: normal startup delay
            logging.debug("Capture %s not found yet (elapsed=%ss)", capture_id, elapsed)  # WHY: audit
        else:  # WHY: past startup grace period
            logging.warning("Capture %s not found in list (elapsed=%ss)", capture_id, elapsed)  # WHY: warn
        return False  # WHY: caller treats False as "not found"

    def poll_capture_once(
        self,
        site_id: str,
        capture_id: str,
        expected_duration: int,
        elapsed: float,
        poll_attempt: int,
    ) -> bool | None:
        """Perform a single capture-status poll cycle."""
        response = _pc().mistapi.api.v1.sites.pcaps.listSitePacketCaptures(  # WHY: fetch latest captures
            self.mist_session, site_id
        )
        if response.status_code != 200:  # WHY: only inspect on success
            return None  # WHY: caller continues polling
        captures = PacketCaptureDownloadManager.parse_captures_response(  # WHY: normalize response
            response.data, poll_attempt
        )
        status = self.check_capture_status(  # WHY: delegate match + logging
            captures, capture_id, expected_duration, (elapsed, poll_attempt)
        )
        return True if status is True else None  # WHY: only "confirmed complete" short-circuits the loop

    def wait_for_capture_completion(self, site_id: str, capture_id: str, expected_duration: int) -> bool:
        """Poll for capture completion status (separate from PCAP download availability)."""
        poll_interval = 3  # WHY: 3s cadence balances responsiveness vs API load
        max_wait = expected_duration + 30  # WHY: allow small backend delay past declared duration
        max_polls = max_wait // poll_interval  # WHY: bound total iterations
        start_time = _pc().time.time()  # WHY: reference epoch for elapsed calculation
        for poll_attempt in range(1, max_polls + 1):  # WHY: bounded loop
            if self._safe_poll(site_id, capture_id, expected_duration, start_time, poll_attempt):  # WHY: check
                return True  # WHY: capture confirmed complete
            _pc().time.sleep(poll_interval)  # WHY: back off between polls to reduce API load
        logging.warning("Capture %s completion check timed out after %ss", capture_id, max_wait)  # WHY: audit
        return False  # WHY: caller treats False as timeout

    def _safe_poll(
        self,
        site_id: str,
        capture_id: str,
        expected_duration: int,
        start_time: float,
        poll_attempt: int,
    ) -> bool:
        """Single poll iteration that traps errors so the wait loop keeps running."""
        try:  # WHY: isolate per-iteration errors
            elapsed = _pc().time.time() - start_time  # WHY: seconds since wait began
            result = self.poll_capture_once(site_id, capture_id, expected_duration, elapsed, poll_attempt)  # WHY: poll
            return result is True  # WHY: True short-circuits, else keep polling
        except Exception as poll_error:  # pylint: disable=broad-exception-caught  # WHY: never abort wait
            logging.exception("Completion poll error: %s", poll_error)  # WHY: full traceback
            return False  # WHY: caller sleeps and retries

    # ----------------------------------------------------- stream monitor
    def monitor_capture_stream(self, channel: str, capture_id: str) -> None:
        """Monitor WebSocket stream for capture packets."""
        try:  # WHY: broad guard so stream errors surface cleanly
            print("\n> Subscribing to capture stream...")  # WHY: user status
            print("  Press Ctrl+C to stop monitoring")  # WHY: expose exit method
            if not self._subscribe_channel(channel):  # WHY: connect + subscribe helper
                return  # WHY: helper already logged failure
            self._print_stream_ready(capture_id)  # WHY: user-facing ready banner
            self.read_stream_packets(channel, capture_id)  # WHY: begin packet loop
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: user-friendly error
            print(f"\n! Error subscribing to stream: {error}")  # WHY: surface error
            logging.exception("Exception in _monitor_capture_stream: %s", error)  # WHY: full traceback

    def _subscribe_channel(self, channel: str) -> bool:
        """Ensure WebSocket manager exists, connect, and subscribe; return confirmation."""
        if not self.websocket_manager:  # WHY: lazy WebSocket creation
            self._mm.websocket_manager = _pc()._get_websocket_manager()(self.mist_session)  # WHY: instantiate on parent
        if not self.websocket_manager.connected:  # WHY: reuse existing connection when possible
            self.websocket_manager.connect()  # WHY: establish WebSocket
        self.websocket_manager.subscribe_to_channel(channel)  # WHY: subscribe to capture channel
        confirmed = self.websocket_manager.wait_for_subscription_confirmation(  # WHY: 10s ack timeout
            channel, timeout_seconds=10
        )
        if not confirmed:  # WHY: subscribe failed
            print("\n! Failed to subscribe to capture stream")  # WHY: surface to user
        return bool(confirmed)  # WHY: caller decides whether to continue

    @staticmethod
    def _print_stream_ready(capture_id: str) -> None:
        """Print the ready-to-monitor banner for a subscribed stream."""
        print("\n* Subscribed to capture stream")  # WHY: user confirmation
        print(f"  Capture ID: {capture_id}")  # WHY: expose id
        print("  Monitoring for packets...")  # WHY: status
        print("-" * 80)  # WHY: visual separator

    def read_stream_packets(self, channel: str, capture_id: str) -> None:
        """Read and count packets from WebSocket stream."""
        if self.websocket_manager is None:  # WHY: guard against uninitialized stream
            logging.error("WebSocket manager not available for stream reading")  # WHY: audit
            return  # WHY: nothing to read
        state = {"count": 0, "start": _pc().time.time()}  # WHY: mutable state shared with helper
        try:  # WHY: catch Ctrl-C to print summary
            while True:  # WHY: infinite drain; helper returns when capture ends
                if self._drain_stream_batch(channel, capture_id, state):  # WHY: batch drain returns True on end
                    return  # WHY: capture ended cleanly
                _pc().time.sleep(0.1)  # WHY: gentle CPU yield between batches
        except KeyboardInterrupt:  # WHY: user aborted monitoring
            print("\n\n! Monitoring stopped by user")  # WHY: user confirmation
            print(f"  Total packets received: {state['count']}")  # WHY: expose summary

    def _drain_stream_batch(self, channel: str, capture_id: str, state: dict[str, Any]) -> bool:
        """Drain one batch of WebSocket messages; return True when the capture end signal is seen."""
        with self.websocket_manager.results_lock:  # WHY: consistent read of shared results dict
            messages = list(self.websocket_manager.command_results.values())  # WHY: snapshot values
        for msg in messages:  # WHY: iterate snapshot
            if not self._msg_matches(msg, channel, capture_id):  # WHY: skip non-matching messages
                continue  # WHY: move on
            state["count"] += 1  # WHY: bump packet count
            self._maybe_print_batch_progress(state)  # WHY: throttle status output
            if msg.get("data", {}).get("pcap_dict") is None:  # WHY: Mist end-of-capture sentinel
                print(f"\n* Capture completed: {state['count']} packets received")  # WHY: user summary
                return True  # WHY: signal caller to exit outer loop
        return False  # WHY: batch drained; keep looping

    @staticmethod
    def _msg_matches(msg: dict[str, Any], channel: str, capture_id: str) -> bool:
        """Return True when a stream message belongs to our channel and capture id."""
        if msg.get("channel") != channel:  # WHY: reject other channels
            return False  # WHY: not ours
        data = msg.get("data", {})  # WHY: safe extract inner data
        return bool(data.get("capture_id") == capture_id)  # WHY: match our capture id

    @staticmethod
    def _maybe_print_batch_progress(state: dict[str, Any]) -> None:
        """Print a running packet count every 10 packets."""
        if state["count"] % 10 == 0:  # WHY: throttle output to every 10 packets
            elapsed = _pc().time.time() - state["start"]  # WHY: seconds since stream began
            print(f"  Received {state['count']} packets ({elapsed:.1f}s elapsed)")  # WHY: user status

    def subscribe_to_site_capture_stream(self, site_id: str, capture_id: str) -> None:
        """Subscribe to WebSocket stream for site capture results."""
        channel = f"/sites/{site_id}/pcaps"  # WHY: Mist channel convention for site captures
        self.monitor_capture_stream(channel, capture_id)  # WHY: shared monitor implementation

    def subscribe_to_org_capture_stream(self, capture_id: str) -> None:
        """Subscribe to WebSocket stream for org capture results."""
        channel = f"/orgs/{self.org_id}/pcaps"  # WHY: Mist channel convention for org captures
        self.monitor_capture_stream(channel, capture_id)  # WHY: shared monitor implementation

    # ------------------------------------------------------- pcap download
    def wait_and_download_pcap(self, site_id: str, capture_id: str, duration: int) -> None:
        """Wait for site-level PCAP capture to complete and download the file."""

        def list_fn() -> Any:
            """Local closure calling listSitePacketCaptures for polling."""
            return _pc().mistapi.api.v1.sites.pcaps.listSitePacketCaptures(  # WHY: list captures for polling
                self.mist_session, site_id
            )

        # WHY: route through manager delegator so tests patching manager._poll_and_download_pcap take effect
        self._mm._poll_and_download_pcap(list_fn, capture_id, duration, prefix="")

    def wait_and_download_pcap_org(self, org_id: str, capture_id: str, duration: int) -> None:
        """Wait for org-level PCAP capture to complete and download the file."""

        def list_fn() -> Any:
            """Local closure calling listOrgPacketCaptures for polling."""
            return _pc().mistapi.api.v1.orgs.pcaps.listOrgPacketCaptures(  # WHY: list org captures for polling
                self.mist_session, org_id
            )

        # WHY: route through manager delegator so tests patching manager._poll_and_download_pcap take effect
        self._mm._poll_and_download_pcap(list_fn, capture_id, duration, prefix="org_")

    def poll_and_download_pcap(
        self,
        list_captures_fn: Callable[[], Any],
        capture_id: str,
        duration: int,
        prefix: str = "",
    ) -> None:
        """Poll for PCAP readiness and download the file."""
        self._print_poll_banner(capture_id, duration)  # WHY: user status
        logging.info("Polling for PCAP availability for capture %s", capture_id)  # WHY: audit
        pcap_url: str | None = None  # WHY: pre-declare for exception branches
        try:  # WHY: broad guard so keyboard interrupt shows a friendly message
            pcap_url = self._download_manager.poll_for_pcap_url(  # WHY: delegate polling to helper
                list_captures_fn, capture_id, duration
            )
            if not pcap_url:  # WHY: polling ended without a URL
                logging.debug("Polling finished for %s without a downloadable URL", capture_id)  # WHY: audit
                return  # WHY: nothing to download
            self._finalize_pcap_save(pcap_url, capture_id, prefix)  # WHY: save the file
        except KeyboardInterrupt:  # WHY: user aborted the wait
            self._handle_pcap_interrupt(capture_id, pcap_url)  # WHY: friendly cancellation UX
        except Exception as error:  # pylint: disable=broad-exception-caught  # WHY: safety net
            self._handle_pcap_error(capture_id, pcap_url, error)  # WHY: friendly failure UX

    @staticmethod
    def _print_poll_banner(capture_id: str, duration: int) -> None:
        """Print the polling banner explaining the wait strategy."""
        print(f"\n* Capture initiated (ID: {capture_id})")  # WHY: user confirmation
        print(f"  Duration: {duration} seconds (plus processing time)")  # WHY: expose duration
        print("  Polling for PCAP file availability...")  # WHY: status
        print("  Press Ctrl+C to cancel wait and check portal manually")  # WHY: expose exit method

    @staticmethod
    def _finalize_pcap_save(pcap_url: str, capture_id: str, prefix: str) -> None:
        """Save the resolved pcap URL to disk and log the outcome."""
        logging.info("PCAP URL resolved for %s; starting file save", capture_id)  # WHY: audit
        PacketCaptureDownloadManager.save_pcap_file(pcap_url, capture_id, prefix)  # WHY: delegate save
        logging.debug("PCAP save callback completed for %s", capture_id)  # WHY: audit

    @staticmethod
    def _handle_pcap_interrupt(capture_id: str, pcap_url: str | None) -> None:
        """User-friendly message when a pcap wait is cancelled by Ctrl-C."""
        print("\n\n! Download cancelled by user")  # WHY: user confirmation
        print(f"  Capture ID: {capture_id}")  # WHY: expose id for manual follow-up
        if pcap_url:  # WHY: only print URL if we already resolved one
            print(f"  Download manually from: {pcap_url}")  # WHY: expose recovery path

    @staticmethod
    def _handle_pcap_error(capture_id: str, pcap_url: str | None, error: Exception) -> None:
        """User-friendly message when a pcap download raises an exception."""
        print(f"\n! Error downloading PCAP file: {error}")  # WHY: surface to user
        logging.exception("Exception in poll_and_download_pcap for %s: %s", capture_id, error)  # WHY: audit
        if pcap_url:  # WHY: only print URL if we already resolved one
            print(f"  Try downloading manually from: {pcap_url}")  # WHY: expose recovery path
