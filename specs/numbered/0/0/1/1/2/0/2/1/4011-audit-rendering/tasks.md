# Tasks: Refactor: isolate audit renderer modules

**Feature**: `4011-audit-rendering` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Analysis**: [analysis.md](analysis.md)

Run the tasks in order. A later task reads the result of an earlier task. A task marked `[P]` edits a different file and can run in parallel with other `[P]` tasks of its phase.

Each task has these fields:

- **Requirements**: The `FR-###` identifiers that the task serves.
- **Files**: The exact repository paths. The worktree root replaces `<worktree>` in each command.
- **Acceptance**: The condition that proves the task is complete.
- **Verification**: The command or check that proves the acceptance condition.
- **Status**: `open`, `verified-present`, `partial`, or `absent`.

Status `verified-present` means the condition already holds on `main`. Status `partial` means part of the condition holds. Status `absent` means the file or folder does not exist yet.

Ownership: Do not modify `.specify/feature.json`, `README.md`, or `CHANGELOG.md`. Do not modify a historical record. Add each new file by explicit path before a guard run, because the guards read tracked files.

## Phase 1: Verify the current state

### T001 [P] Verify the 3824 layout and the current counts

- **Requirements**: FR-001, FR-002, FR-003
- **Files**: `src/mist/access/audit/` (read only)
- **Acceptance**: The audit root holds five children. The rendering package holds five children. The helpers package is absent. Row RC-10 and rows RC-11 to RC-13 match.
- **Verification**: `Get-ChildItem -LiteralPath 'src\mist\access\audit' -Force` and `Get-ChildItem -LiteralPath 'src\mist\access\audit\rendering' -Force` in the main checkout.
- **Status**: verified-present

### T002 Create the worktree and bootstrap the environment

- **Requirements**: FR-020
- **Files**: None. The worktree is `..\MistHelper-4011`.
- **Acceptance**: The worktree branch is `chore/4011-audit-rendering`, and its status is clean.
- **Verification**: `git -C ..\MistHelper-4011 status --porcelain` prints no line.
- **Status**: open

### T003 Record the collected test counts before the change

- **Requirements**: FR-018
- **Files**: None
- **Acceptance**: The command prints the collected counts. The counts appear in the pull request body.
- **Verification**: `python -m pytest --collect-only -q tests/test_audit_renderer.py tests/unit/marvis/mist/access/audit`
- **Status**: open

## Phase 2: Move the helper modules

### T004 [P] Move `_renderer_delta.py` into the helpers package

- **Requirements**: FR-003, FR-004
- **Files**: `src/mist/access/audit/rendering/_renderer_delta.py` to `src/mist/access/audit/rendering/helpers/_renderer_delta.py`
- **Acceptance**: Git reports one rename. The content does not change.
- **Verification**: `git -C ..\MistHelper-4011 diff --cached -M --stat`
- **Status**: open

### T005 [P] Move `_renderer_format.py` into the helpers package

- **Requirements**: FR-003, FR-004
- **Files**: `src/mist/access/audit/rendering/_renderer_format.py` to `src/mist/access/audit/rendering/helpers/_renderer_format.py`
- **Acceptance**: Git reports one rename. The content does not change.
- **Verification**: `git -C ..\MistHelper-4011 diff --cached -M --stat`
- **Status**: open

### T006 [P] Move `_renderer_time.py` into the helpers package

- **Requirements**: FR-003, FR-004
- **Files**: `src/mist/access/audit/rendering/_renderer_time.py` to `src/mist/access/audit/rendering/helpers/_renderer_time.py`
- **Acceptance**: Git reports one rename. The content does not change.
- **Verification**: `git -C ..\MistHelper-4011 diff --cached -M --stat`
- **Status**: open

### T007 [P] Move `_renderer_html.py` into the helpers package

- **Requirements**: FR-003, FR-004
- **Files**: `src/mist/access/audit/rendering/clusters/_renderer_html.py` to `src/mist/access/audit/rendering/helpers/_renderer_html.py`
- **Acceptance**: Git reports one rename. Import edits follow in T012.
- **Verification**: `git -C ..\MistHelper-4011 diff --cached -M --stat`
- **Status**: open

### T008 [P] Move `_renderer_mermaid.py` into the helpers package

