# Feature Specification: Audit Menu #9 — Site Packet Capture

**Feature Branch**: `096-audit-menu-9-site-packet-capture`  
**Created**: 2025-07-25  
**Status**: Draft  
**Type**: Audit (analyze existing implementation, document issues, define acceptance criteria for fixes)  
**Input**: User description: "MistHelper Menu #9: Site Packet Capture — PacketCaptureManager.start_site_packet_capture"

## Current State Summary

Menu #9 provides site-level packet capture for Juniper Mist environments through the `PacketCaptureManager` class. The feature supports six capture types (wireless client, wired client, gateway, switch, new association, scan radio), two output formats (PCAP file download, WebSocket stream), and a continuous loop mode for repeated captures. The implementation spans approximately 2,600 lines within `MistHelper.py` (lines 4787–7404).

**Category**: Interactive (not a data export)  
**SQL Export Relevant**: No

### Capture Types Supported

| Type | Description | Key Parameters |
| ---- | ----------- | -------------- |
| Wireless Client | Captures traffic from connected wireless clients | Client MAC, optional AP MAC, duration, packet count, multicast, tcpdump filter |
| Wired Client | Captures wired client traffic | Client MAC, duration, packet count, tcpdump filter |
| Gateway | Captures WAN/LAN gateway port traffic | Gateway MAC, port selection, duration, tcpdump filter |
| Switch | Captures switch port traffic | Switch MAC, port selection, duration, tcpdump filter |
| New Association | Captures new connection handshakes | Optional SSID filter, duration |
| Scan Radio | Captures raw 802.11 frames on specific channel | AP MAC (or all APs), band, channel, bandwidth |

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Reliable PCAP File Download (Priority: P1)

A network engineer selects Menu #9, configures a wireless client capture in PCAP format, and expects the system to start the capture, wait for completion, download the PCAP file to the local `data/` directory, and confirm the file is valid and complete.

**Why this priority**: This is the primary user workflow — the vast majority of captures use PCAP format. A failure here means the user loses diagnostic data and must restart the entire process manually.

**Independent Test**: Can be fully tested by starting a wireless client capture with PCAP format and verifying the downloaded file opens in Wireshark without corruption.

**Acceptance Scenarios**:

1. **Given** a valid site, client MAC, and PCAP format selected, **When** the user starts a capture and it completes normally, **Then** the system downloads the PCAP file to `data/PacketCapture_{id}.pcap`, reports the file size, and the file is a valid PCAP (correct magic bytes).
2. **Given** a capture is started but the download fails mid-stream (network error, timeout), **When** the download operation encounters an error, **Then** the system cleans up any partial file from disk, notifies the user of the failure, and provides a manual download URL as fallback.
3. **Given** a capture completes but the PCAP URL has expired or returns an error page, **When** the system attempts to download, **Then** the system detects the invalid response (non-PCAP content), notifies the user, and does not save a corrupt file.
4. **Given** a capture is started but the polling for PCAP readiness times out, **When** the timeout expires, **Then** the system informs the user the capture may still be processing and provides the capture ID for manual retrieval.

---

### User Story 2 — Robust Error Handling Across All Capture Types (Priority: P1)

A network engineer uses any of the six capture types and encounters an error condition (API failure, existing capture conflict, invalid input, network interruption). The system handles each error gracefully without crashing, provides clear feedback, and allows the user to recover.

**Why this priority**: Error handling gaps are the most numerous class of issues found in the audit. Unhandled exceptions crash the entire application, losing all session state.

**Independent Test**: Can be tested by simulating each error condition (API errors, network timeouts, invalid inputs) and verifying the system recovers gracefully for each capture type.

**Acceptance Scenarios**:

1. **Given** a capture type is selected, **When** the Mist API returns an error (non-200 status), **Then** the system displays a user-friendly error message with the status code and details, logs the full error, and returns to the menu without crashing.
2. **Given** a capture is attempted on an AP that already has a capture in progress, **When** the API returns "Recording already in progress," **Then** the system informs the user and suggests waiting or checking the Mist portal.
3. **Given** the user enters an invalid MAC address, duration outside 60–86400 seconds, or invalid channel for the selected band, **When** the invalid input is submitted, **Then** the system rejects the input with a clear error message and re-prompts (or returns) without sending a malformed request to the API.
4. **Given** a network interruption occurs during any API call, **When** the request fails with a connection error, **Then** the system catches the exception, logs it, and informs the user without crashing.

