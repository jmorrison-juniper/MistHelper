# Feature Specification: Main file decomposition wave 2 (9 targets, serial)

**Feature Branch**: `[193-main-decomposition-wave-2]`  
**Created**: 2026-05-26  
**Status**: Draft  
**Input**: User description: "Create a new SpecKit feature specification in MistHelper (Python repo) for a serial class decomposition/refactor initiative."

## Problem Statement

`MistHelper.py` remains oversized and tightly coupled in specific class groups that were not addressed in wave 1. This slows safe change delivery, increases regression risk, and makes onboarding harder for maintainers. A controlled, serial decomposition wave is required to reduce complexity while preserving runtime behavior and output parity.

## Goals

- Decompose and relocate exactly 9 target groups from `MistHelper.py` into semantically correct `src/` modules.
- Execute work strictly serially (one target group at a time), in the exact easiest-to-hardest order defined in this specification.
- Preserve behavior parity for menu flows, API outputs, and output backends (CSV, SQLite, polyglot).
- Enforce hard quality gates per phase: tests and automated checks must pass before proceeding.
- Reduce coupling risk by explicitly controlling import boundaries and runtime dependencies.
- Complete all post-refactor documentation synchronization and validation.

## Non-Goals

- Do not include `GlobalImportManager` in this wave.
- Do not alter user-visible feature scope, menu semantics, or output schema contracts.
- Do not redesign unrelated subsystems outside the 9 listed target groups.
- Do not batch multiple target groups into a single completion gate.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute predictable serial decomposition (Priority: P1)

As a maintainer, I need the refactor to proceed one target group at a time in a fixed order so that risk remains bounded and rollback/debug scope is clear.

**Why this priority**: Serial sequencing and hard gates are the core control mechanism for this initiative.

**Independent Test**: Can be fully tested by completing one phase and verifying that no subsequent phase starts unless all phase quality checks pass.

**Acceptance Scenarios**:

1. **Given** phase N is active, **When** extraction and test updates are complete, **Then** phase N only closes if all required checks pass.
2. **Given** any phase check fails, **When** the pipeline is executed, **Then** progression to phase N+1 is blocked until remediation is complete.

---

### User Story 2 - Preserve behavioral parity during decomposition (Priority: P2)

As an operator, I need menu behavior and data outputs to remain unchanged so refactoring does not alter operations.

**Why this priority**: Operational trust depends on no regressions in runtime behavior.

**Independent Test**: Can be tested by comparing pre/post behavior for affected menus and outputs for each phase.

**Acceptance Scenarios**:

1. **Given** a refactored phase, **When** existing menu paths are run, **Then** behavior and responses remain equivalent.
2. **Given** existing export/report operations, **When** outputs are generated post-phase, **Then** API-driven data and backend output behavior remain parity-aligned.

---

### User Story 3 - Finalize and validate documentation integrity (Priority: P3)

As a project owner, I need docs and wiki content updated and validated so the architecture and operating guidance remain accurate.

**Why this priority**: Refactor value is reduced if documentation drifts from implementation.

**Independent Test**: Can be tested by running a completeness audit against required documents and confirming no stale references remain.

**Acceptance Scenarios**:

1. **Given** all 9 phases are complete, **When** documentation updates are performed, **Then** README, CHANGELOG, Mermaid/architecture docs, and wiki pages are synchronized.
2. **Given** doc validation checklist is executed, **When** inconsistencies are found, **Then** final completion is blocked until corrected.

### Edge Cases

- A target group has hidden dependencies on non-target code paths that are only triggered during runtime.
- Circular import risk appears after moving code to `src/` modules.
- Runtime coupling remains through implicit shared state or side effects in `MistHelper.py`.
- Unit tests pass but backend output parity drifts in one backend (CSV, SQLite, or polyglot).
- Documentation updates are completed in repo files but wiki synchronization is incomplete.

## Requirements *(mandatory)*

### Scope Constraints (Mandatory)

