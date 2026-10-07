# Quickstart: Validate Executor Initialization Synchronization

## Purpose

Use this guide after implementation.
It proves the process-local executor race is repaired without changing unrelated routes.

## Prerequisites

- Use Python 3.13.
- Install the repository development dependencies.
- Run commands from the repository root.
- Do not use a production Mist credential.

## Expected implementation files

```text
web_portal/routes/operations.py
tests/unit/web_portal/test_operation_executor_concurrency.py
changelog.d/issue-4026-operation-executor-race.md
```

No file under `web_portal/services/` may change.

## Scenario 1: Prove the forced race

Run the focused concurrency module:

```powershell
python -m pytest tests/unit/web_portal/test_operation_executor_concurrency.py -q
```

Expected result:

- The new forced-race test passes.
- The constructor count is one.
- Every caller result is the same object.
- No test leaves an executor worker pool or a background thread.

Red-run proof:

- Temporarily remove the protected second read and lock only in an uncommitted check.
- Run the new test.
- Confirm that the constructor count exceeds one.
- Restore the synchronized implementation immediately.

## Scenario 2: Preserve PR #4065

Run the account-aware MSP selector tests:

```powershell
python -m pytest tests/unit/web_portal/test_operations_msp_selector.py -q
```

Expected result:

- All selector tests pass.
- The `list_msps` route response shapes remain unchanged.

## Scenario 3: Validate the changed Python files

Run syntax and lint checks:

```powershell
python -m py_compile web_portal/routes/operations.py
ruff check web_portal/routes/operations.py tests/unit/web_portal/test_operation_executor_concurrency.py
```

Expected result:

- Both commands exit with status 0.

## Scenario 4: Verify the scope boundary

Inspect the changed files:

```powershell
git status --short
git diff -- web_portal/routes/operations.py tests/unit/web_portal/test_operation_executor_concurrency.py
git diff --name-only
```

Expected result:

- Product code changes appear only in `web_portal/routes/operations.py`.
- Test changes appear only in the selected unit-test module.
- One issue-specific changelog fragment appears after implementation.
- No file under `web_portal/services/` appears.
- The specification artifacts can remain changed from the planning workflow.

## Scenario 5: Run the new-test quality gate

Follow the test quality procedure in `.github/copilot-instructions.md`.

Expected result:

- The analyzer reports no new finding against the baseline.
- The forced-race test contains deterministic assertions and a timeout.

## Contract references

- See [executor-initialization.md](contracts/executor-initialization.md) for the accessor guarantees.
- See [data-model.md](data-model.md) for the process-local state transition.
