# Feature Specification: WiFi SSID Template Consolidation & Overhaul

**Feature Branch**: `018-ssid-template-consolidation`
**Created**: 2025-07-02
**Status**: Clarified
**Input**: User description: "New menu option in MistHelper that performs a comprehensive WiFi SSID template consolidation — reducing ~170 per-site templates down to 5 consolidated templates using site variables, site groups, and a multi-phase guided workflow."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Discover & Audit All Existing Templates (Priority: P1)

A junior NOC engineer needs to understand the current state of all WLAN templates across the organization before any changes can be planned. They select the new menu option and the system collects every template, every SSID within each template, every site assignment, every Mist Edge cluster reference, and every site-specific value — then presents a clear, exportable matrix report. Sites that use PSK-based authentication are clearly flagged as out-of-scope so the engineer knows exactly which sites will and will not be touched.

**Why this priority**: Without a complete, accurate inventory of the current state, no consolidation work can proceed safely. This phase is the foundation for every subsequent phase and is independently valuable as an audit tool.

**Independent Test**: Can be fully tested by running Phase 1 alone against the live organization and verifying the output report against a manual spot-check of 5–10 known sites. Delivers immediate value as a standalone audit/inventory export.

**Acceptance Scenarios**:

1. **Given** the engineer selects the SSID Template Consolidation menu option and chooses Phase 1, **When** the system finishes data collection, **Then** a matrix report is saved to the `data/` directory in both CSV and SQLite formats containing one row per site with columns for: site name, site ID, assigned template name, template ID, secured SSID name, secured SSID ID, open/guest SSID name, open/guest SSID ID, Mist Edge cluster name, Mist Edge cluster ID, VLAN assignments, authentication type, and a PSK flag (true/false).
2. **Given** any site's template contains an SSID using PSK authentication, **When** the matrix report is generated, **Then** that site's row is marked with `psk_detected = true` and a separate summary section lists all PSK sites with a clear message: "These sites use PSK and are excluded from consolidation."
3. **Given** the engineer has already run Phase 1 within the cache freshness window, **When** they start Phase 1 again, **Then** the system detects fresh cached data, displays "Using cached data (collected X minutes ago)", and offers the choice to use cached data or force a fresh collection.
4. **Given** the organization has templates with varying numbers of SSIDs (not exactly 2), **When** the system encounters a template with fewer or more than 2 SSIDs, **Then** it flags that template as an anomaly in the report and continues processing without failing.

---

### User Story 2 — Configure Site Variables for Consolidation (Priority: P2)

After reviewing the Phase 1 audit, the engineer proceeds to Phase 2 to set up site-level variables that the new consolidated templates will reference. The system reads the per-site unique values extracted in Phase 1 (VLAN ranges, edge cluster references, and other site-specific configuration) and writes them as Mist site variables on each site's settings. This prepares sites to be served by shared templates that use variable substitution instead of hard-coded values.

**Why this priority**: Site variables must exist before consolidated templates can be created and assigned, because the templates will reference these variables. This is the second link in the chain.

**Independent Test**: Can be tested by running Phase 1 + Phase 2, then verifying via the Mist dashboard or API that selected sites now have the expected site variables configured in their site settings.

**Acceptance Scenarios**:

1. **Given** Phase 1 data is available (cached or freshly collected), **When** the engineer runs Phase 2, **Then** the system displays a summary table showing each site and the variables that will be written (variable name, proposed value, current value if any) and waits for CONFIRM before making any changes.
2. **Given** the engineer types "CONFIRM" at the confirmation prompt, **When** site variables are written, **Then** each site's settings are updated via the Mist API with the calculated variables, and a results log shows success/failure per site.
3. **Given** a site already has a site variable with the same name but a different value, **When** Phase 2 processes that site, **Then** the existing value is shown alongside the proposed new value in the confirmation summary and the engineer is informed of the override.
4. **Given** a site is flagged as PSK in Phase 1, **When** Phase 2 runs, **Then** that site is skipped entirely and a message confirms it was skipped due to PSK status.

---

### User Story 3 — Organize Sites into Template Groups (Priority: P3)

