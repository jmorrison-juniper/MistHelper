# Tasks: SSID Template Consolidation Rewrite (Menu 159)

**Input**: Design documents from `specs/018-ssid-template-consolidation-v2/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md
**Branch**: `feat/72-ssid-template-consolidation-rewrite`
**Issue**: #72
**Tests**: Not requested — omitted per template rules

**Organization**: Tasks grouped by user story to enable incremental implementation. Each phase is a testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different code locations, no dependencies on incomplete tasks)
- **[Story]**: Which user story: US1–US7 from spec.md
- All code changes in `MistHelper.py` unless otherwise noted

---

## Phase 1: Setup (Cleanup + PK Strategies)

**Purpose**: Remove old broken implementation and add database schema entries required by all subsequent phases.

- [ ] T001 [P] Delete the old `src/ssid_consolidation/` package directory entirely
- [ ] T002 [P] Remove `SSIDTemplateConsolidationLauncher` class (~line 12862–12943) and its `from src.ssid_consolidation...` import block from MistHelper.py
- [ ] T003 [P] Add 6 PK strategy entries to `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict (~line 3281) in MistHelper.py: `ssidConsolidationMatrix` (composite: site_id+ssid_id), `ssidConsolidationDeviation` (composite: cluster_id+parameter), `ssidConsolidationSiteVars` (composite: site_id+variable_name), `ssidConsolidationSiteGroups` (composite: site_id+group_id), `ssidConsolidationTemplates` (composite: template_id+ssid_name), `ssidConsolidationDisable` (composite: site_id+ssid_id) — see data-model.md for full definitions

**Checkpoint**: `src/ssid_consolidation/` deleted. Old launcher removed. 6 PK strategies added. `python -m py_compile MistHelper.py` passes.

---

## Phase 2: US1 — SSID Selector and Phase Menu (P1) — MVP

**Goal**: A NOC engineer can launch Menu 159, select a target SSID (with `.env` default), and navigate the 5-phase sub-menu with dependency enforcement. No API calls. This is the entry point for all functionality.

**Independent Test**: Launch Menu 159. Verify SSID prompt shows `MIST_TARGET_SSID` default, accepts Enter or typed override. Phase sub-menu displays 5 phases + "Run All". Selecting Phase 3 without Phase 2 complete shows a prerequisite error.

- [ ] T004 [US1] Create `SSIDTemplateConsolidationManager` class (~line 12945 in MistHelper.py, after E911BSSIDReportGenerator) with: class constants (`CACHE_FILE = "data/ssid_consolidation_cache.json"`, `PHASE_RESULT_FILES` dict for phases 2–5, `PSK_AUTH_TYPES = ("psk", "psk-tkip", "psk-wpa2-tkip")`, `METADATA_FIELDS` set, `PILOT_PATTERN = re.compile(r"(?i)\b(pilot|test|lab)\b")`, `CONFIRM_KEYWORD = "CONFIRM"`, `CACHE_FRESHNESS_MINUTES = 60`), `__init__(self, org_id: str, target_ssid: str)` storing state, and `@staticmethod execute()` entry point that reads `MIST_TARGET_SSID` from `os.environ`, prompts via `InputUtils.safe_input()` with default display, retrieves org_id via `ConfigUtils.get_cached_or_prompted_org_id()`, creates instance, calls `run_phase_menu()`
- [ ] T005 [US1] Implement `run_phase_menu(self)` in MistHelper.py: display numbered phase sub-menu (Phase 1–5 with brief descriptions + option 6 "Run All Phases Sequentially"), read selection via `InputUtils.safe_input()`, validate prerequisite via `_check_prerequisite(phase)` before dispatch, dispatch to phase method or sequential run
- [ ] T006 [US1] Implement shared infrastructure methods in MistHelper.py: `_confirm_or_cancel(self, summary: str) -> bool` (display summary, require exact `"CONFIRM"` via `InputUtils.safe_input()`, log confirmation with timestamp, return bool), `_check_prerequisite(self, phase: int) -> bool` (verify required cache/results files exist for prior phases), `_load_cache(self) -> dict | None` (read cache JSON, check freshness timestamp), `_save_cache(self, data: dict) -> None` (write cache JSON with timestamp), `_save_phase_results(self, phase: int, results: list) -> None` (write results JSON), `_load_phase_results(self, phase: int) -> dict | None` (read results JSON), `_offer_resume(self, phase: int, results: dict) -> tuple[bool, list]` (detect partial run by comparing completed count vs total, prompt to resume or restart)
- [ ] T007 [P] [US1] Update menu 159 entry in the menu dict (~line 55952) and category dict (~line 56686) in MistHelper.py to `(SSIDTemplateConsolidationManager.execute, "SSID Template Consolidation (5-Phase Guided Workflow)")` with category `"safe"`
- [ ] T008 [US1] Verify syntax: run `python -m py_compile MistHelper.py` — confirm no errors, Menu 159 shows updated description, SSID prompt and phase sub-menu render correctly

