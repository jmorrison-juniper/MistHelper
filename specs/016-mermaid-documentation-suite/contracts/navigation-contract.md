# Contract: Diagram Navigation Structure

**Feature**: 016-mermaid-documentation-suite  
**Date**: 2026-03-28

## Purpose

Defines the navigation hierarchy that connects all diagrams via markdown links, ensuring every diagram is reachable from the master index within one click (SC-003).

## Navigation Hierarchy

```
README.md (2 inline diagrams)
  |
  +-- "Visual Documentation" section
  |     |
  |     +-- link to documentation/diagrams/README.md (navigation index)
  |
  +-- Architecture diagram (inline)
  +-- Menu mindmap (inline)

documentation/diagrams/README.md (navigation index)
  |
  +-- Core
  |     +-- core/architecture-overview.md (architecture-beta + C4Context)
  |     +-- core/data-pipeline.md (sequenceDiagram + flowchart)
  |     +-- core/database-strategy.md (erDiagram + flowchart)
  |
  +-- Class Hierarchy
  |     +-- class-hierarchy/overview.md (top-level family map)
  |     +-- class-hierarchy/infrastructure.md
  |     +-- class-hierarchy/exporters.md
  |     +-- class-hierarchy/managers.md
  |     +-- class-hierarchy/utilities.md
  |
  +-- Operations
  |     +-- operations/operations-reference.md (stateDiagram + journey + requirementDiagram)
  |     +-- operations/metrics-and-analytics.md (pie + xychart + sankey + quadrant + timeline)
  |     +-- operations/development-workflow.md (kanban)
  |
  +-- Infrastructure
        +-- infrastructure/deployment-pipeline.md (flowchart + gantt + gitgraph)
        +-- infrastructure/container-architecture.md (block-beta + architecture-beta)
        +-- infrastructure/network-protocols.md (packet-beta)
```

## Cross-Reference Rules

1. Every diagram file MUST have a "Back to index" link at the top pointing to `documentation/diagrams/README.md`
2. Every diagram file MUST have "Related diagrams" links at the bottom pointing to semantically related files
3. The README's inline diagrams MUST have a "See all diagrams" link to the navigation index
4. Class hierarchy sub-diagrams MUST link to their parent overview and sibling family diagrams
5. The navigation index MUST list all diagram files with brief descriptions and diagram type badges

## Link Format Convention

```markdown
<!-- Top of every diagram file -->
[<- Back to Diagram Index](README.md)

<!-- Bottom of every diagram file -->
## Related Diagrams
- [Architecture Overview](architecture-overview.md) - System-level context
- [Data Pipeline](data-pipeline.md) - How data flows through the system
```
