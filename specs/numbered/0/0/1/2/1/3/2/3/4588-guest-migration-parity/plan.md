# Implementation Plan: Full guest migration parity

**Branch**: `jmorrison-juniper-guest-migration-parity-specification` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

**Input**: `specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity/spec.md`.

## Summary

Plan the full source-to-target migration, including visual parity, without changing current product behavior.
Retain the existing offline projection and integrate future approved workflows into the existing Flask portal.
Use exact scope, the shared SDK session, existing data services, typed confirmations, and truthful outcomes.
The [inventory](design/contracts/parity.md) is the acceptance boundary, not a generic feature list.
The [decision register](design/research.md#decision-register) blocks unapproved implementation.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing Flask, Flask-WTF, Gunicorn, mistapi, and local Bootstrap assets.
The current environment resolved mistapi 0.64.1. Source requirements pin 0.64.0.

**Storage**: Mist remains authoritative for authorizations.
Reuse the existing operational store for approved intent, batch, and audit records.
Keep product output under `data/`. Add no database or Redis service.

**Testing**: pytest unit, contract, integration, and Playwright browser suites.
Use synthetic responses and isolated stores. Do not construct a live Mist session in tests.

**Target Platform**: Existing MistHelper deployment on Windows 11, macOS, Linux, and rootless Podman.

**Project Type**: One feature inside the existing portal, not another application.

**Performance Goals**: Bound CSV and API work through D3 before implementation.
Do not infer a latency, concurrency, or volume target from source code that specifies none.

**Constraints**: Preserve exact scope, privacy, error reporting, offline projection behavior, shared ownership, and the five-child hierarchy.

**Scale/Scope**: One source dashboard, three dialogs, and every feature in the measured parity inventory.
The [E2E matrix](design/contracts/e2e.md) defines fixtures, viewports, and remaining evidence.

## Constitution Check

Planning gate: pass after artifact checks. Product readiness: blocked by D1-D7 where applicable.

| Principle | Planning compliance | Future implementation condition |
| --- | --- | --- |
| Bounded hierarchy | New managed numeric route. Five feature-root children and five design children. | T007 verifies package and test destinations. No added child in an overfull parent. |
| Class-based design | Named scope, observation, change, batch, and audit responsibilities. | T013,T018,T026,T030 enforce small typed methods and no forwarding wrapper. |
| Safety | No live guest data or write is enabled. | D1-D4/D7, exact scope, CSRF, confirmation, no ambiguous retry. |
| Full pipeline | User explicitly requests planning-only PR and no merge. | Product pipeline follows approved implementation, not this planning PR. |
| Logging and comments | No committed executable code changes. | T029/T030 enforce boundary redaction and meaningful before/after logs. |
| SDK transport | Installed signatures and schema were read offline. | T003 verifies all supported payload and response contracts. No direct REST fallback. |
| Operational store | No source database exists to convert. | D4 defines durable evidence, backup, retention, and fail-closed behavior. |
| Tests and evidence | Current projection and routing checks ran. | T035,T037,T038 execute all future acceptance families. |

Existing `specs/` and process folders have grandfathered debt.
This record uses a bounded managed root rather than adding an unmanaged direct feature.
T007 includes a separate incremental structure remediation proposal, not unrelated restructuring in this PR.
The old source module is an existing direct child. A future package replaces it rather than adding another sibling.
Its class `__module__` and logger name will change during that move.
T009 must document those changes and update every call site without a compatibility shim.

## Project Structure

### Documentation (this feature)

```text
4588-guest-migration-parity/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      parity.md
      api.md
      e2e.md
      source-files.md
    checklists/
      requirements.md
      migration.md
```

### Source Code (repository root)

Proposed paths are future work, not delivered files.

```text
src/interfaces/portals/guest_authorizations/
  __init__.py
  domain/
    __init__.py
    read_model.py
    scope.py
    validation.py
  services/
    __init__.py
    api_client.py
    mutations.py
    imports.py
    audit.py
  web/
    __init__.py
    routes/
    templates/
    static/
```

The package replaces `src/interfaces/portals/guest_authorizations.py`.
Import each symbol from its defining module. Do not re-export it through an alias.
Use `web/routes/` for bounded review, change, and import route groups.
Use `web/templates/` for a page and bounded dialog partials.
Use `web/static/` for one feature CSS file and bounded script groups.
This avoids placing more direct files in the existing shared portal folders.

Replace the existing projection test file with the feature's unit-test directory only after the ownership and hierarchy review.
Planned test roots are `tests/unit/web_portal/guest_authorizations/`,
`tests/contract/web_portal/guest_authorizations/`,
`tests/integration/web_portal/guest_authorizations/`, and
`tests/e2e/web_portal/guest_authorizations/`.
T007 must verify their parents before creation and revise these destinations if they exceed five children.
That is a destination gate, not permission to enlarge a noncompliant parent.

**Structure Decision**: Extend `WebPortalApp`, its shared session/config, and its base navigation after PR #4208 ownership clears.
Register one feature blueprint and use route-presence navigation gating.
Do not create another Flask application, session source, port, database, or Compose stack.
Reuse existing persistence contracts only after D4 verifies transaction and recovery support.

## Phase 0: Research decisions

Source and target pins, source page inventory, rendering, deployment, storage, and tests are recorded in [research](design/research.md).
Current source HEAD equals the old baseline.
The old merged plan is not reused as completeness evidence.
The refreshed inventory includes exact controls, status thresholds, CSV behavior, and backend-only features.
Rights authorization is resolved. Applicable license terms remain.

D1-D7 retain concrete alternatives and task gates rather than unsupported defaults.
Scope fallback, invented success, silent CSV defaults, and inaccessible controls are rejected.
No additional research agent is needed because the direct evidence is already available.

## Phase 1: Design and contracts

The [data model](design/data-model.md) defines identities, state transitions, allowed observations, and proposed coordination.
The [API contract](design/contracts/api.md) records exact SDK candidates, writable fields, and unresolved cloud semantics.
The [E2E contract](design/contracts/e2e.md) defines original-versus-target acceptance.
The [quickstart](design/quickstart.md) separates runnable planning checks from future tests.

Read integration may proceed only after D1 approval and exact-scope contract acceptance.
Write integration additionally needs D2, D4, D7, and the relevant D3/D6 decisions.
The first implementation slice should refactor and preserve the offline projection.
That does not authorize live registration.
Single-guest workflows and CSV use the same reviewed-change and outcome machinery.
A failed batch row must not select broader scope or retry an unknown write.

## Complexity Tracking

| Existing constraint | Narrow treatment | Separate remediation |
| --- | --- | --- |
| Overfull process roots | Add only this routed record. | T007 records a bounded migration proposal outside this PR. |
| Existing portal registration method | One owned registration change after handover. | T007 measures touched block limits and plans extraction where necessary. |
| Existing standalone projection module | Replace with a nested package and update callers. | T009 applies move gates and preserves every public contract. |
| Shared test roots | Validate concrete bounded destinations first. | T007 resolves a compliant route instead of weakening guards. |

No complexity threshold, hierarchy baseline, or analyzer allow-list changes.

## Approval and stopping condition

This workflow ends after planning artifacts, analysis, validation, commit, push, and one planning-only PR.
All future implementation tasks remain unchecked.
The PR does not close #4231 or #4278 and does not merge automatically.
