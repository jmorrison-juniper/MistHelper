# Quickstart: Restart Healthy Reset Test

Use these steps to reproduce the restart class and to verify this change. Run each command from the repository root on Windows 11 with PowerShell. The commands use the pinned Python 3.15.2 environment. The issue used Python 3.13.13, which the repository does not support.

## Prerequisites

1. Install Python 3.15.2 with UV: `uv python install 3.15.2`
2. Create the environment: `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`
3. Activate the environment: `.venv\Scripts\Activate.ps1`

The bootstrap installs the locked dependencies and the browser for browser tests. It also sets the Git credential account. Source: `documentation/development-setup.md` lines 29 and 32 on main.

## Reproduce the restart class

Run the restart class on the pinned environment:

`python -m pytest tests/unit/container/output_defaults/test_session.py::TestSessionRestarts --no-cov -q`

Expected result: 8 passed.

Run the complete unit suite as the issue did. This run takes about 14 minutes:

`python -m pytest tests/unit --no-cov -q`

Expected result: no failure in `TestSessionRestarts`.

## Repeat the restart class (success criterion SC-002)

Run the restart class ten times in a row:

`1..10 | ForEach-Object { python -m pytest tests/unit/container/output_defaults/test_session.py::TestSessionRestarts --no-cov -q }`

Expected result: ten runs, each with 8 passed.

## Read CI evidence (read-only)

Show the restart lines from main run 45774119357:

`gh run view 45774119357 -R jmorrison-juniper/MistHelper --log | Select-String -Pattern "test_actual_restart_controls_match_base|test_restart_controls_ignore_startup_stall|test_clock_exhaustion_refuses_unmeasured_launch"`

Show the failed jobs of run 45767339705:

`gh run view 45767339705 -R jmorrison-juniper/MistHelper --log-failed`

Confirm that PR 4555 is merged:

`gh pr view 4555 -R jmorrison-juniper/MistHelper --json state,mergedAt,headRefOid`

Confirm that the merge commit is in main. Expected status: `ahead`.

`gh api repos/jmorrison-juniper/MistHelper/compare/02ffc4ac1ad65f5018a93b548fc65bc70a445d40...main --jq .status`

## Local gates for this change

Fetch the base branch before the test quality gate:

`git fetch --no-tags origin +refs/heads/main:refs/remotes/origin/main`

Run each command. Each command must report the expected result from the local gates table in `.github/copilot-instructions.md` (lines 57 to 74 on main).

1. `python -m py_compile MistHelper.py` (no output)
2. `python -m ruff check .` (All checks passed)
3. `python -m black --check .` (no file needs a change)
4. `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` (Success)
5. `python -m pytest tests/unit/container/output_defaults/test_session.py` (all tests pass)
6. `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` (one summary line for each shard)
7. `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` (one summary line for each shard)
8. `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` (the preflight passes)
9. `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` (gate: 0 new findings vs baseline)
10. `radon cc tests/unit/container/output_defaults -j | complexity-gate --max 10` (no block above complexity 10)
11. `bandit -c pyproject.toml -r tests/unit/container/output_defaults -q` (no finding)
12. `symbol-diff --base origin/main tests/unit/container/output_defaults/test_session.py` (no module-level name changed)
13. `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\2\1\1\1\1\4531-restart-healthy-reset-delay\spec.md specs\numbered\0\0\1\2\1\1\1\1\4531-restart-healthy-reset-delay\plan.md specs\numbered\0\0\1\2\1\1\1\1\4531-restart-healthy-reset-delay\tasks.md specs\numbered\0\0\1\2\1\1\1\1\4531-restart-healthy-reset-delay\analysis.md specs\numbered\0\0\1\2\1\1\1\1\4531-restart-healthy-reset-delay\design\research.md specs\numbered\0\0\1\2\1\1\1\1\4531-restart-healthy-reset-delay\design\data-model.md specs\numbered\0\0\1\2\1\1\1\1\4531-restart-healthy-reset-delay\design\quickstart.md specs\numbered\0\0\1\2\1\1\1\1\4531-restart-healthy-reset-delay\design\checklists\requirements.md` (each file scores 80 or above)

Not applicable locally: coverage, dependency audit, pylint, vulture, docstrings, menu reference, and the safe sweep. Each has a reason in the pull request body. See `tasks.md`, task T-LOCAL-GATES.

## Remote checks after the pull request exists

Run `gh pr checks --watch` from the branch worktree. Wait for every required check. Confirm that the root-units shard log shows eight restart cases with status PASSED.
