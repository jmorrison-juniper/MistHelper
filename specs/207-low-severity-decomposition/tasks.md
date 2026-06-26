# Tasks: Phase Low — Low-Severity STRUCT Decomposition

- **Spec**: `spec.md` | **Plan**: `plan.md` | **Issue**: #468

## Scope

**184 Low-severity violations** across **155 distinct functions**:
- 116 `STRUCT-COMPLEXITY` (CC 6–9) + 68 `STRUCT-BLOCKS` (6–11 blocks).
Source of truth for "remaining": `python tools/check_compliance.py MistHelper.py`
(Low count must strictly decrease each wave; phase done when Low = 0).

## Per-wave checklist (every wave)

1. Decompose the wave's functions (extract real helpers on the owning class).
2. Inline comment every touched line; preserve/add action logging.
3. `py_compile` + `ruff` + `black` clean; `mypy` no new errors.
4. Re-run analyzer — confirm targeted functions cleared, Low count dropped.
5. `python MistHelper.py --test` — 0 failed ops.
6. Commit, push, PR, CI green, auto-merge after CodeQL, sync main.

## Waves (grouped by code region; ~5–8 functions each)

- [ ] **Wave 1 — Bootstrap config/version (GlobalImportManager + bootstrap)**
  - `_parse_version` (L490, CC6)
  - `_version_satisfies` (L510, BLOCKS 11)
  - `_parse_requirements_file` (L582, CC9 + BLOCKS 6)
  - `_fallback_load_dotenv` (L810, CC7)
- [ ] **Wave 2 — UV upgrade/import pipeline**
  - `_upgrade_uv` (L1082), `_install_package_with_uv` (L1145),
    `_upgrade_all_dependencies` (L1270), `_check_and_upgrade_package` (L1388)
- [ ] **Wave 3 — Module import/global wiring**
  - `import_module_safely`, `_import_packages_concurrently`, `_make_modules_global`,
    `_add_fallbacks_to_globals`, `_import_special_modules`
- [ ] **Wave 4 — Session/auth/MSP**
  - `detect_msp_privileges`, `_fetch_msp_name`, `_parse_api_tokens`,
    `_build_session_attempts`, `_create_session_with_available_tokens`,
    `initialize_mist_session`
- [ ] **Wave 5+ — long tail** (remaining ~130 functions across exporters, utils, TUI,
  test runner, runtime-init). Enumerate from each analyzer re-run; full snapshot in
  session `files/low_offenders.json`.

## Done

- [ ] Analyzer: 0 Low STRUCT-COMPLEXITY + 0 STRUCT-BLOCKS for MistHelper.py.
- [ ] ARCH rules remain 0; gates clean; `--test` green; behavior unchanged.
