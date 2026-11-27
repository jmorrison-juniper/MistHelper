# Feature Specification: Firmware Monitor Treats Failed Stats Pages as Failed Checks

**Feature Branch**: `fix/4710-firmware-monitor-failed-pages`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue #4710, "Firmware monitor reports completion after failed status pages". The issue is open. Its labels are `bug`, `tests`, `in-progress`, and `needs-human-review`.

**Baseline**: `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, verified through the GitHub API. See `design/research.md`.

**Terms**: The monitor is the continuous monitoring mode. Menu 137 starts it with scope 5. A stats page is one response from a stats endpoint. A walk is the set of stats page requests for one status check. A status check is one pass of `_execute_monitoring_check`.

## Clarifications

### Session 2026-11-26

- Q: Must a failed later stats page enter the existing retry path? A: Yes. A failed page never counts as an empty result. It enters the existing failure path. Source: issue body, "Expected" paragraph, and the comment dated 2026-11-09T15:15:42Z.
- Q: Does a missing or non-integer HTTP status count as success? A: No. A missing or invalid status is a failed page. Source: the comment dated 2026-11-09T14:59:15Z.
- Q: Must a successful response with no active upgrades still complete? A: Yes. When every page passes and no active upgrade exists, the monitor completes. Source: issue body, "Expected" paragraph.
- Q: Does this change edit the shared status helper? A: No. The helper keeps its current default. Issue #2753 owns the audit of masked defaults. Decision D-2.
- Q: Does issue #4709 block this work? A: The issue asks for coordination before file reservation. This change adds no shared code. The orchestrator confirms the file reservation before the pull request opens. Analysis item A-03.
- Q: Does the human review gate remain? A: Yes. The `needs-human-review` label stays. Merge waits for human review. Decision D-8.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A failed first stats page does not report completion (Priority: P1)

An operator starts the monitor from menu 137 with scope 5. The first stats page returns HTTP 403 or HTTP 503. The monitor must not print the completion banner.

**Why this priority**: Warning: a false completion message can make an operator believe that an unmonitored upgrade finished. This is the core defect in the issue.

**Independent Test**: Run the offline tests that mock an HTTP 403 first page and an HTTP 503 first page. The test passes when each status check returns no count and prints no completion banner.

**Acceptance Scenarios**:

1. **Given** the first stats page returns HTTP 403 with a JSON error body, **When** one status check runs, **Then** the check returns no count.
2. **Given** the first page returns HTTP 503 with an empty body, **When** one status check runs, **Then** it returns no count.

---

### User Story 2 - A failed later stats page does not report completion (Priority: P1)

The first stats page returns HTTP 200 with one device row that is not upgrading. The page sets a next link. The second page returns HTTP 503 with an empty body.

**Why this priority**: A successful first page does not prove that the whole walk succeeded. See the comment dated 2026-11-09T15:15:42Z.

**Independent Test**: Mock two stats pages with a next link between them. The test passes when the status check returns no count.

**Acceptance Scenarios**:

1. **Given** page one passes with a next link, **When** page two is HTTP 503 with an empty body, **Then** the check returns no count.
2. **Given** the same two pages on the site branch, **When** page two fails, **Then** the status check returns no count.

---

### User Story 3 - A persistent failure ends with the failure exit code (Priority: P2)

Every stats request fails with HTTP 403. The retry policy from issue #1910 already bounds the retries. This story makes the failure reach that bound.

**Why this priority**: A silent failure leaves the operator without a clear stop. The existing bound must receive the failure.

**Independent Test**: Run the monitoring loop with a mocked SDK that always returns HTTP 403. The test passes when the loop returns `MONITOR_EXIT_FAILED` (1) after five checks, with recorded waits of 7, 14, 28, and 56 seconds.

**Acceptance Scenarios**:

1. **Given** every status check returns HTTP 403, **When** the loop runs, **Then** it returns `MONITOR_EXIT_FAILED` after the fifth failed check.
2. **Given** the same run, **When** the loop waits between checks, **Then** the waits are 7, 14, 28, and 56 seconds.

---

### User Story 4 - A genuine empty success still completes (Priority: P2)

Every stats page returns HTTP 200 with a JSON array. The array can be empty. The monitor completes normally.

**Why this priority**: The fix must keep the normal end of an upgrade. Operators depend on that completion message.

**Independent Test**: Mock one HTTP 200 page with an empty array. The test passes when the loop returns `MONITOR_EXIT_COMPLETE` (0) after one check and prints the completion banner.

**Acceptance Scenarios**:

1. **Given** one HTTP 200 page with an empty array, **When** the loop runs, **Then** it returns `MONITOR_EXIT_COMPLETE` on the first check.
2. **Given** two HTTP 200 pages with no active upgrade, **When** the loop runs, **Then** the walk reads both pages before it completes.

---

### Edge Cases

- The HTTP status attribute is missing. The page fails (FR-002).
- The body is a JSON object, not an array. The page fails (FR-003).
- The body on HTTP 200 is not JSON. The body is not a list, so the page fails (FR-003).
- The `X-Page-Total` header is not an integer. The walk fails (FR-006).
- The `X-Page-Total` header announces more rows than the walk collected. The walk fails, even when no next link exists (FR-006).
- A next link repeats. The walk fails (FR-007).
- The operator presses Ctrl+C during a retry wait. Caution: Ctrl+C stops the monitor only. The firmware upgrade keeps running. The existing cancel path returns `MONITOR_EXIT_CANCELLED` (2) (FR-011).
- A failed check is followed by a good check. The retry streak resets through the existing policy (FR-011).
- The error body contains text. The text is not printed or logged. Only the status code appears (FR-010).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The monitor MUST request stats pages only through mistapi methods. It uses `listOrgDevicesStats` or `listSiteDevicesStats` for the first page. It uses `mistapi.get_next` for each later page.
- **FR-002**: A stats page MUST fail when its HTTP status is missing, not an integer, or not 200.
- **FR-003**: A stats page MUST fail when its body is not a list.
- **FR-004**: A failed stats page MUST make the status check return no count. The existing failure path then handles it.
- **FR-005**: The monitor MUST NOT return completion or print the completion banner unless every requested page passes.
- **FR-006**: The walk MUST fail when the last page announces more rows than the walk collected. A non-integer `X-Page-Total` MUST also fail the walk.
- **FR-007**: The walk MUST fail when a next link repeats.
- **FR-008**: A complete walk with zero active upgrades MUST return `MONITOR_EXIT_COMPLETE` (0).
- **FR-009**: A persistent failure MUST return `MONITOR_EXIT_FAILED` (1) after the fifth failed check. The waits MUST be 7, 14, 28, and 56 seconds.
- **FR-010**: A failure message MUST name the HTTP status only. It MUST NOT print or log the response body.
- **FR-011**: The exit codes, the refresh cadence, the backoff constants, and the helper `_response_status_code` MUST keep their current behavior.
- **FR-012**: Each stats page request MUST write an `info` log line before the request. It MUST write a `debug` log line after the page result.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- **Mistapi methods**: `mistapi.api.v1.orgs.stats.listOrgDevicesStats` (org branch, first page), `mistapi.api.v1.sites.stats.listSiteDevicesStats` (site branch, first page), and `mistapi.get_next` (later pages). The change adds no direct HTTP request.
- **SDK insufficiency**: `mistapi.get_all` returns collected rows and never checks a page status. See installed SDK `__pagination.py` lines 39 and 56 to 74. Test N14 shows that an HTTP 403 first page becomes an empty list.
- **SDK authentication and endpoint parity**: The calls pass the same session object, the same endpoint functions, and the same query arguments as the current code. Updated tests verify the arguments.
- **Failure safety**: A failed page raises. The walk returns no partial rows.
- **Secret redaction**: The failure text holds the HTTP status only. Test N12 proves that the response body text is absent from output and logs.

Test identifiers N1 to N14 and U1 to U2 are defined in `tasks.md`.

### Key Entities

- **Monitor**: The continuous monitoring mode. Menu 137 starts it with scope 5. It runs status checks until completion, failure, or Ctrl+C.
- **Stats page**: One response from a stats endpoint. It holds an HTTP status, a JSON body, headers, and an optional next link.
- **Device row**: One element of a stats page body. Its natural key is the `mac` field of the `stats_device` schema.
- **Active upgrade**: A device row whose firmware update state is active under `_is_active_fw_update` (`firmware_manager.py` line 649).
- **Status check**: One pass of `_execute_monitoring_check`. It returns the active upgrade count, or no count when it fails.
- **Retry streak**: The consecutive failed status checks held by `MonitoringRetryPolicy` (`firmware_manager.py` line 144).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tests N1 to N8, N11, N12, and N13 fail before the change and pass after it. Tests N9, N10, and N14 pass before and after the change.
- **SC-002**: A persistent HTTP 403 run returns `MONITOR_EXIT_FAILED` after five checks, with waits of 7, 14, 28, and 56 seconds.
- **SC-003**: An HTTP 200 page with an empty array still returns `MONITOR_EXIT_COMPLETE` after one check.
- **SC-004**: The change adds no module-level name, class, or method. The `symbol-diff` gate prints `no module-level name changed`.
- **SC-005**: Each applicable row of the local gates table passes. The pull request names each row that does not run and gives the reason.
- **SC-006**: Remote CI passes before any auto-merge decision. The `needs-human-review` label stays until a human review completes.

## Assumptions

- The pinned SDK is `mistapi` 0.64.1, installed under `.venv\Lib\site-packages\mistapi`. The pyproject range is `>=0.64.1,<0.65`.
- The `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` headers come from the SDK. The OpenAPI file does not document them.
- The org call passes `fields="*"`. The site call passes no `fields` argument. The site field set is unverified (research item U-01).
- Live Mist calls are out of scope. The brief forbids them. The synthetic tests use the same response shapes as the SDK.
- Menu 137 has category `interactive`, so the automated sweeps do not run it (`operation_registry.py` line 112).

## Out of Scope

- The mistapi pins in `pyproject.toml`, `requirements.txt`, and `.github/copilot-instructions.md` (follow-up F-04).
- The default in `_response_status_code` and other masked defaults (issue #2753).
- The other-device events exporter (issue #4709) and the other `mistapi.get_all` call sites in `firmware_manager.py` at lines 3505, 3526, 4055, 4108, and 4164 (follow-up F-02).
- The site branch field set (follow-up F-03).
- Moving the paging code into a compliant nested package (remediation R-01).
- Any change to menu 137, the scope prompt, or the confirmation rules.
