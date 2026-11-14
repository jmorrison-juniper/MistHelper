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

The cached table uses independent destination policies.
Filter identity text with a case-insensitive substring. Sort site, gateway, port, or peer identifiers lexically.
Use full identity as the deterministic tie key. Default to site ascending and ten rows per page.
Keep route identity and history scope unchanged when table controls change.
CSV exports include all matching cached rows, not just the visible page.
Include full identity, UTC observation hour, collection time, metric value, unit, missing reason, and provenance.
Neutralize spreadsheet formulas in text fields. Do not export credentials, new API data, or stored historical records.
