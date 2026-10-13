# Implementation Plan: Mist WAN Performance

**Worktree Branch**: `jmorrison-jnpr-mist-wan-performance-plan` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: `specs/live/20261013-182629-mist-wan-performance/spec.md`

## Summary

Plan the four completed dashboard journeys inside the current Flask portal.
Use a feature blueprint and the existing navigation, Mist session, storage configuration, and access controls.
Preserve historical behavior without a Snowflake connection or another application database.

This branch contains planning documents only.
Do not run the implementation workflow, create product files, deploy services, or migrate data.
All future tasks remain unchecked.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing Flask, Jinja, `mistapi>=0.64.0,<0.65`, and current database clients.
Chart technology requires an existing-dependency review before selection.
Do not start a separate Dash server or introduce a CDN dependency.

**Storage**: Use the existing configured persistence and export selection for durable WAN records.
Use the current SQLite file when SQLite is selected, or the existing ArangoDB database when that mode is selected.
Redis remains an optional cache, not another authoritative application database.
Do not add or select a second application database.
When no supported durable database is configured, report historical storage unavailable instead of implying that CSV is durable history.

**Testing**: Existing pytest, Flask test-client fixtures, and Playwright.
Synthetic fixtures require no production credentials or Snowflake connection.

**Target Platform**: Windows 11, macOS, Linux, and the existing Podman deployment.

**Project Type**: Existing portal feature, not a new application or service.

**Performance Goals**: One active refresh owner per organization.
No cloud request occurs during page rendering.
The proposed refresh bounds are in [the contract](contracts/wan-performance.md).
Measure page timing and record counts before selecting a release performance target.

**Constraints**: One shared application database, current Compose group, current public ports, and current portal access controls.
Rights and exact data contracts are release prerequisites.

**Scale/Scope**: Four page journeys, hourly records, three calendar summaries, and five user stories.
Organization size and source history coverage remain unmeasured.

## Constitution Check

### Before research

- Planning-only scope passes. The issue exists with `feature`, `web-portal`, and `in-progress` labels.
- The app-created worktree branch is retained. The branch hook ran in dry-run mode instead of creating another branch.
- For later implementation, create `feat/4200-mist-wan-performance` from current `main`. This planning worktree uses the app-managed branch.
- The timestamp record uses the managed `specs/live/` root.
- No product hierarchy, runtime, database, container, or port changes occur in this PR.
- No proprietary source code or visual assets are copied.
- Existing portal access controls are address allowlisting, CSRF protection, and response headers, not user authentication.
- Mist transport uses the existing SDK session. No owned HTTP or WebSocket transport is proposed.

### After design

- Planning may proceed. Implementation remains blocked by T001 through T010 and explicit approval.
- Exact SDK method parity, pagination, retry accounting, and field units require tests before the transport gate passes.
- The current quota cache is process-local. It does not prove cross-worker or cross-operation coordination.
- Durable history uses the existing configured persistence and export selection. Do not bypass its selected durable backend or create a second database.
- Cache expiry must not control durable-history expiry.
- Source screenshots remain reference links until reuse rights are confirmed.
- The standard Spec Kit document set exceeds five direct children in a feature record.
  This plan records that process-record exception without changing the repository baseline.
- Existing `web_portal/routes/` and `web_portal/services/` exceed five Python children.
  Do not add feature modules to those parents.
- T004 measures all future touched parents. T055 tracks incremental hierarchy remediation in a separate maintenance issue without restructuring unrelated modules in this feature.
- Runtime outputs remain under `data/`. Test evidence uses ignored `test-artifacts/`.
- The PR title and final commit use `docs(spec): plan MistWANPerformance portal migration`.
- Deployment, merge, and the implementation workflow remain outside this planning-only authorization.

### Workflow execution notes

The PowerShell setup command cannot run because `pwsh` is absent on this host.
Use the installed templates directly and the explicit feature path.
Do not install another platform tool only to copy templates.
The feature pointer is temporary and returns to its original value before the final commit.
No generated technology-context file enters the PR.
Optional commit hooks are deferred to one final planning commit.
Disabled companion hooks do not run.

## Project Structure

### Documentation (this feature)

```text
specs/live/20261013-182629-mist-wan-performance/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  tasks.md
  analysis.md
  checklists/requirements.md
  contracts/wan-performance.md
```

### Source Code (future implementation only)

```text
src/interfaces/portals/wan_performance/
  domain/       # Identity, measurements, and aggregation
  integration/  # Existing session, selected store, cache, and refresh
  presentation/ # Blueprint, templates, charts, and selectors
web_portal/app.py
web_portal/templates/base.html
src/mist/access/api/
tests/unit/wan_performance/
tests/contract/wan_performance/
tests/integration/wan_performance/
tests/e2e/wan_performance/
documentation/wan-performance.md
changelog.d/issue-4200-wan-performance.md
```

**Structure Decision**: Keep the feature in a compliant nested package under the existing portal package.
Register its blueprint in the current app factory.
Reuse base navigation without new direct children in crowded route or service packages.
The future API coordination integration must extend existing quota ownership, not create a separate WAN request allowance.
T004 must verify parent counts before this proposed tree becomes final.

## Complexity Tracking

| Constraint | Evidence | Action |
| --- | --- | --- |
| Process document count | Standard Spec Kit record has more than five direct children | Keep one unique record and track remediation in T055 |
| Existing portal package debt | Routes and services already exceed five Python children | Use the nested feature package and measure touched parents in T004 |
| Shared quota state | `api_usage_cache` is process-local | Prove coordinated admission in T009 before refresh code |
| Missing source contracts | Documentation does not prove endpoint or field parity | Resolve T002, T003, T005, T006, and T007 before implementation |
