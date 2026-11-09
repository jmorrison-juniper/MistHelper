# Cache generator failure boundary

**Decision**: Keep `except Exception` and use `logging.exception` for the existing root error log.

**Rationale**: Callers supply callbacks that can raise ordinary exceptions unrelated to filesystem access.
The existing boundary returns `False`. Narrowing it would change caller behavior.
Python logging preserves the active traceback with `logging.exception`.
The repository Ruff rule rejects `logging.error(..., exc_info=True)` and requires `logging.exception`.

**Alternatives considered**: A narrower exception list would miss valid callback failures.
Changing the logger or message would alter existing failure context.
Catching `BaseException` would incorrectly convert interrupts into ordinary failures.

No unresolved design question remains.
