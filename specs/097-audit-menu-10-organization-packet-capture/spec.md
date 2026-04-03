# Feature Specification: AUDIT: Menu #10 - Organization Packet Capture

**Feature Branch**: `097-audit-menu-10-organization-packet-capture`
**Created**: 2026-04-03
**Status**: Draft
**Input**: User request: "Audit spec for MistHelper Menu #10: Organization Packet Capture — analyze start_org_packet_capture implementation, document current state, identify issues, and define acceptance criteria for fixes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start org-level packet capture (Priority: P1)

A network operator uses the interactive MistHelper menu to start an organization-level packet capture on an MxEdge device.

Why this priority: This is the primary user flow for Menu #10 and must work reliably for troubleshooting.

Independent Test:
- Run the interactive menu with a mocked API session that returns a single MxEdge and valid interface stats, follow prompts, and verify that the _execute_org_capture path is invoked with the expected payload.

Acceptance Scenarios:
1. Given an org with at least one MxEdge and reachable REST API, When the operator selects an MxEdge, a port, configures duration/filters/format and confirms, Then the tool calls the Mist API to start an org capture with the correct payload and reports the capture ID on success.
2. Given the Mist API returns a non-200 response when starting capture, When the call fails, Then the tool prints the HTTP status and error details and does not crash.
3. Given the capture is started in stream format, When subscribing succeeds, Then the tool subscribes to the org WebSocket channel and shows live packet counts until completion or user cancels.
4. Given the capture is started in pcap format and the pcap_url becomes available within expected time, Then the tool downloads the PCAP to the data directory and reports path and size.

---

### Edge Cases

- Organization has zero MxEdges: the function must detect and exit gracefully (currently handled but should be covered by tests).
- API returns unexpected data shapes (e.g., dict vs list) for stats and capture lists: code attempts to handle both but needs tests for malformed/partial responses.
- API returns success but no capture id / missing pcap_url: code should handle missing fields without raising unhandled exceptions and provide user guidance.
- Download failure (network timeout, non-200): tool must surface a clear error message and suggest manual download URL when available.
- Long durations: ensure polling logic does not produce zero iterations or excessively long blocking behavior.
- User cancels at various prompts: ensure KeyboardInterrupt/EOF are handled consistently without leaving partial state.

## Requirements *(mandatory)*

### Functional Requirements

- FR-001: The interactive menu MUST list available organization MxEdges and associated interface indices for selection.
- FR-002: The tool MUST validate user inputs (indices, duration, num_packets, max_pkt_len, tzsp port) and refuse invalid values with an explanatory message.
- FR-003: On confirmation, the tool MUST construct a payload matching the Mist API contract for org captures (type, duration, num_packets, max_pkt_len, format, mxedges -> interfaces) and call the API.
- FR-004: On API success (200), the tool MUST handle the returned result safely (missing fields allowed) and proceed according to capture format (stream vs pcap vs tzsp).
- FR-005: When format == stream, the tool MUST subscribe to the org WebSocket channel and display progress until capture end or user cancellation.
- FR-006: When format == pcap, the tool MUST poll org capture listings until pcap_url is available (bounded wait) and then download the PCAP to an application data directory and confirm file integrity (non-zero size).
- FR-007: All external calls (API, HTTP download, WebSocket) MUST have timeouts and clear error handling; failures must be logged and produce a user-facing message with next steps.
- FR-008: The tool MUST export capture metadata to CSV after start (or on failure record error metadata) without leaking implementation details to the CSV (only user-facing summary fields).

### Key Entities

- MxEdge: { id, name, model, status }
- Interface/Port: { name, up (bool), speed (int), mac }
- Capture Payload: { type, duration, num_packets, max_pkt_len, format, mxedges: {<mxedge_id>: {interfaces: {<port_name>: {}}}}, tcpdump_expression?, tzsp_host?, tzsp_port? }
- Capture Result: { id, format, duration, expiry, pcap_url? }

## Success Criteria *(mandatory)*

### Measurable Outcomes

