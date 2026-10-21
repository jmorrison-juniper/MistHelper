# Tasks: Migrate Mist Guest Authorizations

**Input**: [Specification](spec.md), [plan](plan.md), and the four supporting paths under `design/`.

**Execution boundary**: This is a future implementation list for issue #4278.
The current request permits planning only. Do not execute any product task during this refresh.
All tasks remain unchecked because no approval or product delivery occurs here.

## Format and Existing Delivery

Tasks use a checkbox, sequential ID, optional story label, action, and concrete path.
Execute serially. No task has a parallel marker.
Mark a task complete only after verification, with a `(delivered: path)` evidence note.
Human decisions require linked dated evidence and remain unchecked until approval exists.

PR #4279 already delivered `src/interfaces/portals/guest_authorizations.py`
and `tests/unit/web_portal/test_guest_authorization_read_model.py`.
Do not recreate them or claim they complete US1. They provide only an offline projection.

Paths below are future targets. T006 must approve their hierarchy and ownership before creation.
Keep the existing projection module unchanged unless a separate approved requirement needs it.

## Phase 1: Setup and Approval Decisions

**Purpose**: Resolve G1-G4 without creating routes, product helpers, or new storage.
The full record path is `specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/`.
Relative design paths below resolve within that record.

- [ ] T001 Obtain the G1 rights decision in `design/research.md`. Record the independent implementation approval or compatible reuse terms before integration.
- [ ] T002 Obtain the G2 access decision in `design/research.md`. Define permitted reads/writes, operator attribution, and exact organization/site/WLAN policy.
- [ ] T003 Obtain G3 numeric byte/row limits and encoding/header/cell rules in `design/research.md`. Approve the bounded request budget without inventing defaults.
- [ ] T004 Obtain G4 durable audit, retention, pre-write failure, post-write failure, and reconciliation decisions in `design/contracts/portal.md`.

## Phase 2: Foundational Contract Gates

**Purpose**: Resolve G5 and establish an approved implementation boundary.
T005 is a documentation and evidence task, not permission to send production writes.
No story begins until T001-T006 pass.

- [ ] T005 Verify G5 in `design/contracts/mist-api.md`. Pin SDK/API revisions and document exact methods, requests, responses, fields, pagination, durations, WLAN scope, and revocation evidence.
- [ ] T006 Record an approved file manifest and owner handover in `plan.md`. Check `src/interfaces/portals/guest_workflows/` and each new hierarchy level against the five-child rule.
- [ ] T007 Add offline contract tests in `tests/contract/web_portal/test_guest_authorizations_api.py`. Cover pinned signatures, arguments, response shapes, HTTP 4xx/5xx, 429, timeouts, and zero live calls.
- [ ] T008 Add access and topology tests in `tests/integration/web_portal/test_guest_authorizations.py`. Prove no second application/database and zero disclosure or writes before permission.
- [ ] T009 Implement approved scope/action checks and audit readiness in `src/interfaces/portals/guest_workflows/access.py`. Preserve CSRF and refuse missing approved attribution or audit readiness.

## Phase 3: User Story 1 - Review Access (Priority: P1)

**Goal**: Show permitted scoped observations without inventing status.
**Independent test**: Mock permitted, denied, incomplete, and missing-credential responses. Confirm zero cross-scope disclosure.

### Tests

- [ ] T010 [US1] Add unit cases in `tests/unit/web_portal/test_guest_authorization_workflows.py`. Enforce "Preserve absent fields as unknown and reject malformed values".
- [ ] T011 [US1] Extend `tests/contract/web_portal/test_guest_authorizations_api.py` for scoped discovery, inherited WLAN resolution, response containers, pagination, and expired-record limits.
- [ ] T012 [US1] Extend `tests/integration/web_portal/test_guest_authorizations.py` and `tests/e2e/web_portal/test_guest_authorizations.py` for permission, selection changes, unknown state, and denied reads.

### Implementation

- [ ] T013 [US1] Define verified scope and observation types in `src/interfaces/portals/guest_workflows/domain.py`. Enforce "Bind returned membership and operator permission before any disclosure or change".
- [ ] T014 [US1] Add explicit scoped SDK reads in `src/interfaces/portals/guest_workflows/sdk.py`. Reuse only the existing session and apply the approved bounded read budget.
- [ ] T015 [US1] Add review routes and templates under `src/interfaces/portals/guest_workflows/presentation/`. Provide stable test IDs and visible unknown or denied states.
- [ ] T016 [US1] After documented handover, register approved review navigation in `web_portal/app.py` and `web_portal/templates/base.html`. Rerun denial and no-write tests before review.

