# Feature Specification: SSID Template Consolidation Rewrite (Menu 159)

**Feature Branch**: `feat/72-ssid-template-consolidation-rewrite`
**Created**: 2026-04-08
**Status**: Draft
**Issue**: #72
**Replaces**: `specs/018-ssid-template-consolidation/` (preserved as reference)
**Input**: User description: "Rewrite the SSID Template Consolidation feature (Menu 159) for MistHelper. Consolidates ~170 per-site WLAN templates into 5 shared templates (4 production mapped 1:1 to Mist Edge clusters + 1 pilot/test) using Mist site variables for per-site configuration and site groups for template assignment. Implemented as a 5-phase guided workflow inside MistHelper.py."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — SSID Selector and Phase Menu (Priority: P1)

A junior NOC engineer selects Menu 159 from the MistHelper main menu. The system reads the default target SSID name from `MIST_TARGET_SSID` in `.env`, displays it, and lets the engineer accept the default or type a different SSID name. After the SSID is selected, the system presents a phase sub-menu (Phases 1–5, or "Run All") and enforces the dependency chain. Only one SSID is processed per run; the engineer runs the workflow again for each additional SSID.

**Why this priority**: The SSID selector and phase menu are the entry point to every phase. Without them, no other functionality is reachable.

**Independent Test**: Launch Menu 159 and verify the prompt displays the `.env` default, accepts Enter for the default, accepts a typed override, and presents the phase sub-menu. No API calls required.

**Acceptance Scenarios**:

1. **Given** `.env` contains `MIST_TARGET_SSID=CorpSecure`, **When** the engineer selects Menu 159, **Then** the prompt displays "Target SSID [CorpSecure]:" and pressing Enter uses "CorpSecure".
2. **Given** `.env` contains `MIST_TARGET_SSID=CorpSecure`, **When** the engineer types "GuestOpen" at the prompt, **Then** the system uses "GuestOpen" for the current session without modifying `.env`.
3. **Given** `.env` does not contain `MIST_TARGET_SSID`, **When** the engineer launches Menu 159, **Then** the prompt displays "Target SSID [none]:" and requires the engineer to enter a value before proceeding.
4. **Given** the SSID is selected, **When** the phase sub-menu appears, **Then** it lists Phase 1 through Phase 5 with brief descriptions and a "Run All Phases" option.
5. **Given** the engineer selects Phase 3 but Phase 2 has not been completed, **When** the system checks prerequisites, **Then** it refuses to proceed and displays: "Phase 3 requires Phase 2 to be completed first. Please run Phase 2 before continuing."

---

### User Story 2 — Phase 1: Read-Only Audit and Matrix Report (Priority: P1)

The engineer selects Phase 1. The system makes 5–7 org-level paginated API calls to collect all WLAN templates, all org WLANs, all sites, all Mist Edge clusters (MxTunnels), and all site groups. It cross-references this data to build a per-site matrix showing: which template each site uses, which SSID matches the target name, the SSID's VLAN/auth/tunnel configuration, which Mist Edge cluster the site connects through, and whether the site uses PSK. It saves the report to `data/` in CSV and SQLite formats.

The system also performs a deviation analysis — comparing the target SSID's configuration parameter-by-parameter within each Edge cluster group, identifying where sites differ. A cross-cluster drift section compares the canonical values across all 4 production clusters.

**Why this priority**: P1 because it is independently valuable as an audit tool and is the foundation for all subsequent phases. No write operations occur.

**Independent Test**: Run Phase 1 against the live org. Verify the output CSV/SQLite contains one row per site. Spot-check 5–10 sites against the Mist dashboard. Verify PSK sites are flagged. Verify anomaly templates (not exactly 2 SSIDs) are flagged. Verify deviation analysis identifies at least one parameter difference within a cluster group.

**Acceptance Scenarios**:

