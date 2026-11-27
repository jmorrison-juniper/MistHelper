# Tasks: Per-port Mist Insights parity in the WAN dashboard

**Input**: Numeric record at `specs/numbered/0/0/1/1/4/3/1/0/4330-per-port-mist-insights-parity/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, and `design/contracts/`.

**Tests**: Required by the specification. The 25 planned tests appear in the Test Cases section. Each test uses mocked responses and synthetic records only.

**Organization**: Tasks are grouped by phase. Each user story has its own phase.

## Format

- **[P]**: The task can run in parallel. It touches different files and has no open dependency.
- **Requirements**: The `FR` identifiers that the task satisfies.
- **Status**: `open`, `verified-present`, `partial`, or `absent`. Each task starts as `absent`.
- **Verification**: One command from the local gates table in `.github/copilot-instructions.md`, unless the task names a remote check.

## Phase 1: Contract and Helpers

### T001 [P] Add the SDK contract tests

- **Requirements**: FR-001, FR-002, FR-003, FR-007, FR-012
- **Files**: modify `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py`
- **Tests**: TC-01, TC-02, TC-03, TC-04, TC-05, TC-06
- **Acceptance**: Each test fails before T005. Each test passes after T005. The file pins the installed SDK version and the method signature.
- **Verification**: `python -m pytest tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py`
- **Status**: absent

### T003 [P] Add the pure port series helpers

- **Requirements**: FR-002, FR-003, FR-005, FR-008, FR-009, FR-011, FR-012
- **Files**: add `src/interfaces/portals/wan_dashboard/services/port_insights.py`
- **Acceptance**: The module holds classes only. Each function has 25 lines or fewer. Each line has an inline comment. Each action has an info line before it and a debug line after it.
- **Verification**: `python -m mypy src/interfaces/portals/wan_dashboard --config-file pyproject.toml`
- **Status**: absent

### T004 Add unit tests for the helpers and the budget

- **Requirements**: FR-002, FR-003, FR-005, FR-008, FR-009, FR-011, FR-012
- **Files**: add `tests/unit/wan_dashboard/test_port_insights.py`
- **Depends on**: T003
- **Tests**: TC-07, TC-08, TC-09, TC-12, TC-24
- **Acceptance**: Each test fails before T003 is complete. The totals match the floor of the sum divided by 8.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/test_port_insights.py`
- **Status**: absent

## Phase 2: Shared Admission

### T002 Add the organization scope for site-scoped requests

- **Requirements**: FR-006, FR-017
- **Files**: modify `src/interfaces/wan_performance/collection/request_admission.py` and `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`
- **Depends on**: D-12. Pull request #4208 and the owner's local change are resolved first.
- **Tests**: TC-13, TC-14
- **Acceptance**: `organization_scope` sets the tenant for site reads inside its block. A site read without a tenant still fails closed. The scope resets on every exit path.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`
- **Status**: absent. This task is blocked until D-12 closes.

## Phase 3: Service and Worker

### T005 Add the refresh method for a port series

- **Requirements**: FR-001, FR-004, FR-006, FR-007, FR-010, FR-011
- **Files**: modify `src/interfaces/portals/wan_dashboard/services/__init__.py` and `tests/integration/web_portal/wan_dashboard/test_services.py`
- **Depends on**: T002, T003
- **Tests**: TC-15, TC-16, TC-22
- **Acceptance**: The method calls `_request` once for each port. It wraps the call in `organization_scope`. It writes nine range keys through `_remember_result`. It creates no second cache writer.
- **Verification**: `python -m pytest tests/integration/web_portal/wan_dashboard/test_services.py`
- **Status**: absent

### T006 Add the port series phase, the request cap, and the cursor

- **Requirements**: FR-004, FR-005
- **Files**: modify `src/interfaces/portals/wan_dashboard/services/worker.py` and `tests/unit/wan_dashboard/test_worker.py`
- **Depends on**: T005
- **Tests**: TC-10, TC-11, TC-17
- **Acceptance**: An unset or zero cap makes no call. A cap of N makes N calls. The cursor moves by N. A lost lease stops the phase before its next request.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/test_worker.py`
- **Status**: absent

