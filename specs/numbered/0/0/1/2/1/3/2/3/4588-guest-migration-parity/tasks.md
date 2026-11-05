# Tasks: Full guest migration parity

**Input**: `specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity/`.

**Prerequisites**: [spec](spec.md), [plan](plan.md), [research](design/research.md),
[data model](design/data-model.md), [API](design/contracts/api.md),
[parity](design/contracts/parity.md), and [E2E](design/contracts/e2e.md).

**Tests**: Required. Write failing unit, contract, integration, and browser tests before the corresponding behavior.
All tests use fictional data and prohibit live Mist requests.

These 40 tasks describe future implementation and acceptance.
All remain unchecked. This planning change does not deliver or approve them.
T001 repeats baseline inspection when implementation starts, rather than treating current planning evidence as permanent.
Keep #4278 as the implementation issue. Create no duplicate implementation issue.

## Format and path conventions

`G` means `src/interfaces/portals/guest_authorizations/`.
`U`, `C`, `I`, and `E` mean the planned guest test directories under unit, contract, integration, and E2E web portal roots.
These aliases shorten descriptions. Each task also names its complete primary path.
T007 must validate the proposed destinations before file creation.
Do not enlarge a noncompliant parent, add an alias, or weaken a hierarchy baseline.
Decision tasks must record an approver and evidence, not guess an answer.

## Phase 1: Setup and decision gates

- [ ] T001 Re-pin source and target before implementation in `design/research.md` and `design/contracts/parity.md`. Compare source history, all current PRs, and every inventory row. Depends on no task. Acceptance: TEST-030/032 includes exact commits, changed features, license notices, and measured coverage.
- [ ] T002 Record D1 and D7 approval in `design/research.md`. Define read/write access, permitted guest fields, exact scope, actor evidence, and confirmation words. Depends on T001. Acceptance: TEST-020/021 has approved alternatives and negative cases. Block live reads and writes until approved.
- [ ] T003 Verify D2 in `tests/contract/web_portal/guest_authorizations/test_sdk.py` and `design/contracts/api.md`. Inspect pinned SDK transport/retries and schema. Resolve creation, path MAC, WLAN identity, writable fields, duration origin, zero-minute expiry, and DELETE observation. Depends on T001,T007. Acceptance: TEST-011/012/013/014/022/034 proves exact signatures and payloads, 4xx/429/5xx, and disabled unsupported behavior. Authoritative cloud semantics need approved evidence, not a mock assertion.
- [ ] T004 Record D3 in `design/research.md`. Approve CSV byte, row, field, concurrency, request, time, invalid-row, and duplicate rules. Depends on T001. Acceptance: TEST-018 has approved numeric limits and limit-1/limit/limit+1 cases. No import implementation before this decision.
- [ ] T005 Record D4 in `design/research.md` and `design/data-model.md`. Approve durable intent/outcome storage, privacy, retention, post-dispatch failure, restart, and reconciliation rules. Depends on T001,T002. Acceptance: TEST-024/025 defines verified persistence and backup shape. No write dispatch before approval.
- [ ] T006 Record D5 and D6 in `design/research.md` and `design/contracts/e2e.md`. Approve source-content styling within target chrome, comparator tolerances, excluded regions, and notification disposition. Depends on T001. Acceptance: TEST-027/028/034 has explicit difference rules and no accidental notification.
- [ ] T007 Validate ownership and bounded destinations in `plan.md`. Recheck PR #4208, `web_portal/app.py`, `web_portal/templates/base.html`, the existing projection, and all planned test roots. Depends on T001. Acceptance: TEST-030 reports counts and a compliant destination. Record separate structure remediation and touched block limits. Obtain handover before shared edits.
- [ ] T008 Reconcile shared app/store/dependencies in `design/data-model.md` and `plan.md`. Inspect existing transaction, locking, Redis, key, and health contracts. Depends on T001,T007. Acceptance: TEST-025/026/035 proposes no source database conversion, second database, service, token source, or dependency downgrade.
- [ ] T009 Preserve projection test evidence in `tests/unit/web_portal/guest_authorizations/test_read_model.py` before a move. Replace `tests/unit/web_portal/test_guest_authorization_read_model.py` only through an owned bounded move. Depends on T007. Acceptance: TEST-029 retains all 22 cases and exact shape. Document future class module/logger changes and update every caller without a shim.

