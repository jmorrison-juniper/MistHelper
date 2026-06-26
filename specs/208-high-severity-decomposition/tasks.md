# Tasks: Phase High — High-Severity STRUCT Decomposition

- **Spec**: `spec.md` | **Plan**: `plan.md` | **Issue**: #470

## Scope

**84 High-severity violations** across **57 distinct functions**:
- 41 `STRUCT-COMPLEXITY` (CC 11–20) + 34 `STRUCT-LENGTH` (40–77 lines) + 9 `STRUCT-PARAMS` (6–8 params).
Source of truth for "remaining": `python tools/check_compliance.py MistHelper.py`
(High count must strictly decrease each wave; phase done when High = 0).
Full snapshot: session `files/high_offenders.json`.

## Per-wave checklist (every wave)

1. Decompose the wave's functions (extract real helpers on the owning class).
2. Inline comment every touched line; preserve/add action logging.
3. `py_compile` + `ruff` + `black` clean; `mypy` no new errors.
4. Re-run analyzer — confirm targeted functions cleared, High count dropped, NO new violations.
5. Behavior-parity harness for the wave's functions.
6. Commit, push, PR, CI green, auto-merge after CodeQL, sync main.

## Waves (risk-ordered: self-contained complexity/length first, PARAMS + hotspots later)

- [ ] **Wave H1 — LENGTH-only safe splits**
  - `combined_inventory_with_site_info` (10004), `gateways_with_site_info` (10255),
    `_update_single_template` (17516), `fetch_synthetic_test_stats_with_retry` (15538)
- [ ] **Wave H2 — exporter/report COMPLEXITY**
  - `device_inventory` (12818), `device_virtual_chassis` (12919), `_map_upgrade_for_export` (19058),
    `_display_import_report` (17165)
- [ ] **Wave H3 — time-series / data COMPLEXITY**
  - `_extract_time_series` (15142), `_extract_sites_data` (15203), `flatten_nested_fields` (6623)
- [ ] **Wave H4 — connection-pool / batch LENGTH+COMPLEXITY**
  - `_pool_process_batch_wait_loop` (7957), `execute_with_connection_pool_management` (8062)
- [ ] **Wave H5 — PARAMS: progress emitters (dataclass)**
  - `emit_test_summary` (22020), `emit_progress_tick` (22054), `emit_progress_complete` (22071)
    — introduce a frozen progress-event dataclass; update all call sites.
- [ ] **Wave H6 — PARAMS: remaining**
  - `_enrich_device_context` (19375), `_listen_for_output` (16263), `_systematic_test_run_option`
    (22627), `write_with_format_selection` (7304), `__init__` (850) — config objects + call sites.
- [ ] **Wave H7+ — CC 18-20 hotspots (one/pair per PR)**
  - `import_module_safely`, `insight_metrics`, `gateway_device_configs`, `detect_msp_privileges`,
    `devices_with_site_info`, `_parse_selection`, `main`, `_run_tui_mode`, runtime-init cluster.

## Done

- [ ] Analyzer: 0 High STRUCT-COMPLEXITY (>=11) + 0 High STRUCT-LENGTH + 0 STRUCT-PARAMS.
- [ ] ARCH rules remain 0; gates clean; `--test` green; behavior unchanged.
