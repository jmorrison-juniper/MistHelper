# Specification Analysis Report

**Date**: 2026-10-14
**Inputs**: [spec.md](spec.md), [plan.md](plan.md), [tasks.md](tasks.md), and the MistHelper constitution.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| A1 | Ambiguity | HIGH | `spec.md` FR-001, FR-002, FR-016; `plan.md` Product Code and Tests; `tasks.md` T003, T008-T009 | PR #4208 is mapped as the proposed canonical owner for shared WAN views and services, but it remains open. Issue #4195 is active. No standalone #4220 product path is approved. | Keep product tasks blocked until both feature owners confirm the mapping and assign any unique source behavior. |
| A2 | Underspecification | HIGH | `contracts/mist-api.md`; `contracts/ownership.md`; `tasks.md` T004 | The source insight implementation uses direct `requests.get` calls and manual token-header extraction. The source request uses `rx_bps`, `tx_bps`, `port_id`, `interval=3600`, and a seven-day window. The SDK response contract remains unproven. | Do not port direct HTTP or implement insights until an SDK contract test proves field, unit, time-window, and identity parity. |
| A3 | Security / provenance | MEDIUM | `spec.md` FR-014; `research.md` Decision 6; `tasks.md` T002, T022 | The source declares CC BY-NC-SA 4.0. Reuse rights and compatible attribution terms remain unconfirmed. | Copy no source code or assets. Record a maintainer decision before any reuse. Independently written code still requires provenance review. |
| A4 | Ambiguity | MEDIUM | `spec.md` FR-008; `research.md` Verified Source Implementation Facts; `contracts/redis-cache.md`; `tasks.md` T005 | The guide reports a three-interval TTL, or 900 seconds at the default interval. The implementation review reports 31 days. The target freshness limit and Redis lease remain undefined. | Do not adopt either source TTL. Complete T005 and approve the target expiry and owner behavior. |
| A5 | Constitution alignment | LOW | `plan.md` Constitution Check; `tasks.md` T024 | The existing process-folder debt is measured. The plan tracks a separate incremental reduction action and does not change the baseline. | Keep T024 separate from this feature's managed record. Do not remove another feature's entry. |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | T003, T006-T009 | Single view and owner gate |
| FR-002 | Yes | T003, T008-T009 | Only accepted, non-overlapping journeys |
| FR-003 | Yes | T011-T012, T014-T015 | Freshness and state labels |
| FR-004 | Yes | T011, T014 | Preserve last valid snapshot |
| FR-005 | Yes | T004, T009, T019 | SDK bounds and shared admission |
| FR-006 | Yes | T011-T015, T019 | Mist and Redis failure states |
| FR-007 | Yes | T005, T010, T013 | Namespace, owner, schema, TTL, and outage contract |
| FR-008 | Yes | T001, T005 | Verify interval and TTL |
| FR-009 | Yes | T001 | Verify each source setting |
| FR-010 | Yes | T004 | Verify source-to-SDK method parity |
| FR-011 | Yes | T004, T009 | Existing session and request admission |
| FR-012 | Yes | T021 | No added service or database |
| FR-013 | Yes | T016-T018 | Synthetic and live data remain separate |
| FR-014 | Yes | T002, T022 | License and provenance gate |
| FR-015 | Yes | T006-T007, T010-T012, T016-T017, T019, T023 | Required test evidence and gates |
| FR-016 | Yes | T003, T020 | One owner for each shared path |
| SC-001 | Yes | T003, T007-T009 | One portal and canonical view |
| SC-002 | Yes | T006-T007, T012 | Identity, collection time, and state |
| SC-003 | Yes | T003, T006-T009 | Accepted journeys and duplicate prevention |
| SC-004 | Yes | T011-T015, T019 | Mist, Redis, pagination, and partial failure |
| SC-005 | Yes | T016-T017, T019 | Mocked credentials and synthetic separation |
| SC-006 | Yes | T021 | No new application infrastructure |
| SC-007 | Yes | T002, T022 | Approved provenance before reuse |

## Constitution Alignment Issues

No blocking constitution conflict remains in the planning artifacts.

- The feature uses the managed `specs/live/` root.
- The process-folder guard data reports 795 direct children, 792 grandfathered entries, and three managed roots. The current counts are `live: 4`, `numbered: 1`, and `skills: 5`.
- The plan records this debt and T024 tracks separate incremental remediation.
- The plan prohibits a new service, database, port, unsupported direct HTTP transport, and unbounded Mist API requests.
- The ownership contract maps shared WAN behavior to the proposed #4208 owner, not to merged product behavior. No product code is part of the planning PR.

## Unmapped Tasks

None. T001-T023 map to a user story, a functional requirement, a success criterion, or a required safety gate. T024 maps to the constitution's process-folder debt requirement.

## Metrics

- **Functional requirements**: 16
- **Success criteria**: 7
- **Total requirements**: 23
- **Total tasks**: 24 (23 open, 1 complete)
- **Tasks by user story**: US1: 4, US2: 6, US3: 3
- **Requirement coverage**: 100% (23 of 23 requirements have one or more tasks)
- **Task format**: 24 task entries have unique sequential IDs T001-T024. Twenty-three remain open, and T003 is complete.
- **Ambiguity or underspecification count**: 3 (A1, A2, and A4)
- **Duplication count**: 1
- **Critical issues count**: 0

## Next Actions

Complete T001, T002, T004, and T005 before any product task. PR #4208 is an open proposal, not merged behavior. The active #4195 work and unresolved insight response contract prevent a safe standalone implementation. Do not copy source code or assets without maintainer approval. Keep this PR planning-only.
