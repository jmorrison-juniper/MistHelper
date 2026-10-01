# Implementation Plan: Browser capture statistics

**Branch**: `jmorrison-juniper-browser-capture-statistics` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: `specs/3494-browser-capture-statistics/spec.md`

**Baseline**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`

**Stage output**: `specs/3494-browser-capture-statistics/plan.md` only.

## Summary

Repair the browser seed input, not the product builder.
Create one statistics record for each inventory record in `stand_in_capture`.
Pass those records to the shipped `devices.build_device_index`.
Keep the shipped count builder.

Prove all five global seeds with direct tests.
Prove the visible version-change count and each version-change row with Chromium.
Test guard failures with independent synthetic records and explicit checked counts.
Retain every requirement from #3359 that #3494 preserves.
Leave the separate #3375 lifecycle fields unchanged.

### File-only workflow

Use the repository plan template and the exact specification path.
Keep research, data-model, contract, and validation decisions in this plan.
Do not create separate design artifacts during this stage.

Do not run `setup-plan`, `create-new-feature`, `update-agent-context`, or shared feature-discovery scripts.
Do not change shared `.specify` state, the branch, source files, or another owner's files.
Do not commit or publish this plan.

Skip the optional git-commit hooks.
The registered companion after-plan hook writes `.spec-context.json`.
That write conflicts with the one-file limit.
Use the specification's template-only exception.
Do not execute the state-writing hook or claim that it ran.
Do not edit `.specify/extensions.yml`.

## Technical Context

**Language/Version**: Python 3.13.13 in the existing worktree `.venv`.

**Primary Dependencies**: Existing pytest, pytest-playwright, Playwright Chromium, Flask, coverage, and repository development tools.
The product SDK constraint remains `mistapi>=0.64.0,<0.65`.

**Storage**: Synthetic in-memory captures and the existing isolated test stores.
Use `tmp_path` or an external session directory for evidence.
Do not use production stores or repository `data/` outputs.

**Testing**: Direct pytest tests, existing unit and contract tests, real Chromium journeys, and changed-line branch coverage.

**Target Platform**: The current Darwin worktree.
Retain the existing cross-platform server and path helpers.

**Project Type**: Test-harness repair for the upgrade capture web portal.
No new product interface, service, schema, or dependency.

**Performance Goals**: One linear statistics comprehension per capture.
Use the existing bounded browser waits.
Add no sleep, network read, or polling loop.

**Constraints**: Three authorized source/test files.
Change only the statistics block inside the existing `stand_in_capture` function.
Use class-based semantic guards and existing safe helpers.
Preserve the shipped MAC, virtual-chassis, API-refusal, and count rules.

**Scale/Scope**: Five global captures, three devices per capture, and one existing pre/post comparison pair.
Run every test under `tests/e2e/upgrade_portal` after the shared seed changes.

The current runtime and development manifests are already installed.
The earlier `ensurepip` failure was recovered with a copied interpreter, its own `libpython` link, and UV installation.
No tracked dependency changed.
Chromium is already available.
Do not repeat bootstrap, dependency installation, or browser installation.

## Constitution Check

*Gate before research and after design.*

The current task reserves the two exact test-module paths.
That explicit reservation controls the location exception for the existing oversized test directories.
New classes must still obey the five-child limit.
The final structure separates count records, seed expectations, call records, and test inputs into nested classes.

The current task requires rare, meaningful comments.
Do not expand this repair into an annotation change on every executable line.
Use action logs around meaningful transformations, browser navigation, selection, and submission.
The authoritative Git workflow requires Conventional Commits and the current task names the required author trailer.
Do not apply the older timestamped commit rule or change protected constitution files.

| Gate | Decision |
| - | - |
| Safety and isolation | Pass. Use the owned loopback server, synthetic records, signed test sessions, and existing scrubbed child environment. |
| Product boundaries | Pass. Change no product capture, firmware, authentication, route, template, storage, key, or schema. |
| Class-based architecture | Pass for new code. Put guard decisions, call recording, browser steps, and tests in semantic classes. Add no standalone delegation wrapper. |
| Structural limits | Apply the explicit grandfathering and reserved-path exceptions below. Keep each new method within five parameters, five blocks, and 25 lines. |
| Comments and action logs | Add explanatory inline comments and ASCII before/after logs within the changed statistics block and new code. Do not expand the existing function edit. |
| Quality gates | Pass by design. Preserve the configured checks, thresholds, baselines, exclusions, and suppressions. Report exact results and checked counts. |
| Git and deployment | Planning performs no Git mutation. Later implementation permits a local commit only. The parent owns publication after position 18. |

Existing debt is not part of this repair.
At the baseline, `stand_in_capture` spans 54 lines and has five parameters.
Its module has 86 top-level functions and nine classes.
The flat browser and unit directories contain 58 and 152 files.
Do not refactor those existing violations.
Place the two new test modules at the exact authorized paths.
Keep their new hierarchy levels within five children.

Separate remediation requires another owner-approved change.
That change can split the seed module and organize the flat test suites.
It must preserve their fixtures and collection behavior.

**Post-design result**: The design stays within the authorized scope and the recorded exceptions.
No unresolved technical clarification or unjustified gate failure remains.

## Project Structure

### Documentation for this feature

```text
specs/3494-browser-capture-statistics/
├── spec.md       # Existing input. Do not change it during planning.
└── plan.md       # The only output of this stage.
```

The next tasks stage can create `tasks.md` in this feature directory.
This stage does not create it.
The feature owns its release-note fragment, but this stage writes no fragment.

### Source and tests

```text
tests/
├── e2e/upgrade_portal/
│   ├── conftest.py                         # Narrow statistics-block repair.
│   └── test_capture_version_comparison.py  # New picker, count, and row proof.
└── unit/upgrade_portal/
    └── test_e2e_capture_statistics.py       # New seed contracts and guard decisions.
