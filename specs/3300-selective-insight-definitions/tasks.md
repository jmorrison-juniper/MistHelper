# Tasks: Selective Insight Definitions

**Input**: Design documents in `specs/3300-selective-insight-definitions/`.

**Prerequisites**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [definition-refresh.md](contracts/definition-refresh.md), and [quickstart.md](quickstart.md).

**Branch**: `jmorrison-juniper-selective-insight-definitions`.

**Source base**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.

**Tests**: The specification requires red caller evidence, compatibility proofs, and controlled timing trials.

**Organization**: Each story has its own phase and independent acceptance criteria.
US1 owns the shared selected entry and failure machinery.
US2 through US4 verify that machinery without separate production implementations.

This tasks step writes only this file.
It does not execute the implementation tasks.
Keep every task unchecked until its completion criteria pass.
Record completion as `(delivered: exact/path)` with evidence in `specs/3300-selective-insight-definitions/evidence.md`.
Keep blocked tasks unchecked and state the reason.

## Format and execution boundary

Every task uses `- [ ] Tnnn [P?] [USn?] Description with an exact file path`.
`[P]` identifies independent file edits after their stated prerequisites.
It does not authorize another agent or concurrent edits to shared evidence.

### Reserved write paths for later implementation

| Purpose | Allowed paths |
| --- | --- |
| Source | `src/export/const_definitions_exporter.py`, `src/analytics/insight_metrics_utils.py`, `src/refactors/serial_cc/site_client_insights.py` |
| Tests | `tests/unit/export/test_selective_insight_definitions.py`, `tests/unit/analytics/test_insight_metrics_utils.py` |
| Release note | `changelog.d/issue-3300-selective-insight-definitions.md` |
| Feature evidence and task status | `specs/3300-selective-insight-definitions/evidence.md`, `specs/3300-selective-insight-definitions/tasks.md` |

Read other caller files, baseline tests, and configuration only for evidence.
Update feature artifacts only to correct a verified contract or record implementation evidence.
Do not edit site, device, or organization caller files.
Do not edit README, CHANGELOG, metadata, menus, dependency manifests, SDK pins, schemas, or primary keys.
Do not edit baselines, suppressions, exclusions, agent instructions, another worktree, or the main checkout.
Do not write shared `.specify` state or companion state.
Do not invoke branch scripts, feature scripts, or hooks.
Use only the SpecKit agents that the user explicitly requires for this workflow.
Keep the existing branch and source base unchanged.

Use only offline responses and temporary CSV output.
Use `tmp_path` for acceptance outputs, cache fixtures, and benchmark data.
Store coverage metadata, tool caches, and gate reports in the current session artifact directory.
The authorized runtime audit lock can use `data/issue-3300/runtime-audit-lock.txt`.
Interpreter and tool caches remain ignored and do not enter the commit.
Copy relevant results into the feature evidence with `apply_patch`.
Do not use shell output redirection to create evidence files.
Do not read Mist credentials or contact live Mist services, databases, stores, or containers.
Do not run unrelated test suites without a targeted need and separate authorization.

Retain public `None` returns for `export_all`, the shared helper, and site, device, and client refresh entries.
The new named entry returns the planned structured attempt result.
Retain the organization metric-list or `None` return.
Use complete STE sentences and ASCII logs.
Add comments only for non-obvious intent.
Retain the plan's limits for new functions without unrelated class restructuring.
Log meaningful cache, fetch, normalization, and write actions before and after execution.
Include counts and status without secrets.

**Publication hold**: The exact parent release remains absent.
Queue position 17 follows [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335).
No task authorizes a fetch, rebase, push, pull request, merge, workflow run, build, or deployment.
The final task permits only a separately authorized local commit and local handoff.

## Phase 1: Setup

**Purpose**: Confirm the reserved scope and existing environment without changing shared state.

- [x] T001 Record the implementation boundary and tool capabilities in `specs/3300-selective-insight-definitions/evidence.md`. (delivered: specs/3300-selective-insight-definitions/evidence.md)
  - **Dependencies**: None.
  - Record the branch, source base, initial changes, and preserved-file fingerprints.
  - Confirm Python `3.13.13`, installed `mistapi 0.64.0`, and the existing worktree-owned virtual environment.
  - Use the current manifests without bootstrap, upgrades, or pin changes.
  - Record the supplied focused baseline as 321 passed, not a new execution.
  - Record the absent PowerShell executables, spelling tools, and `data/ste_dictionary.json`.
  - Record the artifact conflicts listed below.
  - **Completion**: The evidence names all permitted files, unavailable capabilities, and the publication hold.

## Phase 2: Foundational Evidence

**Purpose**: Obtain all four red caller results and before measurements before any production edit.

### Actual caller entries

| Caller | Real entry | Scope and retained return |
| --- | --- | --- |
| Site, Menu 74 | `SiteMetricOperation._refresh_const_metrics` | `site`, `None` |
| Client, Menu 75 | `SiteClientInsightsService._print_intro_and_refresh` | `client`, `None` |
| Device, Menu 76 | `DeviceMetricOperation._refresh_const_metrics` | `device`, `None` |
| Organization | `OrgExportUtils._insight_setup_or_empty` | `org`, ordered list or `None` |

