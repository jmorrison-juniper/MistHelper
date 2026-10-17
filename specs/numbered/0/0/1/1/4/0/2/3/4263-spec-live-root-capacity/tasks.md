# Tasks: Bounded live timestamp records

**Input**: [Specification](spec.md), [plan](plan.md), and [design records](design/research.md).

**Prerequisites**: Separate implementation authorization, current ownership inventory, and the implementation gates below.

**Tests**: Required. Prove failing paths before implementing each process change.

**Organization**: Execute phases serially. No parallel markers apply to this request.
Each task remains unchecked until its delivered file and result are verified.
The planning artifacts do not satisfy these implementation tasks.

## Phase 1: Setup

**Purpose**: Establish the exact future file set and preserve ownership.

- [x] T001 Inventory current records, artifact counts, references, and open PR ownership in `design/contracts/migration.md`. (delivered: design/contracts/migration.md)
- [x] T002 Record approved source-to-destination paths, file sizes, SHA-256 hashes, and owner handovers in `design/contracts/migration.md`. (delivered: design/contracts/migration.md)
- [x] T003 Record the shared task-audit release prerequisite and exact implementation file set in `plan.md`. (delivered: plan.md)

Do not create a grouping directory in the full live root.
Do not start relocation without T002.

## Phase 2: Foundation

**Purpose**: Define deterministic fixture vectors and the unchanged numeric contract.

- [x] T004 Add timestamp vectors, calendar failures, range boundaries, duplicate names, and unchanged eight-level numeric vectors in `tests/guardrails/test_spec_route_contract.py`. (delivered: `tests/guardrails/test_spec_route_contract.py`; verified: focused suite, 49 passed)
- [x] T005 Add six-child fixtures at the live root, nested group, and terminal bucket in `tests/guardrails/test_process_folder_structure.py`. (delivered: tests/guardrails/test_process_folder_structure.py)
- [x] T006 Add independent worktree, missing selection, unsafe path, duplicate identity, and nested feature fixtures in `tests/guardrails/test_spec_route_contract.py`. (delivered: both guard test files; verified: focused suite, 49 passed)

T004 must pin exactly 17 timestamp digits, each between zero and four.
Test the supported UTC epoch range, malformed dates, and pre-1970 rejection.
T005 must prove each invalid tree fails with the path and examined count.
T006 must prove an explicit directory overrides persisted state without writing it.

## Phase 3: User Story 1 - Bounded creation (Priority: P1)

**Goal**: Generate valid grouped timestamp records without changing the numeric route.

**Independent Test**: Generate six records in an isolated fixture and reject the sixth child at each structural depth.

- [x] T007 [US1] Implement validated 17-digit timestamp routes through `Get-SpecRadixSegments` in `.specify/scripts/powershell/spec-route.ps1`. (delivered: .specify/scripts/powershell/spec-route.ps1)
- [x] T008 [US1] Validate destination absence, feature boundaries, and five-child capacity before writes in `.specify/scripts/powershell/create-new-feature.ps1`. (delivered: `.specify/scripts/powershell/create-new-feature.ps1`, `tests/guardrails/test_spec_route_contract.py`; verified: focused suite, 49 passed)
- [x] T009 [US1] Extend structural traversal and count reporting in `tests/guardrails/test_process_folder_structure.py` without changing its threshold or baseline. (delivered: tests/guardrails/test_process_folder_structure.py)
- [x] T010 [US1] Verify bounded feature-artifact generation and no partial output on failure in `tests/guardrails/test_spec_route_contract.py`. (delivered: tests/guardrails/test_spec_route_contract.py)

T009 must retain missing and malformed baseline failure tests.
Traverse structural groups only until a feature boundary.
Reject features beneath features explicitly.
Keep established feature artifact inventories unchanged and record their historical debt.
Require every newly generated directory, including artifact directories, to remain bounded.

## Phase 4: User Story 2 - Correct selection (Priority: P1)

**Goal**: Select the same record and tasks through all supported layouts.

**Independent Test**: Select numeric, direct timestamp, grouped timestamp, and bounded-design fixtures without changing another worktree.

