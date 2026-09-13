# Quickstart: Device Utility Commands

**Feature**: 014-device-utility-commands | **Date**: 2026-03-20

## Prerequisites

- Python 3.13+
- MistHelper venv activated (`.venv\Scripts\Activate.ps1` on Windows)
- Valid `.env` file with `MIST_APITOKEN` and `MIST_ORG_ID`
- At least one Mist-managed site with connected devices

## Development Setup

```powershell
# Clone and checkout feature branch
git checkout 014-device-utility-commands

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Verify dependencies
pip install -r requirements.txt
```

## Running the New Commands

### Interactive Mode
```powershell
python MistHelper.py
# Then select menu numbers 120-154
```

### Direct Invocation
```powershell
# Traceroute
python MistHelper.py --menu 120

# Show OSPF neighbors
python MistHelper.py --menu 121

# Show sessions (SSR)
python MistHelper.py --menu 125
```

## Menu Number Map (Quick Reference)

| Menu | Command | Category |
|------|---------|----------|
| 120 | Traceroute | Diagnostic |
| 121-124 | OSPF (neighbors, interfaces, database, summary) | Diagnostic |
| 125 | Show Sessions (SSR) | Show |
| 126 | Show Service Path (SSR) | Show |
| 127 | Show BGP Summary | Show |
| 128 | Show ARP Table | Show |
| 129 | Show DHCP Leases | Show |
| 130 | Show 802.1X Table | Show |
| 131 | Show EVPN Database | Show |
| 132 | Resolve DNS (SSR) | Diagnostic |
| 133 | Monitor Traffic (streaming) | Diagnostic |
| 134 | Run Top (streaming) | Diagnostic |
| 135 | Locate Device (LED blink) | Management |
| 136 | Unlocate Device (stop LED) | Management |
| 137 | Bounce Port | Management |
| 138 | Cable Test | Management |
| 139 | Reprovision Device | Management |
| 140 | Re-adopt Device | Management |
| 141 | Get ZTP Password | Management |
| 142 | Get Config CLI Commands | Management |
| 143 | Upload Support File | Management |
| 144 | Clear ARP Cache | Clear/Reset |
| 145 | Clear BGP Routes | Clear/Reset |
| 146 | Clear Session | Clear/Reset |
| 147 | Clear MAC Table | Clear/Reset |
| 148 | Clear BPDU Errors | Clear/Reset |
| 149 | Clear Learned MACs | Clear/Reset |
| 150 | Clear Policy Hit Count | Clear/Reset |
| 151 | Release DHCP Lease | Clear/Reset |
| 152 | Release DHCP Lease (SSR) | Clear/Reset |
| 153 | Poll Switch Stats | Hardware |
| 154 | Create Device Snapshot | Hardware |

## Testing

### Automated Tests
```powershell
# Run full test suite (skips interactive and destructive)
python MistHelper.py --test
```

**Test skip list additions**: Menu 133, 134 (streaming/interactive), 137, 139, 144-152 (destructive clear/reset operations).

### Manual Testing Checklist

**P1 — Test First**:
1. Traceroute (120): Pick any device, enter `8.8.8.8`, verify hop output
2. OSPF neighbors (121): Pick SSR/SRX gateway, verify neighbor table
3. Show sessions (125): Pick SSR gateway, verify session list
4. Show service path (126): Pick SSR gateway, verify path table

**P2 — Test Second**:
5. BGP summary (127): Pick switch or gateway with BGP
6. ARP table (128): Pick any switch, verify IP-MAC mappings
7. Locate/unlocate (135-136): Pick any AP, verify LED response
8. Bounce port (137): Pick switch, select port, confirm bounce

**P3 — Test Last (Destructive)**:
9. Clear ARP (144): Pick device, type 'CLEAR', verify cache cleared
10. Reprovision (139): Pick non-production device, confirm reprovision

## Validation Before Commit

```powershell
# Step 1: Syntax check
python -m py_compile MistHelper.py

# Step 2: Run automated tests
python MistHelper.py --test

# Step 3: Manual smoke test (at minimum: traceroute + show ARP)
python MistHelper.py --menu 120
python MistHelper.py --menu 128
```

## Key Implementation Files

| File | What to Change |
|------|----------------|
| `MistHelper.py` | Add `DeviceUtilityCommands` class, menu entries 120-154, PK strategies |
| `README.md` | Update operation count, add menu table entries, changelog |

## Architecture Notes

- All commands in `DeviceUtilityCommands` class (static methods)
- WebSocket commands reuse existing `WebSocketManager`
- Device selection reuses `PromptUtils.select_site_id_from_csv()` and `PromptUtils.select_device_id_from_inventory()`
- Confirmation gates use `safe_input()` with context parameter
- Dual output via `DataExporter.write_with_format_selection()` for show commands
