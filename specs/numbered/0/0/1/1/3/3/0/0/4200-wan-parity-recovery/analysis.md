# Recovery coverage and execution status

## Latest independent destination implementation

T052-T053 add independently defined cached-site navigation and retained UTC observation views.
The task ledger now has 30 completed tasks of 53.
The original 47-task audit still has 24 completed tasks and 23 acceptance tasks open.
These controls do not establish source parity or close issue #4200.

Site choices come only from the selected organization's validated cache.
Exact site routes reject absent identifiers and preserve case-sensitive identity and CSV scope.
Navigation preserves the selected window across site, gateway, port, peer, and overview links.
Site pages contain no organization-refresh action.

The `6h`, `12h`, `24h`, and `7d` intervals end at the current UTC hour boundary.
They exclude the current hour and read one exact detail identity, with at most 168 expected hour buckets.
Retained rows remain hourly projections with collection times, units, missing reasons, and live provenance.
No sample read, interpolation, aggregate calculation, backfill, API request, or storage change occurs.
Missing buckets remain absent. Measurement completeness and elapsed coverage remain unknown even when every bucket exists.
Organization and site aggregate histories remain unavailable because their weighting and completeness contracts are unverified.
Missing stores, failed reads, and successful empty reads have separate visible states.
The current-cache table and CSV export remain explicitly separate from the retained view.

Temporary SQLite cases verify half-open boundaries and missing buckets.
Invalid-history cases reject foreign identities, synthetic provenance, duplicate hours, and out-of-window records.
The browser journey covers all four ranges and site/gateway/port/peer/overview navigation at three viewports.
The mobile assertion reproduced a peer-identity overflow. Text wrapping repairs the defect without changing identifiers.
The complete focused suite reports 447 passed, two existing plugin warnings, and no removed test.
This increment adds 43 cases beyond the preceding 404-case result.

### Site and retained-window validation

Implementation commit: `d519094517ab73f32168fe63a823e3168252a43b`.
The following assertion-only commit strengthens UTC boundaries after the ratchet found three existence-only guards: `960d81c`.
The calendar module then passed all 50 cases. Ruff and Black also passed.
The committed quality ratchet now reports zero findings and zero new findings.
The new tests add 208 browser-module lines and 87 unit-module lines without removing any existing line.
The table module loses no declaration. The route module adds two imports and the `site` route without losing declarations.
The symbol checker returns one for those three intentional additions.
Protected paths remain identical to merge base `2a6a5844698aeb180fea353e0243034890774565`.
No dependency, workflow, baseline, entry point, registry, primary-key map, or feature-pointer change occurred.
No source execution, live Mist call, production write, publication, hosted run, readiness change, or merge occurred.

| Command | Actual result |
| - | - |
| `rtk .venv/bin/python -m pytest -q tests/unit/wan_performance tests/e2e/web_portal/test_wan_performance_offline.py tests/e2e/web_portal/test_wan_performance_live.py tests/integration/test_mistapi_sdk_compatibility.py --tb=short --show-capture=no` | 447 passed, two existing plugin warnings. |
| `rtk .venv/bin/python -m pytest -q tests/e2e/web_portal/test_wan_performance_live.py -k 'cached_site_and_retained' --tb=short --show-capture=no` | Three browser journeys passed after the final assertion formatting change. |
| `rtk .venv/bin/python -m ruff check src/interfaces/wan_performance tests/unit/wan_performance tests/e2e/web_portal/test_wan_performance_live.py` | All checks passed. |
| `rtk .venv/bin/python -m black --check src/interfaces/wan_performance tests/unit/wan_performance/test_calendar_summaries.py tests/e2e/web_portal/test_wan_performance_live.py` | 31 files unchanged. |
| `rtk .venv/bin/python -m mypy src/interfaces/wan_performance --config-file pyproject.toml` | Success, 29 source files. |
| `rtk .venv/bin/python -m compileall -q src/interfaces/wan_performance` | Exit zero, no output. |
| `rtk .venv/bin/bandit -c pyproject.toml -r src/interfaces/wan_performance -q` | Exit zero, no findings. |
| `rtk .venv/bin/radon cc src/interfaces/wan_performance -j \| rtk .venv/bin/complexity-gate --max 10` | All functions within the threshold. |
| `rtk .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | One passed, four input reads and validations. |
| `rtk .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | 15 files checked, zero findings, two skipped, zero parse errors, zero new findings. |
| `rtk git diff --check` | Exit zero. |

STE checks passed on all seven changed Markdown records, with scores from 86 through 97.
The Markdown link check examined seven files and found zero broken links.

### Earlier independent SLE, table, and MOS increment

T048-T051 are complete with local proof. At that checkpoint, the ledger had 28 completed tasks of 51.
The original 47-task audit still has 24 completed tasks and 23 acceptance tasks open.
These increments do not close source-parity acceptance or issue #4200.

The retained-MOS regression first reproduced five failures and one passing incompatible-unit guard.
The exception was `ValueError: Calendar summaries cannot mix metric units.`
The final regression stores retained missing unknown-unit and new score hours in temporary SQLite.
It covers either input order and same-day or different-day hours.
Daily, rolling, weekly, and monthly summaries use the documented score unit when present.
The route test confirms the visible score. Old stored records remain unchanged.

The independent SLE view uses existing access controls, CSRF, cached organization membership, the session transport, and shared organization admission.
Navigation starts no API request. A submission reads the enabled catalog and optionally one impacted-gateway page.
The fixed request duration is one hour. Duration units and completeness remain unknown.
No new storage, worker, background request, classifier mapping, or production operation was added.
The actual lease class is exercised with a mocked Redis client, not a live Redis service.

Cached table controls provide identity filtering, lexical sorting, ten-row pagination, and full filtered CSV export.
History selection uses the full route scope before table filtering.
CSV fields retain identity, UTC observation hour, collection time, units, missing reasons, and provenance.
The observation hour is an hourly projection, not a raw metric timestamp.
Text formula prefixes receive an apostrophe.
Browser journeys cover both new interfaces at 1440x1100, 1280x800, and 390x844 without document overflow.

