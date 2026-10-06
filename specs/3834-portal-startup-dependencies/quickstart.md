# Validation Guide: Portal Startup Dependencies

## Planning-stage checks

Read [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), and
[the dependency contract](contracts/request-dependencies.md).
Verify all FR-001 through FR-009 requirements have design and test coverage.
Verify there is no new direct runtime child and the nine-child debt has a separate remediation action.

This stage does not run product services or claim that the defect is fixed.
Check Markdown links, template completion, requirement coverage, and the final changed-file set.
Run the STE and Markdown link commands when their tools are available.
Report unavailable tools and failed extension hooks separately from document validation.

## Implementation prerequisites

Warning: the portal can change production firmware. Do not validate this issue against production devices or stores.

Use the worktree's Python 3.13 environment.
If runtime test packages are missing, run the documented bootstrap:

```bash
python3 scripts/bootstrap_worktree.py
source .venv/bin/activate
```

Use the existing pytest isolation fixtures and `tmp_path`.
Disable environment-file loading before importing `wsgi_capture`.
Trap socket connections, DNS discovery, Mist calls, ArangoDB, Redis, exporters, and container startup before factory construction.
Provide strict fake responses with real SDK and driver call signatures.
Patch the external construction boundaries, not `install_seams`, the provider, service constructors, or `identity.current_session`.
Do not set `MIST_CLIENT` or `DB_ROUTER` to make the default-factory test pass.

## Required scenarios

| Scenario | Execution | Required measurement |
| - | - | - |
| Default startup | Call `create_app()` with no arguments and exercise authenticated capture and upgrade routes. | Four real service classes resolve with valid dependencies. Required external calls match actual signatures. |
| WSGI startup | Import `wsgi_capture` with dotenv and external boundaries trapped. Use its `app`. | No factory override or live connection. The same provider contract applies. |
| Database construction | Supply controlled env/config readers and strict constructor doubles. | Exact config and strategy arguments. Router and document handle remain distinct. |
| Missing authentication | Omit owner key, remove registry record, change browser cookie, or remove cloud session. | Authentication refusal and zero Mist/storage operations. |
| Missing storage | Test config failure, standalone mode, absent handle, invalid router, and Arango refusal. | 503 before Mist work. No success-shaped fallback. |
| Durable failure | Return CSV-only success, zero writes, explicit failure, or mismatched read-back. | Visible failure and zero later cloud mutations. |
| Request isolation | Overlap two registered operators with two clients and a synchronization barrier. | Every call uses the correct session. Graphs and routers differ. No leaked state after cleanup. |
| Worker ownership | Bind a worker inside the request, then finish the request before fake work ends. | No request lookup in the worker and no premature storage close. |
| Complete E2E overrides | Use the existing complete override builder and constructor traps. | Every supplied object remains identical. Zero production constructors, bootstraps, or connections. |
| Incomplete E2E overrides | Remove one required existing field. | Factory raises before route registration. No production setup. |
| Service failures | Fail capture, settle, comparison read/write, cancellation, and approval update. | No dummy comparison, assumed settle, false cancellation, or completed-run response. |
| Redaction and guards | Use fake secret sentinels and registered route clients. | No secret in response/log. Existing scope, CSRF, write, and lock refusals remain effective. |

Call `SettleGateService` and `ComparisonService` through the request graph in authenticated contexts.
Comparison GET reads stored results. It does not replace the computation scenario.
Retain the current single-owner status-route test.
Include HTTP 4xx and 5xx response cases for affected SDK-backed tests.
Make a deliberately wrong double fail a signature test so the compatibility guard proves a red decision.

## Smallest existing regression commands

After implementation, run these existing selectors together:

```bash
python -m pytest tests/unit/upgrade_portal/test_phase2_service_wiring.py tests/unit/upgrade_portal/test_phase2_phase3_route_connections.py tests/unit/upgrade_portal/test_comparison_routes.py tests/unit/upgrade_portal/test_comparison_service.py tests/unit/upgrade_portal/test_settle_gate_service.py tests/integration/upgrade_portal/test_two_operators.py
python -m pytest tests/unit/upgrade_portal/test_upgrade_service.py tests/unit/upgrade_portal/test_upgrade_service_status.py tests/unit/upgrade_portal/test_upgrade_service_prohibitions.py tests/contract/upgrade_portal/test_comparison.py tests/contract/upgrade_portal/test_comparison_errors.py tests/contract/upgrade_portal/test_comparison_export.py
python -m pytest tests/integration/test_mistapi_sdk_compatibility.py
```

Run the new issue-specific integration package after task generation defines its compliant location.
Run the current E2E portal journeys with the existing isolated harness:

```bash
python -m pytest tests/e2e/upgrade_portal
```

No browser control is added. Preserve stable existing test identifiers.
Keep a failed journey trace or screenshot in the existing ignored test evidence directory.
Do not modify shared E2E fixture or record files while their current pull requests remain open.

## Changed-code gates

Use the documented compile, Ruff, Black, mypy, complexity, security, symbol, and docstring gates for the actual changed paths.
Read the live CI selectors before execution. Do not invent a reduced type-check scope.
Run the test-quality preflight and ratchet exactly as `.github/copilot-instructions.md` specifies.
That procedure requires committed tests and the intended comparison base.
The present planning request forbids rebase and push. Do not perform either as a validation shortcut.

For the implementation documentation:

```bash
ste-linter --config .ste-linter.toml --min-score 80 documentation/upgrade_capture_portal.md changelog.d/issue-3834-portal-startup-dependencies.md
markdown-link-check documentation/upgrade_capture_portal.md changelog.d/issue-3834-portal-startup-dependencies.md
```

Confirm the installed link-check command's arguments before execution.
The issue-specific fragment must have one `###` heading and a `Fixed` bullet that names issue #3834.
Do not write a fragment that claims the fix exists during planning.

## Acceptance result

Record actual counts for each scenario, failures, skips, live-call traps, and resource-close assertions.
Require zero live Mist calls and zero production-store calls across all startup and service tests.
Require all complete E2E override cases to preserve supplied dependencies.
Require all two-operator calls to retain the correct request session.
Require each missing-dependency case to fail before cloud mutation.
SC-001 covers tested supported startup flows, not an unmeasured claim about every future deployment.

## Planning validation receipt

The planning-stage structural check read five artifacts, checked ten local links, and checked nine requirement mappings.
It found no unresolved template marker, missing required plan section, unclosed code fence, or missing debt record.
It also verified that no tracked product source changed.
`git diff --check` passed.

The global `ste-linter` command was absent.
The pinned development-tool requirement supplied the command through an isolated UV environment with Python 3.13.
The STE check read five files and skipped zero files.
The scores were 95 for the plan, research, quickstart, and contract, and 96 for the data model.
Each file passed the required threshold of 80.

`markdown-link-check` found zero tracked files because the new design artifacts remain untracked.
Its zero broken-link result is not validation evidence for these artifacts.
The separate direct path check examined all five artifacts and verified ten existing local link targets.
Run the shared link gate again after the implementation stage explicitly tracks its feature files.

The optional commit hooks remained unexecuted.
The mandatory completion command was attempted through:

```bash
printf '%s\n' '{"feature_directory":"specs/3834-portal-startup-dependencies","currentStep":"plan","status":"planned"}' | specify event run speckit.companion.after-plan after_plan
```

It printed `Event command 'speckit.companion.after-plan' not found`.
The CLI returned zero despite that missing command. This is **not** a successful hook result.
Extension inspection reported companion corrupted and disabled. Its state receipt remains unchanged.
The Python setup script is absent, and the installed PowerShell setup cannot run without `pwsh`.
The planning documents use the supplied feature path and current template without changing either setup script.

Product tests did not run because this stage changed documentation only.
Implementation acceptance remains unmeasured until the next authorized implementation stage.
