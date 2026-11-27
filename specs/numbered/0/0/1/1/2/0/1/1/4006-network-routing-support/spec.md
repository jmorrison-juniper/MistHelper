# Feature Specification: Isolate Network Routing Support Modules

**Feature Branch**: `chore/4006-network-routing-support`

**Spec Kit Feature Name**: `4006-network-routing-support`

**Created**: 2026-11-26

**Status**: Draft. The record is complete. Publication waits for the publication gate in `design/checklists/publication.md`.

**Input**: Issue #4006, "Refactor: isolate network routing support modules". The issue is a bounded child of issue #3824.

## Clarifications

### Session 2026-11-26

- Q: Does `__init__.py` count as a structural child? A: No. The nested-package guard and the structure guard both exclude it. The issue count of seven also excludes it.
- Q: Which modules are the three orchestrators? A: `_routing_utils_forwarding.py`, `_routing_utils_routing.py`, and `_routing_utils_ssr.py`. The module `routing_utils.py` is the public facade.
- Q: Can the preserved candidate commit merge as is? A: No. Its `_routing_utils_payload.py` predates change `5e890ed6` on `main`. The change must be rebuilt from current `main`.
- Q: Does the nested-package baseline change? A: Yes. The network root drops to five children, so its baseline entry becomes stale.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the network root within five children (Priority: P1)

A maintainer finds the three support modules in one support package. The network root package holds five structural children.

**Why this priority**: The constitution five-item rule applies. Parent issue #3824 requires this remediation.

**Independent Test**: Run `python -m pytest tests/guardrails/test_network_routing_support_structure.py -q`. The test reports five network children and three support children.

**Acceptance Scenarios**:

1. **Given** the change is applied, **When** the network root is listed, **Then** it holds four modules and the `support` directory.
2. **Given** the change is applied, **When** the support package is listed, **Then** it holds exactly three modules.
3. **Given** a sixth structural child exists, **When** the structure guard runs, **Then** it fails and prints the measured count.

### User Story 2 - Keep routing behavior and module-level names (Priority: P1)

An operator runs the routing menus and sees the same behavior. A maintainer confirms that each moved module keeps its module-level names.

**Why this priority**: The refactor must not change behavior. A lost name or a changed payload affects production operators.

**Independent Test**: Run the routing unit tests, the unparseable-response guards, and the symbol guard. Run `symbol-diff` for each moved module.

**Acceptance Scenarios**:

1. **Given** the change is applied, **When** the routing unit tests run, **Then** no collected test fails.
2. **Given** a moved module, **When** `symbol-diff` runs, **Then** it reports `no module-level name changed` and exits with code 0.
3. **Given** the change is applied, **When** a moved file is compared with current `main`, **Then** its blob equals the `main` blob.

### User Story 3 - Keep active references and generated pages canonical (Priority: P2)

A maintainer searches the active tree and finds no old module path. The generated WebSocket pages show canonical source links. Historical records remain unchanged.

**Why this priority**: Stale references break imports, guards, and generated documentation. The issue requires canonical paths in active files only.

**Independent Test**: Run the active-path scan in the structure guard. Run the menu generator and check that no generated file changes.

**Acceptance Scenarios**:

1. **Given** the change is applied, **When** the active-path scan runs, **Then** no file under `src`, `tests`, `scripts`, `documentation`, or `README.md` names an old module path.
2. **Given** the change is applied, **When** the menu generator runs twice, **Then** no generated file changes.

### Edge Cases

- An external script imports an old module path. The import fails with `ModuleNotFoundError`. This failure is intended, because the change adds no shim.
- The performance hook catalog names an old path for three rows. The catalog guard fails until its approved move map names the new paths.
- Current `main` changes a moved module after the candidate base. The candidate must not merge as is. Rebuild the change from current `main`.
- A historical record under `specs/` names an old path. The active-path scan excludes `specs/`. The record stays unchanged. The catalog move map also names old paths by design. The active-path scan excludes that one file.
- Open draft pull request #4208 changes the symbol guard file. Publication waits until #4208 merges, closes, or releases that file.
- A shallow CI checkout lacks history for the symbol guard. The guard fetches more history through its `MERGE_BASE_DEEPEN` setting.
- Stale `__pycache__` folders hold compiled files for old modules. The implementer deletes them in the worktree before the import smoke test.