### T007 [P] Document the request cap in the environment example

- **Requirements**: FR-005
- **Files**: modify `deploy/.env.example`
- **Acceptance**: The file lists `WAN_PORT_INSIGHT_REQUEST_CAP` with an empty value. The comment states that an empty value disables the phase.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/test_worker.py`
- **Status**: absent

## Phase 4: Port View

### T008 Update the copy and the port view states

- **Requirements**: FR-010, FR-013, FR-014
- **Files**: modify `src/interfaces/portals/wan_dashboard/templates/wan_dashboard/dashboard.html` and `src/interfaces/portals/wan_dashboard/static/dashboard.js`
- **Depends on**: T005
- **Acceptance**: The overview copy states cumulative counters since the last device reboot. The port view shows the four data states and the UTC collection time. The new elements use `data-testid` values `wan-port-series-state`, `wan-port-series-collected`, `wan-port-series-coverage`, and `wan-port-derived-totals`. The refresh controls keep their current identifiers.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_wan_dashboard_cache_only.py`
- **Status**: absent

### T009 Add the browser tests for the port view

- **Requirements**: FR-010, FR-013, FR-014
- **Files**: modify `tests/e2e/web_portal/test_wan_dashboard_cache_only.py`
- **Depends on**: T008
- **Tests**: TC-18, TC-19, TC-20, TC-21, TC-23
- **Acceptance**: The browser tests use mocked responses only. The existing refresh test still passes.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_wan_dashboard_cache_only.py`
- **Status**: absent

## Phase 5: Documentation and Release Note

### T010 Document the cap, the budget, and the states

- **Requirements**: FR-005, FR-010, FR-013
- **Files**: modify `documentation/operator-guide.md`
- **Depends on**: T006, T008
- **Acceptance**: The section gives the budget formula, the cap rule, and the four data states. Each sentence has 20 words or fewer for each instruction.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`
- **Status**: absent

### T011 [P] Add the release-note fragment

- **Requirements**: All
- **Files**: add `changelog.d/issue-4330-per-port-mist-insights-parity.md`
- **Acceptance**: The fragment has one `###` heading. It has one bullet for each change type. The bullet names issue 4330.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4330-per-port-mist-insights-parity.md`
- **Status**: absent

## Phase 6: Final Gates and Release

### T-LOCAL-GATES Run every local gate that applies

- **Requirements**: All
- **Depends on**: T001 to T011
- **Scope**: Compile, lint, format, types, tests for each changed file, complexity, security lint, dead code, docstrings, symbols, STE, and test quality. Use the commands in `design/quickstart.md`.
- **Verification**: `python -m ruff check .`
- **Status**: absent

### T-PR Commit and open the pull request

- **Requirements**: All
- **Depends on**: T-LOCAL-GATES
- **Acceptance**: The commit title uses the form `feat(web-portal): add per-port Mist Insights series to WAN dashboard`. The branch is `feat/4330-per-port-mist-insights-parity`. The pull request body contains `Closes #4330`. The record folder is copied into the repository record path. The change stages explicit paths only.
- **Verification**: `python -m py_compile MistHelper.py`
- **Status**: absent

### T-REMOTE-CI Watch the remote checks

- **Requirements**: All
- **Depends on**: T-PR
- **Acceptance**: Each required check reports success on the pull request head. A failed check opens a new issue with its full output.
- **Verification**: Remote check through `gh pr checks` on the pull request number from T-PR. No local command substitutes for this check.
- **Status**: absent

### T-MERGE Squash merge after authorization

- **Requirements**: All
- **Depends on**: T-REMOTE-CI and the orchestrator authorization
- **Acceptance**: The `auto-merge` label is added only after each check is green. The squash merge uses the pull request title. The branch is removed after the merge. Merge does not enable production collection, because the request cap stays unset (D-14).
- **Verification**: Remote check through `gh pr view` on the pull request number from T-PR.
- **Status**: absent

