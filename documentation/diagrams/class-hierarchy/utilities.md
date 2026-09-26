[<- Back to Diagram Index](../README.md) | [<- Back to Overview](overview.md)

# Utility and Data Processing Classes

The current tree has 31 classes with names that end in `Utils`.
Several large utility classes use helper clusters and `__getattr__`.
That pattern keeps the public surface stable without wrapper methods.

## Core Utility Classes

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

    class TimeUtils {
        +get_dynamic_lookback_hours()
        +log_dynamic_lookback()
    }
    class InputUtils {
        +ensure_tqdm_available()
        +safe_input()
        +prompt_msp_id()
    }
    class CacheUtils {
        +check_and_generate_csv()
        +load_csv_grouped_by_key()
        +clear_cache()
        +fast_cache_hit()
    }
    class DisplayUtils {
        +dict_list_as_pretty_table()
        +create_progress_bar()
    }
    class FilePathUtils {
        +get_csv_path()
        +create_csv_template()
    }
    class EnvironmentUtils {
        +is_running_in_container()
    }
    class ValidationUtils {
        +validate_site_id()
        +validate_device_id()
        +validate_ping_target()
    }
    class ConfigUtils {
        +set_apisession()
        +get_cached_org_id()
        +get_cached_or_prompted_org_id()
        +check_stop_signal()
    }

    ConfigUtils ..> InputUtils : prompts for org
    FilePathUtils ..> EnvironmentUtils : checks runtime
    DisplayUtils ..> TimeUtils : formats progress
    ValidationUtils ..> InputUtils : validates input
```

## Prompt, Device, and Cluster-Forwarding Utilities

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

    class PromptUtils {
        +select_device_id_from_inventory()
        +select_site_id_from_csv()
        +select_site()
        +select_site_with_logging()
    }
    class PromptNetworkDeviceUtils {
        +select_ap_mac()
        +select_gateway_mac()
        +select_switch_mac()
        +select_ports_from_device()
    }
    class PromptClientUtils {
        +select_client_mac()
        +select_client()
        +select_site_and_device_ids()
    }
    class InteractiveDisplayUtils {
        +site_inventory()
        +device_stats()
        +device_tests()
        +device_config()
    }
    class DeviceUtilityCommands {
        +__getattr__()
    }
    class _UtilityCommandsSelection
    class _UtilityCommandsWebsocket
    class _UtilityCommandsShow
    class _UtilityCommandsAction
    class _UtilityCommandsClear

    PromptNetworkDeviceUtils ..> PromptUtils : selects devices
    PromptClientUtils ..> PromptUtils : selects sites
    InteractiveDisplayUtils ..> PromptUtils : displays selections
    DeviceUtilityCommands *-- _UtilityCommandsSelection : forwards missing methods
    DeviceUtilityCommands *-- _UtilityCommandsWebsocket : forwards missing methods
    DeviceUtilityCommands *-- _UtilityCommandsShow : forwards missing methods
    DeviceUtilityCommands *-- _UtilityCommandsAction : forwards missing methods
    DeviceUtilityCommands *-- _UtilityCommandsClear : forwards missing methods
```

## Data Processing and Routing Utilities

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

    class DataProcessingUtils {
        +flatten_dict()
        +flatten_nested_fields()
        +convert_list_values_to_strings()
        +get_unique_keys()
    }
    class MarvisDataUtils {
        +format_for_csv()
    }
    class DatabaseSchemaUtils {
        +determine_api_function_name_from_context()
        +get_endpoint_strategy()
        +build_create_table_sql()
        +build_indexes_sql()
    }
    class SQLiteDatabaseWriter {
        +write()
    }
    class RoutingUtils {
        +execute_show_forwarding_table()
        +execute_show_ssr_routes()
        +__getattr__()
    }
    class AddressUtils {
        +normalize_zip()
        +enhanced_parse()
        +compare_with_threshold()
    }
    class NameNormalizationUtils {
        +normalize_business_name()
        +normalize_generic()
        +extract_tokens()
    }
    class InsightMetricsUtils {
        +export_const_insight_metrics()
        +get_by_scope()
        +parse_to_normalized_data()
    }
    class TroubleshootUtils {
        +client_connectivity()
        +device_performance()
        +network_connectivity()
        +launch_interactive()
    }

    DataProcessingUtils ..> DatabaseSchemaUtils : infers schema
    SQLiteDatabaseWriter ..> DatabaseSchemaUtils : writes tables
    MarvisDataUtils ..> DataProcessingUtils : formats rows
    AddressUtils ..> NameNormalizationUtils : compares names
    TroubleshootUtils ..> InsightMetricsUtils : reads insights
    RoutingUtils ..> WebSocketManager : sends route commands
```

## SSID Consolidation Cluster Pattern

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

    class SSIDTemplateConsolidationManager {
        +execute()
        +run_phase_menu()
        +__getattr__()
    }
    class _ClusterBase
    class _SsidTemplateCacheCluster
    class _SsidTemplatePhase1Cluster
    class _SsidTemplatePhase2Cluster
    class _SsidTemplatePhase3Cluster
    class _SsidTemplatePhase45Cluster

    _ClusterBase <|-- _SsidTemplateCacheCluster
    _ClusterBase <|-- _SsidTemplatePhase1Cluster
    _ClusterBase <|-- _SsidTemplatePhase2Cluster
    _ClusterBase <|-- _SsidTemplatePhase3Cluster
    _ClusterBase <|-- _SsidTemplatePhase45Cluster
    SSIDTemplateConsolidationManager *-- _SsidTemplateCacheCluster : forwards missing methods
    SSIDTemplateConsolidationManager *-- _SsidTemplatePhase1Cluster : forwards missing methods
    SSIDTemplateConsolidationManager *-- _SsidTemplatePhase2Cluster : forwards missing methods
    SSIDTemplateConsolidationManager *-- _SsidTemplatePhase3Cluster : forwards missing methods
    SSIDTemplateConsolidationManager *-- _SsidTemplatePhase45Cluster : forwards missing methods
```

## Siblings

- [Infrastructure](infrastructure.md) - Core and API fetching classes
- [Exporters](exporters.md) - Data export class families
- [Managers](managers.md) - Manager classes
