# Quickstart: Locked Bootstrap With a Configured Pip Index

This page gives the exact steps to reproduce issue #4774 and to verify the repair. Run each command in PowerShell from the repository root unless a step says otherwise.

## Preconditions

- Owner decision D-1 is recorded before any step that changes code (tasks T011 to T015).
- The reproduction steps in Step 3 run on main. They need no code change.
- The scratch folder `test-artifacts\issue4774` is ignored by Git (research.md, R71).

## Step 1: Create the worktree

Create a separate worktree for the branch. Do not switch branches in the owner checkout (AGENTS branch rule, research.md, R03).

```powershell
git worktree add ..\MistHelper-4774 -b fix/4774-locked-bootstrap-pip-mirror main
cd ..\MistHelper-4774
```

## Step 2: Record the tool versions

Record these values in the issue comment. They identify the uv and Python builds used for the run.

```powershell
uv --version
python --version
```

## Step 3: Reproduce the defect on main

Start a listener on the loopback address only. The bootstrap probe needs a TCP connection that succeeds. It does not need a working package index.

```powershell
New-Item -ItemType Directory -Path test-artifacts\issue4774 -Force
$server = Start-Process -FilePath python -ArgumentList '-m', 'http.server', '8765', '--bind', '127.0.0.1' -WorkingDirectory test-artifacts\issue4774 -PassThru
```

### Step 3a: Check the child environment directly

This command shows the uv behavior that the old child environment triggers.

```powershell
$env:UV_INDEX_URL = 'http://127.0.0.1:8765/simple/'
uv sync --locked --extra dev --dry-run
Remove-Item Env:UV_INDEX_URL
```

- Expected on main: exit code 1. The output contains the text `needs to be updated`. This matches the owner observation in comment 6903867178 (research.md, U-1).
- Expected after the change: unchanged. This command bypasses the bootstrap, so it shows uv behavior only.

### Step 3b: Run the bootstrap with a configured index

```powershell
$env:PIP_INDEX_URL = 'http://127.0.0.1:8765/simple/'
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
Remove-Item Env:PIP_INDEX_URL
```

- Expected on main: exit code 1. The output names the locked UV sync failure. It may also name the index mismatch (research.md, U-3).
- Expected after the change, option C: the locked sync uses the lock registry. The command exits 0 when PyPI answers. It exits 1 with a network error when PyPI does not answer (research.md, D-1).
- Caution: the bootstrap creates `.venv` in the worktree and installs packages. Run it only in the test worktree.

Stop the listener.

```powershell
Stop-Process -Id $server.Id
```

## Step 4: Run the behavior tests

Run these commands after tasks T004 to T010 are complete and before task T011 starts.

```powershell
python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py
python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py
```

- Expected on main: eight of the nine new or rewritten tests fail. The failing tests are TST-01, TST-02, TST-03, TST-04, TST-06, TST-07, TST-08, and TST-09.
- Expected on main: TST-05 passes. It guards a repository invariant that already holds.
- Expected on main: the existing tests KT-01 to KT-08 pass.
- Expected after T011 to T014: all nine new or rewritten tests pass. KT-01 to KT-08 pass.

## Step 5: Owner check on the Windows host (SC-002)

Run the default bootstrap with the configured index already set in the environment. Do not print the index value.

```powershell
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
```

- Expected after the change: exit code 0.
- Record on issue #4774: the output of `uv --version`, the names of the pip index settings, and the commit SHA of the tested branch. Do not record the index value or a host name.

## Step 6: Run the local gates

Run each applicable command from task T-LOCAL-GATES in `tasks.md`. Record each result and its count.

```powershell
python -m py_compile scripts/bootstrap_worktree.py
python -m ruff check .
python -m black --check .
python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py
python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_container_build_trigger.py
symbol-diff --base origin/main scripts/bootstrap_worktree.py
bandit -c pyproject.toml scripts/bootstrap_worktree.py -q
radon cc scripts/bootstrap_worktree.py -j | complexity-gate --max 10
ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

- Expected for `symbol-diff`: the two removed names appear. Record them as the documented exception (D-9).

## Cleanup

Caution: the next command deletes only the scratch folder under `test-artifacts`.

```powershell
Remove-Item -Recurse -Force test-artifacts\issue4774
```

After the merge, remove the worktree.

```powershell
cd ..\MistHelper
git worktree remove ..\MistHelper-4774
```