## Phase 2: Foundational contracts

T002-T008 are decision and destination gates, not delivered infrastructure.
The task dependency table is authoritative for which gate blocks each action.
No live route or write becomes available merely because offline files exist.

## Phase 3: User Story 1 - Review the selected network (P1)

**Goal**: Safe scoped review inside the existing portal.
**Independent Test**: Mock two sites and their WLANs, then verify selection, review, search, and failures without any write.

- [ ] T010 [US1] Write shared-page route and navigation tests in `tests/integration/web_portal/guest_authorizations/test_review.py`. Define local assets, registered navigation, session reuse, and existing-page regression acceptance. Depends on T002,T006,T007,T008. Acceptance: TEST-001/026/035 fails before wiring exists.
- [ ] T011 [US1] Add the guest page and owned registration in `src/interfaces/portals/guest_authorizations/web/routes/review.py`, `web_portal/app.py`, and `web_portal/templates/base.html`. Depends on T010,T013. Acceptance: TEST-001/027 preserves shared chrome and exact scope. Do not register live data until D1 and read contracts pass.
- [ ] T012 [US1] Implement connection, site/WLAN discovery, filtering, and scope invalidation in `src/interfaces/portals/guest_authorizations/services/api_client.py` and `web/routes/review.py`. Depends on T002,T003,T010,T013,T019. Acceptance: TEST-002/003/004 rejects implicit org selection, unrelated org WLANs, failed assignments, and stale results.
- [ ] T013 [US1] Move and reuse the offline projection in `src/interfaces/portals/guest_authorizations/domain/read_model.py`. Add separate scope/observation validation in `domain/scope.py` and `domain/validation.py`. Remove the old module and update callers. Depends on T008,T009. Acceptance: TEST-029 exact public shape and unknown semantics remain unchanged. TEST-005/006 validates scope and observation behavior. Run all repository move gates.
- [ ] T014 [US1] Implement guest cards, statistics, search, refresh, and empty states in `src/interfaces/portals/guest_authorizations/web/templates/page.html` and `web/static/review.js`. Depends on T002,T006,T011,T012. Acceptance: TEST-005/006/007/033 covers every approved detail field, stable order, time boundaries, keyboard record access, and true-empty versus unavailable.
- [ ] T015 [US1] Complete review integration and browser acceptance in `tests/e2e/web_portal/guest_authorizations/test_review.py`. Depends on T014,T029. Acceptance: TEST-001 through TEST-007 and TEST-033 uses deterministic fixtures, stable selectors, zero writes, and retained failure evidence.

## Phase 4: User Story 2 - Manage one authorization (P2)

**Goal**: Approved, exact-scope grant, edit, extension, and revoke.
**Independent Test**: Mock every dispatch and observation, then prove wrong, canceled, stale, and denied operations send no write.

