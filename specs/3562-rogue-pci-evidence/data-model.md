# Data Model: Rogue PCI Evidence Pack

## RogueDetection

| Field | Type | Rule |
| - | - | - |
| `org_id` | string | Required for export identity. |
| `site_id` | string | Required when Mist returns it. |
| `site_name` | string | Use `Unknown Site` when missing. |
| `ssid` | string | Keep blank when Mist returns no value. |
| `bssid` | string | Normalize to lowercase for comparison. |
| `channel` | string | Preserve the Mist value. |
| `band` | string | Preserve the Mist value when present. |
| `rssi` | string | Use `rssi` or `avg_rssi` from the source row. |
| `first_seen` | string | Use event timestamp when no first value exists. |
| `last_seen` | string | Use event timestamp when no last value exists. |
| `client_count` | integer | Use `num_clients`, or zero when missing. |
| `classification` | string | Must be `honeypot`, `rogue`, or `neighbor`. |
| `impersonated_org_ssid` | string | Required only for `honeypot`. |

## SiteRogueSettings

| Field | Type | Rule |
| - | - | - |
| `org_id` | string | Required for export identity. |
| `site_id` | string | Required for every site row. |
| `site_name` | string | Use `Unknown Site` when missing. |
| `rogue_enabled` | boolean | False means detection off. |
| `honeypot_enabled` | boolean | False means honeypot detection off. |
| `neighbor_rssi_threshold` | integer or blank | Read from `rogue.min_rssi`. |
| `approved_ssid_count` | integer | Count `rogue.whitelisted_ssids`. |
| `approved_bssid_count` | integer | Count `rogue.whitelisted_bssids`. |
| `read_status` | string | `ok` or `error`. |
| `run_started_at` | string | Same timestamp for all rows in one run. |

## EvidenceSummary

| Field | Type | Rule |
| - | - | - |
| `run_started_at` | string | UTC ISO 8601 timestamp. |
| `detection_count` | integer | Count of detection rows. |
| `honeypot_count` | integer | Count where classification is `honeypot`. |
| `rogue_count` | integer | Count where classification is `rogue`. |
| `neighbor_count` | integer | Count where classification is `neighbor`. |
| `site_count` | integer | Count of site setting rows. |
| `detection_off_site_count` | integer | Count where `rogue_enabled` is false. |
| `incomplete_site_count` | integer | Count where `read_status` is `error`. |

## Relationships

- One `EvidenceSummary` describes one run.
- One run has many `RogueDetection` rows.
- One run has one `SiteRogueSettings` row per site.
- A `RogueDetection` can refer to one `SiteRogueSettings` row through `site_id`.

## Validation Rules

- Classifications must be one of `honeypot`, `rogue`, or `neighbor`.
- Honeypot classification wins when the SSID matches an org WLAN SSID and the BSSID is not an org AP BSSID.
- Detection-off sites must remain in `RogueSiteSettings.csv`.
- The summary detection-off count must equal the number of settings rows where `rogue_enabled` is false.

