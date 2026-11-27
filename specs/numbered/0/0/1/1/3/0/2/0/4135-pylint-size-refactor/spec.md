# Feature Specification: Function and module size for Pylint limits

**Feature Branch**: `chore/4135-pylint-size-refactor`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue 4135, "Refactor: function and module size -- R0911, R0913, R0914, R0915, R0917, C0302, R0801 (9 findings in 5 files)".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pylint passes on the named paths (Priority: P1)

A maintainer runs the Pylint command from the issue on the four named paths. The run reports none of the seven listed message IDs.

**Why this priority**: This is the expected outcome of the issue. Every other story supports it.

**Independent Test**: Run the explicit Pylint command in `design/quickstart.md`. Read the JSON output and search for the seven message IDs.

**Acceptance Scenarios**:

1. **Given** the branch holds the change, **When** the maintainer runs the Pylint command, **Then** the output lists none of the seven IDs.
2. **Given** the branch holds the change, **When** the maintainer counts LF lines per module, **Then** each module has 1,000 lines or fewer.

---

### User Story 2 - Operators see the same menus and portal rows (Priority: P1)

An operator uses the menus and the web portal after the change. Each menu key, each portal row, and each export keeps its value and order.

**Why this priority**: The refactor must not change operator-visible behavior.

**Independent Test**: Run the portal tests, the menu guards, and the safe sweep `python MistHelper.py --test`.

**Acceptance Scenarios**:

1. **Given** the change is on the branch, **When** the registry hash test runs, **Then** the registry content matches the constant computed on `main`.
2. **Given** the branch holds the change, **When** the menu order test runs, **Then** the menu keys keep the order that `main` has.

---

### User Story 3 - One Juniper row writer (Priority: P2)

A developer changes the export write path for the Juniper workflows once. Both the asset lookup and the correlation workflow use that change.

**Why this priority**: The duplicate code creates a drift risk. The fix removes the risk.

**Independent Test**: Run `tests/unit/juniper_rma/workflows/test_lookups.py` and `tests/unit/juniper_rma/workflows/test_correlation.py`.

**Acceptance Scenarios**:

1. **Given** rows are empty, **When** the shared writer runs, **Then** it writes no file and logs the reason.
2. **Given** rows exist, **When** the shared writer runs, **Then** it forwards the API name and the field list to the exporter.

---

### User Story 4 - Find moved code from the docs (Priority: P2)

A junior engineer reads the contributor map and the architecture table. Each moved group has a documented path and a current line count.

**Why this priority**: The contributor map must match the code after the move.

**Independent Test**: Search the three documents for each new module path and for the old line counts.

**Acceptance Scenarios**:

1. **Given** the change is on the branch, **When** the engineer reads the contributor map, **Then** the map names each new package under `src/interfaces/cli/`.
2. **Given** the change is on the branch, **When** the engineer reads the architecture table, **Then** the `MistHelper.py` row shows the current line count.

### Edge Cases

