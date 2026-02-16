# MistHelper Compliance Report

**Generated**: 2026-02-09  
**Audited Against**: agents.md / copilot-instructions.md  
**File**: MistHelper.py (51,156 lines)

---

## Executive Summary

| Category | Status | Violations | Priority |
|----------|--------|------------|----------|
| Raw `input()` calls | FAIL | 60+ | HIGH |
| Function parameter limits (>5) | FAIL | 8 | MEDIUM |
| Function length limits (>25 lines) | PARTIAL | Not fully audited | MEDIUM |
| Single-letter loop variables | FAIL | 12 | LOW |
| Unicode in logging | PASS | 0 | - |
| Hardcoded path separators | PASS | 0 | - |

---

## 1. Raw `input()` Violations (HIGH PRIORITY)

All input operations should use `InputUtils.safe_input()` for proper EOF and KeyboardInterrupt handling in SSH/container contexts.

### 1.1 Device Selection (No Exception Handling)
| Line | Code | Context |
|------|------|---------|
| 9097 | `input("Enter the index or name of the device to view device: ")` | Device selector |
| 9149 | `input("\nEnter site index or name: ")` | Site selector |
| 10210 | `input(f"\n  Enter client index (0-{max_index}) or 'q' to quit: ")` | Client selector |
| 12810 | `input("Client MAC/Index: ")` | Client lookup |

### 1.2 WebSocket/Gateway Commands (No Exception Handling)
| Line | Code | Context |
|------|------|---------|
| 9987 | `input("Search scope - (s)ite-specific or (o)rganization-wide? [s/o]: ")` | Scope selection |
| 13638 | `input("Enter the target hostname or IP address to ping (default: 8.8.8.8): ")` | Ping target |
| 13650 | `input("Enter number of ping packets (default: 4): ")` | Ping count |
| 14129 | `input("   -> Continue anyway? (y/N): ")` | Warning confirmation |
| 14629 | `input("   -> Continue anyway? (y/N): ")` | Warning confirmation |
| 14941 | `input(prompt)` | SSR tenant selection |
| 14986 | `input("-> Enter tenant name manually (or press Enter to skip): ")` | Manual tenant |
| 15053 | `input(prompt)` | SSR service selection |
| 15101 | `input("Enter custom service name: ")` | Custom service |
| 15111 | `input("Enter service name: ")` | Service name |
| 15120 | `input("\nEnter target host/IP to ping [default: 8.8.8.8]: ")` | Ping target |
| 15138 | `input("Enter ping count [default: 4]: ")` | Ping count |
| 15147 | `input("Enter packet size in bytes [default: 56]: ")` | Packet size |
| 15156 | `input("Enter HA node (node0/node1) [optional]: ")` | HA node |

### 1.3 Routing Table Operations (No Exception Handling)
| Line | Code | Context |
|------|------|---------|
| 16431 | `input("\nEnter IP prefix (press Enter for default 0.0.0.0/0): ")` | IP prefix |
| 16432 | `input("Enter service name (press Enter to skip): ")` | Service name |
| 16433 | `input("Enter VRF name (press Enter to skip): ")` | VRF |
| 16434 | `input("Enter node (node0/node1 for HA, press Enter to skip): ")` | HA node |
| 16710 | `input("Continue with switch routing command anyway? (y/N): ")` | Confirmation |
| 16724 | `input("\nEnter route prefix (press Enter to show all routes): ")` | Route prefix |
| 16727 | `input("Enter protocol filter (press Enter for 'any'): ")` | Protocol |
| 16729 | `input("Enter VRF name (press Enter to skip): ")` | VRF |
| 16730 | `input("Enter BGP neighbor IP (press Enter to skip): ")` | BGP neighbor |
| 16735 | `input("Enter route direction (press Enter for both): ")` | Direction |
| 16737 | `input("Enter node (node0/node1 for HA, press Enter to skip): ")` | HA node |
| 16969 | `input("Continue anyway? (y/N): ")` | Confirmation |
| 16973 | `input("Continue anyway? (y/N): ")` | Confirmation |
| 16990 | `input("Enter protocol (press Enter for API default): ")` | Protocol |
| 16994 | `input("\nEnter route prefix (e.g., 192.168.1.0/24, press Enter to skip): ")` | Prefix |
| 16998 | `input("Enter VRF name (press Enter for default VRF): ")` | VRF |
| 17002 | `input("Enter BGP neighbor IP (press Enter to skip): ")` | BGP neighbor |
| 17006 | `input("Enter route direction (press Enter for both): ")` | Direction |
| 17010 | `input("Enter HA cluster node (node0/node1, press Enter to skip): ")` | HA node |
| 17015 | `input("Refresh interval in seconds (0-10, press Enter for one-time): ")` | Refresh |
| 17021 | `input("Refresh duration in seconds (0-300, press Enter for 30): ")` | Duration |

