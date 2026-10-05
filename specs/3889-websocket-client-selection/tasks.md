# Tasks: WebSocket Client Selection

**Issue**: #3889 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Planning status**: The specification, plan, research, data model, quickstart,
and client-discovery contract are complete.

**Implementation status**: The backend, catalog metadata, page integration, and
isolated regressions are implemented. PR #3897 merged at `56818841691eda43e5db375071a0ec52b7ddd64e`.
The parent then transferred exclusive ownership of the WebSocket page files.
Only client-picker-specific expectations and fixtures changed in the merged audit harness.
Delivery gates and human review remain.

**Task setup**: This file uses `.specify/templates/tasks-template.md`.
The normal bootstrap created this worktree's `.venv`.
It installed Python 3.13 dependencies, including mistapi 0.64.0.
Offline SDK inspection verified both search callables use `mist_get`.
The backend tests verify response association without live Mist calls.

**Tests**: Regression tests are required and must run before production edits.
Use mocked SDK responses and intercepted browser requests. Do not use
credentials, live Mist calls, device utilities, DHCP release, captures, shell
calls, containers, release workflows, or production deployment.

## Ownership Record

The following record clears the files that issue #3889 changed:

| Owner | Protected scope |
| - | - |
| PR #3897 merged before handoff. | `src/mist/realtime/websocket_streams/web/static/websockets.js` |
| Parent transferred page ownership after #3897 merged. | `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` (not changed) |
| Parent-owned audit harness merged in PR #3892. | `tests/e2e/websockets_tab/dialog_audit/`; only client-picker-specific expectations and fixtures changed. |
| Child #3890 merged in PR #3891. | `src/mist/realtime/websocket_streams/catalog/utility_text.py` (not changed) |
| PR #3888 cancellation baseline merged in PR #3897. | Cancellation behavior and its module were preserved. |

Do not change `.specify/feature.json`, shared instructions, shared context
records, or another feature's files.

## Phase 1: Setup

**Purpose**: Confirm the required environment and SDK evidence.

- [x] T001 Use Python 3.13 or newer and verify the installed `mistapi>=0.64.0,<0.65` package against `requirements.txt`.

## Phase 2: Foundational Gates

**Purpose**: Prove the SDK and validator contract, then clear file ownership.
These tasks block every regression and implementation task.

- [x] T002 Inspect the installed pinned SDK callable paths, method signatures, request arguments, response fields, and supported pagination for wired and WAN client search. Prove HTTP GET behavior through offline inspection or mocked transport tests. Record evidence in `specs/3889-websocket-client-selection/tasks.md`.
- [x] T003 [P] Inspect `src/mist/realtime/websocket_streams/intake/fields/scalar_checker.py`, `src/mist/realtime/websocket_streams/intake/fields/list_checker.py`, and the related validator tests. Record whether `mac_address` currently accepts complete, partial, wildcard, and arbitrary filters. Do not claim that arbitrary filters already pass.
- [x] T004 [P] Recheck protected scopes. PR #3897 merged before the parent transferred JavaScript ownership. PR #3892 and PR #3891 merged the audit harness and wording changes. Issue #3889 changed no cancellation module or utility-text file.

**Gate**: T001 through T004 passed before the implementation. The later browser
tests use the merged isolated audit harness.

## Phase 3: Regression Baseline

**Purpose**: Define and verify isolated regressions for the client discovery behavior.

- [x] T005 [P] [US1] Add mocked SDK contract tests in `tests/unit/websocket_streams/intake/test_ws_client_discovery_3889.py`. They cover the verified SDK method, target association, success, empty, 4xx, 5xx, network, timeout, malformed data, duplicates, incomplete results, and manual-only gateway behavior.
- [x] T006 [US1] Add isolated Playwright regressions in `tests/e2e/websockets_tab/dialog_audit/test_client_selection.py`. They cover EX DHCP choices, mixed manual and selected MACs, keyboard use, removal, confirmation, unchanged payload, and no utility transmission.
- [x] T007 [P] [US2] Keep the existing validator unchanged. The pinned SDK does not define partial or wildcard `mac_address` syntax. Do not claim support or file a separate defect without SDK evidence.
- [x] T008 [US3] Cover loading, success, empty, HTTP 403, HTTP 503, network failure, incomplete response, unavailable gateway, and ten-second timeout in the isolated browser regressions.
- [x] T009 [US4] Cover delayed device and site results, operation changes, late timeout replies, cancellation, manual-value preservation, and aggregate streams. Every request is local and fail-closed.
- [x] T010 Run regression tests before production edits. The focused EX DHCP test failed before page integration because no `/clients` request occurred. The same test passes after implementation. Full current results are recorded below.

**Regression checkpoint**: The initial focused EX DHCP browser check failed
because no client lookup started. It passes with the completed integration.
The isolated tests block all unapproved requests.

## Phase 4: User Story 1 - Select DHCP Clients Safely (P1)