- A caller still imports a moved name. Startup fails with an import error. Task T048 migrates each caller, and the full test run finds any missed caller.
- Import-time side effects change order when the bootstrap class moves. Task T042 keeps the call direction one way. Task T049 runs an import smoke test.
- A new module imports `MistHelper`. The new module creates an import cycle. Task T049 fails on any such import.
- The merge of group registry rows changes the key order. Task T012 uses the original merge sequence, and the registry hash test checks the content.
- The endpoint blocks change the key order. Task T030 splits the entries into contiguous blocks, and the endpoint hash test checks the order.
- A test patch targets the old owner after the move. The patch does not reach the new call site. Task T048 changes each target.
- R0913 or R0917 reappears in a function that the reading did not find. Task T002 runs Pylint before any code change. The final Pylint run repeats the check.
- The Windows host cannot read a path written with a forward slash. New code uses `pathlib` (constitution, Technology constraints).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `_is_user_facing` method MUST contain at most six return statements and keep its eight branch outcomes.
- **FR-002**: The registry builder MUST split `_build_registry` into static group builders, each within the Pylint limits, and MUST keep the registry content.
- **FR-003**: The Juniper workflows MUST share one `_write` body, held in `JuniperRowWriter`, and the duplicate body MUST NOT remain in either workflow.
- **FR-004**: The `web_portal/services/operation.py` module MUST contain 1,000 lines or fewer, counted by LF.
- **FR-005**: The `MistHelper.py` module MUST contain 1,000 lines or fewer, counted by LF.
- **FR-006**: The endpoint strategy module MUST contain 1,000 lines or fewer and MUST keep `ENDPOINT_PRIMARY_KEY_STRATEGIES`, `SleTrendIdentity`, and `SleWindowIdentity`.
- **FR-007**: The composed endpoint dictionary MUST keep the original key order, the 612 keys, and the value of each key.
- **FR-008**: The `menu_actions` dictionary MUST keep the original key order and the value of each menu entry.
- **FR-009**: Each new module MUST NOT import `MistHelper`.
- **FR-010**: The change MUST NOT add a compatibility shim, an alias, or a re-export of a moved name.
- **FR-011**: Each test patch target and each source-text guard MUST name the new owner of the code it covers.
- **FR-012**: Each directory that the change creates or grows MUST hold five children or fewer, counted by the ratchet definition.
- **FR-013**: The nested-package ratchet MUST report 190 directories, 33 violations, and 236 total excess after the change.
- **FR-014**: Operator-visible output MUST NOT change. This covers menus, portal rows, CSV output, SQLite output, and XML output.
- **FR-015**: The explicit Pylint command MUST report none of the seven listed message IDs for the four named paths.
- **FR-016**: Each changed or added line MUST carry an inline comment. Each touched block MUST keep action logging.
- **FR-017**: The contributor map, the architecture table, and the copilot instructions MUST name the new paths and the current line counts.
- **FR-018**: The change MUST add one release-note fragment named `issue-4135-pylint-size-refactor.md`.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable. The change moves code and names. It adds no Mist REST request, no mistapi call change, and no WebSocket transport.

### Key Entities *(include if feature involves data)*

- **Registry row**: One menu entry in the portal registry. Natural key: the menu number.
- **Endpoint strategy**: One entry in the endpoint dictionary. Natural key: the API function name.
- **Menu entry**: One entry in `menu_actions`. Natural key: the menu number.
- **Module budget**: One source file, its LF line count, and its child count. Natural key: the repository path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The explicit Pylint command reports zero messages for the seven listed IDs on the four named paths.
- **SC-002**: Each of the three named modules has 1,000 lines or fewer by LF count.
- **SC-003**: The registry hash test, the endpoint order and value test, and the menu key order test pass.
- **SC-004**: Both pytest shards pass, and the coverage report shows 80 percent or above.
- **SC-005**: The safe sweep `python MistHelper.py --test` completes each safe operation.
- **SC-006**: The nested-package ratchet test passes without a change to its baseline or its expected message.

## Assumptions

- The base revision is `main` head `f03c6c9`. A later merge requires a rebase before the push.
- No open pull request changes the five named files. The check ran on 2026-11-26.
- The pinned tools in `requirements-dev.txt` and `pyproject.toml` stay as pinned.
- The Windows environment uses the `.venv` created by `scripts/bootstrap_worktree.py`.

## Out of Scope

- The 25-line and five-block limits for functions outside the seven messages. Task T052 records them as a remediation issue.
- The class-based rule for module-level functions moved from `MistHelper.py`. Task T052 records it as a remediation issue.
- Any change to Mist API calls, menu behavior, operator output, or dependency pins.
- The missing `scripts/menu_api_map` module. Task T053 files a repair issue.
- Changes to `ops-portal/` and `mist-ops-platform/`.

## Clarifications

### Session 2026-11-26

- Q1: Are R0913 and R0917 still present on `main`? Answer: No, by reading. Pylint confirms the result in Task T002 before any code change.
- Q2: Where is the R0801 block now? Answer: The `_write` method in both Juniper workflows. The issue line ranges are stale.
- Q3: Does a deliberate removal of module-level names pass the symbol gate? Answer: The gate reports the names as lost. The pull request lists each name. The record makes no claim that the gate passed.
- Q4: May a new module import `MistHelper`? Answer: No. A new module uses direct imports or the source dependency resolver.
- Q5: Is one pull request acceptable for this size? Answer: Yes. Ordered commits follow the phases in `tasks.md`.
