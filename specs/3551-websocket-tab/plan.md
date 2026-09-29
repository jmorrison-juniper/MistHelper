# Implementation Plan: WebSockets tab in the Operations portal

**Branch**: `feat/3551-websocket-tab` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/3551-websocket-tab/spec.md`

## Summary

The Operations portal gets a new WebSockets tab. The tab lists every WebSocket stream that the `mistapi` SDK gives for the Mist API. An operator picks a stream, fills in the fields, and starts a session. The server holds the Mist connection and relays each message to the page.

The design has two parts:

- A new package `src/websocket_streams/` holds the catalog, the request checks, the live sessions, the SDK runners, and a small Flask blueprint. The lint, type, complexity, and coverage gates read this package.
- The portal in `web_portal/` gets one navigation item in `base.html` and three lines in `app.py`. The lines register the blueprint and stop every session when the portal stops.

The engine drives the SDK in three ways:

1. The channel runner uses the SDK WebSocket client for the 18 channels.
2. The utility runner calls the SDK device utilities for 52 utilities. This count includes 7 packet captures.
3. The shell runner uses the SDK shell session for the 2 remote shells.

The page asks the server for new messages once each second. Each request answers at once, so no request holds a server thread. Two environment flags lock the 9 state-changing utilities and the 2 shells. Both flags are off by default.

## Technical Context

**Language/Version**: Python 3.13 or newer. JavaScript ES2017 in the browser, with no build step.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65` for the WebSocket client, the device utilities, and the shell session. Flask 3 with `flask-wtf` for the blueprint and the CSRF check. Bootstrap 5 from the portal vendor folder. The feature adds no new package.

**Storage**: Memory only. Each session holds a bounded message buffer. No database, no file, and no Redis key.

**Testing**: pytest for the unit and the contract tests. Playwright for the browser tests in `tests/e2e/`. The tests use a fake SDK layer, so no test opens a Mist connection.

**Target Platform**: The misthelper container on Linux with Gunicorn, and Windows 11 for local development.

**Project Type**: A web service. The feature adds one tab to an existing Flask portal.

**Performance Goals**: The page shows a message no later than 2 seconds after the server receives it. With 5 live sessions at 10 messages each second, other portal pages answer in less than 1 second for 95 percent of the requests.

**Constraints**: Gunicorn runs 1 worker with 24 threads. No request holds a thread for more than 5 seconds. The buffers of 5 full sessions use 40 MB or less. The page CSP allows `connect-src 'self'` only, so the browser never connects to Mist.

**Scale/Scope**: 18 channels, 52 utilities, and 2 shells, for 72 catalog entries. The default limit is 5 live sessions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Result | Evidence |
| - | - | - |
| I. Five-Item Rule | Pass with one recorded exception | Each new package holds 5 children or fewer. The only new child of a noncompliant parent is `src/websocket_streams/`. See Complexity Tracking. |
| II. Class-Based Architecture | Pass | Every behavior lives in a named class. The blueprint view functions call one class method each. |
| III. Safety-First | Pass | The server checks each identifier and each parameter before a request goes to Mist. Two flags lock the state-changing utilities and the shell, and each run needs the typed device name. |
| IV. Full Deployment Pipeline | Pass | The work follows the pipeline to the container update. The merge happens only after every check passes. |
| V. Observability and Logging | Pass | Each action logs before and after, in ASCII. A logging filter removes the shell address from the SDK log. |
| VI. Inline Comments | Pass | Each executable line carries an inline comment. |
| VII. Action Logging | Pass | Each start, stop, refusal, and end state logs the session key, the target, and the reason. |
| Technology constraints | Pass | The feature uses `mistapi` for every Mist call. It writes no export, so the multi-backend rule does not apply. |
| Security: fix over suppress | Pass | The design adds no suppression. The token and the shell address never reach the page. |
| SpecKit escalation | Pass | The change touches more than 3 files, so this spec, plan, and task list exist. |

The Phase 1 design keeps each result. The recheck found no new exception.

## Project Structure

### Documentation (this feature)

```text
specs/3551-websocket-tab/
├── spec.md              # The feature specification
├── plan.md              # This file
├── research.md          # Phase 0: decisions and rejected options
├── data-model.md        # Phase 1: entities, states, and checks
├── quickstart.md        # Phase 1: run and check the feature
├── contracts/           # Phase 1: the HTTP contract of the blueprint
├── checklists/          # The specification quality checklist
└── tasks.md             # Phase 2 output, made by the tasks step
```

