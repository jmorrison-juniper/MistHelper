[<- Back to Diagram Index](../README.md)

# Metrics and Analytics

Operation distribution, rate limiting behavior, data flow volumes, and version history.

## Operation Category Distribution

How MistHelper's 193 operations break down by safety classification.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'pie1': '#E20074',
  'pie2': '#FF6F91',
  'pie3': '#99004D',
  'pie4': '#00C853',
  'pie5': '#FFD600',
  'pie6': '#FF1744',
  'pie7': '#448AFF',
  'pie8': '#A0A0B0',
  'pieTitleTextColor': '#E0E0E0',
  'pieSectionTextColor': '#E0E0E0'
}, 'pie': {'textPosition': 0.75}}}%%
pie title Operation Safety Classification (193 total)
    "Safe (59)" : 59
    "Destructive (40)" : 40
    "Interactive Safe (37)" : 37
    "Interactive (27)" : 27
    "WebSocket (22)" : 22
    "Resource Intensive (6)" : 6
    "Continuous (2)" : 2
```

## Operation Complexity vs Frequency

Where operations fall on the complexity-frequency spectrum.

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
flowchart TB
    subgraph q1["Complex and Frequent"]
        pcap["Packet Capture"]
        ws["WebSocket Diag"]
        ssh["SSH Runner"]
    end

    subgraph q2["Complex and Rare"]
        fw["AP Firmware"]
        vc["VC Conversion"]
        fsc["Full Site Config"]
    end

    subgraph q3["Simple and Frequent"]
        inv["Device Inventory"]
        sites["Site Listing"]
        lic["License Summary"]
    end

    subgraph q4["Moderate Complexity"]
        alarms["Alarm Events"]
        stats["Device Stats"]
        clients["Client Export"]
    end
```

## Rate Limiting Adaptive Delay

How MistHelper's PID-like controller adjusts API request delay over time.

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
flowchart LR
    subgraph input["Request Phase"]
        R1["Requests 1-10<br/>Delay: 100ms"]
        R2["Requests 11-15<br/>Delay: 100ms"]
    end

    subgraph spike["429 Rate Limit Hit"]
        R3["Requests 15-20<br/>Delay: 2000-4500ms"]
    end

    subgraph recovery["Recovery Phase"]
        R4["Requests 25-35<br/>Delay: 4000-1500ms"]
        R5["Requests 40-50<br/>Delay: 500-200ms"]
    end

    R1 --> R2 --> R3 -->|"PID controller<br/>backs off"| R4 -->|"Delay decreases<br/>as 429s stop"| R5
```

> **PNG fallback**: If this diagram does not render, see [metrics-xychart.png](metrics-xychart.png).

## Data Flow Volumes

How API data flows through processing stages to output formats.

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
flowchart LR
    API["API Calls<br/>1000 requests"] --> PH["Pagination Handler"]
    PH --> RL["Rate Limiter"]
    RL -->|"950 OK"| JP["JSON Parser"]
    RL -->|"50 retried"| R429["Rate Limited 429"]
    R429 --> RL
    JP --> FL["Flattener<br/>950 records"]
    FL -->|"570 records"| CSV["CSV Writer"]
    FL -->|"380 records"| SQL["SQLite Writer"]
    FL -->|"380 records"| POLY["DatabaseRouter"]
    CSV --> DIR["data/ Directory"]
    SQL --> DB["mist_data.db"]
    POLY --> ARANGO["ArangoDB / Redis"]
```

> **PNG fallback**: If this diagram does not render, see [data-flow-sankey.png](data-flow-sankey.png).

## Version History Milestones

Key milestones in MistHelper's evolution.

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
timeline
    title MistHelper Evolution
    section Foundation
        2023 : Initial CLI tool
             : Basic CSV export
             : Menu system (20 ops)
    section Growth
        2024 Q1 : SQLite backend added
                : Hybrid PK strategy
                : Rate limiting
        2024 Q2 : WebSocket commands
                : Packet captures
                : SSH Runner
    section Maturity
        2024 Q3 : Container deployment
                : SSH server access
                : Session isolation
        2024 Q4 : CI/CD pipeline
                : Auto-merge workflow
                : Web portal (Gunicorn)
    section Current
        2026 : 193 operations
             : 30-group menu reorg (issue #368)
             : SpecKit integration
             : Mermaid documentation suite
             : Polyglot backends (ArangoDB/Redis)
```

---

## Related Diagrams

- [Operations Reference](operations-reference.md) - Operation lifecycle and safety classifications
- [Data Pipeline](../core/data-pipeline.md) - Detailed data flow with error handling
- [Deployment Pipeline](../infrastructure/deployment-pipeline.md) - CI/CD timing context