## Out of Scope

- Moving `_routing_utils_forwarding.py`, `_routing_utils_routing.py`, `_routing_utils_ssr.py`, or `routing_utils.py`.
- Changing routing behavior, request validation, payload construction, or message text.
- Replacing the raw `requests.post` call in `_routing_utils_payload.py` with a mistapi method. The debt stays recorded in `plan.md`.
- Fixing existing function-length and parameter violations. Each one needs a separate remediation action.
- Editing any file under `specs/`, including the `specs/2448` CSV artifacts.
- Repairing the order-dependent failure reported in issue #4728.
- Publishing before the publication gate clears.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST move `_routing_utils_display.py`, `_routing_utils_parsing.py`, and `_routing_utils_payload.py` into `src/mist/networking/network/support/`.
- **FR-002**: The support package MUST contain `__init__.py` with a module docstring only.
- **FR-003**: The network package MUST hold exactly five structural children.
- **FR-004**: The support package MUST hold exactly three structural children.
- **FR-005**: The change MUST keep the facade and the three orchestrators at the network root.
- **FR-006**: The change MUST NOT leave a file, alias, shim, or re-export at an old module path.
- **FR-007**: Imports in `routing_utils.py` and `_routing_utils_routing.py` MUST name canonical paths.
- **FR-008**: Mock targets and logger strings in the routing tests MUST name canonical paths.
- **FR-009**: Module loggers MUST keep `logging.getLogger(__name__)`. Logger names change with the module path.
- **FR-010**: The docstring reference in `_utility_commands_selection.py` MUST name the canonical path.
- **FR-011**: Each moved module MUST keep its module-level names. The symbol guard MUST map each moved module.
- **FR-012**: Both generated WebSocket menu pages MUST show canonical source links after regeneration.
- **FR-013**: The change MUST NOT edit any file under `specs/`.
- **FR-014**: The performance hook catalog guard MUST resolve the three moved hook rows through its move map.
- **FR-015**: The nested-package baseline MUST drop the network entry. The guard report MUST read 32 violations and 234 total excess.
- **FR-016**: The structure guard MUST check FR-003 and FR-004. It MUST scan active paths, except the approved catalog move map, and print examined counts on success.
- **FR-017**: The change MUST add one changelog fragment named `changelog.d/issue-4006-network-routing-support.md`.
- **FR-018**: The change MUST NOT alter function bodies, request validation, payload construction, or message text in the moved modules.
- **FR-019**: The change MUST NOT add credential handling, external access, or a REST call.
- **FR-020**: The change MUST pass each applicable local gate before commit.
- **FR-021**: The change MUST NOT publish before the publication gate clears.
- **FR-022**: The record MUST exist at `specs\numbered\0\0\1\1\2\0\1\1\4006-network-routing-support`.

### Key Entities

Not applicable: this change moves modules and edits tests. It adds no data entity. See `design/data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The structure guard reports five network children and three support children.
- **SC-002**: The active-path scan reports zero files that name an old module path.
- **SC-003**: The routing unit tests and the unparseable-response guards report zero failures.
- **SC-004**: `symbol-diff` reports zero lost module-level names for each moved module.
- **SC-005**: The performance hook catalog guard and the nested-package ratchet guard pass.
- **SC-006**: A second run of the menu generator changes no generated file.
- **SC-007**: Each applicable local gate passes. Each gate that does not apply has a stated reason.
- **SC-008**: Publication starts only after the five publication conditions record as met.

## Assumptions

- **A-1**: A structural child is a direct Python module, except `__init__.py`, or a direct directory. The nested-package guard uses the same rule.
- **A-2**: The three orchestrators are the forwarding, routing, and SSR modules. The facade `routing_utils.py` stays at the root.
- **A-3**: The issue lists historical records 1780, 198, 1034, and 2448. A code search finds old names in 1778, 1924, and 2448. This record treats every file under `specs/` as read-only.
- **A-4**: The coordinator assigns the serial pull request slot. This record does not assign it.
- **A-5**: Local gates run on Windows 11 with the `.venv` environment active.
- **A-6**: This record does not copy test counts from issue comments. Implementation measures the counts again.
