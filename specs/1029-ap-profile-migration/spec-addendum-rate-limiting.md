# Feature Specification Addendum: Adaptive Rate Limiting for AP Profile Migration

**Feature Branch**: `1029-ap-profile-migration` (extends existing branch; no new branch is created)

**Parent Spec**: `specs/1029-ap-profile-migration/spec.md`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Wire the AP profile migration manager (menus 207 and 208) into the project's PID-based API rate limiter at `src/utils/rate_limiting.py` so bulk migrations of thousands of APs stay under Mist's 5000-request-per-clock-hour ceiling."

## Scope of This Addendum

This addendum extends the parent spec (`spec.md`) for feature `1029-ap-profile-migration`. It does not replace any existing requirement in `spec.md`. It adds behavior in one focused area: pacing the PUT calls that the migration and revert operations issue against the Mist API.

The parent spec covers the operator workflow, the backup file format, and the stop-on-failure semantics. This addendum covers only how the PUT calls are paced and how HTTP 429 responses are handled.

## Problem Statement

The migration operation added in the parent spec issues one Mist `PUT /sites/{site_id}/devices/{device_id}` per AP that must move. The current implementation in `src/device/ap_profile_migration_manager.py` (see `_reassign_one_ap`, `_run_reassignment_loop`, and the revert path in `_revert_one_ap` and its enclosing loop near line 1120) has no pacing between PUT calls. The only pacing today is a per-retry `time.sleep(0.5)` before an attempt and a `time.sleep(1.0)` after a failed attempt, both of which run only inside the retry branch, not between successful PUT calls.

Mist enforces a rate limit of 5000 requests per clock hour per API token. A bulk migration of 10,000 APs at full serial throughput can exceed this limit inside a single run and trigger 429 responses. Under the parent spec's stop-on-failure rule (FR-017), a 429 counted as a hard failure would halt a large migration mid-run, leaving the org in a mixed state and forcing the operator to revert or resume manually.

The project already has a PID-based adaptive rate limiter at `src/utils/rate_limiting.py` (`RateLimitingUtils.get_rate_limited_delay(smoothed, apisession, api_usage_cache)`), and it is already the throttle used by `src/api/api_data_fetcher.py._apply_rate_limiting`. This addendum wires the migration manager into that same limiter so that bulk migrations self-throttle instead of hitting 429s.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bulk migration of 10,000 APs completes without a 429-triggered halt (Priority: P1)

An operator retires a device profile that has 10,000 APs bound to it and picks the migration menu to move them all to a replacement profile. The tool paces each PUT so total request volume stays under the Mist 5000-per-clock-hour ceiling averaged across the run, and treats any 429 response as a throttle signal rather than a hard failure. The migration completes without hitting the parent spec's stop-on-failure halt for rate-limit reasons.

**Why this priority**: This is the reason the addendum exists. Without pacing, the parent feature is unsafe for its stated 10,000-AP use case: a single 429 mid-run halts the migration and leaves the org partially migrated. Pacing turns the parent feature from "safe up to a few hundred APs" into "safe at scale."

**Independent Test**: Run the migration operation against a mocked `mistapi` session that has 10,000 APs bound to a source profile and returns HTTP 200 for every PUT. Patch `time.sleep` so the test does not run in real time. Verify that (a) the number of `time.sleep` calls issued from the rate-limiter path equals the number of PUTs, and (b) the migration completes with 10,000 successes and 0 failures.

**Acceptance Scenarios**:

1. **Given** a mocked Mist session that returns HTTP 200 for every PUT and 10,000 APs bound to the source profile, **When** the migration runs, **Then** the tool calls `RateLimitingUtils.get_rate_limited_delay` once before every PUT (10,000 calls), sleeps for the returned delay each time, and reports 10,000 successes and 0 failures.
2. **Given** a mocked Mist session that returns HTTP 429 on every 100th PUT and HTTP 200 otherwise for 10,000 APs, **When** the migration runs, **Then** the 429 responses are fed to the rate limiter as an error signal, the limiter increases the next delay, no 429 counts as a stop-on-failure event, and the migration completes with 10,000 successful reassignments.
3. **Given** a mocked Mist session that returns HTTP 500 on the 42nd PUT, **When** the migration runs, **Then** the tool honors the parent spec's stop-on-failure rule (FR-017), halts before the 43rd PUT, records the 41 successful reassignments in the backup file, and prints the failing AP ID. HTTP 500 is not treated as a rate-limit signal.
4. **Given** a unit test that patches `time.sleep` to a no-op, **When** any migration or revert path is exercised, **Then** the test completes in negligible wall-clock time (no real sleep is performed by the code under test).

---

### User Story 2 - Revert of a large backup file paces its PUTs the same way (Priority: P1)

An operator reverts a migration whose backup lists 10,000 APs. The revert path (menu 208) applies the same pacing behavior as the migration path so a large-scale revert does not itself trigger 429 responses or a stop-on-failure halt.

**Why this priority**: The revert operation is the safety net for the migration operation. If revert cannot itself run at 10,000 APs safely, the parent spec's revert guarantee (SC-003 in the parent) is broken at scale. Pacing revert is not optional.

**Independent Test**: Run the revert operation against a mocked `mistapi` session pointed at a backup file that lists 10,000 APs. Patch `time.sleep`. Verify that (a) `get_rate_limited_delay` is called once before every PUT the revert issues and (b) the revert completes with 10,000 reassignments to the recorded source profile.

**Acceptance Scenarios**:

1. **Given** a backup file that lists 10,000 APs and a mocked Mist session that returns HTTP 200 for every PUT, **When** the revert runs, **Then** the rate limiter is consulted once per PUT (10,000 calls) and every AP is reassigned to the recorded source profile.
2. **Given** the same backup file and a mocked Mist session that returns HTTP 429 on every 100th PUT, **When** the revert runs, **Then** the 429 responses feed the limiter as an error signal, no 429 halts the revert, and all 10,000 APs are eventually reassigned.

---

### Edge Cases

- The rate limiter returns a delay of 0 seconds (cold-start, unloaded token): the tool still calls the limiter but issues no wall-clock sleep. Behavior is identical to today except that the limiter's internal smoothing state is initialized.
- The rate limiter raises an unexpected exception (for example a corrupt tuning-data file): the migration must not halt. It must log a warning, fall back to a conservative fixed delay, and continue. Rate-limit machinery is a helper, not a gate on the migration itself.
- A single AP receives a 429 on every retry inside the parent spec's bounded per-AP retry loop: the tool treats the AP as failed (per parent FR-017 semantics), stops the run, and records the partial-success list. A per-AP retry storm is a hard failure signal, not a limiter signal. The distinction is: 429s seen across different APs feed the limiter and are recovered from; 429s that exhaust one AP's retry budget count as that AP failing.
- A 429 response has no `Retry-After` header: the tool relies on the PID limiter's own back-pressure. It does not add a second sleep path on top of the limiter.
- A 429 response has a `Retry-After` header: v1 of this addendum ignores `Retry-After` and relies on the PID limiter only. Adding `Retry-After` honoring is a future enhancement (see Assumptions).
- `apisession` or the API usage cache is missing when the limiter is called (for example in a unit test that has not initialized the full `MistHelper` module state): the tool must degrade gracefully and use a fixed fallback delay rather than raising.
- A dry-run migration (parent spec User Story 3) does not issue any PUT. Therefore, the pacing path is not exercised in dry-run mode and the limiter is not consulted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-A01**: The migration operation MUST call the project's existing PID-based rate limiter (`RateLimitingUtils.get_rate_limited_delay(...)` in `src/utils/rate_limiting.py`) once before every PUT it issues against `PUT /sites/{site_id}/devices/{device_id}`, and MUST sleep for the returned delay. This applies to both the reassignment loop path (`_run_reassignment_loop` -> `_reassign_one_ap`) and to any retry attempt inside `_reassign_one_ap`.

