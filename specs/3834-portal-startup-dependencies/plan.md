# Implementation Plan: Request-Safe Portal Startup Dependencies

**Branch**: `jmorrison-juniper-startup-dependency-reassessment`

**Date**: 2026-10-06

**Spec**: [spec.md](spec.md)

**Input**: Issue #3834 and `.specify/memory/constitution.md`, version 1.8.0.

## Summary

Replace startup construction with missing collaborators with a request-safe service provider in the existing `app/wiring.py` module.
The default factory installs the provider before route registration. Each authenticated request builds its own service graph.
The provider resolves the operator through `identity.current_session()`. It never installs a shared Mist session in application configuration.
It supplies a configured `DatabaseRouter`, an explicit document-store handle, and a compatible audit service.
The complete `E2EFactoryOverrides` branch returns before any production provider, connector, or bootstrap operation.

Dependency construction alone cannot fix this defect. Existing services use unsupported database and Mist call shapes.
Replace these calls at their current owners. Do not add a compatibility adapter, a router shim, or a direct Mist HTTP transport.
Unavailable capabilities must refuse work. A placeholder result must never establish readiness, persistence, settlement, or comparison success.

This stage creates design documents only. It does not change product code or claim that the runtime defect is fixed.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Flask, flask-wtf, structlog, mistapi `>=0.64.0,<0.65`, python-arango, and redis.
Use current dependencies. Add no package.

**Storage**: Existing ArangoDB capture, run, comparison, settle, and audit records. Redis remains the site-lock store.
Keep existing keys, retention, backup, and output behavior. Add no database schema migration.

**Testing**: pytest unit and integration tests, current route contracts, and Playwright portal journeys.
Use real service classes with strict external doubles. Block network, environment-file loading, production stores, and container startup.

**Target Platform**: Windows 11, macOS, Linux, and the current Podman deployment.

**Project Type**: Flask web application with the `wsgi_capture:app` entry point.

**Performance Goals**: One dependency graph and one owned router per request. No new polling loop or unbounded worker.
No measured latency target exists in this specification. Preserve existing timeouts, page limits, and rate limits.

**Constraints**: No global Mist client, no cross-request service mutation, no fake persistence success, and no production test traffic.
Keep authentication, authorization, write gates, confirmation, locks, audit, and route ownership.
Do not add a direct child to `runtime/` or another noncompliant product parent.

**Scale/Scope**: Four service classes and their existing route consumers. Test two concurrent authenticated operators.
Do not change the primary upgrade driver, sign-in modes, menu registry, dependency versions, or transport ownership.

## Constitution Check

*Pre-research assessment: the proposed request ownership model passes. Construction compatibility requires source research.*
*Post-design assessment: the design passes with the existing debt and implementation prerequisites below.*

| Gate | Design decision |
| - | - |
| I: Five-Item Rule | Reuse existing modules. Replace existing declarations instead of increasing a noncompliant parent's children. |
| II: Class ownership | Put resolution and construction in `PortalServiceProvider`. Do not add forwarding wrappers or compatibility adapters. |
| III: Safety | Authenticate before resolution. Verify required storage before cloud work. Preserve all existing mutation guards. |
| IV: Deployment | This planning request prohibits push, rebase, merge, and auto-merge. Implementation deployment needs a separate authorized stage. |
| V and VII: Logging | Use structured ASCII events before and after resolution and operations. Report safe error types, never dependency contents. |
| VI: Comments | Apply repository code-comment rules during implementation. This stage produces no executable product code. |
| Mist transport | Reuse documented mistapi calls with explicit arguments. Add no REST endpoint or owned WebSocket transport. |
| Durable output | Preserve exports through `DataExporter`. Require durable read-back before an operation or cloud mutation succeeds. |
| Tests | Prove default construction, exact call shapes, refusals, concurrency, redaction, cleanup, and complete E2E isolation. |
| Documentation | Update the existing operator guide and one issue-specific changelog fragment during implementation. |

### Existing hierarchy debt and separate remediation

The measured `runtime/` parent has **nine existing direct functional children**:
`cloud_cache.py`, `containers.py`, `dependencies.py`, `identity.py`, `lock.py`,
`pools.py`, `runs.py`, `server.py`, and `signals.py`.
The package marker `__init__.py` is also tracked. The physical directory therefore has ten tracked files.
No interpretation of the marker makes this parent compliant.

