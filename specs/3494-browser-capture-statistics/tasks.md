# Tasks: Browser capture statistics

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

**Template**: `.specify/templates/tasks-template.md`, read-only.

**Issue**: [#3494](https://github.com/jmorrison-juniper/MistHelper/issues/3494).

**Retained requirements**: [The comment that preserves #3359](https://github.com/jmorrison-juniper/MistHelper/issues/3494#issuecomment-5937045284).

**Separate gap**: [#3375](https://github.com/jmorrison-juniper/MistHelper/issues/3375) remains unchanged.

**Baseline**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.

**Granted delivery baseline**: `0d1cfffbcdef3f1f66cb49b5abcfbbd3d90e0b95`.

**Scope**: Test-only seed repair, direct contracts, negative guard proofs, and real Chromium assertions.

## Historical delivery grant and proof

### Evidence correction for issue #4273

This record preserves historical reports from the #3494 implementation and delivery stages.
Those reports are not fresh results for the current checkout.
The local session artifacts are unavailable.
No replacement artifact was created, and no absent result was inferred.

The permanent [delivery receipt](https://github.com/jmorrison-juniper/MistHelper/pull/3733#issuecomment-5959964003)
records the merge and reported checks.
The [reservation release](https://github.com/jmorrison-juniper/MistHelper/issues/3494#issuecomment-5961232880)
confirms the accepted commit `a11c1189d8e861bd3683e669bfdb9b654ec1eeab`.
These records preserve delivery history, not the missing command outputs, XML, coverage data, or source snapshots.
The closed #3494 and merged #3733 do not resolve the missing citations in #4273.

Source inspection supports T001, T004 through T008, T010 through T012, T014, and T025.
Their delivered files remain in the repository.
T003 remains open because its saved baseline is unavailable.
Every other task that cited absent session evidence remains open, including verification and evidence-reconciliation tasks.
D001 remains complete only as a historical delivery action supported by the permanent receipt.
D002 through D005 remain open because their full verification artifacts are unavailable.
An open task here identifies an evidence gap, not a request to repeat the merged repair or its publication.
The STE limitations and reported optional-suite failures remain unchanged.

The following sections retain the original stage reports and instructions.
Their environment paths are historical, and their execution restrictions apply to those stages only.

### Historical delivery report

The original tasks and evidence describe the initial local preparation.
The parent now grants this session sole position-19 publication and delivery.
The seven-file scope remains unchanged.
The live claim and complete open-PR file lists show no competing owner.
The clean prepared commit rebased onto the exact delivery baseline without a conflict.

The browser module no longer imports resource-bearing globals from another conftest identity.
It selects the exact identifiers as contract literals.
The unit reader first reuses the native pytest fixture module.
If no native fixture is loaded, it reuses an existing matching module before importing one.
Neither correction changes the shared store, fixture state, or product behavior.

| Current-base proof | Exact result |
| - | - |
| Global seed red | All 16 required cases fail on unchanged granted-main seed input. |
| Real Chromium red | All four cases fail on count `0` or `No field changed.`. |
| Owned unit contracts | 87 passed, zero skips. The additional case proves duplicate native-module refusal. |
| Current focused unit and contracts | 395 passed, zero skips. |
| Native unit and real browser proof | 91 passed, including all four required browser cases. |
| Complete current CI E2E collection | 594 collected, 542 passed, 52 existing skips, zero failures. |
| Named capture-options skip | Reproduced on the exact delivery baseline, with 12 passes and one skip. |
| Current changed regions | All 433 executable lines and 54 guard branch paths have complete coverage. |
| Native runtime isolation | Four measured test/server processes have zero actual SDK transport calls and zero external connections. |
| Required input preflight | Six attempted, read, and validated inputs. Three guides read and checked. |
| Full unchanged ratchet | 1008 discovered files, 960 analyzed, 48 existing exclusions, 725 existing findings, zero new findings. |
| Current local writing grade | Partial heuristic evidence only. The licensed dictionary and language model remain unavailable. |

The full E2E command disables automatic tracing, screenshots, and video.
The 51 opt-in policy skips remain named.
The operator journey runner was not executed during this delivery phase.
Its initial `ff3cc1` failures remain historical evidence, not a current-baseline claim.
The separate lifecycle gap remains unchanged.
The merged tier reader, model selectors, authentication seams, and refusal behavior remain unchanged.

The original report stored command outputs, XML, source hashes, and measurements in a local session directory.
That directory is unavailable.
The permanent delivery receipt records the reported source and merged-main identities.
Do not write a guessed future SHA into these documents.

### Delivery stages

- [X] D001 Verify the live claim, exact granted main, and complete open-PR file lists. Rebase only the seven-file repair.
- [ ] D002 Repeat current-base red, native green, focused contracts, full current E2E, exact changed coverage, and applicable local gates. UNAVAILABLE: the original raw verification artifacts are absent.
- [ ] D003 Commit the current proof, run the clean committed-scope ratchet, push once, and open the current full-template PR. Historical delivery: PR #3733 records publication, but the original ratchet output is UNAVAILABLE.
- [ ] D004 Require every fresh applicable quality, title, and CodeQL result. Merge only the full verified head through strict protection.
- [ ] D005 Run the actual resulting-main local proof, verify cleanup, add the persistent PR receipt, and pause after the parent handoff.

## Format and completion evidence

Each task uses `- [ ] TNNN [P?] [Story?] Description with an exact path`.
Story tasks use `[US1]`, `[US2]`, or `[US3]`.
The `[P]` marker permits parallel execution only after the listed prerequisites finish.
Shared test support belongs to the foundational phase because all three stories require it.

All tasks start unchecked.
Supplied baseline evidence does not complete a task.
Complete a task only after you verify its delivered file and evidence.
For source delivery, append `(delivered: actual/path)` with a repository file that can be inspected.
For verification, cite retained evidence with the command, exit code, result, checked counts, and relevant assertions.
Do not use a temporary local session path as a permanent evidence citation.
If raw evidence is unavailable, retain the historical report and leave the verification task unchecked.
Use actual paths and results, not placeholders.

Use `PASS`, `FAIL`, `UNAVAILABLE`, `PARTIAL`, or `SKIPPED` as explicit result labels.
An unavailable verification task stays unchecked.
A capability-report task can finish with `PARTIAL` or `UNAVAILABLE`, but it cannot declare that verification passed.
A required new browser case that skips fails verification.
An existing adjacent skip does not prove the affected behavior.

## Workflow and path boundaries

This tasks stage creates only `specs/3494-browser-capture-statistics/tasks.md`.
It changes no input document and makes no commit.
The tasks below describe later implementation.

Use the explicit feature paths and the template-only workflow.
The optional before-tasks and after-tasks git-commit hooks did not run.
The companion after-tasks hook did not run because it writes `.spec-context.json`.
The specification and plan authorize this file-only exception.
PowerShell is absent on this host.
No PowerShell, shared discovery, branch, companion-state, or Git script ran during task generation.

During implementation, change only these source/test paths:

```text
tests/e2e/upgrade_portal/conftest.py
tests/e2e/upgrade_portal/test_capture_version_comparison.py
tests/unit/upgrade_portal/test_e2e_capture_statistics.py
```

The feature also owns its specification directory and this release-note fragment:

```text
changelog.d/issue-3494-browser-capture-statistics.md
```

Keep the manifest and completion notes in this tasks file.
Keep raw evidence, caches, coverage data, and browser artifacts outside the checkout.
Use `SESSION_DIR` for a unique absolute directory under the current session's `files/` directory.
Use `REPO_ROOT` for the absolute root of this app-owned worktree.
Resolve both variables before execution and record their actual values.

Use the existing `.venv`, Python 3.13.13, installed development tools, and installed Chromium.
Do not repeat bootstrap or dependency installation.
Use synthetic records and the owned loopback test server only.
Preserve the signed-session helpers and scrubbed child environment.
Use no cloud credentials, live Mist requests, production stores, or containers.
Do not reuse a listening portal.

Do not change product code, dependencies, SDK pins, primary keys, schemas, baselines, exclusions, or suppressions.
Do not change `README.md`, `CHANGELOG.md`, shared `.specify` state, another specification, or another owner's files.
Do not repair the lifecycle-state gap.
Do not create another issue.
Permit only the later local commit specified below.
Run no remote Git operations or deployment steps.

Keep new code in semantic classes.
Add no wrapper function, product fallback, or conftest helper.
Keep each new method within five parameters, five logical blocks, and 25 lines.
Apply the plan's reserved-path and existing-debt exceptions without expanding the conftest edit.
Add explanatory comments and ASCII action logs within the changed block and new code.

## Supplied baseline evidence

The plan records the following results at the baseline revision.
These results are inputs, not fresh task results.

| Measurement | Supplied result |
| - | - |
| Global captures | Five captures, with three devices each. |
| Index fields | Empty `version`, `status`, and `ip`. `uptime` equals `0`. |
| Device counts | Connected `0`, disconnected `3`. |
| Shipped version-change count | `0`. The assertion for `3` failed. |
| Adjacent browser probe | `12 passed, 1 skipped in 11.26 seconds`. |
| Probe scope | `test_capture.py` and `test_org_missing_precheck_journey.py` only. |
| Supplied skip | `test_capture.py:837`. The options page offered no version. |

The adjacent probe is not a full browser regression.
Record fresh red and green results for the required new cases.
Report fresh adjacent skips separately, with their actual node IDs and reasons.

## Phase 1: Setup

**Purpose**: Establish the explicit reservation, existing environment, and local evidence paths.

- [X] T001 Confirm the scope and retained requirements in `specs/3494-browser-capture-statistics/spec.md` and `specs/3494-browser-capture-statistics/plan.md`. Record the boundaries in `specs/3494-browser-capture-statistics/tasks.md`. (delivered: specs/3494-browser-capture-statistics/tasks.md)
- [ ] T002 Verify the existing interpreter, tools, Chromium, and isolated-server capabilities. Save their versions and unavailable capabilities in `$SESSION_DIR/environment.txt`. UNAVAILABLE: the original environment record is absent.
- [ ] T003 Record the explicit feature manifest in `specs/3494-browser-capture-statistics/tasks.md`. Save the original conftest, capture invariants, and existing-change boundary in `$SESSION_DIR/baseline/`. The manifest remains here, but the saved baseline is UNAVAILABLE.

Set `PYTHONDONTWRITEBYTECODE=1`.
Set session-local pytest, Ruff, Black, mypy, and general cache paths.
Keep compiled syntax-check output in a session-local pycache.
Do not write repository `data/` outputs.
Use local, read-only baseline comparisons without shared discovery or Git scripts.
Preserve any unrelated existing changes.

**Checkpoint**: The environment and reservation are explicit. Missing capabilities remain labeled.

---

## Phase 2: Foundational shared test support

**Purpose**: Create all direct contracts and guard cases before the browser tests and seed repair.

- [X] T004 Add a semantic call recorder in `tests/unit/upgrade_portal/test_e2e_capture_statistics.py`. Record the real index builder's inputs and outputs, then restore the patch after each test. (delivered: tests/unit/upgrade_portal/test_e2e_capture_statistics.py)
- [X] T005 Add `CaptureStatisticsGuard` in `tests/unit/upgrade_portal/test_e2e_capture_statistics.py`. Validate supplied statistics, normalized MAC membership, explicit fields, and checked counts. (delivered: tests/unit/upgrade_portal/test_e2e_capture_statistics.py)
- [X] T006 Add `CaptureIndexGuard` in `tests/unit/upgrade_portal/test_e2e_capture_statistics.py`. Validate supplied index entries, explicit fields, and checked counts. (delivered: tests/unit/upgrade_portal/test_e2e_capture_statistics.py)
- [X] T007 Add parameterized `TestCaptureStatisticsGuards` cases in `tests/unit/upgrade_portal/test_e2e_capture_statistics.py`. Use independent positive controls and fresh damaged records. (delivered: tests/unit/upgrade_portal/test_e2e_capture_statistics.py)
- [X] T008 Add `TestGlobalCaptureStatistics` contracts in `tests/unit/upgrade_portal/test_e2e_capture_statistics.py`. Check all five captures, builder calls, index fields, counts, preservation, and the empty-site fixture. (delivered: tests/unit/upgrade_portal/test_e2e_capture_statistics.py)
- [ ] T009 Run the global contracts against unchanged seeds in `tests/unit/upgrade_portal/test_e2e_capture_statistics.py`. Save the actual red assertions and checked counts in `$SESSION_DIR/red-unit.txt`. UNAVAILABLE: the original red assertions and output are absent.

### Required direct contracts

Observe five real `devices.build_device_index` calls for the five global captures.
Do not substitute a marker result or construct an index by hand.
Require the complete capture-key set below.

| Capture key | Expected running version | Total | Connected | Disconnected |
| - | - | - | - | - |
| `PRE_CAPTURE_ID` | `0.14.29216` | 3 | 3 | 0 |
| `STANDALONE_PRE_CAPTURE_ID` | `0.14.29216` | 3 | 3 | 0 |
| `POST_CAPTURE_ID` | `0.15.1` | 3 | 3 | 0 |
| `STORED_POLL_CAPTURE_ID` | `0.14.29216` | 3 | 3 | 0 |
| `TIER3_CAPTURE_ID` | `0.14.29216` | 3 | 3 | 0 |

Require three inventory records, three statistics records, and three index entries for each capture.
Require unique, valid MACs under `devices.normalize_device_mac`.
Compare complete normalized MAC membership, not positions or subsets.
Require each statistics row to contain exactly `mac`, `version`, `status`, `ip`, and `uptime`.
Require the explicit capture version, `"connected"`, the inventory address, and uptime `3600`.
Require the same running fields in each index entry.

Compare the full stored nine-key count map with the shipped count builder.
Also assert the fixed device counts independently.
Assert that the shipped `count_version_changes` returns exactly `3` for the existing pre/post pair.
Do not copy a product formula into the tests.

Preserve capture IDs, organizations, sites, roles, tiers, ownership, timestamps, inventory fields, and fake versions.
Preserve the Tier 3 guest-client count and existing extra sections.
Keep the four legacy captures' `capture_status="verified"` and absent `state`.
Keep the polling capture's `capture_status="complete"` and `state="verified"`.
Keep the empty-site fixture's empty statistics and zero counts.
The nonempty global-seed guards must not become a product rule for empty sites.

### Required independent guard cases

Use no browser or server fixture, including indirect fixture dependencies.
Do not inspect source text or mutate global captures.
Test unreadable inputs and these damaged records:

| Guard input | Required proof |
| - | - |
| Empty inventory, statistics, and index | Reject a zero-record check. |
| Nonempty inventory with empty statistics | Reject missing statistics despite an inventory version. |
| Missing, extra, invalid, or duplicate statistics MACs | Name the mismatch and report checked counts. |
| Duplicates after shipped MAC normalization | Reject the duplicate normalized key. |
| Empty or incorrect statistics fields | Reject each version, status, IP, and uptime defect. |
| Missing or extra index entries | Reject incomplete or excess membership. |
| Empty or incorrect index fields | Reject each version, status, IP, and uptime defect. |
| Valid alternate MAC spellings | Accept the join under the shipped normalization rule. |
| Different inventory and statistics versions | Require the explicit statistics version, not an inventory fallback. |

Assert `AssertionError`, the specific field or MAC, and exact checked counts.
Distinguish inventory, statistics, and index input counts from completed field checks.
Use meaningful positive assertions instead of bare truthy assertions or broad exception checks.
The negative tests pass only when their intended guard failures occur.

T009 must fail on the seed defect, not an import, collection, dependency, or server error.
Do not wrap global-seed regressions in `pytest.raises`, `xfail`, or a skip.
Keep `conftest.py` unchanged through this checkpoint.

**Checkpoint**: Fresh unit failures prove the defective global seeds. Guard cases exist before any seed change.

---

## Phase 3: User Story 1 - Read each running version change (Priority: P1)

**Goal**: Prove the retained visible count and all three rendered version rows through the existing picker.

**Independent test**: Chromium must pass one count case and three parameterized row cases with zero skips.

- [X] T010 [US1] Add the semantic picker workflow in `tests/e2e/upgrade_portal/test_capture_version_comparison.py`. Use the owned page, real route, exact capture IDs, and safe navigation helpers. (delivered: tests/e2e/upgrade_portal/test_capture_version_comparison.py)
- [X] T011 [US1] Add the separate visible-count case in `tests/e2e/upgrade_portal/test_capture_version_comparison.py`. Require exact text `3`. (delivered: tests/e2e/upgrade_portal/test_capture_version_comparison.py)
- [X] T012 [US1] Add three parameterized row cases in `tests/e2e/upgrade_portal/test_capture_version_comparison.py`. Require each MAC, changed state, and exact version-change text. (delivered: tests/e2e/upgrade_portal/test_capture_version_comparison.py)
- [ ] T013 [US1] Run the new Chromium module against unchanged seeds in `tests/e2e/upgrade_portal/test_capture_version_comparison.py`. Save red count and row results in `$SESSION_DIR/red-browser.txt`. UNAVAILABLE: the original red browser output is absent.

Open `/compare` and require a real HTTP `200` response.
Select `e2e-capture-pre-0001` with `compare-before-select`.
Select `e2e-capture-post-0001` with `compare-after-select`.
Assert both selected values before submission.
Submit with `compare-run-button` and wait for navigation.
Reuse `_click_and_wait` and `_require_built_route` where they do not convert a refusal into a skip.

Require `compare-stat-devices-version-changed` to be visible with exact text `3`.
Require exactly three device rows with the expected MAC keys.
Parameterize the row proof over `000000000001`, `000000000002`, and `000000000003`.
Each row case must select the same existing pair through the picker.
Require `compare-device-row-<mac>` to show `changed`.
Require its Changes cell to show `version: 0.14.29216 to 0.15.1`.
Use retrying Playwright assertions and whitespace normalization.

Keep the existing module dependency guard for workstation compatibility.
For required evidence, set `UPGRADE_PORTAL_E2E_STRICT=1`.
Do not add missing-data skips, fabricated captures, mocked responses, direct comparison URLs, sleeps, or polling loops.
Require the count case and all three row cases to execute.
If the pair is refused, record the response and refusal text.
Stop before any lifecycle, selection, or product change.

**Checkpoint**: Fresh browser failures cover both retained requirements. The count failure does not hide row evidence.

---

## Phase 4: User Story 2 - Read faithful device statistics (Priority: P1)

**Goal**: Supply representative statistics to the shipped builders without changing any product contract.

**Independent test**: All five global captures must satisfy the direct input, index, and count contracts.

- [X] T014 [US2] Replace only the empty-statistics block of `stand_in_capture` in `tests/e2e/upgrade_portal/conftest.py`. Supply per-device statistics to the shipped index builder. (delivered: tests/e2e/upgrade_portal/conftest.py)
- [ ] T015 [US2] Review the narrow edit in `tests/e2e/upgrade_portal/conftest.py` against the preservation contracts. Save the scoped diff and unchanged lifecycle evidence in `$SESSION_DIR/seed-preservation.txt`. UNAVAILABLE: the original scoped preservation evidence is absent.

T014 requires both T009 and T013 to deliver seed-related red results.
Do not repair the fixture before that evidence exists.
Keep the inventory comprehension unchanged.
Use one linear comprehension over `records` with exactly these values:

| Field | Value |
| - | - |
| `mac` | `record["mac"]` |
| `version` | The explicit `version` argument. |
| `status` | `"connected"` |
| `ip` | `record["ip"]` |
| `uptime` | `3600` |

Keep the existing global addresses `192.0.2.1`, `192.0.2.2`, and `192.0.2.3`.
Retain other stand-in sites' existing documentation addresses.
Log before and after statistics construction and index construction.
Report record and index counts, not credentials.
Keep the statistics local and add no stored capture section.
Call `devices.build_device_index` with the real inventory and statistics.
Keep the shipped count builder.
Do not mutate the resulting index.
Preserve shipped MAC, virtual-chassis, API-refusal, and lifecycle rules.

**Checkpoint**: Only the authorized statistics block changes. The independent guard proofs precede focused green runs.

---

## Phase 5: User Story 3 - Detect missing test input (Priority: P2)

**Goal**: Prove that the direct guards reject missing or incorrect input without a server.

**Independent test**: Valid controls pass. Every damaged case raises its exact failure with checked counts.

- [ ] T016 [US3] Run `TestCaptureStatisticsGuards` in `tests/unit/upgrade_portal/test_e2e_capture_statistics.py`. Save positive controls and all expected negative results in `$SESSION_DIR/guard-proofs.txt`. UNAVAILABLE: the original guard output is absent.
- [ ] T017 [US3] Verify field causes, normalized membership, inventory-only version rejection, and exact counts from `tests/unit/upgrade_portal/test_e2e_capture_statistics.py`. Record the measured case totals in `$SESSION_DIR/guard-summary.json`. UNAVAILABLE: the original measured summary is absent.

Run all related guard selectors in one pytest invocation.
Require positive case and field-check counts for valid controls.
Require explicit failures for zero-record and unreadable inputs.
Do not label a zero-record iteration as a passing guard.
Keep expected guard failures separate from the global regression assertions.
Reject skips, broad exceptions, source-text assertions, and seed-dependent negative records.

**Checkpoint**: Direct negative proofs pass before the focused green results.

---

## Phase 6: Polish and cross-cutting verification

**Purpose**: Prove the repaired behavior, full browser compatibility, changed-region coverage, and configured quality results.

- [ ] T018 Run the focused unit and contract scope from `specs/3494-browser-capture-statistics/plan.md`. The original report states 371 passed with zero skips. UNAVAILABLE: the original reviewed unit XML is absent.
- [ ] T019 Run the required new cases in `tests/e2e/upgrade_portal/test_capture_version_comparison.py` with strict Chromium. Save four passing cases and zero skips in `$SESSION_DIR/focused-browser.txt`. UNAVAILABLE: the original browser output is absent.
- [ ] T020 Run every journey under `tests/e2e/upgrade_portal`, including nested modules and run controls. The original report states 322 passed and 52 existing skips. It reports all 51 opt-in cases executed separately, with 22 passed, 19 baseline failures, and 10 expected failures. It reports 21 passed, 20 failures, and 10 expected failures on the identical baseline. No new group failed according to that report. This result is not a green opt-in suite. UNAVAILABLE: the original browser XML and opt-in comparison are absent.
- [ ] T021 Create a session-local branch coverage configuration for the three authorized Python files. Preserve all tracked coverage settings. Use greenlet tracing for the real Playwright calls. UNAVAILABLE: the original coverage configuration is absent.
- [ ] T022 [P] Measure the new unit module with the session coverage configuration. The original report states 86 passed, including the isolated missing-package guard proof. UNAVAILABLE: the original measured unit XML is absent.
- [ ] T023 [P] Measure the new browser module with strict Chromium and the session coverage configuration. The original report states four required cases passed without skips. UNAVAILABLE: the original measured browser XML is absent.
- [ ] T024 Combine current-source coverage data. The original report states complete coverage for 405 changed executable lines and 46 guard branch paths, without exclusions. UNAVAILABLE: the original coverage measurement is absent.
- [X] T025 [P] Add the owned test-repair note in `changelog.d/issue-3494-browser-capture-statistics.md`. Use one `### Fixed` heading and name #3494. (delivered: changelog.d/issue-3494-browser-capture-statistics.md)
- [ ] T026 [P] Compile the three authorized Python files and `MistHelper.py` without repository bytecode. The original report states all four compiled successfully. UNAVAILABLE: the original gate output is absent.
- [ ] T027 [P] Run full configured Ruff from `pyproject.toml`. The original report states the full root scope passed without findings. UNAVAILABLE: the original gate output is absent.
- [ ] T028 [P] Run full configured Black from `pyproject.toml` without fixes. The original report states all 2002 files were unchanged. UNAVAILABLE: the original gate output is absent.
- [ ] T029 [P] Run the exact CI mypy targets from `.github/workflows/ci.yml`. The original report states 663 source files passed and both new test modules passed a separate strict check. UNAVAILABLE: the original gate output is absent.
- [ ] T030 [P] Run `bandit-exclude-check` against the unchanged exclusions in `pyproject.toml`. The original report states both source-path samples passed. UNAVAILABLE: the original gate output is absent.
- [ ] T031 Run full configured Bandit after T030. The original report states 786 files and 213949 lines had zero findings. Its configured scope excludes tests. UNAVAILABLE: the original Bandit report is absent.
- [ ] T032 [P] Run the full unchanged test-quality ratchet before committing. The original report states 994 files included both new modules, with zero new findings against 725 existing findings. UNAVAILABLE: the original ratchet report is absent.
- [ ] T033 [P] Verify local feature links directly before staging. The original report states four Markdown files contained three valid local links. The tracked-only probe checked zero untracked files, so it was not sufficient evidence. UNAVAILABLE: the original gate output is absent.
- [ ] T034 [P] Complete the dictionary-based STE grade. The available heuristic grade covered seven files and scored 92 through 98. Its dictionary_used value was false for every file. Full STE verification remains UNAVAILABLE until the licensed dictionary and language model are available. No score or exit code converts that limitation into a pass. The original partial report is also unavailable.
- [ ] T035 Summarize exact gate outcomes and owned-server cleanup. Preserve the optional baseline failures and unavailable STE capability. The historical summary remains here, but the original gate and cleanup evidence is UNAVAILABLE.
- [ ] T036 Analyze the explicit spec, plan, tasks, scoped diff, manifest, and evidence. Correct the dependency guard, new class structure, action logs, coverage guide, and trailer. The original report states 13 compliant classes and 35 compliant methods. UNAVAILABLE: the original analysis is absent.
- [ ] T037 Reconcile the seven-file manifest and completion evidence. The original report states eight protected file checks and a protected-tree comparison passed. UNAVAILABLE: the original preservation report is absent.
- [ ] T038 Make the authorized local-only commit after this document and the staged checks are complete. Save its exact SHA, file list, and message outside the committed documents in `$VALIDATION_DIR/local-commit.json`. That external proof records completion without a self-referential commit or a dirty worktree.
- [ ] T039 [P] Run the tracked Markdown link check after staging the seven-file manifest. The original report states four tracked Markdown files passed without broken links. UNAVAILABLE: the original gate output is absent.
- [ ] T040 [P] Complete dictionary-based STE verification. Repeat the available heuristic grade after the final documents. Save its PARTIAL result outside the checkout. This task remains unavailable while the licensed dictionary and language model are absent.
- [ ] T041 Record final local results, remaining capability limits, and task evidence here. Keep the actual commit SHA in the external local-commit proof, not this committed document. Publication requires a separate parent release. The historical summary remains here, but its original gate evidence is UNAVAILABLE.

### Focused commands

Run these commands from `REPO_ROOT`.
Use `rtk proxy` to retain the original command's output and exit code.
Capture each command's full result in its named session artifact.
The red unit run selects only the global contracts:

```bash
rtk proxy .venv/bin/python -B -m pytest -ra --timeout=120 \
  -o cache_dir="$SESSION_DIR/pytest-cache-red-unit" \
  --basetemp="$SESSION_DIR/red-unit" --junitxml="$SESSION_DIR/red-unit.xml" \
  tests/unit/upgrade_portal/test_e2e_capture_statistics.py \
  -k TestGlobalCaptureStatistics
```

For T013, run the new browser command below against unchanged seeds.
Use distinct `red-browser` cache, temporary, output, and XML paths.
Retain the failing count case and all three failing row cases.
Run the direct negative proofs after the repair:

```bash
rtk proxy .venv/bin/python -B -m pytest -ra --timeout=120 \
  -o cache_dir="$SESSION_DIR/pytest-cache-guards" \
  --basetemp="$SESSION_DIR/guards" --junitxml="$SESSION_DIR/guards.xml" \
  tests/unit/upgrade_portal/test_e2e_capture_statistics.py \
  -k TestCaptureStatisticsGuards
```

Run the focused green unit and contract scope:

```bash
rtk proxy .venv/bin/python -B -m pytest -ra --timeout=120 \
  -o cache_dir="$SESSION_DIR/pytest-cache-focused" \
  --basetemp="$SESSION_DIR/focused" --junitxml="$SESSION_DIR/focused.xml" \
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

rtk proxy env UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -B -m pytest \
  -ra --browser chromium --timeout=180 \
  -o cache_dir="$SESSION_DIR/pytest-cache-browser" \
  --basetemp="$SESSION_DIR/browser-new" --output="$SESSION_DIR/playwright-new" \
  --junitxml="$SESSION_DIR/browser-new.xml" \
  tests/e2e/upgrade_portal/test_capture_version_comparison.py

rtk proxy env UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -B -m pytest \
  -ra --browser chromium --timeout=180 \
  -o cache_dir="$SESSION_DIR/pytest-cache-browser-all" \
  --basetemp="$SESSION_DIR/browser-all" --output="$SESSION_DIR/playwright-all" \
  --junitxml="$SESSION_DIR/browser-all.xml" \
  tests/e2e/upgrade_portal
```

Report collected, passed, failed, errored, and skipped counts for each run.
Do not replace the full regression with the supplied adjacent probe.
List every adjacent skip by node ID and reason.
Keep the supplied options-page skip and the separate lifecycle gap visible.
If an adjacent journey fails, record it without editing its file.
Do not claim a green full regression when a required case fails or skips.

### Changed-region coverage

Use exactly this session-local configuration:

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

Export `SESSION_DIR` and `REPO_ROOT`.
Set `COVERAGE_FILE` to `$SESSION_DIR/.coverage`.
Set `COVERAGE_RCFILE` to `$SESSION_DIR/coverage.ini`.
Do not set `source` or instrument the WSGI child.
Disable pytest-cov for these measurements.

```bash
rtk proxy .venv/bin/python -B -m coverage run \
  --rcfile="$COVERAGE_RCFILE" --context=unit -m pytest \
  -p no:cov -o addopts= -o cache_dir="$SESSION_DIR/pytest-cache-coverage-unit" \
  --basetemp="$SESSION_DIR/coverage-unit" \
  tests/unit/upgrade_portal/test_e2e_capture_statistics.py

rtk proxy env UPGRADE_PORTAL_E2E_STRICT=1 .venv/bin/python -B -m coverage run \
  --rcfile="$COVERAGE_RCFILE" --context=browser -m pytest \
  -p no:cov -o addopts= -o cache_dir="$SESSION_DIR/pytest-cache-coverage-browser" \
  --browser chromium --timeout=180 --basetemp="$SESSION_DIR/coverage-browser" \
  --output="$SESSION_DIR/playwright-coverage" \
  tests/e2e/upgrade_portal/test_capture_version_comparison.py

rtk proxy .venv/bin/python -B -m coverage combine --rcfile="$COVERAGE_RCFILE" --keep
rtk proxy .venv/bin/python -B -m coverage json --rcfile="$COVERAGE_RCFILE" \
  --show-contexts --pretty-print -o "$SESSION_DIR/coverage.json"
```

Map the conftest's new-side diff against the saved baseline to executable lines.
Treat both new test files as entirely added, including their untracked content.
Normalize coverage paths against `REPO_ROOT`.
Require a positive executable-line count in each authorized file.
Require 100 percent of changed executable lines and every new guard decision branch.
Report checked-line, checked-branch, missing-line, and missing-branch counts.
Reject unreadable data, zero measured regions, and excluded changed lines.

The aggregate threshold `0` permits data collection only.
It does not satisfy the acceptance gate.
Do not require complete coverage of unrelated conftest code.
Do not change tracked omissions, exclusions, branch rules, or thresholds.

### Configured quality commands

Run the full configured scopes without automatic fixes.
Retain the exact CI mypy targets confirmed in `.github/workflows/ci.yml`.
Do not narrow Ruff or Black to the changed files.

```bash
rtk proxy env PYTHONPYCACHEPREFIX="$SESSION_DIR/pycache" \
  .venv/bin/python -B -m py_compile \
  MistHelper.py \
  tests/e2e/upgrade_portal/conftest.py \
  tests/e2e/upgrade_portal/test_capture_version_comparison.py \
  tests/unit/upgrade_portal/test_e2e_capture_statistics.py

rtk proxy .venv/bin/python -B -m ruff check .
rtk proxy .venv/bin/python -B -m black --check --diff .
rtk proxy .venv/bin/python -B -m mypy \
  src/ MistHelper.py wsgi.py \
  scripts/mist_ideas_analyzer_pkg/__init__.py \
  scripts/mist_ideas_distiller_v2_pkg/__init__.py \
  --config-file pyproject.toml

rtk proxy .venv/bin/bandit-exclude-check \
  --include-sample ./src/foundation/support/utils/zen_city_metadata.py \
  --include-sample '.\src\foundation\support\utils\zen_city_metadata.py'

rtk proxy .venv/bin/python -B -m bandit -c pyproject.toml -r .

rtk proxy .venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --report "$SESSION_DIR/test-quality.json" \
  --summary "$SESSION_DIR/test-quality.md"
```

Record each exact command, exit code, version, configured scope, checked count, and failure reason.
Use a read-only scope listing if a tool does not print its file count.
Configured Bandit excludes tests.
Do not claim that Bandit scanned the new modules.
The exact CI mypy scope is not a separate type-check claim for the new tests.
Confirm that the full test-quality gate includes both new modules before the commit.
Do not use a committed-diff scope that can omit untracked files.
Keep the ratchet baseline and configuration unchanged.
Do not suppress findings or repair unrelated failures.

### Link and STE results

Before committing, check feature-document local paths and anchors directly.
Include the owned release-note fragment.
Record a positive checked-link count.
The supplied untracked link probe checked zero files and does not prove these links.

After the local commit, run the configured tracked check and STE command:

```bash
rtk proxy .venv/bin/markdown-link-check --root "$REPO_ROOT" \
  specs/3494-browser-capture-statistics

rtk proxy .venv/bin/ste-linter --config .ste-linter.toml \
  specs/3494-browser-capture-statistics/plan.md
```

Repeat the configured STE grade for `spec.md`, `tasks.md`, the fragment, and changed test text.
Keep extracted changed text and its source-line mapping in `SESSION_DIR` if the tool requires extraction.
Report each graded count, score, backend, and missing capability.
The installed tool version is `misthelper-devtools 0.6.0`.
The current environment lacks `data/ste_dictionary.json`, spaCy, and an English model.
Retain the tool's `dictionary_unavailable` result and label the grade `PARTIAL`.
Do not claim a complete dictionary check.
Do not install a model, create a dictionary, or change STE configuration.
If another configured check cannot run, label it `UNAVAILABLE` and retain its missing-capability reason.
Neither a skip nor partial coverage converts an unavailable check into a pass.

### Consistency analysis and local commit

T036 is an explicit-path, read-only consistency analysis.
Do not use shared discovery or state-writing SpecKit hooks.
Account for every FR, SC, retained count requirement, and retained row requirement.
Check the real-builder inputs, shipped count map, exact picker selection, and all rendered rows.
Verify guard failure causes, checked counts, full browser results, and changed-region coverage.
Verify that lifecycle fields, product code, dependencies, baselines, exclusions, and other-owner files remain unchanged.
Record existing structural exceptions from the plan without expanding them.
Resolve feature-owned gaps and repeat affected checks before T038.
Keep unresolved verification failures and unavailable checks explicit.

The final manifest contains only these feature-owned paths:

```text
specs/3494-browser-capture-statistics/spec.md
specs/3494-browser-capture-statistics/plan.md
specs/3494-browser-capture-statistics/tasks.md
tests/e2e/upgrade_portal/conftest.py
tests/e2e/upgrade_portal/test_capture_version_comparison.py
tests/unit/upgrade_portal/test_e2e_capture_statistics.py
changelog.d/issue-3494-browser-capture-statistics.md
```

Reconcile committed, staged, unstaged, and feature-owned untracked content before staging.
Do not stage a missing, unrelated, or session-evidence path.
Stage explicit paths only.
Do not stage the whole checkout or use a Git automation script.
Make the local commit only after required executable gates pass and the consistency analysis accepts the feature.
The documented partial STE capability does not become a passing dictionary check.
If another required gate fails or is unavailable, leave T038 unchecked and record the blocker.
Do not amend a commit.

Use this Conventional Commit message:

```text
test(upgrade-portal): supply representative capture statistics

Closes #3494

Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>
```

Verify the local commit's file list and SHA.
Run T039 and T040 on the resulting tracked documents.
If either result is incomplete, preserve that result instead of claiming complete verification.
Confirm that the owned test servers stopped.
Use only recorded process IDs if cleanup is necessary.
Do not stop an unrelated process.

## Dependencies and execution order

### Phase dependencies

Setup establishes the reservation and evidence directory.
The foundation creates direct contracts and negative cases, then records the unit regression.
US1 records the browser regression while the seeds remain unchanged.
US2 requires both red results before its statistics-block repair.
US3 proves the independent guards after that repair.
Focused green results precede the full browser regression.
Coverage and configured checks precede consistency analysis and the local commit.
Tracked link and STE results follow that commit.

### Task prerequisites

These prerequisites include required sequence gates and same-file edit serialization.
Parallel verification tasks use separate session artifacts and do not edit shared files.

| Task | Prerequisites |
| - | - |
| T001 | None. |
| T002 | T001. |
| T003 | T001. |
| T004 | T002, T003. |
| T005 | T004. |
| T006 | T005. |
| T007 | T005, T006. |
| T008 | T004, T007. |
| T009 | T008. |
| T010 | T009. |
| T011 | T010. |
| T012 | T011. |
| T013 | T012. |
| T014 | T009, T013. |
| T015 | T014. |
| T016 | T007, T015. |
| T017 | T016. |
| T018 | T017. |
| T019 | T013, T018. |
| T020 | T019. |
| T021 | T020. |
| T022 | T021. |
| T023 | T021. |
| T024 | T022, T023. |
| T025 | T019, T020. |
| T026 | T024, T025. |
| T027 | T024, T025. |
| T028 | T024, T025. |
| T029 | T024, T025. |
| T030 | T024, T025. |
| T031 | T030. |
| T032 | T024, T025. |
| T033 | T024, T025. |
| T034 | T024, T025. |
| T035 | T026, T027, T028, T029, T030, T031, T032, T033. Report T034 separately as unavailable. |
| T036 | T003, T015, T017, T018, T019, T020, T024, T035. |
| T037 | T036. |
| T038 | T037. |
| T039 | T037 and the explicit staged manifest. |
| T040 | T037. Report the unavailable dictionary separately. |
| T041 | T035, T036, T037. The actual commit proof follows T038 outside the tracked files. |

### User story dependencies

US1 test construction requires the foundation, but not the seed repair.
US2 requires US1's red browser evidence and the foundation's red unit evidence.
US1's final green result requires US2's repaired seed.
This is a test-first dependency, not a cycle between implementation tasks.
US3's decisions are independent of the seeds, but their verification runs after US2 as required.
The common focused run proves US2 without a browser.
The separate browser run proves US1 without relying on a count-only assertion.
The isolated guard run proves US3 without a server.

### Parallel opportunities

T022 and T023 can run together after T021.
Coverage uses unique parallel data files and separate pytest and browser artifact directories.
T025 can run while coverage measurements execute because it changes only the owned fragment.
After T024 and T025, run the marked quality tasks with separate result files.
T031 must wait for T030.
The tracked link check and heuristic STE report can run together after staging.
Neither report changes the files that the commit contains.
Write task-completion notes serially.
Do not edit the shared unit module, browser module, or conftest concurrently.

## Parallel example: User Story 1

After T021, run T022's direct unit coverage and T023's Chromium coverage in parallel.
These runs write different evidence files and read the completed test code.
Create the picker, count, and row tests serially because they share one browser module.

## Parallel example: User Story 2

After T021, T022 measures builder-input contracts while T023 measures the browser assertions.
Neither run changes `tests/e2e/upgrade_portal/conftest.py`.
Do not combine the seed edit with a concurrent test run that reads an incomplete fixture.

## Parallel example: User Story 3

Run all direct guard cases together in T016.
No parallel edit applies because both guard classes and their cases share one unit module.
After T024 and T025, independent quality tasks can inspect the completed guard code in parallel.

## Requirement trace

| Requirement | Tasks and evidence |
| - | - |
| FR-001, FR-002, retained per-device inputs | T004, T008, T009, T014, T018. Real-builder records and explicit versions. |
| FR-003, FR-004, SC-002 | T008, T014, T018. Five complete indexes and exact device counts. |
| FR-005, FR-006, retained visible count | T010, T011, T013, T019. Exact picker values and visible text `3`. |
| FR-007, retained rendered rows | T012, T013, T019. Three distinct row cases with both versions. |
| FR-008 | T005, T006, T007, T016, T017. Independent field and membership failures with counts. |
| FR-009, FR-010, FR-012 | T003, T008, T015, T018, T036, T037. Preserved inputs, shipped rules, and lifecycle boundary. |
| FR-011, SC-004 | T020. Every browser journey and each adjacent skip reason. |
| SC-001 | T009, T013. Fresh seed-related red unit and browser assertions. |
| SC-003 | T019. Four required Chromium cases with zero skips. |
| SC-005 | T021, T022, T023, T024. Complete changed executable lines and guard branches. |
| SC-006 | T026 through T035, T039, T040, T041. Exact scopes, results, and capability limits. |

## Implementation strategy

### MVP first

The MVP proves US1 with the existing picker, exact count, and all three version rows.
It requires US2's narrow seed repair because the baseline has no running statistics.
Do not reduce the MVP to a visible count or a mocked comparison.
Complete the foundation, both red runs, repair, guard proofs, and focused green runs.
The MVP is a local proof, not permission to omit the remaining verification.

### Incremental delivery

Preserve the supplied baseline and create the shared direct tests first.
Record the new unit and browser failures before changing conftest.
Repair only the statistics input.
Prove guard failures, then record focused green results.
Run all browser journeys and measure changed-region coverage.
Run the unchanged configured gates and explicit capability reports.
Analyze consistency, reconcile the manifest, and make the authorized local commit.
Record the tracked link and partial STE results without overstating their coverage.

### Task summary

| Phase | Task count |
| - | - |
| Setup | 3 |
| Foundational shared support | 6 |
| US1 | 4 |
| US2 | 2 |
| US3 | 2 |
| Cross-cutting verification | 24 |
| **Total** | **41** |

All 41 tasks use the required checkbox, sequential ID, applicable labels, and exact file paths.
No task authorizes product changes, lifecycle remediation, shared-state writes, or remote operations.

## Historical implementation completion notes

The user limited this implementation stage to source delivery and focused verification.
The root agent owns broader regression, configured gates, changed-region coverage, analysis, and any local commit.
That instruction also permits the owned release note before the deferred full regression.
T018 and every unexecuted verification, analysis, or commit task remain unchecked.
The focused checks below do not complete T027 or T028, which require full repository scopes.

**REPO_ROOT**: `/Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-laughing-couscous`.

**SESSION_DIR**: The original local implementation evidence directory is unavailable.

### Delivered file manifest

This stage changed exactly these five files.
The existing specification and plan remain unchanged.

```text
tests/e2e/upgrade_portal/conftest.py
tests/e2e/upgrade_portal/test_capture_version_comparison.py
tests/unit/upgrade_portal/test_e2e_capture_statistics.py
changelog.d/issue-3494-browser-capture-statistics.md
specs/3494-browser-capture-statistics/tasks.md
```

The conftest edit replaces one empty-statistics call with a five-field comprehension and before/after action logs.
The edit leaves the inventory builder, count builder, capture dictionary, and all other seams unchanged.
The recorder retains the shipped builder and validates its actual output identity and unchanged input records.
Each global contract observes five real builder calls and the complete expected capture-key set.
The empty-site proof observes one separate real build with zero records.

The unit contracts preserve inventory, metadata, clients, Tier 3 extras, guest counts, and empty-site counts.
Four legacy captures retain `capture_status="verified"` without `state`.
The polling capture retains `capture_status="complete"` and `state="verified"`.
Issue #3375 remains unchanged.
Issue #3359 remains a duplicate, not a separate repair.
The separate visible-count case and all three rendered-row cases retain its requirements.

### Historical measured results

Each named text artifact records the full command and exit code.
The XML artifacts retain every executed node ID.

| Run | Result | Measured cases | Exit code | Evidence under SESSION_DIR |
| - | - | - | - | - |
| Unchanged global unit seeds | FAIL, expected | 16 failed, 68 deselected, zero errors or skips. | 1 | `red-unit.txt`, `red-unit.xml` |
| Unchanged strict Chromium seeds | FAIL, expected | Four failed, zero errors or skips. | 1 | `red-browser.txt`, `red-browser.xml`, `playwright-red-seed/` |
| Independent guard selector | PASS | 68 passed, 16 deselected, zero errors or skips. | 0 | `guard-proofs.txt`, `guards.xml` |
| Final focused unit module | PASS | 85 passed, zero failures, errors, or skips. | 0 | `focused-unit.txt`, `focused.xml` |
| Final strict Chromium module | PASS | Four passed, zero failures, errors, or skips. | 0 | `focused-browser.txt`, `browser-new.xml` |
| Changed-file Ruff | PASS | Three explicit Python files. | 0 | `focused-ruff.txt` |
| Changed-file Black | PASS | Three explicit Python files remained formatted. | 0 | `focused-black.txt` |

Five unit failures named missing statistics.
Five unit failures named empty running versions.
Five unit failures reported connected `0` and disconnected `3`.
One unit failure reported zero version changes instead of three.
The browser count case showed `0`.
Each browser row case showed `No field changed.` instead of the required version text.
All four cases selected the exact existing capture pair and passed both HTTP `200` checks before those failures.
The shared conftest matched the saved baseline through both required red runs.

The first browser attempt rejected an empty shared message region.
That test assertion did not indicate a lifecycle or selection refusal.
The corrected test accepts an empty message region and still rejects visible refusal text.
`red-browser-initial.txt` and `red-browser-initial.xml` preserve that preliminary result.
The subsequent required red run reached the count assertion and all three Changes-cell assertions before any seed repair.

The final unit result contains 16 global contracts and 69 guard-class cases.
The guard cases include two positive controls, 34 membership failures, 32 field failures, and one fixture-target refusal.
Each required negative guard decision asserts its exact cause and complete checked-count message.
Each positive control completes eight running-field checks under the shipped MAC normalization rule.
`guard-summary.json` records those measured categories.
The method inspection checked 33 new methods and found no limit violation.
Every new method stays within 25 lines, five parameters, and five logical blocks.

### Isolation and remaining work

The existing interpreter reports Python `3.13.13`.
The installed Chromium and owned loopback server executed all four required browser cases without a skip.
No dependency or browser installation ran.
The owned server fixtures completed teardown.
The final inspection found zero remaining owner records under the session evidence directory.
The checkout trail guards reported zero records before and after each run.
The browser guards reported zero leaked holds and zero leaked live runs.

This stage used the recorded file-only SpecKit exception.
The optional before-implement and after-implement git-commit hooks did not run.
The companion after-implement hook did not run because it writes shared feature state.
No shared discovery, branch, context, or PowerShell script ran.
No commit, push, pull request, publication, live Mist request, production database, firmware action, or container operation ran.
All protected and parent-owned files remain unchanged.

No execution blocker remains for the delivered focused scope.
Full regression, existing skip reporting, changed-region coverage, full configured gates, and SpecKit analysis remain unexecuted here.
The broader unit and contract scope also remains for the root agent.
These results do not claim a complete dictionary, type, security, coverage, or full-regression check.
`implementation-results.json` records the focused outcomes and the deferred work.
`scope-verification.txt` records the exact file boundary and unchanged protected document hashes.