- [ ] T016 [US2] Write MAC, fields, duration, creation, and extension tests in `tests/unit/web_portal/guest_authorizations/test_validation.py` and `tests/contract/web_portal/guest_authorizations/test_mutations.py`. Depends on T002,T003,T007. Acceptance: TEST-009/010/011/012/013/022/034 covers every source preset, malformed values, read-only fields, and no implicit duration default.
- [ ] T017 [US2] Implement the offline-tested add dialog in `src/interfaces/portals/guest_authorizations/web/templates/add.html` and `web/static/changes.js`. Depends on T006,T010,T016,T020. Acceptance: TEST-009/010/011/034 preserves device/details/client relationships and disables unsupported fields. No dispatch path is enabled until T018/T024 pass.
- [ ] T018 [US2] Implement reviewed-change access and typed confirmation in `src/interfaces/portals/guest_authorizations/domain/scope.py` and `services/mutations.py`. Depends on T002,T003,T005,T013,T016,T030. Acceptance: TEST-020/021 binds actor, action, scope, payload, observation, and revision. Wrong, canceled, repeated, stale, or denied confirmation sends zero writes.
- [ ] T019 [US2] Write and implement exact-site read/search contracts in `tests/contract/web_portal/guest_authorizations/test_reads.py` and `src/interfaces/portals/guest_authorizations/services/api_client.py`. Depends on T002,T003,T007,T013. Acceptance: TEST-003/008/022 verifies client stats, pages, explicit arguments, status checks, bounded read retries, and no org fallback.
- [ ] T020 [US2] Implement connected-client search and selection in `src/interfaces/portals/guest_authorizations/web/static/clients.js`. Depends on T019,T010. Acceptance: TEST-008/012 supports MAC/hostname/IP/SSID, two-character guidance, debounce, stale results, selection, and unknown/read-only names.
- [ ] T021 [US2] Integrate confirmed grant and safe result refresh in `src/interfaces/portals/guest_authorizations/web/routes/changes.py`. Depends on T017,T018,T024,T029. Acceptance: TEST-009/021/023/033 performs one exact-scope write, validates observed results, and distinguishes failure from unknown.
- [ ] T022 [US2] Implement supported edit and extension in `src/interfaces/portals/guest_authorizations/web/templates/edit.html` and `web/routes/changes.py`. Depends on T016,T018,T024,T029. Acceptance: TEST-010/011/012/013 keeps MAC fixed, explains duration origin, and does not turn a detail edit into an unreviewed extension.
- [ ] T023 [US2] Implement verified revoke in `src/interfaces/portals/guest_authorizations/services/mutations.py` and `web/routes/changes.py`. Depends on T003,T018,T024,T029. Acceptance: TEST-014/022 tests cancel, deny, exact-scope DELETE or approved alternative, ineffective success status, timeout, and unknown result.
- [ ] T024 [US2] Implement shared dispatch/outcome/reconciliation in `src/interfaces/portals/guest_authorizations/services/mutations.py` and `tests/integration/web_portal/guest_authorizations/test_changes.py`. Depends on T003,T005,T016,T018,T030. Acceptance: TEST-021/022/023/024 never retries an ambiguous write, broadens scope, or invents success/expiry. Verify SDK retry configuration explicitly.

## Phase 5: User Story 3 - Review and import CSV (P2)

**Goal**: Bounded, confirmed batch changes with complete row accounting.
**Independent Test**: Use mixed valid, invalid, duplicate, unauthorized, failed, unknown, and unstarted rows with no live cloud request.

- [ ] T025 [US3] Write parser/template tests and implementation in `tests/unit/web_portal/guest_authorizations/test_imports.py` and `src/interfaces/portals/guest_authorizations/services/imports.py`. Depends on T003,T004,T007,T016. Acceptance: TEST-015/016/018 covers ten source headers, aliases, two fictional examples, quoting, newlines, BOM/CRLF, formula strings, invalid rows, and approved field limits. Report every input row.
- [ ] T026 [US3] Implement unambiguous scope/duplicate validation in `src/interfaces/portals/guest_authorizations/services/imports.py` and `tests/contract/web_portal/guest_authorizations/test_imports.py`. Depends on T002,T003,T004,T012,T025. Acceptance: TEST-017/018 resolves IDs within scope, rejects ambiguous names, follows approved duplicate policy, and binds file/map revision.
- [ ] T027 [US3] Implement download, file selection, bounded preview, errors, and batch confirmation in `src/interfaces/portals/guest_authorizations/web/templates/import.html` and `web/routes/imports.py`. Depends on T006,T010,T018,T025,T026,T029. Acceptance: TEST-015/016/017/021/033 preserves first-five visual preview and full row accounting. Replacing or closing a file invalidates confirmation.
- [ ] T028 [US3] Implement bounded batch dispatch, progress, outcomes, cancel, and recovery in `src/interfaces/portals/guest_authorizations/services/imports.py` and `tests/integration/web_portal/guest_authorizations/test_imports.py`. Depends on T004,T005,T024,T026,T027,T030. Acceptance: TEST-018/019/021/023 partitions success, rejection, unknown, invalid, duplicate, and unstarted rows. No blind replay or hidden partial success.

## Phase 6: User Story 5 - Shared operation and recovery (P3)

**Goal**: Truthful shared-app behavior with durable approved coordination.
**Independent Test**: Simulate failures and restart using isolated existing-store fixtures.
These cross-cutting tasks execute earlier where the dependency graph requires them.

