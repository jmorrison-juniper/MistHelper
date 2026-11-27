# Quickstart: Windows Symlink Privilege in the Spec-Route Contract Guard

This guide reproduces issue #4778 and checks the fix. Run each command from the worktree root. Use the Python 3.15.2 environment of the repository.

## Prerequisites

- A Windows host with a standard account that lacks the symlink privilege.
- PowerShell 7 on PATH. Check it with `pwsh --version`.
- The environment from `scripts/bootstrap_worktree.py`. Activate it with `.venv\Scripts\Activate.ps1`.
- For the fix check, the branch `fix/4778-windows-symlink-privilege`.

## Scenario 1: Reproduce the failure on main

```powershell
python -m pytest "tests/guardrails/test_spec_route_contract.py::test_unsafe_feature_selection_fails[symlink]" -q
```

Expected: the case errors at setup. The error names `symlink_to` and WinError 1314. Issue #4778 reports this result.

## Scenario 2: Check the fallback methods on any host

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py -k TestLinkSelectionFallback -q
```

Expected: the three tests pass.

## Scenario 3: Report the link kind on the Windows host

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py -k unsafe_feature_selection --log-cli-level=INFO -rs -q
```

Expected: the log names `symlink` or `junction`. A skip prints its cause in the summary. Record the result in the pull request.

## Scenario 4: Prove that the guard still fails without the reparse-point check

1. On the task branch, remove the `ReparsePoint` condition at `.specify/scripts/powershell/common.ps1` line 258.
2. Run `python -m pytest tests/guardrails/test_spec_route_contract.py -k unsafe_feature_selection -q`.
3. Expected: at least one assertion fails.
4. Revert the edit before the commit.

Warning: a commit that keeps this edit reaches `main` after the merge. Revert the edit before you commit.

## Scenario 5: Lint, format, and the test module

```powershell
python -m ruff check .
python -m black --check .
python -m pytest tests/guardrails/test_spec_route_contract.py
```

Expected: `All checks passed`, then `No file needs a change`, then all tests pass.

## Scenario 6: Style of the setup document

```powershell
ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md
```

Expected: the file scores 80 or above.