This feature adds **zero direct runtime children**. It does not place a provider in `runtime/dependencies.py`.
That module owns reachability probes and optional container startup, not authenticated request dependencies.

**Separate incremental remediation R-3834-H1**: In a separately specified change, group runtime modules by lifecycle, identity, and coordination.
Move one cohesive group, update every import, and verify public symbols, request ownership, and portal contracts.
Repeat until each parent has at most five children. Do not retain import aliases or compatibility shims.
This remediation is not a prerequisite for the narrow existing-file changes in this feature.

Other existing functional-child counts are `app/`: 9, `capture/`: 9, `upgrade/`: 21, and `compare/`: 7.
The design permits narrow existing-child edits only. Add no file or package under these noncompliant parents.
`audit/` and `settle/` are compliant, but their existing service classes carry member and function-length debt.

The proposed touched modules already have the following declaration and length debt.
Counts exclude imports and measure function spans including documentation.

| Existing module | Top-level declarations | Functions above 25 lines |
| - | - | - |
| `app/wiring.py` | 87 | 18 |
| `app/factory.py` | 108 | 6 |
| `capture/service.py` | 2 | 10 |
| `upgrade/service.py` | 4 | 12 |
| `settle/service.py` | 3 | 8 |
| `compare/service.py` | 5 | 18 |
| `audit/logger.py` | 2 | 5 |
| `app/routes/capture.py` | 134 | 12 |
| `app/routes/upgrade.py` | 205 | 26 |
| `app/routes/comparison.py` | 3 | 3 |

**Separate incremental remediation R-3834-H2**: Record exact touched declarations during task generation.
Replace or restructure each touched noncompliant block without increasing its parent's children.
Keep new classes within five members and new methods within five parameters, five blocks, and 25 lines.
Schedule remaining module decomposition separately. Do not expand this repair into a package-wide comment or formatting change.

`specs/` has 782 existing visible entries. `changelog.d/` has 128.
Required unique feature and release records use the constitution's process-folder exception.
The feature folder also exceeds five children after the required design artifacts arrive.
**Separate incremental remediation R-3834-H3**: Propose a process-folder grouping change with updated generators and guards.
Do not move shared records during this feature. The exception does not authorize product modules or extra indexes.

## Project Structure

### Documentation for this feature

```text
specs/3834-portal-startup-dependencies/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/request-dependencies.md
  checklists/requirements.md
```

`tasks.md` belongs to the next Spec Kit stage. Do not create it during planning.

### Narrow implementation file set

All product paths below start at `src/interfaces/portals/upgrade_portal/`.

| Existing file | Required change |
| - | - |
| `app/wiring.py` | Replace four eager installers with the class-owned provider and request graph construction. Preserve the complete E2E early return. |
| `app/factory.py` | Change only lifecycle integration if required. Preserve no-argument startup and owned-handle teardown. |
| `app/routes/capture.py` | Resolve the request service and map dependency failures before capture work. |
| `app/routes/upgrade.py` | Resolve service start, status, and cancel paths without creating another status route. Preserve mutation guards. |
| `app/routes/comparison.py` | Resolve storage and services through the same request graph. Replace unsupported router reads and updates. |
| `capture/service.py` | Replace unsupported client and write calls with existing capture and persistence contracts. |
| `upgrade/service.py` | Replace unsupported firmware validation, router queries, and writes at their current owners. |
| `settle/service.py` | Bind the real request session and replace assumed checks with existing gate evidence. Refuse unavailable checks. |
| `compare/service.py` | Read actual captures and settle evidence. Refuse failed writes and remove success-shaped placeholder results. |
| `audit/logger.py` | Supply the actual audit interface and align only affected persistence and audit arguments. |

Use existing collection methods for document reads and updates, with parameterized AQL where necessary.
Use `DatabaseRouter.write(data, api_function_name)` for supported routed writes.
Do not extend `DatabaseRouter` with service-specific query, read, or comparison methods.
Do not modify shared strategy or writer modules merely to preserve an invalid service call.

Tests should extend the existing wiring, route-connection, service, comparison-route, and two-operator modules.
Do not add a direct unit-test file to an already noncompliant test parent.
The integration parent currently has two functional children. A new issue-specific nested package can hold at most five children.
Use existing E2E journey files after their current owners release them.
Do not edit the shared E2E record harness or fixture while another pull request owns it.

