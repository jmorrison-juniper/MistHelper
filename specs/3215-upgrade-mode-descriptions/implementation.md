# Implementation: Upgrade mode descriptions

The original evidence below records the 2026-10-01 repair.
The final section records the local-only refresh on 2026-10-02.

## Delivered Change

The two selection pages now state the actual routes and capture features.
One portal operation can contain several cloud or site child jobs.
The text describes verified standalone pre-check adoption and the confirmation controls for missing captures.
It distinguishes automatic post-check captures from manual post-check captures.
It limits comparison to verified capture pairs.

The change preserves selection actions, route destinations, CSRF fields, mode values, and saved checkbox states.
The existing contracts also verify typed confirmation and pre-check refusal.
No firmware request, strategy, phase order, lock, schema, primary key, or product Python file changes.

## Exact File Manifest

```text
src/upgrade_portal/app/assets/templates/select/mode.html
src/upgrade_portal/app/assets/templates/select/sites.html
tests/contract/upgrade_portal/test_mode_descriptions.py
tests/e2e/upgrade_portal/test_mode_descriptions_journey.py
specs/3215-upgrade-mode-descriptions/spec.md
specs/3215-upgrade-mode-descriptions/plan.md
specs/3215-upgrade-mode-descriptions/tasks.md
specs/3215-upgrade-mode-descriptions/implementation.md
specs/3215-upgrade-mode-descriptions/analysis.md
changelog.d/issue-3215-upgrade-mode-descriptions.md
```

The local base is `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
The issue claim records app session `542073ce-77f3-452d-baff-a993309d0ec0`.
The claim checked all 12 open pull requests and their complete file lists.

## Red Proof

The new cases first ran against the unchanged templates.
The clean red run reported **13 failed, 8 passed, and zero skipped**.
The mode page failed on the actual false organization cloud job claim.
The multi-site page failed on the same false claim in the rendered note.
Single-site guidance failed because its description did not exist.
All eight checks of the unchanged controls passed.

```bash
rtk proxy .venv/bin/python -m pytest tests/contract/upgrade_portal/test_mode_descriptions.py tests/e2e/upgrade_portal/test_mode_descriptions_journey.py --browser chromium --tracing retain-on-failure --screenshot only-on-failure --output /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-red-browser --tb=line --show-capture=no -q
```

The session artifact `issue3215-red-clean.log` holds the failure output.
The red browser artifacts hold the screenshots and traces of the original pages.

## Green Proof and Coverage

The final combined run reported **351 passed and zero skipped**.
That total includes all 15 new rendering contracts and all six new Chromium cases.
The existing contracts verify selection, typed confirmation, locks, pre-check adoption, post-check rows, and comparison eligibility.
Coverage of `src.upgrade_portal.app.routes.select` is **85.55 percent** against the **80 percent** threshold.

```bash
rtk proxy .venv/bin/python -m pytest \
  tests/contract/upgrade_portal/test_mode_descriptions.py \
  tests/contract/upgrade_portal/test_select.py \
  tests/contract/upgrade_portal/test_upgrade_start.py \
  tests/contract/upgrade_portal/test_org_upgrade_routes.py \
  tests/contract/upgrade_portal/test_org_precheck_routes.py \
  tests/contract/upgrade_portal/test_run_create_adopts_precheck.py \
  tests/contract/upgrade_portal/test_lock.py \
  tests/unit/upgrade_portal/test_select_lock_helpers.py \
  tests/unit/upgrade_portal/test_confirm_warning.py \
  tests/unit/upgrade_portal/test_org_postcheck_view.py \
  tests/unit/upgrade_portal/test_org_postcheck.py \
  tests/unit/upgrade_portal/test_upgrade_service_plan.py \
  tests/e2e/upgrade_portal/test_mode_descriptions_journey.py \
  --browser chromium \
  --basetemp /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-green-run \
  --tracing retain-on-failure --screenshot only-on-failure \
  --output /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-green-browser \
  --cov=src.upgrade_portal.app.routes.select \
  --cov-report=term-missing:skip-covered \
  --cov-report=xml:/Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-coverage.xml \
  --cov-report=json:/Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-coverage.json \
  --cov-fail-under=80 --tb=short --show-capture=no -q
