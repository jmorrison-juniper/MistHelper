# Tasks: Locked Bootstrap With a Configured Pip Index

**Input**: Feature record in `specs/numbered/0/0/1/2/3/0/4/4/4774-locked-bootstrap-pip-mirror/`. Design details appear in `plan.md` and `design/`.

**Gate**: Owner decision D-1 must precede tasks T011 through T015. The tasks assume option C. Re-plan when the owner selects another option.

**Format**: Each task names its requirements, exact repository paths, acceptance statement, one verification command from the local gates table, and status. A status is one of open, verified-present, partial, or absent. The marker `[P]` means the task edits a file that no other open task edits.

**Test IDs**: TST-01 to TST-09 are new or rewritten tests. KT-01 to KT-08 are existing tests that keep their behavior. research.md lists the exact test names.

## Phase 1: Verify the base

### T001 [P] Confirm the base code at main

- **Requirements**: FR-002, FR-003
- **Files**: `scripts/bootstrap_worktree.py`
- **Depends on**: none
- **Acceptance**: Blob `e16515ffa789cca7d0bdd7e9789898588e5f1312` equals main and local HEAD. The symbols cited in R28 to R40 exist at the cited lines.
- **Verification**: `python -m py_compile scripts/bootstrap_worktree.py`
- **Status**: verified-present

### T002 [P] Confirm the lock registry

- **Requirements**: FR-003, FR-005
- **Files**: `uv.lock`
- **Depends on**: none
- **Acceptance**: 195 registry lines name `https://pypi.org/simple` (R43). No registry line names another index (R44).
- **Verification**: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Status**: verified-present

### T003 [P] Confirm the existing tests encode the old mapping

- **Requirements**: FR-015
- **Files**: `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`, `tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Depends on**: none
- **Acceptance**: R51, R52, R53, and R55 assert the configured index as the uv primary or assert an inherited fallback. R57 asserts the mismatch message.
- **Verification**: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`
- **Status**: verified-present

## Phase 2: Write the failing tests first

### T004 Add TST-01 and TST-02 (no configured index in uv, loopback and redaction)

- **Requirements**: FR-002, FR-003, FR-015, FR-016, FR-017
- **Files**: `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` (add after line 357)
- **Depends on**: T003
- **Acceptance**: TST-01 is parametrized over the caller primary, the install file, the global file, and an extra-only setting. It asserts that the sync child receives the lock registry as `UV_INDEX_URL`. It asserts that no configured value appears in any `UV_` setting. TST-02 stubs `PipIndexProbe.fallback_index`. It fails on any socket connection and asserts that no secret appears in captured logs. Both tests fail on main.
- **Verification**: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`
- **Status**: open

### T005 Add TST-03 (one Caution line without a URL)

- **Requirements**: FR-004, FR-017
- **Files**: `tests/unit/scripts/test_bootstrap_worktree_uv.py` (add at the end)
- **Depends on**: T003
- **Acceptance**: A configured index that differs from the lock registry produces exactly one Caution line. The line starts with `Caution:`. It contains no URL, host, or credential. The test fails on main.
- **Verification**: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Status**: open

### T006 Add TST-04 (fail closed without a registry)

- **Requirements**: FR-003
- **Files**: `tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Depends on**: T003
- **Acceptance**: A lock file with no registry line stops the bootstrap with a RuntimeError before the locked sync starts. The message names `uv.lock`. The test fails on main, where the sync starts.
- **Verification**: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Status**: open

### T007 Add TST-05 (repository guard for one public registry)

- **Requirements**: FR-003, FR-005
- **Files**: `tests/unit/scripts/test_bootstrap_worktree_uv.py`, which reads `uv.lock`
- **Depends on**: T003
- **Acceptance**: The guard reads `uv.lock` from the repository root. It asserts one distinct registry equal to `PUBLIC_INDEX_URL`. The guard passes on main. It fails when a second registry appears.
- **Verification**: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Status**: open

### T008 Add TST-06 (guide states the policy)

- **Requirements**: FR-013, FR-015
- **Files**: `tests/unit/scripts/test_bootstrap_worktree_uv.py`, which reads `documentation/development-setup.md`
- **Depends on**: T003
- **Acceptance**: The Package sources section states that the lock registry governs the locked sync. It names `--public-lock-index`. The test fails on main.
- **Verification**: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Status**: open

### T009 Rewrite TST-07, TST-08, and TST-09 and delete the precedence test

