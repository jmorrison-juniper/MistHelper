# Tasks: WAN migration parity recovery

**Input**: [specification](spec.md), [plan](plan.md), and [contracts](design/contracts/parity.md).

Tasks marked `[X]` have evidence in `analysis.md`. Open tasks remain gated or blocked by named evidence limits.
Existing implementation is evidence to verify, not an automatic completed task.
Do not execute blocked implementation pairs without their evidence gates.
Preserve these task IDs across updates. Dependency rules override phase display order.
Task paths are repository-relative unless the task names a document in this feature record.
For a combined test and repair task, record the failing assertion before production edits and the passing assertion afterward.
If existing behavior passes, record that evidence instead of adding an unnecessary repair.

## Phase 1 - Setup and preservation

- [X] T001 Record current source, destination, main, ownership, and copying-rights baselines in design/research.md.
- [ ] T002 Reconcile owner-provided historical T001-T087 records into an old-to-new mapping in analysis.md without changing historical states.
- [X] T003 Complete the exhaustive inventory in design/contracts/parity.md from pinned docs, active pages, and tests, using D01-D15 in design/contracts/discovery.md.
- [X] T004 Complete SDK field, timestamp, limitation, and refresh prerequisites in design/contracts/parity.md, using the static signature findings in design/contracts/discovery.md.

## Phase 2 - Foundation

- [X] T005 Write failing authorization, origin isolation, scoped storage, and admission tests in tests/unit/wan_performance/test_live_service.py.
- [X] T006 Repair only T005 failures in src/interfaces/wan_performance/collection/live_service.py and src/interfaces/wan_performance/integration/history_repository.py after the foundation portion of E8 passes.

Goal: preserve host safety before extending metrics.
Independent test: denied and synthetic requests perform no live collection or live writes.

## Phase 3 - US1: Four journeys and source comparison

- [X] T007 [US1] Map every overview element and behavior to destination selectors and evidence in design/contracts/parity.md.
- [X] T008 [US1] Map every gateway identity, panel, port, and peer transition in design/contracts/parity.md.
- [X] T009 [US1] Map every encoded port route, control, metric, and state in design/contracts/parity.md.
- [X] T010 [US1] Map every peer route, tunnel field, quality metric, and state in design/contracts/parity.md.
- [X] T011 [US1] Add failing four-journey navigation, query, scope, and direct-link assertions in tests/e2e/web_portal/test_wan_performance_offline.py.
- [ ] T012 [US1] Repair verified journey differences in src/interfaces/wan_performance/presentation/ after T007-T011 and E1 pass.

Goal: prove equivalent user actions rather than page-load success.
Independent test: complete all source-mapped transitions with correct identity and scope.

## Phase 4 - US2: Utilization and failure views

- [ ] T013 [US2] Verify capacity, units, threshold boundaries, region membership, and role effective times in design/contracts/parity.md.
- [ ] T014 [US2] Test utilization in tests/unit/wan_performance/test_domain.py before repairing src/interfaces/wan_performance/domain/measurement.py after E3 passes. An absent or zero capacity prevents utilization calculation.
- [ ] T015 [US2] Define interval coverage, gaps, continuous runs, cumulative duration, and configurable thresholds in design/contracts/parity.md.
- [ ] T016 [US2] Test duration boundaries and missing intervals in tests/unit/wan_performance/test_calendar_summaries.py before repairing src/interfaces/wan_performance/domain/summary.py after the interval portion of E7 passes.
- [ ] T017 [US2] Verify event types, transition ordering, duplicate handling, flap counting, and availability denominator in design/contracts/parity.md.
- [X] T018 [US2] Test status and availability with complete and incomplete events in tests/unit/wan_performance/test_snapshot_records.py before repairing src/interfaces/wan_performance/collection/snapshot_records.py after E4 passes.
- [ ] T019 [US2] Verify ranking scope, ties, top-N limits, primary/secondary comparison, and failover classification in design/contracts/parity.md.
- [ ] T020 [US2] Test ranking and failover scenarios in tests/unit/wan_performance/test_domain.py before repairing src/interfaces/wan_performance/domain/summary.py after E3-E4 pass. Unknown role or region prevents role or region aggregation.
- [ ] T021 [US2] Add failing circuit, threshold, failure, and availability browser assertions in tests/e2e/web_portal/test_wan_performance_live.py.
- [ ] T022 [US2] Wire only verified performance results into src/interfaces/wan_performance/presentation/ after T014, T016, T018, T020, and T021 pass.

Goal: distinguish observation counts from duration and current state from historical availability.
Independent test: independently calculated intervals and failures produce exact results or explicit unavailable states.

## Phase 5 - US3: Quality and SLE