- **SCOP-001**: This wave MUST exclude `GlobalImportManager`.
- **SCOP-002**: This wave MUST include exactly these 9 target groups and no others:
  1. `SiteInventoryHealthAnalyzer + SiteAnalyticsConfigurator`
  2. `TroubleshootUtils + SSHRunnerManager`
  3. `WAN2MigrationManager + WANProbeDeviceOverrideManager`
  4. `SiteConfigManager`
  5. `SiteExportUtils`
  6. `OrgDeviceInventorySummary`
  7. `GatewayExportUtils`
  8. `ServicePingManager`
  9. `PacketCaptureManager`
- **SCOP-003**: Execution model MUST be serial, one target group at a time, in the exact order above.

### Functional Requirements

- **FR-001**: For each phase, logic for the active target group MUST be extracted/refactored from `MistHelper.py` into semantically correct `src/` modules.
- **FR-002**: For each phase, unit tests MUST be created or updated before the phase can be marked complete.
- **FR-003**: For each phase, automated quality gates and tests MUST pass before moving to the next phase.
- **FR-004**: If any test or quality gate fails in a phase, the failure MUST be fixed in that same phase before progression.
- **FR-005**: Menu behavior MUST remain unchanged for all affected operations during and after each phase.
- **FR-006**: API output behavior MUST remain unchanged for all affected operations during and after each phase.
- **FR-007**: Output backend behavior for CSV, SQLite, and polyglot paths MUST remain unchanged during and after each phase.
- **FR-008**: Each phase MUST have explicit acceptance criteria and a completion checklist.
- **FR-009**: The initiative MUST include explicit controls to prevent circular imports.
- **FR-010**: The initiative MUST include explicit controls to prevent runtime coupling between `MistHelper.py` and extracted `src/` modules.
- **FR-011**: After all phases, README and CHANGELOG MUST be updated for accuracy and completeness.
- **FR-012**: After all phases, Mermaid diagrams and architecture documentation MUST be updated for accuracy and completeness.
- **FR-013**: After all phases, GitHub wiki pages MUST be synchronized with repository documentation and validated.
- **FR-014**: Final completion MUST require passing a documentation validation checklist and completeness audit.

### Ordered Serial Phase Plan (Mandatory Sequence)

| Phase | Target Group | Relative Difficulty | Dependency Rule |
| - | - | - | - |
| 1 | SiteInventoryHealthAnalyzer + SiteAnalyticsConfigurator | Easiest | Must complete before Phase 2 |
| 2 | TroubleshootUtils + SSHRunnerManager | Easy-Medium | Must complete before Phase 3 |
| 3 | WAN2MigrationManager + WANProbeDeviceOverrideManager | Medium | Must complete before Phase 4 |
| 4 | SiteConfigManager | Medium | Must complete before Phase 5 |
| 5 | SiteExportUtils | Medium | Must complete before Phase 6 |
| 6 | OrgDeviceInventorySummary | Medium-Hard | Must complete before Phase 7 |
| 7 | GatewayExportUtils | Hard | Must complete before Phase 8 |
| 8 | ServicePingManager | Hard | Must complete before Phase 9 |
| 9 | PacketCaptureManager | Hardest | Final decomposition phase |

### Per-Phase Acceptance Criteria (Applies to Every Phase)

A phase is accepted only when all of the following are true:

- Target group extraction/refactor is complete and isolated to appropriate `src/` module boundaries.
- `MistHelper.py` retains only required orchestration/compatibility logic for that target group.
- Unit tests for the target group are present/updated and pass.
- Automated quality gates pass for changed scope.
- Menu behavior parity checks pass for impacted paths.
- API output parity checks pass for impacted paths.
- CSV, SQLite, and polyglot backend parity checks pass for impacted outputs.
- Circular import checks pass.
- Runtime coupling checks pass.

### Phase Completion Checklist (Run at End of Each Phase)

- [ ] Active phase target group matches required sequence.
- [ ] Extraction into semantically correct `src/` module(s) completed.
- [ ] Legacy logic duplication removed or intentionally bridged with documented rationale.
- [ ] Unit tests created/updated for refactored behavior.
- [ ] Regression/parity tests executed for menu and output behavior.
- [ ] Quality gates executed and passing.
- [ ] Circular import control checks executed and passing.
- [ ] Runtime coupling control checks executed and passing.
- [ ] Phase sign-off recorded before next phase starts.

### Global Regression & Parity Requirements