- **Requirements**: FR-003, FR-004
- **Files**: `src/mist/access/audit/rendering/clusters/_renderer_mermaid.py` to `src/mist/access/audit/rendering/helpers/_renderer_mermaid.py`
- **Acceptance**: Git reports one rename. Import edits follow in T013.
- **Verification**: `git -C ..\MistHelper-4011 diff --cached -M --stat`
- **Status**: open

### T009 Create the helpers package initializer

- **Requirements**: FR-003, FR-019
- **Files**: `src/mist/access/audit/rendering/helpers/__init__.py`
- **Acceptance**: The file holds one docstring line with an inline comment. The docstring names the helpers package.
- **Verification**: `python -c "import src.mist.access.audit.rendering.helpers"` exits 0 in the worktree.
- **Status**: absent

### T010 Remove the `clusters` package

- **Requirements**: FR-004
- **Files**: `src/mist/access/audit/rendering/clusters/__init__.py` and the empty folder `src/mist/access/audit/rendering/clusters/`
- **Acceptance**: Git stages the removal of the initializer. The folder path does not exist after the removal. Remove the cache folder by its exact path only.
- **Verification**: `Test-Path -LiteralPath '..\MistHelper-4011\src\mist\access\audit\rendering\clusters'` prints `False`.
- **Status**: open

Caution: Remove only the exact `clusters` path. A wider removal can delete unrelated work in the shared tree.

## Phase 3: Update imports and docstrings

### T011 Update the renderer imports, docstring, and stale comment

- **Requirements**: FR-005, FR-006, FR-019
- **Files**: `src/mist/access/audit/rendering/renderer.py`, docstring lines 7 to 11 and import lines 22 to 46.
- **Acceptance**: Each import names `src.mist.access.audit.rendering.helpers`. The comment at line 42 gives the correct reason for an absolute import. No line names `rendering.clusters` or a flat path.
- **Verification**: `git -C ..\MistHelper-4011 grep -n "rendering\._renderer_\|rendering\.clusters" -- src/mist/access/audit/rendering/renderer.py` prints nothing.
- **Status**: open

### T012 [P] Update the HTML helper imports

- **Requirements**: FR-006
- **Files**: `src/mist/access/audit/rendering/helpers/_renderer_html.py` lines 17, 20, and 23
- **Acceptance**: The three imports name the helpers package. Each changed line keeps its inline comment.
- **Verification**: `python -c "import src.mist.access.audit.rendering.helpers._renderer_html"` exits 0 in the worktree.
- **Status**: open

### T013 [P] Update the Mermaid helper imports

- **Requirements**: FR-006
- **Files**: `src/mist/access/audit/rendering/helpers/_renderer_mermaid.py` lines 13 and 16
- **Acceptance**: The two imports name the helpers package. Each changed line keeps its inline comment.
- **Verification**: `python -c "import src.mist.access.audit.rendering.helpers._renderer_mermaid"` exits 0 in the worktree.
- **Status**: open

### T014 [P] Update the renderer test import

- **Requirements**: FR-006
- **Files**: `tests/test_audit_renderer.py` line 15
- **Acceptance**: The import names `src.mist.access.audit.rendering.helpers._renderer_delta`.
- **Verification**: `python -m pytest tests/test_audit_renderer.py`
- **Status**: open

### T015 [P] Update the format wave test docstring and import

- **Requirements**: FR-006
- **Files**: `tests/unit/marvis/mist/access/audit/test_renderer_format_wave9.py` lines 1 and 10
- **Acceptance**: The docstring and the import name the helpers package.
- **Verification**: `python -m pytest tests/unit/marvis/mist/access/audit/test_renderer_format_wave9.py`
- **Status**: open

### T016 [P] Update the time wave test docstring and import

- **Requirements**: FR-006
- **Files**: `tests/unit/marvis/mist/access/audit/test_renderer_time_wave9.py` lines 1 and 11
- **Acceptance**: The docstring and the import name the helpers package.
- **Verification**: `python -m pytest tests/unit/marvis/mist/access/audit/test_renderer_time_wave9.py`
- **Status**: open

### T017 Confirm that four consumers need no edit

- **Requirements**: FR-006, FR-017
- **Files**: `src/mist/access/audit/audit_analysis_ops.py` line 20, `junk/diag_rbo.py` line 5, `tests/run_audit_integration.py` line 11, and `tests/unit/marvis/mist/access/audit/test_audit_analysis_ops.py` line 24
- **Acceptance**: Each file imports the canonical renderer or the audit operations class. None of the four files appears in the diff.
- **Verification**: `git -C ..\MistHelper-4011 diff --name-only` does not list these four files.
- **Status**: verified-present