**Checkpoint**: Menu 159 launches the new class. SSID selector works with `.env` default and override. Phase menu displays and enforces dependencies. Shared helpers compile. No API calls made yet.

---

## Phase 3: US2 — Phase 1 Read-Only Audit and Matrix Report (P1)

**Goal**: Phase 1 collects all org data via 5–7 bulk API calls, builds a per-site matrix report (one row per site with template/SSID/cluster/PSK/anomaly data), performs deviation analysis within each cluster group, and detects cross-cluster drift. Output saved to CSV + SQLite.

**Independent Test**: Run Phase 1 against the live org. Verify output CSV has ~170 rows with correct columns. Spot-check 5–10 sites against the Mist dashboard. PSK sites flagged. Anomaly templates flagged with reason codes. At least one deviation detected. Total API calls ≤ 10.

- [ ] T009 [US2] Implement `_fetch_all_org_data(self) -> dict` in MistHelper.py: 5 org-level bulk API calls using `mistapi.get_all()` pagination — `listOrgTemplates(apisession, org_id)`, `listOrgWlans(apisession, org_id, limit=DEFAULT_API_PAGE_LIMIT)`, `listOrgSites(apisession, org_id, limit=DEFAULT_API_PAGE_LIMIT)`, `listOrgMxTunnels(apisession, org_id)`, `listOrgSiteGroups(apisession, org_id)` — returns dict with all 5 datasets. Log call count. Report empty results honestly (FR-044).
- [ ] T010 [US2] Implement cache freshness logic in MistHelper.py: after `_fetch_all_org_data()`, call `_save_cache()` with timestamp. In `phase1_audit()`, call `_load_cache()` first — if fresh, display "Using cached data (collected X minutes ago)" and offer reuse via `InputUtils.safe_input()` or force-refresh. If stale/missing, fetch fresh.
- [ ] T011 [US2] Implement `_build_matrix(self, org_data: dict) -> list[dict]` and `_classify_site(self, ...) -> tuple[bool, bool, str]` in MistHelper.py: build `mxtunnel_lookup` (cluster_id → name), `template_lookup` (template_id → template with WLANs). For each site: resolve assigned template via `applies.site_ids` and `applies.sitegroup_ids`, find matched SSID by name, extract auth type/VLAN/mxtunnel_ids, detect PSK via `wlan.get("auth", {}).get("type", "") in self.PSK_AUTH_TYPES` (FR-012), flag anomalies (0/1/3+ SSIDs, no cluster, no template, target not found) (FR-013), resolve cluster via `mxtunnel_ids[0]` → lookup, assign `target_group` via `self.PILOT_PATTERN.search(site_name)` for pilot or cluster name for production. Return list of row dicts per data-model.md ConsolidationMatrix schema.
- [ ] T012 [US2] Implement `_analyze_deviations(self, matrix: list[dict], org_data: dict) -> list[dict]` in MistHelper.py: group eligible (non-PSK, non-anomaly) sites by `target_group`. For each group, collect matched SSID WLAN JSON dicts. Build union of all keys excluding `self.METADATA_FIELDS`. For each key, collect unique values with site lists and counts. If >1 unique value → deviation. Identify canonical (majority) value. Then cross-cluster drift: compare canonical values across production clusters; flag parameters where they differ. Return list of deviation dicts per data-model.md DeviationReport schema.
- [ ] T013 [US2] Implement `phase1_audit(self)` orchestrator in MistHelper.py: check/load cache → fetch if needed → `_build_matrix()` → `_analyze_deviations()` → output matrix report via `DataExporter.write_with_format_selection(matrix, "ssid_consolidation_matrix", api_function_name="ssidConsolidationMatrix")` → output deviation report via `DataExporter.write_with_format_selection(deviations, "ssid_consolidation_deviations", api_function_name="ssidConsolidationDeviation")` → display summary counts (total sites, eligible, PSK, anomaly) → save cache with matrix + deviations