---

### User Story 3 — Continuous Loop Mode Capture (Priority: P2)

A network engineer enables loop mode for a wireless client capture. The system continuously runs captures, checks for completed PCAPs, downloads them to a local folder, and starts new captures at regular intervals — all interruptible with Ctrl+C.

**Why this priority**: Loop mode is a power-user feature for long-running diagnostics. It has the most complex control flow and the highest risk of data loss from partial downloads.

**Independent Test**: Can be tested by running loop mode for 2–3 iterations, verifying each PCAP is downloaded completely, and interrupting with Ctrl+C to confirm graceful shutdown.

**Acceptance Scenarios**:

1. **Given** loop mode is enabled and a capture completes, **When** the system downloads the PCAP, **Then** it saves the file atomically (write to temp file, then rename) so partial downloads never persist as apparently-complete files.
2. **Given** loop mode is running and a download fails, **When** the next iteration begins, **Then** the system retries the failed download (the capture ID is not marked as "already downloaded") rather than permanently skipping it.
3. **Given** loop mode is running, **When** the user presses Ctrl+C, **Then** the system stops cleanly — completes any in-progress download, reports how many captures were collected, and exits without leaving partial files.
4. **Given** loop mode starts a new capture, **When** less than the minimum capture interval has elapsed since the last capture, **Then** the system waits the remaining time before starting a new capture.

---

### User Story 4 — WebSocket Stream Monitoring (Priority: P3)

A network engineer selects "stream" format for a capture. The system subscribes to the WebSocket channel, displays real-time packet counts, and exits cleanly when the capture ends or the user interrupts.

**Why this priority**: Stream mode is a secondary format used less frequently than PCAP downloads. However, the current implementation has an infinite loop with no automatic exit condition, which is a significant usability issue.

**Independent Test**: Can be tested by starting a stream-format capture and verifying the system displays packet counts, automatically exits when the capture duration expires, and responds to Ctrl+C.

**Acceptance Scenarios**:

1. **Given** stream format is selected, **When** the WebSocket connection is established, **Then** the system displays real-time packet count updates and a running timer.
2. **Given** stream mode is active, **When** the capture duration expires, **Then** the system automatically stops monitoring and exits (not an infinite loop requiring Ctrl+C).
3. **Given** WebSocket connection fails or subscription times out, **When** the error occurs, **Then** the system reports the failure, cleans up WebSocket resources, and returns to the menu without hanging.
4. **Given** stream mode is active, **When** the user presses Ctrl+C, **Then** the system cleanly disconnects the WebSocket and reports a summary of packets observed.

---

### User Story 5 — Multi-AP Scan Radio Capture (Priority: P3)

A network engineer selects scan radio capture with "ALL_APS" option. The system fetches all APs at the site, checks for existing captures, and launches simultaneous scan captures across all APs.

**Why this priority**: Multi-AP scan is a specialized feature. It works but has potential reliability issues with large AP counts and lacks validation of capture conflicts.

**Independent Test**: Can be tested by selecting scan capture with ALL_APS at a multi-AP site and verifying captures start on all APs without errors.

**Acceptance Scenarios**:

1. **Given** ALL_APS is selected for a scan capture, **When** the site has multiple APs, **Then** the system starts captures on all APs simultaneously and reports the count of successful/failed starts.
2. **Given** some APs already have captures running, **When** the system detects conflicts, **Then** it skips conflicting APs, starts captures on available APs, and reports which APs were skipped and why.

---

### Edge Cases

- What happens when the user selects gateway or switch capture but the selected device has no available ports? The system should detect the empty port list and abort with a clear message rather than sending an empty payload to the API.
- What happens when the polling for capture completion encounters a capture ID that no longer appears in the API results? The system should distinguish between "capture too new to appear" (< 10 seconds) and "capture disappeared" (> 10 seconds) and handle each appropriately.
- What happens when duration is set to the maximum (86,400 seconds / 24 hours) in PCAP mode? The polling timeout buffer of 120 seconds may be insufficient for large captures. The timeout should scale with the capture duration.
- What happens when the Mist API response structure changes (e.g., data returned as dict with "results" key vs. raw list)? The system should handle both structures robustly, which it currently does, but should log warnings for unexpected formats.
- What happens when `num_packets=0` (unlimited) is set? The completion polling relies on `expected_duration` but has no special handling for captures that may end early when packet count is unlimited.
- What happens when the device clock and the polling client clock are significantly skewed? The `_wait_for_capture_completion` method compares device timestamps against local `time.time()`, which can cause premature or delayed completion detection.

