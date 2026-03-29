# Contracts: Device Management Commands

**Feature**: 014-device-utility-commands | **Date**: 2026-03-20

## 1. Locate Device — `startSiteLocateDevice()`

**Menu**: 135 | **Endpoint**: `POST .../locate`
**Device Types**: AP, Switch | **WebSocket**: No | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `duration` | int | No | Minutes to flash LEDs (1-120, default 5) |
| `mac` | string | No | For VC: MAC of member switch |

### Response: `200 OK` (no body)

### MistHelper Behavior
1. Select site -> select device (AP or switch)
2. Validate device type (reject gateways with message)
3. Prompt for duration (default 5 minutes)
4. POST command, confirm success
5. Print: "Device LED blinking for {duration} minutes. Use 'Unlocate' to stop."

---

## 2. Unlocate Device — `stopSiteLocateDevice()`

**Menu**: 136 | **Endpoint**: `POST .../unlocate`
**Device Types**: AP, Switch | **WebSocket**: No | **Destructive**: No

### Request: Empty body
### Response: `200 OK`

### MistHelper Behavior
1. Select site -> select device (AP or switch)
2. POST command, confirm success
3. Print: "Device LED blinking stopped."

---

## 3. Bounce Port — `bounceDevicePort()`

**Menu**: 137 | **Endpoint**: `POST .../bounce_port`
**Device Types**: Switch, Gateway | **WebSocket**: Yes | **Destructive**: Yes (y/N confirm)

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ports` | array[string] | Yes | Port names to bounce (e.g., `["ge-0/0/0"]`) |

### Restrictions
- Ports starting with `vme`, `ae`, `irb` are not supported
- HA control ports (SSR) are not supported

### MistHelper Behavior
1. Select site -> select device (switch or gateway)
2. Fetch and display available ports (FR-041)
3. User selects port(s) by number or types name
4. **Confirmation**: `safe_input("Bounce port {port}? This will briefly disrupt traffic. (y/N): ")`
5. POST command, await WebSocket confirmation ("Port bounce complete.")
6. Display result

---

## 4. Cable Test — `cableTestFromSwitch()`

**Menu**: 138 | **Endpoint**: `POST .../cable_test`
**Device Types**: Switch | **WebSocket**: Yes | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `port` | string | Yes | Port name to test |

### MistHelper Behavior
1. Select site -> select switch device
2. Fetch and display available ports (FR-041)
3. User selects port
4. POST command, await WebSocket results (pair status, length, fault distance)
5. Display cable test results
6. Write to CSV/SQLite

---

## 5. Reprovision Device — `reprovisionSiteOctermDevice()`

**Menu**: 139 | **Endpoint**: `POST .../reprovision`
**Device Types**: Switch, Gateway | **WebSocket**: No | **Destructive**: Yes (y/N confirm)

### Request: Empty body
### Response: `200 OK`

### MistHelper Behavior
1. Select site -> select device (switch or gateway)
2. **Confirmation**: `safe_input("Reprovision device {name}? This will push fresh config. (y/N): ")`
3. POST command, confirm success
4. Print: "Device reprovisioning initiated."

---

## 6. Re-adopt Device — `readoptSiteOctermDevice()`

**Menu**: 140 | **Endpoint**: `POST .../readopt`
**Device Types**: Switch | **WebSocket**: No | **Destructive**: No

### Request: Empty body
### Response: `200 OK`

### MistHelper Behavior
1. Select site -> select switch device
2. POST command, confirm success
3. Print: "Device re-adoption initiated."

---

## 7. Get ZTP Password — `getSiteDeviceZtpPassword()`

**Menu**: 141 | **Endpoint**: `POST .../request_ztp_password`
**Device Types**: Switch, Gateway | **WebSocket**: No | **Destructive**: No

### Request: Empty body
### Response: `200 OK` with password in response body

### MistHelper Behavior
1. Select site -> select device (switch or gateway)
2. POST command
3. Display ZTP password (temporary root password)
4. **Security**: Password displayed on console only, not logged, not written to CSV/SQLite

---

## 8. Get Config CLI Commands — `getSiteDeviceConfigCmd()`

**Menu**: 142 | **Endpoint**: `POST .../get_config_cmd` (exact endpoint TBD from SDK)
**Device Types**: Switch | **WebSocket**: No | **Destructive**: No

### MistHelper Behavior
1. Select site -> select switch device
2. POST command
3. Display CLI commands for brown-field adoption
4. Option to copy to clipboard or save to file

---

## 9. Upload Support File — `uploadSiteDeviceSupportFile()`

**Menu**: 143 | **Endpoint**: `POST .../support`
**Device Types**: Switch, Gateway | **WebSocket**: No | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `info` | string | No | Type: `full`, `process`, `outbound-ssh`, `messages`, `core-dumps`, `var-logs`, `jma-logs` |
| `node` | string | No | SSR: node0/node1 (default: both) |
| `num_messages_files` | int | No | Number of messages files (1-10, default 1) |

### MistHelper Behavior
1. Select site -> select device (switch or gateway)
2. Display support file type options
3. User selects type (default: `full`)
4. POST command, confirm upload initiated
5. Print: "Support file upload initiated. Files will be available in Mist dashboard."

---

## 10-11. Poll Stats & Create Snapshot

### 10. Poll Switch Stats — `pollSiteSwitchStats()`

**Menu**: 153 | **Endpoint**: `POST .../poll_stats`
**Device Types**: Switch | **WebSocket**: No | **Destructive**: No

### 11. Create Device Snapshot — `createSiteDeviceSnapshot()`

**Menu**: 154 | **Endpoint**: `POST .../snapshot`
**Device Types**: Switch | **WebSocket**: No | **Destructive**: No

### Common MistHelper Behavior
1. Select site -> select switch device
2. POST command, confirm success
3. Print confirmation message
