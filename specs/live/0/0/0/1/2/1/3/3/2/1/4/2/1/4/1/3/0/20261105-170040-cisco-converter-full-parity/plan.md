# Implementation Plan: Cisco Converter Full Observed Parity

**Branch**: `jmorrison-juniper-cisco-converter-full-parity-spec` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

**Input**: This new managed timestamp record. Use its explicit directory, not the issue-4224 selector.

## Summary

Complete every observed converter journey with independently authored behavior.
Preserve the offline DNS contract and existing MistHelper portal services.
Add structured review, hardware contracts, proposals, controlled writes, administration, recovery, and visual parity in separate verified stages.
The current assignment creates these documents only.
The future implementation tasks remain unchecked.

## Technical Context

**Language/Version**: Python 3.15 or later. Current worktree interpreter: 3.15.2.

**Primary Dependencies**: Existing Flask portal, CSRF protection, `mistapi` 0.64.1, and existing portal theme services.

**Storage**: Transient upload/review by default. Private files and backups remain under `data/`.
Reuse existing ArangoDB/Redis services only when the approved operation-record design requires them.
Do not add a separate database, Compose project, or credential source.

**Testing**: Existing pytest and Playwright tools. Independent unit, contract, integration, edge-case, and browser fixtures.

**Target Platform**: Existing MistHelper portal on Windows, macOS, Linux, and its Podman deployment.

**Project Type**: Existing portal feature, not a standalone converter application.

**Performance Goals**: Preserve bounded request handling at exactly 16 MiB.
Apply page limits and bounded retries. No new latency promise has owner evidence.

**Constraints**: No copied source expression, live test credentials, automatic cloud writes, or unknown-result retry.

**Scale/Scope**: Forty coverage rows, 24 source routes, eight source test categories, five user journeys.
The comparison defines the capability boundary rather than an arbitrary DNS-only milestone.

## Constitution Check

| Principle | Pre-design decision | Post-design result |
| --- | --- | --- |
| Managed structure | New timestamp path, five children maximum | Record layout passes independent parent check |
| Class structure | Future behavior uses descriptive classes and bounded functions | Implementation gates remain pending |
| Safety | Exact confirmation, stable scope, complete backup, and refusal tests | Defined in contracts, not yet implemented |
| Transport | Existing mistapi only, no custom HTTP/WebSocket | Signatures inspected, payload tests pending |
| Secret protection | Redact at boundaries and keep private records server-side | Test tasks remain pending |
| Deployment pipeline | No code or release fragment changed in this assignment | Publication prohibited by the current request |
| Existing services | Preserve portal routes, health, authentication, and data ownership | Integration-owner approval remains pending |
| Source license | Observation only and independent authorship | Legal review remains a release gate |

No implementation gate is declared passed.
Missing API or permission evidence blocks the affected write, not documentation planning.

## Project Structure

### Documentation (this feature)

```text
20261105-170040-cisco-converter-full-parity/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      portal.md
      mist.md
    checklists/
      requirements.md
```

### Source Code (repository root)

Future changes belong in the existing feature-owned `src/interfaces/portals/cisco_config_converter/` package.
Use compliant child packages for input, parsing, mapping, execution, and presentation behavior.
The implementation owner must resolve the exact bounded layout before adding code.
Do not add direct modules to a parent with five existing children.
Existing package children must be counted, including `__init__.py`.

Existing feature tests are under `tests/unit/gateway/overrides/`, `tests/integration/web_portal/cisco_config_converter/`, and `tests/e2e/web_portal/`.
New contract tests belong in a compliant feature-owned subtree under `tests/contract/`.
Task paths identify proposed files, not an authorization to modify them now.

Only the integration owner may change `web_portal/app.py`, shared navigation, shared request handling, or Compose wiring.
No agent may examine or edit another owner's dirty worktree.
A later explicit handover must precede any shared-file change.

**Structure Decision**: Keep all current artifacts in this new record.
Use explicit feature selection for later commands and leave the tracked selector unchanged here.
The existing process-folder baseline remains untouched.

## Phase 0: Research

Use [research](design/research.md) for revision-pinned source facts and all coverage decisions.
Distinguish observed documentation, route presence, component implementation, and executed evidence.
Do not import source tests or infer production readiness from source route names.

## Phase 1: Design and Contracts

Use [data model](design/data-model.md), [portal contract](design/contracts/portal.md), and [cloud contract](design/contracts/mist.md).
The portal contract preserves current preview/review/export behavior.
The cloud contract names candidate methods and the evidence needed for each write.
The quickstart separates current evidence commands from future acceptance commands.

## Implementation Sequence

1. Obtain implementation ownership and legal decisions. Refresh default-branch evidence without accessing dirty peer work.
2. Define independent contracts, fixtures, private storage, and failure states before adding behavior.
3. Complete input review, roles, hardware, conversion families, proposals, and offline visual journeys.
4. Complete read-only cloud discovery, backups, and operation records with simulated responses.
5. Complete apply, administration, and recovery only after their contracts and owner approvals pass.

Shared integration follows feature acceptance and an explicit owner handover.
Final browser acceptance must use the real portal factory, not only the isolated blueprint fixture.
No deployment or live write follows this documentation task.

## Approval Gates

| Gate | Required evidence | Work blocked |
| --- | --- | --- |
| G1 Legal | Owner/legal decision for reuse, independent-authorship review, and distribution constraints | Any reuse and release |
| G2 API | Current OpenAPI fields, installed signatures, model data, and independent contract tests | Each unverified mapping and write |
| G3 Integration owner | Explicit ownership and shared-file handover | Portal and shared-service changes |
| G4 Cloud owner | Approved operation families, roles, scope, and recovery policy | Enabling apply, restore, delete, or unassign |
| G5 Operator | Current proposal, exact typed word, permission, and backup evidence | Each individual cloud write |

## Complexity Tracking

The current root and historical process folders contain existing structural debt.
This change adds no direct root child or historical record child.
Future implementation must inventory touched package and class violations before editing.
Task T004 requires incremental remediation inside the converter-owned package.
Do not restructure unrelated portal modules to satisfy a converter task.