- [x] T002 Build the offline caller harness in `tests/unit/export/test_selective_insight_definitions.py`. (delivered: tests/unit/export/test_selective_insight_definitions.py)
  - **Dependencies**: T001.
  - Retain real SDK discovery, `_inspect_module`, registration, cache methods, normalization, scope reading, and caller methods.
  - Bind an offline dependency host without importing credential-bearing runtime configuration.
  - Replace only external responses, the backend writer, cache time, and necessary runtime dependencies.
  - Make `mist_get(uri, query)` reject unscripted requests and record every request.
  - Use the actual 28 SDK definitions listed in `research.md`.
  - Confirm the three real special paths: `all_models`, `all_countries`, and `all_countries_channels`.
  - Supply one gateway model and one country through the real special-path dispatch.
  - Implement a temporary CSV writer at `DataExporter.write_with_format_selection`.
  - Return its real Boolean result and retain API-function metadata.
  - Separate primary, fallback, successful definition writes, and unrelated insight-output writes.
  - Guard real definition-file reads, existence checks, timestamps, and writes during each refresh.
  - Take fixture snapshots outside that interval.
  - Freeze only the cache clock. Retain real `time.sleep` and `time.perf_counter_ns`.
  - Print an absolute pytest-created `tmp_path` location for temporary test reports.
  - Capture baseline insight CSV bytes, ordered fields, normalized values, and scope lists before source changes.
  - **Completion**: All four real entries run offline under `tmp_path` without live requests or stores.
  - **Completion**: Discovery reports 28 definitions and three special paths without a fake registration list.

- [x] T003 Record the grouped red caller proof in `specs/3300-selective-insight-definitions/evidence.md`. (delivered: specs/3300-selective-insight-definitions/evidence.md)
  - **Dependencies**: T002.
  - Add `test_actual_stale_caller_refresh_is_selective` in `tests/unit/export/test_selective_insight_definitions.py`.
  - Parameterize the four actual entries with the same fully expired definition caches.
  - Replay the existing focused baseline before changing its reserved analytics assertions.
  - Record its actual count and any difference from the supplied 321-pass result.
  - Run the new caller test separately.
  - Require four behavior failures that show unrelated definition activity, not import or collection failures.
  - Record each caller's requests, definition writes, unrelated accesses, and public return.
  - Do not mock the caller refresh, shared helper, cache predicate, normalizer, or processing methods.
  - **Completion**: Four real stale-cache failures exist before every production edit.

- [x] T004 Record the grouped before trials in `specs/3300-selective-insight-definitions/evidence.md`. (delivered: specs/3300-selective-insight-definitions/evidence.md)
  - **Dependencies**: T003.
  - Add `test_controlled_refresh_benchmark` in `tests/unit/export/test_selective_insight_definitions.py`.
  - Use test-local `ISSUE_3300_BENCHMARK_PHASE=before` for the baseline expectations.
  - Require an explicit before or after phase for timing trials.
  - Without that phase, skip only the timing test with a clear opt-in reason.
  - Keep all functional caller tests active in focused runs.
  - Apply `time.sleep(0.05)` at every mock API request boundary.
  - Use this delay only for controlled timing, not ordinary functional proofs.
  - Use one untimed warm-up and exactly five measured trials for each caller.
  - Recreate identical stale fixture content and cache ages for each trial.
  - Measure the whole real refresh entry with `time.perf_counter_ns`.
  - Include the organization entry's scope read.
  - Exclude fixture creation, snapshots, prompts, and later insight collection.
  - Record all 20 durations, trial IDs, fixture identity, fixed cache clock, and actual I/O counts.
  - Measure the expectation of 28 processed definitions, 31 requests, and 28 successful definition writes per trial.
  - Do not calculate elapsed evidence from request counts or delays.
  - If measured counts differ, record the discrepancy and stop before source changes.
  - **Completion**: All four before medians and 20 measured durations exist with verified counts.

**Blocking checkpoint**: T003 and T004 must pass their evidence criteria before T007 through T010.
An expected red test is evidence, not permission to ignore an unrelated baseline failure.

## Phase 3: User Story 1 - Select Only the Required Definition

**Priority**: P1.

**Goal**: Each caller refreshes `insight_metrics` without unrelated discovery, cache access, requests, or writes.

**Independent test**: Run all four real entries with expired or missing insight caches and offline successful responses.
Require one selected request and one definition write.
Compare the resulting CSV and ordered scope lists with the captured baseline.

### Tests before implementation

