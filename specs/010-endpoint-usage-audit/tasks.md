# Tasks: Mist API Endpoint Usage Audit

**Input**: Design documents from `/specs/010-endpoint-usage-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/audit-report-schema.json, quickstart.md

**Tests**: Not requested — this is a manual code review audit. Verification is built into each audit phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each audit dimension.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Audit targets**: MistHelper.py, maps_manager.py, wsgi.py (repository root)
- **Reference docs**: documentation/api/ (1,013 enriched endpoint files across 8 categories)
- **Audit outputs**: specs/010-endpoint-usage-audit/ (audit-report.json, audit-summary.md)

---

## Phase 1: Setup

**Purpose**: Establish the audit workspace and build the endpoint documentation index

- [X] T001 Build endpoint documentation index by parsing `## mistapi SDK` sections from all 1,013 files in documentation/api/ — target: ~107 unique functions to match against
- [X] T002 Verify output directory structure exists in specs/010-endpoint-usage-audit/ for audit-report.json and audit-summary.md

---

## Phase 2: Foundational (API Call Site Catalog)

**Purpose**: Catalog every `mistapi.api.v1.*` call site across all source files and match to documentation. Maps to FR-001.

**CRITICAL**: No user story audit work can begin until this catalog is complete.

- [X] T003 Scan MistHelper.py for all `mistapi.api.v1.*` invocations, recording function name, parameters passed, and line number (~278 call sites, ~102 unique functions)
- [X] T004 [P] Scan maps_manager.py for all `mistapi.api.v1.*` invocations, recording function name, parameters passed, and line number (~91 call sites, ~24 unique functions)
- [X] T005 [P] Scan wsgi.py for all `mistapi.api.v1.*` invocations, recording function name, parameters passed, and line number (1 call site)
- [X] T006 Match each cataloged call site to its enriched API doc file via the `## mistapi SDK` section index built in T001
- [X] T007 Map each call site to the menu operation(s) that invoke it by tracing through the menu_actions dict (~line 50593 in MistHelper.py, 123 entries spanning keys 0-122)

**Checkpoint**: Complete EndpointCatalogEntry working data for every call site. All audit dimensions can now proceed.

---

## Phase 3: User Story 1 — Endpoint Selection Audit (Priority: P1) MVP

**Goal**: Verify each menu operation uses the most appropriate Mist API endpoint for its stated purpose (FR-002). Cross-reference each call's intent against the endpoint's `## Usage Context` section.

**Independent Test**: Produce findings where an operation's stated goal (from README/menu label) does not match the endpoint's documented purpose. Each mismatch is a finding with severity Critical (wrong endpoint) or Low (suboptimal choice).

### Implementation for User Story 1

- [X] T008 [P] [US1] Audit endpoint selection for all orgs-scope API calls in MistHelper.py against documentation/api/orgs/ docs
- [X] T009 [P] [US1] Audit endpoint selection for all sites-scope API calls in MistHelper.py against documentation/api/sites/ docs
- [X] T010 [P] [US1] Audit endpoint selection for utilities, constants, self, admins, installer, and msps API calls in MistHelper.py against their respective documentation/api/ subdirectories
- [X] T011 [US1] Audit endpoint selection for WebSocket initiation calls (menus 5-8, 87-89) in MistHelper.py — verify REST setup endpoint matches the command's purpose per research.md R3
- [X] T012 [US1] Audit endpoint selection for all API calls in maps_manager.py against documentation/api/ docs, noting any scope mismatches vs MistHelper.py usage of the same endpoints
- [X] T013 [US1] Compile all endpoint selection findings as AuditFinding objects with category `endpoint-selection` in specs/010-endpoint-usage-audit/

**Checkpoint**: All endpoint selection findings documented. US1 independently verifiable by checking each finding's current endpoint vs recommended endpoint.

---

## Phase 4: User Story 2 — Parameter and Usage Correctness Audit (Priority: P2)

**Goal**: Verify each API call passes correct parameters, uses proper filters, handles pagination, and follows the endpoint's documented contract (FR-003, FR-004, FR-005, FR-010). Dual-tier classification: Incorrect (wrong/incomplete results) vs Suboptimal (works but not best practice).

