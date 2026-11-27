# Quickstart: Locked Worktree Bootstrap

**Scope**: The exact reproduction steps and verification commands for issue 4591. Run every command from the repository root in PowerShell.

## 1. Preconditions

- Set the GitHub variables before each `gh` command. The token value is never printed.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

- Keep the checkout read-only for this step. The static steps below change no file.

## 2. Static Reproduction (no tool run)

### Step 2.1: Confirm the lock on `main`

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/uv.lock?ref=main" --jq .sha
```

Expected result: `5445b4eb382dc9f6dd5c351ba40c521f01f93165`.

```powershell
(Select-String -LiteralPath uv.lock -Pattern 'source = \{ registry = "https://pypi.org/simple" \}').Count
```

Expected result: `195`.

```powershell
Select-String -LiteralPath uv.lock -Pattern 'source = \{ registry = "https://pypi.org/simple" \}' | Select-Object -First 1
```

Expected result: a line with the number 8.

### Step 2.2: Confirm the reporter-era sync line

```powershell
git show c57c9b704:scripts/bootstrap_worktree.py | Select-String -Pattern 'Synchronizing project dependencies from uv.lock'
```

Expected result: one match at line 282.

### Step 2.3: Confirm the current child environment and sync command

```powershell
Select-String -LiteralPath scripts\bootstrap_worktree.py -Pattern 'UV_NATIVE_TLS|"--locked"'
```

Expected result: matches at lines 417 and 466.

### Step 2.4: Confirm the CI lock result

```powershell
gh run view --job 139753527647 -R jmorrison-juniper/MistHelper --log | Select-String -Pattern 'Resolved'
```

Expected result: a line `Resolved 197 packages`, from the passing job `Dependency lock and exports`.

## 3. Live Reproduction (after gate G-1)

Caution: the bootstrap creates a `.venv` directory in the worktree where it runs. Run it in a new worktree only.

### Step 3.1: Record the uv version

```powershell
uv --version
```

Record the output on the issue. Do not record a token or a host name.

### Step 3.2: Create a new worktree

```powershell
git worktree add ..\MistHelper-4591-repro -b repro/4591-locked-worktree-bootstrap origin/main
```

### Step 3.3: Run the bootstrap in the new worktree

```powershell
Set-Location ..\MistHelper-4591-repro
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py 2>&1 | Tee-Object -FilePath ..\bootstrap-4591-output.txt
```

Expected result on `main`: with a configured index, the final message names the index cause. After the change, the message also names the active index variables, and it holds no URL.

Caution: `Tee-Object` writes the output file outside the repository. Remove the file after the reporter copies its content to the issue.

### Step 3.4: Remove the new worktree

```powershell
Set-Location ..\..\MistHelper
git worktree remove ..\MistHelper-4591-repro
```

Caution: removing the worktree deletes its `.venv`. Run the bootstrap again in a new worktree to restore it.

## 4. Verification Commands (task T-LOCAL-GATES)

Run each command from the repository root after the change. Each row names the expected result.

| Gate | Command | Expected result |
|---|---|---|
| Compile | `python -m py_compile scripts/bootstrap_worktree.py` | No output |
| Lint | `python -m ruff check scripts tests/unit/scripts` | `All checks passed` |
| Format | `python -m black --check scripts/bootstrap_worktree.py tests/unit/scripts/test_bootstrap_worktree_uv.py` | No file needs a change |
| Changed tests | `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py` | All tests pass |
| Sibling tests | `python -m pytest tests/contract/packaging/test_bootstrap_compose_provider.py tests/unit/scripts/test_browser_driver_bootstrap.py tests/unit/scripts/test_browser_download_certificates.py` | All tests pass |
| Full tests, shard 1 | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` | One summary line, no failed chunk |
| Full tests, shard 2 | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | One summary line, no failed chunk |
| Test quality preflight | `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | Passes |
| Test quality, committed change | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc scripts/bootstrap_worktree.py -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10 |
| Security lint | `bandit -c pyproject.toml -r scripts -q` | No finding |
| Symbols | `symbol-diff --base origin/main scripts/bootstrap_worktree.py` | `no module-level name changed`, exit code 0 |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md` | Score 80 or above |
| Changelog policy | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` | Passes |
| Spec route and folders | `python -m pytest tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py` | Passes |

Gates that do not apply to this change:

- mypy: `scripts/bootstrap_worktree.py` is not in `MYPY_PATHS` (`.github/workflows/ci.yml`, line 93).
- pylint, pydocstyle, interrogate, and vulture: the CI paths exclude `scripts/` (`.github/workflows/ci.yml`, lines 101 to 107).
- Coverage: the CI measures `src/` only.
- Safe sweep and menu reference: no menu operation changes.
- pip-audit: no dependency file changes.
- Ops portal, ops platform, and container build: no file in those trees changes.

## 5. Cleanup

- Delete `..\bootstrap-4591-output.txt` after the output reaches the issue.
- Keep no scratch file in the repository.