```

**Structure Decision**: Use only these three authorized source/test paths during implementation.
Read the shipped builders and existing helpers without changing them.
Do not edit adjacent journeys to make the regression run pass.

## Phase 0: Research

### Established baseline

The parent supplied this evidence at the exact baseline commit:

- The direct probe checked five global captures and three devices per capture.
- Each index entry held empty `version`, `status`, and `ip`, with `uptime` equal to `0`.
- Each count map held `devices_connected=0` and `devices_disconnected=3`.
- The shipped `count_version_changes` returned `0`.
- The assertion that expected `3` failed.
- Chromium ran `test_capture.py` and `test_org_missing_precheck_journey.py`.
- That limited run reported **12 passed, 1 skipped in 11.26 seconds**.
- The only skip was `test_capture.py:837`: the options page offered no version.

This evidence is not a full-browser-suite result.
Record fresh red and green results for the new tests during implementation.
Do not rerun the baseline probe during planning.

### Research decisions

| Decision | Rationale | Alternatives considered |
| - | - | - |
| Supply statistics to the shipped index builder. | `_state_of` reads running fields from statistics, not inventory. | Reject a product fallback, a hand-built index, and index mutation after construction. |
| Use the explicit `version` argument. | It separates the pre-check and post-check running versions. | Reject copying or inferring a version from inventory. |
| Use one five-field comprehension. | It repairs the input without restructuring the existing seed function. | Reject a new conftest helper, a loop with unrelated changes, and a new statistics framework. |
| Keep guards in the new unit module. | Negative tests need only supplied records and shipped normalization. | Reject source-text checks, global-seed mutation, browser startup, and guards that accept zero checks. |
| Select the exact existing capture IDs. | First/last selection can compare two pre-check versions. | Reject a fabricated pair, a direct comparison URL, and a mocked response. |
| Measure coverage in the pytest process. | Direct tests execute the seed block. Browser assertions also execute in that process. | Reject unnecessary WSGI-child instrumentation and tracked coverage changes. |

The read-only coverage research confirmed that child instrumentation is not required for the planned executable changes.
The repository coverage configuration omits tests.
Use a separate session-local configuration for this evidence.

## Phase 1: Design and Contracts

### Seed statistics model

Keep the inventory comprehension unchanged.
Replace only the empty-statistics call block with statistics construction and the real builder call.

| Statistics field | Required value |
| - | - |
| `mac` | The same `record["mac"]` as the inventory record. |
| `version` | The explicit capture `version` argument. |
| `status` | The explicit value `"connected"`. |
| `ip` | The existing documentation address from `record["ip"]`. |
| `uptime` | The deterministic positive integer `3600`. |

Create the list with a comprehension over `records`.
Each row has exactly these five fields.
The existing global addresses remain `192.0.2.1`, `192.0.2.2`, and `192.0.2.3`.
Other stand-in sites retain their own existing documentation addresses.
Pass `records` and this list to `devices.build_device_index`.
Keep statistics local to the function.
Do not add a stored capture section.

Log before and after statistics construction and index construction.
Report record and index counts, not credentials.
Keep those logs and comments inside the statistics block.

### Seed and index contracts

| Global seed | Explicit running version | Required device counts |
| - | - | - |
| `PRE_CAPTURE_ID` | `0.14.29216` | Total `3`, connected `3`, disconnected `0`. |
| `STANDALONE_PRE_CAPTURE_ID` | `0.14.29216` | Total `3`, connected `3`, disconnected `0`. |
| `POST_CAPTURE_ID` | `0.15.1` | Total `3`, connected `3`, disconnected `0`. |
| `STORED_POLL_CAPTURE_ID` | `0.14.29216` | Total `3`, connected `3`, disconnected `0`. |
| `TIER3_CAPTURE_ID` | `0.14.29216` | Total `3`, connected `3`, disconnected `0`. |

Require all five expected capture keys.
Require three inventory records, three statistics records, and three index entries for each seed.
Require unique, valid MACs under `devices.normalize_device_mac`.
Require exact MAC membership, not list position or a subset.
Require each index entry to hold the expected version, status, IP, and uptime.

Use a semantic recording callable to observe the real builder inputs and outputs.
Retain the real builder and restore the patch after each test.
Check five index-builder calls for the five global captures.
Do not replace the result with a marker or a synthetic index.
Compare the stored nine-key count map with the shipped count builder.
Also assert the three fixed device counts independently.

Preserve capture IDs, organization and site fields, run ownership, roles, tiers, timestamps, inventory fields, and fake versions.
Preserve the Tier 3 guest-client count and existing extra sections.
Keep the four legacy global captures' `capture_status="verified"` and absent `state` unchanged.
Keep the polling seed's `capture_status="complete"` and `state="verified"` unchanged.
Do not change the runner, loader, adopter, or lifecycle contract for #3375.

The empty-site fixture remains valid.
Its empty statistics list and zero counts must remain unchanged.
The nonempty global-seed guard must not become a product rule that rejects empty sites.

### Guard decision contracts

Use semantic class methods for statistics and index validation.
Their inputs contain records and explicit expectations.
Negative cases must not read the seed source, mutate global captures, or request a server fixture.

Each guard reports the inventory, statistics, and index counts that it checked.
Each failure names the failing field or MAC.
Distinguish input counts from the number of field checks completed.
An unreadable input or zero-record check must fail, not pass through an empty iteration.

Use independent valid records as the positive control.
Damage fresh copies for these direct failure cases:

1. Empty inventory, empty statistics, and empty index.
2. Nonempty inventory with empty statistics.
3. Missing, extra, invalid, or duplicate statistics MACs.
4. Duplicate MACs that become equal after shipped normalization.
5. Empty or incorrect statistics version, status, IP, or uptime.
6. Missing or extra index entries.
7. Empty or incorrect index version, status, IP, or uptime.

Check `AssertionError`, the specific cause, and the exact checked counts.
Do not use a broad exception check or a bare truthy assertion.
Prove that valid alternate MAC spellings join under the shipped rule.
Use an inventory-only version in one independent case.
Require the explicit statistics version instead.
Require the missing-statistics case to fail despite that inventory version.

Keep new methods and class groups within the structural limits.
Use parameterized cases instead of one large test function.
Reuse existing seed, count, normalization, and safe browser helpers.

### Browser contract

Use the existing owned `page` and server fixtures with Chromium.
Open `/compare` and require a real HTTP `200` response.
Use the picker controls:

- `compare-before-select`: select `e2e-capture-pre-0001`.
- `compare-after-select`: select `e2e-capture-post-0001`.
- `compare-run-button`: submit the selection and wait for navigation.

Assert both selected values before submission.
Use the existing `_click_and_wait` and `_require_built_route` helpers where suitable.
Do not use helpers that turn missing data or refused comparisons into a skip.
Keep the repository module dependency guard for workstation compatibility.
Run required evidence with `UPGRADE_PORTAL_E2E_STRICT=1`.

Use separate count and row tests so the count failure cannot hide the row proof.
Parameterize the row test over `000000000001`, `000000000002`, and `000000000003`.
Each required case selects the same existing pair through the picker.

Require `compare-stat-devices-version-changed` to be visible with exact text `3`.
Require exactly three device rows with the expected MAC keys.
Require each `compare-device-row-<mac>` to show `changed`.
Require its Changes cell to show `version: 0.14.29216 to 0.15.1`.
Use Playwright retrying assertions and whitespace normalization.
A count alone or an API response alone does not satisfy the row contract.

If the shipped selection refuses this pair, record the response and refusal text.
Stop before any scope change.
Do not repair lifecycle fields or selection rules.
No required new case may skip.
Treat a skipped required case as failed verification.

### Requirement trace

| Requirement | Planned proof |
| - | - |
| Preserved #3359 per-device MAC and capture version, FR-001/002 | Real-builder call records for all five seeds. |
| FR-003/004, SC-002 | Explicit index fields and fixed device counts for all five seeds. |
| Preserved #3359 visible count, FR-005/006 | Chromium picker selection and exact visible count `3`. |
| Preserved #3359 rendered row, FR-007 | Chromium checks each expected MAC and both versions in its Changes cell. |
| FR-008, SC-001/003 | Fresh red seed tests and independent negative guards with checked counts. |
| FR-009/010/012 | Narrow edit, preservation assertions, and unchanged shipped MAC, chassis, refusal, and lifecycle tests. |
| FR-011, SC-004/005/006 | Full browser regression, skip report, changed-line coverage, and exact configured gate results. |

### Validation guide

These commands belong to implementation, not this planning stage.
Run from the current worktree root with the existing `.venv`.
Set `SESSION_DIR` to a unique absolute directory outside the checkout.
Set `REPO_ROOT` to the absolute worktree root.
Keep pytest temporary files, browser evidence, analyzer reports, and coverage files in `SESSION_DIR`.
Use `PYTHONDONTWRITEBYTECODE=1` and a session-local pytest cache.
Do not set production store addresses or reuse a listening portal.

#### Red, repair, and green sequence

1. Add the two authorized test modules without changing global seeds.
2. Run the new direct contracts against `stand_in_capture_index`.
3. Run the new Chromium count and row cases against the unchanged seeds.
4. Save the expected failures and checked counts.
5. Repair only the statistics block.
6. Rerun the same tests and require no new-case skip.

The negative guard tests must pass because they prove expected failures.
Do not wrap the defective global-seed assertions in `pytest.raises`, `xfail`, or a skip.

#### Focused unit and contract scope

```bash
.venv/bin/python -B -m pytest -ra --timeout=120 \
  -o cache_dir="$SESSION_DIR/pytest-cache-focused" \
  --basetemp="$SESSION_DIR/focused" \
  tests/unit/upgrade_portal/test_e2e_capture_statistics.py \
  tests/unit/upgrade_portal/test_capture_devices.py \
  tests/unit/upgrade_portal/test_capture_assembly.py \
  tests/unit/upgrade_portal/test_compare_diff.py \
  tests/unit/upgrade_portal/test_compare_statistics.py \
  tests/unit/upgrade_portal/test_compare_render.py \
  tests/unit/upgrade_portal/test_e2e_strict_guard.py \
  tests/unit/upgrade_portal/test_e2e_standin_precheck_adopter.py \
  tests/contract/upgrade_portal/test_comparison.py \
  tests/contract/upgrade_portal/test_comparison_errors.py \
  tests/contract/upgrade_portal/test_compare_picker_moment.py \
  tests/contract/upgrade_portal/test_capture_tables_and_export.py
