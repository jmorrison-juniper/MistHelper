[<- Back to Diagram Index](../README.md)

# Data Pipeline

Traces the complete data flow from menu selection through API calls, pagination, rate limiting, data transformation, to dual-format output (CSV/SQLite).

## Happy-Path Sequence

How a typical data extraction operation flows through MistHelper's class chain.

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
sequenceDiagram
    participant User
    participant Menu as OperationRegistry
    participant Fetch as APIFetchUtils
    participant Rate as RateLimitingUtils
    participant API as Mist Cloud API
    participant Process as DataProcessingUtils
    participant Export as DataExporter

    User->>Menu: Select operation (e.g., --menu 11)
    Menu->>Fetch: fetch_with_pagination(endpoint)
    
    loop Each Page (up to 1000 items/page)
        Fetch->>Rate: _apply_rate_limiting()
        Rate-->>Fetch: delay_ms (adaptive)
        Fetch->>API: GET /api/v1/orgs/{org_id}/...
        API-->>Fetch: JSON response + pagination headers
        Fetch->>Fetch: Accumulate results
    end

    Fetch-->>Menu: Complete dataset (list[dict])
    Menu->>Process: flatten_and_normalize(data)
    Process->>Process: flatten_dict() for nested JSON
    Process->>Process: sanitize_filename()
    Process-->>Menu: Flat records (list[dict])
    Menu->>Export: write_with_format_selection(data, filename)
    
    alt CSV Output
        Export->>Export: Write to data/{filename}.csv
    else SQLite Output
        Export->>Export: Upsert to data/mist_data.db
    end
    
    Export-->>User: Operation complete
```

## Error Handling and Recovery

Decision flowchart showing how MistHelper handles API errors, rate limits, and output failures.

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
    A[API Request] --> B{Response Status?}
    
    B -->|200 OK| C[Parse JSON Response]
    B -->|429 Rate Limited| D[Rate Limit Handler]
    B -->|401/403 Auth Error| E[Log Auth Failure]
    B -->|5xx Server Error| F{Retry Count < Max?}
    B -->|Network Error| F
    
    D --> G[Read Retry-After Header]
    G --> H[Adaptive Delay Calculation]
    H --> I[Update delay_metrics.json]
    I --> J[Wait and Retry]
    J --> A
    
    F -->|Yes| K[Exponential Backoff]
    K --> A
    F -->|No| L[Log Error + Return Partial Data]
    
    E --> L
    
    C --> M{More Pages?}
    M -->|Yes - Has next cursor| N[Update Pagination Cursor]
    N --> A
    M -->|No| O[Flatten and Normalize]
    
    O --> P{Output Format?}
    P -->|CSV| Q[Write CSV to data/ directory]
    P -->|SQLite| R{PK Strategy?}
    
    R -->|natural_pk| S[INSERT OR REPLACE by UUID]
    R -->|composite_pk| T[INSERT OR REPLACE by composite key]
    R -->|auto_increment| U[INSERT with unique constraint]
    
    S --> V[Operation Complete]
    T --> V
    U --> V
    Q --> V
    L --> V

    style A fill:#E20074,stroke:#99004D,color:#E0E0E0
    style V fill:#00C853,stroke:#00C853,color:#1A1A2E
    style D fill:#FFD600,stroke:#FFD600,color:#1A1A2E
    style E fill:#FF1744,stroke:#FF1744,color:#E0E0E0
    style L fill:#FF1744,stroke:#FF1744,color:#E0E0E0
```

## Key Classes in the Pipeline

| Stage | Class | Key Method |
|-------|-------|------------|
| Entry Point | `OperationRegistry` | Dispatches menu selection to handler |
| API Calls | `APIFetchUtils` | `fetch_with_pagination()` |
| Rate Limiting | `RateLimitingUtils` | `_apply_rate_limiting()` with PID-like control |
| Data Transform | `DataProcessingUtils` | `flatten_dict()`, `sanitize_filename()` |
| CSV Output | `DataExporter` | `write_with_format_selection()` |
| SQLite Output | `SQLiteDatabaseWriter` | `upsert_records()` with PK strategies |

---

## Related Diagrams

- [Architecture Overview](architecture-overview.md) - System-level component map
- [Database Strategy](database-strategy.md) - PK strategy details for SQLite upserts
- [Operations Reference](../operations/operations-reference.md) - Operation lifecycle states
- [Class Hierarchy: Utilities](../class-hierarchy/utilities.md) - DataProcessingUtils detail
