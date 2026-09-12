# Tasks: `--testinteractive` Reliability Defects

**Input**: Design documents in `specs/1021-testinteractive-reliability-defects/`
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/interactive-test-telemetry.md`, `contracts/cli-invocation.md`, `quickstart.md`, and `.specify/memory/constitution.md`
**Delivery model**: Six non-stacked, serial bug-fix PRs, exactly in issue order #1636, #1637, #1638, #1639, #1640, then #1641. Story 7 is cumulative coverage supplied by the six issue phases; it is not a seventh implementation branch or PR.

## Safety and workflow constraints

All automated regressions are mock-first and must make no Mist write or mutating call. An optional smoke check is allowed only after focused local checks pass, using an authorized read-only credential and an exact selector. JSONL/log fixtures and other local runtime artifacts must be confined to the controlled `data/` location, must not expose credentials, and must not be committed. Remote GitHub state is read-only during planning; future delivery actions occur only in the issue's own phase. Every implementation PR is opened as a draft before source changes, starts from the last squash-merged `main`, targets `main`, and is fully merged before the next issue worktree is updated.

## Phase 1: Setup (planning and workflow controls only)

**Purpose**: Establish the serial-delivery, remote-safety, and local-artifact rules without modifying application code, tests, configuration, branches, commits, or remote state.

- [ ] T001 Verify the remote-read-only, mock-first, credential-redaction, and controlled-artifact rules in `specs/1021-testinteractive-reliability-defects/spec.md`, `specs/1021-testinteractive-reliability-defects/quickstart.md`, and `data/` before future implementation begins.
- [ ] T002 Record the fixed non-stacked delivery order #1636 -> #1637 -> #1638 -> #1639 -> #1640 -> #1641 in `specs/1021-testinteractive-reliability-defects/plan.md` and prohibit a branch from another issue branch.
- [ ] T003 Confirm the required future PR scope, squash-merge rule, and no-overlap hot-file control against `.specify/memory/constitution.md`, `MistHelper.py`, and `src/troubleshooting/interactive_test_runner.py`.

---

## Phase 2: Foundational (workflow prerequisites only)

**Purpose**: Confirm the future validation and artifact-handling workflow before beginning Issue #1636. This phase intentionally adds no application infrastructure or shared code.

- [ ] T004 Verify the focused mock-test and syntax-gate commands for `tests/unit/troubleshooting/test_interactive_test_runner.py`, `tests/unit/analytics/test_telemetry_emitter.py`, `tests/unit/refactors/test_main_entrypoint.py`, `tests/unit/export/test_wan_client_events_exporter.py`, and `MistHelper.py` against `specs/1021-testinteractive-reliability-defects/quickstart.md`.
- [ ] T005 Verify that future fixtures, JSONL telemetry, and cleanup checks remain under `data/` and that no test target in `tests/unit/` requires a live or mutating Mist call.

**Checkpoint**: Serial workflow controls are understood; only Issue #1636 may start.

---

## Phase 3: User Story 1 - Issue #1636 Telemetry False-Pass Semantics (Priority: P1) - MVP

**Goal**: A handler-scoped `ERROR` record must produce an observable non-clean operation result, summary count, and non-zero suite result rather than a false pass.

**Independent Test**: With mocked handlers in `tests/unit/troubleshooting/test_interactive_test_runner.py`, a handler that logs `ERROR` and returns normally is emitted as `logged_error`, counted by `tests/unit/analytics/test_telemetry_emitter.py`, and yields a non-zero runner result.

**Serial example**: T006 -> T007 -> T008 -> T009 -> T010 -> T011 -> T012 -> T013. No task may overlap work for #1637.

- [ ] T006 [US1] Create `fix/1636-interactive-telemetry` from the last squash-merged updated `main` worktree, verifying the branch base through `.git/HEAD` before touching `src/troubleshooting/interactive_test_runner.py`.
- [ ] T007 [US1] Open a draft PR for Issue #1636 targeting `main` before source changes, declaring the intended files `src/troubleshooting/interactive_test_runner.py`, `src/analytics/telemetry_emitter.py`, `src/dataclasses/progress_event.py`, `tests/unit/troubleshooting/test_interactive_test_runner.py`, and `tests/unit/analytics/test_telemetry_emitter.py`.
- [ ] T008 [US1] Narrow Issue #1636 implementation to scoped `ERROR`+ observation and outcome/summary propagation in `src/troubleshooting/interactive_test_runner.py`, `src/analytics/telemetry_emitter.py`, and `src/dataclasses/progress_event.py`; preserve existing JSONL fields and write any telemetry fixture only under `data/`.
- [ ] T009 [US1] Write focused mock-first failing regressions for normal-return handlers that log `ERROR`, observer cleanup between handlers, summary error counts, and non-zero completion in `tests/unit/troubleshooting/test_interactive_test_runner.py` and `tests/unit/analytics/test_telemetry_emitter.py`.
- [ ] T010 [US1] Implement handler-scoped `ERROR` observation, deterministic `logged_error` versus `raised_exception` outcome precedence, additive telemetry fields, and failure summary/exit semantics in `src/troubleshooting/interactive_test_runner.py`, `src/analytics/telemetry_emitter.py`, and `src/dataclasses/progress_event.py`.
- [ ] T011 [US1] Run focused mock-first tests in `tests/unit/troubleshooting/test_interactive_test_runner.py` and `tests/unit/analytics/test_telemetry_emitter.py`, run `python -m py_compile` for `MistHelper.py`, and inspect `data/` so no artifact escaped the controlled location.
- [ ] T012 [US1] Review the Issue #1636 diff for the contract in `contracts/interactive-test-telemetry.md`, wait for required CI, verify the PR description closes #1636 and lists changed files, then squash-merge the approved draft PR to `main`.
- [ ] T013 [US1] Only after #1636 is squash-merged, update/rebase the next Issue #1637 worktree from merged `main` before work on `src/troubleshooting/interactive_test_runner.py` or `tests/unit/troubleshooting/test_interactive_test_runner.py`.

---

## Phase 4: User Story 2 - Issue #1637 Exact Site Selector Resolution (Priority: P2)

**Goal**: A supplied selector resolves only by exact ID or full name; a partial or unknown selector stops before an operation runs and visibly records the unresolved request.

**Independent Test**: Stubbed sites in `tests/unit/troubleshooting/test_interactive_test_runner.py` prove exact ID/name selection works while partial and unknown supplied selectors invoke no operation callable.

**Serial example**: T014 -> T015 -> T016 -> T017 -> T018 -> T019 -> T020 -> T021. No task may overlap work for #1638.

- [ ] T014 [US2] Create `fix/1637-interactive-selector-fallback` from the merged updated `main` worktree after T013, verifying `.git/HEAD` before touching `src/troubleshooting/interactive_test_runner.py`.
- [ ] T015 [US2] Open a draft PR for Issue #1637 targeting `main` before source changes, declaring `src/troubleshooting/interactive_test_runner.py`, `src/analytics/telemetry_emitter.py`, and `tests/unit/troubleshooting/test_interactive_test_runner.py` as the only expected implementation/test surfaces.
- [ ] T016 [US2] Narrow Issue #1637 to exact `MIST_INTERACTIVE_TEST_SITE` ID/full-name resolution, terminal unresolved reporting, and requested/actual target metadata in `src/troubleshooting/interactive_test_runner.py` and `src/analytics/telemetry_emitter.py`, without changing the unset-selector path.
- [ ] T017 [US2] Write focused mock-first failing regressions for exact ID, exact full-name, partial, unknown, and no-selector cases in `tests/unit/troubleshooting/test_interactive_test_runner.py`, asserting no operation invocation after a supplied unresolved selector.
- [ ] T018 [US2] Implement fail-closed supplied-selector resolution and prominent requested/actual site telemetry in `src/troubleshooting/interactive_test_runner.py` and `src/analytics/telemetry_emitter.py` according to `contracts/cli-invocation.md` and `contracts/interactive-test-telemetry.md`.
- [ ] T019 [US2] Run the selector-focused mock tests in `tests/unit/troubleshooting/test_interactive_test_runner.py`, run `python -m py_compile` for `MistHelper.py` and `src/troubleshooting/interactive_test_runner.py`, and inspect `data/` for controlled local artifacts only.
- [ ] T020 [US2] Review the Issue #1637 diff against `contracts/cli-invocation.md`, wait for required CI, verify the PR description closes #1637 and lists changed files, then squash-merge the approved draft PR to `main`.
- [ ] T021 [US2] Only after #1637 is squash-merged, update/rebase the next Issue #1638 worktree from merged `main` before work on `src/utils/input_utils.py`, `src/troubleshooting/interactive_test_runner.py`, or `tests/unit/troubleshooting/test_interactive_test_runner.py`.

---

## Phase 5: User Story 3 - Issue #1638 Site Context and Prompt Cancellation (Priority: P3)

**Goal**: Per-operation telemetry distinguishes injected versus unavailable `site_id` context and explicit EOF/interrupt cancellation from clean completion.

**Independent Test**: Mixed signature and safe-input mocks in `tests/unit/troubleshooting/test_interactive_test_runner.py` produce distinct injected/unavailable and prompt-cancelled outcomes, with summary fields checked in `tests/unit/analytics/test_telemetry_emitter.py`.

**Serial example**: T022 -> T023 -> T024 -> T025 -> T026 -> T027 -> T028 -> T029. No task may overlap work for #1639.

- [ ] T022 [US3] Create `fix/1638-interactive-site-context` from the merged updated `main` worktree after T021, verifying `.git/HEAD` before touching `src/utils/input_utils.py`.
- [ ] T023 [US3] Open a draft PR for Issue #1638 targeting `main` before source changes, declaring `src/utils/input_utils.py`, `src/troubleshooting/interactive_test_runner.py`, `src/analytics/telemetry_emitter.py`, `src/dataclasses/progress_event.py`, `tests/unit/troubleshooting/test_interactive_test_runner.py`, and `tests/unit/analytics/test_telemetry_emitter.py`.
- [ ] T024 [US3] Narrow Issue #1638 to the canonical safe-input termination seam, signature-derived site-context metadata, outcome precedence, and additive summary counts in `src/utils/input_utils.py`, `src/troubleshooting/interactive_test_runner.py`, `src/analytics/telemetry_emitter.py`, and `src/dataclasses/progress_event.py`.
- [ ] T025 [US3] Write focused mock-first failing regressions for injected and unavailable `site_id`, EOF, interrupt, normal return, and higher-precedence logged/raised errors in `tests/unit/troubleshooting/test_interactive_test_runner.py` and `tests/unit/analytics/test_telemetry_emitter.py`.
- [ ] T026 [US3] Implement structured safe-input termination observation and per-operation site-context/cancellation telemetry in `src/utils/input_utils.py`, `src/troubleshooting/interactive_test_runner.py`, `src/analytics/telemetry_emitter.py`, and `src/dataclasses/progress_event.py` without adding handler-wide signature migration.
- [ ] T027 [US3] Run the context/cancellation-focused mock tests in `tests/unit/troubleshooting/test_interactive_test_runner.py` and `tests/unit/analytics/test_telemetry_emitter.py`, run `python -m py_compile` for `src/utils/input_utils.py` and `src/troubleshooting/interactive_test_runner.py`, and inspect `data/` for controlled local artifacts only.
- [ ] T028 [US3] Review the Issue #1638 diff against `contracts/interactive-test-telemetry.md`, wait for required CI, verify the PR description closes #1638 and lists changed files, then squash-merge the approved draft PR to `main`.
- [ ] T029 [US3] Only after #1638 is squash-merged, update/rebase the next Issue #1639 worktree from merged `main` before work on `src/export/wan_client_events_exporter.py` or `tests/unit/export/test_wan_client_events_exporter.py`.

---

## Phase 6: User Story 4 - Issue #1639 WAN SDK Namespace (Priority: P4)

**Goal**: Option 203 calls the installed direct WAN-client-events SDK member instead of the obsolete nested `.events.search` path.

**Independent Test**: A stub exposing only `sites.wan_clients.searchSiteWanClientEvents` succeeds through `tests/unit/export/test_wan_client_events_exporter.py`, proving no `.events` attribute lookup occurs.

**Serial example**: T030 -> T031 -> T032 -> T033 -> T034 -> T035 -> T036 -> T037. No task may overlap work for #1640.

- [ ] T030 [US4] Create `fix/1639-wan-sdk-namespace` from the merged updated `main` worktree after T029, verifying `.git/HEAD` before touching `src/export/wan_client_events_exporter.py`.
- [ ] T031 [US4] Open a draft PR for Issue #1639 targeting `main` before source changes, declaring `src/export/wan_client_events_exporter.py` and `tests/unit/export/test_wan_client_events_exporter.py` as the expected scope.
- [ ] T032 [US4] Narrow Issue #1639 to the option-203 WAN endpoint lookup in `src/export/wan_client_events_exporter.py`, retaining the supported `mistapi==0.63.3` direct `sites.wan_clients.searchSiteWanClientEvents` namespace and adding no SDK adapter or dependency change.
- [ ] T033 [US4] Write a focused mock-first failing SDK-surface regression in `tests/unit/export/test_wan_client_events_exporter.py` using a stub with `countSiteWanClients`, `searchSiteWanClients`, and direct `searchSiteWanClientEvents` only.
- [ ] T034 [US4] Replace only the obsolete nested WAN event endpoint lookup with the verified direct callable in `src/export/wan_client_events_exporter.py`, preserving read-only API behavior and existing controlled `data/` output handling.
- [ ] T035 [US4] Run the focused mock-first exporter tests in `tests/unit/export/test_wan_client_events_exporter.py`, run `python -m py_compile` for `src/export/wan_client_events_exporter.py` and `MistHelper.py`, and inspect `data/` for controlled local artifacts only.
- [ ] T036 [US4] Review the Issue #1639 diff against `specs/1021-testinteractive-reliability-defects/research.md`, wait for required CI, verify the PR description closes #1639 and lists changed files, then squash-merge the approved draft PR to `main`.
- [ ] T037 [US4] Only after #1639 is squash-merged, update/rebase the next Issue #1640 worktree from merged `main` before work on `MistHelper.py` or `tests/unit/refactors/test_main_entrypoint.py`.

---

## Phase 7: User Story 5 - Issue #1640 Unsupported Hyphenated Flag (Priority: P5)

**Goal**: `--test-interactive` exits non-zero with an actionable `--testinteractive` suggestion and never falls through to the normal interactive menu.

**Independent Test**: Instrumented parser/entrypoint tests in `tests/unit/refactors/test_main_entrypoint.py` prove the unsupported spelling fails clearly while the documented spelling retains interactive-test dispatch.

**Serial example**: T038 -> T039 -> T040 -> T041 -> T042 -> T043 -> T044 -> T045. No task may overlap work for #1641.

- [ ] T038 [US5] Create `fix/1640-unsupported-test-flag` from the merged updated `main` worktree after T037, verifying `.git/HEAD` before touching `MistHelper.py`.
- [ ] T039 [US5] Open a draft PR for Issue #1640 targeting `main` before source changes, declaring `MistHelper.py`, `src/refactors/main_entrypoint.py`, and `tests/unit/refactors/test_main_entrypoint.py` as the expected scope.
- [ ] T040 [US5] Narrow Issue #1640 to explicit unsupported `--test-interactive` detection and an actionable `--testinteractive` suggestion in `MistHelper.py` and `src/refactors/main_entrypoint.py`, preserving the supported flag and leaving the hyphenated name unaliased.
- [ ] T041 [US5] Write focused mock-first parser/entrypoint regressions for unsupported `--test-interactive`, non-zero exit, suggestion text, and preserved `--testinteractive` dispatch in `tests/unit/refactors/test_main_entrypoint.py`.
- [ ] T042 [US5] Implement the explicit unsupported-flag rejection path in `MistHelper.py` and `src/refactors/main_entrypoint.py` so it cannot silently enter the ordinary menu or expand the public flag interface.
- [ ] T043 [US5] Run focused mock-first tests in `tests/unit/refactors/test_main_entrypoint.py` and `tests/unit/` filtered for `testinteractive or test_interactive`, run `python -m py_compile` for `MistHelper.py` and `src/refactors/main_entrypoint.py`, and inspect `data/` for controlled local artifacts only.
- [ ] T044 [US5] Review the Issue #1640 diff against `contracts/cli-invocation.md`, wait for required CI, verify the PR description closes #1640 and lists changed files, then squash-merge the approved draft PR to `main`.
- [ ] T045 [US5] Only after #1640 is squash-merged, update/rebase the next Issue #1641 worktree from merged `main` before work on `MistHelper.py`, `src/refactors/main_entrypoint.py`, or `tests/unit/refactors/test_main_entrypoint.py`.

---

## Phase 8: User Story 6 - Issue #1641 Side-Effect-Free Help (Priority: P6)

**Goal**: `--help`, `-h`, and combined help invocations print usage and exit before deferred imports, dependency initialization, Mist session setup, or interactive dispatch.

**Independent Test**: Instrumented seams in `tests/unit/refactors/test_main_entrypoint.py` show all help forms exit successfully with usage output and zero calls to deferred-initialization or dispatch seams.

**Serial example**: T046 -> T047 -> T048 -> T049 -> T050 -> T051 -> T052 -> T053. This is the final implementation PR; T053 prepares only cumulative verification.

- [ ] T046 [US6] Create `fix/1641-side-effect-free-help` from the merged updated `main` worktree after T045, verifying `.git/HEAD` before touching `MistHelper.py`.
- [ ] T047 [US6] Open a draft PR for Issue #1641 targeting `main` before source changes, declaring `MistHelper.py`, `src/refactors/main_entrypoint.py`, and `tests/unit/refactors/test_main_entrypoint.py` as the expected scope.
- [ ] T048 [US6] Narrow Issue #1641 to an early help-only parse/detection path in `MistHelper.py` and `src/refactors/main_entrypoint.py` that preserves the ordinary non-help initialization sequence.
- [ ] T049 [US6] Write focused mock-first ordering regressions for `--help`, `-h`, and `--testinteractive --help` in `tests/unit/refactors/test_main_entrypoint.py`, asserting no deferred import, dependency/session initialization, or interactive dispatch call.
- [ ] T050 [US6] Implement side-effect-free help handling in `MistHelper.py` and `src/refactors/main_entrypoint.py` so every help form renders parser usage and exits before deferred initialization.
- [ ] T051 [US6] Run focused mock-first tests in `tests/unit/refactors/test_main_entrypoint.py`, run `python -m py_compile` for `MistHelper.py` and `src/refactors/main_entrypoint.py`, and inspect `data/` for controlled local artifacts only.
- [ ] T052 [US6] Review the Issue #1641 diff against `contracts/cli-invocation.md`, wait for required CI, verify the PR description closes #1641 and lists changed files, then squash-merge the approved draft PR to `main`.
- [ ] T053 [US6] Only after #1641 is squash-merged, update/rebase the cumulative-validation worktree from merged `main` before reading `tests/unit/troubleshooting/test_interactive_test_runner.py`, `tests/unit/analytics/test_telemetry_emitter.py`, `tests/unit/export/test_wan_client_events_exporter.py`, and `tests/unit/refactors/test_main_entrypoint.py`.

---

## Phase 9: Polish and Cross-Cutting Concerns - Story 7 Cumulative Coverage Only

**Purpose**: Confirm the six merged issue regressions collectively satisfy Story 7. This phase creates no implementation branch, no new PR, and no new standalone test work; every defect's test authoring remains in its own issue phase above.

- [x] T054 Re-run the cumulative mock-first regression suite in `tests/unit/troubleshooting/test_interactive_test_runner.py`, `tests/unit/analytics/test_telemetry_emitter.py`, `tests/unit/export/test_wan_client_events_exporter.py`, and `tests/unit/refactors/test_main_entrypoint.py`; run `python -m py_compile MistHelper.py`; verify `data/` contains no escaped, credential-bearing, or commit-bound artifacts.

---

## Dependencies and execution order

### Exact serial dependency graph

`T001 -> T002 -> T003 -> T004 -> T005 -> T006 -> T007 -> T008 -> T009 -> T010 -> T011 -> T012 -> T013 -> T014 -> T015 -> T016 -> T017 -> T018 -> T019 -> T020 -> T021 -> T022 -> T023 -> T024 -> T025 -> T026 -> T027 -> T028 -> T029 -> T030 -> T031 -> T032 -> T033 -> T034 -> T035 -> T036 -> T037 -> T038 -> T039 -> T040 -> T041 -> T042 -> T043 -> T044 -> T045 -> T046 -> T047 -> T048 -> T049 -> T050 -> T051 -> T052 -> T053 -> T054`

At the issue level: `#1636 / US1 -> #1637 / US2 -> #1638 / US3 -> #1639 / US4 -> #1640 / US5 -> #1641 / US6 -> Story 7 cumulative verification`. Each successor starts only after the predecessor's review, CI, and squash merge complete and its next worktree is updated from merged `main`.

