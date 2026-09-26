[<- Back to Diagram Index](../README.md)

# Database Strategy

Hybrid primary key system and strategy decision flowchart for MistHelper storage backends.

## Entity Relationship Diagram

Representative tables show the strategy types used across 270 registered menu entries.

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
erDiagram
    SITES {
        uuid id PK "Natural PK - API UUID"
        uuid org_id FK "Index"
        string name "Index"
        string country_code "Index"
        string address "Index"
        timestamp created_at
        timestamp modified_at
    }

    DEVICE_INVENTORY {
        uuid id PK "Natural PK - API UUID"
        uuid org_id FK "Index"
        uuid site_id FK "Index"
        string mac "Index"
        string serial "Index"
        string model "Index"
        string type "Index"
    }

    DEVICE_EVENTS {
        uuid id PK "Composite PK part 1"
        uuid device_id PK "Composite PK part 2"
        timestamp timestamp PK "Composite PK part 3"
        string type "Index"
        uuid org_id FK "Index"
        uuid site_id FK "Index"
        string text
    }

    DEVICE_STATS {
        uuid device_id PK "TimeSeries PK part 1"
        timestamp timestamp PK "TimeSeries PK part 2"
        uuid org_id FK "Index"
        uuid site_id FK "Index"
        string type "Index"
        float cpu_usage
        float memory_usage
    }

    ORG_ALARMS {
        uuid id PK "Composite PK part 1"
        uuid org_id PK "Composite PK part 2"
        timestamp timestamp PK "Composite PK part 3"
        string severity "Index"
        string type "Index"
        uuid site_id FK "Index"
    }

    LICENSES_SUMMARY {
        integer misthelper_internal_id PK "Auto-increment PK"
        uuid org_id "Index"
        string sku "Index"
        string type "Index"
        integer quantity
    }

    SITES ||--o{ DEVICE_INVENTORY : "hosts"
    SITES ||--o{ DEVICE_EVENTS : "generates"
    SITES ||--o{ DEVICE_STATS : "reports"
    SITES ||--o{ ORG_ALARMS : "triggers"
    DEVICE_INVENTORY ||--o{ DEVICE_EVENTS : "produces"
    DEVICE_INVENTORY ||--o{ DEVICE_STATS : "reports"
```

## PK Strategy Decision Tree

How to choose the right primary key strategy when adding a new operation.

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
flowchart TD
    A[New API Endpoint] --> B{Does response include<br/>a stable UUID id field?}

    B -->|Yes| C{Is the data<br/>time-series?}
    B -->|No| F{Is the data<br/>aggregated/summary?}

    C -->|No| D[natural_pk<br/>PK = id]
    C -->|Yes| E{Does the row hold<br/>numeric metric fields?}

    F -->|Yes| G[auto_increment_with_unique<br/>PK = misthelper_internal_id]
    F -->|No| H{Can you construct<br/>a unique composite key?}

    E -->|Yes| TS[timeseries_pk<br/>PK = entity + timestamp]
    E -->|No| CP[composite_pk<br/>PK = id + entity + timestamp]

    H -->|Yes| I[composite_pk<br/>PK = custom composite fields]
    H -->|No| G

    D --> J[INSERT OR REPLACE by UUID]
    CP --> J2[INSERT OR REPLACE by composite]
    TS --> J4[Redis TimeSeries write]
    G --> J3[INSERT with unique constraint check]
    I --> J2

    style D fill:#00C853,stroke:#00C853,color:#1A1A2E
    style E fill:#FFD600,stroke:#FFD600,color:#1A1A2E
    style TS fill:#FFD600,stroke:#FFD600,color:#1A1A2E
    style G fill:#E20074,stroke:#99004D,color:#E0E0E0
    style I fill:#FFD600,stroke:#FFD600,color:#1A1A2E
```

## Strategy Examples

| API Endpoint | PK Type | Primary Key | Use Case |
|-------------|---------|-------------|----------|
| `listOrgSites` | `natural_pk` | `[id]` | Sites have stable UUIDs |
| `searchOrgDeviceEvents` | `composite_pk` | `[id, device_id, timestamp]` | Time-series event data |
| `listOrgDevicesStats` | `timeseries_pk` | `[device_id, timestamp]` | Periodic device statistics |
| `searchOrgAlarms` | `composite_pk` | `[id, org_id, timestamp]` | Time-stamped alarm records |
| `getOrgLicensesSummary` | `auto_increment_with_unique` | `[misthelper_internal_id]` | Aggregated summary without stable ID |

---

## Related Diagrams

- [Data Pipeline](data-pipeline.md) - Output paths with PK strategy selection
- [Data Persistence Routing](data-persistence-routing.md) - Polyglot routing decision tree (ArangoDB/Redis)
- [Architecture Overview](architecture-overview.md) - Database backends in system context
- [Class Hierarchy: Utilities](../class-hierarchy/utilities.md) - DatabaseSchemaUtils and SQLiteDatabaseWriter

## Source of Truth

`src/refactors/endpoint_primary_key_strategies.py` holds the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary. `src/db/router.py` maps
`natural_pk` and `auto_increment_with_unique` to ArangoDB, `composite_pk` to
ArangoDB plus Redis JSON, and `timeseries_pk` to Redis TimeSeries.
