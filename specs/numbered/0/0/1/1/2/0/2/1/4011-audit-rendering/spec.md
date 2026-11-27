# Feature Specification: Refactor: isolate audit renderer modules

**Feature Branch**: `chore/4011-audit-rendering`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4011: Move the renderer and its five helper modules into nested packages, so each affected level holds five children or fewer. This refactor is a bounded child of issue #3824.

## Terms

- **Audit package**: The folder `src/mist/access/audit/`.
- **Rendering package**: The folder `src/mist/access/audit/rendering/`.
- **Helpers package**: The folder `src/mist/access/audit/rendering/helpers/`. This change creates it.
- **Helper module**: One of the five modules `_renderer_delta.py`, `_renderer_format.py`, `_renderer_html.py`, `_renderer_mermaid.py`, and `_renderer_time.py`.
- **Flat layout**: The audit package before issue #3824. The renderer modules sit at the audit root.
- **3824 layout**: The layout on `main` since PR #4552. The helper modules sit in `rendering/` and in `rendering/clusters/`.
- **Target layout**: The layout that this change creates.
- **Retired path**: An import path that this change removes. Flat paths and 3824 paths are retired paths.
- **Canonical path**: The one import path that stays supported after this change.
- **Baseline**: The `main` commit that the symbol guard compares against.
- **Guard**: A pytest test in the folder `tests/guardrails/`.
- **Structure guard**: The new guard `tests/guardrails/test_audit_rendering_structure.py`.
- **Symbol guard**: The guard `tests/guardrails/test_src_public_symbol_preservation.py`.
- **Hook guard**: The guard `tests/guardrails/test_performance_hook_catalog.py`.
- **Nested guard**: The guard `tests/guardrails/test_nested_package_structure.py`.
- **Local gate**: A row of the Local gates table in `.github/copilot-instructions.md`.
- **Serial slot**: The turn that the coordinator gives to one pull request for merge.

## Clarifications

### Session 2026-11-26

- Q: Does the issue describe the current `main`? A: No. Issue #4011 describes the flat layout. PR #4552 merged on 2026-10-31 and created the 3824 layout. This record applies the issue acceptance criteria to the 3824 layout.
- Q: Which commit is the base for this change? A: The current `main` commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local commit `5b665c48` is diverged and is not reused.
- Q: Which files does the issue name for an edit? A: Four consumer files already import the canonical renderer path. They need no edit. The issue still requires their tests to run.
- Q: Does this change alter a Mist API call? A: No. The audit operation keeps its SDK call and its endpoint.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the audit package in the exact layout (Priority: P1)

A maintainer needs each audit level in its own package with an exact child count. The package shape is then easy to read and to guard.

**Why this priority**: The issue sets exact child counts. Without a guard, a later move can break the shape with no failing test.

**Independent Test**: Run the structure guard. It passes when the audit root holds five children, the rendering package holds two, and the helpers package holds five.

**Acceptance Scenarios**:

1. **Given** the target layout, **When** the structure guard runs, **Then** it prints the three measured counts and passes.
2. **Given** a sixth module in the helpers package, **When** the structure guard runs, **Then** it fails and names the measured count.
3. **Given** a leftover `clusters` package, **When** the structure guard runs, **Then** it fails and names the package.

### User Story 2 - Keep rendering behavior with canonical imports (Priority: P1)

A developer needs each caller to import a moved module from its canonical path. The report output must not change.

**Why this priority**: A wrong import breaks the audit report at run time, even when the layout is correct.

**Independent Test**: Run the renderer tests and the audit operation consumer test. They pass with canonical imports and with no changed expected output.

**Acceptance Scenarios**:

1. **Given** each caller of a helper module, **When** the imports are updated, **Then** each caller uses the helpers package path.
2. **Given** a retired path, **When** Python imports it, **Then** the import fails and no alias answers.
3. **Given** the moved helper modules, **When** the symbol guard runs, **Then** it reports zero lost module-level names.
4. **Given** the escaping, HTML, Mermaid, time, format, and delta tests, **When** they run, **Then** each test passes with no changed expected value.

### User Story 3 - Keep guards and artifacts in step (Priority: P2)

A maintainer needs the guards and the hook catalog to match the new layout.

**Why this priority**: A stale guard reports a false failure, or it hides a real loss.

**Independent Test**: Run the hook guard, the nested guard, and the symbol guard.

**Acceptance Scenarios**:

1. **Given** the seven renderer rows of the hook catalog, **When** the hook guard runs, **Then** each row resolves to its helper module.
2. **Given** the historical inventory CSV, **When** the hook guard runs, **Then** the inventory check passes with no change to the CSV.
3. **Given** the nested guard, **When** it runs, **Then** it reports the same examined directory count as before.

### User Story 4 - Record the change for maintainers (Priority: P2)

A maintainer needs the change record to name each moved module, each retired path, and each excluded file.

**Why this priority**: A clear record prevents a later change from restoring a retired path.

**Independent Test**: Review the changelog fragment and the record folder.

**Acceptance Scenarios**:

1. **Given** the change, **When** the changelog policy guard runs, **Then** it passes with one new fragment.
2. **Given** the record folder, **When** a reader opens `plan.md`, **Then** the reader sees each moved module and each retired path.

### Edge Cases

