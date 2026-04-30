# Issue bodies for monolith decomposition - batch creation script

# Run from MistHelper root:
# .venv\Scripts\python.exe scripts\create_decomposition_issues.py

import subprocess

OWNER = "jmorrison-juniper"
REPO = "MistHelper"
LABELS = "refactor,MistHelper.py"

issues = [
    {
        "title": "refactor: Systematic decomposition of MistHelper.py monolith (tracking issue)",
        "body_file": "scripts/issues/00-tracking.md",
    },
    {
        "title": "refactor: Extract MapsManager class (7,731 lines) to src/maps/maps_manager.py",
        "body": """## Extraction Target
**Class**: `MapsManager` (lines 36621-44351, 7,731 lines, 35 methods)
**Target**: `src/maps/maps_manager.py`

## Why Extract
- Largest class in the monolith (7,731 lines = 14% of the file)
- **0 external references** to the class name - completely self-contained
- Contains a single 5,242-line method (`_launch_plotly_viewer`) that is itself a candidate for further decomposition
- Only reached via menu dispatch lambda

## Call Sites (where MapsManager is instantiated/called)
- **Line 58779**: Menu dispatch lambda `MapsManager(...).start_org_packet_capture()` (approximate - verify exact menu entry)
- Internal method calls are all `self.*` within the class

## Dead Code Found Within
- `_launch_viewer_standalone()` (lines 44217-44351, 135 lines, 0 external calls)
- `_download_site_map_images()` (lines 37401-37485, 85 lines, 0 external calls)

## Dependencies to Check
- Uses `mistapi` SDK calls
- Uses `CacheUtils`, `DataExporter` from the monolith
- Uses `safe_input()` pattern
- Plotly/Matplotlib imports (conditional)

## Extraction Steps
1. Create `src/maps/__init__.py` and `src/maps/maps_manager.py`
2. Move entire `MapsManager` class (lines 36621-44351)
3. Add necessary imports at top of new module
4. In MistHelper.py: `from src.maps.maps_manager import MapsManager`
5. Update menu dispatch to use the import
6. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~7,731 lines from MistHelper.py (~14% reduction)
""",
    },
    {
        "title": "refactor: Extract EnhancedSSHRunner class (2,743 lines) to src/ssh/ssh_runner.py",
        "body": """## Extraction Target
**Class**: `EnhancedSSHRunner` (lines 60433-63175, 2,743 lines, 37 methods)
**Target**: `src/ssh/ssh_runner.py`

## Why Extract
- Second-largest standalone class (2,743 lines)
- 63 references but most are internal `self.*` calls
- SSH functionality is logically separate from Mist API operations
- Already near the end of the file, minimal entanglement

## Call Sites (external, outside the class definition)
- **Line 28334**: `EnhancedSSHRunner.run_ssh_commands_multi_host(...)` in SSHRunnerManager._collect_missing_data
- **Line 28367**: `EnhancedSSHRunner.run_application(MockArgs())` in SSHRunnerManager._execute_ssh
- **Line 28486**: `EnhancedSSHRunner.run_ssh_commands_multi_host(...)` in SSHRunnerManager._execute_by_template
- **Line 62534**: `EnhancedSSHRunner._run_multiple_ssh_commands_interactive(...)` in run_ssh_commands_multi_host
- **Line 62540**: `EnhancedSSHRunner._run_multiple_ssh_commands(...)` in run_ssh_commands_multi_host
- **Line 62920**: `EnhancedSSHRunner._run_ssh_command(...)` in run_application
- **Line 62931**: `EnhancedSSHRunner._run_multiple_ssh_commands(...)` in run_application
- **Line 62952**: `EnhancedSSHRunner.run_ssh_commands_multi_host(...)` in run_application
- **Line 63175**: `EnhancedSSHRunner._run_ssh_command(...)` in _interactive_mode

## Dead Code Found Within
- `_create_argument_parser()` (lines 62989-63094, 106 lines, 0 calls)
- `_run_ssh_command_on_host()` (lines 62449-62547, 99 lines, 0 calls)
- `_create_secure_log_file()` (lines 60899-60957, 59 lines, 0 calls)

## Dependencies to Check
- `paramiko` for SSH connections
- `SSHRunnerManager` class calls into EnhancedSSHRunner (must update those refs)
- `safe_input()` pattern
- `FilePathUtils` for path management
- Logging configuration

## Extraction Steps
1. Create `src/ssh/__init__.py` and `src/ssh/ssh_runner.py`
2. Move entire `EnhancedSSHRunner` class (lines 60433-63175)
3. Add necessary imports (paramiko, logging, os, pathlib, etc.)
4. In MistHelper.py: `from src.ssh.ssh_runner import EnhancedSSHRunner`
5. Verify all 9 external call sites still resolve
6. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~2,743 lines from MistHelper.py (~5% reduction)
""",
    },
    {
        "title": "refactor: Extract PacketCaptureManager class (2,621 lines) to src/capture/packet_capture.py",
        "body": """## Extraction Target
**Class**: `PacketCaptureManager` (lines 5972-8592, 2,621 lines, 23 methods)
**Target**: `src/capture/packet_capture.py`

## Why Extract
- Large self-contained class with clear domain boundary (packet captures)
- Only 6 external references
- Complex WebSocket and capture logic that benefits from isolation

## Call Sites (external)
- **Line 58779**: Menu dispatch - `PacketCaptureManager(...).start_org_packet_capture()`
- **Line 6229**: `self._start_site_client_capture_wireless()` (internal)
- **Line 6233**: `self._start_site_gateway_capture()` (internal)
- **Line 6239**: `self._start_site_scan_capture()` (internal)
- **Line 6909**: `self._start_site_scan_capture_all_aps(site_id)` (internal)
- **Line 7280/7342**: `self._wait_and_download_pcap(...)` (internal)
- **Line 8072**: `self._wait_and_download_pcap_org(...)` (internal)

## Dead Code Found Within
- `_wait_for_capture_completion()` (lines 7586-7678, 93 lines, 0 external calls)

## Dependencies to Check
- `WebSocketManager` (used for capture streaming)
- `ValidationUtils.validate_mac_address`
- `mistapi` SDK capture API calls
- `safe_input()` pattern
- `CacheUtils`, `DataExporter`

## Extraction Steps
1. Create `src/capture/__init__.py` and `src/capture/packet_capture.py`
2. Move entire `PacketCaptureManager` class (lines 5972-8592)
3. In MistHelper.py: `from src.capture.packet_capture import PacketCaptureManager`
4. Update menu dispatch reference
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~2,621 lines from MistHelper.py (~4.8% reduction)
""",
    },
    {
        "title": "refactor: Extract FirmwareManager class (2,322 lines) to src/firmware/firmware_manager.py",
        "body": """## Extraction Target
**Class**: `FirmwareManager` (lines 44354-46675, 2,322 lines, 32 methods)
**Target**: `src/firmware/firmware_manager.py`

## Why Extract
- Large class managing firmware upgrade workflows
- Only 5 external references
- Part of a natural firmware module (alongside OrgLevelAPFirmwareUpgrader, BulkAPFirmwareUpgrader, etc.)

## Call Sites (external)
- Menu dispatch lambdas for firmware operations (menus 90, 99, 100)
- `check_firmware_upgrade_status()` - 2 call sites
- `execute_firmware_upgrade_with_mode_selection()` - 1 call site
- `execute_ssr_firmware_upgrade_with_mode_selection()` - 1 call site
- `execute_switch_firmware_upgrade_with_mode_selection()` - 1 call site

## Dead Code Found Within
- `_select_msp_for_upgrade()` (lines 45700-45703, 4 lines, 0 calls)

## Dependencies to Check
- `mistapi` firmware upgrade APIs
- `CacheUtils` for template CSV caching
- `DataExporter` for result export
- `safe_input()` for destructive operation confirmation
- Shared with other firmware classes (OrgLevelAPFirmwareUpgrader, etc.)

## Extraction Steps
1. Create `src/firmware/__init__.py` and `src/firmware/firmware_manager.py`
2. Move entire `FirmwareManager` class (lines 44354-46675)
3. In MistHelper.py: `from src.firmware.firmware_manager import FirmwareManager`
4. Update all menu dispatch references
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~2,322 lines from MistHelper.py (~4.2% reduction)
""",
    },
    {
        "title": "refactor: Extract MistHelperTUI class (2,088 lines) to src/ui/tui.py",
        "body": """## Extraction Target
**Class**: `MistHelperTUI` (lines 54883-56970, 2,088 lines, 19 methods)
**Target**: `src/ui/tui.py`

## Why Extract
- Large TUI class with Rich library dependencies
- Only 2 external references (TUILauncher.launch at lines 59306, 59325)
- UI code is logically separate from business logic
- src/ui/ directory already exists

## Call Sites (external)
- **Line 59306**: `TUILauncher.launch()` -> creates MistHelperTUI instance
- **Line 59325**: `TUILauncher.launch()` -> creates MistHelperTUI instance
- **Line 56887/56918**: Internal - `self.create_layout()` in run()
- **Line 56898**: Internal - `self.check_keyboard_input()` in run()
- **Line 56904**: Internal - `self.handle_input(key)` in run()

## Dead Code Found Within
- `execute_current_item()` (lines 56637-56850, 214 lines, 0 external calls)

## Dependencies to Check
- `rich` library (Console, Layout, Panel, Table, etc.)
- `TUILauncher` class references MistHelperTUI
- `_load_dotenv_only()` loads environment
- Menu system integration
- `safe_input()` pattern

## Extraction Steps
1. Create `src/ui/tui.py` (src/ui/ already exists)
2. Move entire `MistHelperTUI` class (lines 54883-56970)
3. In MistHelper.py: `from src.ui.tui import MistHelperTUI`
4. Update TUILauncher references
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~2,088 lines from MistHelper.py (~3.8% reduction)
""",
    },
    {
        "title": "refactor: Extract OrgLevelAPFirmwareUpgrader class (1,854 lines) to src/firmware/org_ap_upgrader.py",
        "body": """## Extraction Target
**Class**: `OrgLevelAPFirmwareUpgrader` (lines 50896-52749, 1,854 lines, 66 methods)
**Target**: `src/firmware/org_ap_upgrader.py`

## Why Extract
- 1,854 lines with 66 methods dedicated to org-level AP firmware upgrades
- Only 11 references, most are internal self.* calls
- Natural fit in src/firmware/ alongside FirmwareManager

## Call Sites (external)
- Menu dispatch via `execute()` method (called 33 times internally via step methods)
- `run()` method - 23 internal calls (step orchestration)
- `_execute_msp_mode()` - called from line 50988

## Dependencies to Check
- `mistapi` firmware APIs
- `FirmwareManager` (sibling class)
- `safe_input()` for destructive confirmations
- `CacheUtils`, `DataExporter`
- Site/device selection utilities

## Extraction Steps
1. Create `src/firmware/org_ap_upgrader.py`
2. Move entire `OrgLevelAPFirmwareUpgrader` class (lines 50896-52749)
3. In MistHelper.py: `from src.firmware.org_ap_upgrader import OrgLevelAPFirmwareUpgrader`
4. Update menu dispatch and cross-references
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~1,854 lines from MistHelper.py (~3.4% reduction)
""",
    },
    {
        "title": "refactor: Extract BulkAPFirmwareUpgrader class (1,673 lines) to src/firmware/bulk_ap_upgrader.py",
        "body": """## Extraction Target
**Class**: `BulkAPFirmwareUpgrader` (lines 47583-49255, 1,673 lines, 72 methods)
**Target**: `src/firmware/bulk_ap_upgrader.py`

## Why Extract
- 1,673 lines with 72 methods for bulk AP firmware upgrades
- Only 2 external references - highly self-contained
- Natural fit in src/firmware/ module

## Call Sites (external)
- Menu dispatch via `execute()` method (called 33 times - mostly internal step flow)
- 2 class-level references

## Dead Code Found Within
- `_version_sort_key()` (lines 49052-49067, 16 lines, 0 calls)

## Dependencies to Check
- `mistapi` firmware APIs
- `FirmwareManager`, `FirmwareUpgradeStatusChecker` (sibling classes)
- `safe_input()` for destructive confirmations
- Site selection utilities

## Extraction Steps
1. Create `src/firmware/bulk_ap_upgrader.py`
2. Move entire `BulkAPFirmwareUpgrader` class (lines 47583-49255)
3. In MistHelper.py: `from src.firmware.bulk_ap_upgrader import BulkAPFirmwareUpgrader`
4. Update menu dispatch
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~1,673 lines from MistHelper.py (~3.1% reduction)
""",
    },
    {
        "title": "refactor: Extract RoutingUtils class (1,673 lines) to src/network/routing_utils.py",
        "body": """## Extraction Target
**Class**: `RoutingUtils` (lines 21184-22856, 1,673 lines, 40 methods)
**Target**: `src/network/routing_utils.py`

## Why Extract
- 1,673 lines dedicated to routing table parsing and display
- 40 methods with clear single responsibility
- Routing/forwarding table logic is independent of other operations

## Call Sites (external - 60 total references, many internal)
Key external callers:
- `execute_show_routing_table()` - 1 call from menu dispatch
- `execute_show_forwarding_table()` - 1 call from menu dispatch
- `execute_show_ssr_routes()` - 1 call from menu dispatch
- `_connect_websocket()` - 3 calls (internal)
- `_parse_routing_table()` - 4 calls (internal)
- `_display_routing_summary()` - 4 calls (internal)

## Dependencies to Check
- `WebSocketManager` for device command execution
- `PromptNetworkDeviceUtils` for device selection
- `mistapi` site device APIs
- JSON parsing utilities

## Extraction Steps
1. Create `src/network/__init__.py` and `src/network/routing_utils.py`
2. Move entire `RoutingUtils` class (lines 21184-22856)
3. In MistHelper.py: `from src.network.routing_utils import RoutingUtils`
4. Update menu dispatch references
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~1,673 lines from MistHelper.py (~3.1% reduction)

## Note
This class has 60 references but most are internal self.* calls. Careful dependency mapping needed for WebSocketManager interaction.
""",
    },
    {
        "title": "refactor: Extract SSIDTemplateConsolidationManager class (1,444 lines) to src/ssid_consolidation/",
        "body": """## Extraction Target
**Class**: `SSIDTemplateConsolidationManager` (lines 14102-15545, 1,444 lines, 70 methods)
**Target**: `src/ssid_consolidation/manager.py` (directory already exists)

## Why Extract
- 1,444 lines with 70 methods for SSID template consolidation
- Only 2 external references
- `src/ssid_consolidation/` directory already exists - natural home

## Call Sites (external)
- Menu dispatch via `execute()` method (called 33 times - internal step flow)
- 2 class-level references

## Dead Code Found Within (phase methods with 0 external calls)
- `phase1_audit()` (lines 14355-14367, 13 lines, 0 calls)
- `phase2_site_variables()` (lines 14735-14764, 30 lines, 0 calls)
- `phase3_site_groups()` (lines 14927-14953, 27 lines, 0 calls)
- `phase4_templates()` (lines 15112-15143, 32 lines, 0 calls)
- `phase5_disable_old()` (lines 15395-15424, 30 lines, 0 calls)
Note: These may be called via `run_phase_menu()` dispatch, not dead code.

## Dependencies to Check
- `mistapi` WLAN and template APIs
- `CacheUtils` for phase result caching
- `DataExporter` for CSV output
- `safe_input()` for confirmations

## Extraction Steps
1. Create `src/ssid_consolidation/manager.py`
2. Move entire `SSIDTemplateConsolidationManager` class (lines 14102-15545)
3. In MistHelper.py: `from src.ssid_consolidation.manager import SSIDTemplateConsolidationManager`
4. Update menu dispatch
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~1,444 lines from MistHelper.py (~2.6% reduction)
""",
    },
    {
        "title": "refactor: Extract WebSocket classes (~2,000 lines) to src/websocket/",
        "body": """## Extraction Target
**Three classes forming a cohesive WebSocket module:**
1. `WebSocketManager` (~800 lines) - core WebSocket connection management
2. `WebSocketCommands` (~500 lines) - device command execution via WebSocket
3. `WebSocketNetworkDiagCommands` (~700 lines) - network diagnostic commands

**Target**: `src/websocket/manager.py`, `src/websocket/commands.py`, `src/websocket/diag_commands.py`

## Why Extract
- ~2,000 lines of WebSocket-specific code
- Clear domain boundary (real-time device communication)
- Several methods with 0 external call sites (potential dead code)
- WebSocketCommands and WebSocketNetworkDiagCommands depend on WebSocketManager

## Dead Code Found Within
- `WebSocketNetworkDiagCommands.arp_device()` (361 lines, 0 external calls)
- `WebSocketNetworkDiagCommands.ping_device()` (245 lines, 0 external calls)
- `WebSocketCommands.show_mac_table()` (226 lines, 0 external calls)
Note: These may be called via menu dispatch indirection.

## Dependencies to Check
- `websocket-client` library
- `RoutingUtils` uses `WebSocketManager._connect_websocket`
- `PacketCaptureManager` uses WebSocket for capture streaming
- `mistapi` WebSocket APIs
- Thread management for async message handling

## Extraction Steps
1. Create `src/websocket/__init__.py`
2. Move `WebSocketManager` to `src/websocket/manager.py`
3. Move `WebSocketCommands` to `src/websocket/commands.py`
4. Move `WebSocketNetworkDiagCommands` to `src/websocket/diag_commands.py`
5. Update imports in MistHelper.py and cross-references
6. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~2,000 lines from MistHelper.py (~3.6% reduction)
""",
    },
    {
        "title": "refactor: Extract DeviceUtilityCommands class (~800 lines) to src/device/utility_commands.py",
        "body": """## Extraction Target
**Class**: `DeviceUtilityCommands` (~800 lines, ~25 methods)
**Target**: `src/device/utility_commands.py`

## Why Extract
- ~800 lines of device utility commands
- **Many methods with 0 external call sites** - highest concentration of potential dead code
- Each method is a standalone device operation reachable only via menu dispatch

## Dead Code Found Within (0 external calls)
- `clear_session()` (55 lines)
- `bounce_port()` (29 lines)
- `readopt_device()` (30 lines)
- `upload_support_file()` (32 lines)
- `clear_bgp_routes()` (32 lines)
- `monitor_traffic()` (27 lines)
- `clear_learned_macs()` (27 lines)
- `release_dhcp_lease()` (27 lines)
- `clear_policy_hit_count()` (25 lines)
- `get_config_commands()` (25 lines)
- `clear_arp_cache()` (25 lines)
- `show_ospf_neighbors()` (24 lines)
- `show_ospf_interfaces()` (24 lines)
- `show_ospf_database()` (24 lines)
- `show_ospf_summary()` (21 lines)
- `show_session()` (24 lines)
- `locate_device()` (24 lines)
- `show_service_path()` (21 lines)
- `show_dhcp_leases()` (21 lines)
- `clear_mac_table()` (21 lines)
- `clear_bpdu_error()` (22 lines)
- `traceroute()` (26 lines)

Note: These are likely called via WebSocket command menu dispatch, not truly dead.

## Dependencies to Check
- `WebSocketManager` for command execution
- `PromptNetworkDeviceUtils` for device selection
- `safe_input()` for confirmations
- `mistapi` device utility APIs

## Extraction Steps
1. Create `src/device/__init__.py` and `src/device/utility_commands.py`
2. Move entire `DeviceUtilityCommands` class
3. In MistHelper.py: `from src.device.utility_commands import DeviceUtilityCommands`
4. Update menu dispatch
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~800 lines from MistHelper.py (~1.5% reduction)
""",
    },
    {
        "title": "refactor: Extract GatewayTemplateConfigManager class (~700 lines) to src/gateway/template_config.py",
        "body": """## Extraction Target
**Class**: `GatewayTemplateConfigManager` (~700 lines, ~20 methods)
**Target**: `src/gateway/template_config.py`

## Why Extract
- ~700 lines managing gateway template configurations
- Several methods with 0 external call sites

## Dead Code Found Within
- `clone_by_location()` (56 lines, 0 calls)
- `apply()` (42 lines, 0 calls)
- `extract()` (28 lines, 0 calls)

## Call Sites (key external)
- `_select_template()` - 3 calls (lines 27507-27538)
- `_load_extraction_file()` - 1 call
- Menu dispatch for gateway template operations

## Dependencies to Check
- `mistapi` gateway template APIs
- `AddressUtils` for location parsing
- `safe_input()` for confirmations
- `DataExporter` for result export

## Extraction Steps
1. Create `src/gateway/__init__.py` and `src/gateway/template_config.py`
2. Move entire `GatewayTemplateConfigManager` class
3. In MistHelper.py: `from src.gateway.template_config import GatewayTemplateConfigManager`
4. Update menu dispatch and cross-references
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~700 lines from MistHelper.py (~1.3% reduction)
""",
    },
    {
        "title": "refactor: Extract SiteAutoUpgradeConfigurator class (~1,200 lines) to src/firmware/site_auto_upgrade.py",
        "body": """## Extraction Target
**Class**: `SiteAutoUpgradeConfigurator` (~1,200 lines, ~30 methods)
**Target**: `src/firmware/site_auto_upgrade.py`

## Why Extract
- ~1,200 lines managing site auto-upgrade configuration
- Natural fit in the firmware module family
- Has MSP mode functionality overlapping with OrgLevelAPFirmwareUpgrader

## Call Sites (external)
- `_execute_msp_mode()` - 2 calls (lines 49703, 50988)
- `_run()` - 2 calls
- `_step1_fetch_sites()` - 2 calls
- Menu dispatch via execute pattern

## Dependencies to Check
- `mistapi` firmware and site APIs
- `FirmwareManager` (sibling)
- `safe_input()` for confirmations
- Site selection utilities

## Extraction Steps
1. Create `src/firmware/site_auto_upgrade.py`
2. Move entire `SiteAutoUpgradeConfigurator` class
3. In MistHelper.py: `from src.firmware.site_auto_upgrade import SiteAutoUpgradeConfigurator`
4. Update menu dispatch and cross-references
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~1,200 lines from MistHelper.py (~2.2% reduction)
""",
    },
    {
        "title": "refactor: Extract VirtualChassisManager class (~600 lines) to src/device/virtual_chassis.py",
        "body": """## Extraction Target
**Class**: `VirtualChassisManager` (~600 lines, ~15 methods)
**Target**: `src/device/virtual_chassis.py`

## Why Extract
- ~600 lines dedicated to virtual chassis conversion operations
- Several methods with 0 external call sites
- Destructive operations (menus 94-96) benefit from isolation

## Dead Code Found Within
- `convert_by_site_list()` (54 lines, 0 calls)
- `check_status()` (35 lines, 0 calls)

## Call Sites (external)
- `convert_single()` - 1 call (menu dispatch)
- `_execute_bulk_conversion()` - 1 call
- Menu dispatch for VC operations

## Dependencies to Check
- `mistapi` device/switch APIs
- `safe_input()` for destructive confirmation ("CONVERT" pattern)
- Site/device selection utilities
- CSV file loading for site lists

## Extraction Steps
1. Create `src/device/virtual_chassis.py`
2. Move entire `VirtualChassisManager` class
3. In MistHelper.py: `from src.device.virtual_chassis import VirtualChassisManager`
4. Update menu dispatch
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~600 lines from MistHelper.py (~1.1% reduction)
""",
    },
    {
        "title": "refactor: Extract BulkSwitchFirmwareUpgrader class (~600 lines) to src/firmware/bulk_switch_upgrader.py",
        "body": """## Extraction Target
**Class**: `BulkSwitchFirmwareUpgrader` (~600 lines, ~20 methods)
**Target**: `src/firmware/bulk_switch_upgrader.py`

## Why Extract
- ~600 lines for bulk switch firmware upgrade operations
- Natural fit alongside other firmware classes in src/firmware/

## Call Sites (external)
- Menu dispatch via execute pattern
- `_fetch_switch_inventory()` - 1 call
- `_process_site()` - 1 call
- `_record_upgrade_result()` - 1 call

## Dependencies to Check
- `mistapi` firmware/switch APIs
- `FirmwareManager` (sibling)
- `safe_input()` for destructive confirmations
- Cache management for firmware data

## Extraction Steps
1. Create `src/firmware/bulk_switch_upgrader.py`
2. Move entire `BulkSwitchFirmwareUpgrader` class
3. In MistHelper.py: `from src.firmware.bulk_switch_upgrader import BulkSwitchFirmwareUpgrader`
4. Update menu dispatch
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~600 lines from MistHelper.py (~1.1% reduction)
""",
    },
    {
        "title": "refactor: Extract AddressUtils + NominatimValidator (~1,000 lines) to src/utils/address_utils.py",
        "body": """## Extraction Target
**Classes**: `AddressUtils` (~500 lines) + `NominatimValidator` (~500 lines)
**Target**: `src/utils/address_utils.py`

## Why Extract
- ~1,000 lines of address parsing and geocoding validation
- Self-contained domain logic with no Mist API dependencies
- `NominatimValidator` depends on `AddressUtils` - extract together
- Utility code that can be independently tested

## Call Sites (key external)
- `AddressUtils._parse_components()` - 2 calls (lines 29672, 29708)
- `AddressUtils.compare_with_threshold()` - 1 call
- `AddressUtils.enhanced_parse()` - 1 call
- `AddressUtils.check_should_skip()` - 1 call
- `AddressUtils.apply_business_context_rules()` - 1 call
- `NominatimValidator.validate()` - 1 call
- Used by `InventoryCSVComparator`

## Dependencies to Check
- No Mist API dependencies (pure utility)
- HTTP requests for Nominatim geocoding API
- `re`, `difflib` for string matching
- Used by `InventoryCSVComparator` (extract together or import)

## Extraction Steps
1. Create `src/utils/address_utils.py`
2. Move both `AddressUtils` and `NominatimValidator` classes
3. In MistHelper.py: `from src.utils.address_utils import AddressUtils, NominatimValidator`
4. Update all call sites
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~1,000 lines from MistHelper.py (~1.8% reduction)
""",
    },
    {
        "title": "refactor: Extract InventoryCSVComparator class (~800 lines) to src/inventory/csv_comparator.py",
        "body": """## Extraction Target
**Class**: `InventoryCSVComparator` (~800 lines)
**Target**: `src/inventory/csv_comparator.py`

## Why Extract
- ~800 lines of CSV inventory comparison logic
- Complex but self-contained domain logic
- Depends on AddressUtils/NominatimValidator (extract those first)

## Call Sites (key external)
- `_build_diff_item()` - 1 call
- `_build_mismatch_item()` - 1 call
- `_generate_mismatch_records()` - 2 calls
- `_process_single_device()` - 1 call
- `_process_all_devices()` - 2 calls
- Menu dispatch for inventory comparison operations

## Dependencies to Check
- `AddressUtils`, `NominatimValidator` (should extract first)
- CSV file reading/writing
- `CacheUtils` for data caching
- `OrgInventoryExporter` for fresh data

## Extraction Steps
1. Create `src/inventory/__init__.py` and `src/inventory/csv_comparator.py`
2. Move entire `InventoryCSVComparator` class
3. In MistHelper.py: `from src.inventory.csv_comparator import InventoryCSVComparator`
4. Update imports for AddressUtils dependency
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~800 lines from MistHelper.py (~1.5% reduction)
""",
    },
    {
        "title": "refactor: Extract RateLimitingUtils class (~400 lines) to src/utils/rate_limiting.py",
        "body": """## Extraction Target
**Class**: `RateLimitingUtils` (~400 lines)
**Target**: `src/utils/rate_limiting.py`

## Why Extract
- ~400 lines of adaptive rate limiting with PID-like control
- Only 3 external call sites
- Pure utility logic independent of specific API operations
- Manages delay_metrics.json and tuning_data.json files

## Call Sites (external)
- **Line 10916**: `RateLimitingUtils.get_rate_limited_delay(self.smoothed)` in APIDataFetcher._call_api_with_retry
- **Line 25606**: `RateLimitingUtils.get_rate_limited_delay(smoothed)` in GatewayTestExporter
- **Line 25732**: `RateLimitingUtils.get_rate_limited_delay(smoothed)` in GatewayStatsExporter

## Dependencies to Check
- JSON file I/O (delay_metrics.json, tuning_data.json)
- `time` module for delays
- `logging` for debug output
- No Mist API dependencies (pure utility)

## Extraction Steps
1. Create `src/utils/rate_limiting.py`
2. Move entire `RateLimitingUtils` class
3. In MistHelper.py: `from src.utils.rate_limiting import RateLimitingUtils`
4. Update 3 call sites
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~400 lines from MistHelper.py (~0.7% reduction)
""",
    },
    {
        "title": "refactor: Extract ZoneConfigurationAnalyzer class (~600 lines) to src/analytics/zone_analyzer.py",
        "body": """## Extraction Target
**Class**: `ZoneConfigurationAnalyzer` (~600 lines)
**Target**: `src/analytics/zone_analyzer.py`

## Why Extract
- ~600 lines dedicated to zone configuration analysis
- `analyze()` method has 0 external call sites (potential dead code or menu-only)
- Analytics code is logically separate from core operations

## Dead Code Found Within
- `analyze()` (40 lines, 0 calls) - entry point may be via menu dispatch only

## Call Sites
- All internal self.* calls
- Menu dispatch (if any) needs verification

## Dependencies to Check
- `mistapi` site settings APIs
- Site zone configuration structures
- `DataExporter` for report output

## Extraction Steps
1. Create `src/analytics/__init__.py` and `src/analytics/zone_analyzer.py`
2. Move entire `ZoneConfigurationAnalyzer` class
3. In MistHelper.py: `from src.analytics.zone_analyzer import ZoneConfigurationAnalyzer`
4. Update menu dispatch if applicable
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~600 lines from MistHelper.py (~1.1% reduction)
""",
    },
    {
        "title": "refactor: Extract E911BSSIDReportGenerator class (~500 lines) to src/reports/e911_bssid.py",
        "body": """## Extraction Target
**Class**: `E911BSSIDReportGenerator` (~500 lines)
**Target**: `src/reports/e911_bssid.py`

## Why Extract
- ~500 lines dedicated to E911 BSSID report generation
- Specialized reporting logic with clear domain boundary
- Self-contained with few external dependencies

## Call Sites (key external)
- `_build_bssid_rows()` - 1 call
- `_process_sites()` - 1 call
- `_fetch_org_bulk_data()` - 1 call
- Menu dispatch for E911 report operations

## Dependencies to Check
- `mistapi` AP and WLAN APIs
- Site/AP data fetching
- CSV/report output
- `CacheUtils` for data caching

## Extraction Steps
1. Create `src/reports/__init__.py` and `src/reports/e911_bssid.py`
2. Move entire `E911BSSIDReportGenerator` class
3. In MistHelper.py: `from src.reports.e911_bssid import E911BSSIDReportGenerator`
4. Update menu dispatch
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~500 lines from MistHelper.py (~0.9% reduction)
""",
    },
    {
        "title": "refactor: Extract update_gateway_templates_wan2_variable() (722 lines) to src/gateway/wan2_variable.py",
        "body": """## Extraction Target
**Function**: `update_gateway_templates_wan2_variable()` (lines 32423-33144, 722 lines)
**Target**: `src/gateway/wan2_variable.py`

## Why Extract
- 722-line top-level function (largest non-class function in the monolith)
- Only 1 external call site
- Gateway WAN2 variable management is a standalone operation

## Call Sites (external)
- **Line 58869**: `lambda fast=False, dry_run=False: update_gateway_templates_wan2_variable(fast=fast, dry_run=dry_run)`
- This is a menu dispatch lambda - only caller

## Dependencies to Check
- `mistapi` gateway template APIs
- `CacheUtils` for template caching
- `DataExporter` for result export
- `safe_input()` for confirmations
- Gateway template data structures

## Extraction Steps
1. Create `src/gateway/wan2_variable.py`
2. Move entire function with any helper functions it defines
3. In MistHelper.py: `from src.gateway.wan2_variable import update_gateway_templates_wan2_variable`
4. Menu dispatch lambda already uses function name - no change needed
5. Run validation: py_compile, ruff, black, --test

## Size Impact
Removes ~722 lines from MistHelper.py (~1.3% reduction)
""",
    },
]

def create_issue(title, body):
    """Create a GitHub issue using gh CLI."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(body)
        f.flush()
        result = subprocess.run(
            ['gh', 'issue', 'create',
             '--repo', f'{OWNER}/{REPO}',
             '--title', title,
             '--label', LABELS,
             '--body-file', f.name],
            capture_output=True, text=True, encoding='utf-8'
        )
        print(f"{'OK' if result.returncode == 0 else 'FAIL'}: {title}")
        if result.stdout:
            print(f"  URL: {result.stdout.strip()}")
        if result.stderr:
            print(f"  Error: {result.stderr.strip()}")
    return result.returncode == 0


def main():
    print(f"Creating {len(issues)} issues for monolith decomposition...\n")
    success = 0
    for issue in issues:
        body = issue.get("body")
        if not body and issue.get("body_file"):
            with open(issue["body_file"], encoding='utf-8') as f:
                body = f.read()
        if create_issue(issue["title"], body):
            success += 1
    print(f"\nCreated {success}/{len(issues)} issues successfully.")


if __name__ == "__main__":
    main()
