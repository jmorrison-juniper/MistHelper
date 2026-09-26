[<- Back to Diagram Index](../README.md) | [<- Back to Overview](overview.md)

# Manager Classes

The current tree has 40 classes with names that end in `Manager`.
The diagrams below show the main manager families.
They also show the cluster-forwarding pattern where it matters.

## WebSocket and Packet Capture Managers

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

    class WebSocketManager {
        +connect()
        +connect_and_subscribe()
        +subscribe_to_channel()
        +wait_for_command_result()
        +disconnect()
    }
    class ServicePingDiscoveryMixin
    class ServicePingManager {
        +execute()
    }
    class ArpDeviceExecutor {
        +execute()
    }
    class PingDeviceExecutor {
        +execute()
    }
    class MacTableCommand {
        +execute()
    }
    class PacketCaptureManager {
        +validate_mac_address()
        +normalize_mac_address()
        +start_site_packet_capture()
        +start_org_packet_capture()
    }
    class PacketCaptureDownloadManager {
        +fetch_completed_pcaps()
        +download_pending_pcaps()
        +poll_and_download_pcap()
    }
    class PacketCaptureExec
    class PacketCaptureOrg
    class PacketCapturePrompts
    class PacketCaptureTcpdump

    ServicePingDiscoveryMixin <|-- ServicePingManager
    ArpDeviceExecutor ..> WebSocketManager : sends commands
    PingDeviceExecutor ..> WebSocketManager : sends commands
    MacTableCommand ..> WebSocketManager : sends commands
    PacketCaptureManager *-- WebSocketManager : owns one manager
    PacketCaptureManager *-- PacketCaptureDownloadManager : owns one downloader
    PacketCaptureManager *-- PacketCaptureExec : owns executor helpers
    PacketCaptureManager *-- PacketCaptureOrg : owns org helpers
    PacketCaptureManager *-- PacketCapturePrompts : owns prompt helpers
    PacketCaptureManager *-- PacketCaptureTcpdump : owns tcpdump helpers
```

## SSH, Device, and Firmware Managers

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

    class EnhancedSSHRunner {
        +sanitize_filename()
    }
    class SSHRunnerManager {
        +interactive()
        +by_gateway_template()
    }
    class CLIShellManager {
        +launch()
    }
    class BatchExecutor {
        +run()
    }
    class HostRunner {
        +run()
    }
    class MultiHostRunner {
        +run()
    }
    class ARPCommandManager {
        +execute()
    }
    class DeviceRebootManager {
        +by_gateway_template_list()
    }
    class VirtualChassisManager {
        +launch_convert_single()
        +convert_single()
        +check_status()
    }
    class FirmwareManager {
        +check_firmware_upgrade_status()
        +execute_firmware_upgrade_with_mode_selection()
        +execute_switch_firmware_upgrade_with_mode_selection()
    }
    class BulkAPFirmwareUpgrader {
        +execute()
    }
    class BulkSwitchFirmwareUpgrader {
        +execute()
    }
    class OrgLevelAPFirmwareUpgrader {
        +run()
        +execute()
    }

    SSHRunnerManager ..> EnhancedSSHRunner : starts SSH flows
    CLIShellManager ..> EnhancedSSHRunner : launches shell
    BatchExecutor ..> HostRunner : runs one host
    MultiHostRunner ..> HostRunner : runs many hosts
    FirmwareManager ..> BulkAPFirmwareUpgrader : starts AP upgrades
    FirmwareManager ..> BulkSwitchFirmwareUpgrader : starts switch upgrades
    FirmwareManager ..> OrgLevelAPFirmwareUpgrader : starts org AP upgrades
    VirtualChassisManager ..> EnhancedSSHRunner : uses SSH utilities
```

## Map, Gateway, Site, and Org Managers

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

    class MapsManager {
        +select_site()
        +get_current_site()
        +run_interactive_menu()
        +export_site_maps()
        +export_all_site_maps()
    }
    class PlotlyMapCallbackManager {
        +apply_layer_toggles()
        +build_click_details()
    }
    class DashTemplateManager {
        +get_custom_css()
        +get_html_template()
        +validate_template()
    }
    class WAN2MigrationManager {
        +set_site_variable()
    }
    class WANProbeConfigManager {
        +configure()
    }
    class WANProbeDeviceOverrideManager {
        +configure()
    }
    class DeviceConfigTemplateClonerManager {
        +clone()
    }
    class APProfileMigrationManager {
        +migrate_aps_between_device_profiles()
        +revert_ap_profile_migration()
    }
    class SiteConfigManager {
        +create_test_sites_from_csv()
        +create_country_rf_templates_and_assign()
        +create_ap_model_device_profiles()
    }
    class OrgConfigMigrationManager {
        +export_config()
        +import_config()
    }
    class OrgTicketManager {
        +list_tickets()
        +create_ticket()
        +update_ticket()
        +view_ticket()
    }

    MapsManager ..> PlotlyMapCallbackManager : supports viewer callbacks
    MapsManager ..> DashTemplateManager : uses Dash templates
    WAN2MigrationManager ..> WANProbeConfigManager : applies probe settings
    WANProbeDeviceOverrideManager ..> GatewayExportUtils : reads gateway data
    DeviceConfigTemplateClonerManager ..> GatewayExportUtils : reads templates
    APProfileMigrationManager ..> SiteConfigManager : changes site profiles
    OrgConfigMigrationManager ..> OrgTicketManager : shares org context
```

## Siblings

- [Infrastructure](infrastructure.md) - Core and API fetching classes
- [Exporters](exporters.md) - Data export class families
- [Utilities](utilities.md) - Utility and data processing classes