```

Run the new browser module first, then the full regression:

```bash
UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -B -m pytest -ra --browser chromium --timeout=180 \
  -o cache_dir="$SESSION_DIR/pytest-cache-browser" \
  --basetemp="$SESSION_DIR/browser-new" --output="$SESSION_DIR/playwright-new" \
  --junitxml="$SESSION_DIR/browser-new.xml" \
  tests/e2e/upgrade_portal/test_capture_version_comparison.py

UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -B -m pytest -ra --browser chromium --timeout=180 \
  -o cache_dir="$SESSION_DIR/pytest-cache-browser-all" \
  --basetemp="$SESSION_DIR/browser-all" --output="$SESSION_DIR/playwright-all" \
  --junitxml="$SESSION_DIR/browser-all.xml" \
  tests/e2e/upgrade_portal
```

Include nested journey and run-control modules.
Report collected, passed, failed, errored, and skipped counts.
List every existing skip with its node ID and reason.
Keep the options-page baseline skip separate from the new required cases.
If an adjacent journey fails, report it without editing another owner's file.

#### Changed-line coverage

Create `coverage.ini` only in `SESSION_DIR`.
Use this session-local configuration:

```ini
[run]
branch = true
concurrency = greenlet
parallel = true
data_file = ${SESSION_DIR}/.coverage
include =
    ${REPO_ROOT}/tests/e2e/upgrade_portal/conftest.py
    ${REPO_ROOT}/tests/e2e/upgrade_portal/test_capture_version_comparison.py
    ${REPO_ROOT}/tests/unit/upgrade_portal/test_e2e_capture_statistics.py

