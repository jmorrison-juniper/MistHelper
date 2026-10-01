# Implementation Plan: Long packet streams

**Branch**: `jmorrison-juniper-long-packet-streams`

**Date**: 2026-10-01

**Spec**: [spec.md](spec.md)

## Summary

Use a dedicated capture runner in the existing WebSockets service.
Confirm the subscription before the SDK capture start.
Keep the connection until completion, stop, failure, or the selected duration.
Check the active capture identity before cloud stop.

## Technical Context

**Language/Version**: Python 3.13 or newer and the existing browser JavaScript.

**Primary Dependencies**: Installed `mistapi` 0.64.0, requests, Flask, and Playwright.
No dependency change.

**Storage**: Existing in-memory session buffers only.

**Testing**: pytest, controlled clocks, fake SDK transports, a local stream,
actual Flask controllers, and Chromium.

**Target Platform**: The existing macOS, Windows, and Linux portal.

**Project Type**: An existing web application.

**Performance Goals**: Return from start and stop without waiting for the capture.
Keep one capture worker per session.

**Constraints**: Durations from 60 through 3600 seconds.
Keep the existing session and memory caps.
Bound subscription waits, HTTP actions, retries, and connection cleanup.

**Scale/Scope**: The existing seven packet utilities.
Other utilities, channel streams, and shells remain unchanged.

## Constitution Check

The change uses semantic classes in a new nested capture package.
Each new source directory has at most five children.
Existing catalog, intake, and manager classes exceed the hierarchy or method limits.
The change edits those existing children without a general refactor.
A separate maintenance change can split those existing classes later.

New helpers use at most five parameters and small methods.
The requests transport boundary retains the library's keyword options.
That boundary must preserve proxy, TLS, authentication, and request behavior.

The user requires rare, meaningful comments and metadata-only logs.
Those current requirements govern this change.
No suppression, exclusion, baseline, shared changelog, or menu count changes.

Publication and protected merge require the parent grant.
Live capture and production deployment remain unauthorized.
This local work does not satisfy those later steps.

## Project Structure

### Documentation

```text
specs/3575-long-packet-streams/
  spec.md
  plan.md
  tasks.md
  checklists/requirements.md
  design/
    research.md
    data-model.md
    contracts.md
    quickstart.md
    spec-context.json
```

### Source Code

```text
src/websocket_streams/live/captures/
  __init__.py
  model.py
  control.py
  transport.py
  runner/
    __init__.py
    driver.py
    lifecycle.py
```

`model.py` owns the checked plan, clocks, events, and capture progress.
`control.py` owns payloads, authorization checks, SDK actions, and response checks.
`transport.py` owns the SDK connection, packet events, and bounded HTTP transport.
`runner/driver.py` owns the worker and capture scope reservation.
`runner/lifecycle.py` owns capture admission, duration, and final actions.
Cloud stop and connection cleanup run independently.

The existing runner factory selects this runner only for packet captures.
The existing checker validates duration before manager or SDK work.
The existing card and polling controller receive normal packet records.
`IntegerFieldValue` owns bounded integer parsing and catalog range checks.

## Phase 0: Research

The installed SDK source confirms the old cutoff and action order.
The bundled specification confirms the capture identity and status shapes.
[research.md](design/research.md) records the exact decisions.

## Phase 1: Design

The existing session retains the public state and message contract.
[data-model.md](design/data-model.md) defines private capture state.
[contracts.md](design/contracts.md) defines order, duration, stop, and cleanup.
[quickstart.md](design/quickstart.md) defines local-only validation.

## SpecKit Execution

The current templates and agent procedures govern the specification, plan,
tasks, implementation, and consistency analysis.
The PowerShell prerequisite command failed because `pwsh` is unavailable.
The branch hook also creates or switches a branch that the app already manages.
Use the user-authorized file-only path.
Do not change `.specify/feature.json` or run a shared specification commit.
Record the stages in the unique [spec-context.json](design/spec-context.json).

## Complexity Tracking

| Existing constraint | Reason for the narrow edit | Later maintenance |
| - | - | - |
| Large catalog and checker classes | They already define the actual form and request checks. | Split one class in a separate issue. |
| Large manager class | The actual session limit, idle stop, and factory live here. | Separate session policy from session ownership. |
| Library keyword boundary | The requests interface controls TLS, proxies, and timeouts. | Keep the upstream interface instead of an adapter shim. |

## Local Verification

The combined local run passed 261 tests without a failure, error, or skip.
The new capture package covered 608 of 650 statements, or 93.54 percent.
The actual Chromium journeys used the real controller, SDK client, and local stream.
Ten additional local SDK cases verify the shutdown order and zero owned workers.
The SDK compatibility guard checked 556 call signatures and reported zero known failures.
It also reported 10 unresolved call sites and 366 unverifiable signatures.
Those repository-wide counts remain explicit, not a claim that every signature is verified.

The runtime audit needs a macOS recovery path.
The standard resolver aborted during `ensurepip`.
UV compiled the complete runtime tree with hashes.
The strict audit then checked that tree without dependency resolution or pip.
The pinned development-only Git package remains outside the runtime audit.