**Checkpoint**: Phase 1 produces matrix CSV/SQLite with one row per site. PSK sites and anomalies correctly flagged. Deviation report identifies parameter differences within clusters. Cross-cluster drift section populated. Cache file created in `data/`. Re-run offers cached data. ≤10 API calls total.

---

## Phase 4: US3 — Phase 2 Write Site Variables (P2) + US7 Resume

**Goal**: Auto-detect which SSID parameters need site variables from Phase 1 deviations, compute a per-site variable plan, display summary, require CONFIRM, write variables via `updateSiteInfo` with GET→merge→PUT, and save per-site results. Interrupted runs resume from last checkpoint.

**Independent Test**: Run Phases 1 + 2. Verify via Mist API that selected sites now have `MISTHELPER_*` variables in their `vars` dictionary. Re-run shows "already configured" for completed sites. Interrupt and re-run offers resume.

- [ ] T014 [US3] Implement `_compute_variable_plan(self) -> list[dict]` in MistHelper.py: load cached matrix + deviations. For each deviation parameter, derive variable name as `MISTHELPER_<UPPERCASE_PARAM>`. For each eligible (non-PSK, non-anomaly) site, set proposed value from site's current SSID config. Compare with existing `vars` from cached site data: mark `already_configured` (same value), `conflict` (different value), or `pending`. Skip PSK/anomaly sites with `skipped` status and reason. Return list of SiteVariableAssignment dicts per data-model.md.
- [ ] T015 [US3] Implement `_display_variable_summary(self, plan: list[dict])` and `_write_site_variables(self, plan: list[dict], resume_from: list) -> list[dict]` in MistHelper.py: summary displays table (site name, variable name, proposed value, current value, status) with conflict highlighting. Write logic: for each pending site, GET current site vars via cached data, merge new keys (never overwrite existing), PUT via `mistapi.api.v1.sites.sites.updateSiteInfo(apisession, site_id, body={"vars": merged_vars})`. Track success/failure per site. Save checkpoint after each batch for resume support.
- [ ] T016 [US3] Implement `phase2_site_variables(self)` orchestrator in MistHelper.py: `_check_prerequisite(2)` → `_load_cache()` → `_offer_resume(2, ...)` if partial results exist → `_compute_variable_plan()` → `_display_variable_summary()` → `_confirm_or_cancel()` with "CONFIRM" gate → `_write_site_variables()` → save results via `DataExporter.write_with_format_selection(results, "ssid_consolidation_site_vars", api_function_name="ssidConsolidationSiteVars")` + JSON → display success/failure counts

**Checkpoint**: Phase 2 writes site variables to eligible sites. Idempotent: re-run detects "already configured". Conflicts shown in summary. PSK/anomaly sites skipped. Resume works after interruption. Results in CSV + SQLite + JSON.

---

## Phase 5: US4 — Phase 3 Create and Assign Site Groups (P3)

**Goal**: Create 5 site groups (4 production mapped 1:1 to Edge clusters + 1 pilot/test) and assign each eligible site to exactly one group. Missing groups created first. Idempotent: existing correct assignments skipped.

**Independent Test**: Run Phases 1–3. Verify in Mist dashboard that 5 groups exist with correct names and contain the correct sites. Re-run shows "already assigned".

- [ ] T017 [US4] Implement `_compute_group_plan(self) -> dict` in MistHelper.py: define 5 groups — 4 production as `misthelper_prod_<cluster_name>` (one per Edge cluster from cached MxTunnel data) + 1 pilot as `misthelper_pilot`. For each eligible site in matrix, assign to pilot group if `self.PILOT_PATTERN.search(site_name)` matches, else to production group matching its `mxtunnel_id` cluster. Check existing group memberships from cache — mark `already_assigned` or `to_assign`. Return plan dict with groups, site lists, and statuses.
- [ ] T018 [US4] Implement `_ensure_groups_exist(self, plan: dict) -> dict` and `_assign_sites_to_groups(self, plan: dict, resume_from: list) -> list[dict]` in MistHelper.py: `_ensure_groups_exist` checks cached `listOrgSiteGroups` for existing groups by name, creates missing via `mistapi.api.v1.orgs.sitegroups.createOrgSiteGroup(apisession, org_id, body={"name": group_name})`, records group IDs. `_assign_sites_to_groups` for each group: GET current `site_ids`, additive merge (never remove existing), PUT via `updateOrgSiteGroup`. Track per-site success/failure with resume checkpoints.
- [ ] T019 [US4] Implement `phase3_site_groups(self)` orchestrator in MistHelper.py: `_check_prerequisite(3)` → `_load_phase_results(2)` → `_offer_resume(3, ...)` → `_compute_group_plan()` → display plan (group name, cluster mapping, site count, site names) → `_confirm_or_cancel()` → `_ensure_groups_exist()` → `_assign_sites_to_groups()` → save results via `DataExporter.write_with_format_selection(results, "ssid_consolidation_site_groups", api_function_name="ssidConsolidationSiteGroups")` + JSON

