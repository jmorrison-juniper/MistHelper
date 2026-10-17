---
description: "Implementation tasks for the MistCircuitStats Redis dashboard migration"
---

# Tasks: MistCircuitStats Redis Dashboard Migration

**Input**: Design documents in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Important**: Resolve T001-T005 before product implementation. PR #4208 is the proposed canonical owner for overlapping WAN behavior, but it is not merged. Product tasks remain blocked while source behavior, license reuse, API contracts, Redis ownership, or feature ownership is unresolved. Use only confirmed owner paths in `contracts/ownership.md`. Keep product work in a separate implementation PR.

## Phase 1: Setup

**Purpose**: Record source evidence and ownership decisions before code changes.

- [ ] T001 [P] Complete the source review for pagination, enrichment, `SKIP_ENRICHMENT`, token rotation, API host, organization settings, and stale handling. Keep the verified `worker.py` facts and guide discrepancies in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/research.md`.
- [ ] T002 [P] Obtain a maintainer decision on CC BY-NC-SA 4.0 reuse terms. Record approved attribution and any reuse limits in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/research.md`. Copy no source code or assets without approval.
- [x] T003 Map the overview, gateway, port, peer, insight, collector, refresh store, request admission, and offline preview to the canonical #4208 proposal in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/contracts/ownership.md`. Record that #4208 is open and not merged. (delivered: `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/contracts/ownership.md`)

## Phase 2: Foundational

**Purpose**: Confirm shared API and cache contracts. These tasks block every product story.

- [ ] T004 [P] Verify the source request arguments, response fields, pagination, and SDK signatures in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/contracts/mist-api.md`. Resolve the reported insight mismatch for `rx_bps`, `tx_bps`, `port_id`, `interval=3600`, and a seven-day window before any insight work.
- [ ] T005 [P] Verify the existing Redis namespace, payload, owner, target TTL, refresh lease, and outage behavior. Resolve the guide's three-interval TTL against the implementation's 31-day TTL in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/contracts/redis-cache.md`. Record approved values and any assigned product path in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/contracts/ownership.md`.

**Checkpoint**: Wait for T001, T002, T004, T005, and owner approval for one unique scope and path before any product task starts.

## Phase 3: User Story 1 - Review Site WAN Status (Priority: P1)

**Goal**: Provide one canonical view for accepted multi-site gateway WAN status. Reuse the accepted #4195 or #4200 view where it meets the requirement.

**Independent Test**: With fictional records for two authorized sites, verify the selected site controls visible gateway, port, and peer data. Verify one canonical page and one collector serve each data set.

### Tests for User Story 1

- [ ] T006 [P] [US1] Add site and gateway ownership tests in `tests/unit/wan_performance/test_background_refresh.py`. Use mocked Mist responses and assert that each site and gateway retains its source identifiers.
- [ ] T007 [P] [US1] Add browser coverage for the canonical overview and details in `tests/e2e/web_portal/test_wan_performance_live.py`. Assert that filters show only authorized site data and do not create duplicate views.

### Implementation for User Story 1

- [ ] T008 [US1] After #4208 resolves and both feature owners approve one unique source-only behavior, implement it in the single path recorded by `contracts/ownership.md`. Do not create a competing WAN package, route, collector, cache, or API request.
- [ ] T009 [US1] Connect the approved source-only behavior to its assigned canonical view in the single path recorded by `contracts/ownership.md`. Depend on T008. Reuse shared MistHelper session and request admission. Do not add a second collector.

## Phase 4: User Story 2 - Judge Data Freshness (Priority: P2)

**Goal**: Show collection time and explicit current, stale, partial, failed, or unavailable state.

**Independent Test**: Use known synthetic timestamps and mocked Mist and Redis failures. Verify that the prior valid snapshot remains identifiable and no invalid snapshot replaces it.

### Tests for User Story 2

- [ ] T010 [P] [US2] Add TTL, schema, ownership, and malformed-payload tests in `tests/unit/wan_performance/test_refresh_store.py`. Verify each value against the approved `contracts/redis-cache.md` contract.
- [ ] T011 [P] [US2] Add refresh failure and partial-result tests in `tests/unit/wan_performance/test_background_refresh.py`. Verify that failed collection does not publish a partial replacement.
- [ ] T012 [P] [US2] Add browser checks for stale and unavailable states in `tests/e2e/web_portal/test_wan_performance_live.py`. Verify that stale or missing cache data never appears as live.

### Implementation for User Story 2

- [ ] T013 [US2] After #4208 resolves and the owners approve a unique cache requirement, extend the assigned cache path in `contracts/ownership.md`. Use the approved namespace, JSON schema, owner check, and TTL. Do not add another Redis adapter.
- [ ] T014 [US2] Publish a refresh only after full validation in the single path assigned by `contracts/ownership.md`. Depend on T013. Preserve the last valid snapshot when Mist, Redis, or pagination fails.
- [ ] T015 [US2] Return explicit stale, partial, failed, and unavailable states through the canonical view assigned by `contracts/ownership.md`. Depend on T014. Do not make fallback Mist requests from portal reads.

## Phase 5: User Story 3 - Review Offline Examples (Priority: P3)

**Goal**: Keep fictional offline examples available without Mist credentials or live requests.

**Independent Test**: Disable network access and open the offline preview. Verify that its fictional records are labeled and cannot satisfy a live-data request.

### Tests for User Story 3

- [ ] T016 [P] [US3] Verify synthetic labels and zero live requests in `tests/unit/wan_performance/test_offline_fixtures.py`.
- [ ] T017 [P] [US3] Verify offline preview labeling and separation from live routes in `tests/e2e/web_portal/test_wan_performance_offline.py`.

### Implementation for User Story 3

- [ ] T018 [US3] Reuse the #4208 offline preview after it has one confirmed owner. Change no preview file unless the owner assigns a unique source-only requirement and path in `contracts/ownership.md`.

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Verify safety and repository constraints across accepted stories.

- [ ] T019 [P] Verify cache and API failure, request admission, and secret redaction contracts in `tests/integration/wan_performance/test_background_refresh.py`.
- [ ] T020 Verify only assigned product and test paths changed in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/contracts/ownership.md`.
- [ ] T021 Verify no new app, service, Compose group, public port, Redis service, or database appears in `compose.yml`.
- [ ] T022 Verify all source assets and code reuse has maintainer approval and required attribution in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/research.md`.
- [ ] T023 Run the applicable tests, lint, type, security, documentation, and test-quality gates listed in `.github/copilot-instructions.md`. Record each exact command and result in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/quickstart.md`.
- [ ] T024 Record one separate incremental action to reduce the existing grandfathered `specs/` entries in `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/research.md`. Do not remove another feature's entry or change the baseline in this feature.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No product changes. T001-T002 record source evidence and rights. T003 records the #4208 proposal as canonical owner, not merged.
- **Foundational (Phase 2)**: T004-T005 depend on the source and ownership review. They block all product tasks.
- **User Story 1 (Phase 3)**: Depends on T001-T005. It owns the canonical accepted view and refresh entry point.
- **User Story 2 (Phase 4)**: Depends on T001-T005 and the assigned store from User Story 1.
- **User Story 3 (Phase 5)**: Depends on T003. Reuse the offline preview only if it has one confirmed owner.
- **Polish (Phase 6)**: Depends on every accepted implementation task.

