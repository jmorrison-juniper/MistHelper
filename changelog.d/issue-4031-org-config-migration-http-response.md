### Org config export falls back on HTTP refusal

- **Fixed**: The org config migration export no longer crashes when the Mist API returns a real HTTP 400/401 response object instead of raising an exception. The flow now records the error and falls back to an `Unknown` org name. Issue #4031.
