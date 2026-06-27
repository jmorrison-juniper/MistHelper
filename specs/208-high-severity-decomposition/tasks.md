# Tasks: Phase High — High-Severity STRUCT Decomposition

- **Spec**: `spec.md` | **Plan**: `plan.md` | **Issue**: #470

## Scope (fresh baseline 2026-06-27)

**50 High-severity violations** across **32 distinct functions**:
- 28 `STRUCT-COMPLEXITY` (CC 11–17) + 22 `STRUCT-LENGTH` (>60 lines, up to 198).
- 18 functions carry BOTH CC and LENGTH — decompose once, clears both.
- STRUCT-PARAMS now **0** (closed by #431).
Source of truth: `python tools/check_compliance.py MistHelper.py` (High count must strictly
decrease each wave; phase done when High = 0).

## Analyzer thresholds (binding on every new helper)
- Length: inclusive physical span (def->end incl. comments/docstring) **<= 25**.
- Params: **<= 5** (excl self/cls). Blocks (if/for/while/with/try): **<= 5**. Nesting: **<= 4**.
- Complexity: **<= 5** (note: each `and`/`or` operand-1, each comprehension `if` = +1).
- Decompose each target to FULL compliance (parent + helpers all clean) so it does not
  reappear in the Medium/Low phases.

## Per-wave checklist (every wave)
1. Decompose the wave's functions (real helpers on the owning class; NO pass-throughs).
2. Inline comment every touched line; `info` before / `debug` after meaningful actions.
3. `py_compile` + `ruff check` + `black --check` clean.
4. Re-run analyzer — targeted functions cleared, High count dropped, NO new violations.
5. Commit, push, PR, CI green, auto-merge after CodeQL, sync main.

## Waves (risk-ordered: self-contained first, runtime modes last)

- [ ] **H1 — argparse + concurrent import** (self-contained, lowest risk)
  - `_build_argument_parser` (23164, L79), `_import_packages_concurrently` (1566, CC14/L78)
- [ ] **H2 — runtime init cluster**
  - `_initialize_deferred_imports` (23133, CC11), `_initialize_dependencies` (23287, CC11),
    `__init__` (867, L77), `_handle_close` (16546, CC12)
- [ ] **H3 — session auth**
  - `_log_session_auth_status` (2886, CC15), `_build_session_attempts` (2635, CC12)
- [ ] **H4 — data flatten/merge**
  - `flatten_nested_fields` (6637, CC14), `merge_transceiver_data` (5809, CC13/L119)
- [ ] **H5 — CSV / table SQL**
  - `build_create_table_sql` (6827, CC17/L107), `write_to_csv` (7466, CC11/L71)
- [ ] **H6 — report / template analysis**
  - `_display_import_report` (17361, CC13), `_generate_report` (17785, CC15/L64),
    `_analyze_templates` (17588, CC14/L76), `fetch_and_analyze` (17593, CC11)
- [ ] **H7 — anomaly / rogue cluster**
  - `anomaly_events` (13254, CC16/L103), `device_anomaly_events` (13359, CC14/L104),
    `rogue_aps` (11380, CC12/L68), `rogue_clients` (11302, CC12/L76)
- [ ] **H8 — interactive selection**
  - `select_client_mac` (8187, CC17/L133), `select_device_id_from_inventory` (8397, CC12/L93)
- [ ] **H9 — msp / manage / apply**
  - `msp` (12080, CC16/L125), `manage` (21227, CC11/L71), `_apply_changes` (21050, CC11/L66)
- [ ] **H10 — synthetic tests**
  - `synthetic_tests` (15682, CC17/L198), `run_systematic_test` (22940, L117),
    `fetch_synthetic_test_stats_with_retry` (15710, L72)
- [ ] **H11 — runtime modes + entrypoint** (riskiest, last)
  - `_run_interactive_mode` (23519, CC17/L108), `_run_cli_mode` (23426, CC15/L91),
    `_run_tui_mode` (23373, CC13), `main` (23630, CC13)

## Done
- [ ] Analyzer: 0 High STRUCT-COMPLEXITY (>=11) + 0 High STRUCT-LENGTH (>60).
- [ ] ARCH rules remain 0; gates clean; `--test` green; behavior unchanged.
