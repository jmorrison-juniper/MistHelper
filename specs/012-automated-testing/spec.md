# Feature Specification: Automated Testing Infrastructure

**Feature Branch**: `012-automated-testing`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Add automated testing infrastructure for MistHelper with CI/CD pipeline integration, AI-readable telemetry hooks, and zero-intervention test execution"

## Clarifications

### Session 2026-03-11

- Q: Are progress events always emitted or opt-in via flag? → A: Always-on — progress events are emitted during every operation by default (best-effort, FR-008 protects against side effects).
- Q: Single shared telemetry file or separate files for test events vs progress events? → A: Two files — test events (from `--test`/`--testinteractive` runs) are written to timestamped files (`data/test_events_YYYYMMDD_HHMMSS.jsonl`), while progress events (from live operations) are written to a rolling file (`data/test_events.jsonl`). Both use the same NDJSON format, distinguished by the `event_type` field. *(Clarification updated during planning to reflect the final design.)*
- Q: What is the testing scope — offline-only or live end-to-end? → A: Both. Offline unit tests for utility functions (fast, no API). Live end-to-end tests for ALL non-destructive menu operations using real .env files, real orgs, and real API tokens. Destructive operations (changes, deletes, firmware, reboots) get telemetry hooks but are NOT automated. All test execution must be non-interactive (zero user intervention).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Structured Test Event Output for AI Consumption (Priority: P1)

An AI agent (GitHub Copilot, CI bot, or local coding assistant) needs to programmatically understand what happened during a MistHelper test run without parsing human-readable prose from `script.log`. Today, the only output is unstructured log lines prefixed with `SYSTEMATIC_TEST:` — an AI must regex-parse free-form text to determine pass/fail status, timing, error details, and which menu options were tested.

The system emits structured JSON events (one per line, NDJSON format) to a dedicated telemetry file (`data/test_events.jsonl`) during `--test` and `--testinteractive` runs. Each event contains a consistent schema: event type, timestamp, menu option, status (pass/fail/skip), duration, error message (if any), and context metadata. This file is machine-readable without any parsing heuristics. All non-destructive menu operations are tested end-to-end with real API credentials. Destructive operations (firmware upgrades, reboots, VC conversions, config changes, deletes) have telemetry hooks but are not automated — they emit skip events with a documented reason.

**Why this priority**: Without structured output, no downstream automation is possible. Every other user story depends on having machine-readable test results. This is the foundation.

**Independent Test**: Run `python MistHelper.py --test --skip-deps` (with valid credentials), then read `data/test_events.jsonl` and confirm every line is valid JSON with the documented schema fields. No human interpretation required.

**Acceptance Scenarios**:

1. **Given** a completed `--test` run, **When** an AI reads `data/test_events.jsonl`, **Then** every line parses as valid JSON containing at minimum: `event_type`, `timestamp`, `menu_option`, `status`, `duration_seconds`.
2. **Given** a menu option that fails during testing, **When** the failure event is emitted, **Then** the JSON event includes `status: "fail"`, `error_type` (exception class name), and `error_message` (first 500 characters of the exception).
3. **Given** a menu option that is skipped, **When** the skip event is emitted, **Then** the JSON event includes `status: "skip"` and `skip_reason` explaining why.
4. **Given** the test run completes, **When** a summary event is emitted, **Then** it includes `event_type: "test_summary"`, total count, pass count, fail count, skip count, and total elapsed time.

---

### User Story 2 - Offline Unit Test Suite for Core Utilities (Priority: P1)

A developer or AI agent needs to verify that core MistHelper utility functions work correctly without any API credentials, network access, or Mist org. Today, the only testing path (`--test`) requires a live API connection and takes 30+ minutes to complete a full run. Pure logic functions like `check_stop_signal()`, `flatten_dict()`, `escape_multiline()`, and primary key strategy lookups have no isolated tests.

