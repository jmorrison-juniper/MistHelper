# Data Model: Operations Portal Executor Initialization

This feature adds no persistent data model.
It changes the state transition for one process-local object.

## Entity: Executor Slot

**Purpose**: Hold the application-scoped operation executor.

**Storage**: `current_app.config["OPERATION_EXECUTOR"]`

**Fields**:

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `value` | `OperationExecutor` or `None` | Yes | `None` means that no executor is stored. |

**Validation rules**:

- Return a non-`None` stored value without replacement.
- Store only the value returned by the existing constructor.
- Do not store a placeholder or partial executor.

## Entity: Initialization Lock

**Purpose**: Permit one executor construction path at a time.

**Storage**: One private module-level value in `web_portal/routes/operations.py`.

**Fields**:

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `lock` | `threading.Lock` | Yes | One module value protects the executor slot. |

**Validation rules**:

- Acquire the lock only after the first empty read.
- Release the lock after construction and storage complete.
- Do not expose the lock through a route or application configuration.

## Entity: Concurrent Caller

**Purpose**: Represent one request path that asks for the executor.

**Fields**:

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `first_read` | Executor or `None` | Yes | The fast-path configuration result. |
| `protected_read` | Executor or `None` | Conditional | Read only after an empty first read and lock acquisition. |
| `result` | Executor | Yes | The stored executor returned to the caller. |

## Relationships

- Many concurrent callers read one executor slot.
- One initialization lock protects one executor slot.
- Exactly one successful constructor result becomes the executor slot value.
- Every completed caller returns the same stored object.

## State Transitions

```text
UNINITIALIZED
    |
    | first caller acquires the lock
    v
INITIALIZING
    |
    | constructor succeeds and value is stored
    v
READY
```

Waiting callers move from `UNINITIALIZED` observation to `READY` after their protected read.

If construction raises an exception, the slot remains `UNINITIALIZED`.
The lock releases through the context manager.
A later caller can retry through the existing exception behavior.

## Invariants

1. The `READY` state holds one executor reference.
2. No caller replaces a non-`None` executor.
3. Only the lock holder can move the slot from `UNINITIALIZED` to `READY`.
4. The initialized fast path does not acquire the lock.
5. The model is process-local and does not coordinate separate Gunicorn processes.