The engineer proceeds to Phase 3 to assign sites to the appropriate site groups that map to the 5 new consolidated templates (4 production + 1 pilot/test). The system uses the Mist Edge cluster mapping from Phase 1 and any additional grouping logic to place each site into the correct site group via tags.

**Why this priority**: Site group membership determines which consolidated template each site will receive. This must be in place before templates are assigned but after variables are configured.

**Independent Test**: Can be tested by running Phases 1–3, then verifying in the Mist dashboard that sites belong to the expected site groups and that each of the 5 target groups contains the correct set of sites.

**Acceptance Scenarios**:

1. **Given** Phase 1 data is available and the engineer runs Phase 3, **When** the system calculates group assignments, **Then** it displays a summary showing: each site group name, the number of sites assigned to it, and the list of site names per group — and waits for CONFIRM.
2. **Given** the engineer confirms, **When** site group assignments are written, **Then** each non-PSK site is added to exactly one of the 5 site groups via the Mist API, and a results log shows success/failure per site.
3. **Given** a site is already a member of the target site group, **When** Phase 3 processes that site, **Then** it reports "already assigned" and does not duplicate the membership.
4. **Given** one of the 5 target site groups does not yet exist in the organization, **When** Phase 3 runs, **Then** the system creates the missing site group before assigning sites to it.

---

### User Story 4 — Create Consolidated Templates (Priority: P4)

The engineer proceeds to Phase 4 to create or update the 5 WLAN templates. Each run adds the selected target SSID (using site variable references for site-specific values) to each template. If the template does not yet exist, it is created; if it already exists from a prior run for the other SSID, the new SSID is appended. The templates are associated with their corresponding site groups so they apply to the correct sites.

**Why this priority**: Template creation is the culmination of the preparation work. Templates must be created after variables and groups are in place so they can be validated immediately.

**Independent Test**: Can be tested by running Phases 1–4, then verifying in the Mist dashboard that 5 new templates exist with correct SSID configurations and site-group associations, and that site variable references resolve correctly for a sample of sites.

**Acceptance Scenarios**:

1. **Given** site variables and site groups are configured, **When** the engineer runs Phase 4, **Then** the system displays the full configuration of each of the 5 templates (name, the selected SSID configuration, variable references, site group assignment) and waits for CONFIRM.
2. **Given** the engineer confirms, **When** templates are created or updated, **Then** each of the 5 templates has the selected target SSID added (with site variable substitution for site-specific values), and a results log confirms each template was created or updated successfully.
3. **Given** a template with the same name already exists from a prior SSID run, **When** Phase 4 runs, **Then** the system detects the existing template, verifies the previously added SSID is intact, and appends the new SSID without disturbing the first.
4. **Given** the pilot/test template (1 of the 5), **When** it is created, **Then** it is clearly labeled as pilot/test in both its name and its configuration metadata.

---

### User Story 5 — Disable Old Template SSIDs (Priority: P5)

After the new templates are active and verified, the engineer runs Phase 5 to disable the SSIDs in the old ~170 per-site templates. SSIDs are set to disabled (not deleted), preserving the old configuration as a rollback reference. PSK sites are skipped.

**Why this priority**: This is the final cutover step. It must happen last, after all new templates are confirmed working. Disabling rather than deleting preserves rollback capability.

**Independent Test**: Can be tested by running all 5 phases, then verifying that old template SSIDs are disabled in the Mist dashboard and that only the new consolidated template SSIDs are active.

**Acceptance Scenarios**:

1. **Given** the new 5 consolidated templates are in place, **When** the engineer runs Phase 5, **Then** the system displays a list of every old template and every SSID that will be disabled (with site name, template name, SSID name) and waits for CONFIRM.
2. **Given** the engineer confirms, **When** old SSIDs are disabled, **Then** each SSID in each old template is set to `enabled: false` via the Mist API, and a results log shows success/failure per SSID per template.
3. **Given** a site is flagged as PSK, **When** Phase 5 runs, **Then** that site's template SSIDs are not touched and the log confirms the site was skipped.
4. **Given** an old template's SSID is already disabled, **When** Phase 5 processes it, **Then** it reports "already disabled" and does not make a redundant API call.

