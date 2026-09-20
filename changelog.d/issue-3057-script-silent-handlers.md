### Fixed

- Replaced the last four silent exception handlers in the standalone scripts,
  which caught every error and discarded it with a bare `pass`. A malformed DNS
  answer, a malformed TLS extension, a failed packet layer lookup, and a failed
  login probe now each report the exception type at debug level. Each handler
  still returns its safe fallback, so the behavior does not change. See
  issue #3057.
