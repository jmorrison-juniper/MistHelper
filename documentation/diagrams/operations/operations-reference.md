[<- Back to Diagram Index](../README.md)

# Operations Reference

Operation lifecycle, NOC engineer user journey, and destructive operation safety requirements.

## Operation Lifecycle

How an operation moves through states from selection to completion.

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
stateDiagram-v2
    [*] --> Idle : Menu displayed

    Idle --> Validating : User selects operation
    Validating --> Running : Input validated
    Validating --> Idle : Invalid input

    Running --> RateLimited : 429 response
    Running --> Retrying : 5xx / network error
    Running --> Completed : All pages fetched
    Running --> Failed : Max retries exceeded

    RateLimited --> Running : After adaptive delay
    Retrying --> Running : Exponential backoff
    Retrying --> Failed : Max retries exceeded

    Completed --> Exporting : Data ready
    Exporting --> [*] : CSV/SQLite/polyglot written

    Failed --> [*] : Error logged

    state Running {
        [*] --> Fetching
        Fetching --> Processing : Page received
        Processing --> Fetching : More pages
        Processing --> [*] : Last page
    }
```

## NOC Engineer Journey

A typical day for a junior NOC engineer using MistHelper.

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
journey
    title NOC Engineer Daily Workflow with MistHelper
    section Morning Check
        SSH into MistHelper: 5: NOC Engineer
        Export device inventory: 4: NOC Engineer
        Check offline devices: 4: NOC Engineer
        Review alarm events: 3: NOC Engineer
    section Investigation
        Search device events: 4: NOC Engineer
        Run WebSocket diagnostics: 3: NOC Engineer
        Capture packets on switch: 3: NOC Engineer
    section Maintenance
        Review firmware versions: 4: NOC Engineer
        Schedule AP firmware upgrade: 2: NOC Engineer
        Confirm upgrade with UPGRADE: 2: NOC Engineer
        Monitor upgrade progress: 3: NOC Engineer
    section Reporting
        Export data to CSV: 5: NOC Engineer
        Query SQLite database: 4: NOC Engineer
```

## Destructive Operation Safety Requirements

Requirements that MUST be met before any destructive operation (Menu 90-100) executes.

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
    subgraph requirements["Safety Requirements - Menu 90-100"]
        SAF001["SAF-001: Explicit Confirmation<br/>Type exact word to proceed<br/>Risk: HIGH | Verify: test"]
        SAF002["SAF-002: EOF Handling<br/>All input calls handle EOFError<br/>Risk: HIGH | Verify: inspection"]
        SAF003["SAF-003: No Blind Automation<br/>--menu flag requires confirmation<br/>Risk: HIGH | Verify: test"]
        SAF004["SAF-004: Logging Required<br/>Full context logged before execution<br/>Risk: MEDIUM | Verify: inspection"]
        SAF005["SAF-005: Rollback Plan<br/>Firmware upgrades document rollback<br/>Risk: MEDIUM | Verify: inspection"]
    end

    subgraph impl["Implementation"]
        si["safe_input()<br/>MistHelper.py"]
        fm["FirmwareManager<br/>MistHelper.py"]
    end

    si -->|satisfies| SAF001
    si -->|satisfies| SAF002
    fm -->|satisfies| SAF004
    fm -->|satisfies| SAF005
```

---

## Related Diagrams

- [Data Pipeline](../core/data-pipeline.md) - Detailed trace of the running state internals
- [Architecture Overview](../core/architecture-overview.md) - Where operations fit in the system
- [Metrics and Analytics](metrics-and-analytics.md) - Operation category distribution
- [Class Hierarchy: Managers](../class-hierarchy/managers.md) - Manager classes that implement operations
