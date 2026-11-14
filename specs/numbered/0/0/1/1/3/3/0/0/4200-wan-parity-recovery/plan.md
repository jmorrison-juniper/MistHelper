# Implementation Plan: WAN migration parity recovery

**Branch**: `jmorrison-juniper-4200-migrate-mistwanperformance`

**Date**: 2026-11-05

**Spec**: [spec.md](spec.md)

## Summary

Recover migration confidence through a source inventory, independent contract verification, test-first increments, and four-journey acceptance.
Do not treat previous green CI as source parity.

## Technical Context

Use Python 3.15+, the supported Mist SDK, existing Flask portal, and Playwright tests.
Product modules currently reside under `src/interfaces/wan_performance/`.
Reuse configured SQLite or ArangoDB storage. Do not add a second database.
Redis remains optional and evidence-gated. Do not introduce new keys or TTLs without an approved contract.
Use existing portal authorization and request admission.

Source baseline: `jmorrison-juniper/MistWANPerformance` at `2d1c2199fa1e31c129ef1e051c5389349a207785`.
The original PR #4208 head and first local candidate are historical observations from 2026-11-05.
The current reconstruction uses main `2a6a5844698aeb180fea353e0243034890774565` as its merge base.
It started at `07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc` and includes the locally reviewed repairs in `d7a706d71cf13661cf33e5b4a96ddafd79b6b67b`.
This candidate remains local. This plan does not authorize publication, hosted checks, or merge.

The approved sampling decision preserves each real poll as a raw sample with full identity and a UTC timestamp.
Use the poll collection time for scalar statistics. Preserve API timestamps for time-series responses.
Derive hourly display values from raw samples. Never replace raw samples with hourly values.
Add sample storage to the configured store and preserve existing hourly rows.
Keep the existing hourly projection rules unchanged. Do not treat hourly values as raw samples or a coverage claim.
Do not delete or expire samples before retention policy and capacity have evidence.
Historical completeness, backfill, and 13-month retention remain unverified.

## Constitution Check

- New process records use the eight-level numeric route and five children or fewer.
- Feature root contains spec, plan, tasks, analysis, and design.
- Design contains research, data model, quickstart, contracts, and checklists.
- No production code, compatibility shims, new services, or credentials enter this planning change.
- A sample-storage change is additive and preserves existing hourly rows.
- Hourly display values derive from raw samples and do not replace them.
- The hourly projection keeps its current calculations. It does not replace timestamped samples or prove complete coverage.
- No sample expiry, historical backfill, or 13-month guarantee is added without evidence.
- Implementation must obey structural limits and record touched existing violations with separate remediation actions.
- Each increment starts with failing tests and preserves existing portal behavior.
- Publication and deployment require explicit acceptance. The original draft and no-merge holds remain controlling.

## Phase 0 - Evidence and baseline

Inventory source goals, README, TODO, screens, page behavior, tests, and operational documentation.
Record every observed feature instead of selecting only the known gaps.
Review source tests and implementation read-only when documentation cannot establish completed behavior.
Do not copy source expressions, fixtures, screenshots, or assets.
A source launch or screenshot reproduction requires rights and a safe isolated execution decision first.
Without permission, descriptive visual comparison can proceed, but pixel parity remains unverified.

Reconcile the earlier T001-T087 plan from its owner-provided artifacts.
Keep its original task states and create an old-to-new task mapping.
Do not edit the other planning worktree.

## Phase 1 - Contracts and acceptance design

Complete [research](design/research.md), [data model](design/data-model.md), and [comparison contract](design/contracts/parity.md).
Resolve each metric separately. Endpoint presence alone does not verify units, sampling, completeness, or aggregation.
Record unresolved findings as blocking evidence, with dependent tasks named.
Implement only fields with verified SDK and OpenAPI contracts. Keep historical completeness and long-term retention blocked until evidence proves them.

## Phase 2 - Test-first implementation

Use the existing package and test locations, subject to current file ownership.
Add failing domain and mocked integration tests before each production increment.
Implement overview and dimensions, status and utilization, quality and SLE, history, then audience views.
Store each real poll under its full identity and UTC sample timestamp in additive storage.
Derive hourly display values separately and preserve each raw sample for quality calculations.
Keep existing hourly records. Do not add destructive migrations, expiry, or unsupported history claims.
Each increment updates its comparison rows and runs focused regression gates.
Do not bundle unrelated repairs.

