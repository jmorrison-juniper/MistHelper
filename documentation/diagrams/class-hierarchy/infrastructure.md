[<- Back to Diagram Index](../README.md) | [<- Back to Overview](overview.md)

# Infrastructure, Configuration & API Fetching

Core infrastructure classes, configuration dataclass objects, and the API fetching inheritance chain.

## Infrastructure & Core

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
    direction TB

    class DataDirectoryChecker {
        +ensure_data_directory()
        +validate_permissions()
    }

    class SSHConnectionConfig {
        +hostname: str
        +username: str
        +password: str
        +port: int
        +timeout: int
    }

    class SSHExecutionConfig {
        +commands: list
        +sudo: bool
        +output_dir: str
    }

    class AddressValidationConfig {
        +normalize: bool
        +fuzzy_threshold: float
    }

    class DeviceFetchConfig {
        +device_type: str
        +include_stats: bool
    }

    class EndpointConfig {
        +base_url: str
        +page_limit: int
        +timeout: int
    }
```

## API Fetching Chain

The API fetching classes form an inheritance chain, each layer adding specificity.

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
    direction TB

    class APICoreFetchUtils {
        +fetch_single_page()
        +handle_response()
        +parse_pagination()
    }

    class APITenantFetchUtils {
        +fetch_org_data()
        +fetch_site_data()
        +resolve_tenant_context()
    }

    class APIFetchUtils {
        +fetch_with_pagination()
        +fetch_all_pages()
        +build_endpoint_url()
    }

    class DeviceDataFetcher {
        +fetch_devices_by_type()
        +fetch_device_stats()
        +enrich_with_site_names()
    }

    APICoreFetchUtils <|-- APITenantFetchUtils : extends
    APITenantFetchUtils <|-- APIFetchUtils : extends
    APIFetchUtils <|-- DeviceDataFetcher : extends

    class RateLimitingUtils {
        +check_rate_limit()
        +adaptive_delay()
        +update_metrics()
    }

    APIFetchUtils --> RateLimitingUtils : uses
```

## Siblings

- [Exporters](exporters.md) - Data export class families
- [Managers](managers.md) - Manager classes (firmware, SSH, WebSocket)
- [Utilities](utilities.md) - Utility and data processing classes
