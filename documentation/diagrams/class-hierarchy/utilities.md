[<- Back to Diagram Index](../README.md) | [<- Back to Overview](overview.md)

# Utility & Data Processing Classes

23+ utility classes organized by responsibility, plus the data processing chain that transforms raw API responses into exportable records.

## Utility Classes by Responsibility

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
        +format_timestamp()
        +parse_epoch()
        +duration_human()
    }
    class InputUtils {
        +safe_input()
        +validate_selection()
    }
    class CacheUtils {
        +get_cached()
        +set_cached()
        +invalidate()
    }
    class DisplayUtils {
        +print_table()
        +progress_bar()
        +color_output()
    }
    class FilePathUtils {
        +ensure_data_dir()
        +sanitize_filename()
    }
    class EnvironmentUtils {
        +load_env()
        +get_config()
        +is_container()
    }
    class ValidationUtils {
        +validate_hostname()
        +validate_mac()
        +validate_uuid()
    }
    class ConfigUtils {
        +load_config()
        +merge_defaults()
    }

    InputUtils --> ValidationUtils : validates input
    FilePathUtils --> EnvironmentUtils : checks env
    DisplayUtils --> TimeUtils : formats times
    ConfigUtils --> EnvironmentUtils : reads env
```

## Prompt & Interactive Utilities

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
        +prompt_for_site()
        +prompt_for_device()
    }
    class PromptNetworkDeviceUtils {
        +prompt_switch_selection()
        +prompt_ap_selection()
    }
    class PromptClientUtils {
        +prompt_client_selection()
    }
    class InteractiveDisplayUtils {
        +display_menu()
        +display_results()
    }
    class DeviceUtilityCommands {
        +get_device_info()
    }
    class DeviceUtils {
        +filter_by_type()
        +enrich_device_data()
    }
    class TroubleshootUtils {
        +diagnose_connectivity()
    }
    class InsightMetricsUtils {
        +fetch_insights()
        +format_metrics()
    }

    PromptUtils <|-- PromptNetworkDeviceUtils
    PromptUtils <|-- PromptClientUtils
    InteractiveDisplayUtils --> PromptUtils : uses
    DeviceUtilityCommands --> DeviceUtils : delegates
```

## Data Processing Chain

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

    class DataProcessingUtils {
        +flatten_dict()
        +sanitize_for_csv()
        +normalize_keys()
    }

    class MarvisDataUtils {
        +process_marvis_actions()
        +parse_marvis_response()
    }

    class DatabaseSchemaUtils {
        +infer_schema()
        +create_table()
        +alter_table()
    }

    class SQLiteDatabaseWriter {
        +upsert_records()
        +execute_query()
        +get_connection()
    }

    class RateLimitingUtils {
        +check_rate_limit()
        +adaptive_delay()
        +update_metrics()
    }

    class RoutingUtils {
        +parse_route_table()
    }

    class AddressUtils {
        +normalize_address()
        +fuzzy_match()
    }

    class NameNormalizationUtils {
        +normalize_site_name()
        +clean_device_name()
    }

    DataProcessingUtils --> DatabaseSchemaUtils : schema inference
    DatabaseSchemaUtils --> SQLiteDatabaseWriter : creates tables
    DataProcessingUtils --> NameNormalizationUtils : normalizes
    DataProcessingUtils --> AddressUtils : normalizes addresses
```

## Siblings

- [Infrastructure](infrastructure.md) - Core and API fetching classes
- [Exporters](exporters.md) - Data export class families
- [Managers](managers.md) - Manager classes (firmware, SSH, WebSocket)