**Goal**: Offer device-scoped choices while preserving manual input and the
existing DHCP request.

**Independent test**: Use mocked discovery and an intercepted request to check
one, multiple, mixed, disconnected, unlisted, and empty client input. Confirm
that selection alone never starts the utility.

- [x] T011 [US1] Retain the explicit device MAC from the selected site's Mist device record in `src/mist/realtime/websocket_streams/intake/pickers/devices.py`. Do not infer a MAC from `device_id`.
- [x] T012 [US1] Implement the verified read-only client lookup and association checks in `src/mist/realtime/websocket_streams/intake/pickers/resources.py` and `src/mist/realtime/websocket_streams/intake/pickers/service.py`. Use only the verified SDK method and reject rows without selected-site and selected-device evidence.
- [x] T013 [US1] Expose the scoped lookup through `src/mist/realtime/websocket_streams/web/services/pickers/service.py`, `src/mist/realtime/websocket_streams/web/blueprint/routes/pickers.py`, and `src/mist/realtime/websocket_streams/web/blueprint/registry.py`. Preserve app authentication and distinguish lookup errors from empty results.
- [x] T029 [US1] Add isolated backend tests for EX device scope, response association, duplicate normalization, wrong-site rejection, empty and malformed results, unsupported gateway guidance, incomplete pagination, network errors, 4xx and 5xx responses, and JSON route behavior.
- [x] T014 [P] [US1] Add operation-scoped client-picker metadata to `FieldSpec` and `UtilityFieldFactory`. Keep SDK field names unchanged.
- [x] T015 [US1] Add EX client selection in `src/mist/realtime/websocket_streams/web/static/websockets.js`. Keep `macs` optional and editable, support multiple selections, retain manual entries, and leave the request shape, target review, confirmation, and action locks unchanged.
- [x] T016 [US1] Keep SRX and SSR client discovery unavailable and manual input enabled. Do not use site-wide WAN results as gateway results.

## Phase 5: User Story 2 - Preserve MAC Table Filters (P1)

**Goal**: Let a known client fill the field without restricting valid manual
filters or changing the MAC-table request.

**Independent test**: Compare selected, manual complete-MAC, and empty inputs
against the current request payload.

- [x] T017 [US2] Leave `scalar_checker.py` unchanged because the pinned SDK does not define additional filter forms. Record this evidence and keep unsupported forms out of scope.
- [x] T018 [US2] Allow a selected client to fill the editable optional `mac_address` field. Preserve empty-input behavior and submit the existing payload shape.

## Phase 6: User Story 3 - Continue When Discovery Fails (P1)

**Goal**: End every lookup state within ten seconds and keep manual input
available.

**Independent test**: Intercept success, empty, 4xx, 5xx, network, unavailable,
and delayed responses. Confirm each state is distinct and manual submission
does not trigger discovery or a utility.

- [x] T019 [US3] Implement accessible loading, available, empty, request-error, service-error, unavailable, and timeout states. End loading within ten seconds and retain current manual values.

## Phase 7: User Story 4 - Keep Choices Within the Current Target (P1)

**Goal**: Clear stale choices and ignore late responses when the target changes.

**Independent test**: Delay one lookup, change each target field, and complete
responses out of order. Confirm the current target, manual fields, locks, and
cancellation state remain unchanged.

- [x] T020 [US4] Bind lookup results to the site, device, operation, and request generation. Clear stale choices and selector-derived values immediately, ignore late results, and preserve independent manual values.

## Phase 8: User Story 5 - Require Ownership and Human Review (P1)

**Goal**: Record cleared file ownership and require human review for DHCP behavior.

**Independent test**: An absent handoff or human approval keeps the delivery
gate closed. No pull request can auto-merge or merge without explicit human
review.

- [x] T021 [US5] Record the owner handoff above. The pull request must state that DHCP changes require human review and auto-merge is prohibited. The human approval gate stays open until a reviewer approves.

## Phase 9: Polish and Delivery Evidence

**Purpose**: Record the user-visible change, run applicable checks, and prepare
truthful review evidence. Do not run a live release or deployment.

- [x] T022 Add `changelog.d/issue-3889-websocket-client-selection.md`. State that SRX and SSR choices remain unavailable because selected-gateway association is unproven.
- [x] T023 Run every applicable targeted test from the updated quickstart. Record each exact command and result below.
- [x] T024 Run compile, Ruff, Black, mypy, and Bandit checks on changed files. Record each exact command and result below.
- [x] T025 Run the live-guide preflight before the changed-scope test-quality analyzer. The analyzer ran after the implementation commit and before push. It reported zero new findings.

  The live-guide preflight passed on 2026-10-05. The analyzer remains pending
  until after the local commit and before push.