**Checkpoint**: 5 site groups exist (created or pre-existing). Each eligible site in exactly one group. Pilot sites identified by name pattern. Results in CSV + SQLite + JSON. Re-run idempotent.

---

## Phase 6: US5 — Phase 4 Create Consolidated Templates (P4)

**Goal**: Create or update 5 WLAN templates with the target SSID using site variable references for site-specific values. Engineer interactively resolves deviations (no pre-selected default). Templates associated with site groups via `applies.sitegroup_ids`. Second SSID runs append without disturbing existing SSIDs.

**Independent Test**: Run Phases 1–4. Verify in Mist dashboard that 5 templates exist with correct SSID, variable references (`{{MISTHELPER_*}}`), and site group associations. Run again for a second SSID — verify append without overwrite.

- [ ] T020 [US5] Implement `_resolve_deviations(self) -> dict` in MistHelper.py: load deviations from cache. For each deviation parameter within each cluster, display all unique values with site counts in a numbered list. Require engineer to select canonical value by number via `InputUtils.safe_input()` — no pre-selected default (FR-027). Log each resolution: parameter, candidate values, selected value, timestamp (FR-028). Return dict mapping (cluster, parameter) → resolved value.
- [ ] T021 [US5] Implement `_build_template_config(self, group_name: str, resolutions: dict) -> dict` in MistHelper.py: construct WLAN config dict. For each parameter: if it was a deviation → use `"{{MISTHELPER_<UPPERCASE_PARAM>}}"` site variable reference; if non-deviated → use canonical value directly. Set `auth`, `vlan_id`, `mxtunnel_ids`, `ssid` name, `enabled: true`. Return complete WLAN config ready for template embedding.
- [ ] T022 [US5] Implement `_create_or_update_templates(self, configs: dict, group_plan: dict) -> list[dict]` in MistHelper.py: for each of 5 groups — derive template name as `misthelper_<group_name>_<basename>` where basename = `os.environ.get("MIST_TEMPLATE_BASENAME", self.target_ssid)` (FR-031). Check existing templates by name. If exists with `misthelper_` prefix → GET template, verify existing SSIDs intact, append new SSID, PUT via `updateOrgTemplate` (FR-030). If exists without `misthelper_` prefix → warn engineer, ask confirmation before overwriting (FR-032). If not exists → create via `createOrgTemplate` with `applies={"sitegroup_ids": [group_id]}` (FR-029). Track success/failure per template.
- [ ] T023 [US5] Implement `phase4_templates(self)` orchestrator in MistHelper.py: `_check_prerequisite(4)` → load Phase 3 results + cached deviations → `_resolve_deviations()` → `_build_template_config()` per group → display full plan (template name, SSID config, variable refs, target site group) → `_confirm_or_cancel()` → `_create_or_update_templates()` → save results via `DataExporter.write_with_format_selection(results, "ssid_consolidation_templates", api_function_name="ssidConsolidationTemplates")` + JSON

**Checkpoint**: 5 templates exist with correct names, active SSIDs with variable references, and site group associations. Deviation resolutions logged. Second SSID appends cleanly. Results in CSV + SQLite + JSON.

---

## Phase 7: US6 — Phase 5 Disable Old SSIDs (P5)

**Goal**: Set the matching target SSID in each old per-site template to `enabled: false` (not deleted), preserving rollback capability. Only the target SSID is touched — all other SSIDs in each template are left untouched. PSK and anomaly sites skipped.

