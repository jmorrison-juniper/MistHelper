# Data Model: WebSocket Client Selection

This feature adds no stored records. These records describe one temporary lookup and its input values.

## Target Context

| Field | Type | Source | Rule |
| - | - | - | - |
| `site_id` | UUID string | Existing site picker | Required for discovery. |
| `device_id` | UUID string | Existing device picker | Required for discovery. |
| `device_mac` | MAC string | Selected site's Mist device record | Resolve on the server. Do not infer it from `device_id`. |
| `family` | Existing catalog value | Selected device record | Restrict choices to the utility family. |
| `operation_key` | Existing catalog key | Selected utility | Restrict discovery to the four named utilities. |

The site, device, family, and operation define one discovery scope. A change to any scope field expires the current result.

## Client Choice

| Field | Type | Source | Rule |
| - | - | - | - |
| `mac` | MAC string | Client search result | Required and validated before display. |
| `label` | Optional string | Hostname or available client label | Display as plain text. |
| `site_id` | UUID string | Client search result | Must match the selected site. |
| `associated_device_macs` | String list | Wired search result | Must contain the selected device MAC. |
| `association_evidence` | `wired_client` or absent | Checked result | A record without supported evidence is not selectable. |

Deduplicate choices by normalized MAC within the current target. Keep identical labels distinct by displaying each MAC. A choice proves only the returned association. It does not prove that a client is currently connected.

For `ex.retrieveMacTable`, a choice can fill the existing `mac_address` input. The input remains editable and empty by default. The current validator accepts complete MAC addresses only. The pinned SDK does not document partial-filter support, so this feature leaves validation unchanged.

For EX DHCP release, one or more choices populate the existing `macs` input. The input remains editable for disconnected or unlisted clients. The current checker limits the list to 48 unique complete MAC addresses.

For SRX and SSR DHCP release, client choices remain unavailable unless the pinned SDK and response prove selected-gateway association.

## Discovery State

| State | Meaning | Manual input |
| - | - | - |
| `loading` | A scoped read-only lookup is active. | Remains editable. |
| `available` | Complete, validated choices match the target. | Remains editable. |
| `empty` | The read succeeded and returned no eligible choices. | Remains editable. |
| `request_error` | A 4xx response refused the lookup. | Remains editable. |
| `service_error` | A 5xx response or network failure stopped the lookup. | Remains editable. |
| `unavailable` | SDK support, association evidence, complete pagination, or a timely response is unavailable. | Remains editable. |

Each state belongs to one scope and one lookup generation. An expired generation cannot alter the page.
Timeout uses the `unavailable` state with a distinct timeout reason and visible message.

## Utility Input

| Field | Utility keys | Type | Empty behavior | Output |
| - | - | - | - | - |
| `macs` | `ex.releaseDhcpLeases`, `srx.releaseDhcpLeases`, `ssr.releaseDhcpLeases` | Optional list of MAC strings | Omitted | Copied to the existing DHCP utility request. |
| `mac_address` | `ex.retrieveMacTable` | Optional string | Omitted | Copied to the existing MAC-table utility request. |

The selector must not change the utility key, field name, request body shape, target, confirmation, lock, or cancellation behavior. The operation checker remains responsible for validation.
