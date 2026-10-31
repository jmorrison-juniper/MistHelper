# Tasks: Dynamic JVD Labs in the Operations Portal

**Input**: `specs/numbered/0/0/1/2/1/0/0/4/4504-dynamic-jvd-labs-planning/` (`spec.md`, `plan.md`, `design/`).

**Status**: Planning only. Issue #4504 authorizes no implementation and no live operation.
Every task below stays unchecked until a later, separately approved change delivers it and adds
an evidence note in the form `(delivered: path)`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with other tasks of the same phase.
- **[Story]**: The user story from `spec.md`.
- **[HUMAN]**: The task needs a maintainer decision or approval.
- **[LIVE]**: The task needs a live system and a separate approval. No agent runs it without that approval.
- **[ENGINE]**: The task changes the `vmm-topology-automation` repository, not MistHelper.

## Phase 1: Decisions and Evidence

- [ ] T001 [HUMAN] Refresh the framework and host evidence at current revisions and update `design/research.md`.
- [ ] T002 [HUMAN] Decide D-01 submodule path and pinned commit, and D-03 platform policy (POSIX-only live execution or a cross-platform lock).
- [ ] T003 [HUMAN] Decide D-04 numeric limits: import size, YAML depth, key count, page size, poll interval, concurrency, job duration, retention.
- [ ] T004 [HUMAN] Decide D-05 approval words and lease bounds, and D-06 first release scope.

## Phase 2: Foundational (blocks every user story)

- [ ] T010 [ENGINE] Add a public typed service layer with versioned result models and error categories in `framework/src/vmm_topology/application/`.
- [ ] T011 [ENGINE] Add capability discovery and the paired engine, host, schema, and catalog compatibility check.
- [ ] T012 [ENGINE] Replace SQL coupling in the run, execution, probe, and allocation stores with semantic persistence ports.
- [ ] T013 [ENGINE] Add injected Mist, VMM, guest, and clock dependency interfaces and remove home-directory configuration reads from the public path.
- [ ] T020 Add `LabsRepository` and an ArangoDB transaction adapter in `src/interfaces/portals/labs/repository/` with verified indexes and explicit unavailability errors.
- [ ] T021 Add `LabsJobRunner` for durable jobs, owner proofs, worker coordination, and interrupted-job recovery.
- [ ] T022 Add `LabsApprovalService` that binds approvals to action, intent digest, target, backend identity, engine revision, lease, and budget.
- [ ] T023 [P] Prove ArangoDB concurrency for unique keys, snapshot transactions, and overlapping address-range admission against the supported deployment.
- [ ] T024 [P] Add private-download exclusion, backup and restore, retention, schema migration, and rollback rules for Labs records.
- [ ] T030 Map every required Mist endpoint to a working `mistapi` method in `src/interfaces/portals/labs/services/mist_adapter.py` and add SDK authentication, endpoint parity, failure safety, and redaction contract tests.
- [ ] T031 Add server-side VMM connection configuration, credential resolution, and a qualification check that runs from the actual application runtime.
- [ ] T032 Add the pinned submodule, the `framework/` runtime install, wheel resources, container delivery, source revision reporting, and rollback steps.
- [ ] T033 [HUMAN] Fix the reusable image workflow gap so the container build initializes the submodule, through an approved update or a host-local build.

## Phase 3: User Story 1 - Template, forms, preview (P1)

- [ ] T040 [US1] Add `LabsCatalogService` that lists versioned templates with compatibility data.
- [ ] T041 [US1] Register the Labs blueprint in `web_portal/app.py` and add the navigation entry in `web_portal/templates/base.html`.
- [ ] T042 [US1] Render parameter forms from the engine schema with field-level errors.
- [ ] T043 [US1] Render the topology preview, resource budget, and plan digest with no approval control.
- [ ] T044 [P] [US1] Unit tests for catalog listing, schema forms, and preview, including invalid parameters.
- [ ] T045 [P] [US1] Contract tests that pin the engine result models consumed by the portal.
- [ ] T046 [P] [US1] Browser test for catalog selection, parameter edit, and preview with `data-testid` hooks and a retained trace.

## Phase 4: User Story 2 - Import and composition (P1)

- [ ] T050 [US2] [ENGINE] Replace the fixed dual-hub roles with a composition model of supported JVD building blocks.
- [ ] T051 [US2] [ENGINE] Publish the building-block capability list with availability reasons.
- [ ] T052 [US2] Add bounded YAML and JSON import that rejects tags, anchor bombs, unknown keys, and executable content.
- [ ] T053 [US2] Add the composition page that offers only supported blocks.
- [ ] T054 [P] [US2] Rejection tests for oversize, malformed, deep, unknown-key, tag, and command-bearing files.
- [ ] T055 [P] [US2] Browser test for import rejection and composition preview.