The combined WAN, destination-browser, and SDK suite reports 404 passed, with two existing plugin warnings.
The previous candidate reported 355 passed. This increment adds 49 cases and removes no existing test.
The SDK guard reports 587 checked signatures, 10 unresolved sites, 364 unverifiable signatures, and zero known failures.
Ruff and Black pass. Mypy reports success for 28 source files.
Compilation, Bandit, and the maximum-ten complexity gate pass.
The summary module loses no module-level names.
The route symbol comparison reports three intentional imported names and no lost names.
Its exit code is one because additions count as changes, not because a declaration disappeared.

Source execution and protected screen capture remain prohibited without a verified rights grant.
The original application's full test cycle and interactive exploration remain unperformed for that reason.
Exact source temporal, raw-sample percentile, weighting, retention, capacity, historical completeness, and backfill contracts remain prerequisites.
The SLE endpoint does not supply these facts. Its missing SDK pagination arguments prevent complete large-result traversal.
The independently defined table ordering and CSV format do not establish original ordering or export equivalence.
Protected workflow paths, dependency pins, baseline files, entry points, registry files, and the feature pointer remain unchanged.
No publication, hosted check, readiness change, or merge occurred.

### Committed validation evidence

Implementation commit: `2326357014930504e0c6fb68e741f142dbccb106`.
Its merge base remains `2a6a5844698aeb180fea353e0243034890774565`.
The following commands ran locally. No dependency manifest changed.

| Command | Actual result |
| - | - |
| `rtk .venv/bin/python -m pytest -q tests/unit/wan_performance tests/e2e/web_portal/test_wan_performance_offline.py tests/e2e/web_portal/test_wan_performance_live.py tests/integration/test_mistapi_sdk_compatibility.py` | 404 passed, two existing plugin warnings. |
| `rtk .venv/bin/python -m ruff check src/interfaces/wan_performance tests/unit/wan_performance tests/e2e/web_portal/test_wan_performance_live.py` | All checks passed. |
| `rtk .venv/bin/python -m black --check src/interfaces/wan_performance tests/unit/wan_performance/test_calendar_summaries.py tests/e2e/web_portal/test_wan_performance_live.py` | 30 files unchanged. |
| `rtk .venv/bin/python -m mypy src/interfaces/wan_performance --config-file pyproject.toml` | Success, 28 source files. |
| `rtk .venv/bin/python -m compileall -q src/interfaces/wan_performance` | Exit zero, no output. |
| `rtk .venv/bin/bandit -c pyproject.toml -r src/interfaces/wan_performance -q` | Exit zero, no findings. |
| `rtk .venv/bin/radon cc src/interfaces/wan_performance -j \| rtk .venv/bin/complexity-gate --max 10` | All functions within the threshold. |
| `rtk .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | One passed, four input reads and validations. |
| `rtk .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | 15 files checked, zero findings, two skipped, zero parse errors, zero new findings. |
| `rtk git diff --check` | Exit zero. |

STE checks passed on all seven changed Markdown records, with scores from 84 through 97.
The Markdown link check examined seven files and found zero broken links.
The implementation hooks contain only optional active commit hooks. The companion hooks remain disabled.
The implementation commit preserves all original test names and protected paths.

**Date**: 2026-11-05

This record maps requirements to the new execution sequence.
It is not a completed source comparison or a successful Spec Kit command report.
Historical T001-T087 reconciliation remains T002. No historical task state was changed.

## Skill-guided review and corrections

The local analyze and tasks skills supplied the review and task-refinement rules.
PowerShell was unavailable during the original review. The later session-local prerequisite and analysis results appear below.
The user authorized these document refinements on 2026-11-05.

| ID | Category | Severity | Location | Finding and correction |
| --- | --- | --- | --- | --- |
| D1 | Dependencies | HIGH | tasks.md: foundation and E8 | Split existing safety prerequisites from later refresh-policy verification. T004 now establishes foundation evidence before T005-T006. |
| D2 | Dependencies | HIGH | tasks.md: duration and E7 | Separate interval/window evidence from retention. T015, T027, and T029 establish their respective prerequisites. |
| U1 | Execution detail | MEDIUM | tasks.md: metric and storage tasks | Replace abbreviated module paths with repository-relative paths and require recorded failing assertions before repairs. |
| C1 | Coverage | HIGH | contracts/parity.md: source goals | Add exportable top offenders and the region-to-circuit chain to the seed inventory and audience tasks. |
| I1 | Evidence accuracy | HIGH | research.md: destination behavior | Existing duration and event-availability sections are provisional behavior, not absent features. Verify their assumptions instead of repeating obsolete absence claims. |
| U2 | Comparison scope | HIGH | contracts/parity.md: seed inventory | Add 20 classified seed rows and ten assertion scenarios. These do not replace exhaustive per-control comparison. |

No requirement was removed. No evidence gate was changed to verified.
All 47 tasks remain open. The revised execution rules preserve stable task IDs.
The manual review maps all 24 FR/SC entries. It does not establish source runtime or visual parity.
There are no uncovered FR/SC entries in this document mapping.
Source behavior classification and historical task reconciliation remain incomplete.

## Additional discovery

The [discovery record](design/contracts/discovery.md) identifies 15 source surface groups and their remaining verification work.
It adds active routes, download callbacks, device charts, MOS, port counters, and peer path details.
It separates source 6h/7-day UI controls from the desired 3h reporting goal.

Static inspection corrects P11's earlier TODO-only classification.
Both source history methods have bodies, but their SDK calls do not match the installed destination SDK.
The gateway symbol is absent. The peer filter arguments are unsupported by the inspected device-insight signature.
No live request established sample shape, scope, units, or historical completeness.

The record also documents existing configured-store selection, cache keys, TTLs, admission bounds, and calendar calculations.
These observations are not new approved contracts.
Portal middleware, metric catalogs, scheduling, exports, visual comparison, retention, and backfill still require evidence.
T001-T004 remain open because partial discovery does not satisfy their full objectives.
No product file, task status, PR metadata, or remote branch changed during this discovery.

## Requirement coverage

