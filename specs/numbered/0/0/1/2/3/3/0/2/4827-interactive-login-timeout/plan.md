# Implementation Plan: Interactive login request timeout

**Branch**: `fix/4827-interactive-login-timeout` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/3/3/0/2/4827-interactive-login-timeout/spec.md`

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/3/0/2/4827-interactive-login-timeout/spec.md`. The record holds no timestamp specification.

This plan keeps `spec.md`, `plan.md`, and `tasks.md` at the feature root. The research, data model, quickstart, contract, and checklist files sit under `design/`.

## Summary

The interactive login sends requests with no time limit. This change adds a request timeout to every SDK transport that the interactive login builds. The orchestrator wraps the SDK transport factory `_new_session` before the first login request. Each transport then carries a timeout adapter that fills a missing timeout and makes one attempt for each request. The interactive initializer passes the configured `API_REQUEST_TIMEOUT` value into the orchestrator. The removed import of PR #4830 stays removed, and an existing regression test guards it.

## Technical Context

- **Language/Version**: Python 3.15 or newer. The constitution defines this constraint (`.specify/memory/constitution.md`).
- **Primary Dependencies**: mistapi 0.64.1, pinned in `requirements.txt` line 129 (RC-33). requests 2.34.2, pinned in `requirements.txt` line 221 (RC-34). This change adds no dependency.
- **Storage**: Not applicable. The change stores nothing. See `design/data-model.md`.
- **Testing**: pytest, `unittest.mock`, `requests`, and one loopback HTTP server on `127.0.0.1`. The test-quality ratchet applies to the changed test files.
- **Target Platform**: Windows 11, macOS, and Linux (`.github/copilot-instructions.md`, "Language and environment").
- **Project Type**: Command-line tool with a text menu (`MistHelper.py`).
- **Performance Goals**: Each login request ends within `API_REQUEST_TIMEOUT` seconds. The default is 120 seconds (RC-15).
- **Constraints**: No new direct child in `src/mist/access/auth/interactive/` (RC-46). Open PR #4208 holds two files that this change does not edit (RC-85, RC-86). No production credential in any test.
- **Scale/Scope**: Two source files, three test files, three documentation files, and one changelog fragment. The change adds one nested class, one constructor argument, and four private methods to `LoginOrchestrator`.

## Constitution Check

The constitution version is 1.9.0 (`.specify/memory/constitution.md`, RC-68). Each rule has a result and a reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | No new direct child is added. The interactive package keeps five children (RC-46). Each new function has at most five parameters, five blocks, and 25 lines. The `send` override accepts `**kwargs` to stay within five parameters. |
| II. Class-Based Architecture | Pass | The behavior lives in `LoginOrchestrator` methods and in the nested class `RequestTimeoutAdapter`. The closure from `_timed_transport_factory` mounts adapters. It is not a wrapper that only delegates. |
| III. Safety-First | Pass | The timeout value is validated before use. No input prompt is added. No secret reaches a log line (FR-009). No destructive operation is added. |
| IV. Full Deployment Pipeline | Pass, planned | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the local gates, the commit, the rebase, the push, the pull request, CI, the squash merge, and the wait for the container build. The production deployment belongs to the orchestrator. |
| V. Observability and Logging | Pass | Log text is ASCII. Each action has an info line before it and a debug line after it. No new module is added, so the structured log rule for a new module does not apply. |
| VI. Inline Comments | Pass, planned | Each new executable line has an inline comment. Tasks T008 and T009 check this rule. |
| VII. Action Logging | Pass, planned | Each adapter mount and each factory wrap has an info line before it and a debug line after it. |
| Mist transport: mistapi as sole interface | Pass | The change adds no direct HTTP request. The adapter is a transport policy on the SDK session. |
| Mist transport: owned WebSocket transport | Not applicable | The change owns no WebSocket transport. |
| Python version | Pass | The code uses no feature beyond Python 3.15. |
| Package manager | Not applicable | The change alters no dependency. |
| Container runtime and test containers | Not applicable | No container starts. The loopback server runs inside the test process. |
| File paths | Pass | The tests use URLs and the address `127.0.0.1`. No path separator is hardcoded. |
| Output backends and export boundary | Not applicable | The change writes no export. |
| Operational store | Not applicable | The change adds no coordination record. |
| Database keys and data directory | Not applicable | The change adds no table and writes no product output. |
| Container security and Zscaler | Not applicable | The change builds and pushes no container. |
| Menu operations | Not applicable | The change adds no menu operation. |
| Security findings: fix over suppress | Pass | The change adds no suppression comment. The `**kwargs` form avoids a parameter-count warning without a suppression. |
| Documentation | Pass | `README.md` gets one sentence for the behavior change (T011). The operator guide and the CONTRIBUTING row change too. The environment template change is deferred (analysis U-1). |
| Release notes | Pass | One fragment is added (T012). |
| Audience standard | Pass | The operator-facing text uses plain words and short sentences. |
| SpecKit escalation | Pass | The change touches more than three files and two classes, so this record is required. |
| Multi-agent Git workflow | Pass | The issue exists and carries the bug and MistHelper.py labels. The branch is new and starts from `main`. The overlap check is in `design/research.md`, section 5. |
| Pull request checklist | Pass, planned | The pull request body holds `Closes #4827`, the gate results, the file summary, and the rollback note (T-PR). |

