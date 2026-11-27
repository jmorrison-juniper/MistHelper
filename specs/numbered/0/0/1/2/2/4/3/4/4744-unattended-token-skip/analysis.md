# Analysis: Unattended token skip for menu 247

This review checks `spec.md`, `plan.md`, and `tasks.md` against the remote code on main. It records defects in existing work and the items that remain open. Remote row numbers (RC-##) refer to the table in `design/research.md`.

## Consistency Review

- **C-1 Requirement coverage**: Each requirement from FR-001 to FR-017 maps to at least one task and one test or gate. The traceability table in `tasks.md` shows the mapping. Status: consistent.
- **C-2 Count agreement**: `design/research.md` lists 59 remote checks. `META_DIR\4744-STATUS.json` lists 59. `META_DIR\4744-summary.md` states 59. Status: consistent.
- **C-3 Record route**: Feature number 4744 gives base-5 digits 0, 0, 1, 2, 2, 4, 3, 4 at width 8 (RC-45). That matches the route from the orchestrator. The reference record for issue 4920 follows the same rule, and its digits are 0, 0, 1, 2, 4, 1, 4, 0. Status: consistent.
- **C-4 Paths**: The runner (RC-01), runner test module (RC-25), exporter (RC-13), registry (RC-16), and changelog rule (RC-39) match the plan. The new module path is free (RC-50). Status: consistent.
- **C-5 Five-Item Rule debt**: `plan.md` records the test module debt (Complexity Tracking row 1) and the function debt (row 2). The spec does not describe structure. Status: consistent, because the debt is recorded.
- **C-6 Gates and changed files**: Every changed file appears in T-LOCAL-GATES. The runner and the new module run the mypy, radon, bandit, pylint, vulture, pydocstyle, interrogate, and symbol gates. The symbol gate has no base for the new module. The test modules run pytest. The documentation row runs the STE gate. The fragment runs the changelog guard. Status: consistent.
- **C-7 Generated pages**: The spec and plan do not edit `documentation/menu_reference.md` or `documentation/menu-api/`. RC-35 shows the generator source, and RC-34 shows the drift job. Status: consistent.
- **C-8 Interactive path**: FR-012 and task T009 keep the exporter unchanged. RC-13, RC-14, and RC-28 cover the interactive cancel path. Status: consistent.

## Defects in Existing Work

- **A-1 Root cause, optional token prompt**: The exporter asks for the token with a context and no `allow_empty` argument (RC-13, line 65). The input provider therefore treats the token prompt as optional. It returns an empty answer (RC-02, lines 126 and 127). The handler returns normally, and the runner writes a pass (RC-06, line 519). The change fixes this through the operator-only context list (FR-001).
- **A-2 Registry skip reason unused at runtime**: The registry row for menu 247 holds a skip reason (RC-16, line 590). The runner reads a skip reason only on the skip-list paths (RC-10, lines 378 and 414). An interactive-safe option never reads its reason at runtime. The change reads the reason for the operator-only skip only (FR-002).
- **A-3 Summary status ignores zero exercised operations**: The emitter sets the summary status from the failed count alone (RC-23, line 181). The verdict returns failure when zero operations are exercised (RC-11 and RC-12, lines 688 and 690). A run with only skipped operations can write status `pass` while the console verdict is failure. The defect predates this change. This change makes a skip-only run reachable through the unattended sweep. The change does not fix it, because the fix belongs to the emitter and its tests. Follow-up R-3 tracks it.
- **A-4 Grandfathered method length**: `_run_single_option` spans lines 541 to 613, which is 73 lines (RC-56). It has more than five logical blocks. The change adds one except clause. Complexity Tracking row 2 records this.
- **A-5 Grandfathered class size**: `InteractiveTestRunner` declares ten fields (RC-57) and 32 methods (RC-59). That is 42 members. The change adds none. Complexity Tracking row 3 records this.
- **A-6 Grandfathered module shape**: The runner module declares eight classes at module level (RC-58). The change adds no top-level name to that module. Complexity Tracking row 4 records this.
- **A-7 Two-value coupling**: `_run_option_loop` returns two values (RC-07). Six test call sites unpack two values (RC-26). The tally change touches all six sites (FR-015).
- **A-8 Documentation gap**: The `--testinteractive` row in `documentation/cli-reference.md` names the operation set only (RC-36). It does not describe the operator-only skip. FR-016 closes the gap.
- **A-9 Other consumers of the provider**: `tests/unit/marvis/actions/test_selection.py` (RC-29) and `tests/unit/marvis/actions/test_operation.py` (RC-30) use the provider. The decoded lines of both files name no token context. Both files stay in the gate list.
- **A-10 Stale sample in the issue**: The issue log sample shows `Email verification` as the option description. The menu 247 entry on main has a longer title (RC-17). The issue cites commit 7b7d5406, so its sample is older than main. The defect does not change.

## Unresolved Items

- **U-1 Owner confirmation of the skip decision**: The issue allows a skip or another non-success outcome. The record decides skip (D-1). The owner can request a fail. A fail changes FR-004 to FR-006 and needs a different tally path.
- **U-2 Remediation issues**: R-1 and R-2 need separate issues. The orchestrator files them after the owner accepts this record.
- **U-3 Structured logging reading**: Principle V asks for structured logs in each new module. The new module writes a structured telemetry event and uses standard logging, as its sibling modules do. The owner must confirm this reading.
- **U-4 Complexity result**: The radon result for `_run_single_option` is unknown until T-LOCAL-GATES runs. `plan.md` gives the decision rule for a failure.
- **U-5 Telemetry summary status**: A-3 stays open until a follow-up change. Owners of telemetry consumers must know that a skip-only run can report status `pass`.
- **U-6 Stub resolution**: The regression stub must give the same `InputUtils` class to the resolver and the runner. The first test run confirms this.
- **U-7 Code search coverage**: The code search index can lag the default branch. RC-55 records the result at the time of this review.