---

### User Story 6 — SSID Selector via .env with Runtime Override (Priority: P1)

Before any phase executes, the system reads a default target SSID name from the `.env` file, displays it to the engineer, and allows them to accept the default or type a different SSID name. The selector picks exactly one SSID; only that SSID is collected, variablized, and consolidated across all phases — all other SSIDs in each template are ignored. To consolidate both SSIDs (e.g., secured and open/guest), the engineer runs the full workflow twice, once per SSID.

**Why this priority**: P1 because it is a prerequisite for all phases — the system must know which SSID to work with before any data collection or modification begins.

**Independent Test**: Can be tested independently by launching the menu option and verifying the prompt displays the `.env` default, accepts Enter to use the default, and accepts a typed override value.

**Acceptance Scenarios**:

1. **Given** the `.env` file contains `MIST_TARGET_SSID=CorpSecure`, **When** the engineer launches the consolidation menu option, **Then** the prompt displays "Target SSID [CorpSecure]:" and pressing Enter uses "CorpSecure".
2. **Given** the `.env` file contains `MIST_TARGET_SSID=CorpSecure`, **When** the engineer types "GuestOpen" at the prompt, **Then** the system uses "GuestOpen" for the current session without modifying the `.env` file.
3. **Given** the `.env` file does not contain `MIST_TARGET_SSID`, **When** the engineer launches the menu option, **Then** the prompt displays "Target SSID [none]:" and requires the engineer to enter a value before proceeding.

---

### Edge Cases

- What happens when the Mist API rate-limits the script during bulk operations across ~170 sites? The system must implement retry logic with backoff, following the existing `API_REQUEST_MAX_RETRIES` and `API_REQUEST_RETRY_DELAY` patterns.
- What happens when a site has no template assigned? The system must flag that site as an anomaly in the Phase 1 report and skip it in subsequent phases.
- What happens when a template has 0 SSIDs, 1 SSID, or more than 2 SSIDs? The system must flag the anomaly, include the site in the report, and skip it during modification phases with a clear warning.
- What happens when the engineer runs Phase 3, 4, or 5 without having completed the prerequisite phases? The system must check for the existence of prerequisite data (cached Phase 1 results, configured site variables, created site groups) and refuse to proceed with a clear message stating which prerequisite phase must be run first.
- What happens when network connectivity is lost mid-operation? The system must log the last successfully processed site. On the next run, the results log from the interrupted phase enables the system to detect already-completed sites and offer to resume from where it left off (see FR-024a).
- What happens when a site variable name conflicts with an existing variable used by a different feature? The system must detect existing variables with the same name and present the conflict to the engineer before overwriting.
- What happens when the engineer runs the full workflow a second time (e.g., after a partial rollback)? Cached data and idempotent API calls must ensure the system does not create duplicate templates, duplicate site groups, or duplicate site variables.
- What happens when the engineer runs Phase 4 for the second SSID and consolidated templates already exist from the first SSID run? The system must detect the existing template, verify the previously added SSID is intact, and append the new SSID without overwriting or duplicating the first.

---

## Requirements *(mandatory)*

### Functional Requirements

**Menu & Configuration**

- **FR-001**: System MUST provide a menu option accessible from the main menu that launches the SSID Template Consolidation workflow.
- **FR-002**: System MUST read a default target SSID name from environment configuration, display it to the engineer at startup, and allow the engineer to accept the default or override it for the current session. If no default is configured, the system MUST require the engineer to enter a value before proceeding. The selected SSID name defines the scope for the entire run: only that SSID is collected, variablized, and consolidated; other SSIDs in each template are ignored.
- **FR-003**: System MUST present a phase selection sub-menu after launch, allowing the engineer to run any individual phase (1–5) or all phases sequentially.
- **FR-004**: System MUST enforce a strict phase dependency chain: Phase 2 requires Phase 1 data. Phase 3 requires Phase 2 completion. Phase 4 requires Phase 3 completion. Phase 5 requires Phase 4 completion. If a prerequisite phase has not been completed, the system MUST refuse to proceed and display a clear message naming the missing prerequisite.

