[<- Back to Diagram Index](../README.md)

# Metrics and Analytics

Operation distribution, rate limiting behavior, data flow volumes, and version history.

## Operation Category Distribution

How MistHelper's 159 operations break down by safety classification.

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
pie title Operation Safety Classification (159 total)
    "Destructive (50)" : 50
    "Interactive (21)" : 21
    "Safe (18)" : 18
    "WebSocket (18)" : 18
    "Interactive Safe (15)" : 15
    "Resource Intensive (3)" : 3
    "WIP (3)" : 3
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
quadrantChart
    title Operation Complexity vs Usage Frequency
    x-axis Low Frequency --> High Frequency
    y-axis Low Complexity --> High Complexity
    quadrant-1 Complex & Frequent
    quadrant-2 Complex & Rare
    quadrant-3 Simple & Rare
    quadrant-4 Simple & Frequent
    Device Inventory: [0.9, 0.2]
    Site Listing: [0.85, 0.15]
    Alarm Events: [0.7, 0.3]
    Device Stats: [0.75, 0.35]
    Client Export: [0.6, 0.4]
    Packet Capture: [0.3, 0.7]
    WebSocket Diag: [0.4, 0.6]
    AP Firmware: [0.15, 0.85]
    VC Conversion: [0.05, 0.95]
    SSH Runner: [0.25, 0.75]
    Full Site Config: [0.1, 0.8]
    License Summary: [0.5, 0.2]
```

## Rate Limiting Adaptive Delay

How MistHelper's PID-like controller adjusts API request delay over time.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'xyChart': {
    'titleColor': '#E20074',
    'xAxisLabelColor': '#E0E0E0',
    'yAxisLabelColor': '#E0E0E0',
    'xAxisLineColor': '#FF4DA6',
    'yAxisLineColor': '#FF4DA6',
    'plotColorPalette': '#E20074,#FF6F91,#99004D,#00C853,#FFD600'
  }
}}}%%
xychart-beta
    title "Adaptive Delay Response to 429 Rate Limits"
    x-axis "Request Number" [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    y-axis "Delay (ms)" 0 --> 5000
    bar [100, 100, 100, 2000, 3500, 4500, 4000, 2500, 1500, 500, 200]
    line [100, 100, 100, 2000, 3500, 4500, 4000, 2500, 1500, 500, 200]
```

> **PNG fallback**: If the xychart-beta diagram does not render, see [metrics-xychart.png](metrics-xychart.png).

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
sankey-beta

API Calls,Pagination Handler,1000
Pagination Handler,Rate Limiter,1000
Rate Limiter,JSON Parser,950
Rate Limiter,Rate Limited (429),50
Rate Limited (429),Rate Limiter,50
JSON Parser,Flattener,950
Flattener,CSV Writer,570
Flattener,SQLite Writer,380
CSV Writer,data/ Directory,570
SQLite Writer,mist_data.db,380
```

> **PNG fallback**: If the sankey-beta diagram does not render, see [data-flow-sankey.png](data-flow-sankey.png).

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
        2025 : 159 operations
             : SpecKit integration
             : Mermaid documentation suite
```

---

## Related Diagrams

- [Operations Reference](operations-reference.md) - Operation lifecycle and safety classifications
- [Data Pipeline](../core/data-pipeline.md) - Detailed data flow with error handling
- [Deployment Pipeline](../infrastructure/deployment-pipeline.md) - CI/CD timing context
