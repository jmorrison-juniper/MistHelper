# Feature Specification: Mermaid Documentation Suite

**Feature Branch**: `016-mermaid-documentation-suite`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: User description: "Use the mermaid extension to its fullest potential as described in the mermaid documentation, against this project, in a way that creates comprehensive, linked, hierarchical information optimized for our GitHub repository and README. For color scheme use a Dark mode version of T-Mobile's official coloring codes. The audience is somebody that has been directed to read our code for inspiration for their own code."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand Project Architecture at a Glance (Priority: P1)

A developer directed to MistHelper for inspiration opens the GitHub repository README. Before reading any code, they see a high-level architecture diagram that shows how the major system components relate: menu system, API layer, data exporters, database, container runtime, web portal, and SSH access. Within 60 seconds they understand the shape of the system and can decide which areas are relevant to their own project.

**Why this priority**: First impressions determine whether someone continues reading. A clear architectural overview is the single highest-value diagram for code-for-inspiration readers. Every other diagram depends on the reader first understanding where the pieces fit.

**Independent Test**: Can be fully tested by opening the repository README on GitHub (light and dark mode) and verifying the architecture diagram renders correctly with T-Mobile dark-mode colors, all nodes are labeled, and clicking a node's associated link navigates to the corresponding section of documentation.

**Acceptance Scenarios**:

1. **Given** a reader opens the README on GitHub in dark mode, **When** the page loads, **Then** a C4-style or architecture diagram renders showing all major subsystems (menu, API, export, database, container, web portal, SSH) with T-Mobile magenta/dark color scheme and legible labels.
2. **Given** a reader wants to understand a specific subsystem, **When** they find the subsystem node in the architecture diagram, **Then** there is a cross-reference anchor or heading link that takes them to the detailed section or sub-diagram covering that subsystem.

---

### User Story 2 - Trace the Data Pipeline from Menu to Output (Priority: P1)

A developer studying MistHelper's data pipeline wants to understand the complete path a user request follows: menu selection through API call, pagination, rate limiting, data flattening, and dual-format export (CSV/SQLite). They find a sequence diagram or flowchart in the documentation that traces this end-to-end flow, including decision points for output format and error handling branches.

**Why this priority**: The data pipeline is MistHelper's core value proposition and the most architecturally interesting pattern for someone seeking inspiration. Understanding this flow is essential before studying any specific exporter class.

**Independent Test**: Can be fully tested by locating the data pipeline diagram in the documentation, following each labeled step, and confirming the step names match actual class/method names in the codebase.

**Acceptance Scenarios**:

1. **Given** a reader is viewing the data pipeline section, **When** they examine the sequence diagram, **Then** they can trace a request from menu selection through `APIFetchUtils.fetch_with_pagination()` to `DataExporter.write_with_format_selection()` with all intermediate steps labeled.
2. **Given** a reader wants to understand error handling in the pipeline, **When** they examine the flowchart, **Then** they can see decision nodes for rate limiting, retry logic, and API error responses.

---

### User Story 3 - Navigate the Class Hierarchy (Priority: P2)

A developer evaluating MistHelper's object-oriented design wants to see how the 99+ classes are organized into logical groups. They find a class diagram that shows major class families (infrastructure, exporters, managers, utilities) with key relationships (inheritance, composition, delegation). They can identify which classes to study for their own similar feature.

**Why this priority**: Class organization is the second most common thing developers study when reading code for inspiration. It reveals design patterns, separation of concerns, and naming conventions. But it depends on the reader first understanding the overall architecture (Story 1).

**Independent Test**: Can be fully tested by viewing the class diagram, selecting any class family (e.g., "Exporters"), and verifying the diagram accurately reflects the inheritance and composition relationships found in the codebase.

**Acceptance Scenarios**:

1. **Given** a reader views the class hierarchy diagram, **When** they look at the exporter family, **Then** they see all Org-level and Site-level exporter classes grouped under their parent relationships.
2. **Given** a reader wants to understand utility class layering, **When** they examine the API fetch utilities, **Then** they see the three-tier chain: `APICoreFetchUtils` -> `APITenantFetchUtils` -> `APIFetchUtils`.

---

### User Story 4 - Understand the Menu System Organization (Priority: P2)