## Architecture

1. `src/foundation/support/refactors/initialize_mist_session_interactive.py` reads `_MH.API_REQUEST_TIMEOUT` and passes it to `LoginOrchestrator` (RC-14, RC-15).
2. `LoginOrchestrator._run_login_pipeline` creates the SDK session through the existing helper `_create_api_session`. Then it calls `_apply_request_timeout` before the first login request.
3. `_apply_request_timeout` validates the value, wraps the factory `_new_session`, and mounts timeout adapters on the current transport.
4. When the SDK calls `_new_session` for a login, the wrapped factory builds the transport and mounts the adapters before the request is sent.
5. Errors use the existing handlers. A `ValueError` goes to `_handle_value_error`. A `RuntimeError` goes to `_handle_generic_error`. Both print an operator message.

## Design of the Changed Methods

The shapes below set the limits for the implementation. Each function stays within 25 lines and five logical blocks. Each line receives an inline comment during implementation.

```python
def _apply_request_timeout(self, apisession: Any) -> None:
    """Route every login transport of the SDK session through the timeout adapter."""
    timeout_seconds = self.request_timeout_seconds  # Read the configured wait for each login request
    if timeout_seconds <= 0:  # A zero or negative wait fails each request at once
        raise ValueError("API_REQUEST_TIMEOUT must be a positive number of seconds")  # Name the setting for the operator
    logger.info("Applying the %s second request timeout to the login session", timeout_seconds)  # Trace before the change
    transport_factory = getattr(apisession, "_new_session", None)  # SDK hook that builds each login transport
    if transport_factory is None:  # Without the hook a login could wait without a limit
        raise RuntimeError("The Mist API SDK session has no transport factory for the request timeout")  # Fail closed
    apisession._new_session = self._timed_transport_factory(transport_factory, timeout_seconds)  # Bound each new transport
    current_transport = getattr(apisession, "_session", None)  # Transport that exists before the first login
    if current_transport is not None:  # Bound the existing transport as well
        self._mount_timeout_adapters(current_transport, timeout_seconds)  # Mount the adapters on the existing transport
    logger.debug("Request timeout applied to the login session transports")  # Confirm the change finished
```

The method `_timed_transport_factory` returns a closure. The closure calls the original factory, mounts the adapters on the new transport, and returns the transport. The method `_mount_timeout_adapters` mounts one adapter for `https://` and one for `http://`. Each mount receives its own adapter, so the connection pools stay separate. The method `_build_timeout_adapter` defines the nested class `RequestTimeoutAdapter`. Its `send` method fills `timeout` only when the caller gives none. It returns `RequestTimeoutAdapter(max_retries=0)`.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/3/0/2/4827-interactive-login-timeout/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      login-request-timeout.md
    checklists/
      requirements.md