## Phase 4: User Story 2 - Grant Access (Priority: P1)

**Goal**: Submit one reviewed, permitted, exactly confirmed grant.
**Independent test**: Mock scope and duration. Check confirmation and every zero-write rejection path.

### Tests

- [ ] T017 [US2] Extend `tests/unit/web_portal/test_guest_authorization_workflows.py` for MAC formats, approved duration boundaries, changed scope, and supported fields.
- [ ] T018 [US2] Extend contract, integration, and browser cases in `tests/contract/web_portal/test_guest_authorizations_api.py`, `tests/integration/web_portal/test_guest_authorizations.py`, and `tests/e2e/web_portal/test_guest_authorizations.py`. Cover confirmed grant, wrong/canceled confirmation, denied permission, service failure, unknown write, and audit failure.

### Implementation

- [ ] T019 [US2] Add verified grant validation in `src/interfaces/portals/guest_workflows/domain.py`. Use approved limits, not the prior one-hour assumption or source five-year claim.
- [ ] T020 [US2] Add the bound grant handler in `src/interfaces/portals/guest_workflows/presentation/routes.py` and explicit SDK call in `src/interfaces/portals/guest_workflows/sdk.py`. Reject changed scope/content before any write.
- [ ] T021 [US2] Add minimized audit and reconciliation outcomes in `src/interfaces/portals/guest_workflows/access.py`. Enforce "Separate facts, including unknown cloud result" for cloud and audit outcomes.

## Phase 5: User Story 3 - Edit or Extend Access (Priority: P2)

**Goal**: Change only verified writable fields or approved duration.
**Independent test**: Supply a selected record directly. Check exact change, unsupported fields, duration rules, and uncertain outcomes.

### Tests

- [ ] T022 [US3] Extend `tests/contract/web_portal/test_guest_authorizations_api.py` for separate site/organization payload allowlists and verified extension semantics.
- [ ] T023 [US3] Extend `tests/integration/web_portal/test_guest_authorizations.py` and `tests/e2e/web_portal/test_guest_authorizations.py` for edit/extend review, confirmation, denied scope, canceled changes, and audit failure.

### Implementation

- [ ] T024 [US3] Add edit and extension validation in `src/interfaces/portals/guest_workflows/domain.py` and SDK methods in `src/interfaces/portals/guest_workflows/sdk.py`. Reject read-only fields per verified scope.
- [ ] T025 [US3] Add separate edit and extension forms in `src/interfaces/portals/guest_workflows/presentation/`. Bind each typed confirmation to exact reviewed content.

## Phase 6: User Story 4 - Revoke Access (Priority: P2)

**Goal**: Distinguish accepted revocation requests from verified termination.
**Independent test**: Mock approved method and reconciliation results. Reject unsupported semantics and uncertain success.

### Tests

- [ ] T026 [US4] Extend `tests/contract/web_portal/test_guest_authorizations_api.py` for approved revocation, response interpretation, state reconciliation, and no automatic retry.
- [ ] T027 [US4] Extend `tests/integration/web_portal/test_guest_authorizations.py` and `tests/e2e/web_portal/test_guest_authorizations.py` for exact confirmation, cancellation, denied access, unknown termination, and failed audit.

### Implementation

- [ ] T028 [US4] Add only the verified revoke and reconciliation methods in `src/interfaces/portals/guest_workflows/sdk.py`. Do not infer termination from DELETE success or assume `minutes=0` semantics.
- [ ] T029 [US4] Add revoke review and explicit result states in `src/interfaces/portals/guest_workflows/presentation/`. Require an approved typed word and show unverified termination as unknown.

## Phase 7: User Story 5 - Search and Import (Priority: P3)

**Goal**: Search permitted clients and submit only a reviewed bounded batch.
**Independent test**: Mock search and row outcomes. Check all approved boundaries and stop conditions.

### Tests