**Phase 1: Data Collection & Matrix Report**

- **FR-005**: System MUST retrieve all organization WLAN templates and extract template-level metadata (template name, template ID, site assignment). For SSID-level detail, the system MUST extract configuration only for the SSID matching the selected target SSID name — including VLAN configurations, authentication type, and Mist Edge cluster/tunnel references. Non-matching SSIDs within each template are recorded by name and ID for the matrix report but are not deeply inspected or compared.
- **FR-006**: System MUST identify and flag any site whose SSID uses PSK authentication, marking it with a `psk_detected` indicator.
- **FR-006a**: System MUST classify each SSID within a template as either "secured" (using 802.1X/enterprise authentication) or "open/guest" (using open authentication or captive portal) based on the SSID's authentication type. If the authentication type does not clearly map to either category (e.g., PSK), the system MUST flag it as an anomaly.
- **FR-007**: System MUST identify which of the 4 Mist Edge clusters each site's template references, capturing the cluster name and ID.
- **FR-008**: System MUST generate a matrix report saved in both CSV and SQLite formats to the local data output directory.
- **FR-009**: System MUST cache all collected data locally with a freshness timestamp and reuse cached data when it is within the configured freshness window. The engineer MUST be able to force a fresh collection even when cache is fresh.
- **FR-010**: System MUST flag templates that do not contain exactly 2 SSIDs as anomalies in the report, with a reason code (e.g., "0 SSIDs", "1 SSID", "3+ SSIDs"). Anomalous templates MUST be included in the Phase 1 report but excluded from modification in Phases 2–5, with a clear log message explaining why each was skipped.
- **FR-010a**: System MUST perform a deviation analysis across all non-PSK, non-anomaly templates, comparing settings parameter-by-parameter **for the selected target SSID only** within each target consolidation group (i.e., per Mist Edge cluster). The comparison scope is **every field in the matching WLAN JSON object** except the following metadata fields which are excluded: `id`, `org_id`, `site_id`, `template_id`, `created_time`, `modified_time`. For each parameter where values differ across sites, the system MUST report every unique value found and the count of sites using each value. This deviation report is included in the Phase 1 matrix output.
- **FR-010b**: After per-cluster deviation analysis, the system MUST perform a **cross-cluster drift detection** pass. All 4 production consolidation groups are expected to share an identical base SSID configuration (excluding site-variable-resolved values). The system MUST compare the majority/canonical value for each parameter across all 4 clusters and flag any parameter where the canonical values differ between clusters. Cross-cluster drift is reported as a separate section in the Phase 1 deviation report, listing each drifting parameter with the per-cluster values.

**Phase 2: Site Variable Configuration**

- **FR-011**: System MUST read the Phase 1 cached data and compute the site variables needed for each site, including at minimum: VLAN range values and Mist Edge cluster reference.
- **FR-012**: System MUST write site variables to each site's settings. If a site already has a variable with the same name and the same value, the system MUST skip the write and report "already configured" (idempotent behavior). If the existing value differs, the system MUST include the conflict in the confirmation summary.
- **FR-013**: System MUST skip all PSK-flagged sites and all anomaly-flagged sites during variable configuration, logging each skip with the reason.

**Phase 3: Site Group Assignment**

- **FR-014**: System MUST assign each non-PSK, non-anomaly site to one of 5 site groups. The default grouping rule is: each of the 4 Mist Edge clusters maps to one production site group (1:1), and the fifth group is for pilot/test sites. The system MUST create any missing site groups before assigning sites.
- **FR-015**: System MUST verify site group membership is idempotent — if a site is already in the correct group, no duplicate assignment is created.

**Phase 4: Template Creation**

