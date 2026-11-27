# Quickstart: MSP Profile Lookup Failure

This guide proves the change in the unit tests. Run each command from the worktree root. No scenario needs an API token, a live Mist site, or a container.

## Prerequisites

- A worktree for the branch `fix/4713-msp-profile-lookup-failure`.
- A new worktree has no `.venv`. Install Python 3.15.2 and create the environment with `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`. Then activate it with `.venv\Scripts\Activate.ps1` (Language and environment, `.github/copilot-instructions.md`).
- No token. The tests mock every SDK response.

## Scenario 1: Reproduce the defect on the unchanged branch

Run the new cases before T006 and T007. The detector cases import the new names inside each test body, so the rest of the module collects.

```powershell
python -m pytest tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py -q -k "detect_returns_empty_list_on_refused_status"
python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py -q -k "stops_when_lookup_fails"
```

Expected before the change:

- The first command fails at the warning assertion. The unchanged detector returns an empty list for HTTP 403 and writes no warning that names the status.
- The second command fails at patch time. The orchestrator module has no `lookup_msp_privileges` name yet.

Ad hoc check, not committed. Stub `mistapi.api.v1.self.self.getSelf` to return `status_code` 403 with an error `detail` body. Call `detect_msp_privileges` with a mock session. Pass the result to `OrgDeviceInventoryMSPOrchestrator.dispatch` with three mock callbacks and an empty grant list. The unchanged code calls the single-organization callback once. That call is the defect in the issue.

## Scenario 2: Detector contract after T006

```powershell
python -m pytest tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py -q
```

Expected: every case passes. The 13 new cases and the five updated fixtures pass. The lookup returns a failed result for statuses 401, 403, 429, and 503. It also fails for a missing status, an invalid `privileges` value, a non-object body, an exception, and a missing session. The lookup returns a valid result with zero grants for an empty `privileges` list.

## Scenario 3: Dispatch after T007

```powershell
python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py -q
```

Expected: every case passes. A failed live lookup calls no callback and prints `_LOOKUP_FAILED_MSG`. A live lookup with grants calls no callback and prints `_RESTART_FOR_GRANTS_MSG`. A cached grant list makes no lookup. A missing session makes no lookup. A valid live lookup with zero grants calls the single-organization callback once.

## Scenario 4: Redaction

```powershell
python -m pytest tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py -q -k "exception_and_logs_class_only"
```

Expected: the case passes. The captured log holds the exception class name `RuntimeError`. The captured log holds no text from the exception message.

## Scenario 5: Callers outside menu 13 keep their behavior

```powershell
python -m pytest tests/unit/export/test_msp_inventory_exporter.py tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py tests/unit/marvis/mist/access/auth/test_interactive_session.py tests/unit/config/foundation/support/refactors/runtime/session/test_initialize_mist_session_interactive_wave9.py -q
```

Expected: every case passes without any change to these files. The login test still finds the legacy banner text (RC-33).

## Scenario 6: Safe sweep without a token

```powershell
python MistHelper.py --test
```

Expected: each safe operation completes. Menu 13 is in the safe category (RC-62). If the sweep reaches menu 13 without a session, the dispatch prints `_LOOKUP_FAILED_MSG` and returns. Record that output line in the pull request body.

## Scenario 7: Full local gates

Run the list in T-LOCAL-GATES in `tasks.md`. Each gate records its output line in the pull request body.
