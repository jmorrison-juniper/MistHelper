# Quickstart: Legacy Compat Shim Decomposition

## Goal
Execute shim decomposition in controlled phases while preserving menu/export behavior parity.

## Prerequisites
- Feature artifacts present under `specs/1002-legacy-compat-shim-decomposition/`.
- Baseline test environment for MistHelper Python project.
- Migration inventory from `spec.md` accepted as source of truth.

## Phase Execution Flow
1. Lock inventory and decision matrix for all listed symbols.
2. Enable canonical paths and migrate site insights callsites.
3. Decommission approved wrappers/branches; retain only approved temporary adapters.
4. Migrate tests and close menu parity gaps.
5. Remove expired adapters and publish docs/changelog updates.

## Workstreams (must run explicitly)
- **WS-1 MistHelper.py legacy delegates**: Remove/replace `*_legacy` delegates listed in inventory.
- **WS-2 `__init__.py` shim branches**: Retire listed `__getattr__` branches and fallback shims per decision matrix.
- **WS-3 Capture alias wrappers**: Transition `run()` compatibility aliases to `execute()` and remove by expiry.
- **WS-4 `src/export/site_insights` callsite migration**: Replace `InsightMetricsUtils.export_legacy()` usage in `site_metric_operation.py` and `device_metric_operation.py`.

## Validation Gates per Phase
- Static callsite audit for prohibited symbols.
- Menu regression and export parity checks for scoped operations.
- Adapter lifecycle review (active vs expired).
- Documentation/changelog sync check.

## Completion Criteria
- No internal references to retired symbols.
- No internal `InsightMetricsUtils.export_legacy()` calls.
- No retired `__getattr__` branch dependencies.
- Adapter list either removed or active with unexpired, documented gates.
- README/CHANGELOG include migration outcomes and timelines.