Operator documentation: `documentation/upgrade_capture_portal.md`.
Release fragment: `changelog.d/issue-3834-portal-startup-dependencies.md`.
The fragment must describe the implemented fix, not a planning-only success.
The existing README reference remains sufficient because this feature adds no operation.

## Phase 0: Research Result

See [research.md](research.md) for source evidence and rejected alternatives.
All design choices have a recorded decision. There is no unresolved design clarification.
Existing placeholder behavior remains an implementation prerequisite, not evidence that the current runtime works.

## Phase 1: Design and Implementation Sequence

1. Establish strict dependency and service-call contracts before replacing startup construction.
2. Add request-owned resolution in existing wiring and preserve the E2E return before production setup.
3. Align affected service calls with real SDK, router, document-store, and audit signatures.
4. Resolve existing routes through the provider and preserve failure, cancellation, guard, and lifecycle behavior.
5. Add default-factory, missing-dependency, request-isolation, integration, and E2E coverage, then update operator documentation and the fragment.

Within step 3, preserve collected-data exports and current document shapes.
Use existing capture assembly and verification instead of writing a minimal service document that lacks the required schema.
Do not fabricate a policy, neighbor, firmware, settlement, or comparison result when an existing reader cannot supply it.
A capability without supported evidence returns an explicit failure and cannot authorize firmware work.

See [data-model.md](data-model.md) for ownership and state.
See [contracts/request-dependencies.md](contracts/request-dependencies.md) for the dependency and HTTP boundaries.
See [quickstart.md](quickstart.md) for runnable validation scenarios and acceptance measurements.

### Implementation acceptance gates

The default-factory tests must execute real service operations with strict external doubles.
Installing four non-null objects or testing only unwrapped route bodies does not satisfy SC-001.
Each supported flow must prove a real SDK or durable-store call and its exact result handling.
Missing storage must produce 503 before cloud work. Missing identity must retain the current authentication refusal.
Two concurrent requests must use distinct sessions and routers. No request may change application service dependencies.
Complete E2E overrides must retain every supplied object and call no production constructor or connector.

### Requirement traceability

| Requirement | Design boundary | Required test evidence |
| - | - | - |
| FR-001 | No-argument factory installs the provider before routes. | Real service operations through default factory and WSGI startup. |
| FR-002 | Registry resolution inside the request. | Each SDK call receives the authenticated operator's session. |
| FR-003 | Request-owned graph, borrowed session, safe error text. | Concurrent isolation, mismatched cookies, and secret-sentinel checks. |
| FR-004 | Validated config and actual router constructor. | Exact constructor arguments and valid router in all four services. |
| FR-005 | Complete E2E early return. | Object identity and zero production constructor or connector calls. |
| FR-006 | Authentication and required storage before service work. | Missing-dependency refusals and zero later cloud mutations. |
| FR-007 | Durable result checks and actual comparison evidence. | Failed writes, cancellation, settlement, and comparison remain failures. |
| FR-008 | External boundary traps before factory import. | Zero live network calls and zero production-store calls. |
| FR-009 | Existing wiring module, no runtime child, separate remediation. | Hierarchy inventory and changed-file check. |

### Planning execution constraints

The requested `.specify/scripts/python/setup_plan.py` does not exist.
The repository provides `setup-plan.ps1`, but this host has no `pwsh`.
Resolve the supplied feature path and use the existing plan template manually. Do not install or replace Spec Kit scripts.

The `before_plan` commit hook is optional and remains unexecuted.
The mandatory `speckit.companion.after-plan` hook is registered, but the installed companion extension is corrupted and disabled.
Attempt the registered command after validation and report its result. Do not invent a successful hook receipt or update its state manually.

## Complexity Tracking

| Existing constraint | Narrow treatment | Separate action |
| - | - | - |
| Runtime has nine functional children | Reuse `app/wiring.py`. Add no runtime child. | R-3834-H1 |
| Existing module and member debt | Replace existing installers and affected blocks. Inventory exact touched members before implementation. | R-3834-H2 |
| Required process records exceed five children | Add only required issue-owned artifacts under the explicit exception. | R-3834-H3 |
| Invalid service interfaces and placeholder results | Change current call sites and verify exact shapes. Reject unavailable evidence. | Feature implementation prerequisite |

No new product hierarchy exception is requested.
