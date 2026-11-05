# Planning validation and future acceptance

## Current planning checks

Run these commands from this worktree, not the parent worktree.
Use the declared dependencies before validation.

```sh
python3 scripts/bootstrap_worktree.py
F=specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity
P="$PWD/test-artifacts/guest-parity-pwsh"
SPECIFY_FEATURE_DIRECTORY="$F" "$P/pwsh" -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
PATH="$P:$PATH" .venv/bin/python -m pytest -q tests/unit/web_portal/test_guest_authorization_read_model.py tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_nested_package_structure.py
find "$F" -name '*.md' -print0 | xargs -0 .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 --quiet
.venv/bin/markdown-link-check --root . "$F"
.venv/bin/check-citations "$F"
.venv/bin/speckit-task-audit --root .
git diff --check
git diff --exit-code -- .specify/feature.json
```

The PowerShell directory is session-local tooling, not a repository dependency.
Use an installed `pwsh` if this directory is absent.
This session retrieved official PowerShell 7.6.9 and verified its GitHub asset SHA-256 before execution.
Do not disable a routing test when PowerShell is absent.
The full task audit can report unrelated historical records. Record its actual result, then inspect this feature separately without changing an allow-list.
The citation tool checks local `path:line` references, not remote GitHub anchors.
Remote immutable path and line-range validation therefore needs a separate exact check.

## Current source reference reproduction

The source pin is `0213240cb9edfa237f763acd156b90a6049363cb`.
Read its [capture procedure](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/capture_screenshots.py#L1-L177)
before executing any source helper.
The planning capture used Flask test-client responses, an in-memory connection, forbidden SDK construction, and local browser request fulfillment.
No standalone source server or Compose stack ran.

The exact session commands were:

```sh
.venv/bin/python test-artifacts/guest-parity-render.py
(cd test-artifacts/guest-parity-source && PYTHON_DOTENV_DISABLED=1 ../../.venv/bin/python -m unittest discover -s tests -v)
```

These ignored scratch paths are session evidence, not committed application files.
The screenshot manifest persists in this session's `files/guest-parity-evidence/`.
After inspection, the pinned source snapshot moved into that session evidence directory.
Keep original-source tests outside target test discovery before the full test-quality scan.
For another worktree, use a reviewed offline harness with the same isolation contract.
Do not run the source production entry point with a token to recreate visual evidence.

## Future test commands

The paths below are planned, not present today.
T007 validates bounded destinations before creation.
Only after implementation, run:

```sh
.venv/bin/python -m pytest tests/unit/web_portal/guest_authorizations tests/contract/web_portal/guest_authorizations tests/integration/web_portal/guest_authorizations
.venv/bin/python -m pytest tests/e2e/web_portal/guest_authorizations
```

Require each acceptance family in [E2E](contracts/e2e.md), paired screenshot scenario, and inventory row.
Use synthetic fixtures and isolated stores.
Fail on live SDK construction, unexpected external requests, missing required inputs, and unverified scope.
Run the applicable lint, format, type, complexity, security, docstring, move, and full regression gates described in repository instructions.
A moved projection requires direct import, old-path, resolver, symbol, and generated-reference checks.
A new menu operation is not currently proposed.

## Cutover and recovery rehearsal

T039 requires an approved operating window, exact deployment revision, verified private backups, and a tested return to the offline boundary.
No live write occurs in the rehearsal unless the user separately authorizes its exact scope.
Check existing page health and shared-store ownership before enabling approved behavior.
Stop dispatch on audit, scope, contract, or reconciliation failure.
Preserve unknown outcomes for operator review rather than retrying them.
T040 records operator approval and does not treat a planning PR merge as migration acceptance.
