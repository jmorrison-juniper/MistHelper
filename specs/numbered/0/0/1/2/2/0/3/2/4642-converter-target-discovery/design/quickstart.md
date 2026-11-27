# Quickstart: Read-only Mist target discovery

This guide reproduces the gap and verifies the change for issue #4642. The steps run in process. No container starts, and no live Mist request runs.

## Preconditions

- The repository holds `main` at or after commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (R84).
- The Python environment in `.venv` holds `mistapi` 0.64.1 (R72).
- Issues #4634 and #4641 are closed before implementation starts (tasks precondition).
- Do not set or print any environment variable whose name contains TOKEN, KEY, SECRET, or PASSWORD.

## Reproduce the gap

1. Confirm that the discovery module is absent.

   ```powershell
   Test-Path -LiteralPath "src\mist\access\targets"
   ```

   Expected result: `False` (R79).

2. Run the discovery test module before implementation.

   ```powershell
   python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py
   ```

   Expected result: the module fails to collect, because `src.mist.access.targets` does not exist. Tests TC-01 to TC-24 do not pass.

3. Confirm that the discovery route is absent. After T002 to T008 write the failing tests and before T012 changes the routes, the route tests report HTTP 404 for `GET /cisco-config-converter/discovery/status`.

## Verify the change

Run each command in order. Each command must exit with code 0 unless the table says otherwise.

| Step | Command | Expected result |
| - | - | - |
| 1 | `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py` | All offline tests pass. |
| 2 | `python -m pytest tests/integration/web_portal/cisco_config_converter/test_discovery.py` | TC-01 to TC-22 pass. |
| 3 | `python -m pytest tests/e2e/web_portal/test_portal_smoke.py` | TC-23 and TC-24 pass in the isolated converter host. The browser runtime must be installed. |
| 4 | `python -m pytest tests/guardrails/test_nested_package_structure.py` | The nested-package guard passes. |
| 5 | `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py` | The SDK compatibility check passes. No dynamic keyword call exists. |
| 6 | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` | The fragment policy passes. |

The complete gate list appears in task `T-LOCAL-GATES` of `tasks.md`.

## Check the state labels by hand

No live Mist request is needed. The test client shows the states.

1. Start the test client in a Python shell with the blueprint mounted. The operator session is absent.
2. Request `GET /cisco-config-converter/discovery/status`.
3. Confirm the response: HTTP 200, `state` set to `unavailable`, `reason` set to `no_session`, and `items` set to null.

## Cleanup

No file is created. No container starts. No volume exists. No cleanup is needed.