[report]
fail_under = 0
exclude_lines =
partial_branches =
```

Export `SESSION_DIR`, `REPO_ROOT`, `COVERAGE_FILE`, and `COVERAGE_RCFILE`.
Point both coverage variables to the session paths.
Do not set `source`, because it overrides `include`.
Disable pytest-cov for these measurements.

```bash
.venv/bin/python -B -m coverage run --rcfile="$COVERAGE_RCFILE" --context=unit -m pytest \
  -p no:cov -o addopts= -o cache_dir="$SESSION_DIR/pytest-cache-coverage-unit" \
  --basetemp="$SESSION_DIR/coverage-unit" \
  tests/unit/upgrade_portal/test_e2e_capture_statistics.py

UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -B -m coverage run \
  --rcfile="$COVERAGE_RCFILE" --context=browser -m pytest \
  -p no:cov -o addopts= -o cache_dir="$SESSION_DIR/pytest-cache-coverage-browser" \
  --browser chromium --timeout=180 --basetemp="$SESSION_DIR/coverage-browser" \
  --output="$SESSION_DIR/playwright-coverage" \
  tests/e2e/upgrade_portal/test_capture_version_comparison.py

.venv/bin/python -B -m coverage combine --rcfile="$COVERAGE_RCFILE" --keep
.venv/bin/python -B -m coverage json --rcfile="$COVERAGE_RCFILE" \
  --show-contexts --pretty-print -o "$SESSION_DIR/coverage.json"