- [x] T005 [P] [US1] Add selected-entry contract tests in `tests/unit/export/test_selective_insight_definitions.py`. (delivered: tests/unit/export/test_selective_insight_definitions.py)
  - **Dependencies**: T004.
  - Assert selected discovery uses `_inspect_module` and processing uses `_process_single_endpoint`.
  - Spy on real methods instead of replacing their behavior.
  - Reject package enumeration, full-export fallback, and processing of unrelated registrations.
  - Cover invalid, private, dotted, path-like, empty, non-string, and unavailable selections.
  - Cover caught import failures, unusable functions, and a prior selected registration followed by discovery failure.
  - Assert zero requests and writes for rejected or unavailable selections.
  - Specify fresh, updated, failed, discovery-failed, and repeated-attempt result invariants from `data-model.md`.
  - Cover first-error identity, HTTP status, immutable count snapshots, and unchanged earlier results.
  - Add core red HTTP and writer checks before the shared failure repair.
  - Access the planned API inside tests so missing implementation fails execution, not collection.
  - Retain red stdout for T007 without concurrent evidence edits.
  - **Completion**: The new contract assertions expose missing behavior before implementation.

- [x] T006 [P] [US1] Add focused helper assertions in `tests/unit/analytics/test_insight_metrics_utils.py`. (delivered: tests/unit/analytics/test_insight_metrics_utils.py)
  - **Dependencies**: T004.
  - Replace only the existing refresh-delegation assertions and add bounded result cases.
  - Expect `export_endpoint("insight_metrics")`, no `export_all`, and the public `None` return.
  - Cover fresh and updated results with a CSV, and successful backend output without a CSV.
  - Cover a failed result with an existing stale CSV.
  - Reject availability success and file-availability checks after a failed result.
  - Retain the banner and existing absent-file warning contract.
  - Retain existing scope parsing, exclusions, and metric-order assertions.
  - These lightweight helper tests do not replace real caller evidence.
  - Retain red stdout for T007 without concurrent evidence edits.
  - **Completion**: The changed refresh assertions fail against the original comprehensive helper.

### Shared implementation

- [x] T007 [US1] Implement the named entry and attempt result in `src/export/const_definitions_exporter.py`. (delivered: src/export/const_definitions_exporter.py)
  - **Dependencies**: T005, T006.
  - Add `DefinitionRefreshResult` in this module without changing `EndpointConfig`.
  - Include `endpoint_name`, `outcome`, `counts`, `http_status`, and `first_error`.
  - Use `fresh`, `updated`, or `failed` for the outcome.
  - Snapshot the four existing counters and return independent, read-only differences.
  - Add `export_endpoint(endpoint_name)` with early validation of one public ASCII SDK module name.
  - Remove only that name's prior registration before selected discovery.
  - Inspect only `mistapi.api.v1.const.<endpoint_name>` through `_inspect_module`.
  - Process only its `EndpointConfig` through `_process_single_endpoint`.
  - Return original caught discovery errors through the private method chain.
  - Reject missing registration without using old state or a comprehensive fallback.
  - Keep `export_all()` dynamic with its public `None` return.
  - Add selected discovery and current-attempt summary logs with counts and status.
  - Record the preceding red contract evidence in the feature evidence.
  - **Completion**: Selection, discovery-failure, and independent count-snapshot assertions pass.

- [x] T008 [US1] Repair shared fetch and write checks in `src/export/const_definitions_exporter.py`. (delivered: src/export/const_definitions_exporter.py)
  - **Dependencies**: T007.
  - Check SDK HTTP status in `_fetch_standard_endpoint` before normalization or `.data` unwrapping.
  - Preserve HTTP `4xx` and `5xx` responses in `requests.HTTPError`.
  - Retain the first available error text, or a status-bearing message for an empty error body.
  - Treat SDK `status_code=None` as a transport failure.
  - Preserve existing raw-payload support when no SDK status attribute exists.
  - Check primary writer Booleans in `_export_data` for populated and successful-empty responses.
  - Increment `endpoints_updated` only after a successful primary write.
  - Report `False` as a failed writer boundary without inventing a swallowed exception.
  - Return the first expected error through `_fetch_and_export_endpoint` and `_process_single_endpoint`.
  - Count the failure once before the existing empty fallback.
  - Contain expected fallback errors without replacing the first error, HTTP status, or failed count.
  - Keep unexpected programming exceptions visible.
  - Retain the cache rule, normalizer, configured backend, special-path aggregation, and existing fallback lists.
  - Log before and after cache, fetch, normalization, primary write, and fallback actions.
  - Use the existing safe logging boundary for visible errors and traceback context.
  - **Completion**: Core HTTP, writer, first-error, fallback, and counter tests pass without false updates.

- [x] T009 [P] [US1] Use the selected result in `src/analytics/insight_metrics_utils.py`. (delivered: src/analytics/insight_metrics_utils.py)
  - **Dependencies**: T008.
  - Construct the existing exporter with the active session.
  - Select `insight_metrics` through `export_endpoint`.
  - Keep `Export Available Insight Metrics:` and the public `None` return.
  - Replace comprehensive-export notices with truthful selected-refresh notices.
  - Report failure before any availability test.
  - Check only `ConstInsightMetrics.csv` after a fresh or updated result.
  - Distinguish successful backend output from actual CSV availability.
  - Do not add another cache decision, shared result state, retry, abort, or stale-file deletion policy.
  - Leave `get_by_scope` unchanged.
  - **Completion**: The focused assertions from T006 pass for every helper result case.

