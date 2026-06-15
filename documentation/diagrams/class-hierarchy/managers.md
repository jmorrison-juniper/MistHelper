# Manager Classes

[<- Back to Diagram Index](../README.md) | [<- Back to Overview](overview.md)

The 28+ manager classes handle advanced operations: firmware upgrades, SSH execution, packet captures, WebSocket commands, maps, virtual chassis, and WAN migration.

## WebSocket & Network Managers

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
        +send_command()
        +receive_response()
        +close()
    }

    class ArpDeviceExecutor {
        +execute()
    }

    class PingDeviceExecutor {
        +execute()
    }

    class MacTableCommand {
        +show_mac_table()
    }

    class ServicePingManager {
        +ping_service()
        +check_connectivity()
    }

    class PacketCaptureManager {
        +start_capture()
        +stop_capture()
        +download_pcap()
        +site_level_capture()
        +org_level_capture()
    }

    WebSocketManager <|-- ArpDeviceExecutor
    WebSocketManager <|-- PingDeviceExecutor
    WebSocketManager <|-- MacTableCommand
    WebSocketManager --> ServicePingManager : delegates
    WebSocketManager --> PacketCaptureManager : triggers
```

## SSH & Device Managers

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
        +connect()
        +execute_command()
        +execute_batch()
        +close()
    }

    class SSHRunnerManager {
        +run_commands_on_devices()
        +load_commands_csv()
        +save_per_host_logs()
    }

    class CLIShellManager {
        +open_shell()
        +send_command()
        +read_output()
    }

    class ARPCommandManager {
        +collect_arp_tables()
        +parse_arp_output()
    }

    class FirmwareManager {
        +check_firmware_upgrade_status()
        +execute_firmware_upgrade_with_mode_selection()
    }

    class BulkAPFirmwareUpgrader {
        +execute()
    }

    class BulkSwitchFirmwareUpgrader {
        +execute()
    }

    class VirtualChassisManager {
        +convert_to_vc()
        +validate_members()
        +monitor_conversion()
    }

    SSHRunnerManager --> EnhancedSSHRunner : creates
    EnhancedSSHRunner --> CLIShellManager : uses
    SSHRunnerManager --> ARPCommandManager : delegates
    FirmwareManager --> BulkAPFirmwareUpgrader : delegates
    FirmwareManager --> BulkSwitchFirmwareUpgrader : delegates
    FirmwareManager --> VirtualChassisManager : coordinates
```

## Maps & WAN Managers

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
        +launch_viewer()
        +load_site_maps()
        +render_floor_plan()
    }

    class WAN2MigrationManager {
        +migrate_site()
        +validate_config()
        +rollback()
    }

    class WANProbeConfigManager {
        +configure_probes()
        +validate_targets()
    }

    class DataCollectionManager {
        +collect_all_data()
        +schedule_collection()
    }

    MapsManager --> DataCollectionManager : uses
    WAN2MigrationManager --> WANProbeConfigManager : configures
```

## Siblings

- [Infrastructure](infrastructure.md) - Core and API fetching classes
- [Exporters](exporters.md) - Data export class families
- [Utilities](utilities.md) - Utility and data processing classes