A standalone test suite (runnable via `python -m pytest tests/` or `python scripts/run_unit_tests.py`) exercises these utility functions with zero external dependencies. Tests run in under 30 seconds and produce a standard exit code (0 = all pass, 1 = failures). This complements the live end-to-end test mode (`--test`), which exercises all non-destructive menu operations against a real Mist org with real API credentials.

**Why this priority**: Fast feedback loops are essential for CI/CD. Live API tests are slow and fragile (rate limits, network issues, credential rotation). Unit tests catch regressions in minutes instead of hours.

**Independent Test**: Run the unit test suite from a clean checkout with no `.env` file. All tests pass. No network calls are made.

**Acceptance Scenarios**:

1. **Given** a developer runs `python -m pytest tests/unit/` from the project root with no `.env` file, **When** the suite completes, **Then** all tests pass and no network connections are attempted.
2. **Given** the `ConfigUtils.check_stop_signal()` function, **When** tested with file-present and file-absent scenarios, **Then** it correctly returns True/False and cleans up the signal file.
3. **Given** the `DataProcessingUtils.flatten_dict()` function, **When** tested with nested dictionaries, lists, and edge cases (empty dict, None values, deeply nested), **Then** it produces the expected flat key-value pairs.
4. **Given** the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary, **When** every entry is validated, **Then** each has a valid `type` field (one of `natural_pk`, `composite_pk`, `auto_increment_with_unique`) and a non-empty `primary_key` list.

---

### User Story 3 - CI Pipeline Integration with GitHub Actions (Priority: P2)

Today the CI pipeline (`container-build.yml`) only validates Python syntax (`py_compile` + `ast.parse`). It catches syntax errors but not runtime regressions — a broken function signature, a missing import, or a logic error in a utility function all pass CI and only surface when a human runs `--test` manually.

The CI pipeline runs the offline unit test suite (US2) on every push to `main` and on every pull request. Test results are reported as GitHub Actions annotations. The container build only proceeds if all unit tests pass.

**Why this priority**: CI integration gates deployments on test results, preventing regressions from reaching the container. Depends on US2 (unit tests must exist before CI can run them).

**Independent Test**: Open a pull request with a deliberate test failure (e.g., break a utility function). Observe that the CI pipeline fails and the container build is skipped.

**Acceptance Scenarios**:

1. **Given** a push to `main` or a pull request, **When** the GitHub Actions workflow runs, **Then** the unit test suite executes before the container build job.
2. **Given** a unit test failure, **When** the test job reports failure, **Then** the container build job is skipped (not started).
3. **Given** all unit tests pass, **When** the test job succeeds, **Then** the container build proceeds as it does today.

---

### User Story 4 - AI-Readable Progress Hooks During Live Operations (Priority: P2)

When an AI agent monitors a running MistHelper operation (via `script.log` or a separate telemetry channel), it cannot programmatically determine: how far along the operation is, how many items remain, which site is being processed, or whether the rate limiter is throttling. The agent must pattern-match human-readable tqdm output or grep through prose log messages.

Long-running operations always emit structured progress events to the telemetry file at key checkpoints: operation start (with total count), each iteration completion (with item identifier and running count), rate limit events, and operation completion. Progress events are always-on by default — no flag or opt-in is required. These events use the same NDJSON format as US1.

**Why this priority**: Enables AI agents to provide real-time status updates, detect stalls, and make intelligent decisions (like triggering the stop signal) without screen-scraping. Depends on US1 (telemetry format must be established first).

**Independent Test**: Run Menu 11 (device inventory — typically fast), then read `data/test_events.jsonl` and confirm progress events show start/iteration/complete lifecycle with site counts.

**Acceptance Scenarios**:

1. **Given** a site-iteration operation begins, **When** the operation starts, **Then** a `progress_start` event is emitted with `total_items` count, `operation_name`, and `menu_option`.
2. **Given** each site iteration completes, **When** the next iteration begins, **Then** a `progress_tick` event is emitted with `current_item` (site name or ID), `items_completed`, and `items_remaining`.
3. **Given** an operation completes or is stopped via stop signal, **When** the final event is emitted, **Then** a `progress_complete` event includes `items_processed`, `items_total`, `was_stopped` (boolean), and `duration_seconds`.