- [ ] T023 [US3] Verify peer sampling, timestamp source, units, averaging weights, maximum, and p95 method in design/contracts/parity.md.
- [ ] T024 [US3] Test quality history in tests/unit/wan_performance/test_peer_insights.py before repairing src/interfaces/wan_performance/collection/peer_insights.py after E5 passes. An absent timestamp prevents historical placement.
- [ ] T025 [US3] Verify supported SLE methods, score semantics, classifiers, impact fields, and entity mappings in design/contracts/parity.md.
- [ ] T026 [US3] Test SLE contracts, 4xx/5xx, and drilldowns in tests/e2e/web_portal/test_wan_performance_live.py before updating src/interfaces/wan_performance/collection/live_service.py and src/interfaces/wan_performance/presentation/live_routes.py after E6 passes.

Goal: implement supported quality and service-experience behavior without guessed endpoint or timestamp semantics.
Independent test: approved quality results and SLE impacts preserve identity and time scope.

## Phase 6 - US4: Windows, history, and audiences

- [ ] T027 [US4] Define region/site/circuit weighting, canonical hours, UTC boundaries, short windows, and daily/weekly/monthly coverage in design/contracts/parity.md.
- [ ] T028 [US4] Test 3h/12h/24h and calendar rollups in tests/unit/wan_performance/test_calendar_summaries.py before repairing src/interfaces/wan_performance/domain/calendar.py and src/interfaces/wan_performance/domain/summary.py after E3 and interval E7 pass.
- [ ] T029 [US4] Verify 13-month reads, source backfill, storage capacity, retention, and incomplete-history rules in design/contracts/parity.md.
- [ ] T030 [US4] Test both stores in tests/unit/wan_performance/test_history_repository.py before updating src/interfaces/wan_performance/integration/sqlite_history.py and src/interfaces/wan_performance/integration/arango_history.py after retention E7 passes.
- [X] T031 [US4] Define executive, engineering, and SLE audience controls and summaries in design/contracts/parity.md from verified source goals.
- [ ] T032 [US4] Test audience filters, report scope, and required top-offender exports in tests/e2e/web_portal/test_wan_performance_live.py before updating src/interfaces/wan_performance/presentation/live_routes.py after T027-T031 pass.

Goal: show reporting coverage honestly and preserve approved audience requirements.
Independent test: each approved scope and window matches independent results without a second database.

## Phase 7 - US1: Appearance acceptance

- [X] T033 [US1] Record written rights or the explicit runtime-comparison blocker and approved evidence method in design/research.md.
- [X] T034 [US1] Inventory layout, typography, colors, chart semantics, table behavior, and responsive differences in design/contracts/parity.md.
- [X] T035 [US1] Add failing layout, keyboard, overlap, and selector assertions in tests/e2e/web_portal/test_wan_performance_offline.py.
- [ ] T036 [US1] Repair approved visual differences in web_portal/static/css/wan_performance.css and src/interfaces/wan_performance/presentation/templates/wan_performance/ after T033-T035 pass.

Goal: preserve reviewed appearance without reproducing protected material.
Independent test: every required visual row has approved evidence or a named blocker.

## Phase 8 - US5: Safety, refresh, and failures

- [X] T037 [US5] Verify shared refresh bounds, concurrency, retry budgets, stale states, and optional Redis ownership in design/contracts/parity.md.
- [X] T038 [US5] Test request limits, repeated users, expiry, and outage errors in tests/unit/wan_performance/test_background_refresh.py and tests/unit/wan_performance/test_refresh_store.py.
- [X] T039 [US5] Repair verified refresh failures in src/interfaces/wan_performance/background_refresh.py and src/interfaces/wan_performance/integration/refresh_store.py after E8 and T038 pass.
- [X] T040 [US5] Add browser denied-access, missing-data, stale-data, invalid-scope, storage-error, and API-error assertions in tests/e2e/web_portal/test_wan_performance_live.py.
- [X] T041 [US5] Run complete synthetic and mocked live journeys with external requests blocked and retained redacted evidence using design/quickstart.md.
- [X] T042 [US5] Verify unchanged host navigation, existing portal journeys, no extra services, and synthetic isolation in design/quickstart.md.

Goal: complete safe workflows within the existing application.
Independent test: negative cases stop safely and unrelated portal journeys still pass.

## Phase 9 - Acceptance and publication

- [X] T043 Verify every FR/SC and every source inventory row has task, test, evidence, and decision coverage in analysis.md.
- [X] T044 Run Spec Kit consistency, task format, link, structure, and STE checks and record exact results in analysis.md.
- [ ] T045 Run applicable local gates and exact-head CI after ownership reconciliation using design/quickstart.md.
- [X] T046 Update documentation/wan-performance.md and changelog.d/pr-4208.md with verified behavior and unresolved blockers.
- [ ] T047 Prepare owner acceptance evidence in analysis.md and the existing PR template without enabling auto-merge or closing issue #4200.

## Independent destination increments

These tasks do not replace source-parity acceptance or authorize source execution.