**Independent Test**: Run all 5 phases. Verify old template SSIDs are disabled in the dashboard. Non-target SSIDs unchanged. Re-enable an old SSID manually to confirm rollback works.

- [ ] T024 [US6] Implement `_build_disable_plan(self) -> list[dict]` in MistHelper.py: load matrix from cache. For each eligible (non-PSK, non-anomaly) site: find old template → find matched SSID by ID. If SSID already `enabled: false` → status `already_disabled`. If PSK/anomaly → status `skipped` with reason. If non-matching SSID → leave untouched (FR-034). Else → status `to_disable`. Return list of SSIDDisableResult dicts per data-model.md.
- [ ] T025 [US6] Implement `_disable_ssids(self, plan: list[dict], resume_from: list) -> list[dict]` in MistHelper.py: for each `to_disable` entry, GET template via `getOrgTemplate`, find WLAN by ssid_id in template's WLAN list, set `enabled: false` on that WLAN only, PUT entire template via `updateOrgTemplate(apisession, org_id, template_id, body=updated_template)`. Track success/failure per site. Save checkpoint after each operation for resume support.
- [ ] T026 [US6] Implement `phase5_disable_old(self)` orchestrator in MistHelper.py: `_check_prerequisite(5)` → `_load_phase_results(4)` → `_offer_resume(5, ...)` → `_build_disable_plan()` → display plan (site name, old template name, SSID name, action) → `_confirm_or_cancel()` → `_disable_ssids()` → save results via `DataExporter.write_with_format_selection(results, "ssid_consolidation_disable", api_function_name="ssidConsolidationDisable")` + JSON → display summary (disabled count, already disabled, skipped, failed)

**Checkpoint**: All matching SSIDs in old templates set to `enabled: false`. Non-target SSIDs untouched. PSK/anomaly sites unmodified. Results in CSV + SQLite + JSON. Re-run idempotent ("already disabled").

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final validation, and deployment.

- [ ] T027 [P] Update README.md: add Menu 159 description to the menu operations table, update total operation count, add changelog entry with `version YY.MM.DD.HH.MM` (UTC) format documenting the SSID Template Consolidation Rewrite
- [ ] T028 Final syntax validation: run `python -m py_compile MistHelper.py` — confirm zero errors after all changes
- [ ] T029 Full deployment pipeline: `git add MistHelper.py README.md`, `git commit -m "feat(menu159): SSID Template Consolidation Rewrite - Closes #72"`, `git push origin feat/72-ssid-template-consolidation-rewrite`, create PR to main

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately. All 3 tasks are parallelizable [P].
- **Phase 2 (US1)**: Depends on T002 completion (old launcher removed so new class can occupy its location). T007 (menu update) is parallelizable with T004–T006.
- **Phase 3 (US2)**: Depends on Phase 2 completion (class skeleton must exist). T003 (PK strategies) must also be complete for DataExporter output.
- **Phase 4 (US3)**: Depends on Phase 3 completion (Phase 1 cache required).
- **Phase 5 (US4)**: Depends on Phase 4 completion (Phase 2 results required).
- **Phase 6 (US5)**: Depends on Phase 5 completion (Phase 3 results required).
- **Phase 7 (US6)**: Depends on Phase 6 completion (Phase 4 results required).
- **Phase 8 (Polish)**: Depends on all previous phases. T027 (README) can start after Phase 2.

### User Story Dependencies

| Story | Phase | Can Start After | Independent Test? |
| - | - | - | - |
| US1 (SSID Selector + Menu) | Phase 2 | Setup complete | Yes — no API calls |
| US2 (Phase 1 Audit) | Phase 3 | US1 complete | Yes — read-only API calls |
| US3 (Phase 2 Variables) | Phase 4 | US2 complete | Yes — with Phase 1 cache |
| US4 (Phase 3 Groups) | Phase 5 | US3 complete | Yes — with Phase 2 results |
| US5 (Phase 4 Templates) | Phase 6 | US4 complete | Yes — with Phase 3 results |
| US6 (Phase 5 Disable) | Phase 7 | US5 complete | Yes — with Phase 4 results |
| US7 (Resume) | Phases 2–7 | Integrated into each write phase orchestrator | Yes — interrupt and re-run any write phase |

### Parallel Opportunities

Within each phase, tasks marked [P] can run in parallel:
- **Phase 1**: T001, T002, T003 are all parallelizable (different files/code locations)
- **Phase 2**: T007 (menu update) is parallelizable with T004–T006 (class creation)
- **Phase 8**: T027 (README) is parallelizable with T028 (syntax check)

