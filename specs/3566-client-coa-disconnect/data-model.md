# Data Model: Client CoA Disconnect

## Entity: ClientSessionControlRequest

A request attempt for one site, one action, and one target.

### Fields

| Field | Type | Required | Validation |
| - | - | - | - |
| `site_id` | String | Yes | Must be a selected Mist site identifier. |
| `site_name` | String | Yes | Must come from the selected site. |
| `action_key` | String | Yes | Must match one supported action. |
| `action_label` | String | Yes | Must be shown to the operator. |
| `target_type` | String | Yes | Must be `client_mac` or `rogue_bssid`. |
| `raw_target` | String | Yes | Must be the operator input before normalization. |
| `normalized_target` | String | Yes | Must be 12 lowercase hexadecimal characters. |
| `dry_run` | Boolean | Yes | Comes from `--dry-run` dispatcher state. |
| `confirmed` | Boolean | Yes | True only when the normalized confirmation matches the normalized target. |
| `operation_id` | String | Yes | Must be the Mist operation ID selected by the action. |
| `result` | String | Yes | Must be one of the result values below. |
| `message` | String | No | Must not include secrets. |
| `timestamp_utc` | String | Yes | ISO 8601 UTC timestamp. |

### Result values

- `success`
- `dry_run`
- `confirmation_failed`
- `validation_failed`
- `mist_failure`

### Relationships

- A request has one action definition.
- A request has one target identifier.
- A request writes one log row.

### State transitions

1. `created`
2. `validated`
3. `previewed`
4. `confirmed` or `stopped`
5. `sent` or `skipped`
6. `logged`

## Entity: ActionDefinition

A supported destructive action.

### Fields

| Field | Type | Required | Validation |
| - | - | - | - |
| `action_key` | String | Yes | Unique stable key. |
| `label` | String | Yes | Operator-facing label in STE. |
| `target_type` | String | Yes | `client_mac` or `rogue_bssid`. |
| `operation_id` | String | Yes | Must match OpenAPI and `mistapi`. |
| `sdk_module` | String | Yes | Must name the SDK module to import. |
| `sdk_function` | String | Yes | Must name the SDK function to call. |
| `scope` | String | Yes | `site`. |

### Supported values

| Action key | Target type | Operation ID |
| - | - | - |
| `wireless_reauthenticate` | `client_mac` | `reauthSiteDot1xWirelessClient` |
| `wired_reauthenticate` | `client_mac` | `reauthSiteDot1xWiredClient` |
| `disconnect` | `client_mac` | `disconnectSiteWirelessClient` |
| `unauthorize_guest` | `client_mac` | `unauthorizeSiteWirelessClient` |
| `deauth_rogue_clients` | `rogue_bssid` | `deauthSiteWirelessClientsConnectedToARogue` |

## Entity: TargetIdentifier

A normalized client MAC or rogue BSSID.

### Fields

| Field | Type | Required | Validation |
| - | - | - | - |
| `target_type` | String | Yes | Must match the selected action. |
| `raw_value` | String | Yes | Input can use colons, hyphens, dots, or no separators. |
| `normalized_value` | String | Yes | Exactly 12 lowercase hexadecimal characters. |
| `display_value` | String | Yes | Same as `normalized_value` for confirmation. |

## Entity: Confirmation

The destructive approval typed by the operator.

### Fields

| Field | Type | Required | Validation |
| - | - | - | - |
| `prompt_target` | String | Yes | Must be the normalized target shown to the operator. |
| `raw_confirmation` | String | Yes | Input from `safe_input()`. |
| `normalized_confirmation` | String | Yes | Same normalization rules as the target. |
| `matched` | Boolean | Yes | True only for an exact normalized match. |

## Entity: ClientSessionControlLogRow

One CSV audit row for one request attempt.

### Required columns

- `timestamp_utc`
- `site_id`
- `site_name`
- `action_key`
- `action_label`
- `target_type`
- `target`
- `dry_run`
- `confirmed`
- `operation_id`
- `result`
- `message`

### Validation rules

- Write exactly one row for each attempt.
- Create the file with headers when it does not exist.
- Write under `data/ClientSessionControlLog.csv` only.
- Do not write tokens, passwords, or unrelated personal data.

## Entity: WiringManifest

The owned record that defers repository registration.

### Fields

| Field | Value |
| - | - |
| Menu number | `286` |
| Category | `destructive` |
| Handler class | `ClientSessionControl` |
| Entry point | static `run()` |
| Package | `src/device/client_session_control/` |
| Test package | `tests/unit/device/client_session_control/` |
| Registration state | Deferred to `wiring.md` |
