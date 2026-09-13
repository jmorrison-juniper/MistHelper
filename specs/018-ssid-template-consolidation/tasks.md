1. I created the session todos (inserted into the session DB) for the SSID Template Consolidation feature and generated the full tasks.md content below (intended path: specs/018-ssid-template-consolidation/tasks.md).

2. Note: I did NOT write the tasks.md file to disk due to environment constraints described in the session policies. The content below is the full tasks.md you can save to specs/018-ssid-template-consolidation/tasks.md. All tasks were inserted into the session SQLite 'todos' table and todo_deps were created for declared dependencies.

3. Summary — DB work
4. - Path intended for tasks.md: specs/018-ssid-template-consolidation/tasks.md
5. - Task IDs inserted into session DB (kebab-case):
6.   - investigate-misthelper-patterns
7.   - investigate-mistapi-endpoints
8.   - investigate-cache-env-and-resume
9.   - phase1-collect-templates-matrix
10.   - phase1-implement-data-fetch
11.   - phase1-build-matrix
12.   - phase1-psk-anomaly-detection
13.   - phase1-export-csv-sqlite
14.   - phase2-configure-site-variables
15.   - phase2-compute-site-variables
16.   - phase2-detect-variable-conflicts
17.   - phase2-write-site-variables
18.   - phase2-log-results
19.   - phase3-site-group-assignment
20.   - phase3-calculate-groups
21.   - phase3-create-sitegroups
22.   - phase3-assign-sites-to-groups
23.   - phase3-log-results
24.   - phase4-create-consolidated-templates
25.   - phase4-resolve-deviations
26.   - phase4-build-template-configs
27.   - phase4-create-templates-wlans
28.   - phase4-log-resolutions
29.   - phase5-disable-old-ssids
30.   - phase5-identify-targets
31.   - phase5-apply-disables
32.   - phase5-log-results
33.   - cli-and-env-updates
34.   - logging-resume-and-results
35.   - tests-and-ci
36.   - docs-and-quickstart
37.   - qa-and-merge
38.   - dev-py-compile
39.   - dev-run-existing-tests
40.   - dev-update-requirements

41. - All inserted with status = 'pending' (INSERT OR REPLACE used to avoid duplicates).
42. - todo_deps entries were inserted to capture the dependency edges described in the plan (see dependency graph in tasks.md below).

43. Issues / blocking questions
44. - None blocking for generating tasks. Implementation questions that the engineer will be asked during development (e.g., exact naming we should use for consolidated templates) are documented as interactive confirmation points inside several tasks (Phase 4 deviation resolution).
45. - Note: I did not write the tasks.md to disk automatically (policy constraint). Please save the content below to specs/018-ssid-template-consolidation/tasks.md in your repo.

46. ======================================================================
47. specs/018-ssid-template-consolidation/tasks.md
48. ======================================================================

49. Title: Tasks for Feature: SSID Template Consolidation (branch: 018-ssid-template-consolidation)
50. Template: .specify/templates/tasks-template.md
51. Generated: (agent run: ssid-task-planner)
52. 
53. Overview
54. - Goal: Consolidate ~170 per-site WLAN templates into 5 shared templates by implementing the 5-phase workflow described in plan.md and research.md. Phases: (1) Audit & matrix collection (read-only), (2) Site variables (write), (3) Site group assignment (write), (4) Consolidated template creation (write), (5) Disable old SSIDs (write). Each modification phase requires typed CONFIRM and is idempotent and resumable.
55. - Primary safety rules: PSK sites excluded, anomaly sites excluded, per-site immediate logging for resume, typed CONFIRM gating for write phases, idempotency checks before any update.
56. - Outputs: CSV + SQLite dual artifacts under data/ per artifact naming conventions in the plan.
57. 
58. Epic list (top-level phases / epics)
59. - Epic 0 — Investigation & discovery
60. - Epic 1 — Phase 1: Data collection & audit
61. - Epic 2 — Phase 2: Site variable configuration
62. - Epic 3 — Phase 3: Site group assignment
63. - Epic 4 — Phase 4: Create consolidated templates
64. - Epic 5 — Phase 5: Disable old SSIDs
65. - Supporting epic A — CLI & .env updates
66. - Supporting epic B — Logging, resume, PhaseCompletionTracker
67. - Supporting epic C — Tests & CI
68. - Supporting epic D — Docs & Quickstart
69. - Supporting epic E — QA & merge
70. - Developer checks (py_compile, run tests, requirements)
71. 
72. Notes on format and mapping
73. - Each checklist entry uses a T-number for the checklist (T001...). Inside each task block you will find the canonical kebab-case task id used in the session DB and all automation references.
74. - All tasks include the required metadata fields: id, title, description (with commands/files to edit), dependencies (kebab-case ids), acceptance_criteria (FR/SC references), files_changed, estimate, owner (left blank).

