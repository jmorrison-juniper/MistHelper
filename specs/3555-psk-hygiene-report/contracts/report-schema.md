# Contract: `PskHygiene.csv`

## File

The default CSV file is `data\PskHygiene.csv`.

The operation must export through `DataExporter.write_with_format_selection(data, filename, api_function_name=...)`, so configured non-CSV backends remain available.

## Required columns

| Column | Required | Secret-safe rule |
| - | - | - |
| `name` | Yes | Must not contain passphrase data. |
| `ssid` | Yes | Normalized from PSK data. |
| `role` | Yes | Preserved from PSK data. |
| `vlan` | Yes | Preserved from PSK data. |
| `usage` | Yes | Blank when unavailable. |
| `max_usage` | Yes | Blank when unavailable. |
| `expire_time` | Yes | Original expire time or blank. |
| `days_remaining` | Yes | Integer or blank. |
| `rotation_pending` | Yes | Boolean value derived from old passphrase presence. |
| `old_passphrase_present` | Yes | Boolean value only. |
| `wlan_match` | Yes | `true`, `false`, or `unknown`. |
| `findings` | Yes | Comma-separated finding labels. |

## Forbidden columns

The report must not include these columns:

- `passphrase`
- `old_passphrase`

## Finding labels

The `findings` column can hold zero or more labels. Labels must use this stable order:

1. `expired`
2. `expires_soon`
3. `uncapped_multi_use`
4. `rotation_pending`
5. `orphan_ssid`

## Summary contract

The console summary must include:

- Total PSKs reviewed.
- Expired keys.
- Keys that expire in `30` days.
- Uncapped multi-use keys.
- Pending rotations.
- Orphan SSIDs.
- A statement that site-level WLANs are outside scope.

The summary must not include PSK values.
