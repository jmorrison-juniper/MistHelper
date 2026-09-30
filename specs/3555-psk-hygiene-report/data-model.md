# Data Model: PSK Hygiene Report

## Entity: `PskInput`

Represents one sanitized PSK record from Mist.

| Field | Type | Rule |
| - | - | - |
| `name` | `str` | Use an empty string when absent. |
| `ssid` | `str` | Trim leading and trailing spaces before matching. |
| `role` | `str` | Use an empty string when absent. |
| `vlan` | `str | int | None` | Preserve the visible value. Use a blank output cell when absent. |
| `usage` | `int | None` | Use `None` when Mist does not provide usage. |
| `max_usage` | `int | None` | Use `None` when absent or empty. |
| `expire_time` | `str | None` | Preserve the original value for output. |
| `mac` | `str | None` | Use only to determine cap status. Do not export unless already needed. |
| `macs` | `list[str]` | Use only to determine cap status. Do not export unless already needed. |
| `old_passphrase_present` | `bool` | True when `old_passphrase` exists and is not empty. |

Validation rules:

- Remove `passphrase` before building this entity.
- Replace `old_passphrase` with `old_passphrase_present`.
- Treat empty strings, empty lists, and null values as absent for `mac`, `macs`, and `max_usage`.

## Entity: `WlanReference`

Represents one organization-level SSID source.

| Field | Type | Rule |
| - | - | - |
| `ssid` | `str` | Trim leading and trailing spaces. |
| `source` | `Literal["org_wlan", "template"]` | Identify where the SSID was found. |
| `source_name` | `str` | Use WLAN or template name when available. |

Validation rules:

- Ignore records with no SSID.
- Do not include site-level WLANs.
- Treat organization templates as organization scope only.

## Entity: `PskHygieneRow`

Represents one output row for `PskHygiene.csv`.

| Column | Type | Rule |
| - | - | - |
| `name` | `str` | PSK name. |
| `ssid` | `str` | Normalized SSID. |
| `role` | `str` | Role value from the PSK. |
| `vlan` | `str` | VLAN value from the PSK, or blank when absent. |
| `usage` | `int | str` | Usage value or blank. |
| `max_usage` | `int | str` | Maximum usage value or blank. |
| `expire_time` | `str` | Original expire time or blank. |
| `days_remaining` | `int | str` | Blank when no expire time exists or parsing fails. |
| `rotation_pending` | `bool` | True when `old_passphrase_present` is true. |
| `old_passphrase_present` | `bool` | True when Mist returned `old_passphrase`. |
| `wlan_match` | `bool | str` | True, false, or `unknown` when WLAN data is unavailable. |
| `findings` | `str` | Comma-separated labels in stable order. |

Validation rules:

- Never include `passphrase`.
- Never include `old_passphrase`.
- Use a stable finding order: `expired`, `expires_soon`, `uncapped_multi_use`, `rotation_pending`, `orphan_ssid`.

## Entity: `HygieneSummary`

Represents the console and log summary.

| Field | Type | Rule |
| - | - | - |
| `total_psks` | `int` | Count all PSK rows. |
| `expired` | `int` | Count rows with `expired`. |
| `expires_soon` | `int` | Count rows with `expires_soon`. |
| `uncapped_multi_use` | `int` | Count rows with `uncapped_multi_use`. |
| `rotation_pending` | `int` | Count rows with `rotation_pending`. |
| `orphan_ssid` | `int` | Count rows with `orphan_ssid`. |
| `wlan_scope` | `str` | State that site-level WLANs are outside scope. |

Validation rules:

- Summary counts must match the `findings` column exactly.
- Summary text must not contain a PSK value.

## State transitions

```text
Raw Mist PSK -> sanitized PskInput -> PskHygieneRow -> exported report
Raw Mist WLAN/template -> WlanReference -> SSID match set -> PskHygieneRow.wlan_match
PskHygieneRow list -> HygieneSummary -> console and log summary
```

## Finding rules

| Finding | Rule |
| - | - |
| `expired` | `expire_time` is in the past. |
| `expires_soon` | `expire_time` is in the next `30` days and not in the past. |
| `uncapped_multi_use` | `mac`, `macs`, and `max_usage` are absent. |
| `rotation_pending` | `old_passphrase_present` is true. |
| `orphan_ssid` | Normalized SSID has no match in the organization WLAN reference set. |