A developer studying MistHelper's 159-operation menu system wants to visualize how operations are categorized across 8 safety classifications (safe, interactive safe, interactive, WebSocket, destructive, resource intensive, WIP, continuous loop) and numbered. They find a mindmap or hierarchical diagram that shows the full menu taxonomy, color-coded by safety classification.

**Why this priority**: The menu system is MistHelper's user-facing surface and demonstrates how to organize a large number of operations safely. Color-coding by safety level (safe=green, interactive=yellow, destructive=red) provides immediate visual communication of the safety-first design philosophy.

**Independent Test**: Can be fully tested by counting the operations shown in the mindmap and verifying the count and categorization match the `OperationRegistry` in the codebase.

**Acceptance Scenarios**:

1. **Given** a reader views the menu organization diagram, **When** they scan the categories, **Then** they see clear groupings across 8 categories: Safe (18 ops), Interactive Safe (15 ops), Interactive (21 ops), WebSocket (18 ops), Destructive (50 ops), Resource Intensive (3 ops), WIP (3 ops), and Continuous Loop (2 ops) with distinct visual styling per category.
2. **Given** a reader wants to find a specific operation, **When** they look at the diagram, **Then** each operation number and brief label is visible and grouped under its category.

---

### User Story 5 - Understand the Deployment and CI/CD Pipeline (Priority: P3)

A developer evaluating MistHelper's operational maturity wants to see the full lifecycle: code change through CI quality gates, container build, registry push, and deployment. They find a flowchart or Gantt-style diagram showing the complete pipeline with parallel quality gates, build triggers, and deployment modes (standalone vs. containerized).

**Why this priority**: Deployment architecture is valuable for inspiration but is less critical than understanding the core application logic. Readers interested in operational patterns will seek this out specifically.

**Independent Test**: Can be fully tested by comparing the pipeline diagram against the actual GitHub Actions workflow files and verifying each step and gate is represented.

**Acceptance Scenarios**:

1. **Given** a reader views the CI/CD pipeline diagram, **When** they trace a code commit, **Then** they see it flow through lint, type-check, test, security scan, container build, and deployment stages.
2. **Given** a reader wants to understand quality gates, **When** they examine the parallel gate section, **Then** they see Ruff, mypy, pytest, Bandit, pip-audit, CodeQL, and Playwright E2E as distinct parallel steps.

---

### User Story 6 - Explore the Database Strategy (Priority: P3)

A developer interested in MistHelper's hybrid primary key strategy wants a visual explanation of how natural PKs, composite PKs, and auto-increment strategies are applied to different data types. They find an entity-relationship diagram showing key tables with their PK strategies annotated, and a decision flowchart for choosing the right strategy when adding new operations.

**Why this priority**: The database strategy is a sophisticated design decision that many projects get wrong. Visualizing it helps readers appreciate the tradeoffs and apply similar thinking to their own work. It is lower priority because it requires understanding the data pipeline first (Story 2).

**Independent Test**: Can be fully tested by selecting any three endpoint entries from `ENDPOINT_PRIMARY_KEY_STRATEGIES` and verifying the diagram accurately represents their PK type, columns, and indexes.

**Acceptance Scenarios**:

1. **Given** a reader views the ER diagram, **When** they examine the `sites` entity, **Then** they see it annotated as `natural_pk` with `id` as the primary key and `org_id`, `name`, `country_code` as indexes.
2. **Given** a reader wants to add a new operation, **When** they follow the PK strategy decision flowchart, **Then** they arrive at the correct strategy type (natural, composite, or auto-increment) based on whether the data has stable UUIDs, is time-series, or is aggregated summary data.

---

### User Story 7 - Understand the Container and SSH Architecture (Priority: P3)

A developer studying MistHelper's container security model wants to see how the container layers, SSH access, session isolation, and port mapping work together. They find an architecture diagram showing the container internals: non-root user, ForceCommand, session directories, port mappings (2200 for SSH, 8055 for web), and the data volume mount.

**Why this priority**: Container security and SSH session isolation are sophisticated patterns worth studying, but are deployment-specific concerns that most readers will explore after understanding the core application.

**Independent Test**: Can be fully tested by comparing the architecture diagram against the Containerfile/Dockerfile and SSH configuration and verifying ports, users, and paths match.

**Acceptance Scenarios**:

1. **Given** a reader views the container architecture diagram, **When** they trace an SSH connection, **Then** they see it enter on port 2200, authenticate as `misthelper` user, launch MistHelper via ForceCommand, and write to an isolated session directory.
2. **Given** a reader views the web access path, **When** they trace an HTTP request, **Then** they see it enter on port 8055, hit the Gunicorn WSGI server, route through Flask, and access the shared `data/` volume.

---

### Edge Cases

- What happens when a Mermaid diagram exceeds GitHub's rendering size limits? Diagrams with more than approximately 50 nodes or deep nesting may fail to render. Each diagram must be tested for rendering on GitHub and split into smaller linked sub-diagrams if necessary.
- What happens when a reader views diagrams in GitHub light mode instead of dark mode? The T-Mobile dark-mode color scheme must still be legible in light mode. All text must have sufficient contrast ratio (WCAG AA minimum 4.5:1) against both dark and light backgrounds.
- What happens when GitHub updates its Mermaid rendering engine? Diagrams must use only stable Mermaid syntax (no experimental features without fallback) and be tested after any known GitHub Mermaid version bump.
- How does the documentation handle very wide diagrams on mobile GitHub? Horizontal scrolling must be available, or diagrams must use top-to-bottom layout as the default orientation.
- What happens when a class or method is renamed in the codebase? A CI lint check will detect stale references in diagram files and fail the build, surfacing them for manual update during the same PR.
- What happens when GitHub drops support for a beta Mermaid diagram type? Each beta diagram has a static PNG fallback image committed to `documentation/diagrams/fallback/`. If the Mermaid code block fails to render, the PNG is referenced via an HTML `<img>` tag as a graceful degradation path.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Documentation MUST include a top-level system architecture diagram (C4 Context or architecture-beta style) showing all major MistHelper subsystems and their relationships
- **FR-002**: Documentation MUST include a data pipeline sequence diagram tracing the complete path from menu selection through API call, pagination, rate limiting, data flattening, to dual-format export
- **FR-003**: Documentation MUST include an exhaustive class hierarchy covering all 99+ classes, split across multiple linked sub-diagrams by family (infrastructure, exporters, managers, utilities, etc.) with each sub-diagram staying under the ~50-node rendering limit. A top-level overview diagram MUST link to each family sub-diagram.
- **FR-004**: Documentation MUST include a menu system mindmap showing all operation categories (safe, interactive, destructive, WebSocket, WIP) with color-coding by safety classification
- **FR-005**: Documentation MUST include a CI/CD pipeline flowchart showing the complete deployment lifecycle from code commit through quality gates to container deployment
- **FR-006**: Documentation MUST include an entity-relationship diagram for the database strategy showing key tables with their primary key strategy annotations (natural, composite, auto-increment)
- **FR-007**: Documentation MUST include a container architecture diagram showing the layered security model (non-root user, ForceCommand SSH, session isolation, port mappings, volume mounts)
- **FR-008**: All diagrams MUST use a consistent dark-mode color theme derived from T-Mobile's brand colors (Magenta #E20074 as primary accent, deep dark backgrounds, high-contrast text)
- **FR-009**: All diagrams MUST render correctly on GitHub's built-in Mermaid renderer in both dark and light mode with legible text contrast
- **FR-010**: Each diagram MUST cross-reference related diagrams or documentation sections via markdown anchor links, creating a navigable hierarchy
- **FR-011**: Documentation MUST include a primary key strategy decision flowchart that guides developers in choosing the correct PK type when adding new operations
- **FR-012**: Diagrams MUST use stable Mermaid syntax features where available. Beta/experimental diagram types (`architecture-beta`, `packet-beta`, `sankey-beta`, `block-beta`, `xychart-beta`) MAY be used but MUST each have a static PNG fallback image committed alongside the markdown source, so documentation remains intact if GitHub drops beta support
- **FR-013**: Documentation MUST include a git workflow diagram (gitGraph) showing the branching strategy, CI triggers, and auto-merge flow
- **FR-014**: Documentation MUST include a state diagram for the operation lifecycle showing how operations transition through states (idle, running, rate-limited, retrying, completed, failed)
- **FR-015**: Diagrams MUST be organized hierarchically: a navigation index linked from the README connects to subsystem-specific diagrams in dedicated documentation sections or files
- **FR-016**: A CI lint check MUST verify that class names, method names, and operation numbers referenced in Mermaid diagram code blocks still exist in the codebase, failing the build if references become stale

