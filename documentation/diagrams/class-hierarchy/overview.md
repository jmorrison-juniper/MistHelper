[<- Back to Diagram Index](../README.md)

# Class Hierarchy Overview

Top-level view of MistHelper's 99+ classes organized into 12 families with inter-family dependencies.

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
classDiagram
    direction LR

    class InfrastructureCore["Infrastructure & Core (2)"] {
        DataDirectoryChecker
        PerformanceMonitor
    }

    class ConfigObjects["Configuration Objects (6)"] {
        SSHConnectionConfig
        SSHExecutionConfig
        AddressValidationConfig
        MapViewerConfig
        DeviceFetchConfig
        EndpointConfig
    }

    class Utilities["Utility Classes (23+)"] {
        TimeUtils, InputUtils
        CacheUtils, DisplayUtils
        ValidationUtils, ...
    }

    class APIFetching["API Fetching (4)"] {
        APICoreFetchUtils
        APITenantFetchUtils
        APIFetchUtils
        DeviceDataFetcher
    }

    class DataProcessing["Data Processing (8)"] {
        DataExporter
        SQLiteDatabaseWriter
        DataProcessingUtils
        SFPTransceiverDataProcessor
    }

    class OrgExporters["Org Exporters (10)"] {
        OrgSiteExporter
        OrgInventoryExporter
        OrgDeviceStatsExporter
        OrgTemplateExporter
    }

    class SiteExporters["Site Exporters (5)"] {
        SiteDeviceExporter
        SiteClientExporter
        SiteConfigExporter
    }

    class GatewayExporters["Gateway Exporters (4)"] {
        GatewayTestExporter
        GatewayStatsExporter
        MSPInventoryExporter
    }

    class WebSocketNet["WebSocket & Network (5)"] {
        WebSocketManager
        WebSocketCommands
        ServicePingManager
    }

    class Managers["Managers (28+)"] {
        FirmwareManager
        PacketCaptureManager
        EnhancedSSHRunner
        MapsManager
    }

    class UITUI["UI / TUI (2)"] {
        MistHelperTUI
    }

    class SystemRegistry["System / Registry (2)"] {
        OperationRegistry
        TelemetryEmitter
    }

    InfrastructureCore --> Utilities : provides base services
    ConfigObjects --> Managers : configures
    ConfigObjects --> WebSocketNet : configures
    Utilities --> APIFetching : used by
    APIFetching --> DataProcessing : feeds data
    DataProcessing --> OrgExporters : write methods
    DataProcessing --> SiteExporters : write methods
    DataProcessing --> GatewayExporters : write methods
    WebSocketNet --> Managers : real-time commands
    SystemRegistry --> Managers : dispatches to
    SystemRegistry --> OrgExporters : dispatches to
    SystemRegistry --> SiteExporters : dispatches to
    UITUI --> SystemRegistry : user input
```

## Family Sub-Diagrams

| Family | Classes | Details |
|--------|---------|---------|
| [Infrastructure](infrastructure.md) | Infrastructure, Configuration, API Fetching | Core services, config objects, API chain |
| [Exporters](exporters.md) | Org, Site, Gateway Exporters | All data export classes |
| [Managers](managers.md) | Managers & Advanced (28+) | Firmware, SSH, WebSocket, captures |
| [Utilities](utilities.md) | Utilities & Data Processing (31+) | Helper classes and data transform |

---

## Related Diagrams

- [Architecture Overview](../core/architecture-overview.md) - System-level subsystem map
- [Operations Reference](../operations/operations-reference.md) - How operations use these classes
- [Data Pipeline](../core/data-pipeline.md) - Data flow through the class chain