- [ ] T029 [US5] Implement safe state/error reporting in `src/interfaces/portals/guest_authorizations/web/routes/review.py`, `web/static/review.js`, and `tests/integration/web_portal/guest_authorizations/test_errors.py`. Depends on T002,T003,T010,T013. Acceptance: TEST-023/033 distinguishes unavailable, invalid, denied, stale, rejected, rate limited, unknown, and empty results. Escape external values and preserve actionable errors.
- [ ] T030 [US5] Implement approved audit intent/outcome and recovery in `src/interfaces/portals/guest_authorizations/services/audit.py` and `tests/integration/web_portal/guest_authorizations/test_audit.py`. Depends on T005,T007,T008,T013. Acceptance: TEST-024/025 enforces "Missing fields remain unknown", approved durable writes, retention, redaction, locking, before/after failure, and restart behavior. No second store.
- [ ] T031 [US5] Integrate shared health, configuration, dependency and deployment acceptance in `tests/integration/web_portal/guest_authorizations/test_deployment.py`. Change `compose.yml`, `requirements.txt`, `pyproject.toml`, or `deploy/.env.example` only if a verified requirement needs it and ownership permits. Depends on T007,T008,T011,T030. Acceptance: TEST-025/026/035 adds zero applications/databases/Compose groups and retains current health, ports, session ownership, and required status names.

## Phase 7: User Story 4 - Visual and functional parity (P1)

**Goal**: Paired original-versus-target evidence, not inferred equivalence.
**Independent Test**: Compare the pinned source and target with identical synthetic scenarios.
Source reference and difference-policy work begins through T001/T006. Target comparisons necessarily follow target implementation.

- [ ] T032 [US4] Write paired scenario fixtures in `tests/e2e/web_portal/guest_authorizations/conftest.py` and update `design/contracts/e2e.md`. Depends on T001,T006,T007. Acceptance: TEST-027/030 freezes clock, viewport, theme, locale, timezone, fonts, and data digests. All live sessions and unlisted external requests fail.
- [ ] T033 [US4] Implement functional browser and accessibility assertions in `tests/e2e/web_portal/guest_authorizations/test_workflows.py`. Depends on T015,T021,T022,T023,T028,T031,T032. Acceptance: TEST-008 through TEST-028, TEST-033/034 covers each control, state, stable selector, keyboard action, focus, label, and announcement.
- [ ] T034 [US4] Capture and compare every VIS-001 through VIS-015 pair in `tests/e2e/web_portal/guest_authorizations/test_visual.py`. Depends on T006,T032,T033. Acceptance: TEST-027/028 compares declared viewports and approved difference regions. Retain full source/target screenshots, hashes, failure traces, and actual comparator results. Do not claim target parity when evidence is absent.

## Phase 8: Cross-cutting release and operator approval

- [ ] T035 Run all applicable gates for the feature file set and record exact results in `design/quickstart.md`. Depends on T015,T021,T022,T023,T028,T031,T033,T034. Acceptance: TEST-030/035 includes unit/contract/integration/browser, lint, types, format, complexity, security, docstrings, projection move, routing/hierarchy, and existing portal regressions. No skipped or stale check counts as pass.
- [ ] T036 Write the integrated operator guide in `documentation/guest-authorizations.md`, owned `README.md` links, and one unique `changelog.d/` fragment. Depends on T021,T022,T023,T028,T031,T034. Acceptance: TEST-031/032 documents supported contracts, approved visual/safety deviations, source credit/license/change notices, and noncommercial/share-alike obligations. Do not invent a relicense.
- [ ] T037 Audit requirement/task/test traceability in `analysis.md` and `design/contracts/parity.md`. Depends on T035,T036. Acceptance: TEST-030 gives measured row/requirement/task/test counts, zero missing dispositions, zero unmapped requirements, and truthful gate status.
- [ ] T038 Perform final original-versus-target review in `design/contracts/parity.md` and `design/contracts/e2e.md`. Depends on T034,T037. Acceptance: TEST-027/030 records every row's executed result and approved difference against exact commits. Reject missing or unverified evidence.
- [ ] T039 Rehearse cutover, private backup verification, restart, and return to offline mode in `design/quickstart.md`. Depends on T005,T031,T035,T036,T038. Acceptance: TEST-024/025/031/035 proves complete approved backup shape and preserves other data. No live cloud change without separate exact user authorization.
- [ ] T040 Obtain operator release approval in `design/quickstart.md` and the implementation PR for #4278. Depends on T002,T003,T004,T005,T006,T037,T038,T039. Acceptance: TEST-031/035 records approvals, functional/visual evidence, revision, recovery, and outstanding limitations. A planning PR is not release approval.

