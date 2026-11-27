# Quickstart: Windows Path and Symlink Guardrails

Run each command from the worktree root, with the `.venv` of that worktree. The commands use Windows PowerShell 7.

## 1. Reproduce on the untouched branch (Windows)

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py -q -rs -k symlink
python -m pytest tests/guardrails/local_test_quality_loop/test_scope.py -q -k test_git_ignores_poisoned_locations
python -m pytest tests/guardrails/test_analytics_package_structure.py -q -k test_missing_root_fails_with_path_and_cause
```

Expected on the reporter host: three failures.

- The symlink run reports `[WinError 1314] A required privilege is not held by the client`.
- The Git run reports a forward-slash value for the top-level path, and the expected value uses backslashes.
- The analytics run reports `Regex pattern did not match`.

## 2. Verify the fix (Windows)

### 2.1 Symlink skip

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py -q -rs -k symlink
```

Expected on a host without the privilege: `1 skipped`. The reason reads `Host cannot create symlinks: [WinError 1314] A required privilege is not held by the client`. Expected on a host with the privilege: `1 passed`.

### 2.2 Log capture

```powershell
python -m pytest tests/guardrails/test_spec_route_contract.py -q -rs -k symlink -o log_cli=true --log-cli-level=INFO
```

Expected on a host without the privilege, the output holds two log lines. The INFO line starts with `Creating a directory symlink at`. The ERROR line starts with `Cannot create the symlink at`, and then the skip follows. No traceback appears.

### 2.3 Other errors re-raise, and error 1314 skips (one-off check)

This check does not add a repository test (D-7). It writes only under the git-ignored `test-artifacts` folder.

```powershell
@'
import pathlib
import sys
sys.path.insert(0, "tests/guardrails")
import pytest
from test_spec_route_contract import SpecCommandFixture

root = pathlib.Path("test-artifacts") / "symlink-check"
root.mkdir(parents=True, exist_ok=True)
fixture = SpecCommandFixture(root)
target = fixture.feature("specs/live/20261013-182828-parent")

def raise_access_denied(self, link_target, target_is_directory=False):
    error = OSError("[WinError 5] Access is denied")
    error.winerror = 5
    raise error

def raise_privilege_missing(self, link_target, target_is_directory=False):
    error = OSError("[WinError 1314] A required privilege is not held by the client")
    error.winerror = 1314
    raise error

type(root).symlink_to = raise_access_denied
try:
    fixture.symlink(root / "specs" / "linked", target)
except OSError as caught:
    print("re-raised winerror", caught.winerror)
else:
    print("no error")

type(root).symlink_to = raise_privilege_missing
try:
    fixture.symlink(root / "specs" / "linked", target)
except pytest.skip.Exception as skipped:
    print("skipped:", skipped.msg)
else:
    print("no skip")
'@ | python -
```

Expected output:

```text
re-raised winerror 5
skipped: Host cannot create symlinks: [WinError 1314] A required privilege is not held by the client
```

Remove the check folder after the run:

```powershell
Remove-Item -LiteralPath test-artifacts\symlink-check -Recurse -Force
```

## 3. Local gates

Run each command in table order from `.github\copilot-instructions.md` (R-45 to R-52).

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile MistHelper.py` | No output |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Tests | `python -m pytest tests/guardrails/test_spec_route_contract.py -q -rs` | All tests pass, with at most one skip on a host without the privilege |
| Tests | `python -m pytest tests/guardrails/local_test_quality_loop/test_scope.py -q` | All tests pass |
| Tests | `python -m pytest tests/guardrails/test_analytics_package_structure.py -q` | All tests pass |
| Tests | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q` | All tests pass |
| Full tests | The second `pytest-chunks` command of `copilot-instructions.md` (it names `tests\guardrails`) | One summary line for each shard, and no failure |
| Symbols | `symbol-diff --base origin/main tests/guardrails/test_spec_route_contract.py` (repeat for each changed test file) | `symbol_diff: no module-level name changed`, exit code 0 |
| Test quality | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline`. Run it after the commit, because the analyzer reads committed files. |
| Security lint | `bandit -c pyproject.toml -r .` | No finding. The configuration excludes `tests` (R-65). |

Not applicable, with the reason:

- STE: none of the five files named in R-52 changes.
- Types: `MYPY_PATHS` excludes tests (R-61).
- Dead code: `VULTURE_PATHS` excludes tests (R-62).
- Docstrings: `PYDOCSTYLE_PATHS` and `INTERROGATE_PATHS` exclude tests (R-63, R-64).
- Coverage, Complexity, Code quality, Safe sweep, Menu reference, Dependency audit, Ops portal, and Ops platform: no product, package, menu, portal, or dependency file changes.

## 4. Record check (PowerShell)

```powershell
Test-Path -LiteralPath 'specs\numbered\0\0\1\2\4\0\0\3\4878-windows-path-symlink-guardrails\spec.md'
```

Expected after task T006: `True`.

## 5. Remote checks after the pull request opens

```powershell
gh pr checks <number> -R jmorrison-juniper/MistHelper --watch
gh pr view <number> -R jmorrison-juniper/MistHelper --json body --jq .body
```

Expected: every required check passes, and the body contains `Closes #4878`.