**Independent Test**: For each call site, extract parameters passed and compare against the endpoint's documented parameter list. Each missing required parameter, misused optional parameter, or pagination gap is a finding.

### Implementation for User Story 2

- [X] T014 [US2] Audit parameter correctness for all org-level list and search API calls in MistHelper.py — check required params present, optional params appropriate, against documentation/api/orgs/ parameter tables
- [X] T015 [P] [US2] Audit parameter correctness for all site-level list and search API calls in MistHelper.py — check required params present, optional params appropriate, against documentation/api/sites/ parameter tables
- [X] T016 [P] [US2] Audit parameter correctness for all single-entity get, update, create, and delete API calls in MistHelper.py — verify entity IDs and body parameters match documented contracts
- [X] T017 [US2] Audit pagination handling for all list/search endpoints — verify `mistapi.get_all()` usage per research.md R2 criteria (FR-005)
- [X] T018 [US2] Audit multi-call operation chains — verify parameter consistency across sequential API calls within the same menu operation (FR-010)
- [X] T019 [US2] Compile all parameter and usage findings as AuditFinding objects with categories `parameter-usage` and `pagination` in specs/010-endpoint-usage-audit/

**Checkpoint**: All parameter/usage findings documented with dual-tier (Incorrect/Suboptimal) classification. US2 independently verifiable.

---

## Phase 5: User Story 3 — Deprecation and Best Practice Check (Priority: P3)

**Goal**: Identify deprecated endpoints/parameters and best-practice violations by reviewing `## Gotchas` and `## Related Endpoints` sections of all used endpoint docs (FR-006, FR-007).

**Independent Test**: Cross-reference every Gotchas section of used endpoints against actual usage. Flag per-site iteration patterns where org-level bulk alternatives exist.

### Implementation for User Story 3

- [X] T020 [US3] Review `## Gotchas` sections of all enriched API docs for endpoints used in MistHelper.py — flag any usage that violates documented warnings (FR-006)
- [X] T021 [P] [US3] Identify per-site iteration patterns in MistHelper.py where an equivalent org-level bulk endpoint exists, using `## Related Endpoints` sections (FR-007)
- [X] T022 [P] [US3] Check pre-seeded known pitfalls from research.md R5 — verify `listOrgDevices` type filter and any other patterns not yet confirmed
- [X] T023 [US3] Compile all deprecation and best-practice findings as AuditFinding objects with categories `deprecation` and `best-practice` in specs/010-endpoint-usage-audit/

**Checkpoint**: All deprecation/best-practice findings documented. US3 independently verifiable.

---

## Phase 6: User Story 4 — Audit Report Compilation (Priority: P4)

**Goal**: Compile all findings from US1-US3 into the structured dual-format report: JSON (machine-parseable) + Markdown summary (human-readable) (FR-008, FR-009, FR-011).

**Independent Test**: Validate audit-report.json against contracts/audit-report-schema.json. Verify audit-summary.md contains correct aggregate statistics matching the JSON data.

### Implementation for User Story 4

- [X] T024 [US4] Merge all findings from US1 (T013), US2 (T019), and US3 (T023) — assign sequential IDs (F-001, F-002, ...) sorted by severity then category
- [X] T025 [US4] Generate specs/010-endpoint-usage-audit/audit-report.json per contracts/audit-report-schema.json with complete metadata, scope, summary statistics, and all findings
- [X] T026 [US4] Generate specs/010-endpoint-usage-audit/audit-summary.md with severity breakdown, tier breakdown, category breakdown, top findings, and coverage percentage
- [X] T027 [US4] Validate audit-report.json against contracts/audit-report-schema.json — verify all required fields, finding ID format (F-NNN), enum values, and coverage_percentage equals 100.0

**Checkpoint**: Both deliverables complete and validated. Audit report is actionable without additional context (SC-002).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all audit dimensions

