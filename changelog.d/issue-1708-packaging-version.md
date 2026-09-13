### Package version comparison

- **Fixed**: The dependency check now uses `packaging` for version constraints,
  so it rejects a release candidate when a final release is required. Issue #1708.
