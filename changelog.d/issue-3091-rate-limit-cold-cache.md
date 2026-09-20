### Fixed

- The adaptive rate limiter no longer fails on its first call. The shared quota
  cache starts empty, and the delay pipeline read one key from it directly. That
  read raised `KeyError: 'last_updated'`, the safety net caught the error, and
  every call fell back to a fixed 500ms delay. The pipeline now seeds each quota
  key before it reads one, so the adaptive control runs from the first call.
  Issue #3091.
