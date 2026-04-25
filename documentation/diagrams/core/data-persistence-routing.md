# Data Persistence Routing

## Decision Tree

How MistHelper routes data to the appropriate storage backend based on
the primary key strategy defined in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

```mermaid
flowchart TD
    A["Menu Operation<br/>(e.g. Menu 11, 13, 45)"] --> B["API Call<br/>mistapi SDK"]
    B --> C["Flatten / Normalize<br/>JSON Response"]
    C --> D["save_data_to_output()"]

    D --> E["CSV / SQLite / ArangoDB+Redis<br/>write_with_format_selection()"]
    D --> F{"api_function_name<br/>provided?"}

    F -->|No| G["Skip polyglot<br/>(CSV only)"]
    F -->|Yes| H["_route_to_polyglot()"]

    H --> I["DatabaseRouter.write()"]

    I --> J{"Standalone mode?<br/>(no DB env vars)"}
    J -->|Yes| K["Return csv_only<br/>(graceful degrade)"]

    J -->|No| L{"Look up<br/>ENDPOINT_PRIMARY_KEY_STRATEGIES"}

    L --> M{"Strategy Type?"}

    M -->|natural_pk| N["ArangoDB Writer"]
    M -->|auto_increment_with_unique| N
    M -->|composite_pk| O["Redis TimeSeries Writer"]

    N --> P{"ArangoDB<br/>available?"}
    P -->|No| Q["Fallback: csv_only"]
    P -->|Yes| R["import_bulk()<br/>batches of 5,000<br/>on_duplicate=replace"]

    R --> S{"Config entity?<br/>(sites, WLANs, templates...)"}
    S -->|Yes| T["Config Snapshot<br/>SHA-256 hash tracking"]
    S -->|No| U["Done"]
    T --> U

    O --> V{"Redis<br/>available?"}
    V -->|No| W["Fallback: csv_only"]
    V -->|Yes| X["Extract numeric fields<br/>ThreadPoolExecutor<br/>(8 workers)"]

    X --> Y["Pipeline TS.CREATE<br/>batches of 500<br/>DUPLICATE_POLICY LAST"]
    Y --> Z["Pipeline TS.ADD<br/>batches of 10,000"]
    Z --> AA["Auto-compaction rules<br/>hourly + daily rollups"]
    AA --> U

    style N fill:#4a9,stroke:#333,color:#fff
    style O fill:#e74,stroke:#333,color:#fff
    style Q fill:#888,stroke:#333,color:#fff
    style W fill:#888,stroke:#333,color:#fff
    style K fill:#888,stroke:#333,color:#fff
    style G fill:#888,stroke:#333,color:#fff
```

## Strategy Routing Summary

| Strategy Type | Backend | Use Case | Examples |
| - | - | - | - |
| `natural_pk` | ArangoDB | Entities with stable UUIDs | Sites, Inventory, Templates |
| `auto_increment_with_unique` | ArangoDB | Aggregated data without stable keys | Licenses summary |
| `composite_pk` | Redis TimeSeries | Time-series metrics | Device stats, Alarms, Events |

## Key Files

| File | Role |
| - | - |
| `MistHelper.py` | `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict, `_route_to_polyglot()` |
| `src/db/router.py` | `DatabaseRouter` — strategy lookup and backend dispatch |
| `src/db/arango_writer.py` | `ArangoDBWriter` — batch `import_bulk()`, snapshots, graph edges |
| `src/db/redis_writer.py` | `RedisTimeSeriesWriter` — pipelined TS.CREATE/TS.ADD, compaction |
| `src/db/__init__.py` | `DatabaseConfig`, `WriteResult`, shared logger |