## Dependencies and Execution Order

- Phase 1: T001 and T003 run in parallel. T004 follows T003.
- Phase 2: T002 follows D-12.
- Phase 3: T005 follows T002 and T003. T006 follows T005. T007 runs in parallel with any phase.
- Phase 4: T008 follows T005. T009 follows T008.
- Phase 5: T010 follows T006 and T008. T011 runs in parallel with any phase.
- Phase 6: T-LOCAL-GATES follows every task. T-PR, T-REMOTE-CI, and T-MERGE follow in order.

## Test Cases

| ID | Test | File |
| - | - | - |
| TC-01 | Gateway insight request carries `port_id`, `metrics`, `interval`, `limit`, `page`, `start`, and `end` | `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py` |
| TC-02 | Installed mistapi version is 0.64 and the method accepts `port_id` | `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py` |
| TC-03 | Response with named arrays and a matching window is accepted | `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py` |
| TC-04 | Mismatched window, mismatched interval, or non-list arrays are rejected as malformed | `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py` |
| TC-05 | HTTP 429 returns `rate_limited` after one attempt with no SDK retry | `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py` |
| TC-06 | HTTP 4xx and 5xx return explicit states without an empty success | `tests/integration/web_portal/wan_dashboard/test_mistapi_contract.py` |
| TC-07 | Seven-day byte total equals the floor of the sum of bits per second times 3600, divided by 8 | `tests/unit/wan_dashboard/test_port_insights.py` |
| TC-08 | A missing sample stays absent and lowers coverage | `tests/unit/wan_dashboard/test_port_insights.py` |
| TC-09 | A `next` value or a short series yields state `partial` | `tests/unit/wan_dashboard/test_port_insights.py` |
| TC-10 | An unset or zero cap skips the phase with zero SDK calls | `tests/unit/wan_dashboard/test_worker.py` |
| TC-11 | A cap of N makes exactly N calls and moves the cursor by N | `tests/unit/wan_dashboard/test_worker.py` |
| TC-12 | The cursor wraps and covers every port over repeated refreshes | `tests/unit/wan_dashboard/test_port_insights.py` |
| TC-13 | `organization_scope` tags a site-scoped request with its tenant | `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py` |
| TC-14 | A site-scoped request without a tenant fails closed before transport | `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py` |
| TC-15 | A refresh writes each of the nine range keys once through `_remember_result` | `tests/integration/web_portal/wan_dashboard/test_services.py` |
| TC-16 | A malformed port series is never stored as live | `tests/integration/web_portal/wan_dashboard/test_services.py` |
| TC-17 | A lost lease stops the phase before the next request | `tests/unit/wan_dashboard/test_worker.py` |
| TC-18 | The port view shows state `live`, the UTC time, and the port totals | `tests/e2e/web_portal/test_wan_dashboard_cache_only.py` |
| TC-19 | The port view shows state `partial` and the coverage for a short series | `tests/e2e/web_portal/test_wan_dashboard_cache_only.py` |
| TC-20 | An empty cache shows `unavailable` and makes no Mist request | `tests/e2e/web_portal/test_wan_dashboard_cache_only.py` |
| TC-21 | The overview copy states cumulative counters since the last device reboot | `tests/e2e/web_portal/test_wan_dashboard_cache_only.py` |
| TC-22 | Logs and errors contain no token, cookie, or response body | `tests/integration/web_portal/wan_dashboard/test_services.py` |
| TC-23 | The existing refresh queue test still passes | `tests/e2e/web_portal/test_wan_dashboard_cache_only.py` |
| TC-24 | The headroom check skips the phase when the planned calls exceed 2,500 per hour | `tests/unit/wan_dashboard/test_port_insights.py` |
| TC-25 | Change-set review: the pull request file list matches the change map, and no file is copied from the source repository (FR-015 and FR-016) | Pull request file list reviewed in T-PR |
