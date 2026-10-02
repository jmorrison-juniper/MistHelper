# Implementation Plan: Rejected Child Counts

**Branch**: `jmorrison-juniper-rejected-child-outcome-counts` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: [MistHelper #3329](https://github.com/jmorrison-juniper/MistHelper/issues/3329).

## Summary

Repair the child count pipeline in `_aggregate_child_counts`.
The existing summary sends these counts to the status response and the shipped progress page.
No template, JavaScript, CSS, or firmware policy change is necessary.

The durable child outcome key is `status`.
The operation outcome key is `state`.
`not_submitted` proves that no cloud write ran.
The model also stores some uncertain submission responses as `rejected`.
The existing cancellation reader requires an HTTP 4xx response before it treats that rejection as a known refusal.
The implementation must preserve this evidence boundary.
An uncertain, possibly active write must not become a reported target failure.
The parent approved the public `OrgCancelLists.REFUSED_STATUSES` constant as the existing evidence rule.
Do not call `_never_started`, because that private helper also includes planned children.
The import of this public class is the only necessary source change outside the count method.

The parent corrected its initial probe, which used `state` instead of the real child `status` key.
That initial probe did not establish complete model evidence.
The new red proof uses `status=rejected`, `raw_status=400`, and explicit targets.
It also uses real `not_submitted` and uncertainty records.

## Technical Context

**Language/Version**: Python 3.13.13.

**Primary Dependencies**: Existing Flask, mistapi 0.64.0, pytest, Playwright, and repository development tools.

**Storage**: The existing process-owned `PortalRecordStore` supplies detached durable operation records in tests.
No schema, production store, or primary key changes apply.

**Testing**: Real helper, real Flask status route, shipped template and JavaScript, and Chromium.

**Target Platform**: The local macOS worktree. Production behavior remains platform-independent.

**Project Type**: A reporting repair in the upgrade portal.

**Performance Goals**: Retain the existing count complexity. Make no additional cloud call.

**Constraints**: Change only the reserved count method in product code.
Keep the method within 25 lines and five parameters.
Preserve all unrelated source AST.
Make zero live Mist, store, firmware, or deployment calls.

**Scale/Scope**: Known refusal, no-submission, mixed child rows, multiple sites and families, empty targets, nested AP arrays, and completed proof.
Include uncertainty, active, waiting, and cancelled controls.

## Constitution Check

The user authorizes one unpublished local commit with Conventional Commits and the required Copilot App trailer.
The parent now requires `Part of #3329`, not `Closes #3329`.
Uncertain legacy rejected records intentionally retain their counts.
This repair does not satisfy the literal acceptance text for every legacy rejected record.
This authority supersedes older timestamp-commit and automatic deployment text.
No push, pull request, merge, Actions run, auto-merge, or deployment is authorized.
Publication position 41 follows issue #3326.
Issue #3353 remains the sole publication owner.
Publication requires an explicit parent grant with a full verified-main SHA.

The app manages the branch from `main`.
The initial clean revision is `5d38898af5639e90715ec57eb8d48d2985e1acf8`.
The authenticated owner is `jmorrison-juniper`.
The [claim](https://github.com/jmorrison-juniper/MistHelper/issues/3329#issuecomment-5948531022) records the exact reservation.
The claim followed a complete live issue read and all paginated open pull request file checks.
The check found zero open pull requests.

The `speckit.specify` custom agent generated the initial spec, plan, and tasks from current templates.
The feature-only fallback did not run shared Git or companion hooks.
`command -v pwsh` returned no executable.
The Git hook would create a branch outside app management.
The companion hooks would change prohibited shared tracking files.
No hook, PowerShell command, constitution change, or shared `.specify` change succeeded or is claimed.

The existing route module and test directories have hierarchy debt.
The user explicitly reserves three dedicated test modules in those existing directories.
This surgical repair does not restructure unrelated files or add a delegation-only class.
A separate hierarchy cleanup remains outside this issue.

This repair changes firmware outcome reporting, not firmware decision policy.
The publication owner must obtain human review before any firmware-evidence merge.
No automatic merge is authorized.
The parent filed the separate uncertainty and lock-release concern as [issue #3726](https://github.com/jmorrison-juniper/MistHelper/issues/3726).
Its proof used exact initial-base source and intercepted every physical write.
This count branch does not repair that policy concern or change its source scope.

## Project Structure

### Documentation (this feature)

```text
specs/3329-rejected-child-counts/
  spec.md
  plan.md
  tasks.md
```

### Source Code (repository root)

```text
src/upgrade_portal/app/routes/org_upgrade.py
tests/unit/upgrade_portal/test_issue_3329_rejected_child_counts.py
tests/contract/upgrade_portal/test_issue_3329_rejected_child_counts_routes.py
tests/e2e/upgrade_portal/test_issue_3329_rejected_child_counts_journey.py
changelog.d/issue-3329-rejected-child-counts.md
```

**Structure Decision**: Keep the reporting repair in the existing count method.
Keep shared test data in the owned unit module and the isolated application in the owned contract module.
The browser module imports no conftest globals.
It uses existing strict browser fixtures and `RunOwnerHeaderCheck`.

## Count and UI Contract

Known refusal and no-submission counts replace contradictory cloud counts.
Their result is `(explicit target total, 0, explicit target total)`.
An empty explicit target list produces `(0, 0, 0)`.
Each child contributes once to the aggregate and matching child row.

Other outcomes retain native cloud, nested AP, and proven completed counts.
Uncertainty alone produces no failed target.
Status, reason, cancellation text, target content, and row order remain unchanged.

The browser opens an owned record through `/upgrade/org/jobs/<operation_id>`.
It selects the shipped Refresh status control.
The real `/api/org-upgrades/<operation_id>` response must paint the same summary and child counts.
The proof must count checked records, child rows, device rows, completed polls, and forbidden callbacks.
Forbidden callbacks must remain zero.

## Local Evidence

The standard bootstrap genuinely failed:

`rtk proxy python3.13 scripts/bootstrap_worktree.py`

The owned `.venv` interpreter aborted in `ensurepip` with `SIGABRT: 6`.
This is the known macOS setup defect in issue #3701.
The failure is not a passing setup check.

Only the ignored owned environment was recovered:

`rtk proxy env UV_LINK_MODE=copy UV_SYSTEM_CERTS=1 uv venv --clear --seed --python python3.13 .venv`

`rtk proxy env UV_LINK_MODE=copy UV_SYSTEM_CERTS=1 uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt`

Both recovery commands passed.
The owned interpreter is Python 3.13.13.
The `src` import resolves inside this worktree.
The installed Chromium executable exists.

### Red and green proof

The corrected red helper and route run produced 18 expected count failures and 42 passing controls.
The red Chromium run collected all E2E modules and selected five cases.
Three real pages showed Failed 0 instead of 1, 2, or 3.
Both uncertainty controls passed through real browser polls.
No red failure came from a missing package, fixture, or ownership error.

The repaired helper and route run passed all 60 cases.
The final browser run passed 23 cases from a 526-item E2E collection.
It selected all 11 new cases and 12 unchanged adjacent cases.
The other 503 cases were deliberately outside this bounded browser run.
No selected browser case skipped.

The new browser cases exercise the shipped template, script, and status route.
They also retain counts after real HTTP 400 and HTTP 500 errors.
SDK timeout and connection-error stand-ins exercise the real durable fallback.
These failures do not cause a real cloud call.
The tests check the reason, status, cancellation text, and ordered device content.

The count method has 21 lines and one parameter.
Its complexity is eight. The method scan checked 148 top-level complexity records.
Its focused coverage includes all 19 statements and all four measured branches.
No changed statement or measured branch is missing.
The negative assertion rejects a real summary whose known failed counts are removed.
The same assertion accepts the zero-failure uncertainty control.

The AST comparison preserves 234 unrelated top-level nodes.
The only permitted differences are the count method and the approved public import.
The model, lock, cancel, retry, authentication, template, script, and deployment files remain unchanged.

### Exact local commands and results

Each command uses the owned environment.
Red failures are intentional reproduction evidence, not passing checks.

| Command | Result |
| - | - |
| `rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q --tb=short -s tests/unit/upgrade_portal/test_issue_3329_rejected_child_counts.py tests/contract/upgrade_portal/test_issue_3329_rejected_child_counts_routes.py --timeout=120` | Red: 18 failed, 42 passed. |
| `rtk proxy env UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -B -m pytest -p no:cacheprovider tests/e2e/ -k issue_3329 -q --tb=short -s --timeout=180` | Red: 3 failed, 2 passed, 515 deselected. |
| `rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -q --tb=short -rs --timeout=120 tests/unit/upgrade_portal/test_issue_3329_rejected_child_counts.py tests/contract/upgrade_portal/test_issue_3329_rejected_child_counts_routes.py` | Green: 60 passed. |
| `rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider tests/unit/upgrade_portal tests/unit/firmware --ignore=tests/e2e -q --tb=short --timeout=120` | 5,291 passed. One Windows-only real-import case skipped on macOS. |
| `rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider tests/contract/upgrade_portal --ignore=tests/e2e -q --tb=short -rs --timeout=120` | 1,573 passed. |
| `rtk proxy env UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -B -m pytest -p no:cacheprovider tests/e2e/ -k 'issue_3329 or org_cancel_outcomes_journey or org_ended_child_cancel_journey or org_mixed_cancel_state_journey or org_upgrade_flow or org_final_operation_page or org_recovery_controls' -q --tb=short -s -rs --timeout=180` | Final: 23 passed, 503 deselected. |
| `rtk proxy env -u MIST_APITOKEN -u MIST_API_TOKEN -u MIST_ORG_ID -u org_id -u API_TOKEN PYTHON_DOTENV_DISABLED=1 MISTHELPER_STANDALONE=true .venv/bin/python -B -m pytest -p no:cacheprovider tests/integration -k mistapi_sdk_compatibility --ignore=tests/e2e -q -s -rs --timeout=120` | 8 passed, 95 deselected. The guard checked 549 static signatures. |
| `rtk proxy .venv/bin/python -m py_compile MistHelper.py src/upgrade_portal/app/routes/org_upgrade.py tests/unit/upgrade_portal/test_issue_3329_rejected_child_counts.py tests/contract/upgrade_portal/test_issue_3329_rejected_child_counts_routes.py tests/e2e/upgrade_portal/test_issue_3329_rejected_child_counts_journey.py` | Passed. |
| `rtk proxy .venv/bin/python -m ruff check .` | Passed. |
| `rtk proxy env BLACK_NUM_WORKERS=2 .venv/bin/python -m black --check --diff .` | Passed. All 2,019 files remain formatted. |
| `rtk proxy .venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Passed for 665 source files. |
| `rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r . -q` | Passed with no finding. Existing annotation-parser warnings remain. |
| `rtk proxy bash -o pipefail -c 'rtk proxy .venv/bin/radon cc src/ MistHelper.py wsgi.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py -j \| rtk proxy .venv/bin/complexity-gate --max 10'` | Passed at the unchanged limit of 10. |
| `rtk proxy .venv/bin/python -m pylint src/ --fail-under=9.5` | Passed at 9.83 of 10. |
| `rtk proxy .venv/bin/python -m vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | Passed with no finding. |
| `rtk proxy .venv/bin/python -m pydocstyle src/ wsgi.py web_portal` | Passed. |
| `rtk proxy .venv/bin/python -m interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v` | Passed at 99.6 percent. The generated ignored badge was removed. |
| `rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | Passed. Six input reads and validations, three guide reads and checks. |
| `rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --report /Users/jmorrison/.copilot/session-state/92894fd5-ace3-4b38-8692-2d1c07a77639/files/3329-full-quality-report.json --summary /Users/jmorrison/.copilot/session-state/92894fd5-ace3-4b38-8692-2d1c07a77639/files/3329-full-quality-summary.md` | Passed. 1,004 discovered and parsed files, 956 analyzed files, 725 accepted baseline findings, zero new findings. |
| `rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --include-mist-api --roots tests/unit/upgrade_portal/test_issue_3329_rejected_child_counts.py tests/contract/upgrade_portal/test_issue_3329_rejected_child_counts_routes.py tests/e2e/upgrade_portal/test_issue_3329_rejected_child_counts_journey.py --report /Users/jmorrison/.copilot/session-state/92894fd5-ace3-4b38-8692-2d1c07a77639/files/3329-owned-quality-report.json --summary /Users/jmorrison/.copilot/session-state/92894fd5-ace3-4b38-8692-2d1c07a77639/files/3329-owned-quality-summary.md` | Passed. All three new files were analyzed with zero findings. Two unrelated test roots were deliberately omitted from this additional measurement. |
| `rtk proxy git --no-pager diff --check` | Passed. |

The full configured analyzer retains 48 existing SDK exclusions.
All three new files appear in its `analyzed_files`.
The explicit measurement does not replace the full gate.
The baseline, configuration, thresholds, and exclusions remain unchanged.

The SDK guard also reports 366 dynamic signatures and ten unresolved call sites at their existing baselines.
Those paths remain unverified.
The Windows-only real-import case remains unknown on Windows.
The complete repository coverage floor is not measured by the focused method coverage.
No skipped, deselected, or unverified path is reported as a passing path.

### Dependency audit limitation

`rtk proxy .venv/bin/pip-audit -r requirements.txt` failed in temporary-environment `ensurepip` with `SIGABRT: 6`.
That normal audit is not reported as clean.
The approved substitute passed:

`rtk proxy env UV_SYSTEM_CERTS=1 UV_LINK_MODE=copy uv pip compile --python .venv/bin/python --generate-hashes --universal --quiet --output-file /Users/jmorrison/.copilot/session-state/92894fd5-ace3-4b38-8692-2d1c07a77639/files/3329-runtime-audit.txt requirements.txt`

`rtk proxy .venv/bin/pip-audit --require-hashes --no-deps --disable-pip -r /Users/jmorrison/.copilot/session-state/92894fd5-ace3-4b38-8692-2d1c07a77639/files/3329-runtime-audit.txt --progress-spinner off --format json --output /Users/jmorrison/.copilot/session-state/92894fd5-ace3-4b38-8692-2d1c07a77639/files/3329-runtime-audit.json`

The universal graph contains 111 pinned records.
All 105 records applicable to this interpreter received an audit.
There are zero missing applicable records, skipped audit records, or known vulnerabilities.
Six records apply only to other platforms.
This local audit does not prove those platform results or audit the Git development-tool dependency.
The failed audit temporary environment is absent.
The generated hash lock is removed before handoff.

### Cleanup and remaining authority

Each new proof checks seven forbidden seams and 31 actual mutation-route callbacks.
All remain at zero.
The six aggregate mutation callbacks also remain at zero.
Every owned server thread, listener, and temporary resource directory is absent after teardown.
The adjacent browser guards report zero leaked locks and zero leaked live runs.
The checkout audit trail contains zero lines before and after the tests.

Screenshots record the five main count cases before and after real polls in the pytest temporary artifacts.
VS Code Browser Agent Tools are not available.
Playwright verifies the shipped selectors in Chromium.

The STE dictionary is unavailable.
Rule scoring remains partial, with `dictionary_used=false`.
No external dictionary or credential is borrowed.

The offline draft preserves all 23 template items.
Unsupported or unauthorized items remain unchecked.
No remote title check, CI, CodeQL, protected merge, actual-main test, container build, or deployment ran.
The committed-scope result and full local commit SHA belong in the subsequent issue-comment receipt.
That receipt does not authorize publication or issue closure.

## Complexity Tracking

| Existing debt | Bounded treatment | Separate action |
| - | - | - |
| The route module contains more than five top-level definitions. | Edit the existing count method only. | Plan a separate module-boundary repair. |
| The test directories contain more than five modules. | Add only the three explicitly reserved proof modules. | Plan a separate test-package cleanup. |

## Offline Pull Request Draft

The draft below preserves the current template.
It is not a published pull request.
The exact commands and limitations above supply the local evidence.
This bounded repair is **Part of #3329**.
It deliberately preserves uncertain legacy rejections and does not close the issue.

# Spec Conformance Checklist

**Linked Spec Issue**: #3329<!-- Issue number -->

## Acceptance Criteria
- [ ] All acceptance criteria from the linked Spec Issue are met
- [x] Each criterion has a corresponding test or verification

## Quality
- [x] Tests added or updated for all changed functionality
- [ ] Coverage meets or exceeds 80% threshold
- [x] New or changed guards state the measured count and prove one failing path
- [x] No new Ruff lint violations (`ruff check .`)
- [x] Code formatted with Black (`black --check --diff .`)
- [x] mypy passes (`mypy $MYPY_PATHS --config-file pyproject.toml`)

## Security
- [x] No hardcoded secrets, tokens, or passwords
- [x] Bandit passes with no new findings (`bandit -c pyproject.toml -r .`)
- [ ] pip-audit clean (`pip-audit -r requirements.txt`)
- [x] Sensitive data handled via `.env` / environment variables only

## Deployment
- [ ] Dry-run verified locally (ran affected menu operations)
- [ ] `.env` changes documented in `deploy/.env.example` (if applicable)
- [ ] Container builds successfully (if Containerfile changed)

## UI / E2E Testing (if web UI changed)
- [x] Playwright E2E tests added/updated for changed UI flows in `tests/e2e/`
- [ ] Stable `data-testid` attributes added for new interactive elements
- [ ] AI agent verified selectors via VS Code Browser Agent Tools
- [x] Screenshots/traces captured for main UI flows (attached or in CI artifacts)

## Documentation
- [ ] README.md updated (if user-facing changes)
- [x] Release note added as one new fragment under `changelog.d/`
- [x] The fragment name carries the PR number, the issue number, or the date
- [x] `CHANGELOG.md` is unchanged by this branch (the release coordinator owns that file)