### 1.4 Site Configuration Operations (No Exception Handling)
| Line | Code | Context |
|------|------|---------|
| 19910 | `input("Select an option (1-5): ")` | Menu selection |
| 23420 | `input(prompt)` | Generic prompt |
| 24454 | `input("\n  Choose selection method (1-3): ")` | Selection method |
| 24474 | `input("  Site numbers: ")` | Site numbers |
| 24509 | `input("\n  Proceed with setting site variables? (yes/no): ")` | **DESTRUCTIVE** |

### 1.5 VC Conversion Operations (No Exception Handling) - **DESTRUCTIVE**
| Line | Code | Context |
|------|------|---------|
| 25027 | `input("\n  Selection: ")` | VC selection |
| 25062 | `input("\n  Select operation [1/2/cancel]: ")` | Operation select |
| 25207 | `input("\n  Confirmation: ")` | **DESTRUCTIVE** |
| 25779 | `input("\n  Selection: ")` | VC selection |
| 25901 | `input("\n  Confirmation: ")` | **DESTRUCTIVE** |
| 26200 | `input("\n  Selection: ")` | VC selection |
| 26375 | `input("\n  Confirmation: ")` | **DESTRUCTIVE** |
| 26641 | `input("\n  Do you want to proceed with the conversion? (yes/no): ")` | **DESTRUCTIVE** |
| 26728 | `input(f"\nEnter the index or switch name to convert to virtual MAC [0-{len(switches)-1}]: ")` | Selection |
| 26777 | `input("   Would you like to create an empty file to get started? (y/n): ")` | File creation |

### 1.6 SSH Operations (Partial Handling - Mixed)
| Line | Status | Code |
|------|--------|------|
| 21006 | Has try/except | `input("Enter SSH host(s) (comma-separated): ")` |
| 21018 | Has try/except | `input("Enter SSH username: ")` |
| 21040 | Has try/except | `input("Command: ")` |
| 21133 | No handling | `input(f"\n  Enter template number (1-{len(templates)}) or name: ")` |
| 21180 | No handling | `input(f"\n  Execute SSH commands on {count} gateways? (y/N): ")` |
| 27921 | No handling | `input("   Would you like to create an empty file? (y/n): ")` |
| 28108 | No handling | `input(">>> ")` - Interactive SSH session |

### 1.7 Map Operations (No Exception Handling)
| Line | Code | Context |
|------|------|---------|
| 28450 | `input("File path: ")` | File input |
| 28520 | `input("\nSelect scaling mode [1]: ")` | Scale mode |
| 28590 | `input(f"Enter new PPM (current: {self.original_ppm:.2f}): ")` | PPM input |
| 28633 | `input("Continue anyway? (yes/no): ")` | Confirmation |
| 28731 | `input("\nType 'REPLACE' to proceed: ")` | **DESTRUCTIVE** |
| 29035 | `input("Enter site index or name: ")` | Site selection |
| 29115 | `input("\nSelect map number (or 0 to cancel): ")` | Map selection |
| 29464 | `input("\nEnter your selection number now: ")` | Selection |
| 29933 | `input("\nSelect map number (or 0 to cancel): ")` | Map selection |
| 30008 | `input("Enter map name: ")` | Map name |
| 30017 | `input("Select type (1-3, default=1): ")` | Map type |
| 30028 | `input("Enter width in pixels (default=1024): ")` | Width |
| 30029 | `input("Enter height in pixels (default=768): ")` | Height |
| 30030 | `input("Enter pixels per meter (default=10): ")` | PPM |
| 30139 | `input(f"\nEnter name for cloned map [{default_name}]: ")` | Clone name |
| 30217 | `input("\nProceed with full clone? (yes/no): ")` | Clone confirm |
| 30527 | `input(f"Map name [{current_map.get('name', '')}]: ")` | Map name |
| 30532 | `input(f"Width in pixels [{current_map.get('width', '')}]: ")` | Width |
| 30540 | `input(f"Height in pixels [{current_map.get('height', '')}]: ")` | Height |
| 30548 | `input(f"Pixels per meter [{current_map.get('ppm', '')}]: ")` | PPM |
| 30556 | `input(f"Orientation in degrees [{current_map.get('orientation', 0)}]: ")` | Orientation |
| 30574 | `input("\nApply these changes? (yes/no): ")` | **DESTRUCTIVE** |
| 30644 | `input("Confirmation: ")` | **DESTRUCTIVE** |
| 30699 | `input("File path: ")` | File path |
| 30729 | `input("Continue with upload? (yes/no): ")` | Upload confirm |
| 30738 | `input("\nUpload this image to the selected map? (yes/no): ")` | **DESTRUCTIVE** |
| 30830 | `input("\nExport to CSV? (yes/no): ")` | Export |
| 31060 | `input("\nWould you like to continue without interactive features? (yes/no): ")` | Fallback |