## Audit Findings *(mandatory for audit specs)*

### Critical Issues

- **AUDIT-001: PCAP download has no error handling for network failures.** The `requests.get(pcap_url, timeout=300)` call in `_wait_and_download_pcap` (single capture download) is not wrapped in try/except. A connection timeout, DNS failure, or network interruption will crash the method with an unhandled exception. The loop mode download does have a try/except but does not clean up partial files.
- **AUDIT-002: Partial PCAP files are not cleaned up on download failure.** In loop mode, if a download fails mid-stream (after file creation but before completion), the partial file remains on disk. On the next iteration, the file-existence check skips this capture ID, permanently losing the data. Single-capture mode writes the entire response content at once (not streaming), reducing but not eliminating this risk.
- **AUDIT-003: No content validation of downloaded PCAP files.** Downloaded content is written to disk without checking Content-Type headers, PCAP magic bytes, or file size. An expired URL returning an HTML error page, or a zero-byte response, will be saved as a `.pcap` file.
- **AUDIT-004: WebSocket stream monitoring has no automatic exit.** The `_subscribe_to_site_capture_stream` method contains a `while True` loop with `time.sleep(0.1)` that only exits on Ctrl+C (KeyboardInterrupt). There is no timeout or duration-based exit condition. Users must forcefully interrupt the process.
- **AUDIT-005: Channel validation accepts any integer.** The scan radio capture validates that the channel input is an integer but does not validate the value against the selected band's valid channel list. Invalid channels (e.g., channel 999 on 2.4 GHz) are passed directly to the API.

### High-Priority Issues

- **AUDIT-006: Duplicate code between site and org PCAP download methods.** `_wait_and_download_pcap` (site) and `_wait_and_download_pcap_org` (org) are nearly identical (~170 lines each) with only the API endpoint and filename differing. Bug fixes must be applied in both places, creating a maintenance risk.
- **AUDIT-007: No retry logic for transient download failures.** All three download paths (single capture, loop mode, org capture) attempt the download exactly once. Transient HTTP 5xx errors, DNS failures, or connection resets require the user to manually restart the entire capture process.
- **AUDIT-008: Port selection allows empty port list.** In gateway and switch capture, if the device has no available ports or the user selection results in an empty list, the payload is sent to the API with an empty ports dictionary. The API may reject this silently or behave unpredictably.
- **AUDIT-009: WebSocket connection and subscription lack error handling.** The `connect()` and `subscribe_to_channel()` calls are not wrapped in try/except. A network failure during WebSocket setup will crash the method. Additionally, if subscription confirmation times out (10 seconds), no WebSocket cleanup occurs.
- **AUDIT-010: Hardcoded polling intervals and timeout buffers.** Multiple hardcoded values control timing behavior: 3-second completion poll interval, 5-second download poll interval, 30-second completion buffer, 120-second download buffer, 10-second WebSocket subscription timeout. These cannot be adjusted for slow networks or large captures.
- **AUDIT-011: Inconsistent error handling patterns across methods.** Some methods return on error, some continue, some raise exceptions implicitly. This makes behavior unpredictable and complicates testing.

### Test Coverage Gaps

- **AUDIT-012: No automated tests exist for PacketCaptureManager.** The entire class (2,600+ lines, 20+ methods) has zero unit tests, zero integration tests, and zero mock-based tests. All testing is manual. This is the single largest test coverage gap in the feature.

## Requirements *(mandatory)*

### Functional Requirements

#### Error Handling & Reliability

- **FR-001**: System MUST wrap all API calls in error handling that catches connection failures, timeouts, and unexpected response formats, displaying a user-friendly message and returning to the menu without crashing.
- **FR-002**: System MUST wrap the PCAP file download operation in error handling that catches network errors, timeouts, and HTTP error responses.
- **FR-003**: System MUST clean up partial PCAP files from disk when a download fails mid-stream, ensuring no corrupt files remain that would be skipped on retry.
- **FR-004**: System MUST validate downloaded PCAP content before saving — at minimum checking that the response is not an HTML error page and the file is non-zero bytes.
- **FR-005**: System MUST retry failed PCAP downloads at least once (with a brief delay) before giving up, to handle transient network errors.

