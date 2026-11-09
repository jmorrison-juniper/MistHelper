### Anomaly metric discovery errors

- **Fixed**: Anomaly metric discovery preserves file, CSV, encoding, and runtime failure defaults. Short CSV rows use the same defaults.
  Error logs identify the failure type without exception text or private data. Unexpected programming errors propagate. Issue #1794.
