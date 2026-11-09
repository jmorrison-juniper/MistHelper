# Cache generator failure boundary

**Decision**: Keep `except Exception` and log the exception type without its text or traceback.

**Rationale**: Callers supply callbacks that can raise ordinary exceptions unrelated to filesystem access.
The existing boundary returns `False`. Narrowing it would change caller behavior.
The handler filter sanitizes the message before the formatter appends the traceback.
The traceback can therefore expose labeled secrets from chained exceptions.
Unlabeled exception text can also bypass the message filter.

**Alternatives considered**: A narrower exception list would miss valid callback failures.
Retaining exception text or a traceback would expose callback secrets.
The filename and generator name remain in the root error record.
Catching `BaseException` would incorrectly convert interrupts into ordinary failures.

No unresolved design question remains.