1. **Given** the engineer runs Phase 1, **When** data collection completes, **Then** a matrix report is saved to `data/` in CSV and SQLite formats containing one row per site with columns for: site name, site ID, template name, template ID, matched SSID name, matched SSID ID, authentication type, VLAN assignment(s), Mist Edge cluster name, Mist Edge cluster ID, PSK flag, anomaly flag, and anomaly reason.
2. **Given** a site's SSID uses `auth.type` of `psk`, `psk-tkip`, or `psk-wpa2-tkip`, **When** the report is generated, **Then** that row has `psk_detected = true` and a summary section lists all PSK sites with: "These sites use PSK and are excluded from consolidation."
3. **Given** a template has fewer or more than 2 SSIDs, **When** the report is generated, **Then** that row has `anomaly = true` with a reason code (e.g., "0 SSIDs", "1 SSID", "3+ SSIDs").
4. **Given** the target SSID has differing VLAN values across 3 sites in Cluster A, **When** the deviation report is generated, **Then** it lists the parameter name, each unique value, and the count of sites using each value within Cluster A.
5. **Given** the canonical VLAN value for Cluster A is 100 and for Cluster B is 200, **When** the cross-cluster drift report is generated, **Then** it flags "vlan_id" as a drifting parameter with per-cluster values.
6. **Given** Phase 1 was already run within the cache freshness window, **When** the engineer starts Phase 1 again, **Then** the system displays "Using cached data (collected X minutes ago)" and offers the choice to use cache or force a fresh collection.
7. **Given** the org has ~170 sites, **When** Phase 1 runs, **Then** it completes using no more than 10 paginated API calls total (org-level bulk calls with `limit=1000`), not per-site calls.

---

### User Story 3 — Phase 2: Write Site Variables (Priority: P2)

After reviewing the Phase 1 audit, the engineer runs Phase 2. The system reads cached Phase 1 data, computes the site variables each non-PSK, non-anomaly site needs (at minimum: VLAN values, Mist Edge cluster reference), displays a summary table, and waits for the engineer to type "CONFIRM" before writing any variables via the Mist API.

**Why this priority**: Site variables must exist before consolidated templates can reference them. This is the first write phase.

**Independent Test**: Run Phases 1 + 2, then verify via the Mist API or dashboard that selected sites now have the expected site variables in their `vars` dictionary.

**Acceptance Scenarios**:

1. **Given** Phase 1 data is cached, **When** the engineer runs Phase 2, **Then** the system displays a summary table with columns: site name, variable name, proposed value, current value (if any).
2. **Given** the summary is displayed, **When** the engineer types "CONFIRM", **Then** site variables are written via the Mist API and a per-site results log shows success/failure for each site.
3. **Given** a site already has a variable with the same name and same value, **When** Phase 2 processes that site, **Then** it reports "already configured" and makes no API call (idempotent).
4. **Given** a site already has a variable with the same name but a different value, **When** Phase 2 processes that site, **Then** the conflict is shown in the confirmation summary (current value vs. proposed value).
5. **Given** a site is flagged as PSK or anomaly, **When** Phase 2 runs, **Then** that site is skipped with a log message explaining why.
6. **Given** the engineer types anything other than "CONFIRM", **When** the system reads the input, **Then** it cancels the operation with "Operation cancelled — no changes made."

---

### User Story 4 — Phase 3: Create and Assign Site Groups (Priority: P3)

The engineer runs Phase 3. The system uses the Edge cluster mapping from Phase 1 to assign each non-PSK, non-anomaly site to one of 5 site groups (4 production mapped 1:1 to Edge clusters + 1 pilot/test). Missing site groups are created first. The engineer reviews and confirms before any changes.

**Why this priority**: Site group membership determines which consolidated template each site receives. Must be in place before templates are assigned.

**Independent Test**: Run Phases 1–3, then verify in the Mist dashboard that each of the 5 groups exists and contains the correct sites.

**Acceptance Scenarios**:

1. **Given** Phase 2 is complete, **When** the engineer runs Phase 3, **Then** the system displays: each site group name, the Edge cluster it maps to, the number of sites to be assigned, and the list of site names — then waits for "CONFIRM".
2. **Given** the engineer confirms, **When** groups are created/assigned, **Then** each non-PSK, non-anomaly site is added to exactly one of the 5 groups, and a results log shows success/failure per site.
3. **Given** a target site group does not yet exist, **When** Phase 3 runs, **Then** it creates the missing group before assigning sites.
4. **Given** a site is already in the correct group, **When** Phase 3 processes it, **Then** it reports "already assigned" and does not duplicate the membership.
5. **Given** a site is flagged as PSK or anomaly, **When** Phase 3 runs, **Then** it is skipped with a log message.

---

### User Story 5 — Phase 4: Create Consolidated Templates (Priority: P4)