- **FR-A02**: The revert operation MUST apply the same pacing rule as FR-A01 to every PUT it issues. This applies to `_revert_one_ap` and to its enclosing loop (the revert loop that begins near line 1120 of `src/device/ap_profile_migration_manager.py`).

- **FR-A03**: The migration and revert operations MUST feed HTTP 429 responses to the rate limiter as an error signal so subsequent delays adapt upward. This MUST use whatever error-signal path `RateLimitingUtils` already exposes; the addendum MUST NOT introduce a new limiter API surface.

- **FR-A04**: HTTP 429 MUST NOT count as a stop-on-failure event under the parent spec's FR-017. Only non-429 hard failures (any 4xx other than 429, all 5xx, timeouts, connection errors) MAY trigger the stop-on-failure halt.

- **FR-A05**: A 429 seen inside the parent spec's bounded per-AP retry loop MAY still result in that AP being counted as failed if all retries for that specific AP are exhausted. In that case the parent spec's FR-017 applies unchanged (stop the run, record partial success, name the failing AP). The rate-limit signaling in FR-A03 happens on every 429 regardless.

- **FR-A06**: The pacing call MUST be resilient to a limiter exception. If `RateLimitingUtils.get_rate_limited_delay` raises, the tool MUST log a warning, fall back to a fixed conservative delay (chosen during planning; see Assumptions), and continue the run. The migration MUST NOT halt on a limiter fault.

- **FR-A07**: All unit tests covering the pacing behavior MUST patch `time.sleep` so no test runs in wall-clock time. The pacing code MUST call `time.sleep(...)` by module-level reference (not by capturing the function in a local) so that `unittest.mock.patch("time.sleep", ...)` intercepts it. This matches the existing pattern noted in the parent codebase (`ap_profile_migration_manager.py` line 742 docstring: "observe timing by patching `time.sleep` at the module level").

- **FR-A08**: The pacing call MUST NOT be issued in dry-run mode (parent spec User Story 3), because dry-run issues no PUT calls.

- **FR-A09**: Structured telemetry emitted for the migration and revert operations MUST include, per invocation summary: total PUTs issued, total 429 responses observed, total non-429 failures observed, and the mean and max delay values returned by the rate limiter during the run. This extends (does not replace) the summary described in parent FR-018 and FR-024. Telemetry MUST continue to use the existing `TelemetryEmitter` pattern per parent Assumptions.

- **FR-A10**: The pacing behavior MUST NOT introduce a new third-party dependency, MUST NOT introduce a new HTTP client, and MUST NOT introduce a new configuration file. It uses the already-installed `RateLimitingUtils` and its existing tuning-data storage.

- **FR-A11**: All new or modified operator-visible strings introduced by this addendum (progress lines that mention throttling, summary lines that report delay statistics, warning lines that report 429s, fallback-delay warning lines) MUST follow the Simplified Technical English writing guide at `documentation/ASD-STE100_writing-guide.md`.

- **FR-A12**: All new or modified functions, methods, and modules MUST carry a docstring per the DOCS.md rules (summary + Why + Args/Returns/Raises), and docstring coverage for changed files MUST stay at or above 90 percent.

### Key Entities

- **PID rate limiter (`RateLimitingUtils`)**: The existing `src/utils/rate_limiting.py` static-method facade. This addendum consumes it; it does not modify it. The limiter returns an adaptive delay in seconds based on smoothed history and the `apisession`'s known usage cache.
- **429 response**: A Mist HTTP response with `status_code == 429`, signaling that the token has approached or exceeded its clock-hour request budget. Under this addendum a 429 is a signal to the limiter, not a hard failure.
- **Fallback delay**: A fixed, conservative sleep value used only if the limiter raises. This is a safety net so a limiter fault cannot halt a large migration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-A01**: A synthetic 10,000-AP migration run against a mocked `mistapi` session that returns HTTP 200 for every PUT completes with 10,000 successful reassignments, calls the rate limiter exactly 10,000 times, and issues no wall-clock sleep during the test (because `time.sleep` is patched).