- A stale `clusters/` folder that holds only cache files. The structure guard counts tracked files only, so the folder does not change the count.
- A copied helper module in two folders. The structure guard fails, because the helpers package holds six modules.
- A caller that still imports a retired path. The import fails, and the retired-path scan names the file.
- A helper symbol that the move drops. The symbol guard reports the lost name.
- Unrelated edits in the shared working tree. The change stages explicit paths only, so the unrelated edits stay out of the commit.
- Pull request #4208 changes the symbol guard file. The rebase resolves only the `MODULE_PATHS` block.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The audit root MUST hold exactly five direct structural children: `analyzer.py`, `audit_analysis_ops.py`, `filter.py`, `time_parser.py`, and `rendering/`.
- **FR-002**: The rendering package MUST hold exactly two direct structural children: `renderer.py` and `helpers/`.
- **FR-003**: The helpers package MUST hold exactly five direct modules: the five helper modules listed in the Terms section.
- **FR-004**: The change MUST remove the `rendering/clusters/` package and each module that it holds.
- **FR-005**: `renderer.py` MUST stay at `src/mist/access/audit/rendering/renderer.py`. Its public class and its public methods MUST NOT change.
- **FR-006**: Each active import MUST name a canonical path. No active tracked file MUST name a retired path.
- **FR-007**: The change MUST NOT add a wrapper, an alias, a re-export, or a fallback import at any retired path.
- **FR-008**: The symbol guard MUST hold six exact rows. Each row MUST map a baseline path to its final path.
- **FR-009**: The hook catalog MUST show the seven moved rows at their final paths. The hook guard MUST expect the same rows. The historical inventory CSV MUST NOT change.
- **FR-010**: The #3824 structure test MUST list the six canonical renderer modules and the retired paths of both earlier layouts.
- **FR-011**: The structure guard MUST enforce the exact counts, MUST scan active files for retired paths, and MUST prove each failure path. The nested guard MUST keep its baseline and its examined count.
- **FR-012**: Each module-level symbol and each rendering behavior MUST stay unchanged. The symbol guard MUST report zero lost names.
- **FR-013**: The record MUST state that each moved symbol gets a new `__module__` value. The record MUST state that no logger name changes.
- **FR-014**: The change MUST add one release-note fragment named `changelog.d/issue-4011-audit-rendering.md`.
- **FR-015**: The change MUST NOT edit a historical record. It MUST NOT edit `specs/1008-top20-violations-remediation/`, `specs/1013-misthelper-refactor-hot-classes/`, `specs/1924-failure-evidence/`, the #3824 record, or the #4142 record. It MUST NOT edit `python-inventory.csv`.
- **FR-016**: The change MUST NOT edit `AGENTS.md`, `CLAUDE.md`, `README.md`, `CHANGELOG.md`, `.specify/feature.json`, or `src/foundation/support/utils/operation_registry.py`.
- **FR-017**: The audit operation MUST keep its SDK call and its endpoint. `audit_analysis_ops.py` MUST NOT change.
- **FR-018**: Escaping, HTML output, Mermaid output, time formatting, formatting, and delta output MUST stay unchanged.
- **FR-019**: Each changed Python line MUST carry an inline comment. Each new file MUST carry a docstring and an inline comment on each executable line.
- **FR-020**: The work MUST stay local until the serial slot. The change MUST NOT push, open a pull request, or merge without authorization.
- **FR-021**: The record MUST live at `specs/numbered/0/0/1/1/2/0/2/1/4011-audit-rendering/`. It MUST hold `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.

### Mist Cloud Transport Requirements

This feature does not add or change a Mist Cloud transport. It does not change a REST call or a WebSocket path. The audit operation keeps its `mistapi` call (row RC-15 and row RC-52 in `design/research.md`).

### Key Entities

- **Audit package**: The package that holds the audit analysis modules and the rendering package.
- **Rendering package**: The package that holds the public renderer module and the helpers package.
- **Helpers package**: The package that holds the five helper modules.
- **Structure guard**: The guard that measures the exact counts and scans the retired paths.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The structure guard prints the counts 5, 2, and 5 and passes.
- **SC-002**: A search for each retired path finds only the allowlisted files. Each allowlisted file is a guard, a retired-import test, or a historical record.
- **SC-003**: The nested guard passes with the same examined directory count as before the change.
- **SC-004**: The renderer tests and the audit operation consumer test pass. The count of collected tests does not drop.
- **SC-005**: The symbol guard reports zero lost names and prints the count of checked modules and symbols.
- **SC-006**: Each local gate that applies exits with its expected result from the gates checklist.

## Assumptions

- The owner keeps the acceptance criteria of issue #4011 as the target.
- The pinned `mistapi` version is 0.64.1. The pin is `>=0.64.0,<0.65`.
- The local commit `5b665c48` is a reference only. The implementation starts from `origin/main`.
- The coordinator assigns the serial slot before the pull request opens.

## Out of Scope

- A change to renderer output, to report content, or to the audit analysis result.
- A change to `analyzer.py`, `filter.py`, or `time_parser.py`.
- The `**api_kwargs` forwarding at `audit_analysis_ops.py` line 55. It is a pre-existing item (row RC-15). Open a separate issue if a gate fails on it.
- An edit to a historical record. The record names the affected historical files, and it leaves them unchanged.
- A change to the parent issue #3824, including its closure.