The engineer runs Phase 4. The system creates or updates 5 WLAN templates (4 production + 1 pilot/test), adding the selected target SSID with site variable references for site-specific values. When deviation analysis from Phase 1 identified differing parameter values, the system presents each deviation to the engineer for interactive resolution before building the template. Templates are associated with site groups via `applies.sitegroup_ids`.

**Why this priority**: Template creation is the culmination of the preparation work. Templates must be created after variables and groups are configured.

**Independent Test**: Run Phases 1–4, then verify in the Mist dashboard that 5 templates exist with the correct SSID, variable references, and site group associations.

**Acceptance Scenarios**:

1. **Given** Phase 3 is complete, **When** the engineer runs Phase 4, **Then** the system displays the full configuration of each template (name, SSID config, variable references, target site group) and waits for "CONFIRM".
2. **Given** Phase 1 deviation analysis found 3 different VLAN values within Cluster A, **When** Phase 4 processes Cluster A, **Then** it presents all 3 values with site counts and requires the engineer to select one canonical value.
3. **Given** the engineer confirms, **When** templates are created, **Then** each template has the selected SSID using site variable references, associated with its site group via `applies.sitegroup_ids`, and a results log confirms success/failure per template.
4. **Given** a template already exists from a prior SSID run, **When** Phase 4 runs for the second SSID, **Then** it detects the existing template, verifies the first SSID is intact, and appends the new SSID without disturbing it.
5. **Given** the pilot/test template, **When** it is created, **Then** it is clearly labeled with "pilot" in both its name and metadata.
6. **Given** `.env` contains `MIST_TEMPLATE_BASENAME=MyOrg`, **When** templates are named, **Then** names follow the pattern `misthelper_<group>_MyOrg` (e.g., `misthelper_prod_cluster1_MyOrg`). If `MIST_TEMPLATE_BASENAME` is not set, the selected SSID name is used.
7. **Given** an existing template with the same name exists but was NOT created by this tool, **When** Phase 4 detects the conflict, **Then** it warns the engineer and asks for confirmation before overwriting.

---

### User Story 6 — Phase 5: Disable Old SSIDs (Priority: P5)

After the new templates are verified, the engineer runs Phase 5. The system sets the matching SSID in each old per-site template to `enabled: false` (not deleted), preserving rollback capability. PSK and anomaly sites are skipped.

**Why this priority**: This is the final cutover step. Must happen last, after all new templates are confirmed working.

**Independent Test**: Run all 5 phases, then verify old template SSIDs are disabled in the dashboard and only new consolidated template SSIDs are active.

**Acceptance Scenarios**:

1. **Given** Phase 4 is complete, **When** the engineer runs Phase 5, **Then** the system lists every old template and SSID to be disabled (site name, template name, SSID name) and waits for "CONFIRM".
2. **Given** the engineer confirms, **When** SSIDs are disabled, **Then** each matching SSID in each old template is set to `enabled: false`, and a results log shows success/failure per SSID.
3. **Given** a site is flagged as PSK or anomaly, **When** Phase 5 runs, **Then** its SSIDs are not touched and the log confirms the skip.
4. **Given** an old SSID is already disabled, **When** Phase 5 processes it, **Then** it reports "already disabled" and makes no API call.
5. **Given** a non-matching SSID exists in the same old template, **When** Phase 5 runs, **Then** that SSID is left untouched (only the target SSID is disabled).

---

### User Story 7 — Resume After Interruption (Priority: P2)

If the engineer's session is interrupted during any write phase (2–5), the per-site results log records which sites were successfully processed. On the next run of that phase, the system detects the partial results and offers to resume from where it stopped.

**Why this priority**: P2 because network interruptions during 170-site operations are likely, and resumability prevents wasted API calls and incomplete states.

**Independent Test**: Run Phase 2 for 170 sites, interrupt after ~50, re-run Phase 2, verify it offers to resume and picks up at site ~51.

**Acceptance Scenarios**:

1. **Given** Phase 2 was interrupted after processing 50 of 170 sites, **When** the engineer re-runs Phase 2, **Then** the system detects the partial results log and displays: "Previous run processed 50 of 170 sites. Resume from where it stopped?"
2. **Given** the engineer accepts the resume, **When** Phase 2 continues, **Then** it skips the 50 already-processed sites and processes only the remaining 120.
3. **Given** the engineer declines the resume, **When** Phase 2 restarts, **Then** it processes all 170 sites from the beginning (idempotent — already-processed sites receive "already configured" status without redundant writes).

