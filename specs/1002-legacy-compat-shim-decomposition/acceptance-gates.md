# Acceptance Gates

## Gate A — Foundational

- [x] Static retired-symbol guard implemented (`scripts/ci/check_retired_compat_symbols.py`)
- [x] CI workflow includes retired-symbol guard job
- [x] Guard passes on current branch state
- [ ] Canonical ownership map finalized
- [ ] Adapter policy doc finalized

## Gate B — US1 Symbol Retirement

- [x] Retired wrappers removed: `get_csv_file_path_legacy`, `export_gateway_templates_to_csv_legacy`
- [x] Legacy insight callsites replaced (`site_metric_operation`, `device_metric_operation`)
- [x] Capture `run()` adapters explicitly marked temporary with expiry
- [ ] `__init__.py` shim branch retirement phase complete
- [ ] Static scan confirms zero references for all retired US1 symbols

## Gate C — US2 Parity / Risk

- [ ] Menu parity regression suite added
- [ ] Export output-shape parity suite added
- [ ] Fallback growth guard tests added
- [ ] Adapter expiry enforcement tests added

## Gate D — US3 Test Migration

- [ ] Legacy facade test imports migrated to canonical imports
- [ ] Alias-path capture tests migrated to `execute()`
- [ ] No new `export_legacy` callsites test added
- [ ] Canonical import enforcement test added

## Gate E — Release Readiness

- [ ] Final internal reference audit captured
- [ ] README migration guidance updated
- [ ] CHANGELOG deprecation/removal entries added
- [ ] SC-001..SC-007 signoff complete
