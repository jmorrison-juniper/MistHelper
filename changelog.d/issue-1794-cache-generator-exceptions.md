### Cache generator error details

- **Fixed**: Cache generator failures now log the error type, traceback, and module.
  The cache still returns a failure result, and process-control exceptions still propagate. Issue #1794.
