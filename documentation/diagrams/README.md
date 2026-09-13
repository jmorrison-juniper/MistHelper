# MistHelper Visual Documentation

[<- Back to Repository](../../README.md)

Comprehensive Mermaid diagram suite documenting MistHelper's architecture, class hierarchy, operations, and infrastructure. All diagrams use T-Mobile dark-mode theming.

---

## Core

Architecture, data pipeline, and database design.

| Diagram | Types | Description |
|---------|-------|-------------|
| [Architecture Overview](core/architecture-overview.md) | `C4Context` `architecture-beta` | System context and internal component relationships |
| [Data Pipeline](core/data-pipeline.md) | `sequenceDiagram` `flowchart` | Menu-to-output data flow with error handling |
| [Database Strategy](core/database-strategy.md) | `erDiagram` `flowchart` | Hybrid PK system and strategy decision tree |

## Class Hierarchy

All 99+ classes organized into 12 families with inheritance and composition relationships.

| Diagram | Types | Description |
|---------|-------|-------------|
| [Overview](class-hierarchy/overview.md) | `classDiagram` | Top-level family map with inter-family dependencies |
| [Infrastructure](class-hierarchy/infrastructure.md) | `classDiagram` | Core, configuration, and API fetching classes |
| [Exporters](class-hierarchy/exporters.md) | `classDiagram` | Org, site, and gateway exporter families |
| [Managers](class-hierarchy/managers.md) | `classDiagram` | Manager classes (firmware, SSH, WebSocket, etc.) |
| [Utilities](class-hierarchy/utilities.md) | `classDiagram` | 23+ utility classes and data processing |

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

---

## Diagram Type Coverage

This suite uses all 20 Mermaid diagram types:

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

All diagrams apply the T-Mobile dark-mode palette defined in [theme-contract.md](../../specs/016-mermaid-documentation-suite/contracts/theme-contract.md). Primary accent: `#E20074` (T-Mobile Magenta) on `#1A1A2E` backgrounds.

## PNG Fallbacks

Beta diagram types include PNG fallback images for environments where beta rendering is unavailable:

- [architecture-overview.png](core/architecture-overview.png) (architecture-beta)
- [container-architecture.png](infrastructure/container-architecture.png) (block-beta)
- [network-protocols.png](infrastructure/network-protocols.png) (packet-beta)
- [data-flow-sankey.png](operations/data-flow-sankey.png) (sankey-beta)
- [metrics-xychart.png](operations/metrics-xychart.png) (xychart-beta)
