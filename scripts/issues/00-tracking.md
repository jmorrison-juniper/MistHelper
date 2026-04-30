# Monolith Decomposition Tracking Issue

## Problem
`MistHelper.py` has grown to **54,794 lines** containing **110 classes**, **1,571 methods**, and **29 top-level functions**. This makes the codebase difficult to navigate, test in isolation, and develop on with multiple agents (only one PR can touch MistHelper.py at a time).

## Analysis Summary
A systematic AST-based analysis (see `scripts/analyze_monolith.py`) identified **634 decomposition candidates** totaling **42,376 extractable lines** (~77% of the file). Candidates are prioritized by self-containment, size, and logical cohesion.

## Priority Extraction Groups

### Tier 1: Whole-Class Extractions (largest impact)
| Class | Lines | Methods | Refs | Target Module |
| - | - | - | - | - |
| MapsManager | 7,731 | 35 | 0 | src/maps/maps_manager.py |
| EnhancedSSHRunner | 2,743 | 37 | 63 | src/ssh/ssh_runner.py |
| PacketCaptureManager | 2,621 | 23 | 6 | src/capture/packet_capture.py |
| FirmwareManager | 2,322 | 32 | 5 | src/firmware/firmware_manager.py |
| MistHelperTUI | 2,088 | 19 | 2 | src/ui/tui.py |
| OrgLevelAPFirmwareUpgrader | 1,854 | 66 | 11 | src/firmware/org_ap_upgrader.py |
| BulkAPFirmwareUpgrader | 1,673 | 72 | 2 | src/firmware/bulk_ap_upgrader.py |
| RoutingUtils | 1,673 | 40 | 60 | src/network/routing_utils.py |
| SSIDTemplateConsolidationManager | 1,444 | 70 | 2 | src/ssid_consolidation/ |

### Tier 2: Medium Class Extractions
| Class | Lines | Target Module |
| - | - | - |
| WebSocket group (3 classes) | ~2,000 | src/websocket/ |
| DeviceUtilityCommands | ~800 | src/device/utility_commands.py |
| GatewayTemplateConfigManager | ~700 | src/gateway/template_config.py |
| SiteAutoUpgradeConfigurator | ~1,200 | src/firmware/site_auto_upgrade.py |
| BulkSwitchFirmwareUpgrader | ~600 | src/firmware/bulk_switch_upgrader.py |
| VirtualChassisManager | ~600 | src/device/virtual_chassis.py |

### Tier 3: Utility Extractions
| Class/Function | Lines | Target Module |
| - | - | - |
| AddressUtils + NominatimValidator | ~1,000 | src/utils/address_utils.py |
| InventoryCSVComparator | ~800 | src/inventory/csv_comparator.py |
| RateLimitingUtils | ~400 | src/utils/rate_limiting.py |
| ZoneConfigurationAnalyzer | ~600 | src/analytics/zone_analyzer.py |
| E911BSSIDReportGenerator | ~500 | src/reports/e911_bssid.py |
| update_gateway_templates_wan2_variable() | 722 | src/gateway/wan2_variable.py |

## Extraction Pattern
1. Create target module file under src/
2. Move class/function with all dependencies
3. Add import in MistHelper.py
4. Update all call sites (documented per sub-issue)
5. Validate: py_compile, ruff, black, --test

## Constraints
- One class extraction per PR (hot file rule)
- Maintain menu dispatch backward compatibility
- Each extraction must pass full test suite