- [x] T011 [US2] Resolve validated explicit directories and established or bounded design paths in `.specify/scripts/powershell/common.ps1`. (delivered: .specify/scripts/powershell/common.ps1)
- [x] T012 [US2] Preserve non-persisting read paths and actual supporting-artifact output in `.specify/scripts/powershell/check-prerequisites.ps1`. (delivered: .specify/scripts/powershell/check-prerequisites.ps1)
- [x] T013 [US2] Apply selected paths without shared pointer writes in `.specify/scripts/powershell/setup-plan.ps1`, `.specify/scripts/powershell/setup-tasks.ps1`, and `.specify/scripts/powershell/update-agent-context.ps1`. (delivered: .specify/scripts/powershell/setup-plan.ps1, .specify/scripts/powershell/setup-tasks.ps1, .specify/scripts/powershell/update-agent-context.ps1)
- [x] T014 [US2] Obtain a reviewed recursive task-discovery release from the canonical `misthelper-devtools` repository and update `requirements-dev.txt`. (delivered: pin to devtools v0.6.3 at `e8e093d205428b5503887267b6a9751fa7354be7`; verified: PRs [jmorrison-juniper/misthelper-devtools#73](https://github.com/jmorrison-juniper/misthelper-devtools/pull/73) and [jmorrison-juniper/misthelper-devtools#74](https://github.com/jmorrison-juniper/misthelper-devtools/pull/74) merged, tag points to the release commit)
- [x] T015 [US2] Verify valid and failing grouped task fixtures, established layouts, and design-role ambiguity in `tests/guardrails/test_spec_route_contract.py`. (delivered: public-audit tests for completed and open grouped records; verified: 51 route and structure tests passed, 24 canonical task-audit tests passed)

T014 required the canonical devtools owner and a reviewed release.
The owner merged the recursive audit fix and released v0.6.3.
The dependency pin uses the full release commit.
T015 must test a failing grouped task record, not only successful directory discovery.

## Phase 5: User Story 3 - Approved preservation (Priority: P2)

**Goal**: Move approved records without lost content, ownership, or references.

**Independent Test**: Verify the complete original manifest and exact approved reference patches after relocation.

- [x] T016 [US3] Add preservation, occupied-destination, unreadable-source, symlink, and failed-verification fixtures in `tests/guardrails/test_spec_route_contract.py`. (delivered: `tests/guardrails/test_spec_route_contract.py`; verified: focused suite, 49 passed)
- [x] T017 [US3] Relocate only owner-approved records from `specs/live/` using the complete map in `design/contracts/migration.md`. (delivered: design/contracts/migration.md)
- [x] T018 [US3] Update each approved selector and reference listed in `design/contracts/migration.md`, preserving unrelated narrative content. (delivered: specs/live/0/0/0/1/2/1/3/2/2/1/2/3/0/3/4/1/3/20261013-182828-fix-generated-control-labels/plan.md)
- [x] T019 [US3] Record file mapping, unchanged hashes, exact approved reference patches, owner evidence, and remaining historical debt in `design/contracts/migration.md`. (delivered: design/contracts/migration.md)
- [x] T020 [US3] Coordinate the Redis record relocation and rebased guard result with PR #4223 through the handover in `design/contracts/migration.md`. (verified: PR #4223 merged after its grouped-record commit and current-main route tests passed; see `analysis.md`)

T017 cannot run without owner handovers.
T020 followed the merged process implementation and the Redis record owner's handover.
Do not edit `specs/live/0/0/0/1/2/1/3/2/2/2/0/0/1/4/2/2/0/20261014-050510-mistcircuitstats-redis/` from this worktree.

## Phase 6: Documentation and Verification

**Purpose**: Document only verified behavior and publish complete evidence.

- [x] T021 Update path examples in `.specify/templates/plan-template.md`, `.specify/templates/tasks-template.md`, `.github/skills/speckit-specify/SKILL.md`, and `.github/agents/speckit.specify.agent.md`. (delivered: .specify/templates/plan-template.md, .specify/templates/tasks-template.md, .github/skills/speckit-specify/SKILL.md, .github/agents/speckit.specify.agent.md)
- [x] T022 Update the repository grouping rule in `.github/copilot-instructions.md` and add `changelog.d/issue-4263-live-timestamp-groups.md`. (delivered: .github/copilot-instructions.md, changelog.d/issue-4263-live-timestamp-groups.md)
- [x] T023 Run focused process, route, selection, canonical task-audit, prose, link, and changed-code gates from `design/quickstart.md`. (verified: checks and audit results are recorded; the audit reported unrelated findings; see `analysis.md`)
- [x] T024 Record final counts, preservation evidence, old-path search results, and CI results in `analysis.md` before claiming issue completion. (delivered: `analysis.md`; issue #4263 remains open pending review)

Inspect remaining skill, agent, context, CI, and documentation consumers during T001.
Add their exact affected paths to T003 before edits.
If a generic rule changes, update canonical `templates/agent-instructions/AGENTS.md` in `misthelper-devtools` first.
Do not revise the constitution unless the approved design changes a binding rule.

## Dependencies & Execution Order

| Tasks | Prerequisites |
| --- | --- |
| T001 | Implementation authorization and read-only PR inspection |
| T002, T003 | T001 |
| T004, T005, T006 | T003 |
| T007 | T004 |
| T008 | T005, T007 |
| T009 | T005, T006 |
| T010 | T008, T009 |
| T011 | T006, T010 |
| T012 | T011 |
| T013 | T012 |
| T014 | T003 and canonical owner assignment |
| T015 | T013, T014 |
| T016 | T002, T015 |
| T017 | T002, T010, T015, T016 |
| T018 | T017 |
| T019 | T018 |
| T020 | T019 and merged process implementation |
| T021, T022 | T019 |
| T023 | T021, T022 |
| T024 | T020, T023 and required CI results |

The table defines prerequisites, not parallel permission.
Execute one task at a time under the standing serial-work rule.

## Parallel Examples

For US1, route and structural fixtures could use separate files, but this request keeps them serial.
For US2, canonical tool work remains an external prerequisite, not a parallel local worker.
For US3, preserve one approved move set before starting the next.

## Implementation Strategy

The smallest useful process increment is US1 plus US2 with isolated fixtures.
It must not claim to unblock the Redis plan until US3 and its rebased checks pass.
Keep each failing prerequisite explicit.
Do not weaken the guard to deliver a partial result.

## Requirement Coverage

| Requirement | Tasks |
| --- | --- |
| FR-001 | T004, T007, T017 |
| FR-002 | T005, T008, T009, T010 |
| FR-003 | T004, T006, T008, T016 |
| FR-004 | T006, T011, T012, T013, T014, T015 |
| FR-005 | T005, T006, T009, T012, T015 |
| FR-006 | T001, T002, T016, T017, T019 |
| FR-007 | T018, T021, T022, T023 |
| FR-008 | T005, T009, T023 |
| FR-009 | T006, T011, T012, T013 |
| FR-010 | T001, T002, T020, T024 |
| FR-011 | Planning diff inspection, no implementation credit |

## Implementation Gates

The coordinator subsequently reported user authorization to continue beyond planning.
That authorization does not supply another owner's handover or a canonical tool release.
Start only the tasks whose prerequisites are satisfied.
Keep all relocation and integration tasks blocked until their evidence exists.

Evidence for all 24 implementation tasks is recorded on this PR branch and awaits review and merge.
T020 records the merged Redis handover in PR #4223.
T023 records all required feature-level validation. The repository-wide audit exits 1 on unrelated records, which remain unchanged.
T024 records the final counts, preservation proof, old-path search, and merged PR checks in `analysis.md`.
PR #4274 remains open and unmerged.
Issue #4263 remains open pending review.
The user separately authorized T017 through T019 for the single #4202 move before the remaining shared-tool and migration-fixture work.
This scoped exception does not authorize another move or complete those prerequisites.
Selection fixtures use the existing route-contract test file rather than an additional test module.
The focused suite passed 49 tests with PowerShell 7.6.7 on PATH.
Ruff passed, Black left both test files unchanged, and mypy reported no issues in two source files.
No planning or integration task is complete merely because a missed nested audit returned zero.