- [x] T010 [P] [US1] Change only client refresh wiring in `src/refactors/serial_cc/site_client_insights.py`. (delivered: src/refactors/serial_cc/site_client_insights.py)
  - **Dependencies**: T008.
  - Call `deps.InsightMetricsUtils.export_const_insight_metrics` from `_print_intro_and_refresh`.
  - Remove `ConstDefinitionsExporter` from `_resolve_runtime_dependencies`.
  - Retain the existing banners, prompts, selections, scope loading, filenames, and empty-output behavior.
  - Retain the refresh entry's `None` return.
  - Do not edit the site, device, or organization caller files.
  - **Completion**: The client resolves dependencies without reading the removed direct exporter attribute.

### Green caller and output proof

- [x] T011 [US1] Prove selected caller and output compatibility in `tests/unit/export/test_selective_insight_definitions.py`. (delivered: tests/unit/export/test_selective_insight_definitions.py)
  - **Dependencies**: T009, T010.
  - Make all four stale-caller tests from T003 green without replacing their real refresh paths.
  - Cover missing insight caches with unrelated caches of mixed ages.
  - Require one insight request, one successful definition write, and zero unrelated discovery or cache accesses.
  - Compare unrelated bytes and modification times outside the refresh interval.
  - Compare CSV bytes, normalized rows, multiline handling, and interval text with the before fixture.
  - Preserve the real sorted CSV fields: `description`, `intervals`, `metric_name`, `report_intervals`, `report_scopes`, `scopes`, `type`, `unit`.
  - Check ordered scope results for site, device, client, and organization.
  - Include blank names, missing scopes, template names, Unicode descriptions, and a larger ordered payload.
  - Prove caller returns, banners, selection prompts, output names, and existing error and empty-output paths.
  - Verify the client resolver without a direct exporter dependency.
  - Preserve the organization no-metrics outputs and omit `OrgInsightMetrics_Legacy.csv` on that path.
  - Count the four normalized organization insight outputs separately from definition writes.
  - **Completion**: The four real entries and output comparisons pass, with evidence recorded under this feature.

**Checkpoint**: US1 provides the behavioral MVP.
It does not permit a commit or publication before the remaining safety and gate tasks.

## Phase 4: User Story 2 - Retain the Existing Cache Boundary

**Priority**: P1.

**Goal**: Reuse fresh insight definitions and refresh at the existing 24-hour boundary.

**Independent test**: Run each caller with the controlled cache clock and temporary files.
Require zero requests and writes below 86,400 seconds.
Require one selected request and write at or above the boundary.

- [x] T012 [US2] Complete the real caller cache matrix in `tests/unit/export/test_selective_insight_definitions.py`. (delivered: tests/unit/export/test_selective_insight_definitions.py)
  - **Dependencies**: T011.
  - Cover one second below 24 hours, exact 24 hours, expired, missing, and unreadable timestamps.
  - Preserve existing behavior for future timestamps.
  - Cover a fresh insight cache with expired unrelated caches.
  - Cover an expired insight cache with fresh unrelated caches.
  - After a successful refresh, call the same entry again within the cache window.
  - Preserve fresh-cache bytes and modification times.
  - Require zero unrelated discovery, file access, or changes in every selected scenario.
  - Keep `_is_file_fresh` as the only cache authority.
  - **Completion**: All four callers pass every cache case and the second-run cache-hit proof.

## Phase 5: User Story 3 - Retain the First Failure

**Priority**: P1.

**Goal**: Report current-attempt failure without false success from an old file or an empty fallback.

**Independent test**: Inject offline HTTP, transport, discovery, and output failures through each real caller.
Require the original status and first error, zero updates, and one failed count.

- [x] T013 [US3] Complete caller failure and safe-log proofs in `tests/unit/export/test_selective_insight_definitions.py`. (delivered: tests/unit/export/test_selective_insight_definitions.py)
  - **Dependencies**: T012.
  - Cover HTTP `404` and `503` with error bodies and empty bodies.
  - Cover `status_code=None`, an SDK proxy-error result, connection failure, and timeout.
  - Cover malformed data, selected import failure, and missing usable SDK functions.
  - Cover primary writer `False`, expected writer exceptions, and successful-empty responses.
  - Cover empty fallback `False` and expected fallback exceptions after a request failure.
  - Observe the real selected result while retaining the caller and helper path.
  - Require first-error identity or the first available Boolean-boundary evidence.
  - Require the original HTTP status and current-attempt counts.
  - Distinguish processing failures `(1, 0, 0, 1)` from pre-registration failures `(0, 0, 0, 1)`.
  - Verify no second failure count and no update from a fallback.
  - Repeat attempts on one exporter and prove prior results remain unchanged.
  - With an old CSV present, reject availability success after failure.
  - Preserve existing scope reads when a failed writer leaves an old CSV.
  - Verify existing caller error and empty-output behavior without a new abort policy.
  - Prove unexpected programming faults still propagate.
  - Check before-and-after logs for counts, status, primary versus secondary errors, ASCII, and synthetic-secret exclusion.
  - Check formatted traceback text without using real credentials.
  - **Completion**: Every caller failure case passes with truthful result and log evidence.

