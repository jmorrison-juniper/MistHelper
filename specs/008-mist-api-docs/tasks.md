# Tasks: Mist API Endpoint Reference Documentation

**Input**: Design documents from `/specs/008-mist-api-docs/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: No automated tests requested. Validation is manual spot-checking per quickstart.md.

**Organization**: Tasks grouped by user story. US1 (endpoint lookup) is the MVP.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files/methods, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create the script file and output directory structure

- [X] T001 Create `scripts/generate_api_docs.py` with imports (json, pathlib, re, logging, argparse), logging configuration (ASCII-only), argument parser for spec file path, and `if __name__ == '__main__'` entry point with class stubs for SpecParser, SchemaResolver, MarkdownRenderer, IndexGenerator
- [X] T002 Add directory creation logic to `scripts/generate_api_docs.py` that creates `documentation/api/` and 8 category subdirectories (orgs, sites, msps, utilities, constants, installer, self, admins) using pathlib.Path.mkdir(parents=True, exist_ok=True)

---

## Phase 2: Foundational (Parsing & Schema Resolution)

**Purpose**: Core infrastructure that ALL user stories depend on — spec parsing and schema dereferencing

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Implement `SpecParser` class in `scripts/generate_api_docs.py` — load JSON from `documentation/mist-api-openapi31json.json`, extract operations list (method, path, operationId, tags, summary, description, parameters, requestBody, responses, deprecated), extract tag list with descriptions, extract components.schemas dict
- [X] T004 Implement `SchemaResolver` class in `scripts/generate_api_docs.py` — accept components.schemas dict, resolve `$ref` strings to inline definitions iteratively with a visited-set (per R5), handle allOf/oneOf/anyOf composition by merging properties, return fully dereferenced schema dicts with type/properties/items/required/enum/format/description preserved

**Checkpoint**: Parser and resolver ready — user story implementation can begin

---

## Phase 3: User Story 1 — AI Agent Looks Up Endpoint Details (Priority: P1) MVP

**Goal**: Generate one self-contained markdown file per API operation (~1,013 files) with all HTTP details, parameters, schemas, and mistapi function path so an AI agent can write correct code from a single file read.

**Independent Test**: Select 5 random endpoints, verify each markdown file contains all mandatory sections (HTTP method/path, parameters table, request body, response schema, mistapi function), and confirm values match the OpenAPI spec.

### Implementation for User Story 1

- [X] T005 [US1] Implement `MarkdownRenderer.__init__()` accepting a SchemaResolver instance, and `render_operation()` orchestrator method in `scripts/generate_api_docs.py` — assemble title, HTTP line, description, authentication, parameters, request body, responses, errors, pagination, rate limiting, and mistapi sections per the R7 template; if `deprecated` is true, render a `> **DEPRECATED**` warning banner immediately after the title
- [X] T006 [P] [US1] Implement `MarkdownRenderer.render_parameters()` in `scripts/generate_api_docs.py` — render separate tables for path, query, and header parameters with columns: Name, Type, Required, Default, Enum, Description (per FR-009); output "None" if no parameters exist
- [X] T007 [P] [US1] Implement `MarkdownRenderer.render_request_body()` in `scripts/generate_api_docs.py` — extract request body schema from operation, resolve all $refs via SchemaResolver, render as indented JSON with inline descriptions and required markers; output "None" for GET/DELETE operations
- [X] T008 [P] [US1] Implement `MarkdownRenderer.render_responses()` in `scripts/generate_api_docs.py` — iterate response status codes, resolve each response schema via SchemaResolver, render as subsections with status code headers containing content type and full JSON schema (per FR-010); include an Errors table for 4xx/5xx codes
- [X] T009 [US1] Implement `MarkdownRenderer.derive_mistapi_path()` in `scripts/generate_api_docs.py` — map tag name to scope/resource (e.g., "Orgs Sites" → orgs.sites, "Orgs NAC Tags" → orgs.nac_tags), combine with operationId to produce `mistapi.api.v1.{scope}.{resource}.{operationId}()` (per R4)
- [X] T010 [US1] Implement main generation loop in `scripts/generate_api_docs.py` — iterate all operations from SpecParser, determine category directory from first tag word (per R2), compute filename as `{METHOD}_{path_slug}.md` (per R3), render via MarkdownRenderer, write to `documentation/api/{category}/{filename}`, log progress with operation count per category
- [X] T011 [US1] Run `python scripts/generate_api_docs.py` and validate output — confirm ~1,013 .md files created in `documentation/api/`, spot-check 5 endpoints (GET list, POST create, PUT update, DELETE, PATCH) against `documentation/mist-api-openapi31json.json` for correct parameters, schemas, and mistapi path

**Checkpoint**: All ~1,013 endpoint files generated and validated. US1 independently functional.

---

## Phase 4: User Story 2 — AI Agent Discovers Available Endpoints (Priority: P2)

**Goal**: Generate a master INDEX.md that lists every endpoint grouped by OpenAPI tag with relative links, so an AI agent can discover all available endpoints for any domain in one file read.

**Independent Test**: Open INDEX.md, verify all 1,013 operations are listed across 206 tag groups, and confirm each relative link resolves to an existing endpoint file.

### Implementation for User Story 2

- [X] T012 [US2] Implement `IndexGenerator` class in `scripts/generate_api_docs.py` — accept operations list, group by tag name, render markdown with tag headers (## level) and tables per tag with columns: Method, Path, operationId, Summary, and a relative link to the endpoint file (e.g., `[GET_orgs_org_id_sites.md](orgs/GET_orgs_org_id_sites.md)`)
- [X] T013 [US2] Integrate `IndexGenerator.generate()` call into the main generation flow in `scripts/generate_api_docs.py` — invoke after all endpoint files are written, write output to `documentation/api/INDEX.md`, log total operation count and tag count
- [X] T014 [US2] Validate `documentation/api/INDEX.md` — confirm it contains all 1,013 operations across 206 tags, verify 5 random relative links resolve to existing files in the correct category subdirectory

**Checkpoint**: INDEX.md generated with full coverage. US2 independently functional.

---

## Phase 5: User Story 3 — Raw Source Files Available Locally (Priority: P3)

**Goal**: Ensure all raw source files exist in the documentation folder for offline regeneration without web access.

**Independent Test**: Verify `documentation/mist-api-openapi31json.json` and `documentation/mist-api-openapi31yaml.yaml` exist and are non-empty.

### Implementation for User Story 3

- [X] T015 [US3] Verify raw source files exist — confirm `documentation/mist-api-openapi31json.json` (~17MB) and `documentation/mist-api-openapi31yaml.yaml` (~11MB) are present and non-empty; document their origin URLs in a comment at the top of `scripts/generate_api_docs.py`
- [X] T016 [US3] Add a regeneration docstring to `scripts/generate_api_docs.py` module header documenting: source file locations, download URLs for spec updates, and the offline regeneration command (`python scripts/generate_api_docs.py`)

**Checkpoint**: Raw source files verified. US3 complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation for the AI enrichment workflow and end-to-end validation

- [X] T017 [P] Create `documentation/api/ENRICHMENT_GUIDE.md` documenting the Phase 2 AI enrichment workflow — batch strategy by category ascending (admins at 13 files first as pilot, then self/18, installer/23, constants/27, msps/50, utilities/103, sites/330, orgs/449 last), enrichment sections to add (usage context, gotchas, cross-references, MistHelper notes per FR-002), quality checklist for each enriched file
- [X] T018 Run quickstart.md validation steps against `documentation/api/` — count all .md files (expect ~1,014), verify INDEX.md link integrity, spot-check enrichment-ready file structure, confirm end-to-end pipeline from spec to output

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 completion
- **US2 (Phase 4)**: Depends on Phase 2 completion; can run in parallel with US1 but logically benefits from US1 files existing
- **US3 (Phase 5)**: No implementation dependencies — can run in parallel with any phase (verification only)
- **Polish (Phase 6)**: Depends on US1 and US2 completion

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2) only — no dependencies on other stories
- **US2 (P2)**: Depends on Foundational (Phase 2) — uses same SpecParser output as US1; benefits from US1 files for link verification but can generate INDEX.md independently
- **US3 (P3)**: Independent — verifies pre-existing files, no code dependencies

### Within User Story 1

- T005 (renderer skeleton) before T006, T007, T008 (render methods)
- T006, T007, T008 can run in parallel (different methods, no shared state)
- T009 (mistapi mapping) can run in parallel with T006-T008
- T010 (main loop) depends on T005-T009 completion
- T011 (validation) depends on T010 completion

### Parallel Opportunities

```text
Phase 1: T001 → T002

