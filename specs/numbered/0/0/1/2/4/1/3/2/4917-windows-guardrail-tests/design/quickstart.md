# Quickstart: Windows guardrail test failures

This page gives the exact steps to reproduce the failures and the exact commands that verify the fix. Run the commands from the repository root in PowerShell.

## 1. Reproduce the failures before the change

Use the `main` checkout at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on a Windows 11 workstation with the environment folder from the bootstrap.

1. Check that PATH lacks `uv`. Run `Get-Command uv -ErrorAction SilentlyContinue`. Expect no output.
2. Run the guardrail suite. Run `.venv\Scripts\python.exe -m pytest -q tests\guardrails`.
3. Expect 23 failed tests in six files: `test_browser_installation.py` (10), `test_snmp_base_oid_defaults.py` (9), `test_dependency_export.py` (1), `test_spec_route_contract.py` (1), `local_test_quality_loop\test_scope.py` (1), and `test_analytics_package_structure.py` (1).

The issue reports 1,183 passed, 23 failed, and 9 skipped for this run. This record does not reproduce those counts (U-1).

## 2. Verify each changed file after the change

Run each command from the repository root. Each command names the expected result.

| File | Command | Expected result |
| --- | --- | --- |
| `test_browser_installation.py` | `python -m pytest tests\guardrails\e2e_timeout_budget\test_browser_installation.py -q -rs` | 8 passed and 11 skipped. Each skip names Ubuntu CI. |
| `test_snmp_base_oid_defaults.py` | `python -m pytest tests\guardrails\test_snmp_base_oid_defaults.py -q -rs` | 3 passed and 9 skipped. Each skip names Ubuntu CI. |
| `test_dependency_export.py` | `python -m pytest tests\guardrails\test_dependency_export.py -q` | 5 passed. The export test finds `uv` in the environment folder when PATH lacks it. |
| `test_spec_route_contract.py` | `python -m pytest tests\guardrails\test_spec_route_contract.py -q -rs` | No failure. The symlink case skips with the privilege reason when the account lacks the privilege. |
| `test_scope.py` | `python -m pytest tests\guardrails\local_test_quality_loop\test_scope.py -q` | No failure. |
| `test_analytics_package_structure.py` | `python -m pytest tests\guardrails\test_analytics_package_structure.py -q` | No failure. |
| `development-setup.md` | `ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md` | Score 80 or above. |
| Changelog fragment | `python -m pytest tests\guardrails\test_changelog_fragment_policy.py -q` | No failure. |

## 3. Run the full guardrail suite on the Windows workstation

Run `python -m pytest -q tests\guardrails`.

Predicted result, when the account lacks the symbolic link privilege:

- 0 failed
- 1186 passed
- 30 skipped

Predicted result, when the account holds the symbolic link privilege:

- 0 failed
- 1187 passed
- 29 skipped

The prediction adds these changes to the issue baseline. Three failing cases pass. One new case passes. The 19 Bash cases skip. The symlink case skips without the privilege. The `None` case of the browser mirror test skips.

A prediction does not prove a result. Record the actual counts from this run in the pull request body.

## 4. Verify the Ubuntu CI result

After T-PR creates the pull request, run this command from the worktree.

```powershell
gh pr checks -R jmorrison-juniper/MistHelper --watch
```

Expect each required check to report success. The Ubuntu pytest shard for `tests/guardrails` must collect one more test than `main`, and no Ubuntu test gains a skip.

## 5. Confirm the change set

Run this command from the worktree.

```powershell
git diff --name-status main
```

Expect eight rows. Seven rows start with `M`, and one row starts with `A` for `changelog.d/issue-4917-windows-guardrail-tests.md`. No row names a path under `src\`, `.github\workflows\`, or a dependency file.
