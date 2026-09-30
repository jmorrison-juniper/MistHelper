### Align the container SNMP base OID default

- **Fixed**: The container startup fallback matches the SNMP responder default.
  Explicit environment overrides retain their existing order. Issue #3417.
- **Added**: An offline guard compares both defaults and rejects a mismatch.
  Shell tests cover unset, empty, and explicit overrides. Issue #3417.
