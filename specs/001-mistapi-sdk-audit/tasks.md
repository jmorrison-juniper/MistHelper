# Tasks: MistAPI SDK Compatibility Audit

**Input**: Design documents from `/specs/001-mistapi-sdk-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The spec requires regression verification and smoke coverage, so test tasks are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `MistHelper.py`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the audit boundary and call-site inventory that the compatibility matrix will use

- [x] T001 Capture the audited MistAPI release boundary and supported floor in `specs/001-mistapi-sdk-audit/research.md`
- [x] T002 Inventory direct MistAPI call sites in `MistHelper.py` and group them by workflow in `specs/001-mistapi-sdk-audit/research.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the dependency floor before any user story work begins

- [x] T003 [P] Raise the dependency floors in `pyproject.toml` to `mistapi>=0.61.4` and `websocket-client>=1.8.0`
- [x] T004 [P] Raise the runtime dependency floor in `requirements.txt` to `mistapi>=0.61.4` and `websocket-client>=1.8.0`

**Checkpoint**: The audited SDK floor is now in place, so user story implementation can begin

---

## Phase 3: User Story 1 - Compatibility Review Matrix (Priority: P1)

**Goal**: Produce a clear compatibility matrix for every direct MistAPI call site in `MistHelper.py`

**Independent Test**: A reviewer can inspect `specs/001-mistapi-sdk-audit/research.md` and confirm that every direct MistAPI call site in `MistHelper.py` has a status and a release-note reference

### Implementation for User Story 1

- [x] T005 Finish the compatibility matrix in `specs/001-mistapi-sdk-audit/research.md` with a status for every direct MistAPI call site in `MistHelper.py`
- [x] T006 Record compatible workflows and any deferred follow-ups in `specs/001-mistapi-sdk-audit/research.md`

**Checkpoint**: The audit matrix is complete and traceable

---

## Phase 4: User Story 2 - Safe SDK Update Path (Priority: P2)

**Goal**: Apply the one confirmed breaking MistAPI change and keep the rest of the MistHelper workflows stable

**Independent Test**: The updated insight-metrics workflow in `MistHelper.py` still completes with the audited SDK floor, and the regression test in `tests/unit/test_exports.py` passes

### Tests for User Story 2

- [x] T007 [P] [US2] Extend `tests/unit/test_exports.py` with a regression assertion for the updated `getSiteInsightMetricsForClient()` call signature

### Implementation for User Story 2

- [x] T008 [US2] Update the `getSiteInsightMetricsForClient()` call in `MistHelper.py` to use the SDK's newer `metrics=` parameter form
- [x] T009 [US2] Capture any follow-up compatibility notes from the updated insight-metrics workflow in `specs/001-mistapi-sdk-audit/research.md`

**Checkpoint**: The breaking SDK call-site change is fixed and documented

---

## Phase 5: User Story 3 - Verification and Notes (Priority: P3)

**Goal**: Prove that the remaining representative workflows still behave correctly, including the client insight metrics path, and record the final audit summary

**Independent Test**: The smoke coverage in `tests/integration/test_mistapi_sdk_compatibility.py` passes for alarms, device events, stats, SLE summaries, client insight metrics, maps, WLAN lookups, and the E911 BSSID report, and the documentation captures the final audit result

### Tests for User Story 3

- [x] T010 [P] [US3] Add integration smoke coverage in `tests/integration/test_mistapi_sdk_compatibility.py` for alarms, device-event pagination, stats, SLE summaries, client insight metrics, maps, WLAN lookups, and the E911 BSSID report

### Implementation for User Story 3

- [x] T011 [P] [US3] Update `CHANGELOG.md` with the audited MistAPI floor, upstream release summary, and verification outcome
- [x] T012 [P] [US3] Update `specs/001-mistapi-sdk-audit/quickstart.md` with the final validation steps and expected results

**Checkpoint**: The representative workflows are covered and the audit summary is documented

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Run final validation and record the last compatibility status after the code and docs are updated

- [x] T013 Run `python -m py_compile MistHelper.py` and the focused regression suite covering `tests/unit/test_exports.py` plus `tests/integration/test_mistapi_sdk_compatibility.py`
- [x] T014 Refresh `specs/001-mistapi-sdk-audit/research.md` with the final pass/fail status for each `MistHelper.py` workflow and compatibility finding

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user story work until the audited dependency floor is in place
- **User Stories (Phase 3+)**: Depend on the foundational dependency updates
  - User stories can then proceed in priority order or in parallel where file scope does not overlap
- **Polish (Final Phase)**: Depends on the code, tests, and documentation work being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Uses the release-note findings from US1, but remains testable on its own
- **User Story 3 (P3)**: Starts after the SDK update work in US2 so the smoke checks reflect the updated code path

### Within Each User Story

- Matrix/document tasks come before their final summary task
- Tests are written before the code they verify whenever a story includes explicit test tasks
- Story-specific verification is completed before moving to the next phase

### Parallel Opportunities

- Phase 2 dependency updates can be done in parallel (`pyproject.toml` and `requirements.txt`)
- User Story 3 smoke coverage is consolidated into one integration file so `tests/integration/` stays within the five-item rule
- The changelog and quickstart updates can proceed in parallel after the code update is defined

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm the compatibility matrix in `specs/001-mistapi-sdk-audit/research.md`
5. Deliver the matrix if the audit needs to be reported before code changes land

### Incremental Delivery

1. Complete Setup + Foundational → dependency floor is aligned
2. Add User Story 1 → release-note matrix is complete and reviewable
3. Add User Story 2 → `MistHelper.py` uses the updated insight-metrics signature
4. Add User Story 3 → representative workflows and documentation confirm the update is safe
5. Run final validation and capture the last compatibility status in `research.md`

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 + Phase 2 together
2. Developer A works on US1 matrix updates in `specs/001-mistapi-sdk-audit/research.md`
3. Developer B works on the `MistHelper.py` insight-metrics update and `tests/unit/test_exports.py`
4. Developer C works on the integration smoke tests in `tests/integration/`

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] labels map task to specific user stories for traceability
- This feature is an audit-and-compatibility update, so documentation is part of the deliverable, not a side quest
- Verify the test suite before considering the audit complete
- The integration smoke coverage is intentionally consolidated into one file to stay within the five-item rule