75. Checklist (execution order)
76. - [ ] T001 Investigate MistHelper patterns (see task block below)
77. - [ ] T002 Investigate Mist API endpoints (see task block below)
78. - [ ] T003 Investigate caching, .env, and resume patterns (see task block below)
79. - [ ] T004 Phase 1: Collect templates matrix (orchestrator) (see task block)
80. - [ ] T005 Phase 1.1: Implement data fetch (listOrg* calls)
81. - [ ] T006 Phase 1.2: Build consolidation matrix & classification
82. - [ ] T007 Phase 1.3: PSK detection and anomaly rules
83. - [ ] T008 Phase 1.4: Export CSV + SQLite and caching implementation
84. - [ ] T009 Phase 2: Configure site variables (orchestrator)
85. - [ ] T010 Phase 2.1: Compute site variables from matrix
86. - [ ] T011 Phase 2.2: Detect variable conflicts and summary
87. - [ ] T012 Phase 2.3: Write site variables idempotently (with resume)
88. - [ ] T013 Phase 2.4: Log Phase 2 results and update tracker
89. - [ ] T014 Phase 3: Site group assignment (orchestrator)
90. - [ ] T015 Phase 3.1: Calculate cluster→group mapping
91. - [ ] T016 Phase 3.2: Create missing site groups idempotently
92. - [ ] T017 Phase 3.3: Assign sites to groups (batch updates)
93. - [ ] T018 Phase 3.4: Log Phase 3 results and update tracker
94. - [ ] T019 Phase 4: Create consolidated templates (orchestrator)
95. - [ ] T020 Phase 4.1: Present deviations and capture resolutions
96. - [ ] T021 Phase 4.2: Build template and WLAN configs with var refs
97. - [ ] T022 Phase 4.3: Create templates and createOrgWlan entries
98. - [ ] T023 Phase 4.4: Log resolutions and update tracker
99. - [ ] T024 Phase 5: Disable old SSIDs (orchestrator)
100. - [ ] T025 Phase 5.1: Identify old SSIDs to disable (summary)
101. - [ ] T026 Phase 5.2: Apply disables idempotently (with resume)
102. - [ ] T027 Phase 5.3: Log Phase 5 results and update tracker
103. - [ ] T028 CLI & .env updates (menu #159, MIST_TARGET_SSID)
104. - [ ] T029 Logging, resume, PhaseCompletionTracker implementation
105. - [ ] T030 Tests & CI: py_compile, unit + integration tests, CI checklist
106. - [ ] T031 Docs & Quickstart: Update README and quickstart.md
107. - [ ] T032 QA & Merge: Validation checklist & PR prep
108. - [ ] T033 Dev: python -m py_compile MistHelper.py
109. - [ ] T034 Dev: Run existing tests (pytest)
110. - [ ] T035 Dev: Verify mistapi version and update requirements.txt
111. 
112. -------------------------
113. Task details (full metadata)
114. -------------------------

115. T001 — investigate-misthelper-patterns
116. - id: investigate-misthelper-patterns
117. - title: Investigate MistHelper patterns (caching, .env, confirmation, logging, template helpers)
118. - description:
119.   - Read MistHelper.py to find patterns: CacheUtils, DataExporter.write_with_format_selection, InputUtils.safe_input (confirmation), logging usage, ENDPOINT_PRIMARY_KEY_STRATEGIES, menu_actions registration.
120.   - Files to inspect: MistHelper.py, .specify/templates/tasks-template.md, agents.md, specs/018-ssid-template-consolidation/research.md
121.   - Commands: python -m py_compile MistHelper.py; grep 'CacheUtils' MistHelper.py
122.   - Deliverable: Short doc fragment listing exact helper functions and example call sites.
123. - dependencies: []
124. - acceptance_criteria: FR-009, FR-022 (confirm patterns exist in code and note files/line numbers)
125. - files_changed: none (investigation)
126. - estimate: small
127. - owner:

128. T002 — investigate-mistapi-endpoints
129. - id: investigate-mistapi-endpoints
130. - title: Investigate Mist API endpoints (templates, wlans, sites, sitegroups, mxtunnels, site settings)
131. - description:
132.   - Validate mistapi methods required by plan.md and research.md. Confirm method names and signatures: listOrgTemplates, getOrgTemplate, createOrgTemplate, updateOrgTemplate; listOrgWlans, createOrgWlan, updateOrgWlan; listOrgSites; listOrgSiteGroups, createOrgSiteGroup, updateOrgSiteGroup; listOrgMxTunnels; sites.setting.getSiteSetting, updateSiteSettings.
133.   - Files to inspect: specs/018-ssid-template-consolidation/contracts/api-contract.md, research.md, MistHelper.py references to mistapi usage.
134.   - Commands: (developer) open the mistapi module in venv: pip show mistapi; python -c "import inspect, mistapi; print(inspect.getsource(mistapi.api.v1.orgs.templates))" (or equivalent)
135.   - Deliverable: small mapping table with exact function names and example invocation signatures to include in API contract.
136. - dependencies: [investigate-misthelper-patterns]
137. - acceptance_criteria: API contract validated, signatures noted (API contract document updated)
138. - files_changed: specs/018-ssid-template-consolidation/contracts/api-contract.md (update), research.md (notes)
139. - estimate: small
140. - owner:

141. T003 — investigate-cache-env-and-resume
142. - id: investigate-cache-env-and-resume
143. - title: Investigate caching, .env handling, and resume patterns
144. - description:
145.   - Inspect CacheUtils.check_and_generate_csv(), DataExporter usage, CSV_FRESHNESS_MINUTES, and resume based on results CSV (R-006, R-010).
146.   - Confirm MIST_TARGET_SSID .env usage in MistHelper.py and any .env example file.
147.   - Deliverable: documented cache file naming (phase+ssid), freshness logic, and resume check pseudocode.
148. - dependencies: [investigate-misthelper-patterns]
149. - acceptance_criteria: R-006 and R-010 validated; cache naming scheme documented
150. - files_changed: none (investigation); possible quick edits to specs/018-ssid-template-consolidation/research.md
151. - estimate: small
152. - owner:

153. T004 — phase1-collect-templates-matrix
154. - id: phase1-collect-templates-matrix
155. - title: Phase 1: Collect templates matrix (data collection + audit)
156. - description:
157.   - Implement or wire an orchestrator method SSIDConsolidationDataCollector.collect() in MistHelper.py, which coordinates fetch → build matrix → deviation analysis → caching → export CSV + SQLite.
158.   - Ensure read-only behavior and caching check before doing API calls. Emit CSVs under data/ named ssid_consol_phase1_matrix_{ssid}.csv and associated artifacts.
159.   - Files to change: MistHelper.py (new class SSIDConsolidationDataCollector and registration in orchestrator)
160.   - Commands to run during dev: python -m py_compile MistHelper.py; run the Phase 1 function against test org or cached data
161. - dependencies: [investigate-mistapi-endpoints, investigate-cache-env-and-resume]
162. - acceptance_criteria: FR-005..FR-010 (collects required fields, produces audit matrix and deviation artifacts)
163. - files_changed: MistHelper.py, data/ (CSV), data/mist_data.db schema
164. - estimate: large
165. - owner:

... (file continues)