```

The session artifact `issue3215-green-final.log` holds the final output.
The browser cases save six screenshots of the mode and site states.
The isolated harness reports zero leaked runs and zero leaked holds.
Its audit trail checks also report zero changes to the worktree's trail.
The known adjacent version-options skip is outside this run and does not count as a pass.

## Python and Test Quality Commands

Each command below passed.
Syntax, Ruff, and Black cover the entrypoint and both new test modules.
The configured source type check covers 663 files.
The additional explicit type check covers both new test modules.

```bash
rtk proxy .venv/bin/python -m py_compile MistHelper.py tests/contract/upgrade_portal/test_mode_descriptions.py tests/e2e/upgrade_portal/test_mode_descriptions_journey.py
rtk proxy .venv/bin/python -m ruff check MistHelper.py tests/contract/upgrade_portal/test_mode_descriptions.py tests/e2e/upgrade_portal/test_mode_descriptions_journey.py
rtk proxy .venv/bin/python -m black --check MistHelper.py tests/contract/upgrade_portal/test_mode_descriptions.py tests/e2e/upgrade_portal/test_mode_descriptions_journey.py
rtk proxy .venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
rtk proxy .venv/bin/python -m mypy tests/contract/upgrade_portal/test_mode_descriptions.py tests/e2e/upgrade_portal/test_mode_descriptions_journey.py --config-file pyproject.toml
rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r src/upgrade_portal -q -f json -o /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-bandit.json
rtk proxy .venv/bin/python -m pydocstyle tests/contract/upgrade_portal/test_mode_descriptions.py tests/e2e/upgrade_portal/test_mode_descriptions_journey.py
rtk proxy .venv/bin/python -m radon cc tests/contract/upgrade_portal/test_mode_descriptions.py tests/e2e/upgrade_portal/test_mode_descriptions_journey.py -j | rtk proxy .venv/bin/complexity-gate --max 10
rtk proxy .venv/bin/test-quality-analyzer --roots tests/contract/upgrade_portal/test_mode_descriptions.py tests/e2e/upgrade_portal/test_mode_descriptions_journey.py --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --log-level WARNING --report /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-test-quality.json --summary /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-test-quality-summary.md
```

Bandit checked 102 product files and 45,060 source lines.
It reported zero findings and zero input errors.
The two-module test quality scope reported zero findings and zero parse errors.
The analyzer names two omitted repository roots because this run targets only the new modules.
Neither new module is omitted.
The baseline and rule configuration remain unchanged.

The 18 new functions have at most 23 body lines and five parameters.
Their maximum complexity is 10.
The longest description sentence has 16 words.

## Runtime Dependency Audit

The normal resolver command failed before the audit.
Its temporary Python process aborted during `ensurepip` with `SIGABRT: 6`.
That result is not a successful audit.

```bash
rtk proxy .venv/bin/pip-audit -r requirements.txt --progress-spinner off --format json --output /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-runtime-audit.json
```

The authorized alternative compiled the complete runtime closure with hashes.
The strict audit checked **105 dependencies**, found **zero known vulnerabilities**, and skipped **zero dependencies**.
Both commands below passed without a manifest change.

```bash
rtk proxy uv pip compile --quiet --system-certs --python .venv/bin/python --generate-hashes --output-file /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-runtime-hashed.txt requirements.txt
rtk proxy .venv/bin/pip-audit -r /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-runtime-hashed.txt --no-deps --disable-pip --require-hashes --strict --progress-spinner off --format json --output /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-runtime-audit.json
```

This audit covers the runtime manifest, not the Git-only development tools package.
The development manifest pins that package at `b140350ebc40e61b57a3a65731c0df520f143661`.
A PyPI audit does not verify that pinned Git revision.

## Missing Capabilities

The initial interpreter check found Python 3.9 and no worktree environment.
The repair uses its own seeded uv environment with Python 3.13.13.
It installs the existing manifests without any dependency edit.
The first uv command rejected `--copies`.
The successful install uses `--seed` and `--link-mode copy`.

The native SpecKit prerequisite command failed because PowerShell is absent.

```bash
rtk proxy env SPECIFY_FEATURE_DIRECTORY=specs/3215-upgrade-mode-descriptions pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

The five specification files provide the authorized file-only equivalent.
The repair does not change shared `.specify` metadata or execute branch hooks.