## Phase 6: User Story 4 - Preserve Full Definition Export

**Priority**: P2.

**Goal**: Retain the separate dynamic full-definition export and its existing parameter handling.

**Independent test**: Compare real `export_all()` discovery and output with the unchanged before fixture.
Require all 28 definitions and all three special paths.

- [x] T014 [US4] Prove complete full export in `tests/unit/export/test_selective_insight_definitions.py`. (delivered: tests/unit/export/test_selective_insight_definitions.py)
  - **Dependencies**: T013.
  - Run real SDK enumeration and real processing against the complete offline fixture.
  - Compare registered names, filenames, normalized output, and API-function metadata with the before evidence.
  - Require 28 stale definitions, 31 measured requests, and 28 successful definition writes.
  - With all caches fresh, require 28 skips and zero requests or writes.
  - Cover `all_models`, `all_countries`, and `all_countries_channels`.
  - Retain model and country fallback behavior and unsupported-required-parameter skips.
  - Verify a failed definition does not prevent remaining full-export processing.
  - Retain the public `None` return.
  - Do not mock `_process_all_endpoints` or replace dynamic production discovery with a fixed list.
  - **Completion**: Full export retains the baseline coverage, outputs, cache policy, and parameter behavior.

## Phase 7: Polish and Local Handoff

- [x] T015 Record the matching after trials in `specs/3300-selective-insight-definitions/evidence.md`. (delivered: specs/3300-selective-insight-definitions/evidence.md)
  - **Dependencies**: T014.
  - Use `ISSUE_3300_BENCHMARK_PHASE=after` with the same benchmark and real caller entries.
  - Reuse the same fixture content, cache clock, stale ages, writer, request delay, and paired trial IDs.
  - Use one untimed warm-up and five measured trials for each caller.
  - Measure with real `time.perf_counter_ns` and `time.sleep(0.05)`.
  - Require one processed definition, one request, and one successful definition write per after trial.
  - Require zero unrelated cache accesses and changes.
  - Report all 40 durations in seconds.
  - Report four before medians, four after medians, and each caller's actual request and file counts.
  - Report attempted, fallback, and successful definition writes separately from insight-output writes.
  - Calculate `100 * (before_median - after_median) / before_median` for each caller.
  - Require at least 90% reduction for every caller.
  - If a target fails, retain all trials and investigate without changing the delay or fixture.
  - Identify the host, Python, SDK, fixture, warm-ups, and elapsed clock.
  - Label the results **controlled offline measurements**.
  - State that these results do not reproduce or replace the issue's live 67.3-second report.
  - **Completion**: All 40 durations, eight medians, paired counts, and four passing reduction calculations exist.

- [x] T016 Write the reserved release note in `changelog.d/issue-3300-selective-insight-definitions.md`. (delivered: changelog.d/issue-3300-selective-insight-definitions.md)
  - **Dependencies**: T015.
  - Use one `###` heading and concise `Fixed` or `Changed` bullets.
  - Describe selective refresh, unchanged caching and outputs, truthful failures, and retained full export.
  - Link issue #3300 and related issue #3266.
  - If timing appears, label it controlled offline evidence and link the feature report.
  - Do not claim a live duration, shipped release, or deployment.
  - Do not add a version stamp or edit shared release files.
  - **Completion**: The fragment states only verified behavior and remains within the reserved path.

- [x] T017 Record the required configured gates in `specs/3300-selective-insight-definitions/evidence.md`. (delivered: specs/3300-selective-insight-definitions/evidence.md)
  - **Dependencies**: T016.
  - Run the focused scope listed below, including both reserved test files.
  - Report opt-in timing skips separately from the completed T004 and T015 measurements.
  - Report every changed method's line and branch coverage.
  - Cover every added cache and failure branch.
  - Retain the configured 90% coverage floor and identify the focused denominator.
  - Run full configured Ruff, Black, exact CI mypy paths, Bandit, and runtime pip-audit.
  - Run the unchanged test-quality ratchet with both reserved test files in its measured scope.
  - Run relevant citation, local-link, and structural STE checks.
  - Explicitly validate untracked feature files when a link tool scans tracked files only.
  - Record command, scope, count, exit status, and any missing capability for each gate.
  - Install a missing tool only after a command fails because that dependency is missing.
  - Use current manifests without a bootstrap rerun, upgrade, new dependency, or pin change.
  - Never ignore an advisory, lower a threshold, write a baseline, or add a suppression.
  - If a gate needs an unreserved change, stop and report the blocker.
  - Do not represent missing dictionary or PowerShell checks as passes.
  - **Completion**: Required executable gates pass, changed-method coverage is reported, and capability limits remain explicit.

