# Implementation Plan: Migrate Mist Guest Authorizations

**Branch**: `jmorrison-juniper-refresh-guest-migration-spec` | **Date**: 2026-10-18 | **Spec**: [spec.md](spec.md)

**Input**: Existing issue #4231, implementation issue #4278, historical checkpoint `20cf234e2`, and merged PR #4279.

## Summary

Refresh the existing migration record without product changes.
Plan independently authored guest review and access workflows inside the existing portal.
Keep every guest-data route and workflow blocked until the five gates in [research](design/research.md) pass.
Do not treat the existing offline projection as a deployed guest portal.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing Flask application and authenticated Mist session.
MistHelper permits `mistapi>=0.64.0,<0.65`. This worktree resolved version `0.64.1`.
Future contract evidence must pin the actual tested version and dependency revision.
The source separately pins `mistapi==0.64.0`, Flask `3.1.3`, and python-dotenv `1.2.4`.

**Storage**: Existing database and Redis services only. No authorization snapshot, second database, or second application.
The portal uses Redis for existing webhook ingestion and backend checks. This does not justify guest caching.
Do not add guest keys, retention, or Redis authorization decisions without a separate approved requirement.

**Testing**: Offline pytest unit, contract, Flask integration, and browser tests.
Use fictional data, mocked SDK responses, stable test identifiers, and failed-browser traces or screenshots.

**Target Platform**: Windows 11, macOS, Linux, and the existing Podman deployment.

**Project Type**: Existing web portal migration.

**Performance Goals**: No invented response-time threshold. Imports remain sequential with approved byte, row, and bounded-request budgets.
Record measured scope and an approved request budget before connecting live reads.

**Constraints**: Exact scope, approved access control, typed confirmation, minimized audit, no direct REST fallback, and no automatic uncertain-write retry.
CSV values, audit recovery, final duration rules, and identity decisions remain unapproved.

**Scale/Scope**: One selected organization with explicit site and WLAN scope.
Discovery must not imply organization-wide write permission.
No new menu, credential setting, service, or port is planned.

## Constitution Check

| Gate | Before research | After design |
| --- | --- | --- |
| Managed route | Same numeric identity and eight base-5 segments | Pass for planning |
| Five-child limit | Historical root layout exceeded the limit | Supporting files grouped under `design/`, checklist path preserved |
| Safety | No cloud action permitted in this refresh | All portal work blocked by G1-G5 |
| SDK transport | Only working `mistapi` methods permitted | Signatures inspected, runtime request/response evidence still blocked |
| Privacy | No source data, credentials, or personal fixtures imported | Masked projection remains offline |
| Rights | Source declares CC BY-NC-SA 4.0 | No source code, assets, screenshots, or tests reused |
| Deployment | No product or Compose changes | No build, merge, deployment, or auto-merge authorized |

**Result**: Planning may proceed. Operational integration fails the gate until G1-G5 have approved, verified evidence.
This is not a waiver of a failed operational gate.

Existing process-folder debt remains outside this issue.
Incremental remediation: group this record's supporting files under `design/` instead of restoring its oversized historical root.
No shared baseline or instruction file changes.

## Phase 0: Research

[Research](design/research.md) separates observed source behavior, current main, historical assumptions, and unresolved decisions.
It records the source commit, license, deployment, dependency differences, scope risks, and approval owners.
No research result substitutes for maintainer approval.

## Phase 1: Design and Contracts

[Data model](design/data-model.md) defines transient scope, observations, imports, and audit outcomes.
[API contract](design/contracts/mist-api.md) records candidate signatures and required request/response evidence.
[Portal contract](design/contracts/portal.md) defines conditional journeys, confirmation binding, access tests, and failure states.
[Quickstart](design/quickstart.md) separates runnable current checks from future blocked checks.

Reuse the existing projection only within its verified three-field contract.
Do not add a route, persistence, or new fixture implementation in this planning change.
Additional offline work may be proposed later, but it must have an independent requirement and explicit issue scope.
The already merged projection removes any need to invent another preparatory product increment now.

## Project Structure

### Documentation

```text
4231-mist-guest-authorizations/
  spec.md
  plan.md
  tasks.md
  checklists/
    requirements.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      mist-api.md
      portal.md
```

The root has five children. `design/` has four. The feature selector stays command-scoped.
Do not change `.specify/feature.json` or the shared agent context.
Read-only analysis reports appear in the PR, not as a sixth root child.

### Source Code

Current completed files remain unchanged:

- `src/interfaces/portals/guest_authorizations.py`
- `tests/unit/web_portal/test_guest_authorization_read_model.py`

Future implementation first claims a compliant nested package and test locations after all gates pass.
The task plan names proposed files, not existing implementation.
Shared portal registration and navigation require a fresh ownership check and explicit handover.
At inspection, PR #4208 owns `web_portal/app.py` and `web_portal/templates/base.html`.

## Complexity Tracking

No exception is requested. No production code changes.
Future package allocation must pass the nested-package guard before its first source commit.
The source path and class module values remain unchanged in this refresh.
