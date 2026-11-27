# Quickstart: Weak zero-assertion triage

These steps reproduce the current state and verify each slice. Run each command from the repository root. Read `.github/copilot-instructions.md` before you change a test file.

## Prerequisites

- Python 3.15.2 in `.venv`, created with `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`.
- The worktree for the slice branch. Do not run `git checkout` in a checkout that another session uses.
- `gh` signed in to `jmorrison-juniper`. Set `$env:GH_HOST='github.com'` and the account token variable named in the operator guide. Never print a token value.

## Step 1: Confirm the pinned analyzer

Open `.venv\Lib\site-packages\misthelper_devtools-0.6.4.dist-info\direct_url.json`. The `commit_id` value must equal `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.

Then run the preflight. It reads the inputs and checks the procedure against the live job.

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Stop when the preflight fails. Stop when the installed commit differs from the pin.

## Step 2: Run the full-suite gate

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected output: a `gate_scope` line, a `gate: 0 new findings vs baseline` line, and `test_quality_analyzer_output\report.json`. Record the count of `weak_zero_assertions` findings in the pull request body. The expected count is 244 before T004.

## Step 3: Run the changed-from gate for a slice

Set the base branch, fetch it, and resolve it.

```powershell
$BASE_REF = "main"
git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
git rev-parse --verify "origin/${BASE_REF}^{commit}"
```

Then run the gate against the committed slice.

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Commit the intended change first. The command stops when a staged, unstaged, or untracked change remains.

## Step 4: Run each changed test file alone

```powershell
python -m pytest tests/unit/export/test_org_template_exporter.py
```

Replace the path with each changed file. Run the file again after each edit. A file that passes only in the full run changes shared state, so repair the test that changes it.

## Step 5: Prove each repaired test

Create the control plugin under `test-artifacts\`. That folder is git-ignored. The plugin applies one in-memory mutation to the code under test. Then run the repaired test with the plugin, and expect a failure. Run the same test without the plugin, and expect a pass.

```powershell
$env:PYTHONPATH = 'test-artifacts'
python -m pytest -p weak_zero_control tests/unit/export/test_org_template_exporter.py::TestExportOneTemplate::test_exception_is_logged_not_raised
Remove-Item Env:PYTHONPATH
```

Record the two results in the pull request body. Remove the plugin file when the slice ends.

## Step 6: Lint, format, and type-check

```powershell
python -m ruff check .
python -m black --check .
python -m mypy $MYPY_PATHS --config-file pyproject.toml
```

Read `MYPY_PATHS` from `.github/workflows/ci.yml`. Expected results: `All checks passed`, no file that needs a change, and `Success`.

## Step 7: Check symbols

```powershell
symbol-diff --base origin/main tests/unit/export/test_org_template_exporter.py
```

Expected output: `no module-level name changed`, with exit code 0.

## Step 8: Clean up

Remove the control plugin. Remove the worktree after the merge. Clear the `PYTHONPATH` variable when the slice ends.

Warning: Removing another user's volume deletes that user's data, and the loss cannot be undone. Do not run a system prune on a shared host.