---

### Edge Cases

- **API rate limit**: When the Mist API returns 429 during bulk operations, the system uses existing `API_REQUEST_MAX_RETRIES` and `API_REQUEST_RETRY_DELAY` retry/backoff patterns. Phase 1 uses ~5–7 paginated calls total (not 170 per-site calls), staying well under the 5000 calls/hour limit.
- **Site with no template**: Flagged as anomaly in Phase 1, skipped in Phases 2–5 with a log message.
- **Template with 0, 1, or 3+ SSIDs**: Flagged as anomaly in Phase 1, included in the matrix report, excluded from modification phases.
- **SSID name not found in a template**: That template/site is flagged as "target SSID not found" and excluded from modification phases.
- **Phase run out of order**: System checks for prerequisite data (Phase 1 cache, Phase 2 results, Phase 3 results, Phase 4 results) and refuses with a clear message naming the missing prerequisite.
- **Network loss mid-operation**: Results log tracks last successful site. Next run detects partial results and offers resume.
- **Variable name conflict**: Phase 2 detects existing variables with the same name but different values and includes them in the confirmation summary.
- **Duplicate run (idempotent)**: Running any phase twice produces no duplicates — cached data, "already configured", "already assigned", "already disabled" checks prevent redundant writes.
- **Second SSID run**: Phase 4 detects existing templates from the first SSID run and appends the new SSID without overwriting.
- **EOF in SSH/container context**: All `input()` calls use `safe_input()` wrapper for clean session termination.

---

## Requirements *(mandatory)*

### Functional Requirements

**Architecture & Integration**

- **FR-001**: All code MUST be implemented as classes within `MistHelper.py`, following the same pattern as `E911BSSIDReportGenerator`, `FirmwareManager`, and other existing classes. No separate packages or modules.
- **FR-002**: Feature MUST be registered as Menu option **159** in the main menu system, replacing the old broken implementation.
- **FR-003**: The old implementation in `src/ssid_consolidation/` MUST be deleted as part of this rewrite.

**SSID Selector**

- **FR-004**: System MUST read a default target SSID name from the `MIST_TARGET_SSID` environment variable. If set, display it as the default; if not set, require the engineer to enter a value.
- **FR-005**: System MUST allow the engineer to override the default SSID at runtime without modifying `.env`.
- **FR-006**: The selected SSID defines the scope for the entire run: only the matching SSID is collected, variablized, consolidated, and disabled. All other SSIDs in each template are ignored for modification purposes.

**Phase Menu & Dependencies**

- **FR-007**: System MUST present a phase selection sub-menu after SSID selection: Phase 1 through Phase 5, plus "Run All Phases Sequentially".
- **FR-008**: System MUST enforce strict phase dependency: Phase 2 requires Phase 1 data. Phase 3 requires Phase 2. Phase 4 requires Phase 3. Phase 5 requires Phase 4. If a prerequisite is missing, refuse with a clear message naming the missing phase.

**Phase 1: Data Collection & Matrix Report**

- **FR-009**: System MUST use org-level bulk API calls with `limit=1000` and `mistapi.get_all()` pagination:
  - `mistapi.api.v1.orgs.wlantemplates.listOrgTemplates(session, org_id)` — all WLAN templates
  - `mistapi.api.v1.orgs.wlans.listOrgWlans(session, org_id)` — all org WLANs (NOT per-site)
  - `mistapi.api.v1.orgs.sites.listOrgSites(session, org_id)` — all sites
  - `mistapi.api.v1.orgs.mxtunnels.listOrgMxTunnels(session, org_id)` — Mist Edge clusters
  - `mistapi.api.v1.orgs.sitegroups.listOrgSiteGroups(session, org_id)` — existing site groups