- **FR-016**: System MUST create or update 5 WLAN templates (4 production + 1 pilot/test). Each run adds **only the selected target SSID** to each template, using site variable references for site-specific configuration values. If a target template does not yet exist, the system creates it with the single selected SSID. If the template already exists (e.g., from a prior run for the other SSID), the system MUST append the selected SSID to the existing template without disturbing the previously added SSID.
- **FR-016a**: During template creation, when the Phase 1 deviation analysis identifies parameters with differing values across sites within a consolidation group, the system MUST present all unique values for each deviating parameter (with site counts) and require the engineer to explicitly select one canonical value per parameter. No value is pre-selected as default; the engineer must make an active choice for every deviation.
- **FR-016b**: The system MUST log each deviation resolution choice (parameter name, all candidate values, selected value, engineer confirmation timestamp) to the results log for audit purposes.
- **FR-017**: System MUST associate each new template with its corresponding site group exclusively via `sitegroup_ids`. No direct `site_id` bindings are used; site membership in the site group is the sole mechanism controlling which sites receive a template.
- **FR-018**: System MUST detect naming conflicts with existing templates and prompt the engineer before overwriting.
**FR-016c**: System MUST generate consolidated template names by deriving a base name from environment configuration (prefer the `MIST_TEMPLATE_BASENAME` variable if present, otherwise use the selected `MIST_TARGET_SSID`), combined with the target group identifier (e.g., `prod_cluster1`) to produce predictable, idempotent names such as `misthelper_prod_cluster1_CorpSecure`.

### Session 2026-04-06


**Phase 5: Disable Old SSIDs**

- **FR-019**: System MUST set the SSID matching the selected target SSID name in each old per-site template to disabled, preserving all other configuration for rollback purposes. Non-matching SSIDs in each old template are not touched.
- **FR-020**: System MUST skip all PSK-flagged sites and all anomaly-flagged sites during the disable operation, logging each skip with the reason.
- **FR-021**: System MUST not disable SSIDs that are already disabled.

**Confirmation & Safety**

- **FR-022**: System MUST display a detailed summary of all planned changes before any modification phase (2, 3, 4, 5) and require the user to type "CONFIRM" (exact string match) before proceeding.
- **FR-023**: System MUST log the user's confirmation entry (including timestamp) to the script log.
- **FR-024**: System MUST produce a per-site success/failure results log after each modification phase, saved to the local data output directory.
- **FR-024a**: System MUST track processing progress during each modification phase. If a phase is interrupted and re-run, the system MUST detect previously completed sites (via the results log) and offer to resume from where processing stopped rather than restarting from the beginning.

**Output & Caching**

- **FR-025**: System MUST save all reports and data in both CSV and SQLite formats to the local data output directory.
- **FR-026**: System MUST cache all API-retrieved data with a freshness mechanism, using the configured cache freshness window as the default.
- **FR-027**: System MUST offer the engineer the option to force a fresh data collection even when cached data is within the freshness window.

**Communication Style**

- **FR-028**: All user-facing messages MUST use clear, professional, reassuring language suitable for junior NOC engineers — direct, calm, specific, and free of jargon. Think Fred Rogers explaining what's happening, combined with NASA/JPL mission-control precision about what will change and what safeguards are in place.

### Key Entities