- [ ] T030 [US5] Add CSV tests in `tests/unit/web_portal/test_guest_authorization_import.py`. Enforce "Exactly one final outcome per row", approved limits, encoding, headers, cells, duplicate scope/MAC pairs, and changed-preview rejection.
- [ ] T031 [US5] Extend `tests/contract/web_portal/test_guest_authorizations_api.py` for permitted returned search fields, sequential calls, rate limits, unknown writes, and no scope fallback.
- [ ] T032 [US5] Extend `tests/integration/web_portal/test_guest_authorizations.py` and `tests/e2e/web_portal/test_guest_authorizations.py` for search, zero-write preview, batch confirmation, partial outcomes, and audit failure.

### Implementation

- [ ] T033 [US5] Add bounded parsing and ordered row transitions in `src/interfaces/portals/guest_workflows/imports.py`. Enforce "Changed content or scope invalidates confirmation".
- [ ] T034 [US5] Add scoped client reads in `src/interfaces/portals/guest_workflows/sdk.py`. Search only verified returned fields and never infer guest authorization from client presence.
- [ ] T035 [US5] Add import preview and submission handlers in `src/interfaces/portals/guest_workflows/presentation/`. Apply "Approved byte, row, header, encoding, and cell bounds apply" before unbounded parsing.
- [ ] T036 [US5] Add stop and audit outcomes in `src/interfaces/portals/guest_workflows/imports.py`. Stop later rows after 429, unknown writes, or audit failure and never repeat uncertain writes.

## Phase 8: Cross-Cutting Validation

- [ ] T037 Verify masking, injection-safe rendering, zero direct HTTP fallback, and all denied/canceled cases in `tests/integration/web_portal/test_guest_authorizations.py`. Exclude tokens, names, email addresses, raw payloads, and complete MAC addresses from logs.
- [ ] T038 Verify all interactive labels, stable test IDs, and failure artifacts in `tests/e2e/web_portal/test_guest_authorizations.py`.
- [ ] T039 Write the approved operator guide in `documentation/guest-authorizations.md` and a unique fragment under `changelog.d/`. Document supported workflows, limits, rights, and recovery without changing the shared changelog.
- [ ] T040 Run the applicable checks in `design/quickstart.md`. Record exact commands, counts, results, and remaining limitations in the implementation PR before requesting review.

## Dependencies & Execution Order

```text
T001-T004 decisions -> T005 contracts -> T006 ownership
-> T007-T009 foundation -> US1 -> US2 -> US3 -> US4 -> US5
-> T037-T040 validation
```

The decision tasks can collect evidence independently, but this assignment executes serially.
T007-T009 and every story require all G1-G5 evidence first.
Within each story, tests must fail for the missing behavior before implementation, then pass afterward.
US2-US5 use US1 scope selection. Their independent tests supply fictional scopes instead of executing earlier UI journeys.
US3, US4, and US5 do not require each other's behavior, but run serially to avoid shared-file conflicts.
US5 imports require the confirmed grant and outcome contract from US2.
T037-T040 require all selected story increments.

## Parallel Execution Examples

No parallel execution is authorized in this assignment.
US1 contract, integration, and browser files are distinct, but execute T010-T016 serially.
For US2, US3, US4, and US5, shared SDK, access, and presentation files prohibit concurrent edits.
Do not apply the old task list's parallel markers to these shared files.

## Implementation Strategy

Complete the planning PR and stop. Do not start T001-T040 as product implementation in this session.
A later authorized implementation first obtains decisions and verifies evidence.
Its first portal increment is US1 only after all gates pass, including CSV and audit gates.
Add grant, edit/extension, revoke, and import as separately reviewed increments in the stated order.
The existing offline projection is not a reason to bypass a missing approval.

## Requirement Coverage

| Requirements | Tasks |
| --- | --- |
| FR-001, FR-002, SC-007 | T006, T008, T040 |
| FR-003, FR-004, SC-001 | T001-T009, T012, T016 |
| FR-005, FR-006, SC-003 | T010-T016 |
| FR-007 | T031, T032, T034 |
| FR-008, FR-009, FR-010, SC-002 | T017-T025, T027, T032, T035 |
| FR-011, FR-012, SC-005 | T018, T021, T026-T029, T031, T036 |
| FR-013, FR-014, FR-015, FR-016, SC-004 | T003, T030-T036 |
| FR-017, FR-018 | T002, T004, T009, T021, T027, T036, T037 |
| FR-019, FR-020, SC-006 | T007-T008, T012, T018, T023, T027, T032, T037-T040 |