- **FR-010**: Phase 1 MUST complete using no more than ~10 paginated API calls total. Per-site API calls are prohibited.
- **FR-011**: System MUST cross-reference WLAN `mxtunnel_ids` or `mxtunnel_name` fields with `listOrgMxTunnels` results to resolve which Edge cluster each site connects through. The field `site.edge_cluster_id` does NOT exist and MUST NOT be used.
- **FR-012**: System MUST detect PSK SSIDs by checking `wlan["auth"]["type"]` for values `psk`, `psk-tkip`, `psk-wpa2-tkip`. Checking `wlan.get("psk")` is WRONG and MUST NOT be used.
- **FR-013**: System MUST flag templates with fewer or more than 2 SSIDs as anomalies, with reason codes. Anomalous templates appear in the report but are excluded from Phases 2–5.
- **FR-014**: System MUST perform deviation analysis: for the selected SSID, compare every WLAN JSON field (excluding `id`, `org_id`, `site_id`, `template_id`, `created_time`, `modified_time`) parameter-by-parameter within each Edge cluster group. Report each differing parameter with unique values and site counts.
- **FR-015**: System MUST perform cross-cluster drift detection: compare canonical values across all 4 production clusters and flag parameters where canonical values differ between clusters.
- **FR-016**: System MUST generate the matrix report in both CSV and SQLite formats via `DataExporter.write_with_format_selection()`, saved to the `data/` directory.
- **FR-017**: System MUST cache all collected data with a freshness timestamp. When cache is fresh, offer to reuse or force-refresh. Cache format must support resume logic in Phases 2–5.

**Phase 2: Site Variable Configuration**

- **FR-018**: System MUST compute required site variables from Phase 1 data: at minimum VLAN values and Mist Edge cluster reference.
- **FR-019**: System MUST display a summary table (site name, variable name, proposed value, current value) and require "CONFIRM" before writing.
- **FR-020**: System MUST be idempotent: if a variable already exists with the same value, skip with "already configured". If the value differs, show the conflict in the confirmation summary.
- **FR-021**: System MUST skip PSK-flagged and anomaly-flagged sites, logging each skip with reason.

**Phase 3: Site Group Assignment**

- **FR-022**: System MUST assign each non-PSK, non-anomaly site to one of 5 groups: 4 production groups mapped 1:1 to Edge clusters + 1 pilot/test group.
- **FR-023**: System MUST create missing site groups before assigning sites.
- **FR-024**: System MUST be idempotent: if a site is already in the correct group, report "already assigned" without duplicating.
- **FR-025**: System MUST display group assignments and require "CONFIRM" before writing.

**Phase 4: Template Creation**

- **FR-026**: System MUST create or update 5 WLAN templates (4 production + 1 pilot/test). Each run adds only the selected target SSID using site variable references for site-specific values.
- **FR-027**: When deviation analysis found differing values, system MUST present all unique values per parameter with site counts and require the engineer to select one canonical value. No pre-selected default.
- **FR-028**: System MUST log each deviation resolution (parameter, candidate values, selected value, timestamp) for audit.
- **FR-029**: System MUST associate templates with site groups via `applies.sitegroup_ids` exclusively. No direct `site_id` bindings.
- **FR-030**: On re-run for a second SSID, system MUST detect existing templates, verify the first SSID is intact, and append the new SSID without disturbing it.
- **FR-031**: Template names MUST follow the pattern: `misthelper_<group_id>_<basename>` where basename comes from `MIST_TEMPLATE_BASENAME` env var (if set) or the selected SSID name.
- **FR-032**: System MUST detect naming conflicts with existing non-MistHelper templates and warn before overwriting.

**Phase 5: Disable Old SSIDs**

- **FR-033**: System MUST set the matching SSID in each old per-site template to `enabled: false`, preserving all other configuration for rollback.
- **FR-034**: Non-matching SSIDs in each old template MUST NOT be touched.
- **FR-035**: System MUST skip PSK and anomaly sites, logging each skip.
- **FR-036**: System MUST not disable already-disabled SSIDs (idempotent).

**Confirmation & Safety**

- **FR-037**: All write phases (2, 3, 4, 5) MUST display a detailed summary of planned changes and require the engineer to type "CONFIRM" (exact match) before proceeding. Any other input cancels.
- **FR-038**: System MUST log the engineer's confirmation entry with timestamp to the script log.
- **FR-039**: System MUST produce a per-site success/failure results log after each write phase, saved to `data/`.
- **FR-040**: System MUST track processing progress during write phases. If interrupted and re-run, detect previously completed sites via the results log and offer to resume.
- **FR-041**: All `input()` calls MUST use `safe_input()` for EOF handling in SSH/container contexts.

**Output & Caching**

- **FR-042**: All reports MUST be saved in both CSV and SQLite formats to `data/` via `DataExporter.write_with_format_selection()`.
- **FR-043**: System MUST add primary key strategy entries to `ENDPOINT_PRIMARY_KEY_STRATEGIES` for new database tables.
- **FR-044**: If the API returns no matches for any query, the system MUST report it honestly. No sample data fallback. No silently fabricated data.

