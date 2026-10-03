# Implementation Plan: Own Mist WebSocket Client and Interactive Terminal

**Branch**: `feat/3671-interactive-terminal` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: The feature specification in `specs/3671-interactive-terminal/spec.md`.

## Summary

The portal replaces the WebSocket paths of the Mist software kit with its own client. The
software kit stays for REST requests only. The affected SDK method is
`mistapi.device_utils.__tools.__ws_wrapper.WebSocketWrapper.start_with_trigger`. The new
client subscribes before it sends the command request, so the first output stays (#3660).
It gives raw screen bytes to the browser terminal, so split control sequences work (#3659).

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
- Required contract tests for
  `mistapi.device_utils.__tools.__ws_wrapper.WebSocketWrapper.start_with_trigger`.
  One test proves 0-of-1 early-event retention. One test proves corruption of a control
  sequence split across two frames. The owned transport preserves both inputs.
- A fake Mist cloud server that uses the Python standard library only. It speaks RFC 6455.
- Playwright browser journeys with screenshots under `test-artifacts/websockets-terminal/`.
- Live checks on the lab switch and the lab gateway with read-only commands.

**Target Platform**: The Linux container runs one threaded Gunicorn worker. The process
owns all in-memory terminal state. `container/scripts/start.sh` fixes `--workers 1`, and
`test_start_script_uses_a_single_worker` pins this contract. The Windows workstation runs
local tests. The page supports Chrome 120 or newer and Edge 120 or newer. Firefox support
is outside this feature.

**Project Type**: A feature of the existing web portal on port 8055.

**Performance Goals**:

- SC-001: The portal adds less than 50 ms to the echo time for 95 percent of keys.
- SC-005: Five shells each start a 1 MiB output burst. A barrier holds all five bursts open.
  Each stream sends bytes during each measured load and completes exactly 1 MiB. The browser
  alternates five visible `/websockets` loads with five visible `/operations` loads. All 10
  loads must finish. The nearest-rank p95 selects rank 10 from the 10 loads, and it must be
  less than 1 second.
- SC-007: The terminal shows 1 MiB of output within 3 seconds on the local test path.

**Constraints**:

- The content security policy allows scripts and connections to the same origin only. The
  page cannot open a WebSocket to Mist. The page cannot load a script from another host.
- Gunicorn runs 24 threads in one worker. A long poll holds one thread. The portal allows
  8 waiting polls at most, and each wait is 25 seconds at most.
- The utility-command first-output limit is a fixed 30 seconds. `UtilityTriggerDefinitions`
  owns it. The feature provides no environment override, so the supported range is exactly
  30 seconds. A shell waits until the cloud closes it.
- Logs hold no token, cookie, shell address path, key, pasted text, or terminal output.

**Scale/Scope**: 5 live sessions in each portal process. 1 MiB of history for each terminal
session. 256 KiB for each paste. 16 KiB for each input request. Input and resize share 60
requests per monotonic second. Resize accepts 20 to 500 columns and 5 to 200 rows.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Result | Evidence |
| - | - | - |
| I. Five-Item Rule | PASS | Each new folder holds 5 entries or fewer. Each new class keeps 5 public methods or fewer. The design moves code out of the manager. The branch adds no child to a noncompliant code folder. Task T062 moved the tests into the small packages `tests/e2e/websockets_tab/`, `tests/unit/websocket_streams/live/transport/fake_mist_cloud/`, and `tests/unit/websocket_streams/live/transport/clients/`. See Complexity Tracking for the touched debt. |
| II. Class-Based Architecture | PASS | Each feature lives in a named class. The plan adds no wrapper function and no legacy shim. The old line input route goes away. |
| III. Safety-First | PASS | The shell lock and the typed device name stay. The client refuses a shell address without TLS or outside the cloud domain. Each input route checks the session, the size, and the rate. |
| IV. Full Deployment Pipeline | PENDING | Local gates ran, and the release note exists. T057 through T061 remain open for the commit, rebase, pull request, required checks, merge, image verification, and local container update. This row cannot pass before the deployed container health check. |
| V. Observability | PASS | The feature uses one shared structured logger. Each record is ASCII JSON. The logger permits bounded safe fields and redacts secrets at the boundary. `test_records_are_ascii_json_with_only_bounded_safe_fields`, `test_sensitive_fields_are_redacted_at_boundary`, and `test_safe_text_values_redact_embedded_secrets` pass. The focused logging file reports 15 passed tests. |
| VI. Inline Comments | PASS | Each executable line gets an inline comment. |
| VII. Action Logging | PASS | Each action logs before and after. Logs for keys and output hold byte counts only. |
| Technology: mistapi REST and owned WebSocket transport | PASS | REST requests use mistapi. The 8-test SDK contract file passes. `test_trigger_order_controls_early_command_event_retention` checks 1 early event and proves 0-of-1 SDK retention and 1-of-1 owned retention. `test_split_screen_sequence_requires_owned_byte_retention` checks 2 frames and proves SDK corruption. The owned transport preserves both frames. |
| Process-record exception | PASS | Constitution 1.7.0 permits this unique feature folder and release-note fragment. Complexity Tracking records existing `specs/` and `changelog.d/` debt. Issue #3750 will restructure the existing process-folder debt. |
| Generated evidence exception | PASS | Constitution 1.7.0 permits screenshots under the established git-ignored `test-artifacts/` folder. Product outputs remain under `data/`. |
| Security: Fix Over Suppress | PASS | The plan adds no suppression comment. |
| SpecKit Escalation | PASS | This feature uses the full SpecKit flow. |

Re-check after the Phase 1 design: PASS for observability and the owned WebSocket
exception. The data model and transport contracts keep the authentication,
endpoint, safety, and redaction rules.

Final re-check for T084 on 2026-10-03: PASS for the feature gate set and the focused
proofs. The final T083 analysis checked all 45 requirements and 92 tasks. It reported no
actionable finding. Principle IV remains PENDING until T057 through T061 finish. Research
R20 records the final results and the existing platform-specific exceptions. T092 owns the
last pre-commit checkpoint.

The merge does not wait for issues #3718 and #3721. The owner gave a standing instruction to
merge the work that is ready. The final report names both issues for an owner decision.

## T081 Convergence Evidence

All commands used the worktree interpreter at `.venv\Scripts\python.exe`.

| Gate | Exact test and command | Result |
| - | - | - |
| Structured logging | `test_records_are_ascii_json_with_only_bounded_safe_fields`, `test_sensitive_fields_are_redacted_at_boundary`, and `test_safe_text_values_redact_embedded_secrets`. Command: `python -m pytest tests\unit\websocket_streams\live\transport\runtime\test_structured_logging.py -q`. | PASS. 15 passed. The records parse as JSON, stay ASCII, use bounded safe fields, and redact tokens, cookies, shell paths, keys, pasted text, and terminal output. |
| Owned WebSocket exception | `test_trigger_order_controls_early_command_event_retention` and `test_split_screen_sequence_requires_owned_byte_retention`. Command: `python -m pytest tests\contract\websocket_streams\test_ws_sdk_contract.py -q`. | PASS. 8 tests passed. The first contract checks 1 early event. The second contract checks 2 split frames. |
| Structural guard | `test_bounded_bad_fixture_fails`, `test_unreadable_input_fails`, and `test_current_feature_obeys_structural_limits`. Command: `python -m pytest tests\unit\websocket_streams\live\transport\runtime\test_ws_feature_structure.py -q -s`. | PASS. 3 passed. The guard checked 27 mappings, 25 analyzed paths, 145 modules, 204 classes, and 619 functions. The red fixture failed at 6 module children. The unreadable-input fixture also failed. |

## Project Structure

### Documentation (this feature)

```text
specs/3671-interactive-terminal/
|-- spec.md
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
|   |-- channel/            (retry, routing, and runner leaf modules)
|   |-- shell/              (lifecycle, modes, and runner leaf modules)
|   |-- text/               (message, packet, and redaction leaf modules)
|   `-- utility/
|       |-- filters/        (early buffer and message filter)
|       |-- runner/         (capture, execution, monitoring, and runner)
|       `-- triggers/       (models and trigger table)
|-- sessions/
|   |-- __init__.py
|   |-- buffer/             (encoding, message, page, and buffer leaf modules)
|   |-- manager/            (contracts, factory, lifecycle, and operations)
|   |-- record/             (lifecycle, output, session, and state)
|   `-- settings.py         (changed: reads the terminal history size)
|-- terminal/               (new package)
|   |-- __init__.py
|   |-- byte_history.py     (ByteHistory)
|   |-- input_queue.py      (TerminalInput)
|   |-- state/              (size, state, and chunk payload leaf modules)
|   `-- gateway.py          (TerminalGateway)
`-- transport/              (new package)
    |-- __init__.py
    |-- endpoint.py         (MistStreamEndpoint, ShellAddressPolicy, and ConnectFailure)
    |-- runtime/            (frame decoder, reader, and structured logging)
    |-- stream_client.py    (StreamClient)
    `-- shell_client.py     (ShellClient)

src/websocket_streams/web/
|-- blueprint/              (route and response leaf modules)
|-- services/               (assembly, operations, picker, and registry leaf modules)
|-- static/
|   |-- websockets.js       (changed: hands shell and screen sessions to the terminal)
|   |-- terminal/           (controller, input, clipboard, menu, paste, and preferences)
|   |-- websockets.css      (changed: terminal panel styles)
|   `-- vendor/xterm/       (new: xterm.min.js, addon-fit.min.js, xterm.css, LICENSE, README.md)
`-- templates/
    `-- websockets_page.html     (changed: terminal panel, menu, and dialogs)

tests/
|-- unit/websocket_streams/live/
|   |-- transport/
|   |   |-- runtime/            (frame, logging, and structural tests)
|   |   |-- clients/            (stream client and shell client tests)
|   |   `-- fake_mist_cloud/    (server.py, devices.py, and api.py)
|   |-- terminal/               (new)
|   `-- runners/utility/        (utility and screen runner tests)
|-- contract/websocket_streams/
|   |-- test_ws_utility_trigger_parity.py   (new)
|   `-- test_ws_sdk_contract.py             (SDK insufficiency and private field contracts)
`-- e2e/websockets_tab/                     (new package)
    |-- __init__.py
    |-- terminal_support.py                 (new: the fake portal harness and the helpers)
    |-- test_websockets_page.py             (moved and changed: the shell card uses the terminal)
    |-- test_websockets_terminal.py         (new: journeys J1 to J22 and the review checks)
    `-- test_websockets_terminal_performance.py   (new: SC-001, SC-005, and SC-007)
```

**Structure Decision**: The new code stays inside `src/websocket_streams/`. The final
convergence replaces each noncompliant module with a package of named leaf classes. Each
replacement `__init__.py` contains a docstring only. The structural guard checks the 25
analyzed Python paths, one support mapping, and one JavaScript mapping.

The tests follow the same rule. The fake Mist cloud stays next to the transport tests that
use it. The browser tests of the tab go into the new package `tests/e2e/websockets_tab/`.
The move takes `test_websockets_page.py` out of `tests/e2e/`, so that folder keeps 18
entries.

## Complexity Tracking

The counts below come from `origin/main` at commit 0d1cfffb on 2026-10-02, with the
branch rebased onto that commit.

**Grandfathered debt that the branch touches**:

| Folder | Entries before | Entries after | Remediation |
| - | - | - | - |
| `tests/e2e/` | 18 | 18 | One file moves out, and the new package `websockets_tab/` comes in. The count does not grow. Issue #3722 splits the folder. |

**Touched structural violations from the final analysis**:

| Original path | Remediation |
| - | - |
| `src/websocket_streams/catalog/registry.py` | T085 replaced it with a compliant package. |
| `src/websocket_streams/catalog/utilities.py` | T085 replaced it with a compliant package. |
| `src/websocket_streams/intake/fields.py` | T086 replaced it with a compliant package. |
| `src/websocket_streams/intake/identifiers.py` | T086 replaced it with a compliant package. |
| `src/websocket_streams/intake/pickers.py` | T086 replaced it with a compliant package. |
| `src/websocket_streams/intake/start_request.py` | T086 replaced it with a compliant package. |
| `src/websocket_streams/live/runners/channel.py` | T087 replaced it with a compliant package. |
| `src/websocket_streams/live/runners/shell.py` | T076 replaced it with a compliant package. |
| `src/websocket_streams/live/runners/text.py` | T087 replaced it with a compliant package. |
| `src/websocket_streams/live/runners/utility/filters.py` | T075 replaced it with a compliant package. |
| `src/websocket_streams/live/runners/utility/runner.py` | T075 replaced it with a compliant package. |
| `src/websocket_streams/live/runners/utility/triggers.py` | T075 replaced it with a compliant package. |
| `src/websocket_streams/live/sessions/buffer.py` | T088 replaced it with a compliant package. |
| `src/websocket_streams/live/sessions/manager.py` | T088 replaced it with a compliant package. |
| `src/websocket_streams/live/sessions/record.py` | T088 replaced it with a compliant package. |
| `src/websocket_streams/live/terminal/byte_history.py` | T074 decomposed the classes and functions in place. |
| `src/websocket_streams/live/terminal/gateway.py` | T074 decomposed the classes and functions in place. |
| `src/websocket_streams/live/terminal/input_queue.py` | T074 decomposed the classes and functions in place. |
| `src/websocket_streams/live/terminal/state.py` | T089 replaced it with a compliant package. |
| `src/websocket_streams/live/transport/endpoint.py` | T073 decomposed the classes and functions in place. |
| `src/websocket_streams/live/transport/frames.py` | T072 replaced it with the compliant `runtime/` package. |
| `src/websocket_streams/live/transport/stream_client.py` | T073 decomposed the classes and functions in place. |
| `src/websocket_streams/live/transport/shell_client.py` | T073 decomposed the classes and functions in place. |
| `src/websocket_streams/web/blueprint.py` | T090 replaced it with a compliant package. |
| `src/websocket_streams/web/services.py` | T090 replaced it with a compliant package. |

T091 directly targets all 25 paths, 28 classes, and 19 functions. Its recursive scan
checked 145 modules, 204 classes, and 619 functions after each replacement.

**New design decisions that need a reason**:

| Item | Reason | Simpler option that the plan does not use |
| - | - | - |
| An own WebSocket client instead of the SDK WebSocket paths | The SDK paths lose the first output and split control sequences (#3659 and #3660). | Keep the SDK paths. The operator then sees missing or broken output. Issue #3718 records the exception. |
| Shared structured logging in the feature modules | Constitution V requires machine-parseable logs. One shared boundary emits ASCII JSON, permits bounded safe fields, and redacts secrets before a handler receives them. | Use separate text templates in each module. That option does not enforce one JSON shape, field bounds, or boundary redaction. |
| One release note fragment in `changelog.d/`, which grows from 69 to 70 entries | The release note rule requires one fragment for each change. | Edit `CHANGELOG.md` on the branch. The rule forbids that edit, because each parallel branch then conflicts on the same lines. Issue #3750 will restructure the existing process-folder debt. |
| One feature folder in `specs/`, which grows from 761 to 762 entries | The SpecKit flow keeps one folder for each feature. | Keep the design in the issue only. The escalation rule requires the SpecKit flow for a change of this size. Issue #3750 will restructure the existing process-folder debt. |