## Phase 4: Update the guards and the artifacts

### T018 [P] Replace the six symbol guard rows

- **Requirements**: FR-008, FR-012
- **Files**: `tests/guardrails/test_src_public_symbol_preservation.py` lines 82 to 87
- **Acceptance**: The six rows map baseline paths to final paths. The renderer row maps to itself. The five helper rows refer to the helpers package.
- **Verification**: `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py`
- **Status**: partial

### T019 [P] Update the expected hook guard rows

- **Requirements**: FR-009
- **Files**: `tests/guardrails/test_performance_hook_catalog.py` lines 277 to 288
- **Acceptance**: The expected rows name the helpers package for `hook-0079`, `hook-0080`, `hook-0081`, `hook-0082`, `hook-0083`, `hook-diag-0068`, and `hook-diag-0069`. The renderer rows for `hook-0087` and `hook-0088` do not change.
- **Verification**: `python -m pytest tests/guardrails/test_performance_hook_catalog.py`
- **Status**: open

### T020 [P] Update the seven hook catalog rows

- **Requirements**: FR-009
- **Files**: `specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv` lines 80 to 84, 559, and 560, column 3 (`file_path`) only
- **Acceptance**: Git shows seven changed lines. Each changed line differs only in the `file_path` column.
- **Verification**: `git -C ..\MistHelper-4011 diff --stat -- specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv` shows seven changed lines.
- **Status**: open

### T021 Confirm that the historical inventory and the summaries do not change

- **Requirements**: FR-009, FR-015
- **Files**: `specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv`, `specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog-summary.json`, and `specs/2448-misthelper-performance-monitoring/artifacts/scan-summary.json`
- **Acceptance**: Git shows no diff for the three files.
- **Verification**: `git -C ..\MistHelper-4011 diff --quiet -- specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog-summary.json specs/2448-misthelper-performance-monitoring/artifacts/scan-summary.json` exits 0.
- **Status**: verified-present

### T022 Update the #3824 structure test lists

- **Requirements**: FR-010
- **Files**: `tests/unit/marvis/mist/access/audit/test_renderer_structure_issue_3824.py` lines 8 to 13 (canonical list) and 17 to 22 (retired list)
- **Acceptance**: The canonical list names the six modules at the helpers package. The retired list keeps the six flat paths and adds the five 3824 paths.
- **Verification**: `python -m pytest tests/unit/marvis/mist/access/audit/test_renderer_structure_issue_3824.py`
- **Status**: partial

### T023 Add the structure guard

- **Requirements**: FR-011, FR-019
- **Files**: `tests/guardrails/test_audit_rendering_structure.py`
- **Acceptance**: The file holds the class `AuditLayoutInspector` and five tests: TS-01 to TS-05 in `analysis.md`. Each function holds 25 lines or fewer. Each git call and file read logs before and after.
- **Verification**: `python -m pytest tests/guardrails/test_audit_rendering_structure.py`
- **Status**: absent

### T024 Confirm the nested guard keeps its baseline and count

- **Requirements**: FR-011
- **Files**: `tests/guardrails/nested_package_baseline.json` and `tests/guardrails/test_nested_package_structure.py` (read only)
- **Acceptance**: The baseline file has no diff. The nested guard passes with the examined count that its message names.
- **Verification**: `python -m pytest tests/guardrails/test_nested_package_structure.py`
- **Status**: verified-present

## Phase 5: Records and documentation

### T025 Add the changelog fragment

- **Requirements**: FR-014
- **Files**: `changelog.d/issue-4011-audit-rendering.md`
- **Acceptance**: The file holds one `### Changed` heading and one bullet. The bullet names issue #4011 and the package move.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

### T026 Create the record folder

- **Requirements**: FR-021
- **Files**: `specs/numbered/0/0/1/1/2/0/2/1/4011-audit-rendering/` with `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`
- **Acceptance**: The folder holds the five children of the layout. Each file comes from this draft, and no other record folder is created.
- **Verification**: `python -m pytest tests/guardrails` passes, and the process folder check in the guard run reports no new direct child.
- **Status**: absent