- **Requirements**: FR-002, FR-008, FR-009, FR-012, FR-015
- **Files**: `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` (lines 203-219 for TST-07, lines 220-241 for TST-08, lines 131-163 for TST-09, and delete lines 336-357)
- **Depends on**: T004
- **Acceptance**: TST-07 asserts the lock registry for `UV_INDEX_URL` and keeps the parent-environment checks. TST-08 asserts that `apply` sets no `UV_INDEX_URL`, and keeps the pip and alias checks. TST-09 asserts that the second invocation receives the lock registry and no inherited fallback. TST-07 and TST-09 fail on main. The deleted precedence test is covered by TST-01.
- **Verification**: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`
- **Status**: open

### T010 Remove the mismatch test and its import

- **Requirements**: FR-012, FR-015
- **Files**: `tests/unit/scripts/test_bootstrap_worktree_uv.py` (delete lines 258-270, remove the import on line 25)
- **Depends on**: T005
- **Acceptance**: No test imports or asserts `INDEX_MISMATCH_MESSAGE`. KT-03 (R58) and KT-05 (R88) remain and pass after T013.
- **Verification**: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Status**: open

## Phase 3: Implement the policy (after decision D-1)

### T011 Map the lock registry into the locked sync child

- **Requirements**: FR-002, FR-003, FR-006, FR-007, FR-008, FR-009
- **Files**: `scripts/bootstrap_worktree.py` (lines 404-425, 432-447, 462-475)
- **Depends on**: T004, T006, T007, T009, T010, decision D-1
- **Acceptance**: `apply` no longer calls `_effective_sources` (R34). Delete `_effective_sources` (R35). `sync` reads the lock registry with `read_lock_registry` (R31). It stops with one message when the registry is None. It sets `UV_INDEX_URL` to the registry. It keeps `--locked --extra dev` (R36). TST-01, TST-04, TST-07, TST-08, and TST-09 pass. KT-01 and KT-02 pass.
- **Verification**: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`
- **Status**: open

### T012 Add the Caution line for a differing configured index

- **Requirements**: FR-004, FR-017
- **Files**: `scripts/bootstrap_worktree.py` (inside `sync`, lines 462-475)
- **Depends on**: T005, T011
- **Acceptance**: The configured index is the caller `PIP_INDEX_URL`, then the install file setting, then the global file setting. It comes from `self.sources` and the environment. When it differs from the lock registry, the bootstrap logs this exact text: `Caution: the locked sync uses the registry in uv.lock. The configured package index does not change this sync. Your pip configuration is not changed.` TST-03 passes.
- **Verification**: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Status**: open

### T013 Remove the unreachable mismatch branch and its names

- **Requirements**: FR-012
- **Files**: `scripts/bootstrap_worktree.py` (lines 136, 342-347, 477-493, and the docstring at line 20)
- **Depends on**: T011
- **Acceptance**: Delete `INDEX_MISMATCH_MESSAGE` (R30) and `configured_index` (R32). `diagnose_sync_failure` returns `LOCK_DRIFT_MESSAGE` for a stale lock (R38 branch removed). It returns the original error for a current or unknown lock. The docstring at line 20 describes the new rule. KT-03 and KT-05 pass.
- **Verification**: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Status**: open

### T014 Keep the opt-in option and update its help text

- **Requirements**: FR-010
- **Files**: `scripts/bootstrap_worktree.py` (lines 679-683)
- **Depends on**: T011
- **Acceptance**: The option name stays `--public-lock-index`. The help text says that the option uses the public index for one run. It also says that the default already uses the lock registry. KT-04 passes.
- **Verification**: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Status**: open

### T015 [P] Update the setup guide

- **Requirements**: FR-013
- **Files**: `documentation/development-setup.md` (lines 61-66 and 95-106)
- **Depends on**: T011
- **Acceptance**: The lock paragraph and the Package sources section state the lock registry rule and the Caution text. The mistapi row at line 14 stays unchanged (D-11). TST-06 passes.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md`
- **Status**: open

## Phase 4: Changelog and CI guards

### T016 [P] Add the changelog fragment

- **Requirements**: FR-014
- **Files**: `changelog.d/issue-4774-locked-bootstrap-pip-mirror.md`
- **Depends on**: none
- **Acceptance**: The fragment has one `###` heading and one bullet. The bullet uses the type `Fixed` and names issue #4774. KT-06 passes.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: open

### T017 [P] Confirm the CI guards stay unchanged

- **Requirements**: FR-001, FR-019
- **Files**: `.github/workflows/ci.yml` (line 648), `.github/workflows/container-build.yml` (line 95), `tests/guardrails/test_container_build_trigger.py` (line 86)
- **Depends on**: none
- **Acceptance**: Each file keeps its current line (R61, R63, R64). No edit is made to these files. KT-07 and KT-08 pass.
- **Verification**: `python -m pytest tests/guardrails/test_container_build_trigger.py`
- **Status**: verified-present

## Final tasks

### T-LOCAL-GATES