```

Map the new-side conftest diff against the saved baseline to executable coverage lines.
Treat every line of each new test file as added, including untracked files.
Normalize report paths against `REPO_ROOT`.
Require a positive executable-line count in each authorized file.
Require **100 percent of changed executable lines** and every new guard decision branch.
Report checked-line, checked-branch, missing-line, and missing-branch counts.
Reject excluded changed lines and unreadable coverage data.

The zero aggregate threshold permits collection only.
It is not the acceptance gate.
Do not require full coverage of unrelated conftest code.
Do not change tracked coverage omissions, thresholds, or report exclusions.

#### Configured quality checks

Run the full configured scopes without automatic fixes:

```bash
.venv/bin/python -B -m ruff check .
.venv/bin/python -B -m black --check --diff .
.venv/bin/python -B -m mypy \
  src/ MistHelper.py wsgi.py \
  scripts/mist_ideas_analyzer_pkg/__init__.py \
  scripts/mist_ideas_distiller_v2_pkg/__init__.py \
  --config-file pyproject.toml
.venv/bin/bandit-exclude-check \
  --include-sample ./src/utils/zen_city_metadata.py \
  --include-sample '.\src\utils\zen_city_metadata.py'
.venv/bin/python -B -m bandit -c pyproject.toml -r .
.venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --report "$SESSION_DIR/test-quality.json" \
  --summary "$SESSION_DIR/test-quality.md"