---

### User Story 5 - Test Result Comparison Across Runs (Priority: P3)

A developer or AI agent wants to detect regressions by comparing test results across multiple runs. Today there is no historical record — each `--test` run overwrites `script.log` and there is no structured way to compare "did Menu 11 get slower?" or "did Menu 42 start failing?"

Test event files are named with timestamps (`data/test_events_YYYYMMDD_HHMMSS.jsonl`) so multiple runs accumulate. A comparison utility reads two test event files and reports: new failures, resolved failures, significant timing changes (greater than 2x slower), and menu options that changed status.

**Why this priority**: Regression detection is valuable but requires US1 and US2 to be in place first. Lower priority because manual inspection of a single run already catches most issues.

**Independent Test**: Run the test suite twice, introduce a deliberate slow-down in a utility function between runs, then run the comparison utility and confirm it flags the timing regression.

**Acceptance Scenarios**:

1. **Given** two test event files from different runs, **When** the comparison utility processes them, **Then** it produces a summary listing: new failures, resolved failures, and timing changes exceeding 2x.
2. **Given** a menu option that passed in run A but fails in run B, **When** the comparison runs, **Then** it appears in the "new failures" section with both error details.
3. **Given** identical results across two runs, **When** the comparison runs, **Then** it reports "no regressions detected."

---

### Edge Cases

- What happens when `data/test_events.jsonl` cannot be written (permissions, disk full)?  
  The test run continues normally — telemetry is best-effort. A warning is logged to `script.log` and the test outcome is not affected.
- What happens when a unit test imports MistHelper.py and triggers top-level initialization (API session, dependency checks)?  
  Unit tests must be isolated from top-level side effects. The test framework imports only the specific classes/functions under test, not the entire module.
- What happens when the CI runner has no Mist API credentials?  
  Only offline unit tests run in CI. Live API tests (`--test`) are explicitly excluded from CI workflows.
- What happens when test event JSONL files accumulate and consume disk space?  
  A configurable retention policy (default: keep last 10 files) deletes oldest files when the limit is exceeded.
- What happens when a non-destructive menu operation is added to MistHelper?  
  It should be added to the automated test list by default. New operations are assumed safe to test unless explicitly categorized as destructive.
- What happens when `--test` encounters a menu operation that requires interactive input (e.g., site selection)?  
  All test execution must be non-interactive. The test harness auto-selects required inputs (first available site, default parameters) without user intervention.
- What happens when a destructive operation (e.g., firmware upgrade) is executed during `--test`?  
  Destructive operations are never executed during automated testing. They emit a skip event with `skip_reason: "destructive_operation"` and move to the next operation. Telemetry hooks are present in the destructive code paths for when a human runs them manually.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST emit structured NDJSON events with one JSON object per line, distinguished by the `event_type` field. Test events (from `--test`/`--testinteractive` runs) MUST be written to timestamped files (`data/test_events_YYYYMMDD_HHMMSS.jsonl`). Progress events (from live operations) MUST be written to a rolling file (`data/test_events.jsonl`).
