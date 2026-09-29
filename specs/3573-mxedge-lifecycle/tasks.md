# Tasks: Mist Edge Lifecycle Operation

**Input**: Design documents from `/specs/3573-mxedge-lifecycle/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/request-bodies.md`

**Tests**: Required. Unit tests prove confirmation guards, dry-run, OpenAPI request body shapes, claim-code redaction, CSV rows, and upgrade polling.

**Organization**: Tasks are grouped by user story so each step can be tested independently.

## Phase 1: Setup

- [X] T001 Create `specs/3573-mxedge-lifecycle/spec.md` with destructive scope and acceptance criteria. (delivered: specs/3573-mxedge-lifecycle/spec.md)
- [X] T002 Create `specs/3573-mxedge-lifecycle/plan.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/request-bodies.md`. (delivered: specs/3573-mxedge-lifecycle/plan.md)

## Phase 2: Foundation

- [ ] T003 Create package skeleton under `src/org/mxedge_lifecycle/` with `__init__.py`, `models.py`, `client.py`, and `operation.py`.
- [ ] T004 Create test skeleton under `tests/unit/org/mxedge_lifecycle/` with `__init__.py`.
- [ ] T005 Create `specs/3573-mxedge-lifecycle/wiring.md` with every fleet-contract section. Mark `MistHelper.py`, `OperationRegistry`, primary key strategy, README, and generated reference edits as deferred to the integration pull request.
- [ ] T006 Create `changelog.d/issue-3573-mxedge-lifecycle.md` with one `### Added` section and a bullet that names issue #3573.

## Phase 3: User Story 1 - Claim (Priority: P1)

- [ ] T007 [US1] Add model tests that assert `claimOrgMxEdge` body is `{"code": "..."}` and that the redacted log row never stores the code.
- [ ] T008 [US1] Implement claim request creation and claim-code redaction in `models.py`.
- [ ] T009 [US1] Implement the client method that calls `mistapi.api.v1.orgs.mxedges.claimOrgMxEdge` with action logs.
- [ ] T010 [US1] Implement operation prompt handling for `CLAIM`, wrong confirmation, and dry-run.

## Phase 4: User Story 2 - Assign and unassign (Priority: P2)

- [ ] T011 [US2] Add model tests for assign body `mxedge_ids` plus `site_id` and unassign body `mxedge_ids`.
- [ ] T012 [US2] Implement assign and unassign request creation in `models.py`.
- [ ] T013 [US2] Implement client methods for `assignOrgMxEdgeToSite` and `unassignOrgMxEdgeFromSite`.
- [ ] T014 [US2] Implement operation prompt handling for `ASSIGN`, `UNASSIGN`, wrong confirmation, and dry-run.

## Phase 5: User Story 3 - Bounce data ports (Priority: P3)

- [ ] T015 [US3] Add model tests for bounce body `ports` and empty-port refusal.
- [ ] T016 [US3] Implement bounce request creation in `models.py`.
- [ ] T017 [US3] Implement client method for `bounceOrgMxEdgeDataPorts`.
- [ ] T018 [US3] Implement operation prompt handling for `BOUNCE`, wrong confirmation, and dry-run.

## Phase 6: User Story 4 - Upgrade and poll status (Priority: P4)

- [ ] T019 [US4] Add model tests for upgrade body shape and terminal status detection.
- [ ] T020 [US4] Add operation tests for polling completion and `UPGRADE_POLL_TIMEOUT_SECONDS` timeout.
- [ ] T021 [US4] Implement upgrade request creation and poll result modeling in `models.py`.
- [ ] T022 [US4] Implement client methods for `upgradeOrgMxEdges`, `listOrgMxEdgeUpgrades`, and `getOrgMxEdgeUpgrade`.
- [ ] T023 [US4] Implement operation prompt handling for `UPGRADE`, dry-run, and status polling.

## Phase 7: Export and integration manifest

- [ ] T024 Implement `MxEdgeLifecycleLog.csv` writing under `data/` with one row per sent request or dry-run.
- [ ] T025 Complete `wiring.md` with menu entry `293`, registry comment, primary key strategy, category table update, and import line.
- [ ] T026 Verify the release note fragment exists.

## Phase 8: Validation and analysis

- [ ] T027 Run py_compile, ruff, black, mypy, pydocstyle, pytest, vulture, and interrogate for the package and tests.
- [ ] T028 Run SpecKit analysis. Repair each finding and commit the repair.

## Deferred integration tasks

- [ ] D001 Add `MxEdgeLifecycleOperation.run` import and dispatch in `MistHelper.py`. Deferred to the integration pull request because this branch must not edit `MistHelper.py`.
- [ ] D002 Add menu `293` to `src/utils/operation_registry.py` as `destructive`. Deferred to the integration pull request because this branch must not edit `OperationRegistry`.
- [ ] D003 Add primary key strategy records for `mxedge_lifecycle_log`. Deferred to the integration pull request because this branch must not edit `endpoint_primary_key_strategies.py`.
- [ ] D004 Regenerate menu references. Deferred to the integration pull request because this branch must not edit generated menu files.