#### Input Validation

- **FR-006**: System MUST validate channel numbers against the selected band's valid channel list (2.4 GHz: 1–14, 5 GHz: 36–177 in standard DFS/non-DFS ranges, 6 GHz: 1–233) before sending the capture request to the API.
- **FR-007**: System MUST validate that the port list is non-empty before sending a gateway or switch capture request, displaying an error message if no ports are available or selected.
- **FR-008**: System MUST validate duration at the execution layer (not just the UI prompt), rejecting values outside the 60–86400 range before constructing the API payload.

#### WebSocket Stream

- **FR-009**: System MUST automatically exit WebSocket stream monitoring when the capture duration expires, rather than requiring the user to press Ctrl+C.
- **FR-010**: System MUST wrap WebSocket connection and subscription operations in error handling that catches network failures, cleans up resources, and returns to the menu.

#### Loop Mode

- **FR-011**: System MUST write downloaded PCAP files atomically in loop mode (write to a temporary file, then rename on success) to prevent partial files from persisting.
- **FR-012**: System MUST not permanently skip a capture ID in loop mode if the download fails — failed downloads should be eligible for retry on subsequent iterations.

#### Code Quality

- **FR-013**: System MUST consolidate the site and org PCAP download methods into a single parameterized method to eliminate code duplication and ensure consistent behavior.
- **FR-014**: System MUST have automated test coverage for all capture type configurations, error handling paths, input validation, download operations, and loop mode behavior.

### Key Entities

- **PacketCaptureManager**: The main class handling all capture operations. Initialized with a Mist API session and organization ID. Manages capture lifecycle from user input through API invocation to file download or stream monitoring.
- **Capture Payload**: The configuration dictionary sent to the Mist API. Structure varies by capture type (client, gateway, switch, scan). Key attributes: type, duration, num_packets, max_pkt_len, format, and type-specific fields (client_mac, gateways dict, aps dict).
- **Capture Session**: The API response after starting a capture. Key attributes: id (capture UUID), format, duration, expiry, and (after completion) the PCAP download URL.
- **Tcpdump Expression**: An optional traffic filter applied to the capture. The system provides 40+ pre-built filter options plus custom expression entry. Passed as a string in the payload.

## Assumptions

- The Mist API's "Recording already in progress" error (HTTP 400) is the only capture-conflict indicator; no other status codes signal this condition.
- PCAP download URLs generated by the Mist API are time-limited but valid for at least 24 hours — sufficient for the polling and download window.
- The `mistapi` SDK handles authentication and session management; PacketCaptureManager does not need to re-authenticate.
- WebSocket streaming is a secondary feature; PCAP file download is the primary and recommended workflow.
- Channel validation lists (valid channels per band) can use standard IEEE 802.11 ranges; region-specific restrictions are enforced by the Mist API, not by the client tool.
- The `data/` directory is writable and has sufficient disk space for PCAP files (typical captures are under 100 MB).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of capture workflows (all 6 types × 2 formats) complete without unhandled exceptions when the API returns any standard HTTP status code (200, 400, 401, 403, 404, 500).
- **SC-002**: Zero corrupt or partial PCAP files remain on disk after any error condition (verified by checking PCAP magic bytes on all files in `data/` after error scenarios).
- **SC-003**: Users can complete a standard wireless client PCAP capture (select site → configure → download file) in under 5 minutes of interactive time (excluding capture duration).
- **SC-004**: Automated test coverage reaches at least 80% of PacketCaptureManager methods, covering all capture types, error handling paths, input validation, and download operations.
- **SC-005**: WebSocket stream monitoring automatically exits within 10 seconds of the capture duration expiring, without requiring user intervention.
- **SC-006**: Loop mode operates for 10+ consecutive iterations without data loss — every completed capture has a corresponding valid PCAP file on disk.
- **SC-007**: Invalid inputs (bad MAC format, out-of-range channel, out-of-range duration, empty port list) are rejected before any API call is made, with clear error messages displayed to the user.