| Requirement | Tasks | Acceptance evidence |
| --- | --- | --- |
| FR-001 | T001, T003, T007-T010 | Complete pinned source inventory |
| FR-002 | T002-T003, T043 | Completed/TODO/goal/unverified classifications |
| FR-003 | T007-T012, T033-T036 | Four journeys and reviewed visual hierarchy |
| FR-004 | T013-T016, T021-T022 | Capacity and threshold interval calculations |
| FR-005 | T017-T022 | Status, ranking, failure, and availability cases |
| FR-006 | T023-T024 | Timestamped quality sampling and calculations |
| FR-007 | T025-T026 | Verified SLE contracts and impact navigation |
| FR-008 | T013, T027-T028 | Dimensions, weighting, UTC windows, and coverage |
| FR-009 | T029-T030 | Configured-store history and capacity evidence |
| FR-010 | T031-T032 | Approved audience controls and reports |
| FR-011 | T004-T006, T037-T042 | Host authorization, session, storage, and admission tests |
| FR-012 | T042, T045 | No extra service, port, database, or token store |
| FR-013 | T005-T006, T040-T042 | Synthetic isolation assertions |
| FR-014 | T005, T038-T042 | Positive and negative state assertions |
| FR-015 | T033-T036, T041, T043 | Reviewed source-to-test evidence |
| FR-016 | T043-T047 | Exact-revision acceptance and blocked rows |
| SC-001 | T003, T007-T010, T043 | Zero unclassified inventory rows |
| SC-002 | T011-T042, T043 | Required completed behavior and deviations |
| SC-003 | T014-T030, T040 | Values or explicit unavailable states |
| SC-004 | T014-T030 | Independent expected calculations |
| SC-005 | T011, T021, T026, T032, T035, T040-T042 | All four browser journeys |
| SC-006 | T033-T036, T043 | Visual evidence or explicit blocker |
| SC-007 | T005-T006, T037-T042 | Host isolation and service inventory |
| SC-008 | T043-T047 | Owner decision on exact tested revision |

Document coverage: 16 functional requirements and 8 success criteria have task mappings.
This is 24 of 24 mapped requirements, not 100 percent implementation completion.
There are 47 open tasks and five user stories.
US1 has 10 tasks. US2 has 10. US3 has 4. US4 has 6. US5 has 6.
The remaining 11 tasks cover setup, foundation, and final acceptance.

## Remaining acceptance gaps

| Gap | Evidence gate | Execution tasks |
| --- | --- | --- |
| Complete original look, controls, and functionality | E1, E2 | T003, T007-T012, T033-T036 |
| Region/site/circuit hourly aggregation | E3, E7 | T013-T014, T027-T028 |
| Top-N and primary/secondary failure views | E3, E4 | T019-T022 |
| Continuous and cumulative threshold duration | E3, E7 | T015-T016 |
| Historical status, flaps, and availability | E4 | T017-T018 |
| Historical peer mean, maximum, and p95 | E5 | T023-T024 |
| WAN SLE scores and impact drilldowns | E6 | T025-T026 |
| 3h, 12h, 24h, and calendar windows | E3, E7 | T027-T028 |
| 13-month history and backfill | E7 | T029-T030 |
| Executive, engineering, and SLE views | E1, E3, E6 | T031-T032 |
| Shared refresh and optional Redis safety | E8 | T037-T040 |
| Full end-to-end and host regression evidence | All required gates | T041-T047 |

## Historical command status

The first Spec Kit prerequisite command failed with exit 127 because `pwsh` was unavailable:

```text
pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
/bin/bash: pwsh: command not found
```

That attempt stopped before Spec Kit analysis. A verified session-local PowerShell runtime later became available.
The branch hook was loaded but not executed because this app already owns the feature branch.
Optional commit hooks were deferred. No feature pointer or other worktree was changed.
The successful feature-specific prerequisite and consistency results are recorded below.

## Historical local document validation

- STE examined nine files with no skipped files. Scores range from 93 to 97, above the required 80.
- Markdown link validation examined nine indexed Markdown files and found zero broken links.
- A direct format check verified 47 sequential unique open task IDs and 24 requirement coverage rows.
- The same check verified bounded feature and route directories.
- `git diff --cached --check` reported no whitespace errors.
- An initial directory argument to STE read zero files. The corrected explicit file selection examined all nine files.
- An initial link scan before indexing read zero files. Only the subsequent nine-file scan counts as validation.
- No production tests ran for this documentation-only record. The regression commands are future execution instructions, not new results.

The refined record passed another nine-file STE check with scores from 93 to 97 and no skipped files.
The nine-file link scan again found zero broken links.
Direct checks again verified 47 unique sequential open tasks, 24 mapped requirements, and bounded directories.
An isolated task audit examined this feature under a temporary `specs/` root and reported 47 open tasks, exit 0.
The temporary audit copy was removed automatically. No test baseline or feature pointer changed.
`git diff --check` passed after refinement.

The discovery update examined ten Markdown files with no skipped files.
STE scores ranged from 92 to 97.
Direct checks verified 47 sequential open tasks, 24 mapped requirements, and bounded feature directories.
The isolated task audit again reported 47 unchecked tasks and exit 0.
The source tree response was not truncated.
Static callback inspection found three CSV handlers, but did not prove region/site export buttons work.
Offline SDK inspection found the gateway symbol absent and peer filter arguments unsupported.
During that document review, no product tests ran because only documentation had changed.
The final link scan examined ten tracked Markdown files and found zero broken links.
The final STE scan examined ten files, skipped none, and passed with scores from 92 to 97.
`git diff --cached --check` passed.

## Start decision

Proceed with T001-T004 and descriptive comparison.
Do not implement a metric while its dependent gate remains unverified.
Do not accept full visual parity without permissible comparison evidence.
Do not merge or close issue #4200 because the recovery documents exist.

## Progress tracking