## Phase 5: User Story 3 - Qualify and approve (P2)

- [ ] T060 [US3] Add read-only qualification and capability gates with `available`, `unavailable`, and `unverified` states.
- [ ] T061 [US3] Add approval proposal, typed confirmation, revocation, and recheck before each write.
- [ ] T062 [US3] Return the same 404 for foreign private proposals and jobs.
- [ ] T063 [P] [US3] Tests that change one bound value and expect invalidation, and a cross-browser reuse test.
- [ ] T064 [P] [US3] Browser test for qualification and approval, including a wrong approval word.

## Phase 6: User Story 4 - Deploy and monitor (P2)

- [ ] T070 [US4] [ENGINE] Implement full-scenario approval-bound apply, onboarding, and convergence.
- [ ] T071 [US4] Add deployment job creation, sanitized progress, and SSE with polling fallback.
- [ ] T072 [US4] Add bounded monitoring read models for inventory, VM and link state, logs, events, lease, and freshness.
- [ ] T073 [US4] Add uncertain-write reconciliation and `recovery-required` states.
- [ ] T074 [P] [US4] Restart tests, SSE disconnect tests, and concurrency tests on the real backend.
- [ ] T075 [P] [US4] Browser test for progress, monitoring, and recovery with screenshots.

## Phase 7: User Story 5 - Test, impair, restore (P3)

- [ ] T080 [US5] [ENGINE] Implement general lab traffic composition and retained assessment.
- [ ] T081 [US5] [ENGINE] Implement impairment profiles with strict bounds, permitted interfaces, prior-state capture, observed-profile verification, and restoration.
- [ ] T082 [US5] Add traffic, impairment, and restoration proposals and jobs.
- [ ] T083 [P] [US5] Tests for management-interface refusal, foreign qdisc refusal, and partial-write restoration.
- [ ] T084 [P] [US5] Browser test for impairment approval, restoration, and retained evidence.

## Phase 8: User Story 6 - Exact cleanup (P3)

- [ ] T090 [US6] [ENGINE] Implement complete lab cleanup with fresh ownership checks and independent deletion confirmation.
- [ ] T091 [US6] Add cleanup proposal, approval, and result pages that report outcomes only after verification.
- [ ] T092 [P] [US6] Tests with foreign resources that share the name prefix.
- [ ] T093 [P] [US6] Browser test for cleanup and the `uncertain` state.

## Phase 9: Polish and Release

- [ ] T100 [P] Add installed-package tests that load packaged resources from the wheel and the container.
- [ ] T101 [P] Add redaction tests for responses, logs, SSE, browser storage, and downloads.
- [ ] T102 [P] Update `README.md`, `documentation/`, `deploy/.env.example`, and add a `changelog.d/` fragment for the delivered feature.
- [ ] T103 Run the local gates in `.github/copilot-instructions.md` and record results in the delivery pull request.
- [ ] T104 [LIVE] [HUMAN] Separately approved isolated live acceptance of deployment, monitoring, traffic, impairment, restoration, and cleanup.
- [ ] T105 [LIVE] [HUMAN] Separately approved rollback and recovery drill.
- [ ] T106 [HUMAN] Release approval after T104 and T105 evidence.

## Dependencies

- T001 to T004 precede Phase 2.
- T010 to T013 precede T020 to T033 where a task uses an engine service.
- Phase 2 blocks Phases 3 to 8.
- Phase 3 precedes Phases 4 to 8. Phases 5 and 6 precede Phases 7 and 8.
- T050 and T051 precede T053. T070 precedes T071. T081 precedes T082. T090 precedes T091.
- Phase 9 follows the phases it covers. T104 and T105 precede T106.

## Requirement Traceability

| Requirement | Tasks | Verifying tasks |
| - | - | - |
| FR-001 | T011, T040 | T044 |
| FR-002 | T052 | T054 |
| FR-003 | T010, T042 | T044 |
| FR-004 | T050, T051, T053 | T055 |
| FR-005 | T010, T043 | T044, T046 |
| FR-006 | T011, T060 | T064 |
| FR-007 | T022, T061 | T063 |
| FR-008 | T022, T061 | T063 |
| FR-009 | T021, T071 | T074 |
| FR-010 | T012, T073 | T074 |
| FR-011 | T013, T031 | T101 |
| FR-012 | T062 | T063 |
| FR-013 | T072 | T075 |
| FR-014 | T061, T082, T091 | T083, T093 |
| FR-015 | T081 | T083 |
| FR-016 | T090 | T092 |
| FR-017 | T012, T020 | T023, T024 |
| FR-018 | T041 | T046 |
| FR-019 | T041, T061 | T064 |
| FR-020 | T032, T033 | T100 |
| FR-021 | T032 | T100 |
| FR-022 | T042, T046 | T046, T055, T064, T075, T084, T093 |