- [x] T018 Record current SpecKit analysis in `specs/3300-selective-insight-definitions/evidence.md`. (delivered: specs/3300-selective-insight-definitions/evidence.md)
  - **Dependencies**: T017.
  - Invoke the explicitly required current `speckit.analyze` agent with this feature directory.
  - Use this explicit feature directory, not branch inference or the shared path resolver.
  - Analyze the current spec, plan, tasks, and constitution without changing them.
  - After the read-only analysis, copy its report into the feature evidence with `apply_patch`.
  - Report duplication, ambiguity, missing detail, constitution alignment, coverage gaps, and inconsistent ordering.
  - Map every FR-001 through FR-013 and SC-001 through SC-007 to tasks and evidence.
  - Include a findings table, coverage table, unmapped tasks, metrics, and next actions.
  - Retain the severity of unresolved governance conflicts.
  - Do not claim formal script initialization when PowerShell is unavailable.
  - Do not invoke hooks, nested agents, or automatic remediation.
  - **Completion**: The current analysis report exists with honest findings and coverage.
  - **Blocking condition**: Unresolved critical findings block T019 and require separate authorization for any excluded remediation.

- [x] T019 Prepare the local commit and handoff record in `specs/3300-selective-insight-definitions/evidence.md`. (delivered: specs/3300-selective-insight-definitions/evidence.md)
  - **Dependencies**: T018 and the original request's explicit local commit authorization.
  - Verify the reserved diff, preserved artifacts, unchanged branch, and unchanged source base.
  - Include only the three reserved sources, two reserved tests, release note, and feature-owned artifacts in the local manifest.
  - Exclude temporary output, credentials, shared state, and unrelated files.
  - If authorization or required validation is incomplete, provide an uncommitted local handoff and leave this task unchecked.
  - If separately authorized and all blocking checks pass, stage only explicit manifest paths.
  - Use a local Conventional Commit, such as `fix(insights): refresh only insight definitions`.
  - Include `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
  - Repeat the configured changed-test ratchet against the agreed local source base after the local commit.
  - Retain both CI `--full-gate-path` arguments and confirm both reserved test files enter the measured scope.
  - Record the local revision, focused results, coverage, timing table, gate results, capability limits, and remaining blockers.
  - Restate that the exact parent release remains absent.
  - Stop locally. Do not fetch, rebase, push, open a pull request, or start publication.
  - **Completion**: The authorized local commit and handoff exist without publication.
  - The final handoff records the exact commit SHA, clean status, and post-commit ratchet outside the self-referential commit artifact.

## Verification commands and scope

These commands describe later validation, not work performed during tasks generation.
The examples can disable bytecode writes and the pytest cache provider.
Those options do not change acceptance behavior.
Keep acceptance outputs and cache fixtures under pytest `tmp_path`.
Use the current session artifact directory for coverage metadata and gate reports.
The evidence records the exact commands and report paths that ran.
Do not use a report directory as an application output directory.

## Authorized publication continuation

The parent granted sole position 17 on exact main `77699c7483c1e90df14f9650ed90e98e512bee97`.
This grant supersedes the earlier local-only hold for this continuation.
The [publication evidence](publication.md) records the exact current-base commands and results.
Historical preparation records remain intact.

- [x] T020 Rebase only this clean branch onto the exact authorized base and repeat native current-base local proof. (delivered: specs/3300-selective-insight-definitions/publication.md)
  - Recheck authenticated claim, complete open PR file lists, and strict protection.
  - Repeat four actual caller red and green decisions, code-object execution, 40 controlled durations, cache and fault paths, and full export.
  - Measure all changed statements, branches, and 27 changed methods.
  - Run current configured gates and the six-input, three-guide preflight.
  - Preserve all protected source and policy inputs.
- [ ] T021 Commit the bounded publication record, prove the clean committed ratchet, push once, and create the current full-template PR.
  - **Dependencies**: T020.
  - Preserve all 23 template items, exact commands, results, and conditional capability limits.
  - Post the single-owner protocol in PR comments.
- [ ] T022 Verify fresh exact-head quality, final title, applicable STE, CodeQL analysis, separate required CodeQL, and all 15 strict contexts.
  - **Dependencies**: T021.
  - Preserve application bindings, the authorized current base, and the complete checked source.
  - Stop on unrelated main advance or substantive scope conflict.
- [ ] T023 Perform protected full-head-match squash without administrator bypass, automatic merge, or a branch-deletion flag.
  - **Dependencies**: T022.
  - Verify actual-main parent and complete tree against the authorized base and checked source.
- [ ] T024 Prove exact actual main locally, persist the PR receipt, perform named cleanup, and send the full SHA, tree, and proof URL.
  - **Dependencies**: T023.
  - Use only this own worktree and own environment.
  - Never edit the main checkout or push after squash.
  - Pause after the receipt. The parent alone releases the next issue.

### Red caller and timing selectors

```bash
.venv/bin/python -B -m pytest tests/unit/export/test_selective_insight_definitions.py \
  -k actual_stale_caller_refresh_is_selective -q -s --no-cov --timeout=120 -p no:cacheprovider

