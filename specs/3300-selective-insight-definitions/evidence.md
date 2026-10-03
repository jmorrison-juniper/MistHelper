# Evidence: Selective Insight Definitions

The [publication evidence](publication.md) records the later sole publication grant and exact current-base proof.
This document retains the earlier local-only preparation record.
The publication record also retains the later authorized six-page generator repair and additional checked-push condition.

## Scope and environment

Issue [#3300](https://github.com/jmorrison-juniper/MistHelper/issues/3300) owns this repair.
The [claim](https://github.com/jmorrison-juniper/MistHelper/issues/3300#issuecomment-5936871419) records the authenticated account and exact file reservation.
The account is `jmorrison-juniper`.
The app session is `97654420-27aa-4469-b541-949a2e1d042d`.
The branch is `jmorrison-juniper-selective-insight-definitions`.
The source base is `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
The initial worktree was clean.

The live issue had zero assignees and zero comments before the claim.
It did not have the `in-progress` label.
The claim added `jmorrison-juniper`, `bug`, `src`, `tests`, and `in-progress`.
Exact paginated file lists from all 11 open pull requests showed no reservation overlap.
The open pull requests were 3670, 3633, 3632, 3630, 3629, 3628, 3627, 3626, 3625, 3624, and 3621.

The permitted source files are:

- `src/operations/exporting/export/const_definitions_exporter.py`.
- `src/mist/intelligence/analytics/insight_metrics_utils.py`.
- `src/foundation/support/refactors/serial_cc/site_client_insights.py`.

The permitted test files are:

- `tests/unit/export/test_selective_insight_definitions.py`.
- `tests/unit/analytics/test_insight_metrics_utils.py`.

Feature artifacts stay under `specs/3300-selective-insight-definitions/`.
The release note is `changelog.d/issue-3300-selective-insight-definitions.md`.
No other source, metadata, menu, dependency, schema, baseline, suppression, or shared state change is authorized.
The site, device, and organization callers already use the shared insight helper.
Their source files need no change.

The default-main worktree has its own Python `3.13.13` environment and `mistapi 0.64.0`.
The first `.venv/bin/python -m pytest --version` attempt failed because the environment did not exist.
The following commands restored the missing environment with unchanged manifests:

```text
rtk proxy env UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 UV_LINK_MODE=copy uv venv --python 3.13 --seed --link-mode copy .venv
rtk proxy .venv/bin/python scripts/bootstrap_worktree.py
```

Both commands passed.
The bootstrap installed the current runtime and development manifests.
Its health check read 160 install records and found zero corrupt installs.
It confirmed the authenticated GitHub account.

`pwsh`, `powershell`, `hunspell`, `aspell`, and `data/ste_dictionary.json` are absent.
PowerShell workflow helpers and dictionary grading are unavailable, not passed.
The explicit feature path replaces shared SpecKit selection state.
Comments explain only non-obvious intent under the current instructions.
The named exporter returns a structured attempt result.
Existing caller and full-export public returns remain unchanged.

## Existing focused baseline

This exact command passed 321 tests in 1.71 seconds:

```text
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_const_definitions_exporter.py tests/unit/analytics/test_insight_metrics_utils.py tests/unit/serial_cc/test_site_client_insights.py tests/unit/export/test_org_export_utils.py tests/unit/export/test_site_insights_exporter.py tests/unit/export/site_insights/test_site_insight_path.py tests/unit/serial_cc/test_site_client_insight_path.py tests/integration/serial_cc/test_site_client_insights_integration.py -q --no-cov --timeout=120
```

The checkout trail guard checked one trail.
The trail held zero lines before and after the run.
No live Mist request, database access, or container operation ran.

## Red proof through every actual caller

The following command ran before any production source edit:

```text
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_selective_insight_definitions.py -k actual_stale_caller_refresh_is_selective -q -s --no-cov --timeout=120
```

It produced four expected behavior failures in 0.35 seconds.
Each failure identified 31 requests instead of the one required insight request.
There were no collection or environment failures.

| Actual caller | Requests | Definition write attempts | Definition cache files checked | Result |
| --- | ---: | ---: | ---: | --- |
| `SiteMetricOperation._refresh_const_metrics` | 31 | 28 | 28 | Failed the selective-request assertion. |
| `SiteClientInsightsService._print_intro_and_refresh` | 31 | 28 | 28 | Failed the selective-request assertion. |
| `DeviceMetricOperation._refresh_const_metrics` | 31 | 28 | 28 | Failed the selective-request assertion. |
| `OrgExportUtils._insight_setup_or_empty` | 31 | 28 | 28 | Failed the selective-request assertion. |

The harness retained the real callers, shared helper, exporter, SDK discovery, cache rule, normalizer, scope reader, and CSV serializer.
It replaced only request responses, database-capable output selection, the cache clock, and necessary runtime dependencies.
All output files used pytest `tmp_path`.
The measured cache age was 86,401 seconds.

## Controlled offline before measurements

These measurements do not reproduce or replace the issue's original live 67.3-second observation.
No live speed claim applies.

The host was macOS on Apple Silicon with Python `3.13.13` and `mistapi 0.64.0`.
The fixture was `sdk-0.64.0-one-country-one-gateway`.
Each offline SDK request performed a real `time.sleep(0.05)`.
The cache clock was fixed at `1800000000.0`.
The elapsed clock was the unchanged `time.perf_counter_ns`.
Each trial used the same definition data and 86,401-second-old cache fixtures.
Each phase included one excluded warm-up for each caller.
Timing included each actual refresh entry.
Organization timing included its existing scope read.
Fixture creation, snapshots, interactive prompts, and later metric collection were excluded.

```text
rtk proxy env ISSUE_3300_BENCHMARK_PHASE=before .venv/bin/python -m pytest tests/unit/export/test_selective_insight_definitions.py -k controlled_refresh_benchmark -q --no-cov --timeout=120
```

The command passed four caller benchmarks in 43.80 seconds.
Every measured trial processed 28 definitions and made 31 requests.
Every measured trial attempted and completed 28 definition writes.
Every measured trial checked 28 definition cache files.
The three extra requests came from existing model and country dispatch.

| Caller | Trial 1, seconds | Trial 2, seconds | Trial 3, seconds | Trial 4, seconds | Trial 5, seconds | Before median, seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Site | 1.801976042 | 1.809003500 | 1.796538041 | 1.775953541 | 1.799229208 | 1.799229208 |
| Client | 1.812356208 | 1.786107667 | 1.796314792 | 1.798184875 | 1.795540917 | 1.796314792 |
| Device | 1.824558125 | 1.813444667 | 1.786623791 | 1.786930666 | 1.765124291 | 1.786930666 |
| Organization | 1.804374000 | 1.820744625 | 1.802741166 | 1.815521417 | 1.824151292 | 1.815521417 |

The before evidence is complete.

## Controlled offline after measurements

```text
rtk proxy env ISSUE_3300_BENCHMARK_PHASE=after .venv/bin/python -m pytest tests/unit/export/test_selective_insight_definitions.py -k controlled_refresh_benchmark -q --no-cov --timeout=120
```

The command passed all four caller benchmarks in 1.92 seconds.
It used the same response fixture, cache clock, cache age, request delay, writer, and elapsed clock.
Every measured trial processed one definition and made one insight request.
Every measured trial attempted and completed one definition write.
Every measured trial checked only `ConstInsightMetrics.csv`.
No trial used a fallback or wrote an insight output file.

| Caller | Trial 1, seconds | Trial 2, seconds | Trial 3, seconds | Trial 4, seconds | Trial 5, seconds | After median, seconds | Median reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Site | 0.061242458 | 0.057255791 | 0.061671583 | 0.056204875 | 0.060681458 | 0.060681458 | 96.627% |
| Client | 0.060830542 | 0.050762166 | 0.060477833 | 0.051007333 | 0.058318542 | 0.058318542 | 96.753% |
| Device | 0.055419375 | 0.061041625 | 0.051100625 | 0.060664292 | 0.060814292 | 0.060664292 | 96.605% |
| Organization | 0.050718791 | 0.060755583 | 0.059146125 | 0.059163584 | 0.060766291 | 0.059163584 | 96.741% |

The benchmark checked five measured trials for each caller and phase.
All four median reductions exceeded the required 90% threshold.
These are controlled offline measurements, not new live measurements.
The original live 67.3-second report remains separate.

## Green behavior and coverage

The final focused run passed 430 tests.
Four opt-in benchmark tests skipped because the phase variable was absent.
Both benchmark phases ran separately and passed all four tests.
The focused run reached 96.20% combined line and branch coverage.
The denominator was 1,084 statements and 284 branches in the three changed source modules.
The configured 90% floor remained unchanged.

```text
rtk proxy env COVERAGE_FILE=/Users/jmorrison/.copilot/session-state/43167b87-e78e-4ecb-80f8-4b1ea622d466/files/coverage-3300 .venv/bin/python -m pytest tests/unit/export/test_selective_insight_definitions.py tests/unit/export/test_const_definitions_exporter.py tests/unit/analytics/test_insight_metrics_utils.py tests/unit/serial_cc/test_site_client_insights.py tests/unit/export/test_org_export_utils.py tests/unit/export/test_site_insights_exporter.py tests/unit/export/site_insights/test_site_insight_path.py tests/unit/serial_cc/test_site_client_insight_path.py tests/integration/serial_cc/test_site_client_insights_integration.py -q -rs --cov=src.operations.exporting.export.const_definitions_exporter --cov=src.mist.intelligence.analytics.insight_metrics_utils --cov=src.foundation.support.refactors.serial_cc.site_client_insights --cov-branch --cov-report=term-missing --cov-report=json:/Users/jmorrison/.copilot/session-state/43167b87-e78e-4ecb-80f8-4b1ea622d466/files/coverage-3300.json --cov-fail-under=90 --timeout=120 --tb=short
```

This command passed in 9.89 seconds.
The checkout trail guard checked one trail and found zero lines before and after the run.
No full unrelated test suite ran.

The proofs cover all four real callers with fresh, exact-boundary, expired, missing, mixed-age, future-time, and second-run caches.
They guard definition reads, existence checks, timestamps, and writes.
Unrelated file contents and timestamps remain unchanged.
The real CSV serializer preserves sorted fields, normalized values, row order, and ordered scope results.
The separate full export retains all 28 definitions, 31 controlled requests, and all three special paths.
It continues after an insight definition failure.

Failure proofs cover HTTP 404 and 503 with bodies and empty bodies.
They also cover transport faults, missing HTTP status, proxy errors, discovery faults, malformed rows, and false or failing writers.
The SDK `raw_data` and requests `text` error bodies retain the first safe reason.
Secondary output failures do not replace the first error or increment failure counts again.
Repeated attempts keep independent, read-only counter snapshots.
Synthetic headers, credential URLs, and token values do not appear in messages or formatted tracebacks.
No stale file can produce a refresh success notice after failure.

### Changed-method coverage

An AST comparison against the source base identified 27 changed methods.
The coverage check found zero missed changed-method lines or branches.
These values do not claim complete coverage of unchanged client-service methods.

| Source owner | Changed method | Lines | Branches |
| --- | --- | ---: | ---: |
| Exporter | `export_endpoint` | 11/11 | 6/6 |
| Exporter | `_is_valid_endpoint_name` | 2/2 | 0/0 |
| Exporter | `_discover_selected_endpoint` | 11/11 | 4/4 |
| Exporter | `_snapshot_counts` | 2/2 | 0/0 |
| Exporter | `_refresh_result` | 7/7 | 0/0 |
| Exporter | `_error_http_status` | 4/4 | 0/0 |
| Exporter | `_safe_error_text` | 8/8 | 0/0 |
| Exporter | `_report_failure` | 5/5 | 0/0 |
| Exporter | `export_all` | 14/14 | 2/2 |
| Exporter | `_inspect_module` | 14/14 | 2/2 |
| Exporter | `_process_single_endpoint` | 17/17 | 2/2 |
| Exporter | `_is_file_fresh` | 18/18 | 2/2 |
| Exporter | `_fetch_and_export_endpoint` | 14/14 | 0/0 |
| Exporter | `_write_empty_fallback` | 10/10 | 2/2 |
| Exporter | `_fetch_standard_endpoint` | 15/15 | 6/6 |
| Exporter | `_response_error_text` | 10/10 | 6/6 |
| Exporter | `_fetch_one_gateway_model` | 11/11 | 2/2 |
| Exporter | `_get_gateway_models_list` | 14/14 | 2/2 |
| Exporter | `_fetch_all_country_states` | 20/20 | 4/4 |
| Exporter | `_call_countries_api` | 9/9 | 0/0 |
| Exporter | `_fetch_all_country_channels` | 20/20 | 4/4 |
| Exporter | `_get_channel_country_codes` | 15/15 | 2/2 |
| Exporter | `_export_data` | 13/13 | 2/2 |
| Exporter | `_report_export_success` | 7/7 | 2/2 |
| Insight helper | `export_const_insight_metrics` | 17/17 | 4/4 |
| Client service | `_resolve_runtime_dependencies` | 3/3 | 0/0 |
| Client service | `_print_intro_and_refresh` | 6/6 | 0/0 |

## Local quality results

| Check | Exact command | Result |
| --- | --- | --- |
| Syntax | `rtk proxy .venv/bin/python -m py_compile MistHelper.py src/operations/exporting/export/const_definitions_exporter.py src/mist/intelligence/analytics/insight_metrics_utils.py src/foundation/support/refactors/serial_cc/site_client_insights.py tests/unit/export/test_selective_insight_definitions.py tests/unit/analytics/test_insight_metrics_utils.py` | Passed for six files. |
| Full Ruff | `rtk proxy .venv/bin/python -m ruff check --no-cache .` | Passed with zero findings. |
| Full Black | `rtk proxy .venv/bin/python -m black --check --diff --no-cache .` | Passed. All 2,001 files remained unchanged. |
| Exact CI mypy | `rtk proxy .venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml --cache-dir /Users/jmorrison/.copilot/session-state/43167b87-e78e-4ecb-80f8-4b1ea622d466/files/mypy-3300` | Passed for 663 source files. Existing untyped-body notes remain. |
| Configured Bandit | `rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r .` | Passed. It checked 214,133 code lines and found zero issues. |
| Bandit excludes | `rtk proxy .venv/bin/bandit-exclude-check` | Passed without exclusion changes. |
| Exact CI complexity | `rtk proxy .venv/bin/python -m radon cc src/ MistHelper.py wsgi.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py -j \| rtk proxy .venv/bin/complexity-gate --max 10` | Passed. Every measured function remained at or below 10. |
| New-test complexity | `rtk proxy .venv/bin/python -m radon cc tests/unit/export/test_selective_insight_definitions.py -j \| rtk proxy .venv/bin/complexity-gate --max 10` | Passed without suppressions. |
| Changed-owner Pylint | `rtk proxy .venv/bin/python -m pylint src/operations/exporting/export/const_definitions_exporter.py src/mist/intelligence/analytics/insight_metrics_utils.py src/foundation/support/refactors/serial_cc/site_client_insights.py --fail-under=9.5 --score=y` | Passed at 9.79/10. Reported style warnings remain visible. |
| Citations | `rtk proxy .venv/bin/check-citations src tests` | Passed. It checked 251 citations and found zero unresolved references. |
| Whitespace | `rtk proxy git diff --check` | Passed with zero findings. |

The unchanged quality ratchet passed with zero new findings:

```text
rtk proxy .venv/bin/test-quality-analyzer --gate --roots tests/unit/export tests/unit/analytics --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --report /Users/jmorrison/.copilot/session-state/43167b87-e78e-4ecb-80f8-4b1ea622d466/files/test-quality-3300.json --summary /Users/jmorrison/.copilot/session-state/43167b87-e78e-4ecb-80f8-4b1ea622d466/files/test-quality-3300.md --log-level WARNING
```

It checked 54 files and 88 existing findings.
Its analyzed scope included both reserved test files.
It reported zero parse errors.
The baseline, rules, and exclusions remain unchanged.
The first run reported one missing HTTP 4xx proof.
A direct HTTP 404 result test corrected that finding without a suppression.

### Related guard contracts

```text
rtk proxy .venv/bin/python -m pytest tests/integration/test_mistapi_sdk_compatibility.py tests/unit/web_portal/test_output_scan_runtime_files.py tests/guardrails/test_changelog_fragment_policy.py -q -rs --no-cov --timeout=120 --tb=short
```

The command passed 52 tests in 5.30 seconds.
One changelog diff test skipped because no pull request event exists.
That event-only check is unavailable locally, not passed.
The SDK guard checked 548 signatures and found zero known signature failures.
It also reported 10 unresolved call sites and 366 unverifiable signatures.
Those existing limits remain explicit.
All eight SDK tests ran.

### Writing and capability limits

The local link check passed after explicit staging made the feature documents visible to the tracked-file scanner:

```text
rtk proxy .venv/bin/markdown-link-check --root . specs/3300-selective-insight-definitions changelog.d/issue-3300-selective-insight-definitions.md
```

It checked 10 Markdown files and found zero broken links.
No untracked-file skip supplied that result.

The configured structural STE check read all three changed source files and the release note.
Their scores were 99, 99, 98, and 92.
The final feature document and release-note scores ranged from 92 to 98.
All scores exceeded 80.
Dictionary grading skipped because the configured dictionary is absent.
PowerShell workflow initialization and companion hooks remain unavailable.
The five required core SpecKit steps use this explicit feature directory.
No shared selection or companion state changed.

## Additional red contracts

The following command also ran before any production source edit:

```text
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_selective_insight_definitions.py tests/unit/analytics/test_insight_metrics_utils.py -k 'export_endpoint_selection or invalid_selection or import_failure or same_exporter or writer_failure or refresh_failure or refresh_success or delegates_and_reports' -q --no-cov --timeout=120 --tb=short
```

It produced 15 expected failures and two passes in 0.47 seconds.
Thirteen failures identified the missing selected exporter entry.
The existing helper did not call the selected entry.
The existing helper also reported an available stale CSV after a failed refresh.
The two existing availability behaviors passed.
These contracts supplement the four actual stale caller failures.
They do not replace those caller proofs.

## Runtime dependency audit

The initial runtime audit failed before package assessment:

```text
rtk proxy .venv/bin/python -m pip_audit -r requirements.txt --progress-spinner off --strict
```

Its temporary resolver process aborted during `ensurepip` with `SIGABRT`.
This environmental failure was not an advisory result or a passed audit.
The authorized alternative used the same runtime manifest and this worktree's interpreter:

```text
rtk proxy env UV_SYSTEM_CERTS=1 UV_NATIVE_TLS=1 UV_LINK_MODE=copy uv pip compile requirements.txt --python .venv/bin/python --generate-hashes --output-file data/issue-3300/runtime-audit-lock.txt --quiet
rtk proxy .venv/bin/python -m pip_audit --no-deps --disable-pip --require-hashes --strict --progress-spinner off -r data/issue-3300/runtime-audit-lock.txt
```

Both alternative commands passed.
The strict audit found no known vulnerabilities.
The lock contains 105 resolved runtime package pins with hashes.
No advisory was ignored.
The Git-only development package `misthelper-devtools` remains outside this runtime audit.
The lock is an ignored validation artifact, not a dependency-manifest change.

## Output contract correction

The real CSV writer sorts the eight column names.
The specification originally confused normalizer insertion order with CSV column order.
The corrected CSV header is:

```text
description,intervals,metric_name,report_intervals,report_scopes,scopes,type,unit
```

The repair preserves this existing order.
The repair also preserves normalized values, multiline escaping, row order, and ordered scope results.
The real writer does not create a file for empty data.
An empty fallback attempt can leave an old file present.
Failure reporting must not infer success from that old file.

## Publication hold

Queue position 17 follows [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335).
The parent did not authorize publication.
This repair will stop after its verified local commit and handoff.
No push, pull request, merge, deployment, or workflow run is authorized.
The original request explicitly authorizes the local commit.
No additional local commit approval is required.
The local source base remains `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
The shared cached `origin/main` reference moved during other work.
That observation does not authorize a fetch, rebase, or publication.

## Current SpecKit analysis

The required `speckit.analyze` step read the nine feature artifacts and the constitution.
It used the explicit feature directory without shared state or PowerShell initialization.
It did not inspect source again, repeat tests, or change files.
The analysis mapped all 13 functional requirements and seven success criteria to completed tasks and persisted evidence.
It found no critical issue, missing requirement, unmapped task, or dependency contradiction.

The analysis identified four medium artifact findings.
The corrections below resolve them without source or behavioral changes.

| ID | Finding | Correction | State |
| --- | --- | --- | --- |
| I1 | Research confused normalizer insertion order with CSV column order. | Research now requires normalizer order and sorted CSV columns. | Resolved. |
| I2 | Tasks described settled comment and commit decisions as unresolved conflicts. | Tasks now state the current comment rule, existing local commit approval, and parent publication hold. | Resolved. |
| U1 | Empty-output wording suggested creation of empty CSV files. | The contract and data model now describe empty write attempts and unchanged existing files. | Resolved. |
| I3 | Tasks required pytest report locations that did not match actual gate metadata locations. | Tasks now separate `tmp_path` acceptance output from session reports and the authorized audit lock. | Resolved. |

The analysis reported 100% task coverage for 20 requirements and 13 acceptance scenarios across four user stories.
It reported 19 tasks with 17 complete at analysis time.
This persisted report completes T018.
The authorized local commit and final handoff remain T019.

| Requirement | Completed task mapping | Recorded proof |
| --- | --- | --- |
| FR-001 | T002-T005, T007, T009-T011, T015 | Four actual caller red and green results. |
| FR-002 | T002, T005, T007, T011-T012, T015 | Guarded reads, timestamps, requests, writes, and unchanged unrelated snapshots. |
| FR-003 | T007-T008, T012 | Boundary, missing, expired, future-time, and second-run cache cases. |
| FR-004 | T005-T011 | Existing shared discovery, cache, normalization, and helper paths. |
| FR-005 | T008, T014 | Full 28-definition export and three special paths. |
| FR-006 | T002, T006, T011, T014 | Exact CSV bytes, fields, normalized values, and intervals. |
| FR-007 | T002, T006, T011 | Ordered scope lists and retained exclusions. |
| FR-008 | T006, T009-T011, T013 | Caller returns, resolver removal, and existing empty-output attempts. |
| FR-009 | T005, T007-T009, T013 | Original status, first error, raw error bodies, and secondary failures. |
| FR-010 | T005, T007-T008, T013 | Independent immutable counts and one failure without false updates. |
| FR-011 | T007-T009, T013, T017 | ASCII logs, status, counts, safe messages, and safe tracebacks. |
| FR-012 | T005, T007, T013 | Invalid and unavailable selections with zero I/O. |
| FR-013 | T001-T004, T011-T015, T017 | Offline session, temporary CSV output, and no production services. |
| SC-001 | T002-T005, T007, T009-T011, T015 | One request and write instead of 31 requests and 28 writes. |
| SC-002 | T007-T008, T012 | Complete four-caller cache matrix. |
| SC-003 | T004, T015 | Forty measured durations and four reductions above 90%. |
| SC-004 | T002, T006, T011, T014 | Compatible fields, values, scopes, and caller output behavior. |
| SC-005 | T008, T014 | Complete dynamic full-export coverage. |
| SC-006 | T005, T007-T009, T013 | Failed results retain evidence and record zero successful updates. |
| SC-007 | T007-T009, T013, T017 | Distinct cache, update, and failure reports without synthetic secrets. |

## Local commit manifest and handoff

The local commit contains exactly 15 reserved files:

```text
changelog.d/issue-3300-selective-insight-definitions.md
specs/3300-selective-insight-definitions/checklists/requirements.md
specs/3300-selective-insight-definitions/contracts/definition-refresh.md
specs/3300-selective-insight-definitions/data-model.md
specs/3300-selective-insight-definitions/evidence.md
specs/3300-selective-insight-definitions/plan.md
specs/3300-selective-insight-definitions/quickstart.md
specs/3300-selective-insight-definitions/research.md
specs/3300-selective-insight-definitions/spec.md
specs/3300-selective-insight-definitions/tasks.md
src/mist/intelligence/analytics/insight_metrics_utils.py
src/operations/exporting/export/const_definitions_exporter.py
src/foundation/support/refactors/serial_cc/site_client_insights.py
tests/unit/analytics/test_insight_metrics_utils.py
tests/unit/export/test_selective_insight_definitions.py
```

A byte comparison checked 15 protected tracked files against the source base.
It found zero changes.
The existing shared `.specify/feature.json` remains byte-identical.
Only the reserved sources, tests, release note, and feature artifacts enter the commit.
Ignored tool caches, runtime audit files, credentials, and temporary test outputs do not enter it.

The commit uses `fix(insights): refresh only the insight definition`.
It includes `Closes #3300` and the required Copilot App co-author trailer.
The final handoff records the exact local SHA and clean worktree result outside this self-referential commit artifact.
It also records the post-commit changed-test ratchet against the unchanged source base.
The parent receives the complete command results and file manifest.
No push, pull request, merge, or workflow run occurs.
The parent must explicitly release publication after queue predecessor #3335.
