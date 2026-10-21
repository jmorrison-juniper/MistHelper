# Quickstart: Guest Migration Validation

This refresh changes planning documents only.
Do not start the source application, register routes, invoke guest operations, or use production credentials.

## Environment

If the worktree lacks its environment, run:

```sh
python3 scripts/bootstrap_worktree.py
```

Use the worktree interpreter for each check.
PowerShell is required by the route and prerequisite scripts.
Keep `SPECIFY_FEATURE_DIRECTORY` command-scoped:

```sh
export SPECIFY_FEATURE_DIRECTORY=specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
```

Expect the same feature path and all supporting documents. The script must not change `.specify/feature.json`.

## Current Runnable Checks

```sh
.venv/bin/python -m pytest -q tests/unit/web_portal/test_guest_authorization_read_model.py
.venv/bin/python -m pytest -q tests/guardrails/test_process_folder_structure.py tests/guardrails/test_nested_package_structure.py tests/guardrails/test_spec_route_contract.py
.venv/bin/ste-linter --config .ste-linter.toml --min-score 80 "$SPECIFY_FEATURE_DIRECTORY"/*.md "$SPECIFY_FEATURE_DIRECTORY"/checklists/*.md "$SPECIFY_FEATURE_DIRECTORY"/design/*.md "$SPECIFY_FEATURE_DIRECTORY"/design/contracts/*.md
.venv/bin/markdown-link-check --root . "$SPECIFY_FEATURE_DIRECTORY"
.venv/bin/speckit-task-audit --root .
git diff --cached --check
```

Stage only the explicit feature files before hierarchy and tracked-link checks.
Expect 22 existing projection cases, visible hierarchy counts, zero broken local links, and zero completed implementation claims.
The task audit must discover this record and its tasks. A zero-file scan is not evidence.
Separate unrelated historical failures from this record's 40 open tasks and zero completed implementation claims.
The read-only analyze phase checks every requirement against the final plan and tasks.

## Future Checks After G1-G5

The following files are planned targets, not current runnable tests:

| Proposed test file | Required evidence |
| --- | --- |
| `tests/unit/web_portal/test_guest_authorization_workflows.py` | Validation, duration boundaries, unknown state, and state transitions |
| `tests/unit/web_portal/test_guest_authorization_import.py` | Approved CSV boundaries, encoding, duplicates, and row outcomes |
| `tests/contract/web_portal/test_guest_authorizations_api.py` | Pinned methods, payloads, response shapes, all error classes, and zero live calls |
| `tests/integration/web_portal/test_guest_authorizations.py` | Access, scope, CSRF, typed confirmation, audit outcomes, and zero unauthorized calls |
| `tests/e2e/web_portal/test_guest_authorizations.py` | All seven journeys, stable selectors, denial, cancellation, partial results, and failure artifacts |

After implementation, run these files together with the existing projection tests.
Run applicable compile, Ruff, Black, mypy, Bandit, complexity, docstring, symbol, and hierarchy checks for the actual changed files.
Follow the committed-test quality procedure in `.github/copilot-instructions.md` before a product push.
No product gate result is claimed by this planning record.
