# Quickstart: Validate the Fetcher Failure Contract

## Purpose

Use this guide during implementation. It proves the fetcher contract and the
Menu 95 portal verdict without a live Mist credential.

## Prerequisites

1. Bootstrap the worktree if `.venv` does not exist.

```powershell
rtk python scripts\bootstrap_worktree.py
```

2. Confirm that the implementation changes only these files:

```text
src/foundation/support/refactors/device_data_fetcher.py
tests/unit/refactors/test_device_data_fetcher.py
tests/unit/web_portal/test_portal_silent_completion.py
```

3. Keep the existing issue #4030 changelog fragment unchanged.

## Scenario 1: Capture the pre-repair portal failure

Add the portal regression before the production edit.

The test must:

- Register Menu 95 with the real display handler.
- Keep the real `DeviceDataFetcher`.
- Create an unrelated file during site selection.
- Return no site ID.
- Use the real output scanner against `tmp_path`.
- Expect the final portal status to be `failed`.

Run only the new regression:

```powershell
rtk .venv\Scripts\python.exe -m pytest tests\unit\web_portal\test_portal_silent_completion.py -k 4030 -q
```

**Expected before repair**: The test fails. The run status is `completed`
because the unrelated file supplies output evidence.

Record this result in the pull request validation notes.

## Scenario 2: Apply the production repair

Edit only the unresolved-site branch in
`src/foundation/support/refactors/device_data_fetcher.py`.

The branch must:

1. Log
   `! Error fetching device data: site ID could not be resolved.`.
2. Return explicit `False`.
3. Stop before device selection and the Mist endpoint.

Do not edit the display, portal service, or parameter registry.

## Scenario 3: Validate the focused fetcher contract

Extend the existing unresolved-site test in
`tests/unit/refactors/test_device_data_fetcher.py`.

Assert:

- The result is `False`.
- The exact error appears.
- Device selection is not called.
- The Mist endpoint is not called.
- Data processing is not called.
- Export is not called.
- Display rendering is not called.

Run the focused module:

```powershell
rtk .venv\Scripts\python.exe -m pytest tests\unit\refactors\test_device_data_fetcher.py -q
```

**Expected after repair**: All tests pass.

## Scenario 4: Validate the repaired portal verdict

Run the portal regression again:

```powershell
rtk .venv\Scripts\python.exe -m pytest tests\unit\web_portal\test_portal_silent_completion.py -k 4030 -q
```

**Expected after repair**:

- The status is `failed`.
- The unrelated file remains in output evidence.
- The failure reason contains the exact fetcher error.
- `Completed device_tests execution.` is absent.
- The Mist endpoint is not called.

This red-green pair proves Complete before repair and Failed after repair.

## Scenario 5: Run the focused regression set

```powershell
rtk .venv\Scripts\python.exe -m pytest tests\unit\refactors\test_device_data_fetcher.py tests\unit\web_portal\test_portal_silent_completion.py -q
```

**Expected**: Both modules pass.

## Applicable Quality Gates

```powershell
rtk .venv\Scripts\python.exe -m ruff check src\foundation\support\refactors\device_data_fetcher.py tests\unit\refactors\test_device_data_fetcher.py tests\unit\web_portal\test_portal_silent_completion.py
rtk .venv\Scripts\python.exe -m black --check src\foundation\support\refactors\device_data_fetcher.py tests\unit\refactors\test_device_data_fetcher.py tests\unit\web_portal\test_portal_silent_completion.py
rtk .venv\Scripts\python.exe -m mypy src\foundation\support\refactors\device_data_fetcher.py --config-file pyproject.toml
rtk bandit -c pyproject.toml -r src\foundation\support\refactors\device_data_fetcher.py -q
rtk radon cc src\foundation\support\refactors\device_data_fetcher.py -j
```

Use `complexity-gate --max 10` with the Radon JSON in the implementation
phase. Run the test quality preflight and ratchet after the tests are committed.

## Scope Check

Before completion, run:

```powershell
rtk git diff --name-only
```

The implementation diff must not contain:

```text
web_portal/services/operation.py
src/interfaces/visualization/ui/interactive_display_utils.py
```

The implementation must not change `PARAMETER_REGISTRY`.