### User Story Dependencies

- **User Story 1 (P1)**: Depends on T001, T002, T004, T005, and the owners' approval of one unique scope. It cannot duplicate #4195 or #4200.
- **User Story 2 (P2)**: Depends on the canonical refresh and store owner from User Story 1.
- **User Story 3 (P3)**: Can proceed independently after its owner is confirmed. Existing preview behavior may satisfy it without code.

### Parallel Opportunities

- T001 and T002 can run in parallel because source behavior review and license review produce separate evidence.
- After T003, API and Redis verification tasks T004 and T005 can run in parallel.
- Test tasks T006 and T007 can run in parallel after the ownership contract is approved.
- User Story 2 tests T010-T012 can run in parallel after the cache and route owners are confirmed.
- User Story 3 tests T016-T017 can run in parallel after offline preview ownership is confirmed.

## Parallel Example: User Story 1

```text
Task: T006 Add site and gateway ownership tests in tests/unit/wan_performance/test_background_refresh.py
Task: T007 Add browser coverage in tests/e2e/web_portal/test_wan_performance_live.py
```

## Implementation Strategy

### MVP First

1. Complete T001-T005. Stop if a maintainer has not assigned one owner or if the insight response contract remains unresolved.
2. Implement only a unique source behavior that the #4195 and #4200 owners confirm is not already planned or implemented.
3. Verify User Story 1 with mocked data before adding freshness states.
4. Reuse offline preview only when it remains distinct from live data.

### Incremental Delivery

1. Land the planning PR without product changes.
2. Open a separate implementation PR on #4220 after T001-T005 pass.
3. Add the canonical refresh path and its tests.
4. Add approved cache freshness and failure states.
5. Reuse existing offline preview behavior or make no change when it already passes.

## Notes

- `[P]` marks tasks that can run in parallel after their stated dependencies.
- `[US1]`, `[US2]`, and `[US3]` trace tasks to the user scenarios in `spec.md`.
- Product file paths remain unassigned. Do not create a competing package or modify a shared portal file until an owner assigns the path.
- Do not mark a task complete until its tests or evidence pass.