## Phase 3 - Visual and end-to-end acceptance

Compare layout regions, labels, metric order, spacing, typography, colors, controls, charts, tables, and responsive behavior.
Use 1440-by-1100 as the documented source comparison viewport.
Also test 1280-by-800 and 390-by-844 destination layouts.
Do not invent source mobile behavior where no evidence exists.
Require keyboard operation, readable missing-data states, and stable selectors.
Use independently authored synthetic scenarios with no external browser requests.
Run mocked live-mode journeys separately and assert authorization and shared storage behavior.

## Phase 4 - Publication and handoff

Run [quickstart validation](design/quickstart.md), source-to-test coverage, and Spec Kit consistency analysis.
Reconcile shared workflow and portal ownership before any publication.
Preserve other migrations and both rename endpoints.
Use the existing PR template for any authorized update.
Keep PR #4208 draft and auto-merge disabled until acceptance evidence and owner approval exist.
Merge and deployment are separate owner decisions, not automatic results of this workflow.

## Project Structure

This record is the execution entry point. Historical plans remain evidence, not active instructions.
Supporting contracts reside under `design/`.
Future tests use existing `tests/unit/wan_performance/` and `tests/e2e/web_portal/` locations.
Do not create new direct children in a noncompliant package.

## Complexity Tracking

The large shared portal and workflow files are existing structural debt.
Do not restructure them during evidence collection.
Before touching them, record current violations, obtain scoped ownership, and define separate remediation.

## Tool limitations

PowerShell was unavailable during the initial planning review.
A verified session-local PowerShell 7.7.0 runtime now supports read-only prerequisite checks.
The WAN prerequisite check ran with an explicit feature directory and did not update `.specify/feature.json`.
Managed-route allocation and setup scripts remain unexecuted.
The mandatory branch hook was loaded but not executed because this app already owns the feature branch.
Optional commit hooks were not executed.
This record does not claim that the complete Spec Kit command pipeline ran.

## Renewed parity investigation

### Independently designed replacement sequence

The continuation adds T064 ranking, T065 declarations, and T066 historical-import behavior.
Ranking uses only existing cached or selected retained observations. It adds no source request or history query.
Rename inspection/sle.py to inspection/reports.py before adding its fifth module-level name.
Change every import and patch target. Keep no old-path alias.
This changes the SLE logger name and SleResult/SleValidation/SleReader module names, not their behavior or serialized data.
The inspection directory keeps five children. Existing SLE classes retain their tracked structural debt.
Use existing integration/record_codec.py and integration/history_repository.py for archive and declaration classes.
Do not add an integration-directory child. Preserve existing live codec and history behavior.
Live archive writes use atomic non-replacing inserts, not a read-then-overwrite transaction.
The declaration and synthetic archive stores remain isolated process-lifetime state with downloadable artifacts.
No production operation, service, dependency, workflow, or publication change forms part of these increments.

The later user direction permits defensible replacements instead of waiting for absent source evidence.
Use [version-one contracts](design/contracts/replacements.md), and preserve original acceptance states.
T061 records replacement requirements, evidence labels, and future ranking/declaration/backfill policies.
T062 implements observation mean, nearest-rank p95, and configurable percentage-threshold counts over the existing retained view.
Keep old calendar summaries, raw samples, cache exports, and source-parity decisions unchanged.
T063 validates thirteen calendar months with independently authored synthetic records in temporary SQLite and mocked Arango.
Preserve the application codec prohibition on synthetic data.
Use native temporary SQLite payload storage and separate adapter-rejection checks. Mocked Arango proves query guards, not executed persistence.
Do not claim that synthetic storage evidence establishes production retention or deployment capacity.
Each verified commit receives a uniquely named recovery copy with remote SHA verification.
Do not update the existing PR branch or change the publication hold.

The inspection window module already has five top-level classes/constants.
Move its window-choice constant into the existing selection method before adding the replacement statistics class.
Update every internal reference, remove the old declaration, and record the intentional symbol change.
The new report class has at most five methods and introduces no directory or schema.
Existing oversized route/test structures remain recorded debt. Their ownership-approved division remains separate work.

