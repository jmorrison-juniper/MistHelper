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
Destination baseline: PR #4208 remote head `fbb23f8a2348e6840caf479dc10d8841635ea91e`. Local candidate: `8552557d635f1e4e3fdcf8c1388ea1370cdf6214`.
Observed remote main: `816f42bac74aebfb936ac9fc9b72fe1ec2030c09`.
These refs are read-only observations. This planning change does not rebase product work.

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

PowerShell is unavailable. Managed-route allocation, setup, and prerequisite scripts were not executed.
The route was calculated from the repository radix algorithm and must pass local structure checks.
The mandatory branch hook was loaded but not executed because this app already owns the feature branch.
No feature pointer was changed. Optional commit hooks were not executed.
This is a manually prepared Spec Kit record, not a claim that the complete command pipeline ran.
