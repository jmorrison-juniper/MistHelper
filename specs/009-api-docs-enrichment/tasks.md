# Tasks: Mist API Documentation Enrichment

**Input**: Design documents from `/specs/009-api-docs-enrichment/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: No test tasks generated — tests not explicitly requested in the feature specification. Validation is performed via grep and link-checking scripts defined in quickstart.md.

**Organization**: Tasks are grouped by user story. US1 (actionable endpoint guidance) and US2 (MistHelper menu mapping) are tightly coupled — both are satisfied simultaneously during each file's enrichment. US3 (complete coverage) is satisfied as all category batches complete. Phases are organized by category batch in ascending size order per FR-005.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (no content dependencies — may operate on different sections of the same files)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Prepare reference data and validate the enrichment workflow prerequisites

- [x] T001 Verify all 1,013 endpoint files exist with 4 placeholder sections by running `Select-String -Path "documentation\api\**\*.md" -Pattern "To be enriched by AI agent" -Recurse | Measure-Object` and confirming Count = 4052
- [x] T002 Scan MistHelper.py to build the full MistHelper-to-API mapping for all 127 used operations (per R5 inventory in research.md), noting menu operation numbers and special parameter handling
- [x] T003 Read documentation/api/ENRICHMENT_GUIDE.md to confirm quality checklist and section templates for enrichment content

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the cross-reference index needed for Related Endpoints sections before any enrichment begins

**CRITICAL**: The full relationship graph (CRUD siblings, parent, sub-resources, cross-scope) requires knowing all 1,013 filenames across all 8 categories. This index MUST be built before enrichment starts.

- [x] T004 Build cross-reference index by listing all files in each of the 8 category directories under documentation/api/ to enable correct relative linking between categories
- [x] T005 Identify resource groups by parsing endpoint filenames (HTTP method + URL path) to map CRUD siblings, parent/child resources, and cross-scope equivalents (org-level ↔ site-level)

**Checkpoint**: Cross-reference index and MistHelper mapping ready — enrichment can begin

---

## Phase 3: Batch 1 — admins/ (13 files) — Pilot

**Goal**: Enrich all 13 admins/ endpoint files as the pilot batch, validating the enrichment workflow and content quality before scaling to larger categories

**Independent Test**: Run `Select-String -Path "documentation\api\admins\*.md" -Pattern "To be enriched by AI agent" | Measure-Object` — expect Count = 0. Spot-check 3 files against ENRICHMENT_GUIDE.md quality checklist.

- [x] T006 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for all 13 files in documentation/api/admins/
- [x] T007 [P] [US2] Enrich MistHelper Notes for all 13 files in documentation/api/admins/ (admins scope has 0 direct MistHelper operations — all get "Not currently used by MistHelper")
- [x] T008 [US3] Validate admins/ batch: zero remaining placeholders, all cross-reference links resolve to existing files, spot-check 3 files against quality checklist
- [x] T009 [US3] Git commit admins/ batch: `git add documentation/api/admins/ && git commit -m "enrich: admins/ (13 files) - pilot batch"`

**Checkpoint**: Pilot batch complete — review quality before proceeding

---

## Phase 4: Batch 2 — self/ (18 files)

**Goal**: Enrich all 18 self/ endpoint files. This category includes `getSelfApiUsage` which IS used by MistHelper.

**Independent Test**: Run `Select-String -Path "documentation\api\self\*.md" -Pattern "To be enriched by AI agent" | Measure-Object` — expect Count = 0.

- [x] T010 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for all 18 files in documentation/api/self/
- [x] T011 [P] [US2] Enrich MistHelper Notes for all 18 files in documentation/api/self/ (1 used operation: getSelfApiUsage)
- [x] T012 [US3] Validate self/ batch: zero remaining placeholders, all links resolve, spot-check quality
- [x] T013 [US3] Git commit self/ batch: `git add documentation/api/self/ && git commit -m "enrich: self/ (18 files)"`

---

## Phase 5: Batch 3 — installer/ (23 files)

**Goal**: Enrich all 23 installer/ endpoint files

**Independent Test**: Run `Select-String -Path "documentation\api\installer\*.md" -Pattern "To be enriched by AI agent" | Measure-Object` — expect Count = 0.

- [x] T014 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for all 23 files in documentation/api/installer/
- [x] T015 [P] [US2] Enrich MistHelper Notes for all 23 files in documentation/api/installer/ (0 direct MistHelper operations)
- [x] T016 [US3] Validate installer/ batch: zero remaining placeholders, all links resolve, spot-check quality
- [x] T017 [US3] Git commit installer/ batch: `git add documentation/api/installer/ && git commit -m "enrich: installer/ (23 files)"`

---

## Phase 6: Batch 4 — constants/ (27 files)

**Goal**: Enrich all 27 constants/ endpoint files

**Independent Test**: Run `Select-String -Path "documentation\api\constants\*.md" -Pattern "To be enriched by AI agent" | Measure-Object` — expect Count = 0.

- [x] T018 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for all 27 files in documentation/api/constants/
- [x] T019 [P] [US2] Enrich MistHelper Notes for all 27 files in documentation/api/constants/ (0 direct MistHelper operations)
- [x] T020 [US3] Validate constants/ batch: zero remaining placeholders, all links resolve, spot-check quality
- [x] T021 [US3] Git commit constants/ batch: `git add documentation/api/constants/ && git commit -m "enrich: constants/ (27 files)"`

---

## Phase 7: Batch 5 — msps/ (50 files)

**Goal**: Enrich all 50 msps/ endpoint files (first medium-sized batch, single commit)

**Independent Test**: Run `Select-String -Path "documentation\api\msps\*.md" -Pattern "To be enriched by AI agent" | Measure-Object` — expect Count = 0.

- [x] T022 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for all 50 files in documentation/api/msps/
- [x] T023 [P] [US2] Enrich MistHelper Notes for all 50 files in documentation/api/msps/ (0 direct MistHelper operations)
- [x] T024 [US3] Validate msps/ batch: zero remaining placeholders, all links resolve, spot-check quality
- [x] T025 [US3] Git commit msps/ batch: `git add documentation/api/msps/ && git commit -m "enrich: msps/ (50 files)"`

---

## Phase 8: Batch 6 — utilities/ (103 files)

**Goal**: Enrich all 103 utilities/ endpoint files (~2 commits at ~50 files each)

**Independent Test**: Run `Select-String -Path "documentation\api\utilities\*.md" -Pattern "To be enriched by AI agent" | Measure-Object` — expect Count = 0.

### Sub-batch 6a (files 1–50)

- [x] T026 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 1–50 in documentation/api/utilities/
- [x] T027 [P] [US2] Enrich MistHelper Notes for files 1–50 in documentation/api/utilities/
- [x] T028 [US3] Validate utilities/ sub-batch 6a: zero remaining placeholders in files 1–50
- [x] T029 [US3] Git commit utilities/ sub-batch 6a: `git add documentation/api/utilities/ && git commit -m "enrich: utilities/ (files 1-50 of 103)"`

### Sub-batch 6b (files 51–103)

- [x] T030 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 51–103 in documentation/api/utilities/
- [x] T031 [P] [US2] Enrich MistHelper Notes for files 51–103 in documentation/api/utilities/
- [x] T032 [US3] Validate utilities/ full batch: zero remaining placeholders, all links resolve, spot-check quality
- [x] T033 [US3] Git commit utilities/ sub-batch 6b: `git add documentation/api/utilities/ && git commit -m "enrich: utilities/ (files 51-103 of 103)"`

---

## Phase 9: Batch 7 — sites/ (330 files)

**Goal**: Enrich all 330 sites/ endpoint files (~7 commits at ~50 files each). This category has ~58 MistHelper-used operations.

**Independent Test**: Run `Select-String -Path "documentation\api\sites\*.md" -Pattern "To be enriched by AI agent" | Measure-Object` — expect Count = 0.

### Sub-batch 7a (files 1–50)

- [x] T034 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 1–50 in documentation/api/sites/
- [x] T035 [P] [US2] Enrich MistHelper Notes for files 1–50 in documentation/api/sites/
- [x] T036 [US3] Validate sites/ sub-batch 7a: zero remaining placeholders in files 1–50
- [x] T037 [US3] Git commit sites/ sub-batch 7a: `git add documentation/api/sites/ && git commit -m "enrich: sites/ (files 1-50 of 330)"`

### Sub-batch 7b (files 51–100)

- [x] T038 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 51–100 in documentation/api/sites/
- [x] T039 [P] [US2] Enrich MistHelper Notes for files 51–100 in documentation/api/sites/
- [x] T040 [US3] Validate sites/ sub-batch 7b: zero remaining placeholders in files 51–100
- [x] T041 [US3] Git commit sites/ sub-batch 7b: `git add documentation/api/sites/ && git commit -m "enrich: sites/ (files 51-100 of 330)"`

### Sub-batch 7c (files 101–150)

- [x] T042 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 101–150 in documentation/api/sites/
- [x] T043 [P] [US2] Enrich MistHelper Notes for files 101–150 in documentation/api/sites/
- [x] T044 [US3] Validate sites/ sub-batch 7c: zero remaining placeholders in files 101–150
- [x] T045 [US3] Git commit sites/ sub-batch 7c: `git add documentation/api/sites/ && git commit -m "enrich: sites/ (files 101-150 of 330)"`

### Sub-batch 7d (files 151–200)

- [x] T046 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 151–200 in documentation/api/sites/
- [x] T047 [P] [US2] Enrich MistHelper Notes for files 151–200 in documentation/api/sites/
- [x] T048 [US3] Validate sites/ sub-batch 7d: zero remaining placeholders in files 151–200
- [x] T049 [US3] Git commit sites/ sub-batch 7d: `git add documentation/api/sites/ && git commit -m "enrich: sites/ (files 151-200 of 330)"`

### Sub-batch 7e (files 201–250)

- [x] T050 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 201–250 in documentation/api/sites/
- [x] T051 [P] [US2] Enrich MistHelper Notes for files 201–250 in documentation/api/sites/
- [x] T052 [US3] Validate sites/ sub-batch 7e: zero remaining placeholders in files 201–250
- [x] T053 [US3] Git commit sites/ sub-batch 7e: `git add documentation/api/sites/ && git commit -m "enrich: sites/ (files 201-250 of 330)"`

### Sub-batch 7f (files 251–300)

- [x] T054 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 251–300 in documentation/api/sites/
- [x] T055 [P] [US2] Enrich MistHelper Notes for files 251–300 in documentation/api/sites/
- [x] T056 [US3] Validate sites/ sub-batch 7f: zero remaining placeholders in files 251–300
- [x] T057 [US3] Git commit sites/ sub-batch 7f: `git add documentation/api/sites/ && git commit -m "enrich: sites/ (files 251-300 of 330)"`

### Sub-batch 7g (files 301–330)

- [x] T058 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 301–330 in documentation/api/sites/
- [x] T059 [P] [US2] Enrich MistHelper Notes for files 301–330 in documentation/api/sites/
- [x] T060 [US3] Validate sites/ full batch: zero remaining placeholders, all links resolve, spot-check quality
- [x] T061 [US3] Git commit sites/ sub-batch 7g: `git add documentation/api/sites/ && git commit -m "enrich: sites/ (files 301-330 of 330)"`

---

## Phase 10: Batch 8 — orgs/ (449 files)

**Goal**: Enrich all 449 orgs/ endpoint files (~9 commits at ~50 files each). This category has ~67 MistHelper-used operations — the most of any category.

**Independent Test**: Run `Select-String -Path "documentation\api\orgs\*.md" -Pattern "To be enriched by AI agent" | Measure-Object` — expect Count = 0.

### Sub-batch 8a (files 1–50)

- [x] T062 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 1–50 in documentation/api/orgs/
- [x] T063 [P] [US2] Enrich MistHelper Notes for files 1–50 in documentation/api/orgs/
- [x] T064 [US3] Validate orgs/ sub-batch 8a: zero remaining placeholders in files 1–50
- [x] T065 [US3] Git commit orgs/ sub-batch 8a: `git add documentation/api/orgs/ && git commit -m "enrich: orgs/ (files 1-50 of 449)"`

### Sub-batch 8b (files 51–100)

- [x] T066 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 51–100 in documentation/api/orgs/
- [x] T067 [P] [US2] Enrich MistHelper Notes for files 51–100 in documentation/api/orgs/
- [x] T068 [US3] Validate orgs/ sub-batch 8b: zero remaining placeholders in files 51–100
- [x] T069 [US3] Git commit orgs/ sub-batch 8b: `git add documentation/api/orgs/ && git commit -m "enrich: orgs/ (files 51-100 of 449)"`

### Sub-batch 8c (files 101–150)

- [x] T070 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 101–150 in documentation/api/orgs/
- [x] T071 [P] [US2] Enrich MistHelper Notes for files 101–150 in documentation/api/orgs/
- [x] T072 [US3] Validate orgs/ sub-batch 8c: zero remaining placeholders in files 101–150
- [x] T073 [US3] Git commit orgs/ sub-batch 8c: `git add documentation/api/orgs/ && git commit -m "enrich: orgs/ (files 101-150 of 449)"`

### Sub-batch 8d (files 151–200)

- [x] T074 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 151–200 in documentation/api/orgs/
- [x] T075 [P] [US2] Enrich MistHelper Notes for files 151–200 in documentation/api/orgs/
- [x] T076 [US3] Validate orgs/ sub-batch 8d: zero remaining placeholders in files 151–200
- [x] T077 [US3] Git commit orgs/ sub-batch 8d: `git add documentation/api/orgs/ && git commit -m "enrich: orgs/ (files 151-200 of 449)"`

### Sub-batch 8e (files 201–250)

- [x] T078 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 201–250 in documentation/api/orgs/
- [x] T079 [P] [US2] Enrich MistHelper Notes for files 201–250 in documentation/api/orgs/
- [x] T080 [US3] Validate orgs/ sub-batch 8e: zero remaining placeholders in files 201–250
- [x] T081 [US3] Git commit orgs/ sub-batch 8e: `git add documentation/api/orgs/ && git commit -m "enrich: orgs/ (files 201-250 of 449)"`

### Sub-batch 8f (files 251–300)

- [x] T082 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 251–300 in documentation/api/orgs/
- [x] T083 [P] [US2] Enrich MistHelper Notes for files 251–300 in documentation/api/orgs/
- [x] T084 [US3] Validate orgs/ sub-batch 8f: zero remaining placeholders in files 251–300
- [x] T085 [US3] Git commit orgs/ sub-batch 8f: `git add documentation/api/orgs/ && git commit -m "enrich: orgs/ (files 251-300 of 449)"`

### Sub-batch 8g (files 301–350)

- [x] T086 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 301–350 in documentation/api/orgs/
- [x] T087 [P] [US2] Enrich MistHelper Notes for files 301–350 in documentation/api/orgs/
- [x] T088 [US3] Validate orgs/ sub-batch 8g: zero remaining placeholders in files 301–350
- [x] T089 [US3] Git commit orgs/ sub-batch 8g: `git add documentation/api/orgs/ && git commit -m "enrich: orgs/ (files 301-350 of 449)"`

### Sub-batch 8h (files 351–400)

- [x] T090 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 351–400 in documentation/api/orgs/
- [x] T091 [P] [US2] Enrich MistHelper Notes for files 351–400 in documentation/api/orgs/
- [x] T092 [US3] Validate orgs/ sub-batch 8h: zero remaining placeholders in files 351–400
- [x] T093 [US3] Git commit orgs/ sub-batch 8h: `git add documentation/api/orgs/ && git commit -m "enrich: orgs/ (files 351-400 of 449)"`

### Sub-batch 8i (files 401–449)

- [x] T094 [P] [US1] Enrich Usage Context, Gotchas, and Related Endpoints for files 401–449 in documentation/api/orgs/
- [x] T095 [P] [US2] Enrich MistHelper Notes for files 401–449 in documentation/api/orgs/
- [x] T096 [US3] Validate orgs/ full batch: zero remaining placeholders, all links resolve, spot-check quality
- [x] T097 [US3] Git commit orgs/ sub-batch 8i: `git add documentation/api/orgs/ && git commit -m "enrich: orgs/ (files 401-449 of 449)"`

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all 1,013 files and cross-category link integrity

- [x] T098 Run full placeholder validation: `Select-String -Path "documentation\api\**\*.md" -Pattern "To be enriched by AI agent" -Recurse | Measure-Object` — expect Count = 0
- [x] T099 Run full link validation script from quickstart.md across all 1,013 files — expect 0 broken links
- [x] T100 Spot-check 5 files per category (40 total) against ENRICHMENT_GUIDE.md 7-item quality checklist
- [x] T101 Verify MistHelper Notes accuracy: cross-reference 10 MistHelper-used endpoints against MistHelper.py to confirm correct menu operation numbers
- [x] T102 [US1] Verify factual accuracy (FR-007): cross-reference a sample of enriched endpoint HTTP methods, paths, and parameters against the OpenAPI spec JSON to confirm no hallucinated details
- [x] T103 Git commit any fixes from validation: `git add documentation/api/ && git commit -m "enrich: final validation fixes"`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T002 (MistHelper mapping) from Setup
- **Batch 1 admins/ (Phase 3)**: Depends on Phase 2 — serves as pilot validation
- **Batches 2–8 (Phases 4–10)**: Depend on Phase 2 (cross-reference index). Can proceed sequentially without waiting for pilot review, but pilot review is recommended before scaling.
- **Polish (Phase 11)**: Depends on all batches (Phases 3–10) being complete

### User Story Dependencies

- **US1** (actionable guidance): Requires cross-reference index (T004–T005) for Related Endpoints section; web research for Gotchas and Usage Context
- **US2** (MistHelper mapping): Requires MistHelper scan (T002); independent of US1 content
- **US3** (complete coverage): Meta-story — satisfied when all batches complete with zero remaining placeholders

### Within Each Batch

1. US1 enrichment (Usage Context, Gotchas, Related Endpoints) and US2 enrichment (MistHelper Notes) can run in parallel — they write to different sections
2. Validation (T0xx) runs after both US1 and US2 enrichment complete
3. Git commit runs after validation passes

### Parallel Opportunities

- Within any batch: US1 tasks [P] and US2 tasks [P] can execute simultaneously (different sections of the same files)
- Across batches: Batches 2–8 could theoretically run in parallel after Phase 2, but sequential processing is recommended to apply lessons learned from earlier batches
- Sub-batches within a large category (sites/, orgs/): Strictly sequential to maintain ~50-file commit boundaries

---

## Parallel Example: Batch 1 (admins/)

```text
# After Phase 2 completes:

# These run in parallel (different sections of same files):
T006: Enrich Usage Context, Gotchas, Related Endpoints for admins/
T007: Enrich MistHelper Notes for admins/

# After both complete:
T008: Validate admins/ batch (zero placeholders, links resolve)
T009: Git commit admins/ batch
```

---

## Implementation Strategy

### MVP First (Batch 1 — admins/ only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T005)
3. Complete Phase 3: Batch 1 admins/ (T006–T009)
4. **STOP and VALIDATE**: Review 3 pilot files for quality, link integrity, and MistHelper Notes accuracy
5. If quality passes, proceed to remaining batches

### Incremental Delivery

1. Setup + Foundational → Cross-reference index ready
2. Batch 1 admins/ (13 files) → Pilot validation → Quality gate
3. Batch 2 self/ (18 files) → Running total: 31 files enriched
4. Batch 3 installer/ (23 files) → Running total: 54 files enriched
5. Batch 4 constants/ (27 files) → Running total: 81 files enriched
6. Batch 5 msps/ (50 files) → Running total: 131 files enriched
7. Batch 6 utilities/ (103 files) → Running total: 234 files enriched
8. Batch 7 sites/ (330 files) → Running total: 564 files enriched
9. Batch 8 orgs/ (449 files) → Running total: 1,013 files enriched
10. Polish → Final validation → Done

Each batch is a self-contained increment with its own commit(s) and validation.

---

## Notes

- [P] tasks = no content dependencies — may operate on different sections of the same files
- [Story] labels: US1 = actionable guidance (Usage Context, Gotchas, Related Endpoints), US2 = MistHelper mapping (MistHelper Notes), US3 = coverage/validation
- US1 and US2 are enriched simultaneously per batch; both must complete before validation
- File ordering within sub-batches follows alphabetical sort of filenames in the directory
- The AI agent should use `multi_replace_string_in_file` to enrich multiple sections per file efficiently
- For web research (Gotchas), use `fetch_webpage` tool to consult Mist API docs, Juniper KB, and community forums
- ~31 total git commits expected across all batches (increased from ~23 due to sub-batch validation tasks)