T060 addresses the independently supported portion of P36-P37.
The existing selected-gateway discovery retains the `stats_gateway` payload in the snapshot cache.
Display `cpu_stat.usage` and `memory_stat.usage` as reported percentages, `uptime` as seconds since boot, and `last_seen` as gateway observation time.
Keep these fields outside historic metrics and CSV exports. Do not derive sampling times, complete counts, HA roles, or CPU histories.
Validate exact tenant/site/MAC/type scope and each optional numeric field independently.
Use the existing inspection table module, live route/template, gateway tests, and browser tests.
No new SDK request, request budget, cache format, database schema, service, or dependency is required.

T059 investigates the original selector's expected site input without copying fixtures or changing original source.
Use independently authored dictionary rows only in a declared private scenario after recording the existing model-input result.
Keep the original methods intact. Record signature failures instead of fabricating missing gateway, port, or peer arguments.
The original production launcher remains outside the isolated examination.

T059 also adds independent rectangular point selection in the existing live template and browser test module.
Use visible plot coordinates, not invented metric conversions. Four keyboard bounds describe percentages of the visible plot.
Pointer capture supports reversed drags and cancellation. Both input paths select inclusive point centers with unchanged metadata.
Keep exact missing values and all table rows. A selected list does not constitute a new metric, aggregate, or history query.
Selection stays within one metric/unit figure. UTC or visibility changes clear it without changing the underlying observation set.
Separate rectangle interaction and selection rendering into two classes with at most five methods each.
The existing figure and test module have structural debt. Do not add files or divide unrelated tests during this increment.
Their future division remains a separate ownership-approved task.

The next bounded destination increment adds independent discrete plots to the existing retained-window view.
It changes `presentation/inspection/windows.py`, `presentation/live_routes.py`, the existing live template, and their existing tests.
The existing feature records, operator guide, and PR fragment record the behavior and evidence.
Reuse the destination SVG chart classes without importing synthetic preview types into live views.
Do not connect points across gaps or merge different units.
Use the existing single scoped history read without collection, raw-sample reads, writes, or new aggregates.

T056 adds independent browser-only controls within the same retained-plot template and existing live browser tests.
The existing live browser test module exceeds five module-level names.
Small semantic journey classes keep new checks readable without dividing unrelated existing tests.
A separate approved follow-up must divide that test module after ownership reconciliation.
Zoom only the visible UTC bucket interval. Bound movement to the selected retained window.
Preserve point values, units, missing buckets, exact collection metadata, and the accessible table.
Offer keyboard controls, reset, exact point inspection, and a local PNG download without a new library or asset.
Do not call the server or change history selection when these controls operate.
Render failures as explicit messages. If JavaScript is unavailable, keep the exact table and a visible limitation.
The operator guide, fragment, and existing evidence records document the change.

The later direct authorization permits isolated original execution and internal captures, not proprietary code or fixture copying.
Use a pinned source archive and independently seeded application provider in an ignored review directory.
Verify absent network egress, absent credential variables, read-only source, and bounded resources before every source process.
Use only a named temporary test container in the project Compose group.
Do not publish container ports or mount production data, credentials, or engine sockets.
If browser access is needed, use an independently authored loopback HTTP relay to the isolated process.
The relay must not provide a general outbound proxy or execute instructions from source responses.
Record original unit-test results separately from independently seeded operator exploration and destination parity tests.

The 2026-11-14 request adds an original-application test cycle and complete operator exploration before further parity acceptance.
The source package explicitly declares a proprietary license. Repository administration does not establish copying or reproduction rights.
Record the rights grant before source execution, fixture imports, or protected captures.
Dependency inspection and independently authored tests can proceed without those actions.

Use the existing comparison rows as the exploration checklist.
After rights approval, replace source fixtures with independently authored normal, empty, missing, stale, and error scenarios.
Block outbound connections before importing source modules. Do not initialize Mist, Snowflake, or production Redis clients.
Run source unit tests separately from the interactive application.
Reject fixtures that require real credentials or connect to an external store.
Bind an authorized preview only to an inspected free loopback port.
Stop each temporary process and remove its exact temporary resources after capture.

Record each control's enabled state, selection, resulting request, navigation, download, chart change, and error.
Record nonfunctional options as failures, not as successful parity.
Cover overview, gateway, encoded port, peer, region, site, SLE, filters, sorting, pagination, exports, and refresh.
Repeat keyboard and browser-history journeys at the three documented viewport sizes.
Keep static observations separate from executed results.

The first independent increment validates the bundled peer-schema MOS bounds of zero through five.
Display a dimensionless score without invented health categories, source sample time, or historical aggregation.
This changes no storage schema, retention policy, network request, or existing record.
Subsequent increments require verified inputs and expected results for each existing task pair.

