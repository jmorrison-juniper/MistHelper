### Prove the Cradlepoint transport status before an export

- **Fixed**: The Cradlepoint connection status export reads the response body only
  after the HTTP transport status proves a completed 2xx success. An absent, a
  `None`, a malformed, a boolean, a 1xx, or a 3xx status now stops the export with
  a named outcome in the log, so no row can report `last_status: active` when the
  HTTP result is unknown. Issue #3819.
