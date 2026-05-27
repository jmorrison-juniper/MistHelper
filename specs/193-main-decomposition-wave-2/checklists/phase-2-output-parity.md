# Phase 2 Output Parity Evidence (API/Backend)

Date: 2026-05-26

## Scope

- Operation `139` output artifacts (Marvis CSV exports):
  - `MarvisInsights_Client_<...>.csv`
  - `MarvisInsights_Device_<...>.csv`
  - `MarvisInsights_Network_<...>.csv`
  - `MarvisInsights_<endpoint>.csv` (insights views)
- Operation `175`/`176` output behavior:
  - per-host SSH log files in `data/per-host-logs/`
  - existing `EnhancedSSHRunner` execution/result summaries preserved

## Parity Verification Approach

- Extracted logic copied from existing `MistHelper.py` paths into:
  - `src/troubleshooting/marvis_troubleshoot_utils.py`
  - `src/ssh/ssh_runner_manager.py`
- Export/write boundaries preserved:
  - `DataExporter.save_data_to_output(...)` for Marvis CSV artifacts
  - `EnhancedSSHRunner` APIs for SSH command execution and host log output
- `MistHelper.py` now provides dependency wiring without changing menu contracts.

## Test Gate Evidence

- Executed targeted suite:
  - `python -m pytest tests/unit/troubleshooting/ tests/unit/ssh/ tests/contract/test_import_graph.py tests/integration/test_runtime_coupling.py -q`
- Result: `23 passed in 1.28s`.

## Conclusion

- Phase 2 extraction preserves output shaping and backend write paths for operations `139`, `175`, and `176` in this automated gate scope.
