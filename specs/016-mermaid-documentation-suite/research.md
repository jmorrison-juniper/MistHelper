# Research: Mermaid Documentation Suite

**Feature**: 016-mermaid-documentation-suite  
**Date**: 2026-03-28

## R1: GitHub Mermaid Rendering Engine Capabilities

**Task**: Determine which Mermaid features and diagram types GitHub actually supports, and what theming controls are available.

### Decision: GitHub supports `%%{init}%%` directives and most Mermaid v11 diagram types

**Rationale**:
- GitHub uses a built-in Mermaid renderer (version checkable via `info` diagram type)
- GitHub renders Mermaid inside fenced code blocks with `mermaid` language identifier
- `%%{init: {'theme': 'dark', 'themeVariables': {...}}}%%` directives ARE processed by GitHub's renderer. This is confirmed by widespread usage in public repositories.
- GitHub applies its own CSS context (dark/light mode) around the rendered SVG, which means diagram backgrounds may be overridden by GitHub's page background
- YAML frontmatter (`---\nconfig:\n---`) is also supported for configuration

**Alternatives considered**:
- Using static images only (rejected: loses the text-searchable, version-controllable advantage of Mermaid source)
- Using mermaid.ink API for rendering (rejected: spec explicitly excludes third-party hosting)

### Supported Diagram Types on GitHub (confirmed)

| Type | Keyword | Status |
|------|---------|--------|
| Flowchart | `flowchart` / `graph` | Stable |
| Sequence | `sequenceDiagram` | Stable |
| Class | `classDiagram` | Stable |
| State | `stateDiagram-v2` | Stable |
| ER | `erDiagram` | Stable |
| Gantt | `gantt` | Stable |
| Pie | `pie` | Stable |
| Git Graph | `gitgraph` | Stable |
| Mindmap | `mindmap` | Stable |
| Timeline | `timeline` | Stable |
| User Journey | `journey` | Stable |
| Requirement | `requirementDiagram` | Stable |
| Quadrant | `quadrantChart` | Stable |
| XY Chart | `xychart-beta` | Beta (functional) |
| Sankey | `sankey-beta` | Beta (functional) |
| Block | `block-beta` | Beta (functional) |
| Packet | `packet-beta` | Beta (functional) |
| Architecture | `architecture-beta` | Beta (functional) |
| C4 | `C4Context` | Stable (via built-in) |
| Kanban | `kanban` | Stable (v11+) |

**Key risk**: Beta types may change syntax or be removed. Mitigation per spec: PNG fallback images for all beta diagrams.

## R2: Theming Strategy for T-Mobile Dark Mode on GitHub

**Task**: Determine the best approach for applying custom T-Mobile colors across all diagram types on GitHub.

### Decision: Use `%%{init}%%` with `themeVariables` per diagram, falling back to `classDef` node styling

**Rationale**:
- GitHub does NOT strip `%%{init}%%` directives. Custom `themeVariables` like `primaryColor`, `primaryTextColor`, `lineColor`, `secondaryColor` are applied.
- However, GitHub wraps the rendered SVG in its own container with background applied via CSS. This means the `background` themeVariable may be overridden.
- Best approach: Use `theme: 'dark'` as the base, then override specific variables for the magenta palette. For node-level coloring (e.g., safety categories), use `classDef` with explicit fill/stroke.
- For diagram types that don't support `themeVariables` well (Gantt, XY chart), use `style` directives on individual nodes.

**Implementation pattern**:
```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'fontFamily': 'ui-monospace, monospace'
}}}%%
```

For safety-classification coloring in flowcharts/mindmaps:
```
classDef safe fill:#00C853,stroke:#00C853,color:#1A1A2E
classDef warning fill:#FFD600,stroke:#FFD600,color:#1A1A2E
classDef danger fill:#FF1744,stroke:#FF1744,color:#E0E0E0
classDef wip fill:#448AFF,stroke:#448AFF,color:#E0E0E0
```