Issue [#4200](https://github.com/jmorrison-juniper/MistHelper/issues/4200) remains the migration and recovery tracker.
It has the `in-progress` label and a recovery progress comment.
Do not create a duplicate issue for the same recovery scope.
Update task status only when its full evidence or implementation objective is satisfied.
Future issue updates must identify completed tasks, open gates, exact revisions, and validation results.

## Candidate validation before PR #4358 merged

This historical candidate used base `816f42bac74aebfb936ac9fc9b72fe1ec2030c09`.
Its implementation commit is `40278aa1948cda154f7372c1b0dd893b3865c9f5`.
Keep issue #4200 open, and leave the existing draft PR #4208 unchanged.
No workflow, dependency pin, test-quality baseline, `MistHelper.py`, operation registry, or primary-key map changed.
The current-main workflow fixes remain unchanged, including the WAN browser upload with `if-no-files-found: warn`.

| Gate | Command | Result |
| --- | --- | --- |
| WAN unit | `python -m pytest -q tests/unit/wan_performance` | 250 passed. |
| WAN browser | `python -m pytest -q tests/e2e/web_portal/test_wan_performance_live.py tests/e2e/web_portal/test_wan_performance_offline.py` | 61 passed. |
| Mist SDK | `python -m pytest -q tests/integration/test_mistapi_sdk_compatibility.py` | 8 passed. It found zero known signature failures. |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | 900 source files passed. |
| Style and compile | `python -m ruff check .` and `python -m black --check .` and `python -m compileall -q src/interfaces/wan_performance web_portal/app.py` | Ruff passed. Black left 2,596 files unchanged. Compilation passed. |
| Complexity and security | `radon cc src/interfaces/wan_performance -j \| complexity-gate --max 10` and `bandit -c pyproject.toml -r src/interfaces/wan_performance -q` | Both passed. |
| Dependencies | `pip-audit -r requirements.txt` | No known vulnerabilities. Cache warnings did not stop the audit. |
| Test quality | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` and `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | Full gate checked 1,260 files and 404 findings, with zero new findings. Post-commit gate checked 15 test files, found zero findings, skipped two, and reported zero parse errors. |
| Writing style | `ste-linter --config .ste-linter.toml --min-score 80` on the 12 candidate Markdown files | All 12 passed. Scores ranged from 88 to 97. No file was skipped. |
| Links | `markdown-link-check --root .` on the 12 candidate Markdown files | Zero broken links. |

The test inventory replaces eight prior unit modules with 13 focused unit-test modules and two browser-test modules.
All tests used offline or mocked data. No live Mist call, production credential, or production database write occurred.
These checks do not complete the feature. Of 47 tasks, 12 have direct local proof, eight remain buildable, and 27 remain blocked.
The table below gives the status and evidence for each task.
Source temporal, weighting, and p95 semantics remain unverified.
The existing 13-month history, backfill, retention capacity, and completeness also remain unverified.

### Fresh-main revalidation

| Check | Command | Result |
| --- | --- | --- |
| Regression tests | `rtk .venv/bin/python -m pytest -q tests/unit/wan_performance/test_history_repository.py tests/unit/wan_performance/test_calendar_summaries.py tests/unit/wan_performance/test_gateway_insights.py tests/e2e/web_portal/test_wan_performance_live.py` | 160 passed. Two existing pytest warnings remain. |
| Mist SDK | `rtk .venv/bin/python -m pytest -q tests/integration/test_mistapi_sdk_compatibility.py` | Eight passed. The guard checked 585 calls and found zero known signature failures. |
| Static checks | `ruff check`, `black --check`, `mypy`, `compileall`, Radon, and Bandit on the WAN package | All passed. Mypy checked 24 source files. |
| Markdown | `ste-linter --min-score 80` and `markdown-link-check --root .` on the nine changed Markdown files | Scores ranged from 84 to 97. The link scan found zero broken links. |
| Test-quality preflight | `rtk .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | One passed. The guard read and validated all four required inputs. |
| Task audit | `rtk .venv/bin/speckit-task-audit --root .` | The repository-wide scan failed on its existing backlog: 3,572 unchecked markers and 36 malformed markers. It listed this feature with 35 unchecked tasks. |

## Current candidate task audit

The 2026-11-14 continuation adds a rights and dependency investigation and a bounded MOS correction.
The original application remains unexecuted because its package explicitly declares a proprietary license.
The renewed request does not establish a rights grant.
See [research](design/research.md#renewed-original-application-investigation) for the current boundary and dependency findings.
See [the exploration matrix](design/contracts/parity.md#original-application-exploration-plan) for the complete interaction plan.

The bundled `vpn_peer_stat` schema bounds MOS from zero through five.
Independent red tests reproduced missing score support and absent bound validation: eight failed and 19 passed.
The collector now retains the score, accepts both bounds, and rejects invalid values.
It infers no quality category, metric timestamp, or historical aggregation.
The existing replay policy still rejects changed payloads at an existing sample key.
This increment does not rewrite retained records.

| Continuation check | Exact command or scope | Result |
| --- | --- | --- |
| Destination regression | `rtk .venv/bin/python -m pytest -q tests/unit/wan_performance tests/e2e/web_portal/test_wan_performance_offline.py tests/e2e/web_portal/test_wan_performance_live.py tests/integration/test_mistapi_sdk_compatibility.py` | 355 passed, two existing warnings. No original-source test ran. |
| Style | `ruff check` and `black --check` on `snapshot_records.py`, `test_peer_snapshot_metrics.py`, and `test_peer_insights.py` | Both passed. Black examined three files. |
| Types | `rtk .venv/bin/mypy src/interfaces/wan_performance --config-file pyproject.toml` | Passed on 24 source files. |
| Compilation | `rtk .venv/bin/python -m py_compile src/interfaces/wan_performance/collection/snapshot_records.py` | Passed. |
| Plan setup | Session-local PowerShell `setup-plan.ps1 -Json` with the explicit feature directory and telemetry disabled | Resolved the existing plan without replacing it. |

These are destination results, not a full original-application cycle.
Source startup, control interaction, visualization changes, downloads, failure behavior, and cleanup remain unexecuted.
No new environment, process, container, volume, or network was started for the source.
Initial SDK inspection confirmed a site-scoped SLE impacted-gateway operation and its metric catalog.
That initial mocked call verified forwarding only. T049 now adds application scope, admission, response, failure, and browser tests.
The [SLE contract note](design/contracts/parity.md#supported-sle-gateway-drilldown-candidate) retains the source-unit, paging, and source-equivalence limits.

The current candidate starts from main `2a6a5844698aeb180fea353e0243034890774565`.
Its starting head was `07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc`.
The 47 task IDs below were checked against current code, tests, and evidence.
`Complete` means the task deliverable has direct local proof.
`Buildable` means evidence or implementation work remains, with no established external blocker.
`Blocked` names the exact evidence or owner decision that prevents safe completion.

| Task | Audit | Proof or remaining work |
| --- | --- | --- |
| T001 | Complete | `design/research.md` now records pinned source, fresh-main base, candidate start, branch ownership, and absent copying rights. |
| T002 | Blocked | Preserved commit `d77a900f9ec4db7149f90f324f1ade7772a6243d` contains only the current T001-T047 file. The owner-provided historical T001-T087 records are unavailable. |
| T003 | Complete | `design/contracts/parity.md` now maps D01-D15, ProjectGoals, source test intent, destination selectors, and unknown contracts in P21-P50. No source code or assets were copied. |
| T004 | Complete | `design/contracts/parity.md` records gateway and organization-stat schemas, timestamps, SDK limits, admission, paging, lease, and cache bounds. |
| T005 | Complete | `test_live_service.py` and `test_request_admission.py` cover organization scope, admission, and failed writes. The focused feature suite passed. |
| T006 | Complete | `live_service.py` and `history_repository.py` preserve authorization, configured-store selection, and fail-closed admission. Their regression tests passed. |
| T007 | Complete | P21-P35 map overview summaries, rankings, alerts, charts, controls, navigation, SLE details, and exports to destination selectors or explicit gaps. |
| T008 | Complete | P36-P39 map gateway identity, health, tables, links, charts, and unsupported fields. |
| T009 | Complete | P40-P44 map port status, configuration, encoded routing, bandwidth, and counters. |
| T010 | Complete | P45-P48 map peer quality, MOS, path fields, tunnel scope, and destination links. |
| T011 | Complete | `test_wan_performance_offline.py` covers direct routes, encoded paths, scope, and four-journey navigation. |
| T012 | Blocked E1 | Journey changes must follow the incomplete source inventory. Do not claim source parity from destination tests. |
| T013 | Blocked E3 | Source capacity, region membership, role history, and complete-hour semantics remain unverified. |
| T014 | Blocked E3 | Destination tests preserve unknown capacity, but source capacity units and boundaries are not established. |
| T015 | Blocked E7 | The exact source interval, coverage, and duration rules are unavailable. |
| T016 | Blocked E7 | Local gap tests pass, but source duration boundaries and continuous-versus-cumulative semantics remain unknown. |
| T017 | Blocked E4 | Source event definitions, ordering, duplicate policy, flap rule, and availability denominator remain unverified. |
| T018 | Complete | `test_snapshot_records.py` covers complete and incomplete event states. The full selected suite passed. |
| T019 | Blocked E3/E4 | Ranking scope, tie rules, roles, and failover classification lack verified source contracts. |
| T020 | Blocked E3/E4 | Do not calculate primary/secondary or failover results before source role and event rules are known. |
| T021 | Blocked E3/E4 | Current browser tests cover threshold and sampled-state displays. Source ranking and failover expectations remain unavailable. |
| T022 | Blocked E3/E4 | Do not wire unverified role, ranking, or availability calculations into presentation pages. |
| T023 | Blocked E5 | Peer statistics have scalar values and no metric timestamp. Source averaging, maximum, and p95 rules remain unknown. |
| T024 | Blocked E5 | Poll samples are tested and retained, but they do not prove source quality history or raw-sample percentiles. |
| T025 | Blocked E6 | T049 verifies enabled catalog choices, gateway identity fields, and bounded raw-response handling. Source score meanings, classifier mappings, duration units, and source-equivalent impact semantics remain unverified. |
| T026 | Blocked E6 | T049 implements independent catalog-validated site inspection and raw impacted-gateway results. Source-specific score calculations and equivalent drilldowns remain blocked by missing contracts. |
| T027 | Blocked E3/E7 | Region membership, circuit weights, canonical source hours, and source coverage rules remain unknown. |
| T028 | Blocked E3/E7 | Local 3h, 12h, 24h, and calendar tests pass. Source aggregation and coverage acceptance remain blocked. |
| T029 | Blocked E7 | Existing 13-month data, backfill, retention, capacity, and completeness have no proof. |
| T030 | Blocked E7 | Both stores pass append-only replay tests. No retention or backfill policy is approved. |
| T031 | Complete | The audience table maps executive, engineering, and SLE goals to selectors or explicit gaps. T049-T051 add independent SLE, cached-table, and export controls without claiming audience parity. |
| T032 | Blocked E1/E3/E6 | Independent cached filters and CSV export now exist under T050-T051. Source-specific audience dimensions, controls, export formats, and SLE score mappings remain unverified. |
| T033 | Complete | `design/research.md` records absent written rights and permits descriptive static comparison only. Runtime and visual parity remain blocked. |
| T034 | Complete | The descriptive inventory covers hierarchy, type, colors, charts, tables, and responsive behavior. Source captures remain unopened and visual approval remains blocked by E2. |
| T035 | Complete | Offline browser tests check stable selectors at 1440x1100, 1280x800, and 390x844, plus horizontal overflow, sibling overlap, Tab focus, and Enter activation. |
| T036 | Blocked E2 | No written rights or approved runtime capture method exists for protected visual comparison. |
| T037 | Complete | `design/contracts/parity.md` records worker and cache bounds, Redis ownership, retries, stale states, and matching local tests. |
| T038 | Complete | `test_background_refresh.py`, `test_refresh_store.py`, and `test_request_admission.py` cover limits, expiry, repeated requests, and outages. |
| T039 | Complete | Added concurrent-owner, retry, and lost-lease regressions. All pass. No refresh-policy defect was reproduced, so no production code change was justified. |
| T040 | Complete | `test_wan_performance_live.py` covers stale, missing, invalid-scope, store, session, and API failure states. |
| T041 | Complete | The quickstart regression command ran mocked live and synthetic journeys with no production credentials. It passed 408 tests. |
| T042 | Complete | The same 408-test run covered portal smoke, converter routes, websocket routes, and synthetic isolation. No service or port changed. |
| T043 | Complete | The coverage matrices below map all 50 inventory rows and 24 FR/SC entries to tasks, tests or explicit test gaps, evidence, and decisions. |
| T044 | Complete | The feature-specific prerequisite, consistency review, task format audit, link scan, structure tests, and STE checks passed. The broader route contract has one unrelated failure, recorded below. |
| T045 | Blocked by assignment scope | Local gates can run. Hosted exact-head CI is not authorized before parent review. |
| T046 | Complete | `documentation/wan-performance.md` and `changelog.d/pr-4208.md` describe replay, unknown event coverage, gateway scope, issues #4793-#4795, retained MOS compatibility, and independent SLE, table, cached-site, and retained-window controls. |
| T047 | Blocked by assignment scope | Parent review must precede PR metadata or acceptance changes. No PR template or hosted state was changed. |

### Source inventory and requirement coverage for T043

The inventory contains P01-P50.
Every row has a source classification, destination evidence, and an acceptance decision in `design/contracts/parity.md`.
The table below gives the task and local test evidence.
An explicit test gap means the behavior remains unaccepted.

| Row | Task | Destination test or evidence | Decision |
| --- | --- | --- | --- |
| P01 | T007, T011 | Offline overview browser journey and `wan-overview` selectors | Synthetic route only. |
| P02 | T008, T011 | Gateway route and gateway-to-detail browser links | Identity and history parity remain open. |
| P03 | T009, T011 | Encoded-port and calendar-summary tests | Synthetic values only. |
| P04 | T010, T011 | Peer route and peer-quality tests | Synthetic fields only. |
| P05 | T019-T022 | `wan-top-congested-circuits` preview selector | Top-N ranking test is absent. |
| P06 | T013-T016 | Threshold observation tests in the live test module | Source threshold and override semantics remain unknown. |
| P07 | T015-T016 | `test_wan_performance_live.py` duration assertions | Current sample intervals do not prove source duration parity. |
| P08 | T017-T018 | `test_calendar_summaries.py` event and unknown-coverage cases | Historical flap and availability parity remains open. |
| P09 | T019-T022 | No primary/secondary parity assertion exists | Blocked by missing role and failover contracts. |
| P10 | T023-T024 | Peer snapshot and history tests | Poll samples do not establish source mean, maximum, or p95. |
| P11 | T003, T004, T023 | SDK compatibility test and pinned source discovery | Source methods exist, but required SDK symbols or arguments are unsupported. |
| P12 | T025-T026, T049 | Catalog-choice, raw-value, and SLE browser tests in `test_wan_performance_live.py` | Independent inspection passes. Source score normalization, duration units, and equivalence remain unverified. |
| P13 | T025-T026, T049 | Scoped impacted-gateway request, response-validation, admission, and browser tests | Bounded raw gateway inspection passes. Source-specific classifiers and impact semantics remain unverified. |
| P14 | T013, T027-T028 | No region-to-circuit metric test exists | Region mapping and effective dates remain unknown. |
| P15 | T027-T028 | Calendar summary domain and offline route tests | Local observation windows pass. Source aggregation parity remains open. |
| P16 | T029-T030 | Append-only history tests for both stores | Retention, capacity, completeness, and backfill remain unverified. |
| P17 | T031-T032, T049-T051 | Audience goal matrix and independent SLE, cached-table, and CSV tests | Independent controls exist. Source-specific audience behavior remains unverified. |
| P18 | T003, T031-T032, T051 | `wan-table-export` and scoped cached CSV tests | Full filtered cached export passes. Source export fields, format, and audience equivalence remain unverified. |
| P19 | T007-T012, T052 | Core journeys, keyboard navigation, and cached-site browser tests | Organization/site/gateway/port/peer navigation passes independently. Source navigation equivalence and region routing remain unverified. |
| P20 | T034-T036 | Responsive browser tests and rights record | Destination layout passes. Source visual approval remains blocked. |
| P21 | T007, T011 | Offline overview status, KPI, and route tests | Synthetic population only. |
| P22 | T007, T011 | Live snapshot route tests | Current states pass. Historical failover remains unverified. |
| P23 | T007, T011, T049 | Offline alert selectors and independent SLE request/browser tests | Catalog and raw-impact handling pass with mocked data. Source alert rules and SLE score normalization remain unknown. |
| P24 | T007, T011 | Offline top-circuit table selector and link tests | Rank and precision parity remain untested. |
| P25 | T007, T050 | `wan-table-next`, `wan-table-previous`, and cached pagination route/browser tests | Independent ten-row pagination passes. Source pagination behavior and equivalence remain unverified. |
| P26 | T007, T011, T049 | Offline degraded-SLE selectors and separate raw SLE inspection tests | Overview panels remain synthetic. Independent raw inspection does not establish source degraded-score panel parity. |
| P27 | T007, T050 | `wan-table-filter`, `wan-table-sort`, `wan-table-direction`, and route/browser tests | Independent identity filtering and lexical sorting pass. Source ordering, filters, and ranking semantics remain unverified. |
| P28 | T007, T011, T035 | Offline chart selectors and responsive-region assertions | Layout passes. Source chart semantics remain unknown. |
| P29 | T007, T049, T052 | `wan-cached-site`, exact site routes, scoped CSV, case-sensitive membership, and browser tests | Independent cached-site selection passes. Complete organization inventory and source selector equivalence remain unverified. |
| P30 | T007, T053 | `wan-retained-selection`, bounded repository tests, and four-range route/browser tests | Independent 6h/12h/24h/7d retained UTC views pass. The default remains cache/calendar summaries. Source time semantics, aggregation, and 24-hour default parity remain unverified. |
| P31 | T037-T039 | Background worker retry, ownership, failure, and start-gate tests | Local scheduling policy is bounded and passes. |
| P32 | T007-T011, T049, T052-T053 | Core, cached-site, SLE return, and selected-window browser journeys | Cached site-to-gateway-to-port/peer navigation passes. Region routing and source navigation equivalence remain unverified. |
| P33 | T007, T049 | `wan-live-sle-link`, `wan-sle-metric`, `wan-sle-results`, and SLE browser tests | Independent site/metric inspection passes. Source SLE-detail behavior and score equivalence remain unverified. |
| P34 | T007, T049 | `wan-sle-site`, `wan-sle-results`, `wan-sle-coverage`, and scoped request tests | Raw impacted-gateway rows and partial-page labels pass. Source impact-detail interactions, units, and classifier equivalence remain unverified. |
| P35 | T007, T051 | `wan-table-export`, CSV scope/formula tests, and browser download tests | Independent full filtered cached CSV export passes. Source export format and equivalence remain unverified. |
| P36 | T008, T011 | Gateway live and offline route tests | Offline identity is synthetic. Live field units remain unverified. |
| P37 | T008 | Gateway selector and explicit field-gap record | CPU, memory, and uptime have no destination assertion. |
| P38 | T008, T011 | Gateway port/peer table and link tests | Synthetic navigation passes. Full identity parity remains open. |
| P39 | T008, T011 | Gateway chart selectors in offline browser tests | Source axes, units, and coverage remain unknown. |
| P40 | T009, T011 | Port KPI and gauge assertions | Synthetic status and utilization only. |
| P41 | T009, T011 | Current-statistic and configuration selectors | Field mapping and units remain unverified. |
| P42 | T009, T011 | Encoded-slash route test | Offline encoded route behavior passes. |
| P43 | T009, T023 | Selected-port history and SDK compatibility tests | Source historical method is not portable to the installed SDK. |
| P44 | T009 | Packet and error-counter selectors | Synthetic counters only. No source counter semantics are accepted. |
| P45 | T010, T023-T024, T048 | Peer scalar tests plus retained-MOS SQLite, calendar, and route regressions | Scalar units, MOS bounds, and missing-unit compatibility pass. Source history and MOS quality categories remain unknown. |
| P46 | T010 | Peer detail selector and explicit contract gap | Live field mapping remains unverified. |
| P47 | T010 | Peer statistics selector and explicit contract gap | Live uptime and counter semantics remain unknown. |
| P48 | T010, T040 | Scoped live peer route and path-key tests | MistHelper identity is tested. Source identity equivalence remains open. |
| P49 | T003, T011 | Source test names and destination independent route tests | Source tests were inspected, not executed. No fixtures were copied. |
| P50 | T003, T019-T022 | Source test names and destination live test module | Source tests were inspected, not executed. Ranking parity remains blocked. |

| Requirement | Task | Local test or evidence | Decision |
| --- | --- | --- | --- |
| FR-001 | T003, T007-T010 | P01-P50 inventory and offline browser tests | Static inventory is complete. Runtime parity is not. |
| FR-002 | T002-T003, T043 | Source classifications in `parity.md` and `discovery.md` | Goals, TODOs, and implemented-but-unverified methods remain separate. |
| FR-003 | T007-T012, T033-T036, T049-T053 | Core, SLE, cached-site, table, and selected-window browser journeys | Independent destination navigation and responsive checks pass. Source visual and interaction parity remain unverified. |
| FR-004 | T013-T016, T021-T022 | Threshold and duration tests in the live module | Source calculations and thresholds remain unverified. |
| FR-005 | T017-T022 | Calendar event and live state tests | Flap, failover, and availability parity remains open. |
| FR-006 | T023-T024, T048 | Peer snapshot, history, retained-MOS SQLite, and displayed-unit tests | Missing-unit compatibility passes without rewriting data. Poll-sample statistics do not prove source history. |
| FR-007 | T025-T026, T049 | Catalog, cached-site scope, raw impacted-gateway, failure, and browser tests | Independent bounded SLE inspection passes. Source score, classifier, duration-unit, and impact equivalence remain unverified. |
| FR-008 | T013, T027-T028, T053 | UTC calendar, rolling summaries, and bounded retained-window tests | Independent UTC views pass without new aggregation. Region weighting, source time semantics, and measured completeness remain unknown. |
| FR-009 | T029-T030 | SQLite and Arango append-only tests | Retention and backfill evidence is missing. |
| FR-010 | T031-T032, T049-T051 | Audience goal matrix plus independent SLE, cached-filter, and CSV tests | Independent destination controls exist. Source-specific audience dimensions and export equivalence remain unverified. |
| FR-011 | T004-T006, T037-T042, T049 | Admission, live service, worker, Redis protocol, SLE scope, and browser tests | Local scope and failure controls pass. No live Redis or multi-process proof is claimed. |
| FR-012 | T042, T045 | Changed-file inventory and offline tests | No extra service, port, or credential store was added. |
| FR-013 | T005-T006, T040-T042 | Synthetic isolation and provenance tests | Offline data remains separate from live collection. |
| FR-014 | T005, T038-T042, T048-T049, T053 | Missing-unit, empty, stale, denied, store, session, SLE, and retained-window failure tests | Missing buckets and values remain explicit. Failed or unsupported history never appears as healthy empty data. |
| FR-015 | T033-T036, T041, T043 | Descriptive comparison, browser evidence, and rights record | Runtime comparison remains blocked by missing rights. |
| FR-016 | T043-T047 | Exact local candidate and check records | Hosted and owner acceptance remain pending. |
| SC-001 | T003, T007-T010, T043 | P01-P50 classifications | All inventory rows have a decision, including explicit unknowns. |
| SC-002 | T011-T042, T043 | Focused tests and blocked-row decisions | Full source behavior is not complete. |
| SC-003 | T014-T030, T040, T048-T049, T053 | Unknown-value, missing-unit, raw SLE, and retained-window assertions | Unavailable values remain explicit. Missing buckets remain absent, and bucket presence does not establish measurement completeness. |
| SC-004 | T014-T030 | Domain expected-value tests | Supported calculations pass. Unsupported source formulas remain open. |
| SC-005 | T011, T021, T026, T032, T035, T040-T042, T049-T053 | Core, SLE, cached-control, site, and retained-window browser tests at three viewports | Tested independent destination journeys pass. Source interaction equivalence remains unverified. |
| SC-006 | T033-T036, T043 | Descriptive layout inventory and rights record | Source visual acceptance remains blocked. |
| SC-007 | T005-T006, T037-T042, T049-T053 | Offline, scoped-store, admission, SLE, CSV, site, and bounded-window tests | No live Mist call or production store was used. |
| SC-008 | T043-T047 | Local validation record and parent review hold | Parent review is pending. |

### Frozen-head defect regressions

The parent reproduced #4793 with the actual SQLite repository and a temporary database.
The second refresh raised `sqlite3.IntegrityError: UNIQUE constraint failed: wan_performance_samples.identity, wan_performance_samples.sampled_at`.
`test_sqlite_api_sample_replay_keeps_one_original_sample` now proves an unchanged replay is a no-op.
`test_sqlite_rejects_changed_api_sample_without_replacing_prior_rows` proves changed data aborts the hourly and sample transaction.
`test_arango_api_sample_replay_is_idempotent_and_rejects_changes` proves both Arango replay outcomes through the transactional repository boundary.

## Current continuation validation

The read-only consistency review found no conflict with the constitution.
It covered 24 requirements, 47 tasks, and 50 inventory rows.
All 24 requirement rows map to tasks. All 50 inventory rows have evidence and a decision.
No task lacks an evidence row. No critical issue remains in these artifacts.
The review found and corrected three stale statements about inventory completeness, live site selection, and PowerShell availability.
The candidate removes eight existing unit-test modules under `tests/unit/wan_dashboard/wan_performance` and adds thirteen modules under `tests/unit/wan_performance`.
It also adds two browser test modules. The old `last_seen` window assertion is not retained because `last_seen` is peer observation time, not metric sample time.
No source test or fixture was copied.

| Gate | Command or evidence | Result |
| --- | --- | --- |
| Spec Kit prerequisite | `POWERSHELL_TELEMETRY_OPTOUT=1 DOTNET_CLI_TELEMETRY_OPTOUT=1 SPECIFY_FEATURE_DIRECTORY=specs/numbered/0/0/1/1/3/3/0/0/4200-wan-parity-recovery rtk /Users/jmorrison/.copilot/session-state/9dc828a7-11a6-41a6-8d00-fe4383d12c54/files/tools/pr4208-powershell-7.7.0-osx-arm64/runtime/pwsh -NoLogo -NoProfile -NonInteractive -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` | Passed. JSON resolved this feature and listed five available documents. |
| Feature pointer | `rtk shasum -a 256 .specify/feature.json` before and after the prerequisite | Unchanged at `2a4c81936e119e39033cb787044b14649832177a469855d843835ea8f2189039`. |
| Task format | `rtk .venv/bin/speckit-task-audit --root <temporary-root>` on an isolated copy of this feature record | Examined 47 task markers: 24 checked, 23 unchecked, and zero malformed. The 23 open tasks remain gated or blocked. |
| Markdown links | `rtk .venv/bin/markdown-link-check` with the four changed feature record paths | Examined four tracked Markdown files and found zero broken links. |
| Feature structure | `rtk .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/test_process_folder_structure.py tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | 12 passed. The structure guard examined 795 children, 262 structural directories, and 104 feature records. |
| STE | `rtk .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 --quiet` with the four changed feature record paths | Passed. Scores: analysis 94, plan 95, tasks 97, parity 92. |
| Local whitespace | `git diff --check` | Passed. |
| WAN suite | `rtk .venv/bin/python -m pytest tests/unit/wan_performance tests/e2e/web_portal/test_wan_performance_live.py tests/e2e/web_portal/test_wan_performance_offline.py` | 341 passed with two existing deprecation warnings. |
| Mist SDK | `rtk .venv/bin/python -m pytest tests/integration/test_mistapi_sdk_compatibility.py` | Eight passed. The guard found zero known signature failures. |
| Types | `rtk .venv/bin/python -m mypy src/interfaces/wan_performance src/foundation/support/refactors/initialize_mist_session.py --config-file pyproject.toml` | Passed with no issues in 25 source files. |
| Style | `rtk .venv/bin/python -m ruff check` and `rtk .venv/bin/python -m black --check` with both changed test paths | Passed. |
| Test quality | `rtk .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | Scanned 15 test files with zero findings, two skips, zero parse errors, and zero new findings. |
| Quality guidance | `rtk .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | One passed. The gate read and validated all four required inputs. |

The broader `test_spec_route_contract.py` run had 39 passes and one unrelated failure.
`test_timestamp_route_rejects_invalid_names[20261013-240000-bad]` expected the shared route script to reject hour `24`, but the script accepted it.
This task changed no route script. The folder structure guard and feature prerequisite passed.

The repository-wide task audit examined 900 feature records and found 36 malformed markers outside this feature.
This feature audit found zero malformed markers. The repository-wide audit also found open tasks, as expected.
No dependency manifest changed, so no dependency audit ran.

The parent reproduced #4794 with actual domain modules.
`CalendarSummaries.build` raised `KeyError('flap_count')` when an event hour and an ordinary poll hour shared one circuit.
The current summary excludes records without known flap evidence and keeps missing duration and flap values unknown.
Mixed, missing, and known-zero cases pass in `test_calendar_summaries.py`.

The parent reproduced #4795 with actual domain modules and a mock repository.
Gateway history returned one summary and made one read before ordinary refresh, then returned no summary and made no read afterward.
The current route resolves one full gateway identity from circuit or peer rows, with organization and site scope.
`test_gateway_history_remains_visible_after_ordinary_refresh` and `test_gateway_history_rejects_ambiguous_or_foreign_gateway_identity` pass.

### Current local validation

The quickstart command passed 408 tests with two existing pytest deprecation warnings.
The earlier focused run passed 159 tests before the ambiguity regression was added.
Re-run focused tests and all applicable style, type, link, STE, and test-quality gates after the final edits.
Do not treat these local results as hosted CI or source acceptance.