The configured STE dictionary, `data/ste_dictionary.json`, is absent.
The licensed PDF source is also absent.
The linter can grade structural rules, but it reports `dictionary: skipped` and `Scope: partial`.
That partial result does not prove the configured STE gate.
The verified descriptions use sentences with at most 16 words and one action per instruction.

## Markdown and STE Commands

The Markdown command checks all six tracked artifacts and reports zero broken links.

```bash
rtk proxy .venv/bin/markdown-link-check --root . specs/3215-upgrade-mode-descriptions changelog.d/issue-3215-upgrade-mode-descriptions.md
```

The STE command uses explicit file paths because this tool does not accept a directory.
The absent dictionary prevents a complete result.
The tool also cannot grade HTML files directly.
The real rendering contracts verify the exact template text and its sentence lengths.

```bash
rtk proxy .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 specs/3215-upgrade-mode-descriptions/spec.md specs/3215-upgrade-mode-descriptions/plan.md specs/3215-upgrade-mode-descriptions/tasks.md specs/3215-upgrade-mode-descriptions/implementation.md specs/3215-upgrade-mode-descriptions/analysis.md changelog.d/issue-3215-upgrade-mode-descriptions.md tests/contract/upgrade_portal/test_mode_descriptions.py tests/e2e/upgrade_portal/test_mode_descriptions_journey.py --quiet
```

## Publication Boundary

This artifact records local preparation only.
This phase permits no push or pull request.
The repair must wait for an explicit, fully verified main SHA after issue #3494.
No protected merge or exact-main proof occurred in this phase.

## Local-Only Refresh on 2026-10-02

The parent permits local work only on `0d1cfffbcdef3f1f66cb49b5abcfbbd3d90e0b95`.
This permission does not authorize publication, a workflow, a merge, or delivery.
Issue #3494 retains the sole publication window.

The original commit remains at the local tag `preservation/issue3215-local-7ee65990`.
The local rebase created `74fbd4ec61d9295e16dd68934f15f111557da902`.
The range comparison confirms an identical patch before the refresh edits.
The exact ten-file reservation remains unchanged.
The live issue claim remains assigned to this app session.
The paged public PR list contains zero open pull requests at the reservation check.

The accepted per-model repair in #3633 supports two AP cases.
One shared target version uses the organization AP job.
Different AP target versions use separate site child jobs.
The descriptions now state both cases.
They also state a supported version choice for each device's model.
The browser module retains `pytest.importorskip`.
Strict mode still refuses a missing browser package instead of hiding an empty suite.

### Current Runtime Evidence

| Check | Current result |
| - | - |
| Real route, model, capture, safety, and lock cases | 398 passed, zero skipped. |
| Selection route coverage | 85.55 percent against the 80 percent threshold. |
| Required rendering and Chromium cases | All 21 passed, including all six Chromium cases. |
| Strict and owner refusal proofs | 19 passed, including missing-package, missing-owner, and wrong-owner cases. |
| Full E2E collection | 596 cases collected without an import error or skipped module. |
| Required Chromium cases after full collection | 596 collected, 590 deselected, and all six required cases passed. |
| Full upgrade-portal browser run | 327 passed and 52 skipped. |

The full run uses the current CI browser timeout and strict setting.
Of its skips, 51 require the optional journey flag.
The remaining skip is the unchanged capture journey with no available version.
No skipped case counts as a pass.
No unpublished #3494 capture seed enters this worktree.

The full isolated run reads 134 audit records across eight sites.
It reports zero leaked holds.
The live-run guard checks five sites after each of 68 modules.
It reads 371 history rows and reports zero leaked live runs.
The worktree audit trail remains empty before and after the run.

The exact runtime commands are:

```bash
rtk proxy .venv/bin/python -m pytest tests/contract/upgrade_portal/test_mode_descriptions.py tests/contract/upgrade_portal/test_select.py tests/contract/upgrade_portal/test_upgrade_start.py tests/contract/upgrade_portal/test_org_upgrade_routes.py tests/contract/upgrade_portal/test_org_precheck_routes.py tests/contract/upgrade_portal/test_run_create_adopts_precheck.py tests/contract/upgrade_portal/test_lock.py tests/unit/upgrade_portal/test_select_lock_helpers.py tests/unit/upgrade_portal/test_confirm_warning.py tests/unit/upgrade_portal/test_org_postcheck_view.py tests/unit/upgrade_portal/test_org_postcheck.py tests/unit/upgrade_portal/test_org_postcheck_bridge.py tests/unit/upgrade_portal/test_upgrade_service_plan.py tests/unit/firmware/test_aggregate_upgrade_service.py --timeout=120 --cov=src.upgrade_portal.app.routes.select --cov-report=term-missing:skip-covered --cov-report=json:/Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-coverage.json --cov-report=xml:/Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-coverage.xml --cov-fail-under=80 --tb=short --show-capture=no -q
rtk proxy env UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -m pytest tests/contract/upgrade_portal/test_mode_descriptions.py tests/e2e/upgrade_portal/test_mode_descriptions_journey.py -v --base-url=http://127.0.0.1:8056 --timeout=180 --screenshot=only-on-failure --tracing=retain-on-failure --output=/Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-required-browser --basetemp=/Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-required-temp
rtk proxy .venv/bin/python -m pytest tests/unit/upgrade_portal/test_e2e_strict_guard.py tests/unit/upgrade_portal/test_e2e_run_owner_header.py -v --timeout=120
rtk proxy env UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -m pytest tests/e2e/ --collect-only -q --base-url=http://127.0.0.1:8056 --timeout=180
rtk proxy env UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -m pytest tests/e2e/ -k TestModeDescriptionJourney -v --base-url=http://127.0.0.1:8056 --timeout=180 --screenshot=only-on-failure --tracing=retain-on-failure --output=/Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-collected-browser --basetemp=/Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-collected-temp
rtk proxy env UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -m pytest tests/e2e/upgrade_portal/ -v --base-url=http://127.0.0.1:8056 --timeout=180 --output=/Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-full-browser --basetemp=/Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-full-browser-temp -ra
```

### Current Local Gates

Syntax and focused Ruff and Black checks pass for the entrypoint and both owned test modules.
The complete Ruff command also passes.
The complete Black check leaves 2,026 files unchanged.
The configured type check passes for 665 source files.
The explicit type check passes for both owned test modules.
Docstring style and the unchanged complexity threshold also pass.
The 18 functions still have at most 23 body lines and five parameters.
The verified descriptions still have at most 16 words in a sentence.

The configured portal Bandit check reads 103 files and 45,568 source lines.
It reports zero findings and zero input errors.
The complete PR-template Bandit command also passes.
It reads 788 files and 215,141 source lines with zero findings and zero input errors.
The strict hashed runtime audit reads the complete unchanged runtime manifest.
Its session report records 105 dependencies, zero vulnerabilities, and zero skips.
It does not audit the pinned Git development tools revision.

```bash
rtk proxy .venv/bin/python -m ruff check .
rtk proxy .venv/bin/python -m black --check --diff .
rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r . -q -f json -o /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-full-bandit.json
rtk proxy uv pip compile --quiet --system-certs --python .venv/bin/python --generate-hashes --output-file /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-runtime-hashed.txt requirements.txt
rtk proxy .venv/bin/pip-audit -r /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-runtime-hashed.txt --no-deps --disable-pip --require-hashes --strict --progress-spinner off --format json --output /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-runtime-audit.json
```

The current manifests are identical to the original repair base.
The existing Python 3.13.13 environment therefore needs no dependency installation.
The configured STE dictionary and licensed source remain unavailable.
Partial structural scores do not prove the complete STE gate.

### Clean Commit Checks and Offline PR Review

The current PR template contains 23 items.
The offline session review preserves all its headings, comments, checklist text, and order.
It names unavailable browser-agent tools, prohibited menu actions, and unchanged deployment files.
It does not represent a published PR.

The live guide preflight passes with six input validations and three guide checks.
After the new local commit, repeat that preflight before each required analyzer command.
Require a clean relevant tree before the committed-tree comparison and full ratchet.
Keep both reports in the session artifact directory.

```bash
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from 0d1cfffbcdef3f1f66cb49b5abcfbbd3d90e0b95 --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt --log-level WARNING --report /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-committed-quality.json --summary /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-committed-quality.md
rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --log-level WARNING --report /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-full-quality.json --summary /Users/jmorrison/.copilot/session-state/463f83b1-ff82-4ada-9e60-ba359652884c/files/issue3215-refresh-full-quality.md
```

This comparison uses the parent's immutable local refresh base.
It is not a before-push comparison or publication permission.
Any later publication grant requires its own current-base comparison and fresh CI.