**Alternatives considered**:
- Single theme file referenced across diagrams (rejected: Mermaid doesn't support shared theme imports in markdown)
- Custom CSS injection (rejected: GitHub strips inline styles and script tags)

## R3: GitHub Rendering Limits and Diagram Splitting Strategy

**Task**: Determine practical limits for diagram complexity and how to split large diagrams.

### Decision: Target 40-50 nodes per diagram; split by semantic family with cross-reference links

**Rationale**:
- GitHub's Mermaid renderer has no documented hard limit, but community reports indicate diagrams with 100+ nodes frequently fail to render or render incorrectly
- Empirical best practice: 40-50 nodes maximum per diagram for reliable rendering
- The class hierarchy (99+ classes) will require 6+ sub-diagrams (one per family)
- The menu mindmap (137+ operations) will require either deep nesting (which Mermaid mindmaps handle well since each branch is a separate subtree) or splitting into category-specific sub-diagrams
- Cross-referencing: Use markdown links between diagram pages. Mermaid `click` events are not supported on GitHub.

**Splitting strategy**:
1. **Class hierarchy**: 1 overview diagram (family names only, ~10 nodes) + 6 family sub-diagrams (~10-20 classes each)
2. **Menu mindmap**: Single diagram with collapsed depth (category -> subcategory -> operation ranges, not individual operations). Individual operation listings as markdown tables below the mindmap.
3. **Data pipeline**: 1 sequence diagram (happy path, ~15 participants) + 1 flowchart (error handling, ~20 nodes)
4. **All other diagrams**: Single diagram each, all under 30 nodes

## R4: CI Lint Script Design for Diagram Reference Validation

**Task**: Research best approach for a CI lint script that validates class/method names in diagrams against the codebase.

### Decision: Python script using regex extraction from Mermaid code blocks + AST parsing of MistHelper.py

**Rationale**:
- Mermaid diagram source is embedded in markdown fenced code blocks
- The lint script needs to: (1) find all Mermaid code blocks in docs, (2) extract identifiers that look like class/method names, (3) verify those identifiers exist in the Python codebase
- Python's `ast` module can parse MistHelper.py and extract all class names and method names
- Regex patterns can extract identifiers from Mermaid syntax (node labels in brackets, participant names in sequence diagrams, class names in class diagrams)
- The script should have a configurable allowlist for Mermaid keywords that look like identifiers but aren't (e.g., "API", "SSH", "CSV")

**Implementation approach**:
- Class: `DiagramReferenceValidator` (per Constitution Principle II)
- Input: list of markdown files to scan, Python source files to validate against
- Output: list of stale references (file, line, identifier, closest match)
- Exit code: 0 if clean, 1 if stale references found
- CI integration: Add as matrix entry in `quality-gates` job in `ci.yml`

**Alternatives considered**:
- Shell script with grep (rejected: too brittle for Mermaid syntax parsing)
- Third-party tool like `mermaid-lint` (rejected: no tool exists for cross-reference validation)
- Skipping validation entirely (rejected: spec requires FR-016)

## R5: PNG Fallback Generation for Beta Diagrams

**Task**: Determine how to generate static PNG fallback images for beta Mermaid diagram types.

### Decision: Use Mermaid CLI (`mmdc`) locally to render PNGs; commit to `documentation/diagrams/fallback/`

**Rationale**:
- `@mermaid-js/mermaid-cli` (mmdc) can render any Mermaid diagram to PNG/SVG from the command line
- PNGs are committed alongside the markdown source for offline resilience
- If a beta diagram stops rendering on GitHub, the markdown file can switch to `![fallback](fallback/filename.png)` via a simple PR
- PNGs are generated once during initial authoring and updated when diagram source changes
- No CI automation for PNG generation (manual process; static docs)

**Beta diagrams requiring fallbacks** (4 total):
1. `architecture-beta` - System architecture overview
2. `block-beta` - Container layer architecture
3. `packet-beta` - Network packet structure
4. `sankey-beta` - Data flow volume

**Alternatives considered**:
- CI-generated PNGs via GitHub Actions (rejected: adds build complexity for a rare failure mode)
- SVG fallbacks (rejected: PNG is more portable and renders consistently)
- No fallbacks (rejected: spec requires FR-012 fallback strategy)

## R6: Existing Documentation Integration Points

**Task**: Understand what already exists in the `documentation/` directory and where new diagrams integrate.

### Decision: Create new `documentation/diagrams/` subdirectory; link from existing README and docs

**Rationale**:
- The `documentation/` directory currently contains 27+ files (API specs, guides, samples, HTML docs) but zero Mermaid diagrams and no `diagrams/` subdirectory
- README.md has zero existing diagrams -- there is a clean insertion point
- The README already has sections for architecture, operations, deployment that can receive inline diagram references
- Existing docs like `SSH_GUIDE.md` and `CHANGELOG.md` can link to relevant diagrams but should not be restructured
- The `documentation/diagrams/README.md` will serve as the master navigation index

**Integration points in README.md**:
1. Top of file: Insert architecture diagram (inline) after project description
2. After operations table: Insert menu mindmap (inline)
3. After operations section: Add "Visual Documentation" section linking to `documentation/diagrams/`
