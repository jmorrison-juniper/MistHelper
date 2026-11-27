# Feature Specification: Split the Juniper RMA and export packages

**Feature Branch**: `chore/4168-split-rma-and-export-packages`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4168, "Refactor: split the Juniper RMA packages and export folder to meet the nested package ratchet". Measured on remote `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove three paths from accepted debt (Priority: P1)

A maintainer runs the nested package ratchet guard. The guard no longer accepts debt for the export folder or for the two Juniper RMA packages. The guard reports 30 violations and 190 total excess children.

**Why this priority**: Issue #4168 requires the three baseline entries to be removed. The guard is the only automated proof of this change.

**Independent Test**: Run `python -m pytest tests/guardrails/test_nested_package_structure.py`. The test passes and prints the measured scope.

**Acceptance Scenarios**:

1. **Given** the baseline holds 33 entries and 236 total excess, **When** the change merges, **Then** the baseline holds 30 entries and 190 total excess.
2. **Given** a directory under the moved packages holds six children, **When** the guard runs, **Then** the guard fails with an unknown violation.

---

### User Story 2 - Run the same menus after the move (Priority: P1)

An operator runs the export menus and the Juniper RMA menus 294 to 304. Each menu writes the same output columns and the same files as before the move.

**Why this priority**: The move must not change the operator result. A broken export stops a network operations center task.

**Independent Test**: Run `python MistHelper.py --test` and the moved-module test suites. Each `safe` operation completes with the same result as on `main`.

**Acceptance Scenarios**:

1. **Given** a menu imports a moved module, **When** the operator runs the menu, **Then** the menu starts and writes the same output columns.
2. **Given** a test patches a moved module by dotted path, **When** the test runs, **Then** the patch applies to the new dotted path.

---

### User Story 3 - Find each moved module at one path (Priority: P2)

A developer searches the live repository for an old module path. The search finds no live file that names the old path. The resolver, scripts, generated references, and documentation name the new path.

**Why this priority**: A stale path in a live file causes a wrong import or a wrong documentation link.

**Independent Test**: Run the old-path search in `design/quickstart.md`. Each live file returns zero hits.

**Acceptance Scenarios**:

1. **Given** a live file names an old module path, **When** the old-path search runs, **Then** the search reports that file.
2. **Given** a dated record names an old module path, **When** the old-path search runs, **Then** the search excludes the dated record and the dated record stays unchanged.

### Edge Cases

- A test imports a moved module in package form, for example `from src.operations.exporting.export import gateway_test_exporter`. The import must name the new package.
- A moved module keeps its class names. Its logger name changes to the new dotted path, because the logger uses `__name__`.
- Pull request #4813 changes `src/operations/exporting/export/data_exporter.py` and two export test files. This change edits one of those test files, `tests/unit/export/test_endpoint_family_exporter.py`, so this change waits until that pull request merges.
- The hook catalog keeps its historical rows. The guard maps each old row to the new path through its approved move table.
- A new package reaches six children during the move. The guard reports an unknown violation, and the move stops until the package is split.
- The record folder `4168-org-auto-upgrade-policy` uses the same number, but it belongs to issue #4217. This change does not reuse, rename, or edit that folder.
- A generated menu page names an old path. The generator regenerates the page, and the regenerated page names the new path.
- The current code uses absolute imports only. No relative import changes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change must remove the baseline entries for `src/operations/exporting/export`, `src/operations/exporting/juniper_rma/model`, and `src/operations/exporting/juniper_rma/workflows`.
- **FR-002**: Every directory under the moved packages must hold five children or fewer.
- **FR-003**: The change must keep `src/operations/exporting/export/data_exporter.py` at its current path.
- **FR-004**: The change must place each export module in the `org`, `site`, `wan`, or `generic` package, as the change map defines.
- **FR-005**: The change must split `juniper_rma/model` into `parsers` and `rows` packages, and keep `run_record.py` in place.
- **FR-006**: The change must split `juniper_rma/workflows` into `reads` and `lookups` packages, and keep `access_check.py` and `correlation.py` in place.
- **FR-007**: The change must not add a compatibility shim, alias, or re-export at any old module path.
- **FR-008**: The change must update each import, patch target, module string, and live reference that names a moved module.
- **FR-009**: Each moved module must keep its module-level names unchanged.
- **FR-010**: The change must keep the `### Move a module` table in `.github/copilot-instructions.md` unchanged.
- **FR-011**: The change must keep the `tests/unit/` directory layout unchanged, because issue #4142 owns that split.
- **FR-012**: The change must keep dated records unchanged. Dated records are `specs/`, `changelog.d/` fragments, `.specify/bugs/`, and `CHANGELOG.md`.
- **FR-013**: The change must add `changelog.d/issue-4168-split-rma-and-export-packages.md`.
- **FR-014**: The change must not start until pull request #4813 merges.
- **FR-015**: The change must update the expected message in `test_nested_package_ratchet_matches_main` to the measured counts.
- **FR-016**: The change must add one guard test that proves each old module file no longer exists.
- **FR-017**: The change must record each logger name change and each class `__module__` change in `plan.md`.
- **FR-018**: The change must leave every Mist REST request unchanged.

### Key Entities

- **Moved module**: A Python file whose path changes. Its natural key is the old dotted path. See `design/data-model.md`.
- **Baseline entry**: One accepted violation in `tests/guardrails/nested_package_baseline.json`. Its natural key is the repository path.
- **Measured directory**: One directory under `src` with tracked Python descendants. Its natural key is the repository path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The guard reports 206 directories examined, 30 violations, and 190 total excess.
- **SC-002**: `python -m pytest tests/guardrails/test_nested_package_structure.py` exits with code 0.
- **SC-003**: The old-path search in `design/quickstart.md` returns no hit in a live file.
- **SC-004**: The unit, integration, and guardrail suites for export, Juniper RMA, the web portal, and the guardrails pass.
- **SC-005**: `python MistHelper.py --test` completes each `safe` operation without a new failure.
- **SC-006**: A second run of the menu reference generators changes no file.
- **SC-007**: `symbol-diff` reports no module-level name changed for each changed Python file.

## Assumptions

- The bootstrap environment in `.github/copilot-instructions.md` provides every local gate tool.
- The `mypy` override `src.operations.exporting.export.*` in `pyproject.toml` applies to the new subpackages. `T-LOCAL-GATES` verifies this.
- No code outside this repository imports the moved modules.
- No Mist REST call changes, so no mistapi contract changes.
- Issue #3824 keeps the other 30 baseline entries.

## Non-Goals

- Split `tests/unit/` (issue #4142).
- Reduce the other 30 baseline entries (issue #3824).
- Change `data_exporter.py` (pull request #4813).
- Renumber the legacy record folder for issue #4217. A new issue must handle this.
- Change any menu behavior or output column.

## Clarifications

### Session 2026-11-26

- Q: Does this change move `data_exporter.py`? A: No. Pull request #4813 owns its content, and a move would conflict with it.
- Q: Does one pull request cover all three packages? A: Yes. The guard requires the three entries to change together.
- Q: Does the legacy folder `4168-org-auto-upgrade-policy` change? A: No. Its plan names issue #4217, so another issue owns it.
- Q: Do dated records change? A: No. The live files in `plan.md` change, and dated records stay as they are.
