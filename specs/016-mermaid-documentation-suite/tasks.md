# Tasks: Mermaid Documentation Suite

**Input**: Design documents from `/specs/016-mermaid-documentation-suite/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included only for the CI lint script (FR-016) which is a Python utility requiring pytest coverage. Diagram files are static documentation validated by rendering on GitHub and the lint script itself.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. User stories are ordered by priority (P1 first, then P2, then P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All diagram files live under `documentation/diagrams/` organized into 4 subdirectories: `core/` (architecture, data pipeline, database), `class-hierarchy/` (class family diagrams), `operations/` (menu system, metrics, workflow), and `infrastructure/` (deployment, container, network). PNG fallbacks live alongside their source markdown. The lint script lives under `scripts/`. Tests under `tests/unit/`. Two inline diagrams are inserted into the root `README.md`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and placeholder files for the diagram suite

- [x] T001 Create directory structure: `documentation/diagrams/core/`, `documentation/diagrams/class-hierarchy/`, `documentation/diagrams/operations/`, `documentation/diagrams/infrastructure/`, and ensure `scripts/` and `tests/unit/` directories exist

---

## Phase 2: Foundational (Theme + Navigation Framework)

**Purpose**: Establish the navigation index and README integration point that ALL user stories depend on

**CRITICAL**: No diagram file can be properly linked until the navigation index exists

- [x] T002 Create navigation index skeleton at documentation/diagrams/README.md per navigation-contract.md (section headings, "Back to repository" link, placeholder sections for each diagram category)
- [x] T003 Add "Visual Documentation" section to README.md with a link to documentation/diagrams/README.md and placeholder anchors for the 2 inline diagrams (architecture + mindmap)

**Checkpoint**: Navigation framework ready - diagram authoring can begin

---

## Phase 3: User Story 1 - Understand Project Architecture at a Glance (Priority: P1) MVP

**Goal**: A developer sees a high-level architecture diagram in the README showing all major subsystems (menu, API, exporters, database, container, web portal, SSH) with T-Mobile dark-mode colors

**Independent Test**: Open README.md on GitHub, verify the inline architecture diagram renders with all subsystems labeled, T-Mobile magenta theme applied, and cross-reference links to detailed docs work

### Implementation for User Story 1

- [x] T004 [US1] Create documentation/diagrams/core/architecture-overview.md with C4Context diagram showing users, external APIs (Mist Cloud), and MistHelper subsystems, applying theme-contract.md init directive
- [x] T005 [US1] Add architecture-beta diagram to documentation/diagrams/core/architecture-overview.md showing internal component relationships (menu system, API layer, data exporters, SQLite, container runtime, web portal, SSH server)
- [x] T006 [US1] Generate PNG fallback for architecture-beta diagram and save to documentation/diagrams/core/architecture-overview.png using mmdc CLI
- [x] T007 [US1] Insert inline architecture-beta diagram in README.md after the project description, using the standard theme init directive, with a "See detailed architecture diagrams" link to documentation/diagrams/core/architecture-overview.md

**Checkpoint**: User Story 1 complete - README shows architecture overview, detailed file has C4 + architecture-beta

---

## Phase 4: User Story 2 - Trace the Data Pipeline from Menu to Output (Priority: P1)

**Goal**: A developer can follow a request from menu selection through API call, pagination, rate limiting, data flattening, to dual-format export (CSV/SQLite) via sequence and flowchart diagrams

**Independent Test**: Open documentation/diagrams/core/data-pipeline.md on GitHub, verify the sequence diagram shows the full happy-path trace with actual class/method names (APIFetchUtils, DataExporter, etc.), and the error-handling flowchart shows decision nodes for retries and rate limiting

### Implementation for User Story 2

- [x] T008 [P] [US2] Create documentation/diagrams/core/data-pipeline.md with a sequenceDiagram tracing the happy-path flow: User -> OperationRegistry -> APIFetchUtils.fetch_with_pagination() -> RateLimitingUtils -> DataProcessingUtils -> DataExporter.write_with_format_selection(), applying theme-contract.md init directive
- [x] T009 [US2] Add error-handling flowchart to documentation/diagrams/core/data-pipeline.md showing decision nodes for rate limiting (429 response), retry logic, API error responses, and output format selection (CSV vs SQLite)

**Checkpoint**: User Story 2 complete - data pipeline fully traced in sequence + flowchart diagrams

---

## Phase 5: User Story 3 - Navigate the Class Hierarchy (Priority: P2)

**Goal**: A developer can see how all 99+ classes are organized into logical families with inheritance/composition relationships, split across linked sub-diagrams that each stay under the 50-node rendering limit

**Independent Test**: Open documentation/diagrams/class-hierarchy/overview.md, verify all 12 class families appear with links to sub-diagrams; open any sub-diagram and verify class names match actual names in MistHelper.py

### Implementation for User Story 3

- [x] T010 [P] [US3] Create documentation/diagrams/class-hierarchy/overview.md with a top-level classDiagram showing 12 class family nodes (Infrastructure, Configuration, Utilities, API Fetching, Data Processing, Org Exporters, Site Exporters, Gateway Exporters, WebSocket, Managers, UI/TUI, System/Registry) with family-to-family dependency arrows and links to sub-diagram files
- [x] T011 [P] [US3] Create documentation/diagrams/class-hierarchy/infrastructure.md with classDiagram covering Infrastructure (DataDirectoryChecker, PerformanceMonitor), Configuration Objects (SSHConnectionConfig, SSHExecutionConfig, AddressValidationConfig, MapViewerConfig, DeviceFetchConfig, EndpointConfig), and API Fetching (APICoreFetchUtils -> APITenantFetchUtils -> APIFetchUtils, DeviceDataFetcher) showing inheritance chain
- [x] T012 [P] [US3] Create documentation/diagrams/class-hierarchy/exporters.md with classDiagram covering Org-Level Exporters (10 classes), Site-Level Exporters (5 classes), Gateway Exporters (4 classes), and shared export utilities (DataExporter, SFPTransceiverDataProcessor, ConstDefinitionsExporter) showing relationships to DataExporter base
- [x] T013 [P] [US3] Create documentation/diagrams/class-hierarchy/managers.md with classDiagram covering Managers (PacketCaptureManager, FirmwareManager, BulkAPFirmwareUpgrader, BulkSwitchFirmwareUpgrader, EnhancedSSHRunner, SSHRunnerManager, CLIShellManager, WebSocketManager, MapsManager, VirtualChassisManager, WAN2MigrationManager, and others) showing composition and delegation relationships
- [x] T014 [P] [US3] Create documentation/diagrams/class-hierarchy/utilities.md with classDiagram covering all 23+ Utility classes (TimeUtils, InputUtils, CacheUtils, DisplayUtils, FilePathUtils, ValidationUtils, etc.) and Data Processing classes (DataProcessingUtils, MarvisDataUtils, DatabaseSchemaUtils, SQLiteDatabaseWriter) showing groupings by responsibility
- [x] T015 [US3] Add cross-reference links to all class-hierarchy/ files: each file gets a "Back to overview" link to overview.md, sibling links to other family files, and a "Back to index" link to documentation/diagrams/README.md per navigation-contract.md

**Checkpoint**: User Story 3 complete - all 99+ classes documented across 5 linked sub-diagrams

---

## Phase 6: User Story 4 - Understand the Menu System Organization (Priority: P2)

**Goal**: A developer can visualize all 159 operations organized by category (safe, interactive, destructive, WebSocket, WIP, etc.) with color-coding by safety classification

**Independent Test**: Count operations shown in the mindmap and verify the count matches 159 from OperationRegistry; verify safety colors match the theme-contract classDef definitions

### Implementation for User Story 4

- [x] T016 [P] [US4] Create documentation/diagrams/operations/operations-reference.md with: (1) stateDiagram-v2 showing operation lifecycle (idle -> running -> rate-limited -> retrying -> completed/failed), (2) user journey diagram for a NOC engineer menu navigation experience, and (3) requirementDiagram for destructive operation safety requirements, applying theme-contract.md init directive
- [x] T017 [US4] Insert inline mindmap in README.md showing the full menu taxonomy: 8 categories (Safe 18 ops, Interactive Safe 15, Interactive 21, WebSocket 18, Destructive 50, Resource Intensive 3, WIP 3, Continuous 2) with safety-classification classDef coloring per theme-contract.md

**Checkpoint**: User Story 4 complete - README shows color-coded menu mindmap, operations-reference has lifecycle + journey + requirements

---

## Phase 7: User Story 5 - Understand the Deployment and CI/CD Pipeline (Priority: P3)

**Goal**: A developer can see the full lifecycle from code change through CI quality gates (Ruff, mypy, pytest, Bandit, pip-audit, CodeQL, Playwright) to container build, registry push, and deployment

**Independent Test**: Compare deployment-pipeline.md diagrams against actual .github/workflows/ files and verify each CI step and quality gate is represented

### Implementation for User Story 5

- [x] T018 [US5] Create documentation/diagrams/infrastructure/deployment-pipeline.md with: (1) flowchart showing commit -> CI matrix (7 parallel quality gates) -> container build -> GHCR push -> deployment, (2) gantt chart showing CI pipeline timing and stage durations, and (3) gitgraph showing branching strategy (main, feature branches, auto-merge flow), applying theme-contract.md init directive

**Checkpoint**: User Story 5 complete - full CI/CD pipeline visualized with 3 diagram types

---

## Phase 8: User Story 6 - Explore the Database Strategy (Priority: P3)

**Goal**: A developer can see the hybrid PK system (natural, composite, auto-increment) via an ER diagram and follow a decision flowchart to choose the right strategy for new operations

**Independent Test**: Select 3 entries from ENDPOINT_PRIMARY_KEY_STRATEGIES and verify the ER diagram accurately represents their PK type, columns, and indexes

### Implementation for User Story 6

- [x] T019 [US6] Create documentation/diagrams/core/database-strategy.md with: (1) erDiagram showing representative tables (sites, device_events, licenses_summary) with PK strategy annotations and index relationships, and (2) flowchart decision tree guiding PK type selection (has stable UUID? -> natural_pk; time-series? -> composite_pk; aggregated? -> auto_increment_with_unique), applying theme-contract.md init directive

**Checkpoint**: User Story 6 complete - database PK strategy visually documented with ER + decision flowchart

---

## Phase 9: User Story 7 - Understand the Container and SSH Architecture (Priority: P3)

**Goal**: A developer can see container internals (non-root user, ForceCommand SSH, session isolation, port mappings 2200/8055, data volume) in architecture and block diagrams

**Independent Test**: Compare diagrams against Containerfile/Dockerfile and SSH configuration and verify ports, users, and paths match

### Implementation for User Story 7

- [x] T020 [US7] Create documentation/diagrams/infrastructure/container-architecture.md with: (1) block-beta diagram showing container layers (base image -> Python deps -> app code -> non-root user -> SSH server -> web server), session isolation directories, and volume mounts, and (2) architecture-beta diagram showing external access paths (SSH on 2200, HTTP on 8055) through to internal components, applying theme-contract.md init directive
- [x] T021 [US7] Generate PNG fallback for container block-beta diagram and save to documentation/diagrams/infrastructure/container-architecture.png using mmdc CLI

**Checkpoint**: User Story 7 complete - container security model and SSH architecture diagrammed

---

## Phase 10: Supplementary Diagrams (Remaining Diagram Types)

**Purpose**: Complete the 20-diagram-type coverage with analytics, protocol, and workflow diagrams that span multiple user stories

- [x] T022 [P] Create documentation/diagrams/operations/metrics-and-analytics.md with: (1) pie chart showing operation category distribution (Safe 18, Interactive Safe 15, Interactive 21, WebSocket 18, Destructive 50, etc.) and (2) quadrantChart showing operation complexity-vs-frequency matrix, applying theme-contract.md init directive and type-specific overrides
- [x] T022b [P] Add to documentation/diagrams/operations/metrics-and-analytics.md: (1) xychart-beta showing rate limiting adaptive delay curve, (2) sankey-beta showing data flow volume (API calls -> processing stages -> output formats), and (3) timeline showing MistHelper version history milestones, applying theme-contract.md type-specific overrides
- [x] T023 [P] Create documentation/diagrams/infrastructure/network-protocols.md with packet-beta diagram showing network packet structure relevant to the packet capture feature (Menu 9-10), applying theme-contract.md init directive
- [x] T024 [P] Create documentation/diagrams/operations/development-workflow.md with kanban diagram showing the speckit feature lifecycle (Spec -> Plan -> Tasks -> Implement -> CI -> Merge -> Deploy), applying theme-contract.md init directive
- [x] T025 Generate PNG fallbacks for remaining beta diagrams: documentation/diagrams/infrastructure/network-protocols.png (packet-beta), documentation/diagrams/operations/data-flow-sankey.png (sankey-beta), and documentation/diagrams/operations/metrics-xychart.png (xychart-beta) using mmdc CLI

**Checkpoint**: All 20 Mermaid diagram types used across the documentation suite

---

## Phase 11: CI Lint Script (FR-016)

**Purpose**: Create the Python lint script that validates diagram references against the codebase, plus its tests and CI integration

- [x] T026 Create scripts/lint_diagram_refs.py with DiagramReferenceValidator class implementing: (1) Mermaid code block extraction from markdown files, (2) identifier extraction via regex patterns per lint-script-contract.md, (3) Python symbol extraction via ast.parse() of MistHelper.py, (4) reference validation with fuzzy closest-match suggestions, (5) built-in allowlist of 25 Mermaid/domain terms, (6) CLI interface with --docs-dir, --extra-files, --source-files, --allowlist, --verbose arguments (--extra-files defaults to README.md to catch inline diagrams), (7) exit codes 0/1/2 per contract
- [x] T027 Create tests/unit/test_lint_diagram_refs.py with pytest tests covering: (1) Mermaid code block extraction from sample markdown, (2) identifier extraction for each supported pattern (classDiagram, sequenceDiagram, flowchart, PascalCase), (3) Python symbol extraction via ast, (4) allowlist filtering, (5) stale reference detection and closest-match output, (6) exit code behavior
- [x] T028 Add diagram reference lint job to .github/workflows/ci.yml as a matrix entry: `python scripts/lint_diagram_refs.py` alongside existing Ruff, mypy, pytest, Bandit, pip-audit checks

**Checkpoint**: CI lint script operational - stale diagram references will fail the build

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Finalize navigation, cross-references, and validate the complete suite

- [x] T029 Finalize documentation/diagrams/README.md: populate all sections with diagram file links, brief descriptions, diagram type badges (e.g., `[flowchart]`, `[sequenceDiagram]`), and category groupings per navigation-contract.md
- [x] T030 Add "Related Diagrams" footer section to every diagram file (excluding class-hierarchy/ files which already have sibling links from T015) per navigation-contract.md: each file links to 2-3 semantically related diagram files in other subdirectories
- [x] T031 Run scripts/lint_diagram_refs.py against all diagram files and fix any stale references or mismatched identifiers
- [x] T032 Validate all diagrams render correctly on GitHub.com in both dark and light mode (manual push to branch and visual verification)
- [x] T033 Run quickstart.md validation steps: verify file locations table matches actual files, lint script runs without errors, color reference matches theme-contract.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories (navigation index must exist)
- **User Stories (Phases 3-9)**: All depend on Foundational phase completion
  - P1 stories (US1, US2) can proceed in parallel
  - P2 stories (US3, US4) can proceed in parallel after Foundational, independent of P1
  - P3 stories (US5, US6, US7) can proceed in parallel after Foundational, independent of P1/P2
- **Supplementary (Phase 10)**: Depends on Foundational only - can run parallel with any user story
- **CI Lint Script (Phase 11)**: Depends on at least one diagram file existing (can start after Phase 3)
- **Polish (Phase 12)**: Depends on ALL previous phases - final integration step

### User Story Dependencies

- **US1 (P1)**: Foundational only - no cross-story dependencies
- **US2 (P1)**: Foundational only - references architecture concepts but authored independently
- **US3 (P2)**: Foundational only - class diagrams are self-contained
- **US4 (P2)**: Foundational only - menu mindmap and operations reference are self-contained
- **US5 (P3)**: Foundational only - CI/CD pipeline documented independently
- **US6 (P3)**: Foundational only - database strategy documented independently
- **US7 (P3)**: Foundational only - container architecture documented independently

### Within Each User Story

- Theme init directive (from theme-contract.md) applied to every diagram
- Navigation links added after diagram content is authored
- PNG fallbacks generated after beta diagram content is finalized
- Cross-references finalized in Phase 12 (Polish)

### Parallel Opportunities

- **Phase 2**: T002 and T003 can run in parallel (different files)
- **Phase 3-4**: US1 (T004-T007) and US2 (T008-T009) can run in parallel
- **Phase 5**: T010-T014 (class hierarchy sub-diagrams) can ALL run in parallel
- **Phase 5-6**: US3 and US4 can run in parallel
- **Phase 7-9**: US5, US6, and US7 can ALL run in parallel
- **Phase 10**: T022, T022b, T023, T024 can ALL run in parallel
- **Phase 11**: T026 and T027 can run in parallel (script + tests in different files)

---

## Parallel Example: User Story 3 (Class Hierarchy)

```bash
# Launch all class hierarchy sub-diagrams together (different files, no dependencies):
Task T010: "Create class-hierarchy/overview.md"
Task T011: "Create class-hierarchy/infrastructure.md"
Task T012: "Create class-hierarchy/exporters.md"
Task T013: "Create class-hierarchy/managers.md"
Task T014: "Create class-hierarchy/utilities.md"