```

The feature root holds five children. The `design` folder holds five children. The `contracts` folder and the `checklists` folder each hold one file.

### Source and documentation changes

| Path | Action | Requirements | Change |
| - | - | - | - |
| `src/mist/access/auth/interactive/login_orchestrator.py` | Modify | FR-003 to FR-009 | Add `from requests.adapters import HTTPAdapter`. Add the constructor argument `request_timeout_seconds`. Call `_apply_request_timeout` after the `apisession is None` guard in `_run_login_pipeline` (after line 107). Add the method `_apply_request_timeout`, the static methods `_timed_transport_factory`, `_mount_timeout_adapters`, and `_build_timeout_adapter`, and the nested class `RequestTimeoutAdapter`. |
| `src/foundation/support/refactors/initialize_mist_session_interactive.py` | Modify | FR-003 | Pass `request_timeout_seconds=_MH.API_REQUEST_TIMEOUT` to `_MH.LoginOrchestrator` after line 51. |
| `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py` | Modify | FR-001 to FR-009 | Add `request_timeout_seconds` to `_make_orchestrator` (line 44). Replace the fake sessions created with `MagicMock(spec=object)` at lines 295, 309, and 325 with fakes that name `_new_session` and `_session`. Add class `TestRequestTimeout`. Update the module docstring to name the timeout tests. |
| `tests/unit/marvis/mist/access/auth/test_interactive_session.py` | Modify | FR-003 | Add `request_timeout_seconds=120` to the two constructors at lines 27 and 51. |
| `tests/unit/config/foundation/support/refactors/runtime/session/test_initialize_mist_session_interactive_wave9.py` | Modify | FR-003 | Add one test that checks the value from `MistHelper.API_REQUEST_TIMEOUT`. |
| `tests/integration/test_mistapi_sdk_compatibility.py` | Modify | FR-008, SC-004 | Add class `TestInteractiveTransportHook` with two tests. |
| `documentation/CONTRIBUTING-MistHelper.md` | Modify | FR-011 | Replace the description in the row for `configure_session_timeout` (line 46). |
| `documentation/operator-guide.md` | Modify | FR-011 | Add one paragraph after line 589 about the request timeout. |
| `README.md` | Modify | FR-011 | Add one sentence after line 26 about the request timeout. |
| `changelog.d/issue-4827-interactive-login-timeout.md` | Add | FR-012, SC-006 | One `###` heading and one Fixed bullet that names issue #4827. |

The following files stay unchanged on purpose.

- `src/foundation/support/refactors/initialize_mist_session.py` and `deploy/.env.example` are changed by open PR #4208 (RC-85, RC-86).
- `MistHelper.py` holds the public name list in `__all__` (RC-18). Changing that list needs a snapshot update, which this change does not make.
- `src/foundation/runtime/config/runtime_settings.py` holds the retry settings only (RC-21).

## Dependencies

- No new dependency. The change uses `requests` and the pinned mistapi.
- Tests come first. Tasks T004 to T007 add or update tests before the implementation in T008. This order follows the task rules in `.specify/templates/tasks-template.md`.
- T008 depends on T004. T009 depends on T008.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| R-1: A later SDK release removes `_new_session`. | Interactive login fails closed. | The pin `mistapi>=0.64.1,<0.65` (RC-32). The SDK compatibility test (RC-47). The fail-closed rule (D-5). |
| R-2: Operators see failed logins on slow links. | Failures appear that were hangs before. | The operator guide sentence (T011). The variable `API_REQUEST_TIMEOUT` raises the limit. |
| R-3: The token path and the interactive path keep two adapters. | The two copies can drift. | Unify both after PR #4208 merges (analysis item U-2). |
| R-4: An operator sets the timeout to 0. | Each login fails at once. | The `ValueError` message names the setting (FR-007). A caution appears in the quickstart. |
| R-5: The `symbol-diff` gate lists the new import as a change. | The gate output differs from its expected result. | Record the added import in the pull request body (analysis item U-6). |
| R-6: Pylint reports the `send` override. | The pylint score falls. | The override uses `**kwargs`. The score is checked in T-LOCAL-GATES (SC-003). |
| R-7: The loopback test is slow or unstable. | CI time grows or the test fails at random. | The server waits on an event with a 5 second cap. The client timeout is 1 second. The server stops in a `finally` block. |
| R-8: Three existing fake sessions fail after the change. | Test failures in `TestRunLoginPipeline`. | Task T004 replaces those fakes with fakes that name `_new_session` and `_session`. |

## Rollback Steps

1. Revert the squash commit of the pull request on `main`.
2. Run `python -m pytest tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py::TestImportResolution -q` to confirm the state that PR #4830 left.
3. Confirm that `changelog.d/issue-4827-interactive-login-timeout.md` no longer exists on `main`.
4. Keep issue #4827 open until the owner decides the next step.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| The timeout adapter repeats the shape of the token path adapter `TimeoutAdapter` (`initialize_mist_session.py` lines 65 to 135, RC-87). | The interactive path needs a bounded wait with no retry and no Redis admission adapter. The token path file belongs to open PR #4208. | Reusing `configure_once` adds read retries and the admission adapter. It also edits a file that open PR #4208 owns (decisions D-2 and D-6). |

Grandfathered debt in the touched files: none. Remediation action R-3 tracks the duplicate adapter after PR #4208 merges.

## Structure Decision

The change modifies existing files only. It adds no direct child to any directory. The record uses the numbered route from `specs/numbered/0/0/1/2/3/3/0/2/`. The numbered route rule in `.github/copilot-instructions.md` (RC-70) gives this route. The route equals the base-5 digits of 4827, padded to eight digits. The route leaf does not exist on `main` (RC-83), and it holds only this record folder.
