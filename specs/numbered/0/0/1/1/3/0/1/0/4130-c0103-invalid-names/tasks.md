# Tasks: C0103 naming exceptions in MistHelper.py

**Input**: Numeric record `specs/numbered/0/0/1/1/3/0/1/0/4130-c0103-invalid-names/`. Use `spec.md`, `plan.md`, `design/research.md`, and `design/quickstart.md`.

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `design/research.md`, `design/quickstart.md`.

**Tests**: The guard test cases in task T003 are required by FR-008.

**Organization**: Tasks are grouped by user story. Each story can be checked on its own.

## Format

- **[P]**: The task can run in parallel because it changes a different file.
- **[US#]**: The user story that the task serves.
- **Verification**: One command from the local gates table in `.github/copilot-instructions.md`. The extra check is named when a task needs one.
- **Status**: `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Verify and Baseline

**Purpose**: Confirm the current state before any edit.

- [ ] **T001** [P] [US1] Verify `web_portal/services/operation.py` has no C0103 finding (FR-001). Path: `web_portal/services/operation.py`. Acceptance: `PARAMETER_REGISTRY = _build_registry()` appears once, at line 915. Verification: Compile gate, `python -m py_compile web_portal\services\operation.py`. Status: verified-present. Evidence: remote blob `39f9446da8648fb245022c63dc382ff38ccece76`, PR #4662 merged.
- [ ] **T002** [US1] Capture the baseline pylint output for `MistHelper.py` (FR-002). Path: `MistHelper.py` (read only). Acceptance: the JSON output lists 25 messages at the lines in `design/research.md`, Table 1. Verification: Compile gate, `python -m py_compile MistHelper.py`. Extra check: `design/quickstart.md`, step 2. Status: open.

## Phase 2: Red Guard

**Purpose**: Prove that the guard detects the current state.

- [ ] **T003** [P] [US3] Add three guard test cases to `tests/guardrails/test_src_public_symbol_preservation.py` (FR-008). Acceptance: the three cases fail before tasks T004 to T007. Verification: Tests gate, `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py`. Status: open.

## Phase 3: Exceptions and Rule

**Purpose**: Apply the reviewed exceptions. Each edit keeps every name unchanged.

- [ ] **T004** [US2] Add the module-name rule to `pyproject.toml` under `[tool.pylint.basic]` (FR-003, FR-005). Acceptance: `module-rgx` accepts `MistHelper` and snake_case names, with a TOML comment. No other key changes. Verification: Lint gate, `python -m ruff check .`. Depends on: T002. Status: open.
- [ ] **T005** [US1] Add the reviewed pragma to lines 182, 183, 184, 1082, 1096, 1114, and 1117 in `MistHelper.py` (FR-006, FR-007). Acceptance: each line keeps its code. Each line ends with `  # pylint: disable=invalid-name  # <reason>`. Verification: Compile gate, `python -m py_compile MistHelper.py`. Depends on: T002. Status: open.
- [ ] **T006** [US1] Add the reviewed pragma to these `MistHelper.py` lines: 1123, 1125, 1126, 1135, 1136, 1137, 1150, 1172, and 1174 (FR-006, FR-007). Acceptance: the same format as T005. Verification: Compile gate, `python -m py_compile MistHelper.py`. Depends on: T005. Status: open.
- [ ] **T007** [US1] Add the reviewed pragma to these `MistHelper.py` lines: 2345, 2458, 2460, 2461, 2463, 2474, 2475, and 2479 (FR-006, FR-007). Line 2345 is the `def SSHClient` line. Acceptance: the same format as T005. Verification: Compile gate, `python -m py_compile MistHelper.py`. Depends on: T006. Status: open.
- [ ] **T008** [P] [US3] Add the changelog fragment `changelog.d/issue-4130-c0103-invalid-names.md` (FR-009). Acceptance: one `###` heading and one `**Changed**` bullet that names issue 4130. Verification: Tests gate, `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`. Extra check: STE gate on the fragment. Status: open.

## Phase 4: Reconcile and Green

**Purpose**: Confirm the predicted list and the guard.

- [ ] **T009** [US1] Reconcile the pragmas with pylint (FR-002, FR-005, FR-006). Paths: `MistHelper.py`, `pyproject.toml`. Acceptance: the C0103 JSON output is `[]` for both files. Run pylint with `--enable=useless-suppression`. Remove each pragma that suppresses nothing. Verification: Compile gate, `python -m py_compile MistHelper.py`. Extra check: `design/quickstart.md`, steps 1 and 2. Depends on: T004, T005, T006, T007. Status: open.
- [ ] **T010** [US3] Run the guard test cases until all pass (FR-008). Path: `tests/guardrails/test_src_public_symbol_preservation.py`. Acceptance: three cases pass. Verification: Tests gate, `python -m pytest tests/guardrails/test_src_public_symbol_preservation.py`. Depends on: T003, T009. Status: open.
- [ ] **T011** [P] [US2] Copy the record from the draft folder to `specs/numbered/0/0/1/1/3/0/1/0/4130-c0103-invalid-names/` (FR-011). Acceptance: the copy matches the draft file for file. Verification: STE gate, `ste-linter --config .ste-linter.toml --min-score 80` on each record Markdown file. Depends on: T010. Status: open.
- [ ] **T012** [P] [US3] File the follow-up issue for deferred renames and the fallback redesign (FR-010). Acceptance: one open issue titled `Lint: C0103 -- replace module-level optional bindings and fallback names`. Labels: `lint`, `MistHelper.py`. The body lists the 24 kept names. Verification: none from the local gates table, because the task changes no repository file. Read the issue with `gh issue view <number> -R jmorrison-juniper/MistHelper --json title,labels`. Status: open.

## Phase 5: Final Tasks

**Purpose**: Gates, pull request, remote checks, and merge.

- [ ] **T-LOCAL-GATES** Run each applicable local gate in `design/quickstart.md` (FR-004, FR-007, FR-011). Paths: `MistHelper.py`, `pyproject.toml`, `tests/guardrails/test_src_public_symbol_preservation.py`, `changelog.d/issue-4130-c0103-invalid-names.md`, and the record folder. Acceptance: each gate matches its expected result. The Symbols gate confirms that no module-level name changed (FR-004). Record each result in the pull request body. Verification: Symbols gate, `symbol-diff --base origin/main MistHelper.py`. Depends on: T008, T009, T010, T011. Status: open.
- [ ] **T-PR** Commit, push, and open the pull request (FR-011, FR-012). Branch: `chore/4130-c0103-invalid-names`. Commit subject and pull request title: `chore(lint): keep reviewed C0103 names in MistHelper.py`. The body contains `Closes #4130`, the changed-file list, the gate results, and the rollback note. Before the push, run the overlap check `gh pr list -R jmorrison-juniper/MistHelper --state open --json number,files`. Verification: Symbols gate, `symbol-diff --base origin/main MistHelper.py`. Depends on: T-LOCAL-GATES. Status: open.
- [ ] **T-REMOTE-CI** Watch the remote checks (FR-011). Command: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`. Acceptance: each required check passes. Verification: Full tests gate, the two `pytest-chunks` commands in `design/quickstart.md`, as run by CI. Depends on: T-PR. Status: open.
- [ ] **T-MERGE** Add the `auto-merge` label after every check passes and the orchestrator authorizes the merge (FR-011). Verification: none from the local gates table, because the task changes no repository file. Read the merge state with `gh pr view <number> -R jmorrison-juniper/MistHelper --json state,autoMergeRequest`. Depends on: T-REMOTE-CI. Status: open.

## Dependencies

- T002 depends on no task.
- T003 depends on no task.
- T004 and T005 need T002.
- T006 depends on T005. T007 depends on T006.
- T009 depends on T004, T005, T006, and T007.
- T010 depends on T003 and T009.
- T011 depends on T010.
- T-LOCAL-GATES depends on T008, T009, T010, and T011.
- T-PR depends on T-LOCAL-GATES. T-REMOTE-CI depends on T-PR. T-MERGE depends on T-REMOTE-CI.

## Notes

- Keep one pragma per flagged line. Do not add a pragma to any other line (FR-006).
- Do not rename any module-level name (FR-004).
- Do not change `web_portal/services/operation.py` (decision D-4).
