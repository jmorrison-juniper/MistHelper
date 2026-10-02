# Implementation Plan: Own Mist WebSocket Client and Interactive Terminal

**Branch**: `feat/3671-interactive-terminal` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: The feature specification in `specs/3671-interactive-terminal/spec.md`.

## Summary

The portal replaces the WebSocket paths of the Mist software kit with its own client. The
software kit stays for REST requests only. The new client subscribes to a command channel
before it sends the command request, so the first output messages stay (issue #3660). It
gives the raw screen bytes to a terminal emulator in the browser, so a control sequence in
two parts shows correctly (issue #3659).

The device shell becomes an interactive terminal. The page uses xterm.js 6.0.0 from a
vendored file. Each key goes to the device in order. The terminal supports copy by
selection, copy keys, paste keys, a paste confirmation, a right-click menu, and a history
file. The server holds a byte history for each terminal session. The page reads the history
with a long poll and sends keys with short POST requests.

## Technical Context

**Language/Version**: Python 3.13 for the server. JavaScript classes (ES2020) with no build
step for the page.

**Primary Dependencies**:

- `websocket-client>=1.8.0,<2`. The repository pins this package today. The feature adds no
  new Python package.
- `mistapi>=0.64.0,<0.65` for REST requests only. The client reads 4 private attributes of
  the API session. A contract test pins them.
- Flask 3 and Flask-WTF. The global CSRF protection covers each new POST route.
- xterm.js 6.0.0 and the xterm fit addon 0.11.0. Both use the MIT license. The repository
  holds a copy of each UMD build and the license text.

**Storage**: Memory only. Each terminal session holds a byte history of 1 MiB by default.
The browser keeps the terminal preferences in local storage. The portal writes no terminal
data to a disk.

**Testing**:

- pytest unit tests and contract tests.
- A fake Mist cloud server that uses the Python standard library only. It speaks RFC 6455.
- Playwright browser journeys with screenshots under `test-artifacts/websockets-terminal/`.
- Live checks on the lab switch and the lab gateway with read-only commands.

**Target Platform**: The Linux container with Gunicorn in the threaded worker mode. The
Windows workstation for local tests. The page supports current Chrome, Edge, and Firefox.

**Project Type**: A feature of the existing web portal on port 8055.

**Performance Goals**:

- SC-001: The portal adds less than 50 ms to the echo time for 95 percent of keys.
- SC-005: With 5 busy shell sessions, other pages answer within 1 second.
- SC-007: The terminal shows 1 MB of output within 3 seconds on the local test path.

**Constraints**:

- The content security policy allows scripts and connections to the same origin only. The
  page cannot open a WebSocket to Mist. The page cannot load a script from another host.
- Gunicorn runs 24 threads in each worker. A long poll holds one thread. The portal allows
  8 waiting polls at most, and each wait is 25 seconds at most.
- Logs hold no token, cookie, shell address path, key, pasted text, or terminal output.

**Scale/Scope**: 5 live sessions in each portal process. 1 MiB of history for each terminal
session. 256 KiB for each paste. 16 KiB for each input request.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Result | Evidence |
| - | - | - |
| I. Five-Item Rule | PASS | Each new folder holds 5 entries or fewer. Each new class keeps 5 public methods or fewer. The design moves code out of the manager. The branch adds no child to a noncompliant code folder. The tests moved into small packages in commit 40bc8e6e. See Complexity Tracking for the touched debt. |
| II. Class-Based Architecture | PASS | Each feature lives in a named class. The plan adds no wrapper function and no legacy shim. The old line input route goes away. |
| III. Safety-First | PASS | The shell lock and the typed device name stay. The client refuses a shell address without TLS or outside the cloud domain. Each input route checks the session, the size, and the rate. |
| IV. Full Deployment Pipeline | PASS | Every quality gate runs. The pull request adds a release note fragment. Tasks T057 to T061 hold the 12 pipeline steps, which include the container update after the merge. The commit subject uses Conventional Commits, because the title guard requires it. Issue #3720 records the conflict with step 4. |
| V. Observability | PARTIAL | Each connection logs the host, the state, and the byte counts. A test scans the logs for secrets and keys. The new modules use standard logging with fixed templates and `%s` arguments, as the rest of the package does. Issue #3721 decides the structlog move for the package. |
| VI. Inline Comments | PASS | Each executable line gets an inline comment. |
| VII. Action Logging | PASS | Each action logs before and after. Logs for keys and output hold byte counts only. |
| Technology: mistapi sole interface | EXCEPTION | REST requests use mistapi. The WebSocket transport is own code, because the SDK WebSocket paths lose output (#3659 and #3660). The client reads 4 private session attributes, and a contract test pins them. Issue #3718 holds the amendment decision and the return path to the SDK. |
| Security: Fix Over Suppress | PASS | The plan adds no suppression comment. |
| SpecKit Escalation | PASS | This feature uses the full SpecKit flow. |

Re-check after the Phase 1 design: PASS. The data model and the contracts keep each rule.

Re-check after the SpecKit analysis on 2026-10-02: the five-item findings are fixed. The mistapi
exception and the logging style are recorded above, and each one has an issue.

## Project Structure

### Documentation (this feature)

```text
specs/3671-interactive-terminal/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- terminal-http.md
|   |-- transport.md
|   `-- terminal-page.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
src/websocket_streams/live/
|-- __init__.py
|-- runners/
|   |-- __init__.py
|   |-- channel.py          (changed: uses the own stream client)
|   |-- shell.py            (changed: uses the own shell client and the terminal history)
|   |-- text.py             (changed: removes the shell text cleaner)
|   `-- utility/            (new package, replaces utility.py)
|       |-- __init__.py
|       |-- runner.py       (UtilityRunner and CaptureStopper)
|       |-- triggers.py     (UtilityTriggerTable and UtilityRequest)
|       |-- filters.py      (UtilityMessageFilter)
|       `-- screen.py       (ScreenRunner for Top and Monitor Traffic)
|-- sessions/
|   |-- __init__.py
|   |-- buffer.py
|   |-- manager.py          (changed: builds terminal sessions, drops line input)
|   |-- record.py           (changed: holds the terminal state)
|   `-- settings.py         (changed: reads the terminal history size)
|-- terminal/               (new package)
|   |-- __init__.py
|   |-- byte_history.py     (ByteHistory)
|   |-- input_queue.py      (TerminalInput)
|   |-- state.py            (TerminalState and TerminalChunk)
|   `-- gateway.py          (TerminalGateway)
`-- transport/              (new package)
    |-- __init__.py
    |-- endpoint.py         (MistStreamEndpoint, ShellAddressPolicy, and ConnectFailure)
    |-- frames.py           (FrameReader and FrameDecoder)
    |-- stream_client.py    (StreamClient)
    `-- shell_client.py     (ShellClient)

src/websocket_streams/web/
|-- blueprint.py            (changed: adds the terminal, input, and resize routes)
|-- services.py             (changed: calls the terminal gateway)
|-- static/
|   |-- websockets.js       (changed: hands shell and screen sessions to the terminal)
|   |-- websockets_terminal.js   (new: TerminalController and its helper classes)
|   |-- websockets.css      (changed: terminal panel styles)
|   `-- vendor/xterm/       (new: xterm.min.js, addon-fit.min.js, xterm.css, LICENSE, README.md)
`-- templates/
    `-- websockets_page.html     (changed: terminal panel, menu, and dialogs)

tests/
|-- unit/websocket_streams/live/
|   |-- transport/              (new)
|   |   |-- test_ws_endpoint.py and test_ws_frames.py
|   |   |-- clients/            (new: the stream client and shell client tests)
|   |   `-- fake_mist_cloud/    (new: server.py, devices.py, api.py)
|   |-- terminal/               (new)
|   `-- runners/utility/        (new, replaces test_ws_utility_runner.py)
|-- contract/websocket_streams/
|   |-- test_ws_utility_trigger_parity.py   (new)
|   `-- test_ws_sdk_contract.py             (changed: pins the private session attributes)
`-- e2e/websockets_tab/                     (new package)
    |-- __init__.py
    |-- terminal_support.py                 (new: the fake portal harness and the helpers)
    |-- test_websockets_page.py             (moved and changed: the shell card uses the terminal)
    |-- test_websockets_terminal.py         (new: journeys J1 to J22 and the review checks)
    `-- test_websockets_terminal_performance.py   (new: SC-001, SC-005, and SC-007)
```

**Structure Decision**: The new code stays inside `src/websocket_streams/live/`. The top
package already holds 5 entries, so the plan adds no top-level folder. The `live/` folder
grows from 3 to 5 entries. The `runners/` folder keeps 5 entries, because the utility runner
becomes a package. The manager loses the line input code, and the terminal gateway takes the
terminal routes.

The tests follow the same rule. The fake Mist cloud stays next to the transport tests that
use it. The browser tests of the tab go into the new package `tests/e2e/websockets_tab/`.
The move takes `test_websockets_page.py` out of `tests/e2e/`, so that folder keeps 17
entries.

## Complexity Tracking

**Grandfathered debt that the branch touches**:

| Folder | Entries before | Entries after | Remediation |
| - | - | - | - |
| `tests/e2e/` | 17 | 17 | One file moves out, and the new package `websockets_tab/` comes in. The count does not grow. Issue #3722 splits the folder. |
| `changelog.d/` | 57 | 58 | The release note rule adds one fragment for each change. Issue #3720 asks for a constitution rule for process folders. |
| `specs/` | 752 | 753 | The SpecKit rule adds one folder for each feature. Issue #3720 covers this folder too. |

**New design decisions that need a reason**:

| Item | Reason | Simpler option that the plan does not use |
| - | - | - |
| An own WebSocket client instead of the SDK WebSocket paths | The SDK paths lose the first output and split control sequences (#3659 and #3660). | Keep the SDK paths. The operator then sees missing or broken output. Issue #3718 records the exception. |
| Standard logging in the new modules | The rest of `src/websocket_streams/` uses standard logging. One style in one package keeps the logs easy to read. | Move only the new modules to structlog. The package then mixes two log styles. Issue #3721 decides the move for the whole package. |