Cross-phase parallelism is limited because this is a single-file monolith — most changes are sequential within `MistHelper.py`.

### Implementation Strategy

- **MVP = Phase 1 + Phase 2 + Phase 3**: SSID selector, phase menu, and read-only audit. Independently valuable as an audit tool with zero write risk.
- **Incremental delivery**: Each phase adds one write capability. Engineers can stop at any phase and have a working tool.
- **Single SSID per run**: The workflow processes one SSID at a time. Run again for each additional SSID (Phase 4 appends to existing templates).

---

## FR Traceability

| FR | Task(s) | Description |
| - | - | - |
| FR-001 | T004 | Class inside MistHelper.py |
| FR-002 | T007 | Menu 159 registration |
| FR-003 | T001, T002 | Delete old src/ssid_consolidation/ |
| FR-004 | T004 | MIST_TARGET_SSID env var |
| FR-005 | T004 | Runtime SSID override prompt |
| FR-006 | T004 | Single SSID scope per run |
| FR-007 | T005 | Phase sub-menu display |
| FR-008 | T005 | Phase dependency enforcement |
| FR-009 | T009 | 5 org-level bulk API calls |
| FR-010 | T009 | ≤10 paginated calls total |
| FR-011 | T011 | mxtunnel_ids cross-reference |
| FR-012 | T011 | auth.type PSK detection |
| FR-013 | T011 | Anomaly flagging with reason codes |
| FR-014 | T012 | Per-cluster deviation analysis |
| FR-015 | T012 | Cross-cluster drift detection |
| FR-016 | T013 | CSV + SQLite dual output |
| FR-017 | T010 | Cache with freshness timestamp |
| FR-018 | T014 | Auto-detect variable fields from deviations |
| FR-019 | T015 | Summary table + CONFIRM gate |
| FR-020 | T015 | Idempotent variable writes |
| FR-021 | T016 | PSK/anomaly site skip with logging |
| FR-022 | T017 | 5 site groups (4 prod + 1 pilot) |
| FR-023 | T018 | Create missing groups |
| FR-024 | T018 | Idempotent group assignment |
| FR-025 | T019 | Group summary + CONFIRM gate |
| FR-026 | T022, T023 | 5 WLAN templates |
| FR-027 | T020 | Interactive deviation resolution |
| FR-028 | T020 | Resolution audit logging |
| FR-029 | T022 | sitegroup_ids association |
| FR-030 | T022 | Second SSID append logic |
| FR-031 | T022 | Template naming convention |
| FR-032 | T022 | Non-MistHelper naming conflict detection |
| FR-033 | T025 | Set enabled: false |
| FR-034 | T024 | Only target SSID disabled |
| FR-035 | T024 | PSK/anomaly skip in Phase 5 |
| FR-036 | T024 | Already-disabled idempotency |
| FR-037 | T006, T016, T019, T023, T026 | CONFIRM gate on all write phases |
| FR-038 | T006 | Log confirmation with timestamp |
| FR-039 | T016, T019, T023, T026 | Per-site results log |
| FR-040 | T006, T016, T019, T023, T026 | Resume from interruption |
| FR-041 | T004 | safe_input() for all input |
| FR-042 | T013, T016, T019, T023, T026 | Dual CSV + SQLite via DataExporter |
| FR-043 | T003 | PK strategies in ENDPOINT_PRIMARY_KEY_STRATEGIES |
| FR-044 | T009 | No sample data fallback |
| FR-045 | All | Clear NOC engineer language |

---

## Summary

| Metric | Value |
| - | - |
| Total tasks | 29 |
| Setup tasks | 3 |
| US1 (SSID Selector + Menu) | 5 |
| US2 (Phase 1 Audit) | 5 |
| US3 (Phase 2 Variables) | 3 |
| US4 (Phase 3 Groups) | 3 |
| US5 (Phase 4 Templates) | 4 |
| US6 (Phase 5 Disable) | 3 |
| Polish | 3 |
| Parallel opportunities | 6 tasks marked [P] |
| MVP scope | Phases 1–3 (T001–T013): Setup + SSID Selector + Read-Only Audit |
| US7 (Resume) integrated in | T006 (infrastructure), T016, T019, T023, T026 (orchestrators) |