- [X] T028 Cross-validate a sample of findings — confirm line numbers and code references in audit-report.json match current MistHelper.py source
- [X] T029 Verify audit coverage — confirm total_call_sites and unique_api_functions in the report scope match the catalog from Phase 2
- [X] T030 Run quickstart.md validation — verify the audit followed all 5 steps and deliverables match the documented workflow

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (needs doc index from T001) — BLOCKS all user stories
- **US1 Endpoint Selection (Phase 3)**: Depends on Foundational (needs complete call site catalog)
- **US2 Parameter Correctness (Phase 4)**: Depends on Foundational (needs complete call site catalog)
- **US3 Deprecation/Best Practice (Phase 5)**: Depends on Foundational (needs complete call site catalog)
- **US4 Report Compilation (Phase 6)**: Depends on US1 + US2 + US3 (needs all findings)
- **Polish (Phase 7)**: Depends on US4 (needs completed report)

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P2)**: Can start after Phase 2 — no dependencies on other stories
- **US3 (P3)**: Can start after Phase 2 — no dependencies on other stories
- **US4 (P4)**: Depends on US1 + US2 + US3 completion (compilation step)

### Within Each User Story

- Audit tasks within a story proceed by API domain (orgs, sites, other)
- Tasks marked [P] within a story can run in parallel (different file scopes)
- Each story ends with a findings compilation task that consolidates results

### Parallel Opportunities

**After Phase 2 completes, US1-US3 can all proceed in parallel:**

```
Phase 2 complete
    ├── US1: Endpoint Selection (T008-T013) ──┐
    ├── US2: Parameter Correctness (T014-T019) ├── US4: Report (T024-T027)
    └── US3: Deprecation/Best Practice (T020-T023) ┘
```

**Within US1** (parallel by API scope):
- T008 (orgs) and T009 (sites) and T010 (other) can run in parallel
- T011 (WebSocket) and T012 (maps_manager) can run in parallel
- T013 (compile) depends on T008-T012

**Within US2** (parallel by call type):
- T014 (org-level list/search) and T015 (site-level list/search) and T016 (single-entity) can run in parallel
- T017 (pagination) and T018 (multi-call chains) can run in parallel
- T019 (compile) depends on T014-T018

**Within US3** (parallel by check type):
- T020 (gotchas) and T021 (bulk alternatives) and T022 (known pitfalls) can run in parallel
- T023 (compile) depends on T020-T022

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (build doc index)
2. Complete Phase 2: Foundational (catalog all call sites)
3. Complete Phase 3: US1 — Endpoint Selection Audit
4. **STOP and VALIDATE**: Review endpoint selection findings independently
5. Proceed to US2 if findings are actionable

### Incremental Delivery

1. Setup + Foundational → Call site catalog ready
2. US1 → Endpoint selection findings → Review (MVP — catches the most severe bugs)
3. US2 → Parameter/usage findings → Review (catches data quality issues)
4. US3 → Deprecation/best-practice findings → Review (catches future-proofing issues)
5. US4 → Compile final report → Validate against schema
6. Each story adds a new audit dimension without invalidating previous findings

### Single Agent Strategy

For a single AI agent executing sequentially:

1. Complete Setup + Foundational (T001-T007)
2. Execute US1 (T008-T013) — endpoint selection is highest impact
3. Execute US2 (T014-T019) — parameter correctness is next highest
4. Execute US3 (T020-T023) — deprecation/best practice is lowest urgency
5. Execute US4 (T024-T027) — compile everything
6. Execute Polish (T028-T030) — final validation

---

## Notes

- This is a manual code review by an AI agent, not an automated script
- No runtime code is produced — output is JSON + Markdown files only
- All findings must include specific line numbers referenced against current source
- The `## mistapi SDK` section in enriched docs is the deterministic matching key (research.md R1)
- WebSocket operations audit only the REST initiation call, not WebSocket streaming (research.md R3)
- Pagination audit uses the criteria from research.md R2 (get_all usage, limit parameter)
- Known pitfalls from research.md R5 are pre-seeded but audit should discover new ones
- Report format must conform to contracts/audit-report-schema.json