- **Requirements**: FR-018, SC-005
- **Files**: `scripts/bootstrap_worktree.py`, `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`, `tests/unit/scripts/test_bootstrap_worktree_uv.py`, `documentation/development-setup.md`, `changelog.d/issue-4774-locked-bootstrap-pip-mirror.md`, and the Markdown files under `specs/numbered/0/0/1/2/3/0/4/4/4774-locked-bootstrap-pip-mirror/`
- **Depends on**: T011 through T016
- **Acceptance**: Run each applicable command below. Record each result and its count. Expected results: Compile prints no output. Lint prints `All checks passed`. Format reports no file that needs a change. Tests pass. Symbols lists the two removed names as the documented exception (D-9). Security lint reports no finding. Complexity reports no block above 10. Test quality prints `gate: 0 new findings vs baseline`. STE scores 80 or above for each Markdown file. Not applicable: Types, Dead code, Docstrings, and Code quality, because their scopes exclude `scripts/` (R62). Coverage measures `src/` only. Dependency audit, Menu reference, Safe sweep, Ops portal, and Ops platform cover areas this change does not touch.
- **Commands**:
  - `python -m py_compile scripts/bootstrap_worktree.py`
  - `python -m ruff check .`
  - `python -m black --check .`
  - `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`
  - `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
  - `python -m pytest tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_container_build_trigger.py`
  - `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`
  - `symbol-diff --base origin/main scripts/bootstrap_worktree.py`
  - `bandit -c pyproject.toml scripts/bootstrap_worktree.py -q`
  - `radon cc scripts/bootstrap_worktree.py -j | complexity-gate --max 10`
  - `ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md`
  - `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
- **Verification**: `python -m py_compile scripts/bootstrap_worktree.py`
- **Status**: open

### T-PR

- **Requirements**: FR-005, FR-019, SC-004, SC-006
- **Files**: `scripts/bootstrap_worktree.py`, `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`, `tests/unit/scripts/test_bootstrap_worktree_uv.py`, `documentation/development-setup.md`, `changelog.d/issue-4774-locked-bootstrap-pip-mirror.md`, and `specs/numbered/0/0/1/2/3/0/4/4/4774-locked-bootstrap-pip-mirror/`. Stage each path by name.
- **Depends on**: T-LOCAL-GATES
- **Acceptance**: The branch is `fix/4774-locked-bootstrap-pip-mirror`. The commit subject is `fix(bootstrap): keep the locked sync on the lock registry`. The commit includes the Co-authored-by trailer for Copilot App. The pull request body contains `Closes #4774`, the gate results, the symbol-diff exception, and the removed-line count. The pull request title uses the same subject. The push uses `--force-with-lease` only when the owner allows an update. Warning: a force push replaces remote history and cannot restore it.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: open

### T-REMOTE-CI

- **Requirements**: FR-019, SC-003
- **Files**: None changed. The remote run tests the pushed paths listed in T-LOCAL-GATES, and the workflows `.github/workflows/ci.yml` and `.github/workflows/container-build.yml`.
- **Depends on**: T-PR
- **Acceptance**: `gh pr checks --watch` reports each required check as passed. The dependency lock step (R61) passes. The changelog and pull request title checks pass.
- **Commands**: `gh pr checks --watch`
- **Verification**: `python -m pytest tests/guardrails/test_container_build_trigger.py`
- **Status**: open

### T-MERGE

- **Requirements**: FR-019, SC-006
- **Files**: None changed. The merge carries the pushed paths listed in T-LOCAL-GATES.
- **Depends on**: T-REMOTE-CI and the orchestrator authorization
- **Acceptance**: After each check passes and the orchestrator authorizes the merge, add the `auto-merge` label. The squash merge closes issue #4774. Remove the branch and the worktree after the merge.
- **Commands**: `gh pr edit --add-label auto-merge`, then `git worktree remove ..\MistHelper-4774`
- **Verification**: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`
- **Status**: open

## Requirement coverage

Each requirement maps to at least one task and at least one test.

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T017, T-LOCAL-GATES | KT-01 (R50), KT-07 (R64) |
| FR-002 | T004, T009, T011 | TST-01, TST-07 |
| FR-003 | T002, T004, T006, T007, T011 | TST-01, TST-04, TST-05 |
| FR-004 | T005, T012 | TST-03 |
| FR-005 | T002, T007, T-PR | TST-05 |
| FR-006 | T011 | KT-01 |
| FR-007 | T011 | KT-02 (R54) |
| FR-008 | T011 | KT-02, TST-07 |
| FR-009 | T009, T011 | TST-08, KT-02 |
| FR-010 | T014 | KT-04 (R59) |
| FR-011 | T013 | KT-05 (R88) |
| FR-012 | T010, T013 | KT-03 (R58), TST-08 |
| FR-013 | T008, T015 | TST-06 |
| FR-014 | T016 | KT-06 (R65) |
| FR-015 | T003, T004, T009 | TST-01, TST-07, TST-09 |
| FR-016 | T004 | TST-02 |
| FR-017 | T004, T005, T012 | TST-02, TST-03, KT-02 |
| FR-018 | T-LOCAL-GATES | Every TST and KT test |
| FR-019 | T-PR, T-REMOTE-CI | KT-08 (R61) |

## Summary counts

- Tasks: 21 (T001 to T017, T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE).
- Verified-present: T001, T002, T003, T017.
- Open: the remaining 17 tasks.