### Key Entities

- **Diagram**: A single Mermaid code block that renders a specific visualization. Has a type (flowchart, sequence, class, mindmap, etc.), a scope (what it documents), and a location (which file it lives in).
- **Diagram Family**: A group of related diagrams covering one subsystem (e.g., "Data Pipeline" family includes the sequence diagram, flowchart, and ER diagram). Families are linked via cross-references.
- **Color Theme**: The T-Mobile dark-mode palette applied consistently across all diagrams. Defined once and referenced by all diagram init blocks.
- **Navigation Index**: A master diagram or table of contents that links to all other diagrams, forming the hierarchy root.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer unfamiliar with MistHelper can identify all major subsystems and their relationships within 60 seconds of opening the README, by scanning the top-level architecture diagram alone
- **SC-002**: 100% of diagrams render correctly on GitHub.com's Mermaid renderer without errors, broken nodes, or truncated labels, verified in both dark and light mode
- **SC-003**: Every diagram is reachable from the navigation index within one click (direct anchor link or file link)
- **SC-004**: The color theme is consistent across all diagrams: primary accent matches T-Mobile Magenta (#E20074), backgrounds use dark tones (#1A1A2E or similar), and text contrast meets WCAG AA (4.5:1 ratio minimum)
- **SC-005**: At least 10 distinct Mermaid diagram types are used across the documentation suite (from: flowchart, sequence, class, state, ER, mindmap, C4/architecture, gitGraph, pie, Gantt, timeline, Kanban, packet, Sankey, XY chart, block, quadrant, requirement, user journey)
- **SC-006**: 100% of class names, method names, and operation numbers referenced in diagrams match actual identifiers found in the codebase (verified by CI lint script FR-016; non-code terms handled via allowlist), ensuring diagrams stay accurate
- **SC-007**: A developer can trace any menu operation from user invocation to data output by following the chain of linked diagrams (menu mindmap -> data pipeline sequence -> exporter class -> database ER) without consulting the source code
- **SC-008**: The complete diagram suite adds no more than 15 minutes to a reader's orientation time (the time to understand the project well enough to locate and modify a specific feature)

## Out of Scope

The following are explicitly excluded from this feature and may be addressed in future specifications:

- **Interactive click events**: Mermaid supports `click` callbacks for node interactivity. These are not supported by GitHub's renderer and are excluded.
- **Web portal embedding**: Diagrams will not be rendered in the Flask/Gunicorn web portal UI. They exist only as GitHub markdown.
- **Runtime auto-generation**: Diagrams will not be generated from runtime telemetry, code introspection, or database queries. They are static authored artifacts maintained via CI lint checks.
- **Animated diagrams**: No CSS animations or transition effects.
- **Third-party hosting**: Diagrams will not be hosted on external services (Mermaid Live Editor, mermaid.ink, etc.). All rendering relies on GitHub's built-in engine.

## Assumptions

- GitHub's Mermaid rendering engine supports `%%{init: {'theme': 'dark', 'themeVariables': {...}}}%%` directives for custom theming. If GitHub strips these directives, fallback to the default dark theme with high-contrast node styling.
- T-Mobile's official brand colors are public knowledge: Magenta (#E20074), with common dark variants (#99004D, #B9005A). The "dark mode" adaptation uses these as accents on dark backgrounds (#1A1A2E, #0D0D0D) with light text (#E0E0E0, #F5F5F5).
- Exactly 2 diagrams will be embedded inline in the README: the system architecture overview and the menu system mindmap. All other diagrams will live in separate markdown files under `documentation/diagrams/` and be linked from a navigation index in the README. This keeps the README scannable and supports the 60-second comprehension target.
- The audience is technical (developers reading code for inspiration) but potentially unfamiliar with Juniper Mist or network operations. Diagram labels should use plain language with technical terms explained on first use.
- GitHub imposes no hard limit on Mermaid diagram complexity, but empirical testing shows diagrams with more than ~100 nodes may fail to render. Diagrams will be split at the ~50-node boundary.

## Diagram Type Inventory

The following Mermaid diagram types will be used, mapped to the project concepts they document:

| Diagram Type | Mermaid Keyword | Project Concept | Location |
| --- | --- | --- | --- |
| Architecture | `architecture-beta` | System overview (subsystems, ports, external services) | README (inline) |
| Flowchart | `flowchart` | Data pipeline, PK strategy decision tree, error handling | docs |
| Sequence | `sequenceDiagram` | API call lifecycle, menu-to-output trace, WebSocket flow | docs |
| Class | `classDiagram` | Class families, inheritance chains, utility layering | docs |
| State | `stateDiagram-v2` | Operation lifecycle, rate limiter states, connection states | docs |
| Entity-Relationship | `erDiagram` | Database tables, PK strategies, index relationships | docs |
| Mindmap | `mindmap` | Menu system taxonomy, operation categories | README (inline) |
| Git Graph | `gitgraph` | Branching strategy, CI/CD triggers, auto-merge | docs |
| C4 Context | `C4Context` | High-level system context (users, external APIs, storage) | docs |
| Timeline | `timeline` | Project evolution, version history milestones | docs |
| Pie | `pie` | Operation category distribution, test coverage breakdown | docs |
| Gantt | `gantt` | CI/CD pipeline timing, deployment stages | docs |
| Kanban | `kanban` | Feature development workflow, spec-to-deploy lifecycle | docs |
| Packet | `packet-beta` | Network packet structure (for packet capture feature docs) | docs |
| User Journey | `journey` | NOC engineer workflow, menu navigation experience | docs |
| Block | `block-beta` | Container layer architecture, SSH session isolation | docs |
| Requirement | `requirementDiagram` | Safety requirements traceability (destructive ops) | docs |
| Sankey | `sankey-beta` | Data flow volume (API calls -> processing -> output) | docs |
| XY Chart | `xychart-beta` | Rate limiting metrics, adaptive delay visualization | docs |
| Quadrant | `quadrantChart` | Operation complexity vs. frequency matrix | docs |

## Clarifications

### Session 2026-03-28

- Q: How many diagrams should be embedded directly in the README vs. linked from docs? -> A: Exactly 2 in README (architecture overview + menu mindmap); all others linked from `documentation/diagrams/`
- Q: Should diagrams be static documentation or include automated freshness checks? -> A: Static + lint -- add a CI check that verifies class/method names referenced in diagrams still exist in the codebase
- Q: How should beta/experimental Mermaid diagram types be handled? -> A: Best-effort -- use beta types but include a fallback strategy (static PNG screenshot alongside each beta diagram in case GitHub drops support)
- Q: What level of class detail should the class hierarchy diagram show? -> A: Exhaustive -- every class appears, split across 5+ linked sub-diagrams by family (infrastructure, exporters, managers, utilities, etc.)
- Q: Which areas should be explicitly declared out of scope? -> A: All three -- no interactive click events, no web portal embedding, no runtime auto-generation. This feature is purely static documentation for GitHub markdown rendering.

## T-Mobile Dark Mode Color Palette

All diagrams will use this consistent palette applied via Mermaid `%%{init}%%` directives:

| Role | Color | Hex | Usage |
| --- | --- | --- | --- |
| Primary Accent | T-Mobile Magenta | `#E20074` | Key nodes, primary flow arrows, active states |
| Secondary Accent | Light Magenta | `#FF6F91` | Secondary nodes, hover states, annotations |
| Tertiary Accent | Deep Magenta | `#99004D` | Borders, emphasis strokes, destructive operations |
| Background | Near Black | `#1A1A2E` | Diagram backgrounds (where supported) |
| Surface | Dark Gray | `#16213E` | Container/group backgrounds, card surfaces |
| Text Primary | Off White | `#E0E0E0` | Primary labels, node text |
| Text Secondary | Light Gray | `#A0A0B0` | Secondary labels, annotations |
| Safe Ops | Muted Green | `#00C853` | Safe operation nodes in menu diagrams |
| Warning Ops | Amber | `#FFD600` | Interactive operation nodes |
| Danger Ops | Red | `#FF1744` | Destructive operation nodes |
| WIP Ops | Muted Blue | `#448AFF` | Work-in-progress operation nodes |
| Link Lines | Soft Magenta | `#FF4DA6` | Edge/arrow colors |