- [X] T048 Repair mixed retained missing-unit and new MOS history in domain/summary.py, with calendar and route regressions.
- [X] T049 Add a bounded catalog-validated SLE inspection page under presentation/inspection/, with mocked scope, admission, failure, and browser tests.
- [X] T050 Add cached identity filtering, lexical sorting, and ten-row pagination without changing route or history scope.
- [X] T051 Add a full-identity cached CSV export with explicit missing values, scope preservation, and spreadsheet-formula protection.
- [X] T052 Add cached-site selection and scoped site/detail navigation with tenant and selected-window preservation, plus route and browser tests.
- [X] T053 Add bounded 6h/12h/24h/7d retained UTC observation views with explicit missing/unavailable states and repository, route, and browser tests.
- [X] T054 Verify the approved original-execution isolation, run its local test cycle, and explore independently seeded controls with factual evidence in design/contracts/parity.md.
- [X] T055 Add independently designed retained projection plots with discrete points, metric/unit separation, exact UTC bucket placement, and missing-data tests.
- [X] T056 Add independently designed browser-only retained-plot zoom, bounded movement, reset, exact point inspection, and local PNG download with keyboard and no-request tests.
- [X] T057 Add independent local raw SLE identity-text sorting and five-row display pagination, preserving missing values, response scope, and completeness labels without additional API requests.
- [X] T058 Examine remaining authorized source legends, sharing, clipboard boundaries, and selection modes. Add independent retained metric visibility controls with keyboard, no-script, figure-isolation, zoom/reset, PNG, and no-request browser tests.
- [X] T059 Verify the original site-selector provider shape with independent isolated data. Add accessible independent retained-point rectangle selection with exact identity, zero/missing, bounds, pointer cancellation, keyboard, figure-isolation, and no-query browser tests.
- [X] T060 Display only documented cached gateway CPU/memory usage, device uptime, and last observation in the existing inspection table module and live route/template, with unit, scope, missing/invalid, no-query, and three-viewport browser tests.
- [X] T061 Define independently designed version-one replacement contracts and preserve original acceptance states in spec.md, plan.md, analysis.md, and design/contracts/replacements.md.
- [X] T062 Add scoped hourly-projection observation statistics and configurable percentage-threshold counts in presentation/inspection/windows.py and the existing live route/template, with hand-calculated unit, missing/overflow, scope, no-extra-read, and browser assertions.
- [X] T063 Validate thirteen calendar months of independently authored synthetic records through temporary SQLite and mocked Arango in tests/unit/wan_performance/test_history_repository.py, preserving provenance, gaps, exact identity, boundaries, and repeat-write behavior.
- [x] T064 Implement bounded cached/retained observation ranking in inspection/reports.py and the live view, with exact units, stable identity/time ties, missing counts, and unit/browser tests.
- [x] T065 Implement scoped operator-declaration validation, process-lifetime storage, and export in the existing integration and inspection modules, with no network changes.
- [ ] T066 Implement bounded archive validation, isolated synthetic import/export, and trusted-review atomic live append in the existing integration and inspection modules, with native SQLite and mocked Arango tests.

## Dependencies and execution order

T001-T004 establish evidence before implementation.
T004 must establish existing authorization, scoped storage, origin isolation, and admission contracts before T005.
T005 precedes T006. Only foundation E8 blocks T006. New background policies remain T037-T039.
US1 inventory depends on T001-T003. T011 precedes T012.
Every combined test/implementation task requires a demonstrated failing test before production edits.
E3 blocks T014. E7 blocks T016. E4 blocks T018. E3-E4 block T020.
T021 precedes T022 and does not replace its domain prerequisites.
E5 blocks T024. E6 blocks T026.
E3/E7 block T028. E7 blocks T030. T027-T031 block T032.
T015 establishes interval E7 for T016. T027 establishes window E7 for T028.
T029 establishes retention E7 for T030. Retention research does not block independent duration tests.
E2 and T033-T035 block T036. Missing rights blocks protected comparison, not descriptive inventory.
T037-T038 and E8 block T039.
T041-T042 depend on the verified story increments, not unsupported substitute values.
T043-T047 follow all required comparison rows. A blocked required row prevents acceptance.
T054 establishes source isolation for T059. T055-T058 establish the retained geometry and visibility contracts before T059.
T061 precedes T062 and T063. These independent replacements do not mark original source acceptance tasks complete.
T064, T065, and T066 each require the extended replacement contract. Their implementations remain separate increments.

## Parallel opportunities

Evidence investigation for E3-E8 can run independently after the baseline.
Different investigators must not edit the shared contract file concurrently.
After contracts pass, different tests may run independently with isolated data.
No implementation task has a parallel marker because package and shared-portal ownership require serial reconciliation.

## Implementation strategy

First complete source inventory and safe offline navigation.
Then implement each evidence-approved metric increment with failing tests.
Do not reduce required source functionality silently. Request an explicit deviation decision when a required contract cannot be established.
Finish with full visual, functional, negative-case, and host-regression acceptance.