- SC-001: Operators can start a successful organization packet capture end-to-end in under 2 minutes (assuming API responsiveness), including subscription or download.
- SC-002: For 95% of successful capture starts, the tool displays a capture ID and either successfully subscribes to the stream or downloads the pcap within duration+120s.
- SC-003: Invalid user inputs are rejected with clear messages; automated tests cover all input validation branches at 100% assertion coverage.
- SC-004: Error conditions (API 4xx/5xx, missing fields, download failures) produce actionable messages and are covered by automated tests.

## Current Implementation Analysis (summary)

This section documents findings from the existing implementation in MistHelper.py (PacketCaptureManager.start_org_packet_capture and helpers).

1) Flow overview
   - Fetch org MxEdges via mistapi.api.v1.orgs.mxedges.listOrgMxEdges and expand with mistapi.get_all.
   - Fetch stats via mistapi.api.v1.orgs.stats.listOrgMxEdgesStats and map them by mxedge id.
   - Present a numbered list of MxEdges and prompt the user to select exactly one MxEdge (API limitation).
   - For selected MxEdge, fetch interface/port stats via mistapi.api.v1.orgs.stats.getOrgMxEdgeStats.
   - Prompt user to select a single port index and various capture parameters (duration, num_packets, max_pkt_len, format/tzsp fields).
   - Build payload and call _execute_org_capture which calls mistapi.api.v1.orgs.pcaps.startOrgPacketCapture.
   - On success, either call _wait_and_download_pcap_org or _subscribe_to_org_capture_stream depending on format and export info to CSV.

2) Error handling patterns
   - Most API calls are wrapped in try/except and on exception they print a user message and return early (graceful failure in interactive flow).
   - Response objects are assumed to have .status_code and .data attributes; when mistapi.get_all is used it's handled differently (list or dict).
   - Several branches perform `return` on validation or error, avoiding raises but potentially leaving partial state.

3) Notable code-level issues and inconsistencies
   - Inconsistent format naming:
     - start_org_packet_capture builds payload with "format" values: 'stream' (default) or 'tzsp' (when format_choice=="2").
     - _execute_org_capture defaults capture_format = payload.get("format","pcap") and checks for capture_format == 'pcap' to trigger pcap download; given the interactive options, 'pcap' is never set by the prompts, so the pcap branch may never be executed for org captures. This is confusing and could cause unreachable logic or misclassification of behavior.

   - Malformed print statement and stray brace:
     - The printed line for MxEdge listing includes a `\n}` stray brace in the formatted string across a line-break which looks accidental and may render incorrectly or indicate an editing error.

   - Assumptions about API response shapes:
     - The polling routine (_wait_and_download_pcap_org) handles both list and dict with 'results', but many places assume response.data exists and is iterable; inconsistent assumptions increase risk of unhandled cases.

   - CSV export API name choice:
     - _export_capture_info_to_csv selects api_function_name by comparing scope == 'site' else 'startOrgPacketCapture' — this is fine but make sure CSV does not include raw object graphs (sensitive fields) unexpectedly.

   - Download behavior and safety:
     - _wait_and_download_pcap_org uses requests.get(timeout=300) with no explicit SSL verification configuration or retry handling.
     - Files are saved to a relative "data" directory without allowing configuration; path creation uses Path('data').mkdir(exist_ok=True) which is acceptable but needs clear documentation.

   - Polling/bounds logic:
     - max_wait_time = duration + 120 and poll_interval=5; max_polls computed by integer division could be zero if duration is small and poll_interval > max_wait_time (unlikely with defaults but should be robust).

   - WebSocket subscription lifecycle:
     - The subscribe loops poll websocket_manager.command_results without clearing processed messages; in heavy usage this might grow memory but current design appears simplistic for interactive tools.

   - Input validation & UX:
     - Many prompts validate ranges and types and return early on invalid input. This is reasonable but could be improved to re-prompt instead of exiting.

## Test Coverage Gaps

