# Contract: Operation Executor Initialization

## Contract owner

`web_portal/routes/operations.py::_get_executor()`

## Preconditions

- The caller can access the active application configuration.
- The configuration can contain `OPERATION_EXECUTOR`.
- Existing constructor inputs remain available under their current keys.

## Fast path

1. Read `OPERATION_EXECUTOR` once.
2. If the value is not `None`, return that exact object.
3. Do not acquire the initialization lock.
4. Do not import or call the executor constructor.

## Initialization path

1. Acquire the one module-level initialization lock after an empty fast read.
2. Read `OPERATION_EXECUTOR` again while the lock is held.
3. If the protected value is not `None`, return that exact object.
4. If the protected value is `None`, import the existing executor class.
5. Call the constructor with the current four configuration values.
6. Store the constructor result under `OPERATION_EXECUTOR`.
7. Return the stored constructor result.

## Concurrency guarantees

- One process constructs no more than one executor for concurrent first access.
- All concurrent first callers return the same stored object.
- A waiting caller does not replace an executor that another caller stored.
- A later initialized caller does not acquire the lock.

## Failure behavior

- Preserve the current constructor exception behavior.
- Do not store a value when construction fails.
- Release the lock when an exception leaves the protected section.
- Do not add retry, fallback, or compatibility behavior.

## Preservation requirements

- Keep `_get_executor()` as the only accessor.
- Keep the existing constructor arguments and configuration keys.
- Do not change `list_msps` from PR #4065.
- Do not change unrelated route functions.
- Do not modify `web_portal/services/operation.py`.
- Do not change operation scheduling, shutdown, or worker counts.

## Test contract

The forced-race unit test must:

1. Use at least two concurrent callers.
2. Hold each caller at its first empty configuration read.
3. Release all first reads together.
4. Avoid real `OperationExecutor` worker pools.
5. Finish within a fixed timeout.
6. Assert one constructor call.
7. Assert one stored executor.
8. Assert identity equality for every caller result.
9. Fail against the current unsynchronized accessor.