## Dependencies & Execution Order

The explicit `Depends on` lists are the graph, not task number order.
T007 precedes T003 because contract tests need an approved bounded destination.
T030 precedes T018, and T018 precedes T024. T024 precedes dispatch integration.
T019 precedes T012 and T020. There is no dependency cycle.
Read-only work must pass its own access and contract gates even though it sends no write.
US2 and US3 use common dispatch and audit machinery, but tests can exercise each independently with synthetic fixtures.
US4 is P1 evidence work. Its final target comparison follows implementation because no target guest UI exists today.

## Requirement coverage

| Requirement | Task IDs | Acceptance family |
| --- | --- | --- |
| FR-001 | T010,T011,T015 | TEST-001 |
| FR-002 | T002,T012 | TEST-002 |
| FR-003 | T003,T012,T019 | TEST-003 |
| FR-004 | T012,T029 | TEST-004 |
| FR-005 | T013,T014,T015 | TEST-005 |
| FR-006 | T013,T014 | TEST-006 |
| FR-007 | T002,T014 | TEST-007 |
| FR-008 | T019,T020,T033 | TEST-008 |
| FR-009 | T016,T017,T021 | TEST-009 |
| FR-010 | T005,T016,T017,T022,T030 | TEST-010 |
| FR-011 | T003,T016,T022,T025 | TEST-011 |
| FR-012 | T003,T016,T020,T022 | TEST-012 |
| FR-013 | T003,T016,T022 | TEST-013 |
| FR-014 | T003,T023,T024 | TEST-014 |
| FR-015 | T025,T027 | TEST-015 |
| FR-016 | T025,T026,T027 | TEST-016 |
| FR-017 | T002,T026,T027 | TEST-017 |
| FR-018 | T004,T025,T026,T028 | TEST-018 |
| FR-019 | T027,T028 | TEST-019 |
| FR-020 | T002,T018 | TEST-020 |
| FR-021 | T002,T018,T024,T028 | TEST-021 |
| FR-022 | T003,T019,T024 | TEST-022 |
| FR-023 | T024,T029 | TEST-023 |
| FR-024 | T005,T024,T030 | TEST-024 |
| FR-025 | T008,T030,T031 | TEST-025 |
| FR-026 | T008,T010,T031 | TEST-026 |
| FR-027 | T006,T032,T034,T038 | TEST-027 |
| FR-028 | T006,T033,T034 | TEST-028 |
| FR-029 | T009,T013 | TEST-029 |
| FR-030 | T001,T032,T035,T037,T038 | TEST-030 |
| FR-031 | T036,T039,T040 | TEST-031 |
| FR-032 | T001,T036 | TEST-032 |
| FR-033 | T012,T014,T021,T027,T029 | TEST-033 |
| FR-034 | T003,T006,T017,T033 | TEST-034 |
| FR-035 | T031,T035,T039,T040 | TEST-035 |

## Parallel opportunities

Do not assign two agents the same file or shared integration surface.
After T001, D1/D3/D4/D5 approvals can be gathered independently, but use separate evidence records before integration.
After foundation acceptance, read-only fixture review and single-change unit tests can proceed on distinct test files.
After T024, CSV unit/contract work can proceed independently of edit/revoke browser acceptance.
After T032, source capture and target accessibility review can proceed independently on separate evidence outputs.
No task uses a `[P]` marker because file ownership and decision evidence are not yet assigned.

## Implementation strategy

First preserve and refactor the offline projection with its existing tests.
Then deliver independently tested read-only review after approved access and contracts.
Then add approved single-guest changes and audited dispatch.
Then add reviewed CSV execution.
Finish with paired visual review, complete regressions, documentation, recovery rehearsal, and operator approval.
Do not reduce the full migration scope to the offline projection when reporting completion.
Do not enable a gate by choosing an unapproved policy or by treating a mock as cloud evidence.
