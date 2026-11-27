# Quickstart: Reviewed Restore and Partial-Operation Recovery

## Prerequisites

- PowerShell on Windows 11, with the `gh` command authenticated for github.com.
- A local checkout of `jmorrison-juniper/MistHelper` with the `.venv` environment for Python 3.15. The `.venv` environment is needed only for the test scenarios.
- No Mist credential is needed. No command in this quickstart makes a live Mist API call.

## Scenario 1: Confirm that no restore code exists on main

Run these commands from the repository root.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
$tree = gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" | ConvertFrom-Json
$tree.tree | Where-Object { $_.path -like 'src/interfaces/portals/cisco_config_converter/state*' } | ForEach-Object { $_.path }
```

Expected result: no output. Remote check 42 in `design/research.md` records the same absence.

## Scenario 2: Confirm the Mist functions in the installed SDK

```powershell
Select-String -LiteralPath '.venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py' -Pattern '^def '
```

Expected result: five definitions, at lines 17, 58, 89, 117, and 145. Remote checks 97 to 99 record the same definitions for the three modules.

## Scenario 3: Confirm that the SDK request module has no timeout

```powershell
Select-String -LiteralPath '.venv\Lib\site-packages\mistapi\__api_request.py' -Pattern 'timeout'
```

Expected result: no output. Remote check 102 records the absence. The gateway in this feature bounds each write wait (decision D-16).

## Scenario 4: Confirm the create operation in the Mist contract

```powershell
Select-String -LiteralPath 'documentation\mist-api-openapi31yaml.yaml' -Pattern 'operationId: createOrgNetwork'
```

Expected result: one line at line 15161. Remote check 76 records the same line on `main`.

## Scenario 5: Run the decision tests after implementation

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_restore_decisions.py
```

Expected result before tasks T009 and T010: collection or import failures. Expected result after those tasks: 14 tests pass.

## Scenario 6: Run the execution and recovery tests after implementation

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_restore_execution.py
python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_recovery.py
```

Expected result after tasks T012 and T013: 15 tests pass in the first module and 7 tests pass in the second module.

## Scenario 7: Confirm the existing converter routes

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
```

Expected result: the existing tests pass with no change in their output.

## Scenario 8: Confirm the structure guards

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py
python -m pytest tests/guardrails/test_move_module_guidance.py
```

Expected result: both modules pass. Each guard prints the count of directories and modules that it examined.

## Scenario 9: Confirm the SDK compatibility guard

```powershell
python -m pytest tests/integration/test_mistapi_sdk_compatibility.py
```

Expected result: the guard passes. The gateway uses explicit arguments only.

## Scenario 10: Confirm the refusal of an unverified operator

Run the test that proves the refusal. The test uses a fake gateway and makes no live call.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_restore_execution.py -k test_unverified_operator_refused
```

Expected result: the test passes. The test asserts zero write calls on the fake gateway.

Caution: Do not run the `execute` command against a real organization during this quickstart. The tests use fakes. A real run needs the approvals in issue 4636 and the decision D-14 owner approval.