### Source Code (repository root)

```text
src/websocket_streams/                 # New, 5 children
├── __init__.py                        # Package docstring
├── catalog/                           # New, 5 children: what streams exist
│   ├── __init__.py
│   ├── model.py                       # FieldSpec, ChannelDefinition, UtilityDefinition, and the enums
│   ├── channels.py                    # ChannelCatalog: the 18 channels
│   ├── utilities.py                   # UtilityCatalog: the 54 device utilities and shells
│   └── registry.py                    # StreamCatalog: lookup, flags, and the page payload
├── intake/                            # New, 5 children: what the operator asks for
│   ├── __init__.py
│   ├── identifiers.py                 # IdentifierRules: UUID, MAC, host, port, and name checks
│   ├── fields.py                      # FieldValueChecker: one value against one FieldSpec
│   ├── start_request.py               # StartRequestChecker: a checked StartRequest or a refusal
│   └── pickers.py                     # StreamPickerService: sites, devices, maps, assets, SDK clients, and Mist Edges
├── live/                              # New, 3 children: running sessions
│   ├── __init__.py
│   ├── sessions/                      # New, 5 children
│   │   ├── __init__.py
│   │   ├── buffer.py                  # MessageBuffer: count cap, byte cap, drop count
│   │   ├── record.py                  # StreamSession, SessionState, and the counters
│   │   ├── manager.py                 # StreamSessionManager: limit, lookup, stop, and the reaper
│   │   └── settings.py                # StreamSettings: the flags and the limits from the environment
│   └── runners/                       # New, 5 children
│       ├── __init__.py
│       ├── channel.py                 # ChannelStreamRunner: the SDK WebSocket client
│       ├── utility.py                 # UtilityRunner and CaptureStopper: the SDK device utilities
│       ├── shell.py                   # ShellRunner: the SDK shell session
│       └── text.py                    # MessageShaper, PacketSummary, and ShellAddressFilter
└── web/                               # New, 5 children: the Flask blueprint
    ├── __init__.py
    ├── blueprint.py                   # websockets_bp and the WebSocketsApi view class
    ├── services.py                    # WebSocketsServices: builds and holds the manager for the app
    ├── templates/                     # websockets_page.html
    └── static/                        # websockets.js and websockets.css

web_portal/
├── app.py                             # Edit: register websockets_bp, stop the sessions at shutdown
└── templates/base.html                # Edit: one navigation item

tests/unit/websocket_streams/          # New, 5 children
├── __init__.py
├── catalog/                           # Catalog, SDK parity, and payload tests
├── intake/                            # Identifier, field, start request, and picker tests
├── live/                              # Buffer, manager, and runner tests with a fake SDK
└── web/                               # Blueprint tests with the Flask test client

tests/contract/websocket_streams/      # New: the SDK signature and channel path contracts
tests/e2e/test_websockets_page.py      # New: the browser journey with a fake engine

deploy/.env.example                    # Edit: the flags and the limits
changelog.d/issue-3551-websocket-tab.md # New: the release note
```

**Structure Decision**: The engine and the blueprint live in `src/websocket_streams/`, as `src/upgrade_portal/` did for the capture portal. The lint gates skip `web_portal/`, and the gates must read the new code. The blueprint carries its own `templates/` and `static/` folders. For this reason, the feature adds no child to `web_portal/routes/` (7 children) or to `web_portal/templates/` (5 children).

## Complexity Tracking

| Violation | Type | Why Needed | Simpler Alternative Rejected Because | Remediation |
| - | - | - | - | - |
| One new child `websocket_streams/` under `src/`, which holds 43 children | Grandfathered parent, new child | The repository puts each feature in one top-level `src/` package. Examples are `upgrade_portal`, `ssid_consolidation`, and `juniper_docs`. | `src/websocket/` holds 7 children and imports the CLI manager at import time. A nested package there adds a child to a noncompliant parent and slows each portal import. | Issue #3574 groups the `src/` packages into domain packages. |
| `tests/unit/` holds 148 children, `tests/contract/` holds 11 children, and `tests/e2e/` holds 15 children | Grandfathered parent, new child | Each test tree mirrors its source package. The browser tests live in `tests/e2e/`, where the `gunicorn_server` fixture lives. | A flat file for each test adds more children to the same parents. | Issue #3574 covers the test trees with the source tree. |