Phase 2: T003 → T004

Phase 3 (US1):
  T005 (skeleton)
    ├── T006 [P] (parameters)
    ├── T007 [P] (request body)
    ├── T008 [P] (responses)
    └── T009 (mistapi path)
  T010 (main loop) ← waits for T005-T009
  T011 (validation) ← waits for T010

Phase 4 (US2): T012 → T013 → T014

Phase 5 (US3): T015 [P], T016 [P] — can run alongside any phase

Phase 6: T017 [P], T018
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — script file with stubs and directory structure
2. Complete Phase 2: Foundational — SpecParser and SchemaResolver working
3. Complete Phase 3: User Story 1 — all ~1,013 endpoint files generated
4. **STOP and VALIDATE**: Spot-check 5 endpoints, verify file count matches expected ~1,013
5. This delivers the core value: any AI agent can look up any Mist API endpoint

### Incremental Delivery

1. Setup + Foundational → Script infrastructure ready
2. User Story 1 → ~1,013 endpoint files generated → **MVP complete**
3. User Story 2 → INDEX.md for discovery → Enhanced navigation
4. User Story 3 → Source files verified → Offline guarantee
5. Polish → Enrichment guide + validation → Ready for AI enrichment passes

### AI Enrichment (Post-Script, Manual)

After all script-generated tasks are complete, the AI enrichment phase begins:
1. Start with smallest category: `admins/` (13 files) as a pilot batch
2. Then `self/` (18), `installer/` (23), `constants/` (27), `msps/` (50)
3. Then `utilities/` (103), `sites/` (330), `orgs/` (449)
4. Each batch: AI reads raw file → rewrites with enriched content → validates sections

---

## Notes

- All 18 tasks target a single file: `scripts/generate_api_docs.py` (plus output files)
- No external dependencies — stdlib only (json, pathlib, re, logging, argparse)
- No automated tests — validation is manual spot-checking per quickstart.md
- The script is idempotent — re-running overwrites all output files
- AI enrichment is a separate manual process documented in ENRICHMENT_GUIDE.md