### T027 Confirm the scope of the change

- **Requirements**: FR-015, FR-016
- **Files**: None
- **Acceptance**: The diff lists only the paths in `plan.md` section "File change map". No historical record and no governance file appears in the diff.
- **Verification**: `git -C ..\MistHelper-4011 diff --name-only origin/main` lists only allowed paths.
- **Status**: open

## Phase 6: Focused checks

### T028 Run the focused tests and the guards

- **Requirements**: FR-011, FR-012, FR-018
- **Files**: None
- **Acceptance**: Each focused command exits 0. The printed counts match the counts in the tests.
- **Verification**: The focused command in `design/quickstart.md`, step 8.
- **Status**: open

## Final tasks

### T-LOCAL-GATES Run each applicable local gate

- **Requirements**: FR-019, SC-006
- **Files**: None
- **Acceptance**: Each gate in `design/checklists/gates.md` with status `applies` exits with its expected result. Record each result in the pull request body.
- **Verification**: The commands in `design/checklists/gates.md`.
- **Status**: open

### T-PR Commit, rebase, push, and open the pull request

- **Requirements**: FR-020
- **Files**: None
- **Acceptance**: The commit has the subject `refactor(audit): isolate the audit renderer modules`, a body with `Closes #4011`, and the co-author trailer. The branch rebases on `origin/main`. The pull request opens only after the coordinator assigns the serial slot.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body,headRefName` shows the title and the closing line.
- **Status**: open

### T-REMOTE-CI Watch the remote CI run

- **Requirements**: FR-020
- **Files**: None
- **Acceptance**: Each required check reports success on the latest commit of the pull request.
- **Verification**: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`
- **Status**: open

### T-MERGE Merge after authorization

- **Requirements**: FR-020
- **Files**: None
- **Acceptance**: The orchestrator authorizes the merge. The auto-merge label is added only after each check reports green. The squash commit lands on `main`.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json state,mergedAt` shows `MERGED`.
- **Status**: open

Warning: A squash merge closes the pull request. A commit that you push after that point is orphaned, so open a new issue and branch from `main` instead.

## Dependencies and execution order

- T001 runs first. T002 and T003 need T001.
- T004 to T008 need T002 and can run in parallel.
- T009 and T010 need T004 to T008.
- T011 needs T004 and T005 and T006. T012 and T013 need T007 and T008.
- T014 to T016 can run after T004 to T008.
- T017 has no dependency after T001.
- T018 to T020 can run in parallel after the moves.
- T021 needs T020. T022 needs T004 to T008.
- T023 needs every move and import task. T024 needs T010.
- T025 and T026 need T023. T027 needs every edit task.
- T028 needs T023 and T018 to T024.
- T-LOCAL-GATES needs T028. T-PR needs T-LOCAL-GATES and the serial slot. T-REMOTE-CI needs T-PR. T-MERGE needs T-REMOTE-CI and the authorization.

## Verification map

Each task names one gate or check from `design/checklists/gates.md`.

| Task | Gate or check |
|------|---------------|
| T001 | Guardrails (baseline run before the change) |
| T002 | C-01 (worktree scope) |
| T003 | Tests (collect-only form of `python -m pytest tests/<changed file>`) |
| T004 to T008 | C-01 (rename scope) |
| T009 | Import smoke |
| T010 | Import smoke (retired import fails) |
| T011 | Old paths |
| T012 and T013 | Import smoke |
| T014 to T016 | Tests |
| T017 | C-01 (scope) |
| T018 | Guardrails (symbol guard) |
| T019 and T020 | Guardrails (hook guard) |
| T021 | C-01 (scope) |
| T022 | Tests (#3824 structure test) |
| T023 | Guardrails (structure guard) |
| T024 | Guardrails (nested guard) |
| T025 | Guardrails (changelog policy) |
| T026 | Guardrails (process folder guard) and C-06 |
| T027 | C-01 (scope) |
| T028 | Tests (focused command) |
| T-LOCAL-GATES | Each gate with status `applies` |
| T-PR | C-08 (serial slot) |
| T-REMOTE-CI | Remote CI checks, which are not a local gate |
| T-MERGE | Remote CI checks and authorization, which are not a local gate |

## Counts

- Tasks in phases 1 to 6: 28.
- Final tasks: 4.
- Total tasks: 32.
