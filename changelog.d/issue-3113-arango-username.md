### Fixed

- Every operation now writes its records to the database again. `compose.yml`
  never passed `ARANGO_USERNAME` or `ARANGO_ROOT_PASSWORD` to the application
  service, and `src/db` requires both whenever MistHelper is not standalone.
  The database router refused to build, the exporter caught the error, and each
  run kept the CSV file as its only copy. Both stores reported healthy the whole
  time, so the log gave no reason to look. Issue #3113.

### Changed

- The skipped-database-write message now sends the reader to the warning that
  names the failed setting. It used to name `ARANGO_HOST` and `REDIS_HOST`,
  and both values were correct. Issue #3113.
