### Fixed

- SSH sessions now receive the seven ArangoDB and Redis settings from the explicit configuration allowlist (#3313).
  The session file keeps mode `0400`, the session owner, and name-only reports.