ISSUE_3300_BENCHMARK_PHASE=before .venv/bin/python -B -m pytest \
  tests/unit/export/test_selective_insight_definitions.py \
  -k controlled_refresh_benchmark -q -s --no-cov --timeout=120 -p no:cacheprovider

ISSUE_3300_BENCHMARK_PHASE=after .venv/bin/python -B -m pytest \
  tests/unit/export/test_selective_insight_definitions.py \
  -k controlled_refresh_benchmark -q -s --no-cov --timeout=120 -p no:cacheprovider
```

### Focused baseline and green scope

For the unchanged baseline in T003, omit only the new selective test file.
For T017, run all nine paths:

```bash
.venv/bin/python -B -m pytest \
  tests/unit/export/test_selective_insight_definitions.py \
  tests/unit/export/test_const_definitions_exporter.py \
  tests/unit/analytics/test_insight_metrics_utils.py \
  tests/unit/serial_cc/test_site_client_insights.py \
  tests/unit/export/test_org_export_utils.py \
  tests/unit/export/test_site_insights_exporter.py \
  tests/unit/export/site_insights/test_site_insight_path.py \
  tests/unit/serial_cc/test_site_client_insight_path.py \
  tests/integration/serial_cc/test_site_client_insights_integration.py \
  -q --no-cov --timeout=120 -p no:cacheprovider
```

Repeat that scope with these options instead of `--no-cov`:

```text
--cov=src.export.const_definitions_exporter
--cov=src.analytics.insight_metrics_utils
--cov=src.refactors.serial_cc.site_client_insights
--cov-branch
--cov-report=term-missing
--cov-report=json:"$test_output_root/coverage.json"
```

Set `COVERAGE_FILE` within the same temporary test-output boundary.
Do not lower `pyproject.toml` coverage settings or present focused coverage as repository-wide coverage.

### Configured static, security, and dependency gates

Read the current `MYPY_PATHS` from `.github/workflows/ci.yml` before execution.
The required scope at the source base is:

```bash
RUFF_CACHE_DIR="$validation_root/ruff" .venv/bin/python -B -m ruff check .
BLACK_CACHE_DIR="$validation_root/black" .venv/bin/python -B -m black --check --diff .
MYPY_CACHE_DIR="$validation_root/mypy" .venv/bin/python -B -m mypy \
  src/ MistHelper.py wsgi.py \
  scripts/mist_ideas_analyzer_pkg/__init__.py \
  scripts/mist_ideas_distiller_v2_pkg/__init__.py \
  --config-file pyproject.toml
.venv/bin/python -B -m bandit -c pyproject.toml -r .
.venv/bin/python -B -m pip_audit -r requirements.txt
```

The audit covers runtime requirements and uses no ignored advisories.
Do not send source code, credentials, or production data to an external service.

### Quality ratchet, citations, links, and STE

Before a local commit, include the untracked selective tests in the static ratchet:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/test-quality-analyzer --gate \
  --roots tests/unit/export tests/unit/analytics \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --report "$validation_root/test-quality/report.json" \
  --summary "$validation_root/test-quality/summary.md"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/check-citations src tests
PYTHONDONTWRITEBYTECODE=1 .venv/bin/markdown-link-check \
  --root . specs/3300-selective-insight-definitions/ changelog.d/issue-3300-selective-insight-definitions.md
```

Confirm the ratchet's actual measured scope includes both reserved test files.
After the separately authorized local commit, use the configured changed-test arguments:

```text
--changed-from ff3cc1bea8ab58026210a968ff1465f61c9fec78
--full-gate-path .github/workflows/ci.yml
--full-gate-path requirements-dev.txt
--config .github/test-quality-config.toml
--baseline .github/test-quality-baseline.json
```

Run `.venv/bin/ste-linter` with `--config .ste-linter.toml --min-score 80`.
Include `--grade-logging-strings --grade-user-facing-strings` for the three changed sources.
Grade new test prose, tasks, evidence, and the reserved release note.
Review the relevant links and local anchors, including untracked feature files.
Keep the issue, related work, and authenticated scope claim in the evidence.
Report structural STE separately from unavailable dictionary checks.
Do not claim a controlled vocabulary result without the configured dictionary.

## Dependencies and execution order

### Task graph

```text
T001 -> T002 -> T003 -> T004
                         |
                         +-> T005 --+
                         +-> T006 --+-> T007 -> T008
                                                  |
                                                  +-> T009 --+
                                                  +-> T010 --+-> T011
T011 -> T012 -> T013 -> T014 -> T015 -> T016 -> T017 -> T018 -> T019
```

T019 also requires separate local commit authorization and resolution of blocking analysis findings.
No authorization for publication appears in this graph.

### Story completion order

| Story | Implementation prerequisites | Completion task | Independent acceptance |
| --- | --- | --- | --- |
| US1, P1 | T001-T004 evidence, then T005-T010 | T011 | Four callers select one definition and preserve outputs. |
| US2, P1 | Shared implementation through T011 | T012 | Fresh, boundary, stale, missing, timestamp, and second-run cases pass. |
| US3, P1 | Shared failure repair in T008 and caller wiring through T011 | T013 | First error and status survive failures without false success. |
| US4, P2 | Shared exporter repair in T007-T008 | T014 | Full discovery retains 28 definitions and parameter handling. |

