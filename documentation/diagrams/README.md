# MistHelper Visual Documentation

[<- Back to Repository](../../README.md)

Mermaid diagram suite for MistHelper architecture, operations, and infrastructure. The diagrams use a shared dark theme.

---

## Core

Architecture, data pipeline, and database design.

| Diagram | Types | Description |
|---------|-------|-------------|
| [Architecture Overview](core/architecture-overview.md) | `C4Context` `architecture-beta` | System context and internal component relationships |
| [Data Pipeline](core/data-pipeline.md) | `sequenceDiagram` `flowchart` | Menu-to-output data flow with error handling |
| [Database Strategy](core/database-strategy.md) | `erDiagram` `flowchart` | Hybrid PK system and strategy decision tree |

## Class Hierarchy

Class diagrams group the current Python classes by responsibility and dependency.

| Diagram | Types | Description |
|---------|-------|-------------|
| [Overview](class-hierarchy/overview.md) | `classDiagram` | Top-level family map with inter-family dependencies |
| [Infrastructure](class-hierarchy/infrastructure.md) | `classDiagram` | Core, configuration, and API fetching classes |
| [Exporters](class-hierarchy/exporters.md) | `classDiagram` | Org, site, and gateway exporter families |
| [Managers](class-hierarchy/managers.md) | `classDiagram` | Manager classes (firmware, SSH, WebSocket, etc.) |
| [Utilities](class-hierarchy/utilities.md) | `classDiagram` | Utility classes and data processing |

## Operations

Menu system, metrics, and development workflow.

| Diagram | Types | Description |
|---------|-------|-------------|
| [Operations Reference](operations/operations-reference.md) | `stateDiagram-v2` `journey` `requirementDiagram` | Operation lifecycle, NOC engineer journey, safety requirements |
| [Metrics and Analytics](operations/metrics-and-analytics.md) | `pie` `xychart-beta` `sankey-beta` `quadrantChart` `timeline` | Operation distribution, rate limiting, data flow volumes |
| [Development Workflow](operations/development-workflow.md) | `kanban` | SpecKit feature lifecycle board |

## Infrastructure

Deployment, container architecture, and network protocols.

| Diagram | Types | Description |
|---------|-------|-------------|
| [Deployment Pipeline](infrastructure/deployment-pipeline.md) | `flowchart` `gantt` `gitgraph` | CI/CD quality gates, timing, and branching strategy |
| [Container Architecture](infrastructure/container-architecture.md) | `block-beta` `architecture-beta` | Container layers, session isolation, port mappings |
| [Network Protocols](infrastructure/network-protocols.md) | `packet-beta` | Packet structure for pcap feature documentation |

## Menu API Endpoint Map

A generator writes these pages from the code. Each menu option gets one flowchart of the Mist API endpoints that it calls.

| Page | Types | Description |
|---------|-------|-------------|
| [Menu API endpoint map](../menu-api/README.md) | `flowchart` `pie` | The request path, the method mix, and one endpoint breakdown for each menu option |

---

## Diagram Type Coverage

This suite uses these Mermaid diagram types:

| Type | File(s) |
|------|---------|
| `architecture-beta` | Architecture Overview, Container Architecture |
| `block-beta` | Container Architecture |
| `C4Context` | Architecture Overview |
| `classDiagram` | Class Hierarchy (5 files) |
| `erDiagram` | Database Strategy |
| `flowchart` | Data Pipeline, Database Strategy, Deployment Pipeline |
| `gantt` | Deployment Pipeline |
| `gitgraph` | Deployment Pipeline |
| `journey` | Operations Reference |
| `kanban` | Development Workflow |
| `mindmap` | README.md (inline) |
| `packet-beta` | Network Protocols |
| `pie` | Metrics and Analytics |
| `quadrantChart` | Metrics and Analytics |
| `requirementDiagram` | Operations Reference |
| `sankey-beta` | Metrics and Analytics |
| `sequenceDiagram` | Data Pipeline |
| `stateDiagram-v2` | Operations Reference |
| `timeline` | Metrics and Analytics |
| `xychart-beta` | Metrics and Analytics |

---

## Theme

Most diagrams use the shared dark palette that sets `#E20074` as the primary accent.

## Beta diagram types

These diagrams use a beta Mermaid type. A viewer without beta support does not
render them. Open them on GitHub:

- [Architecture Overview](core/architecture-overview.md) (architecture-beta)
- [Container Architecture](infrastructure/container-architecture.md) (block-beta)
- [Network Protocols](infrastructure/network-protocols.md) (packet-beta)
- [Metrics and Analytics](operations/metrics-and-analytics.md) (sankey-beta, xychart-beta)