**Communication**

- **FR-045**: All user-facing messages MUST use clear, calm, professional language suitable for junior NOC engineers. Direct, specific, free of jargon.

### Key Entities

- **WLAN Template**: A named configuration container holding one or more SSID/WLAN configurations. Currently ~170 (one per site); target is 5 consolidated. Key attributes: name, ID, `applies` field (with `sitegroup_ids`, `site_ids`, `org_id`), list of contained WLANs.
- **SSID/WLAN**: An individual wireless network within a template. Key attributes: name, ID, `enabled` state, `auth.type` (802.1X, open, psk, psk-tkip, psk-wpa2-tkip), VLAN assignment, `mxtunnel_ids`/`mxtunnel_name`, site variable references.
- **Site**: A physical location. Key attributes: name, ID, assigned template, site group memberships, `vars` dictionary (site variables).
- **Site Variable**: A key-value pair in a site's `vars` dictionary that templates reference for site-specific values (e.g., `{{VLAN_ID}}`, `{{MXTUNNEL_ID}}`).
- **Site Group**: A logical grouping of sites. Templates target site groups via `applies.sitegroup_ids`. Key attributes: name, ID, member site list.
- **Mist Edge Cluster (MxTunnel)**: A tunneling endpoint retrieved via `listOrgMxTunnels`. 4 clusters serve ~170 sites. Key attributes: name, ID. Sites reference clusters via WLAN `mxtunnel_ids`/`mxtunnel_name`.
- **Consolidation Matrix**: Phase 1 output — tabular dataset (CSV + SQLite) with one row per site and columns for all collected config, flags, and deviations.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Active WLAN templates managing production SSIDs are reduced from ~170 to exactly 5, verified by re-running Phase 1 after full completion.
- **SC-002**: 100% of non-PSK, non-anomaly sites have correct site variables configured, verified by a post-Phase-2 comparison of expected vs. actual values.
- **SC-003**: 100% of non-PSK, non-anomaly sites are assigned to exactly one of the 5 target site groups, verified by post-Phase-3 group membership check.
- **SC-004**: All 5 consolidated templates are created with active SSIDs and correct site variable references that resolve correctly per site.
- **SC-005**: 100% of matching SSIDs in old per-site templates are disabled (not deleted) for non-PSK, non-anomaly sites.
- **SC-006**: Zero PSK sites are modified by any phase.
- **SC-007**: A junior NOC engineer can complete the full 5-phase workflow in under 60 minutes using only on-screen guidance, without external documentation.
- **SC-008**: Every write phase produces a confirmation summary reviewed before "CONFIRM", and every confirmation is logged with a timestamp. Zero unconfirmed changes.
- **SC-009**: If any phase is interrupted, re-running resumes idempotently without duplicate resources or skipped sites.
- **SC-010**: Phase 1 uses no more than 10 org-level API calls total (not 170+ per-site calls), staying within the 5000 calls/hour rate limit.

---

## Assumptions

- The Mist organization has a single org ID configured via `MIST_ORG_ID` or `ORG_ID` in `.env`.
- `mistapi` >= 0.59.0 provides all required API endpoints: `orgs.wlantemplates`, `orgs.wlans`, `orgs.sites`, `orgs.mxtunnels`, `orgs.sitegroups`, `orgs.sites` (for site settings/vars updates).
- Each of the ~170 sites currently has one template assigned, and each template typically contains 2 SSIDs (one secured, one open/guest). Deviations are treated as anomalies.
- The 4 Mist Edge clusters already exist and are correctly configured. This feature does not create or modify clusters.
- The default Mist Edge cluster-to-site mapping is determined by cross-referencing WLAN `mxtunnel_ids`/`mxtunnel_name` with `listOrgMxTunnels` results. There is no `site.edge_cluster_id` field.
- Template-to-site assignment uses `applies.sitegroup_ids`. Templates do NOT use direct `site_ids` for the new consolidated templates.
- The `data/` directory is writable (validated by existing `FilePermissionValidator`).
- API rate limits are manageable with existing retry/backoff configuration.
- The `.env` file follows existing `python-dotenv` patterns.
- The pilot/test site group membership is determined by a consistent mechanism (e.g., site name pattern, a tag, or manual designation during Phase 3).
- All code changes are confined to `MistHelper.py` (classes) and the menu registration section.
