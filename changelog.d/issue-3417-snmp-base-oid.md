### Align the container SNMP base OID default

- **Added**: An offline guard compares both defaults and rejects a mismatch.
  Shell tests cover unset, empty, and explicit `METRICS_SNMP_BASE_OID` overrides.
  The retired `SNMP_BASE_OID` variable has no effect. Issue #3417.