```

The mypy targets exactly match `MYPY_PATHS` in `.github/workflows/ci.yml`.
Do not narrow Ruff or Black to the changed files.
Configured Bandit excludes tests.
Report that boundary instead of claiming it scanned the new modules.
Run the full test-quality gate before committing so it includes untracked test modules.
Do not rely on a committed-diff scope that can omit them.
Do not rewrite or prune the baseline.
Do not disable rules or add suppressions.

Run syntax checks without leaving repository bytecode.
Keep any compiled output in the session directory.
Record each command, exit code, tool version, scope, count, and failure reason.
Do not repair unrelated gate failures under this reservation.

#### Link and STE capability reporting

The installed `misthelper-devtools` version is `0.6.0`.
Both `markdown-link-check` and `ste-linter` are available.
The link tool scans tracked Markdown only.
Its read-only specification probe checked zero files because this feature directory is untracked.
That result does not prove its links.

Check the feature documents' local paths and anchors directly before the local commit.
Report the positive checked-link count.
After the authorized local commit, run:

```bash
.venv/bin/markdown-link-check --root "$REPO_ROOT" specs/3494-browser-capture-statistics
.venv/bin/ste-linter --config .ste-linter.toml specs/3494-browser-capture-statistics/plan.md
```

Grade the later feature documents and changed test text during implementation.
The current worktree has no `data/ste_dictionary.json`, spaCy package, or English model.
The available STE tool reports partial coverage and `dictionary_unavailable`.
Report its score, graded count, backend, and missing capability.
Do not claim a complete dictionary check.
Do not install a model, create a dictionary, or change the STE configuration.

## Phase 2: Planning Handoff

The next tasks stage must preserve this order:

1. Add direct contracts, semantic guards, and independent negative cases.
2. Add the exact-picker Chromium count and row tests.
3. Record red results against unchanged global seeds.
4. Repair the narrow statistics block and record green results.
5. Run the focused checks, full browser regression, changed-line coverage, and configured quality gates.
6. Analyze the specification, plan, tasks, diff, evidence, and feature manifest for gaps.
7. Make the authorized local-only commit after the gates and analysis.

The analysis must account for every FR and SC and all retained #3359 requirements.
Verify that no #3375 lifecycle field or other-owner file changed.
Do not run shared discovery or state-writing SpecKit hooks.
Keep later stage artifacts inside the feature's reserved directory.

Use a Conventional Commit such as `test(upgrade-portal): supply representative capture statistics`.
Include the issue footer `Closes #3494`.
Include the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
Stage only the explicit feature manifest.
Do not commit during planning or amend another owner's commit.
Do not fetch, rebase, push, open a pull request, merge, publish, build a container, or deploy.
The parent controls the separate release after position 18.

## Complexity Tracking

| Scope exception | Why needed | Simpler alternative rejected because |
| - | - | - |
| Template-only SpecKit planning | Shared discovery, context updates, and companion state writes violate the one-file contract. | Standard stage scripts can change shared state or additional files. |
| Existing function and module hierarchy debt | The repair must remain inside the statistics block of `stand_in_capture`. | Refactoring the seed module exceeds the reservation and can alter adjacent journeys. |
| Two additions to oversized test directories | The user reserves these exact test paths and grandfathers existing hierarchy violations. | Moving tests into a new package changes the authorized layout and can change fixture discovery. |
| Local-only commit and deferred deployment | This feature is part of a parent-managed release after position 18. | Automatic branch operations or publication violate the app-managed workflow and user authorization. |