- **SC-A02**: A synthetic 10,000-AP migration run against a mocked session that returns HTTP 429 on every 100th PUT (100 total 429 responses) completes with 10,000 successful reassignments, feeds every 429 to the limiter as an error signal, and never triggers the parent spec's stop-on-failure halt.

- **SC-A03**: A synthetic 10,000-AP revert run against a mocked session that returns HTTP 429 on every 100th PUT completes with 10,000 successful reassignments and never triggers a stop-on-failure halt.

- **SC-A04**: A synthetic migration run where the 42nd PUT returns HTTP 500 halts before the 43rd PUT, records exactly 41 successful reassignments in the backup file, prints the failing AP ID, and returns the non-zero exit path described in parent FR-017. HTTP 500 is not routed through the limiter as a throttle signal.

- **SC-A05**: A unit test that raises an exception from `RateLimitingUtils.get_rate_limited_delay` on the 5th call verifies that the migration logs a warning, applies the fallback delay, and continues without halting. The run reports the same success count it would have reported without the fault.

- **SC-A06**: The full existing MistHelper test suite (`cd src; pytest`) passes. `ruff check .` reports zero violations. Docstring coverage for `src/device/ap_profile_migration_manager.py` remains at or above 90 percent per the DOCS.md rule.

- **SC-A07**: The migration and revert summary output reports the pacing statistics required by FR-A09 (PUTs issued, 429 count, non-429 failure count, mean delay, max delay).

- **SC-A08**: No new third-party dependency is added to `pyproject.toml` by this addendum. No new module is added under `src/utils/` for rate-limit handling; the existing `src/utils/rate_limiting.py` is the only limiter the migration and revert paths consult.

## Assumptions

- Menu numbers 207 (migrate) and 208 (revert) are those already assigned by the parent spec. This addendum does not add a menu entry, does not change the `operation_registry.py` entries, and does not add a new interactive prompt.
- The fixed fallback delay used in FR-A06 is a small conservative value (planning phase to pick; a value in the 0.5 to 1.0 second range matches the existing per-retry backoff constants already present in `_reassign_one_ap`). Choice of exact value is an implementation detail for the planning phase.
- The addendum does not honor the `Retry-After` HTTP header on 429 responses in v1. The PID limiter's own back-pressure is treated as sufficient. Adding `Retry-After` honoring is a candidate for a follow-up addendum if operational experience shows the PID convergence is too slow at 10,000-AP scale.
- The addendum does not add parallel or concurrent PUTs. The parent operation stays strictly serial. Pacing is a per-PUT sleep, not a concurrency change.
- The addendum does not add a batch endpoint. Mist does not expose a batch update for `deviceprofile_id`; this remains one PUT per AP.
- The addendum does not add a resume-from-partial feature to the migration operation. If a migration halts on a non-429 failure, the parent spec's revert operation (menu 208, reading the partial-success backup) remains the recovery path.
- Tests reuse the parent codebase's existing pattern for patching `time.sleep` at the module level (see the parent `_reassign_one_ap` docstring at line 742). No new test helper is required.
- `apisession` and the API usage cache are available on the module `MistHelper` in the same way `api_data_fetcher.py._apply_rate_limiting` accesses them today. The addendum does not require a new plumbing route to the limiter's inputs.
- The pacing addendum does not require a change to the backup file format defined in parent FR-013. The pacing statistics from FR-A09 live in the summary text and in the JSONL telemetry, not in the backup JSON file. This keeps parent SC-003 (backup is sufficient input for revert) unchanged.
