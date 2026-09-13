[<- Back to Diagram Index](../README.md) | [<- Back to Overview](overview.md)

# Exporter Classes

Org-level, site-level, and gateway exporter families plus shared export utilities.

## Org-Level Exporters

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

    class DataExporter {
        +write_with_format_selection()
        +write_csv()
        +write_sqlite()
    }

    class OrgExportUtils {
        +get_org_context()
        +validate_org_id()
    }

    class OrgSiteExporter {
        +export_sites()
    }
    class OrgInventoryExporter {
        +export_inventory()
        +export_combined_weekly()
    }
    class OrgDeviceStatsExporter {
        +export_device_stats()
    }
    class OrgTemplateExporter {
        +export_ap_templates()
        +export_rf_templates()
        +export_network_templates()
    }
    class OrgAlarmEventExporter {
        +export_alarms()
        +export_device_events()
    }
    class OrgClientSecurityExporter {
        +export_client_events()
        +export_psks()
    }
    class OrgAdminExporter {
        +export_admins()
        +export_api_tokens()
    }
    class OrgConfigExporter {
        +export_wlans()
        +export_vlans()
    }
    class OfflineDeviceReporter {
        +find_offline_devices()
        +generate_report()
    }

    DataExporter <|-- OrgExportUtils
    OrgExportUtils <|-- OrgSiteExporter
    OrgExportUtils <|-- OrgInventoryExporter
    OrgExportUtils <|-- OrgDeviceStatsExporter
    OrgExportUtils <|-- OrgTemplateExporter
    OrgExportUtils <|-- OrgAlarmEventExporter
    OrgExportUtils <|-- OrgClientSecurityExporter
    OrgExportUtils <|-- OrgAdminExporter
    OrgExportUtils <|-- OrgConfigExporter
    OrgExportUtils <|-- OfflineDeviceReporter
```

## Site & Gateway Exporters

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

    class DataExporter {
        +write_with_format_selection()
    }

    class SiteExportUtils {
        +get_site_context()
    }
    class SiteDeviceExporter {
        +export_site_devices()
    }
    class SiteClientExporter {
        +export_wireless_clients()
        +export_wired_clients()
    }
    class SiteConfigExporter {
        +export_site_wlans()
    }
    class SiteAnomalyExporter {
        +export_anomalies()
    }

    class GatewayExportUtils {
        +get_gateway_context()
    }
    class GatewayTestExporter {
        +export_speed_tests()
    }
    class GatewayStatsExporter {
        +export_gateway_stats()
    }
    class MSPInventoryExporter {
        +export_msp_inventory()
    }

    class SFPTransceiverDataProcessor {
        +process_sfp_data()
        +normalize_transceiver_fields()
    }

    class ConstDefinitionsExporter {
        +export_const_definitions()
    }

    DataExporter <|-- SiteExportUtils
    SiteExportUtils <|-- SiteDeviceExporter
    SiteExportUtils <|-- SiteClientExporter
    SiteExportUtils <|-- SiteConfigExporter
    SiteExportUtils <|-- SiteAnomalyExporter

    DataExporter <|-- GatewayExportUtils
    GatewayExportUtils <|-- GatewayTestExporter
    GatewayExportUtils <|-- GatewayStatsExporter
    GatewayExportUtils <|-- MSPInventoryExporter

    DataExporter <|-- SFPTransceiverDataProcessor
    DataExporter <|-- ConstDefinitionsExporter
```

## Siblings

- [Infrastructure](infrastructure.md) - Core and API fetching classes
- [Managers](managers.md) - Manager classes (firmware, SSH, WebSocket)
- [Utilities](utilities.md) - Utility and data processing classes