- [x] T026 Inspect the pull request template. Preserve its headings and checklist when creating the pull request.
- [ ] T027 Request human review for DHCP release changes. Keep auto-merge disabled and do not merge before approval. This task remains open until the required human review is recorded.
- [x] T028 [US1] Record isolated browser evidence for keyboard selection, removal, manual entry, target review, and confirmation. Execute no live utility.

## Dependencies and Execution Order

- T001 precedes T002. T003 and T004 can run in parallel with T001 or T002.
- T004 blocks every regression or implementation task that touches an owned
  scope until the owner records a handoff. The parent transferred page
  ownership after PR #3897 merged.
- T002 and T004 must pass before T005 through T009. T010 depends on all five
  regression tasks.
- T010 records the regression baseline. T011 through T016 require verified
  SDK method and device-association evidence.
- T012 depends on T011. T013 depends on T012. T015 depends on T013 and T014.
- T017 depends on T002, T003, T007, and T010. Unsupported or undocumented
  filters stay rejected until the specification defines them.
- T018 depends on T010 and T017. T019 depends on T010 and the response contract
  established by T013. T020 depends on T010 and must preserve T019's states.
- T021 and T027 require ownership clearance. T027 also requires all applicable
  tests and quality checks to pass.
- T022 through T026 depend on implementation completion. T025 applies after
  the local commit and before push.
- T028 depends on implementation and T023. Its result is required before T027.
- Stop if SDK method paths, response association, pagination, or supported
  `mac_address` syntax cannot be proven. Do not invent an endpoint or report an
  unsupported contract as verified.

## Parallel Opportunities

- T003 and T004 are read-only checks and can run in parallel.
- T005 and T007 use separate test files and can run in parallel after T002 and
  T004 pass.
- T014 can run beside T011 after the regression checkpoint because it changes
  separate catalog files.
- Do not parallelize work on `websockets.js`, the shared parity test file, or
  any protected scope. Recheck ownership immediately before each edit.
- The user authorized a commit, push, and review pull request after all checks
  pass. No task authorizes a live API call, utility run, capture, shell call,
  release, or production deployment. Do not merge before human review.

## Implementation and Validation Evidence

The backend tests use a fake SDK session and Flask's local test client. The
browser tests use synthetic responses. They do not call Mist Cloud or run a
device utility.

The selector supports verified EX wired-client choices only. SRX and SSR show
manual-entry guidance because WAN search does not prove selected-gateway
association. Incomplete result pages are not shown as complete.

The current scalar checker accepts complete MAC addresses only and normalizes
them. The pinned SDK documents `mac_address` as a filter and copies a
nonempty string to its request body. It does not document partial or wildcard
filter syntax. This does not prove that the existing validator rejects a
supported filter, so no separate defect issue was filed. Keep broader filter
support out of issue #3889 until the device contract proves a supported form.

Validation results:

- `rtk proxy .venv/bin/python -m pytest -q tests/unit/websocket_streams/intake/test_ws_client_discovery_3889.py tests/unit/websocket_streams/catalog/test_ws_client_field_modes_3889.py tests/e2e/websockets_tab/dialog_audit tests/e2e/websockets_tab/test_websockets_page.py` passed. It ran 141 tests.
- `rtk proxy .venv/bin/python -m ruff check` on the changed Python files passed.
- `rtk proxy .venv/bin/python -m black --check` on the changed Python files passed.
- `rtk proxy .venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` passed. It checked 804 source files.
- `rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r src/mist/realtime/websocket_streams tests/e2e/websockets_tab/dialog_audit/support/journeys.py tests/e2e/websockets_tab/dialog_audit/support/policy.py tests/e2e/websockets_tab/dialog_audit/test_dialogs.py tests/e2e/websockets_tab/dialog_audit/test_client_selection.py tests/unit/websocket_streams/catalog/test_ws_client_field_modes_3889.py tests/unit/websocket_streams/intake/test_ws_client_discovery_3889.py -q` passed.
- `rtk proxy .venv/bin/python -m py_compile` on the changed Python files passed.
- `rtk proxy .venv/bin/python -m pytest -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` passed. It ran 1 preflight test.
- `rtk proxy .venv/bin/python -m pytest -q tests/guardrails/test_changelog_fragment_policy.py` passed. It ran 17 tests with 1 skipped.
- `rtk proxy test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` passed. It checked 4 changed test files, reported 0 findings and 0 new findings, parsed 3 files, and skipped 3.
- The full `rtk proxy test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` gate passed. It checked 1,077 files, reported 727 baseline findings, 0 new findings, 46 skipped files, and 0 parse errors.
- No live Mist request, DHCP release, device utility, capture, or shell call ran.

## Implementation Strategy

1. Verify environment, SDK behavior, validator behavior, and file ownership.
2. Keep manual values available for EX DHCP and MAC-table selections.
3. Keep SRX and SSR discovery unavailable until device association is proven.
4. Complete error states and stale-result protection without editing the
   cancellation module or utility descriptions.
5. Run the required tests and quality gates. Require human review before merge.
