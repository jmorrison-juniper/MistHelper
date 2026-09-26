[<- Back to Diagram Index](../README.md) | [<- Back to Overview](overview.md)

# Infrastructure, Configuration, and API Fetching

These diagrams show the core, the configuration objects, and the utilities for API fetches.
The utility classes for API fetches are separate facades.
They do not form an inheritance chain in the current tree.

## Infrastructure and Configuration

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
        +check()
    }

    class EndpointConfig
    class ExportBackendOptions
    class SSHConnectionConfig
    class SSHExecutionConfig
    class AddressValidationConfig
    class DeviceFetchConfig
    class UtilityCommandsDeps
    class SsidTemplateDeps

    DataDirectoryChecker ..> EndpointConfig : reads configured paths
    SSHExecutionConfig ..> SSHConnectionConfig : uses connection values
    DeviceUtilityCommands ..> UtilityCommandsDeps : receives dependencies
    SSIDTemplateConsolidationManager ..> SsidTemplateDeps : receives dependencies
```

## API Fetch Utilities

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
        +all_sites_with_limit()
        +all_inventory_with_limit()
        +get_api_response_data()
    }

    class APITenantFetchUtils {
        +organization_tenants()
        +site_tenants()
        +service_policy_tenants()
        +gateway_template_tenants()
    }

    class APIFetchUtils {
        +organization_services()
        +all_site_settings()
        +gateway_device_configs()
    }

    class DeviceDataFetcher

    class RateLimitingUtils {
        +get_rate_limited_delay()
    }

    APICoreFetchUtils ..> RateLimitingUtils : delays API calls
    APITenantFetchUtils ..> APICoreFetchUtils : reuses paged fetches
    APIFetchUtils ..> APITenantFetchUtils : resolves tenant context
    DeviceDataFetcher ..> APICoreFetchUtils : fetches device rows
```

## Verified Module Paths

| Class | Module path |
|-------|-------------|
| `DataDirectoryChecker` | `src/refactors/data_directory_checker.py` |
| `EndpointConfig` | `src/dataclasses/endpoint_config.py` |
| `SSHConnectionConfig` | `src/ssh/ssh_runner.py` |
| `SSHExecutionConfig` | `src/ssh/ssh_runner.py` |
| `APICoreFetchUtils` | `src/api/api_core_fetch_utils.py` |
| `APITenantFetchUtils` | `src/api/tenant_fetch.py` |
| `APIFetchUtils` | `src/api/api_fetch_utils.py` |
| `DeviceDataFetcher` | `src/refactors/device_data_fetcher.py` and `src/gateway/overrides/device_data_fetcher.py` |

## Siblings

- [Exporters](exporters.md) - Class families for data export
- [Managers](managers.md) - Manager classes
- [Utilities](utilities.md) - Utility classes and data processing classes
