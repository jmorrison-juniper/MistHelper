# Contracts: Hardware Operations

**Feature**: 014-device-utility-commands | **Date**: 2026-03-20

Hardware operations are switch-specific. BIOS and FPGA upgrades are the most destructive operations in this feature and require the strongest confirmation gates.

## 1. Poll Switch Stats — `pollSiteSwitchStats()`

**Menu**: 153 | **Endpoint**: `POST .../poll_stats`
**Device Types**: Switch | **WebSocket**: No | **Destructive**: No

### Request: Empty body
### Response: `200 OK`

### MistHelper Behavior
1. Select site -> select switch device
2. POST command
3. Print: "Fresh statistics polled from switch. Updated stats will appear in next stats export."

---

## 2. Create Device Snapshot — `createSiteDeviceSnapshot()`

**Menu**: 154 | **Endpoint**: `POST .../snapshot`
**Device Types**: Switch | **WebSocket**: No | **Destructive**: No

### Request: Empty body
### Response: `200 OK`

### MistHelper Behavior
1. Select site -> select switch device
2. POST command
3. Print: "Device snapshot created successfully."

---

## 3. Upgrade BIOS — `upgradeSiteDeviceBios()`

**Note**: This may overlap with existing Menu 99-100 (Switch/SSR Firmware). If already covered, this entry serves as a cross-reference. If not covered, it becomes a new menu entry.

**Endpoint**: `POST .../upgrade_bios`
**Device Types**: Switch | **WebSocket**: No | **Destructive**: Yes (type 'UPGRADE')

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `version` | string | No | Target BIOS version |

### MistHelper Behavior
1. Select site -> select switch device
2. Display current BIOS version and available upgrade
3. **Destructive confirmation**: `safe_input("Type 'UPGRADE' to proceed with BIOS upgrade: ", context="bios_upgrade")`
4. POST command
5. Print: "BIOS upgrade initiated. Device will reboot when complete."

---

## 4. Upgrade FPGA — `upgradeSiteDeviceFpga()`

**Note**: Same overlap consideration as BIOS above.

**Endpoint**: `POST .../upgrade_fpga`
**Device Types**: Switch | **WebSocket**: No | **Destructive**: Yes (type 'UPGRADE')

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `version` | string | No | Target FPGA version |

### MistHelper Behavior
1. Select site -> select switch device
2. Display current FPGA version and available upgrade
3. **Destructive confirmation**: `safe_input("Type 'UPGRADE' to proceed with FPGA upgrade: ", context="fpga_upgrade")`
4. POST command
5. Print: "FPGA upgrade initiated. Device will reboot when complete."