## Independent destination increments

These increments do not claim source parity and do not close the existing acceptance tasks.
New presentation code enters a compliant `presentation/inspection/` package.
The existing presentation directory has four counted children. This package is its fifth child.
Existing large route and summary modules remain structural debt.
Limit changes there to integration points and the missing-unit repair. Track further module division separately.

Preserve missing unknown-unit records during summary validation and choose a documented display unit when one exists.
Reject genuinely incompatible measured units. Do not rewrite retained records.

The SLE page makes no API call on GET.
An explicit CSRF-protected POST validates site membership from the selected organization's cached records.
Use the existing session transport, organization cooldown, and admission checks before each request.
Read the site catalog first and accept only an enabled supported metric.
A blank metric returns catalog choices only. A selected metric permits one additional impacted-gateway request.
The fixed duration is one hour. Return only the first response page and label completeness as unverified.
Do not calculate scores or infer units for degraded, duration, or total.
Do not persist SLE results or start background collection.

The next independent increment adds cached organization-site navigation and retained observation windows.
Use `presentation/inspection/windows.py` as the inspection package's fifth counted child.
The site selector lists only IDs in the selected organization's cached pages.
Add a scoped cached-site route and preserve the selected window across existing detail links.
Do not fetch a site catalog or invent region membership or site display names.

Support only `6h`, `12h`, `24h`, and `7d` retained-window identifiers.
End each half-open interval at the current UTC hour boundary.
Read at most one exact identity with the existing hourly-history repository.
The maximum interval contains 168 expected hour buckets.
Reject duplicate hours, foreign identities, non-live provenance, and out-of-window results.
Show the hourly projection values and collection times without new aggregation or interpolation.
Count missing retained buckets, but never equate bucket presence with metric completeness or elapsed measurement coverage.
Show an explicit unavailable state for organization/site aggregate history, missing stores, or failed reads.
Keep the current snapshot table and its CSV export explicitly separate from the retained view.
Preserve the existing default summaries when no window is selected.
Do not change storage, start background work, request API history, or backfill missing hours.

The cached table uses independent destination policies.
Filter identity text with a case-insensitive substring. Sort site, gateway, port, or peer identifiers lexically.
Use full identity as the deterministic tie key. Default to site ascending and ten rows per page.
Keep route identity and history scope unchanged when table controls change.
CSV exports include all matching cached rows, not just the visible page.
Include full identity, UTC observation hour, collection time, metric value, unit, missing reason, and provenance.
Neutralize spreadsheet formulas in text fields. Do not export credentials, new API data, or stored historical records.

T057 adds display-only controls in `presentation/inspection/templates/wan_performance/sle.html`.
The existing SLE reader validates at most 1,000 returned rows. Its SDK method provides no page arguments.
Keep that request limit unchanged. Sort only gateway MAC, name, and model text in the browser.
Use case-sensitive lexical order and preserve response order for ties. Keep the original response-order option.
Do not rank or sort unknown-unit measurements.
Display five returned rows per page, with first, previous, next, and last controls.
Keep the complete bounded table accessible when JavaScript is unavailable.
Add responsive browser regressions to `tests/e2e/web_portal/test_wan_performance_live.py`.
Verify unchanged cached organization/site/metric scope, missing values, partial-page labels, and exactly two mocked SDK calls.

T058 follows the authorized source legend and sharing examination.
Change only the existing live template, live browser module, operator guide, PR fragment, and this feature's spec, plan, tasks, analysis, and comparison contract.
Add one independent visibility control per existing retained metric/unit plot.
Use a stable button with an explicit pressed state, keyboard operation, and a disabled no-script state.
Hide only rendered circles. Preserve values, missing reasons, fixed vertical extent, UTC zoom, other figures, and the exact table.

Do not treat operator-hidden points as missing observations.
Reset changes only the UTC view. A hidden plot's PNG identifies the operator's visibility choice.
Move point rendering and inspection into a small subject class to keep the existing chart methods within 25 lines.
Test two separate metric figures, measured zero, missing values, keyboard operation, zoom/reset, actual PNG output, and unchanged requests.

The source cloud workflow requires an external service and remains unexecuted beyond the intercepted launch.
Do not add cloud sharing, external links, clipboard actions, or source implementation to the destination.