- **GR-001**: No user-visible menu navigation or behavior changes for impacted operations.
- **GR-002**: No API response interpretation changes that alter existing output meaning.
- **GR-003**: No output behavior drift in CSV, SQLite, or polyglot routes.
- **GR-004**: Any detected parity drift is a hard stop until corrected.

### Risk Controls: Imports and Runtime Coupling

- **RC-001**: Enforce one-way dependency direction from `MistHelper.py` orchestration into extracted modules.
- **RC-002**: Forbid extracted modules from importing high-level runtime entrypoint logic.
- **RC-003**: Validate import graph after each phase to detect circular dependencies.
- **RC-004**: Validate runtime coupling by checking for hidden shared mutable state or side-effect reliance.
- **RC-005**: Require explicit dependency boundaries and ownership notes for each extracted module.

### Finalization Requirements After Phase 9

- **FIN-001**: Update README and CHANGELOG to reflect decomposition outcomes and any maintainer-facing changes.
- **FIN-002**: Update Mermaid diagrams and architecture docs to match post-refactor structure.
- **FIN-003**: Synchronize GitHub wiki pages with updated repo documentation.
- **FIN-004**: Execute documentation validation checklist and completeness audit before final sign-off.

### Documentation Validation Checklist and Completeness Audit Criteria

Final completion requires all checks to pass:

- Documentation set coverage includes README, CHANGELOG, Mermaid/architecture docs, and wiki pages.
- No stale references to pre-refactor class ownership for the 9 target groups.
- Refactor phase outcomes and resulting module ownership are explicitly documented.
- All links/references resolve and point to current locations.
- Wiki and repository docs are semantically synchronized for the same topics.
- Validation evidence is captured and reviewable.

### Test Strategy

#### Per-Phase Test Strategy

Each phase must execute, at minimum:

1. Unit tests for extracted/refactored target group behavior.
2. Regression checks for impacted menu paths.
3. Parity checks for API output behavior.
4. Parity checks for CSV/SQLite/polyglot behavior.
5. Import/coupling risk checks.
6. Automated quality gates.

#### Global Test Strategy

- Maintain a running regression baseline across all completed phases.
- Re-run comprehensive automated quality gates at the end of each phase and after phase 9.
- Require zero unresolved test failures at every gate.
- Treat any parity regression as blocking work.

### Implementation Hints for speckit.plan and speckit.tasks

- Generate plan/tasks strictly in dependency order by phase number (1 through 9).
- For each phase, create tasks in this sequence: extract/refactor -> tests -> quality gates -> parity/regression checks -> import/coupling checks -> sign-off.
- Do not schedule downstream phase tasks until prior phase sign-off is complete.
- Include explicit rollback/remediation task paths for failed gates.
- Include final documentation synchronization and completeness audit as a separate terminal stage after phase 9.

### Key Entities *(include if feature involves data)*

- **Decomposition Phase**: A single gated execution unit tied to one target group and its required checks.
- **Target Group**: The exact class set assigned to a specific phase in the serial order.
- **Parity Baseline**: The expected unchanged behavior for menu operations, API outputs, and backend outputs.
- **Risk Control Record**: Evidence that circular import and runtime coupling controls passed for a phase.
- **Documentation Audit Record**: Evidence of final documentation synchronization and completeness validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 9 phases complete in the exact mandated order with no skipped or merged phases.
- **SC-002**: 100% of phase completion checklists are fully satisfied before the next phase begins.
- **SC-003**: 0 unresolved test or quality-gate failures remain at each phase boundary.
- **SC-004**: 0 accepted regressions in menu behavior, API output behavior, or CSV/SQLite/polyglot behavior.
- **SC-005**: 100% of required final documentation artifacts are updated, synchronized, and validated.
- **SC-006**: Circular import and runtime coupling controls pass in every phase.

## Assumptions

- Existing baseline behavior in `MistHelper.py` is the source of truth for parity.
- Existing automated quality gates and test infrastructure are available and executable per phase.
- Refactor can be partitioned by target group without changing external feature scope.
- Required maintainers/reviewers can review per-phase checkpoints before progression.
- Wiki synchronization access and process are available during finalization.

## Out of Scope Validation Notes

- No wave-2 work item may pull in `GlobalImportManager`.
- Any new decomposition candidate not listed in the 9 target groups must be deferred to a separate future wave.
