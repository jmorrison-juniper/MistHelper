# Failure record contract

No stored data model changes.

The existing error record retains its root logger, error level, filename, and callback name.
It reports the exception type, but carries no exception text or traceback.

Successful generation returns `True`.
An ordinary exception returns `False`.
An interrupt or process exit propagates the original exception instance.

The change introduces no external interface.
