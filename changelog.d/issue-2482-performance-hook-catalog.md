### Python performance hook catalog (issue #2482)

- **Added**: The SpecKit workflow for the performance monitoring plan records the
  hook catalog, the Python file inventory, the scan summary, and the strategy
  coverage table. Issue #2482.
- **Added**: `tests/guardrails/test_performance_hook_catalog.py` reads each shipped
  artifact and compares it against an AST scan of the recorded files. The guard
  fails when a catalog row names a file that no longer exists, when a hook row
  names a symbol that no longer exists, or when a summary count disagrees with the
  table it describes. Issue #2482.