- **FR-002**: Each test event MUST contain at minimum: `event_type`, `timestamp` (ISO 8601), `menu_option`, `status`, and `duration_seconds`.
- **FR-003**: System MUST provide an offline unit test suite runnable via `python -m pytest tests/unit/` that requires no API credentials or network access.
- **FR-004**: Unit tests MUST cover at minimum: `ConfigUtils.check_stop_signal()`, `DataProcessingUtils.flatten_dict()`, `DataProcessingUtils.escape_multiline()`, `DataProcessingUtils.get_unique_keys()`, and `ENDPOINT_PRIMARY_KEY_STRATEGIES` validation.
- **FR-005**: The GitHub Actions workflow MUST run the offline unit test suite before the container build job, with the build gated on test success.
- **FR-006**: Long-running site/device iteration operations MUST always emit `progress_start`, `progress_tick`, and `progress_complete` events to the telemetry file during every operation (no opt-in flag required).
- **FR-007**: Progress events MUST include operation context: `operation_name`, `menu_option`, `total_items`, `current_item`, `items_completed`.
- **FR-008**: Telemetry emission MUST be best-effort — failures to write telemetry MUST NOT affect the operation's primary function or output.
- **FR-009**: Unit tests MUST complete in under 30 seconds on a standard developer machine.
- **FR-010**: The test event file MUST support timestamped naming (`test_events_YYYYMMDD_HHMMSS.jsonl`) with a configurable retention limit.
- **FR-011**: The `--test` mode MUST execute ALL non-destructive menu operations end-to-end using real API credentials from `.env`, with zero user intervention required.
- **FR-012**: Destructive operations (firmware upgrades, reboots, VC conversions, config changes, deletes) MUST be excluded from automated test execution and MUST emit a skip event with a documented reason.
- **FR-013**: Destructive operations MUST still have telemetry hooks (progress events, test events) that activate when a human runs them manually.
- **FR-014**: All test execution (`--test`, `--testinteractive`) MUST be fully non-interactive — the test harness auto-selects required parameters (site, device, defaults) without prompting.

### Key Entities

- **TestEvent**: A single structured record of a test action — contains event type, timing, menu option, pass/fail status, and optional error context. Written to the single shared telemetry file (`data/test_events.jsonl`).
- **ProgressEvent**: A checkpoint record emitted during live operations — contains operation name, item counts, and timing for AI consumption. Written to the same shared telemetry file, distinguished from TestEvents by the `event_type` field.
- **TestComparison**: A derived analysis comparing two sets of TestEvents — identifies regressions, resolutions, and timing changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An AI agent can determine the pass/fail status of every tested menu option by reading a single file, with zero regex parsing or heuristic interpretation required.
- **SC-002**: A developer can validate core utility functions in under 30 seconds from a clean checkout with no external credentials.
- **SC-003**: Code changes that break a utility function are caught automatically before reaching the production container.
- **SC-004**: An AI agent monitoring a live operation can determine percentage completion and current item being processed at any point during execution.
- **SC-005**: Test regressions between any two runs can be identified programmatically without manual log comparison.

## Assumptions

- Python 3.13+ is available in both local development and CI environments.
- The `pytest` framework is acceptable for the offline unit test suite (already used in `mist-ops-platform`).
- NDJSON (newline-delimited JSON) is the preferred structured format — one JSON object per line, readable by `jq`, Python, and any JSON parser.
- Unit tests will be placed in a `tests/` directory at the project root (separate from `mist-ops-platform/tests/`).
- The existing `--test` and `--testinteractive` modes continue to function as-is; structured telemetry is additive, not a replacement.
- GitHub Actions runners have Python 3.13+ available via `actions/setup-python`.
- Live end-to-end tests require real `.env` files with valid Mist API tokens, real org IDs, and real site access. These are the only way to test actual API integration.
- The boundary between "non-destructive" and "destructive" operations is defined by the existing skip lists in the test runner (Menu 90-100 for destructive, plus any operation that creates, modifies, or deletes resources).

## Scope Boundaries

**In scope**:
- Structured telemetry output for test runs and live operations
- Offline unit tests for utility functions
- Live end-to-end testing of all non-destructive menu operations with real APIs
- Non-interactive test execution (zero user intervention)
- Telemetry hooks in destructive operations (used when humans run them manually)
- CI pipeline enhancement with test gating (offline tests only in CI)
- Test result comparison utility
- Progress hooks for site/device iteration loops

**Out of scope**:
- Automating destructive operations (firmware, reboots, VC conversions, config changes, deletes) in test mode
- Mocking the Mist API for integration-level tests (future feature)
- Web-based test dashboard or UI
- Performance benchmarking or load testing
- Running live API tests in CI (requires credentials not available in GitHub Actions)