- **WLAN Template**: A named configuration container that holds one or more SSID/WLAN configurations. Currently ~170 exist (one per site); target state is 5 consolidated templates. Key attributes: name, ID, associated site or site group, list of contained WLANs.
- **SSID/WLAN**: An individual wireless network configuration within a template. Key attributes: name, ID, enabled/disabled state, authentication type (802.1X, open, PSK), VLAN assignment, Mist Edge tunnel reference, site variable references.
- **Site**: A physical location managed by Mist. Key attributes: name, ID, assigned template, site group memberships, site settings (including site variables).
- **Site Variable**: A key-value pair stored in a site's settings (`vars` dictionary) that templates can reference for site-specific values. Key attributes: variable name, value, owning site.
- **Site Group**: A logical grouping of sites, identified by a name and ID. Templates can be assigned to a site group so all member sites inherit the template. Key attributes: name, ID, member site list.
- **Mist Edge Cluster**: A tunneling infrastructure endpoint that sites connect through. There are currently 4 clusters across the ~170 sites. Key attributes: cluster name, cluster ID, associated sites.
- **Consolidation Matrix**: The Phase 1 output artifact — a tabular dataset (CSV + SQLite) with one row per site containing all collected configuration details, anomaly flags, and PSK flags.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The number of active WLAN templates managing production SSIDs is reduced from ~170 to exactly 5, as verified by the Phase 1 audit report run after full completion.
- **SC-002**: 100% of non-PSK sites have the correct site variables configured, as verified by a post-Phase-2 validation report comparing expected vs. actual site variable values.
- **SC-003**: 100% of non-PSK sites are assigned to exactly one of the 5 target site groups, as verified by a post-Phase-3 validation report.
- **SC-004**: All 5 new consolidated templates are created with active SSIDs, and site variable references resolve correctly for every assigned site — meaning each site receives the correct site-specific VLAN and edge cluster values through variable substitution.
- **SC-005**: 100% of SSIDs in old per-site templates are set to disabled (not deleted) for non-PSK sites, as verified by a post-Phase-5 audit report.
- **SC-006**: Zero PSK sites are modified by any phase of the operation, as verified by the per-phase skip logs.
- **SC-007**: A junior NOC engineer with no prior exposure to this tool can complete the full 5-phase workflow in under 60 minutes using only the on-screen guidance, without requiring escalation or external documentation.
- **SC-008**: Every modification phase produces a confirmation summary that the engineer reviews before typing CONFIRM, and every confirmation is logged with a timestamp. Zero unconfirmed changes are made.
- **SC-009**: If any phase is interrupted mid-execution, the engineer can re-run that phase and it resumes or re-applies idempotently without creating duplicate resources or skipping sites.
- **SC-010**: The Phase 1 matrix report is accurate for 100% of sites, as verified by spot-checking 10 randomly selected sites against the Mist dashboard.

---

## Assumptions

- The Mist organization has a single org ID, already configured via `MIST_ORG_ID` or `ORG_ID` in `.env`.
- The existing `mistapi` library (≥0.59.0) provides all necessary API endpoints for templates, WLANs, sites, site groups, site settings, and Mist Edge operations. The `mistapi.api.v1.orgs.sitegroups` module is expected to exist for site group CRUD operations even though it is not currently called in MistHelper.py.
- Each of the ~170 sites currently has exactly one template assigned, and each template contains exactly 2 SSIDs (one secured, one open/guest). Deviations from this pattern are treated as anomalies and flagged rather than causing failures.
- The 4 Mist Edge clusters already exist and are correctly configured. This feature does not create or modify Mist Edge clusters.
- The 5 target site groups and 5 new templates do not yet exist at the time of first execution. If they do, the system handles conflicts gracefully.
- The `.env` file follows the existing project pattern of key=value pairs loaded by `python-dotenv`.
- The `data/` directory is writable (validated by the existing `FilePermissionValidator` at startup).
- API rate limits are manageable with the existing retry/backoff configuration (`API_REQUEST_MAX_RETRIES`, `API_REQUEST_RETRY_DELAY`).

---

## Clarifications

### Session 2026-04-02

- Q: When creating consolidated templates, how should the system resolve parameter deviations (differing SSID settings across sites within the same consolidation group)? → A: No default, pick each — show all unique values per parameter with site counts; engineer must explicitly select one for each. No pre-selected default.
- Q: How should consolidated templates be assigned to sites — via sitegroup_ids, direct site_ids, or both? → A: sitegroup_ids only. Each new template targets its site group; site membership controls assignment. No direct site_id binding.
- Q: Which WLAN properties should the deviation analysis compare when fingerprinting SSIDs across sites within a consolidation group? → A: All properties. Compare every field in the WLAN JSON object except metadata fields: `id`, `org_id`, `site_id`, `template_id`, `created_time`, `modified_time`. Full-object comparison ensures no setting divergence is missed.
- Q: When the SSID selector identifies a target SSID, does the system operate on all SSIDs in each template or only the selected one? → A: Selector picks exactly one SSID. Only that SSID is collected, variablized, and consolidated; the other SSID in the template is ignored. The engineer runs the workflow separately for each SSID (e.g., once for secured, once for open/guest).
- Q: Should the 4 production templates share an identical SSID base configuration, or can each cluster's template have independent settings? → A: Identical base. All 4 production templates share the same SSID settings; differences are only in site-variable-resolved values. Cross-cluster deviations are flagged as drift.
