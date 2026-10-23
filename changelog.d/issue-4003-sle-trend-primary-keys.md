### SLE trend window identity

- **Fixed**: Both SLE summary-trend exports use complete identifier and start/end keys.
  Repeated exports replace the new keyed record in SQLite and ArangoDB.
  Existing rows remain unchanged without migration or deletion.
  The first matching export can add one keyed record beside legacy duplicates.
  Historical duplicate totals remain unchanged.
  SQLite previously refreshed its auto-increment table. ArangoDB previously added UUID documents on each export.
  Issue #4003.
