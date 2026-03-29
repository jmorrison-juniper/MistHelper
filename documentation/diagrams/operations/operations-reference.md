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
    Exporting --> [*] : CSV/SQLite written

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
requirementDiagram

    requirement explicit_confirmation {
        id: SAF-001
        text: Destructive operations require typing exact confirmation word
        risk: high
        verifymethod: test
    }

    requirement eof_handling {
        id: SAF-002
        text: All input calls handle EOFError for SSH session disconnects
        risk: high
        verifymethod: inspection
    }

    requirement no_automation {
        id: SAF-003
        text: Menu 90-100 cannot run via --menu flag without confirmation
        risk: high
        verifymethod: test
    }

    requirement logging_required {
        id: SAF-004
        text: All destructive actions logged with full context before execution
        risk: medium
        verifymethod: inspection
    }

    requirement rollback_plan {
        id: SAF-005
        text: Firmware upgrades document rollback procedures
        risk: medium
        verifymethod: inspection
    }

    element safe_input {
        type: function
        docRef: MistHelper.py
    }

    element FirmwareManager {
        type: class
        docRef: MistHelper.py
    }

    safe_input - satisfies -> explicit_confirmation
    safe_input - satisfies -> eof_handling
    FirmwareManager - satisfies -> logging_required
    FirmwareManager - satisfies -> rollback_plan
```

---

## Related Diagrams

- [Data Pipeline](../core/data-pipeline.md) - Detailed trace of the running state internals
- [Architecture Overview](../core/architecture-overview.md) - Where operations fit in the system
- [Metrics and Analytics](metrics-and-analytics.md) - Operation category distribution
- [Class Hierarchy: Managers](../class-hierarchy/managers.md) - Manager classes that implement operations