---

## 2. Function Parameter Limit Violations (MEDIUM PRIORITY)

Rule: Max 5 parameters per function/method (excluding `self`/`cls`).

| Line | Function | Parameters | Exceeds By |
|------|----------|------------|------------|
| 34316 | `handle_drawing_tools` | 11 | +6 |
| 33977 | `toggle_layers` | 6 | +1 |
| 35242 | `refresh_client_positions` | 6 | +1 |
| 16807 | `_process_routing_table_results` | 6 | +1 |
| 17079 | `_process_ssr_route_results` | 6 | +1 |
| 8353 | `_insert_single_row` | 5 + self (6 total) | +1 |
| 29140 | `_backup_map_geometry` | 5 + self (6 total) | +1 |
| 45480 | `_format_value_hierarchical` | 5 + self (6 total) | +1 |

### Remediation Recommendations:
- **handle_drawing_tools**: Convert parameters to a `DrawingToolsContext` dataclass
- **toggle_layers**: Accept a `LayerVisibility` config object
- **refresh_client_positions**: Accept a `RefreshConfig` dataclass

---

## 3. Single-Letter Loop Variable Violations (LOW PRIORITY)

Rule: No abbreviations - use descriptive names like `for device in devices`.

| Line | Current | Recommended |
|------|---------|-------------|
| 9864 | `for i in range(...)` | `for index in range(...)` |
| 27323 | `for t in templates_to_update[:5]` | `for template in templates_to_update[:5]` |
| 28882 | `for v in vertices` | `for vertex in vertices` |
| 37069 | `for r in completed` | `for result in completed` |
| 37075 | `for r in failed` | `for result in failed` |
| 37080 | `for r in interrupted` | `for result in interrupted` |
| 39548 | `for v in self.available_versions` | `for version in self.available_versions` |
| 39557 | `for v in raw_versions` | `for version in raw_versions` |
| 39573 | `for d in self.aps_by_model[model]` | `for device in self.aps_by_model[model]` |
| 41957 | `for v in self.available_versions` | `for version in self.available_versions` |
| 41967 | `for v in versions` | `for version in versions` |
| 49249 | `for h in list(logger.handlers)` | `for handler in list(logger.handlers)` |

**Note**: Single-letter variables in list comprehensions (e.g., `[p for p in self.failed_imports]`) are idiomatic Python and can be considered acceptable in that context.

---

## 4. Compliant Areas

### 4.1 Unicode in Logging - PASS
No Unicode characters found in logging statements.

### 4.2 Hardcoded Path Separators - PASS  
Container paths (`/app/`) are legitimate for container detection logic.

### 4.3 InputUtils.safe_input() Implementation - PASS
The implementation at line 1897 correctly handles EOFError and KeyboardInterrupt.

---

## 5. Previously Remediated (Session)

The following violations were fixed during the previous audit session:

| Menu | Function | Issue | Resolution |
|------|----------|-------|------------|
| 96 | `wan_port_conflicts` | 88 lines (max 25) | Refactored to 8 helper methods |
| 98 | `_select_gateway_template` | Only KeyboardInterrupt | Added EOFError |
| 98 | `_confirm_execution` | Only KeyboardInterrupt | Added EOFError |
| 99 | `execute_switch_firmware_upgrade...` | Only KeyboardInterrupt | Added EOFError |
| 100 | `execute_ssr_firmware_upgrade...` | Only KeyboardInterrupt | Added EOFError |
| 120 | `SiteAnalyticsConfigurator.execute` | Raw input() | Changed to InputUtils.safe_input() |

---

## 6. Remediation Priority Matrix

| Priority | Category | Impact | Effort | Recommendation |
|----------|----------|--------|--------|----------------|
| P0 | Destructive input() calls | App crash in container | LOW | Immediate fix |
| P1 | All other raw input() | Session termination | MEDIUM | Batch remediation |
| P2 | Function parameters >5 | Code maintainability | HIGH | Refactor with dataclasses |
| P3 | Single-letter variables | Readability | LOW | Opportunistic cleanup |

### P0 Destructive Calls (Require Immediate Attention):
```
Lines: 24509, 25207, 25901, 26375, 26641, 28731, 30574, 30644, 30738
```

---

## 7. Remediation Template

Replace raw `input()` calls with:
```python
# Before (violation):
user_input = input("Enter value: ").strip()

# After (compliant):
user_input = InputUtils.safe_input(
    "Enter value: ",
    context="operation_name"
)
```

For destructive operations:
```python
# Before (violation):
confirm = input("Type 'DELETE' to proceed: ").strip()

# After (compliant):
confirm = InputUtils.safe_input(
    "Type 'DELETE' to proceed: ",
    context="delete_operation"
)
if confirm != "DELETE":
    logging.warning("Operation cancelled - confirmation failed")
    return
```

---

**Report End**