- No unit tests found referencing start_org_packet_capture or the helper methods. (Search found no test files invoking this code.)
- Missing tests for:
  - API non-200 responses and the tool's user-facing messages for each API call (listOrgMxEdges, getOrgMxEdgeStats, startOrgPacketCapture, listOrgPacketCaptures).
  - Polling logic in _wait_and_download_pcap_org for different response shapes (list vs dict, pcap_url missing, delayed pcap_url availability).
  - TZSP flow and invalid tzsp host/port handling.
  - WebSocket subscription logic for org captures, including KeyboardInterrupt cancel behavior and subscription confirmation failures.
  - File download success/failure paths including partial downloads, large files, and write permission errors.

## Recommended Fixes (prioritized)

1. Fix unreachable/incorrect 'pcap' handling:
   - Decide authoritative values for payload["format"] (e.g., 'pcap'|'stream'|'tzsp') and make interactive choices map to those values consistently.
   - Update _execute_org_capture to use explicit checks for 'stream' / 'tzsp' / 'pcap' and document behavior. Add unit tests to verify each branch.

2. Correct formatting/printing bug:
   - Remove stray `}` and ensure f-strings are single-line or correctly escaped to avoid rendering errors.

3. Harden API response handling:
   - Normalize API helper responses via a thin adapter so functions can assume a consistent shape (e.g., always return list for capture listings and stats). Add guard clauses when response.data is None.

4. Improve polling logic and observability:
   - Ensure max_polls >= 1 and add a configurable poll_interval and max_wait override for testing.
   - Add clear logging on each poll and capture of telemetry (timestamps when pcap_url becomes available).

5. Make download resilient and explicit:
   - Add retries and smaller request timeouts for the download; validate Content-Length when present and report partial failures.
   - Allow configuring output directory and avoid using current working directory implicitly.

6. Add tests:
   - Unit tests for input validation, payload construction, _execute_org_capture branches (mocking mistapi and requests), polling loop with simulated delayed pcap_url, and WebSocket subscribe/unsubscribe behaviors.

## Acceptance Criteria (for code fixes)

- AC-001: Payload format values are consistent and documented; interactive options map to payload["format"] exactly as documented (tests assert mappings).
- AC-002: The MxEdge listing does not output stray characters (no stray `}`) and renders indexes and status correctly.
- AC-003: _wait_and_download_pcap_org handles list and dict capture listings without exceptions and returns early with a clear message when pcap_url not available after waiting.
- AC-004: Download uses timeouts and retries; on download failure the user is shown HTTP status and manual download URL when available.
- AC-005: WebSocket subscription for org captures correctly subscribes/monitors the org channel and exits cleanly on capture completion or user cancel; memory growth of command_results is bounded or messages are pruned.
- AC-006: Unit tests cover:
  - Payload construction for all formats (stream, tzsp, pcap if applicable)
  - start_org_packet_capture happy path (mocked APIs)
  - start_org_packet_capture error paths (API errors, invalid input)
  - _wait_and_download_pcap_org polling with delayed pcap_url and download success/failure
  - _subscribe_to_org_capture_stream handles subscription failure and cancellation

## Assumptions

- Mist API client (mistapi) follows a response object pattern with attributes .status_code and .data, but helper functions (mistapi.get_all) may return Python lists/dicts — code must bridge both patterns.
- Organization-level captures are single-MxEdge, single-port as noted in interactive messaging.
- The interactive UX can be modified to re-prompt in place of returning on invalid input if desired; this spec assumes conservative change (improve validation and test coverage) but not a UX redesign.

## Risks

- Downloading large PCAP files may exhaust disk or memory if not streamed to disk; current code writes content via requests.content which loads body into memory. This must be fixed for large captures.
- WebSocket message accumulation could increase memory use if not pruned.

## Next steps

1. Implement the prioritized fixes (format unification, printing bug, polling resilience, download robustness).
2. Add unit tests for each acceptance criteria item and integrate into CI.
3. Run manual QA with a test org to verify end-to-end behavior for stream, tzsp, and pcap (if pcap option is re-introduced).

---

**Spec Status**: Ready for planning (/speckit.plan) after fixes are implemented and unit tests added.