# Then sequentially:
Task T015: "Add cross-reference links across all files" (depends on T010-T014)
```

## Parallel Example: All P3 Stories

```bash
# After Foundational (Phase 2) is complete, launch all P3 stories together:
Task T018: "Create infrastructure/deployment-pipeline.md" (US5)
Task T019: "Create core/database-strategy.md" (US6)
Task T020: "Create infrastructure/container-architecture.md" (US7)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (1 task)
2. Complete Phase 2: Foundational (2 tasks)
3. Complete Phase 3: User Story 1 - Architecture Overview (4 tasks)
4. Complete Phase 4: User Story 2 - Data Pipeline (2 tasks)
5. **STOP and VALIDATE**: Push to branch, verify on GitHub
6. README has inline architecture diagram, docs have pipeline trace
7. **Total MVP: 9 tasks**

### Incremental Delivery

1. Setup + Foundational -> Framework ready
2. Add US1 + US2 -> Architecture + Data Pipeline (MVP - 2 diagram types: architecture-beta, C4, sequence, flowchart)
3. Add US3 + US4 -> Class Hierarchy + Menu System (adds classDiagram, mindmap, stateDiagram, journey, requirementDiagram)
4. Add US5 + US6 + US7 -> Deployment + Database + Container (adds gantt, gitgraph, erDiagram, block-beta)
5. Add Supplementary -> Remaining types (adds pie, xychart, sankey, quadrant, timeline, packet, kanban)
6. Add Lint Script -> CI protection against stale references
7. Polish -> Final navigation, cross-references, validation
8. **Each increment adds value without breaking previous diagrams**

### Parallel Agent Strategy

With multiple agents working simultaneously:

1. All agents: Complete Setup + Foundational together (Phase 1-2)
2. Once Foundational is done:
   - Agent A: US1 (architecture) + US2 (data pipeline) [P1 priority]
   - Agent B: US3 (class hierarchy - 5 parallel sub-diagrams) [P2 priority]
   - Agent C: US4 (menu system) + Supplementary diagrams [P2 priority]
3. After P1/P2 complete:
   - Agent A: US5 + US6 + US7 (all P3, parallel) [P3 priority]
   - Agent B: Lint script + tests (Phase 11)
4. Final: Any agent: Polish (Phase 12)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to the specific user story from spec.md
- Every Mermaid code block MUST begin with the theme-contract.md init directive
- Every diagram file MUST have "Back to index" link per navigation-contract.md
- Keep all diagrams under 50 nodes per research.md R3
- Beta diagram types (architecture-beta, block-beta, packet-beta, sankey-beta, xychart-beta) MUST have PNG fallbacks
- Commit after each phase or logical group
- Stop at any checkpoint to validate on GitHub
