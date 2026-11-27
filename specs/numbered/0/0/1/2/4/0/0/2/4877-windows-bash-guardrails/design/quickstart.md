# Quickstart: Windows Bash Guardrail Skips

## Prerequisites

- A Windows 11 host with PowerShell 7 and the `.venv` environment from `scripts/bootstrap_worktree.py`. See `documentation/development-setup.md`, section Step 2.
- A checkout on branch `fix/4877-windows-bash-guardrails`, rebased onto `main`.
- The repository root as the working directory.

## Scenario 1: Reproduce the failure before the change

Run the two modules on the Windows host:

```powershell
.venv\Scripts\python.exe -m pytest tests/guardrails/e2e_timeout_budget/test_browser_installation.py tests/guardrails/test_snmp_base_oid_defaults.py -rs -q
```

Expected result on a host where bash runs: 19 failed and 12 passed. The issue reports the same 19 failures. This expectation stays unverified (research U-1) until a run confirms it.

## Scenario 2: Verify the Windows result after the change

Run the same command from Scenario 1.

Expected result: `11 passed, 20 skipped`. The short summary lists each skip reason with its count. Each reason names issue #4877. The exit code is 0, because a skip does not fail the run.

## Scenario 3: Verify the Ubuntu result

Run this command on an Ubuntu host with bash:

```bash
python -m pytest tests/guardrails/e2e_timeout_budget/test_browser_installation.py tests/guardrails/test_snmp_base_oid_defaults.py -q
```

Expected result: `31 passed`, with no skipped case.

## Scenario 4: Verify the guards and the documentation

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_container_policy_docs.py -q
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 changelog.d\issue-4877-windows-bash-guardrails.md
```

Expected result: both pytest runs pass. Each `ste-linter` command scores its file at 80 or above.

## Scenario 5: Verify the static rules

Search both modules for a module-level mark:

```powershell
Select-String -Path tests\guardrails\e2e_timeout_budget\test_browser_installation.py, tests\guardrails\test_snmp_base_oid_defaults.py -Pattern "^pytestmark"
```

Expected result: no output.

Search the changed files for characters outside ASCII:

```powershell
Select-String -Path tests\guardrails\e2e_timeout_budget\test_browser_installation.py, tests\guardrails\test_snmp_base_oid_defaults.py, changelog.d\issue-4877-windows-bash-guardrails.md -Pattern "[^\x00-\x7F]"
```

Expected result: no output.

List the changed paths against `main`:

```powershell
git diff --name-only origin/main
```

Expected result: no path under `src/`, and no `MistHelper.py` path.

## Scenario 6: Run the repository gates

```powershell
python -m ruff check .
python -m black --check .
symbol-diff --base origin/main tests/guardrails/e2e_timeout_budget/test_browser_installation.py
symbol-diff --base origin/main tests/guardrails/test_snmp_base_oid_defaults.py
bandit -c pyproject.toml -r . -q
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected result:

- Ruff prints `All checks passed`.
- Black reports that no file needs a change.
- Each symbol-diff command prints `no module-level name changed`.
- Bandit prints no finding.
- The test quality gate prints `gate: 0 new findings vs baseline`.

After the local commit, run the required test quality check from `.github/copilot-instructions.md` before you push.
