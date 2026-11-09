# Failure record contract

No stored data model changes.

The existing error record retains its root logger, error level, filename, callback name, and exception text.
Its exception information contains the original exception type, instance, and nonempty traceback.

Successful generation returns `True`.
An ordinary exception returns `False`.
An interrupt or process exit propagates the original exception instance.

The change introduces no external interface.
