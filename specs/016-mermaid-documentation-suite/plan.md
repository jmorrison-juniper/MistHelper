# Implementation Plan: Mermaid Documentation Suite

**Branch**: `016-mermaid-documentation-suite` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-mermaid-documentation-suite/spec.md`

## Summary

Create a comprehensive Mermaid diagram documentation suite for MistHelper using 20 distinct diagram types, themed with T-Mobile dark-mode colors (#E20074 magenta on #1A1A2E backgrounds). Two diagrams embed inline in the README (architecture overview + menu mindmap); all others live in `documentation/diagrams/`. A CI lint script validates that class/method names referenced in diagrams still exist in the codebase. Beta diagram types include PNG fallback images.

## Technical Context

**Language/Version**: Mermaid (GitHub-rendered), Python 3.13 (CI lint script only)
**Primary Dependencies**: GitHub Mermaid renderer (built-in), Mermaid syntax v11.x
**Storage**: N/A (documentation-only feature; no runtime data)
**Testing**: Manual GitHub rendering verification + CI lint script (pytest for the lint script itself)
**Target Platform**: GitHub.com markdown rendering (dark and light mode)
**Project Type**: Documentation / static content + one CI lint utility
**Performance Goals**: All diagrams render on GitHub within default timeout; no diagram exceeds 50 nodes
**Constraints**: GitHub Mermaid renderer limitations (no click events, limited theming, beta type stability); WCAG AA 4.5:1 contrast ratio
**Scale/Scope**: 20+ diagrams across 8-10 markdown files; 1 CI lint script; PNG fallbacks for 4-5 beta diagrams

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Status | Notes |
|-----------|----------|--------|-------|
| I. Five-Item Rule | YES | PASS | CI lint script will follow max 25 lines/function, max 5 params. Documentation files follow directory nesting <=5 children. |
| II. Class-Based Architecture | YES | PASS | CI lint script will be a class (`DiagramReferenceValidator`), not standalone functions. |
| III. Safety-First | NO | N/A | No user input, no destructive operations. Documentation-only feature. |
| IV. Full Deployment Pipeline | YES | PASS | CI lint script changes trigger normal pipeline. Documentation changes follow standard commit/push flow. |
| V. Observability & Logging | PARTIAL | PASS | CI lint script uses `logging` with ASCII-only output. No runtime logging for static markdown files. |

**Gate result: PASS** -- No violations. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/016-mermaid-documentation-suite/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
documentation/
└── diagrams/
    ├── README.md                        # Navigation index (all diagrams linked)
    ├── core/                            # Architecture, data pipeline, database
    │   ├── architecture-overview.md     # C4 Context + architecture-beta
    │   ├── architecture-overview.png    # PNG fallback (architecture-beta)
    │   ├── data-pipeline.md             # Sequence + flowchart diagrams
    │   └── database-strategy.md         # ER diagram + PK decision flowchart
    ├── class-hierarchy/                 # Class family diagrams
    │   ├── overview.md                  # Top-level class family map
    │   ├── infrastructure.md            # Core/infra class family
    │   ├── exporters.md                 # Exporter class family
    │   ├── managers.md                  # Manager class family (WebSocket, Firmware, etc.)
    │   └── utilities.md                 # Utility class family (API fetch chain, etc.)
    ├── operations/                      # Operations, metrics, workflow
    │   ├── operations-reference.md      # State diagram + user journey + requirement diagram
    │   ├── metrics-and-analytics.md     # Pie, XY chart, Sankey, quadrant, timeline
    │   ├── metrics-xychart.png          # PNG fallback (xychart-beta)
    │   ├── data-flow-sankey.png         # PNG fallback (sankey-beta)
    │   └── development-workflow.md      # Kanban diagram
    └── infrastructure/                  # Deployment, container, network
        ├── deployment-pipeline.md       # CI/CD flowchart + Gantt + gitGraph
        ├── container-architecture.md    # Block diagram + architecture-beta
        ├── container-architecture.png   # PNG fallback (block-beta)
        ├── network-protocols.md         # Packet diagram (for pcap feature docs)
        └── network-protocols.png        # PNG fallback (packet-beta)

scripts/
└── lint_diagram_refs.py             # CI lint: validate diagram references

tests/
└── unit/
    └── test_lint_diagram_refs.py    # Tests for the lint script

README.md                            # Updated: 2 inline diagrams + nav index link
```

**Structure Decision**: Documentation files organized under `documentation/diagrams/` with 4 content subdirectories: `core/` (architecture + data pipeline + database), `class-hierarchy/` (class family diagrams), `operations/` (menu system + metrics + workflow), and `infrastructure/` (deployment + container + network). Each directory has at most 5 children, satisfying the Five-Item Rule at every level. PNG fallback images for beta diagram types are placed alongside their source markdown files.

## Complexity Tracking

No constitution violations to justify. All principles are satisfied by the structure above.

## Constitution Re-Check (Post Phase 1 Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | `documentation/diagrams/` has 5 children (README.md + 4 subdirectories). Each subdirectory has at most 5 children. Class hierarchy properly split into its own subdirectory (5 files). The lint script has max 5 params, max 25 lines/function. |
| II. Class-Based Architecture | PASS | Lint script uses `DiagramReferenceValidator` class per contract. No standalone wrapper functions. |
| III. Safety-First | N/A | No user input or destructive operations in any artifact. |
| IV. Full Deployment Pipeline | PASS | Documentation and lint script changes follow standard pipeline. CI integration adds one matrix entry. |
| V. Observability & Logging | PASS | Lint script outputs structured results to stdout with ASCII-only text. |

**Post-design gate result: PASS** -- All principles satisfied. No deviations.