### Parallel opportunities

There are **no parallel execution opportunities**. The specified non-stacked PR order, shared hot files (`MistHelper.py` and `src/troubleshooting/interactive_test_runner.py`), mandatory draft-before-change rule, and update-after-merge rule require all tasks to execute serially. Therefore no task is marked `[P]`, including tests within a story.

## Implementation strategy

### MVP first

Complete Setup and Foundational workflow controls, then complete and independently validate only Issue #1636 / User Story 1. Its telemetry correction is the MVP because it prevents false-clean harness results and establishes the trustworthy signal used to assess later fixes.

### Incremental delivery

For each issue, create a fresh branch from the latest merged `main`, open its draft PR before source changes, write mock-first regressions, implement only the narrow scoped files, run focused quality gates, obtain review/CI, squash-merge, then update the next worktree. Do not open or prepare a later issue PR early. Story 7 is achieved by the six issue-specific regression suites and ends with T054 only; it is never a seventh implementation PR.

## Format validation

All 54 tasks use the required `- [ ] T### [P?] [US#?] Description with exact file path` checklist shape: every task has a checkbox, sequential ID, exact path, no `[P]` marker, and a `[US#]` label only in the six issue/story phases. Setup, Foundational, and cumulative Story 7 validation tasks intentionally have no story label.