T012 through T014 run in order because they edit the same reserved test file and shared evidence.
Their acceptance scenarios remain independently runnable.
No production edits may occur before T004.
No source edit may overlap a timing phase.
T017 follows the release note so gates inspect the final reserved content.

## Parallel examples per user story

| Story | Safe example | Boundary |
| --- | --- | --- |
| US1 | After T004, perform T005 and T006 in separate test files. After T008, perform T009 and T010 in separate sources. | Join both branches before the dependent task. Do not edit evidence concurrently. |
| US2 | After the cache tests are complete, run site and device cache cases in separate pytest invocations. | Use distinct `tmp_path` fixtures and frozen test content. |
| US3 | After the failure tests are complete, run HTTP cases and writer cases in separate pytest invocations. | Use independent sessions, result observations, and temporary files. |
| US4 | After the full-export tests are complete, run fresh and stale full-export cases in separate pytest invocations. | Retain real SDK discovery and separate temporary cache sets. |

These are scheduling examples, not permission to use another agent.
Keep benchmark phases serial and preserve every trial.
Combine independent stdout results in one later evidence edit.
Do not install a parallel test runner for these examples.

## Implementation strategy

1. Complete the scope check and offline harness.
2. Record all four red callers and all 20 before durations.
3. Add the selected contract tests and focused helper assertions.
4. Implement the exporter result and truthful shared fetch/write path.
5. Change the helper and the client wiring.
6. Validate the US1 behavioral MVP.
7. Prove cache, failure, and full-export compatibility in their story phases.
8. Record the matching after phase and every required reduction.
9. Prepare the release note and run the configured local gates.
10. Perform current artifact analysis and prepare the gated local handoff.

Do not treat US1 alone as release-ready.
US2, US3, US4, timing, gates, and analysis remain required for this repair.
Do not implement a new cache policy, framework, schema, retry system, or output backend.
Do not claim completion from an existing file, a fallback write, or skipped validation.

## Requirement coverage

| Requirements | Tasks |
| --- | --- |
| FR-001, FR-002, FR-012, SC-001 | T002-T005, T007, T009-T012, T015 |
| FR-003, SC-002 | T007-T008, T012 |
| FR-004, FR-008 | T005-T011, T013 |
| FR-005, SC-005 | T008, T014 |
| FR-006, FR-007, SC-004 | T002, T006, T011, T014 |
| FR-009, FR-010, SC-006 | T005, T007-T009, T013 |
| FR-011, SC-007 | T007-T009, T013, T017 |
| FR-013 | T001-T004, T011-T015, T017 |
| SC-003 | T004, T015 |

## Settled precedence decisions and tool limits

The current instructions require comments only for non-obvious intent.
This decision supersedes the constitution's per-line comment rule for this task.
The plan and implementation use the current decision.

The original request explicitly authorizes the local commit after validation.
No additional local commit approval is required.
The parent controls the later publication pipeline.
The current request prohibits publication until the parent releases this queue position.
The plan records structural exceptions for the existing exporter and reserved test path.
Current analysis accepts these bounded task-specific decisions.
An unresolved critical implementation finding would still block the local commit.

The required tasks setup attempt failed with exit code 127 because `pwsh` is absent.
No setup JSON came from that script.
The explicit feature path and core tasks template supplied the read-only generation context.
No substitute shared-state writer ran.
The configured companion command has no installed implementation.
Do not create replacement companion state.

The configured dictionary and PowerShell capabilities remain unavailable.
A structural STE result does not certify dictionary validation.
The focused 321-pass baseline is supplied history until T003 records its own execution.
No test, timing trial, production edit, local code gate, analysis workflow, or commit ran during tasks generation.

## Task summary

| Scope | Count |
| --- | --- |
| Setup | 1 |
| Foundational evidence | 3 |
| US1 | 7 |
| US2 | 1 |
| US3 | 1 |
| US4 | 1 |
| Polish and local handoff | 5 |
| **Total** | **19** |

Four tasks have `[P]` markers.
They form two independent edit pairs within US1.
US2 through US4 also have isolated, read-only verification opportunities.

## References

- [Issue #3300](https://github.com/jmorrison-juniper/MistHelper/issues/3300).
- [Related issue #3266](https://github.com/jmorrison-juniper/MistHelper/issues/3266).
- [Authenticated scope claim](https://github.com/jmorrison-juniper/MistHelper/issues/3300#issuecomment-5936871419).
- [Publication predecessor #3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335).
- [Requirements checklist](checklists/requirements.md).
- [Current CI configuration](../../.github/workflows/ci.yml) and [project configuration](../../pyproject.toml).
- [Current analysis procedure](../../.github/agents/speckit.analyze.agent.md).
- [Project constitution](../../.specify/memory/constitution.md).
- [STE writing guide](../../documentation/ASD-STE100_writing-guide.md).
