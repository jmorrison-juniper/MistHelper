# Implementation Plan: Site health dashboard

**Branch**: `jmorrison-juniper-mistsitedashboard-planning` | **Date**: 2026-10-18 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4232 and the later user direction to implement a verified offline slice.

## Summary

Preserve the source dashboard workflows through an independent MistHelper design.
Use the existing Flask portal, configured output backend, and Compose group.
Implement only a normalized service-measurement model in the current slice.
Do not register routes, call Mist, change a database, copy source assets, or deploy.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing Flask, `mistapi>=0.64.0,<0.65`, and standard-library dataclasses.
The current slice adds no dependency.

**Storage**: No storage in the current slice.
Future collected data uses `DataExporter.write_with_format_selection()` and the configured existing backend.
Do not introduce a second database or new Redis requirement.

**Testing**: pytest, pytest-cov, Ruff, Black, mypy, Bandit, Radon, and documentation gates.

**Target Platform**: Windows 11, macOS, Linux, and the existing Podman application.

**Project Type**: Existing Python web application with an isolated domain-model increment.

**Performance Goals**: No extra collection during rendering. Future refresh has one active request per scope and bounded collection.
Use one worker initially and at most three transient retries with capped exponential backoff.
Measure larger workloads before permitting parallel collection.

**Constraints**: No source reuse approval, live credentials, cloud writes, deployment approval, or shared portal-file ownership.

**Scale/Scope**: Eight page workflows, three service categories, worst-100 organization comparison, and paginated site/device/client records.
No measured source latency or production capacity claim exists.

## Constitution Check

Before research, the source license and current portal ownership prevent source reuse and portal registration.
These gates remain failed for those phases. They do not authorize a bypass.
The offline model uses no source expression, external service, transport, or shared file.

After design, the isolated model passes the structural, safety, and dependency checks.
The feature root has five children: specification, plan, tasks, analysis, and design.
The design directory has five children: research, data model, quickstart, contracts, and checklists.
Command-scoped selectors preserve `.specify/feature.json`.

The existing `src/interfaces/portals/` directory already has five children.
Do not add a package there before an approved structure change.
The existing `src/foundation/models/data/` directory has two children before this change and can accept the model.
The existing `tests/unit/dataclasses/` directory has two children and can accept its tests.
The model retains descriptive types, explicit errors, immutable values, and action logs.
The source score helper is not reused.

Existing process folders exceed five children.
Only the required issue-specific release fragment enters `changelog.d/`.
A separate future process-folder migration must reduce this existing debt.
No baseline changes belong to this feature.

The full deployment pipeline conflicts with the explicit no-deployment boundary.
Stop after the permitted local increment and pull request.
Do not merge or enable auto-merge.

All future Mist requests require verified SDK contracts.
The source worst-sites endpoint has no matching typed method in the installed SDK.
That live feature remains blocked, not replaced with a private transport.
No WebSocket transport is needed.

## Project Structure

### Documentation (this feature)

The feature root contains `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The [research](design/research.md) records source evidence and blockers.
The [data model](design/data-model.md) defines normalized values and future keys.
The [quickstart](design/quickstart.md) defines validation.
The [API](design/contracts/api.md) and [portal](design/contracts/portal.md) contracts define future integration.

### Source Code (repository root)

```text
src/foundation/models/data/service_measurement.py
tests/unit/dataclasses/test_service_measurement.py
changelog.d/issue-4232-site-health-measurement.md
```

**Structure Decision**: Add one independent model and one test module to compliant existing parents.
Future portal code needs a separate ownership and hierarchy decision.
Do not edit `web_portal/app.py`, `web_portal/templates/base.html`, `compose.yml`, or another feature's files.

## Phase 0: Research

Inspect the pinned source, all eight templates, source license, dependency declarations, and deployment files.
Verify SDK symbols by import and signature inspection only.
Compare source endpoint behavior with local API documentation.
Record disagreements rather than inventing response fields or permission grants.
See [research](design/research.md).

## Phase 1: Design

The offline model accepts normalized integer counts and distinguishes unavailable values from a measured zero.
The public property returns the exact nondegraded percentage without display rounding.
Future presentation owns rounding and threshold labels.
No API response is accepted directly by this model.

Future dashboard entry is a Site health tab in the existing portal on port 8055.
Reuse portal security middleware and the server-owned SDK session.
Do not claim that an address allowlist provides per-user authorization.
Do not duplicate the existing WAN dashboard.
Obtain its owner's decision before connecting gateway views.

Future data collection must declare natural keys before export.
Use existing SQLite or polyglot storage, not both as new duplicate stores.
Redis is not a source dependency and needs no new feature service.
Validate all scoped records before an atomic snapshot replacement.
Preserve the prior snapshot when collection or persistence fails.
Do not persist private raw responses merely to populate a view.

## Phase 2: Delivery Boundaries

The later user direction permits T010 through T012, the independent offline measurement slice.
All live, protected-reuse, shared-file, and deployment tasks remain unchecked.
The dedicated pull request must distinguish the completed planning workflow from this limited implementation.
Reference #4232 without claiming that the entire dashboard migration is complete.

## Complexity Tracking

| Constraint | Decision | Follow-up |
| --- | --- | --- |
| Full portal parent | No new portal child | Obtain a hierarchy and ownership plan before T013 |
| Process-folder debt | Add only the required unique fragment | Track incremental process migration separately |
| Live API contract gap | Block organization worst-sites collection | Resolve B02 before T015 |
| Deployment pipeline | Honor the user's no-deployment boundary | Require separate release approval |
