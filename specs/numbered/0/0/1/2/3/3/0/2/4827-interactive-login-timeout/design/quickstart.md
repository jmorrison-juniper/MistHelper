# Quickstart: Interactive login request timeout

**Record**: `specs\numbered\0\0\1\2\3\3\0\2\4827-interactive-login-timeout`
**Branch**: `fix/4827-interactive-login-timeout`

## 1. Prerequisites

1. Open PowerShell in the repository root. Use a worktree for the implementation branch, as AGENTS.md requires.
2. Create the environment. Run `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`, then run `.venv\Scripts\Activate.ps1`.
3. Do not set `MIST_APITOKEN` or `MIST_API_TOKEN` in the shell for tests. The tests need no credential and no network.
4. Before each `gh` command, set the host and the token. Use the two lines that section 2 shows.

## 2. Confirm the merged defect fix on main (read-only)

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1 --jq '.tree[] | select(.path | test("session_timeout")) | .path'
```

Expected result: no output (RC-07). The import regression test passes:

```powershell
python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py::TestImportResolution -q
```

Expected result: one test passes (RC-09, RC-10).

## 3. Reproduce the open timeout gap

Add the new tests from `tasks.md` (T004, T005, T006) before the implementation (T008). Then run the loopback test:

```powershell
python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py -k loopback -q
```

Expected result before T008: the test fails with an attribute error, because `_apply_request_timeout` does not exist yet. That failure proves the test runs red.

Expected result after T008 without the adapter: the test fails because no `ReadTimeout` occurs inside the one-second bound. The test then waits for the server cap of five seconds.

## 4. Confirm the SDK pin

```powershell
python -m pytest tests/integration/test_mistapi_sdk_compatibility.py -q
```

Expected result: each test in the file passes on mistapi 0.64.1 (RC-64).

## 5. Run the local gates after the change

Run each command from the repository root. Each command names its expected result.

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile src\mist\access\auth\interactive\login_orchestrator.py src\foundation\support\refactors\initialize_mist_session_interactive.py` | No output |
| Lint | `python -m ruff check .` | `All checks passed!` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| Tests | `python -m pytest tests/unit/marvis/mist/access/auth tests/unit/config/foundation/support/refactors/runtime/session tests/unit/refactors/test_initialize_mist_session.py tests/integration/test_mistapi_sdk_compatibility.py tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_src_domain_structure.py -q -p no:cacheprovider` | All tests pass |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | Coverage of 80 percent or above |
| Test quality | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` (run after the local commit) |
| Complexity | `radon cc src\mist\access\auth\interactive -j \| complexity-gate --max 10` | No block above complexity 10 |
| Security lint | `bandit -c pyproject.toml -r src\mist\access\auth\interactive -q` | No finding |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation, and coverage of 90 percent or above |
| Symbols | `symbol-diff --base origin/main src\mist\access\auth\interactive\login_orchestrator.py` | `no module-level name changed` |
| STE | `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 README.md documentation/operator-guide.md documentation/CONTRIBUTING-MistHelper.md` | Each file scores 80 or above |
| Safe sweep | `python MistHelper.py --test` | Each safe operation completes. Mist API checks skip without a credential. |

The menu reference gate and the ops portal gates do not apply. This change adds no menu operation and changes no portal file.

## 6. Verify the changelog fragment

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
```

Expected result: the guard passes and reports the number of fragments it examined.

## 7. Roll back

Revert the squash commit of the pull request on `main`. The rollback restores the state after PR #4830. The interactive login then sends requests with no time limit again, as it does today.

Caution: a rollback removes the timeout only. It does not restore the removed import.

## 8. Reproduce the reported defect at the base commit

This section gives the reproduction steps from the issue. Run them only in a separate worktree at the base commit. The base commit lacks PR #4830. Do not push from that worktree.

1. Create the worktree with `git worktree add ..\misthelper-4827-base b7a18b7ead7b1de5882bcd288203c015b1eef792`. Then open that folder in PowerShell and run `.venv\Scripts\Activate.ps1`.
2. Run `.venv\Scripts\pylint.exe src\mist\access\auth\interactive\login_orchestrator.py --fail-under=9.5`. The report from macOS shows `.venv/bin/pylint` with exit code 30 and error E0401 at line 240.
3. Run `git ls-files '*session_timeout*'`. The result has no tracked path.
4. Remove the worktree after the check with `git worktree remove ..\misthelper-4827-base`.

Caution: a worktree on the base commit runs the old code. Its results describe the base state, not the current `main`.

