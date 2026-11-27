# Quickstart: Entry-point test quality for HTTP status scope

Run each command from the repository root. Use the local `.venv` on this host. Each command comes from the local gates table (RC-63) or from the test quality procedure (RC-47).

## 1. Reproduce the issue at its cited revision

Use a separate worktree so that the current checkout stays unchanged.

1. Create the worktree: `git worktree add ..\MistHelper-4828-repro 838046104f606c008b034e0176ccd34ddf44a5f9`
2. Change to the worktree: `cd ..\MistHelper-4828-repro`
3. Run the gate from the issue body, with the Windows command form: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
4. Expected result at that revision: the output names `missing_fm_http_4xx` and `missing_fm_http_5xx` for the help test file, and `gate: 2 new findings vs baseline` (issue body).
5. Return to the main checkout and remove the worktree: `git worktree remove ..\MistHelper-4828-repro`

Caution: Remove the worktree after the check. The worktree holds a second full copy of the repository.

## 2. Check the present state on main

Run each search from the main checkout. Each search reads files only.

1. Help file: `Select-String -Path tests\unit\config\foundation\support\refactors\runtime\entrypoint\test_help_invocation_side_effect_free.py -Pattern "ApplicationBootstrap"` returns no line (RC-01).
2. Reject-flag file: `Select-String -Path tests\unit\config\foundation\support\refactors\runtime\entrypoint\test_reject_unsupported_flag_variants.py -Pattern "ApplicationBootstrap"` returns one match at line 118. That match is a string target, not an import (RC-05, RC-07).
3. Argument call in the module: `Select-String -Path tests\unit\config\foundation\support\refactors\runtime\entrypoint\test_main_entrypoint.py -Pattern "ApplicationBootstrap\(argv"` returns line 162 before T003 and no line after T003 (RC-12).

## 3. Run the entry-point tests

1. `python -m pytest tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_help_invocation_side_effect_free.py` prints `15 passed`.
2. `python -m pytest tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_reject_unsupported_flag_variants.py` prints `3 passed`.
3. `python -m pytest tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py` passes. After T003 the module holds one case fewer.

## 4. Run the preflight and the test quality gate

1. Preflight: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` prints `1 passed`.
2. Changed-file gate, used before T007: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` prints `gate: 0 new findings vs baseline`.
3. Full-suite gate, used after T007: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` prints `gate: 0 new findings vs baseline`.

## 5. Check the pin and the lock

1. Lock check: `uv lock --check` exits with code 0 (RC-25).
2. Export guard: `python -m pytest -s -q tests/guardrails/test_dependency_export.py` passes.
3. Pin match: `Select-String -Path pyproject.toml,requirements-dev.txt -Pattern "misthelper-devtools"` shows one commit in both files. `Select-String -Path uv.lock -Pattern "misthelper-devtools"` shows the same commit.

## 6. Check the baseline diff

1. Run `git diff --numstat origin/main -- .github/test-quality-baseline.json`.
2. The first number in the output is the count of added lines. It must equal 0 (SC-004).

## 7. Run the static checks for the test files

1. `python -m py_compile MistHelper.py` prints no output (RC-60).
2. `python -m ruff check .` prints `All checks passed` (RC-53).
3. `python -m black --check .` reports that no file needs a change.
4. `bandit -c pyproject.toml -r . -q` prints no finding.

## 8. Check the module-level names

Run `symbol-diff --base origin/main tests/unit/config/foundation/support/refactors/runtime/entrypoint/test_main_entrypoint.py`. The output reads `no module-level name changed`, and the exit code is 0.
