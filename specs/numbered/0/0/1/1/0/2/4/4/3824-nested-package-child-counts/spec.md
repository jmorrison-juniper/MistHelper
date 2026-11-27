# Feature Specification: Nested Source Package Child Counts

**Feature Branch**: `refactor/3824-<slice-slug>`, one branch for each slice

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue 3824, "Refactor: reduce nested source package child counts"

**Record route**: `specs\numbered\0\0\1\1\0\2\4\4\3824-nested-package-child-counts`

**Measured base**: remote `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`

## Problem

The constitution limits each hierarchy level to five children. Principle I names this rule the Five-Item Rule. Some nested source directories on remote main hold more than five counted children. This record fixes the inventory, the owner of each violation, the order of remediation, and the gates for each change.

The guard `tests/guardrails/test_nested_package_structure.py` measures the state. It counts each direct Python module, except `__init__.py`, and each direct child directory that holds tracked Python files.

## Measured State

| Measure | Value | Remote check |
| - | - | - |
| Directories examined | 190 | C-09 |
| Violating directories | 33 | C-51 to C-83 |
| Total excess children | 236 | C-09 |
| Baseline entries | 33, each matching its measured count | C-08 |
| Violations owned by issue 3824 | 31 | Baseline `remediation_issue` |
| Violations owned by issue 4168 | 2, both in `juniper_rma` | Baseline `remediation_issue` |

## User Scenarios and Testing

### User Story 1 - Read the complete inventory (Priority: P1)

A maintainer reads one inventory. Each violating directory has one row. The row gives its count, its owner, its slice, and its holds.

**Why this priority**: The issue requires an inventory and one recorded remediation task for each violation.

**Independent Test**: Run `python -m pytest tests/guardrails/test_nested_package_structure.py -s -q`. The printed totals equal the totals in this record.

**Acceptance Scenarios**:

1. **Given** remote main at the measured base, **When** the guard runs, **Then** it reports 190 directories, 33 violations, and 236 total excess.
2. **Given** the inventory in `tasks.md`, **When** a reader counts the rows, **Then** the count equals the 33 violating directories.

### User Story 2 - Split one bounded group for each slice (Priority: P1)

A maintainer splits one package group in one change. Each directory that the change touches holds five or fewer counted children after the change.

**Why this priority**: Each change must reduce measured debt without a compatibility path.

**Independent Test**: Run the import-path test for the slice and the nested package guard.

**Acceptance Scenarios**:

1. **Given** a wave 1 slice, **When** the slice merges, **Then** the guard reports the totals that `plan.md` gives for that slice.
2. **Given** an old module path, **When** Python imports that path, **Then** the import fails.

### User Story 3 - Keep the ratchet green (Priority: P2)

A maintainer merges one slice at a time. Each merge lowers total excess and adds no violation.

**Independent Test**: Compare the guard output before and after one slice.

**Acceptance Scenarios**:

1. **Given** a slice that moves modules out of a violating directory, **When** the guard runs, **Then** total excess decreases and the guard reports no unknown violation.

## Edge Cases

- A new module in a directory at five counted children creates a new violation. The guard rejects that change.
- A moved module that `MistHelper.py` imports needs an import update in the same slice. The slice holds `MistHelper.py` while it works.
- A held path has an open pull request. The slice waits, or it uses a different group.
- A Juniper RMA directory belongs to issue 4168. This record does not schedule that work.
- A legacy record under `specs\` describes merged work. Each legacy record stays unchanged.
- The reserved file `src/foundation/support/utils/zscaler_catalogue.py` stays in place until issue 1794 releases it.

## Requirements

### Functional Requirements

- **FR-001**: Each violating directory MUST have one inventory row with its count, owner, slice, and holds.
- **FR-002**: The measure MUST count direct Python modules except `__init__.py`, and direct child directories that hold tracked Python files.
- **FR-003**: Each slice MUST move one bounded package group. Each directory that the slice touches MUST hold five or fewer counted children after the slice.
- **FR-004**: Each slice MUST reduce total excess. Each slice MUST NOT add a violation.
- **FR-005**: Each slice MUST update the baseline, the expected totals in the nested package test, and the symbol map in the same change.
- **FR-006**: Each slice MUST remove each old module path. A slice MUST NOT add an alias, a re-export, a shim, or a fallback import.
- **FR-007**: Each slice MUST update each active import, patch target, and documentation path for each moved module.
- **FR-008**: Each slice MUST record each changed logger name and each changed class `__module__` value in its pull request.
- **FR-009**: A slice MUST NOT change a held path while the hold is active.
- **FR-010**: Each slice MUST run each gate in T-LOCAL-GATES that applies to its changed files.
- **FR-011**: This record MUST leave the Juniper RMA directories under issue 4168.
- **FR-012**: The nested source package row in `.github/copilot-instructions.md` MUST name the ratchet guard in its local command.
- **FR-013**: Each slice MUST add one changelog fragment named `issue-3824-<slug>.md`.
- **FR-014**: The guard MUST keep printing the examined directory count and the three totals.

### Key Entities

- **Directory measurement**: A directory with its counted children. The natural key is the repository path.
- **Baseline entry**: A recorded violation with its child count and its remediation issue. The natural key is the repository path.
- **Slice**: One bounded change with its wave, its target directory, and its holds. The natural key is the slice ID.
- **Hold**: A reservation on a path. The natural key is the hold ID.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The inventory has 33 rows. Each row has one owner and one slice ID.
- **SC-002**: After wave 1, the guard reports 25 violations and 213 total excess.
- **SC-003**: After waves 2 and 3, the guard reports 2 violations and 3 total excess. Both violations belong to issue 4168.
- **SC-004**: Each slice passes each applicable gate in T-LOCAL-GATES.
- **SC-005**: Each old module path fails to import after its slice merges.
- **SC-006**: The nested source package row in `.github/copilot-instructions.md` names `tests/guardrails/test_nested_package_structure.py`.

## Clarifications

### Session 2026-11-26

- Q: Which measure decides progress for a slice? A: Total excess, the sum of the counts above five. The issue text asks for a violation count. Decision D-1 replaces that text. Source: C-04 and C-05.
- Q: Which issue owns the Juniper RMA directories? A: Issue 4168. The baseline names it. Decision D-5. Source: C-82 and C-83.
- Q: Does the audit renderer work need a new record? A: No. Its legacy record covers merged work. Decision D-7.
- Q: Does a slice close issue 3824? A: No. A slice uses `Refs #3824`. Decision D-11.

## Assumptions

- Remote main keeps the measured base until wave 1 starts. Each slice measures the guard again at its start.
- The target Python version is 3.15. Source: C-11.
- Each slice moves modules only. Mist API calls and menu behavior stay unchanged.

## Out of Scope

- The Juniper RMA packages. Issue 4168 owns them.
- The guard rule and the five-child limit.
- The legacy records under `specs\`.
- Menu operations, container files, and Mist API calls.

## Dependencies

- Issue 4168 owns the Juniper RMA packages and must confirm the export coordination.
- Issue 4009 covers open changes to the metrics gateway core modules.
- Issue 1794 owns the reserved file `zscaler_catalogue.py`.
- Pull requests 4208 and 4813 are open. They change files in the refactors and export directories.
