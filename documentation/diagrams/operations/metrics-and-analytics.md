[<- Back to Diagram Index](../README.md)

# Metrics and Analytics

Operation distribution, rate limiting behavior, data flow paths, and version history.

## Operation Category Distribution

How MistHelper's 270 registered menu entries break down by safety classification.

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
pie title Operation Safety Classification (270 entries, no menu 152)
    "Interactive Safe (93)" : 93
    "Safe (73)" : 73
    "Destructive (42)" : 42
    "Interactive (29)" : 29
    "WebSocket (22)" : 22
    "Resource Intensive (10)" : 10
    "Continuous Loop (1)" : 1
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
        fw["Firmware Upgrade"]
        vc["VC Conversion"]
        fsc["Upgrade Capture Portal"]
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

How the rate limiter adjusts API request delay when the Mist API returns 429.

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
        R1["Normal requests"]
        R2["Delay metrics update"]
    end

    subgraph spike["429 Rate Limit Hit"]
        R3["429 response"]
    end

    subgraph recovery["Recovery Phase"]
        R4["Backoff delay"]
        R5["Lower delay after recovery"]
    end

    R1 --> R2 --> R3 -->|"RateLimitingUtils<br/>backs off"| R4 -->|"Delay decreases<br/>after recovery"| R5
```

> **Beta diagram type**: this diagram uses `xychart-beta`. A viewer without beta
> support does not render it. Open this page on GitHub.

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
    API["API Calls"] --> PH["Pagination Handler"]
    PH --> RL["Rate Limiter"]
    RL -->|"OK"| JP["JSON Parser"]
    RL -->|"429 retry"| R429["Rate Limited"]
    R429 --> RL
    JP --> FL["Flattener"]
    FL --> CSV["CSV Writer"]
    FL --> SQL["SQLite Writer"]
    FL --> POLY["DatabaseRouter"]
    CSV --> DIR["data/ Directory"]
    SQL --> DB["mist_data.db"]
    POLY --> ARANGO["ArangoDB / Redis JSON / Redis TimeSeries"]
```

> **Beta diagram type**: this diagram uses `sankey-beta`. A viewer without beta
> support does not render it. Open this page on GitHub.

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
        2026 : 270 registered menu entries
             : No registered menu 152
             : SpecKit integration
             : Mermaid documentation suite
             : Polyglot backends (ArangoDB/Redis)
             : Metrics gateway on menu 241
```

---

## Related Diagrams

- [Operations Reference](operations-reference.md) - Operation lifecycle and safety classifications
- [Data Pipeline](../core/data-pipeline.md) - Detailed data flow with error handling
- [Deployment Pipeline](../infrastructure/deployment-pipeline.md) - CI/CD timing context
