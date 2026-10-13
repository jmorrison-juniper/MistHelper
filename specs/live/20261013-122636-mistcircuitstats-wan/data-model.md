# Data Model: MistCircuitStats WAN Dashboard

This feature reads Mist data for a selected authorized organization. It stores no independent long-term copy of gateway telemetry.

## Organization

| Field | Meaning | Validation |
|---|---|---|
| `org_id` | Mist organization identifier | Must belong to the active Mist session. |
| `name` | Display name | Treat as untrusted text. |
| `last_updated` | Mist organization update time, when supplied | Parse as a timestamp and display in the selected timezone. |

An organization has sites and gateway inventory records.

## Site

| Field | Meaning | Validation |
|---|---|---|
| `site_id` | Mist site identifier | Must belong to the selected organization. |
| `name` | Site display name | Escape before rendering. |
| `timezone` | Site timezone | Use only a recognized timezone. |
| `address` | Optional site address | Escape before rendering. |

A site has gateways. Use a stable site identifier for filtering and cache keys.

## Gateway

| Field | Meaning | Validation |
|---|---|---|
| `device_id` | Mist gateway identifier | Match the selected site and organization. |
| `mac` | Gateway MAC or SDK device identifier | Normalize only as the documented SDK call requires. |
| `site_id` | Owning site | Must match a site in the organization. |
| `model` | Gateway model | Display as untrusted text. |
| `status` | Available Mist status fields | Preserve unknown values without inventing a state. |
| `profile_id` | Optional device profile identifier | Fetch through the documented SDK method. |
| `template_id` | Optional gateway template identifier | Fetch through the documented SDK method. |

A gateway has one or more WAN ports. Some gateways can lack optional profile or template data.

## WAN Port

| Field | Meaning | Validation |
|---|---|---|
| `port_id` | Port identifier | URL-encode for route use. |
| `name` | Port name | Escape before rendering. |
| `configuration_type` | DHCP, static, or other Mist value | Preserve the source value. |
| `vlan_id` | Optional VLAN identifier | Display only when supplied. |
| `mac` | Optional port MAC address | Validate its format before display. |
| `speed` | Optional port speed | Preserve the SDK unit. |
| `uptime` | Optional port uptime | Parse as a non-negative duration. |
| `counters` | Available Rx/Tx counters | Preserve the SDK unit and sample time. |

## Traffic Sample

| Field | Meaning | Validation |
|---|---|---|
| `timestamp` | Sample time | Store or compare in UTC. |
| `rx_bps` | Receive rate | Must be numeric and non-negative. |
| `tx_bps` | Transmit rate | Must be numeric and non-negative. |
| `max_rx_bps` | Peak receive rate when supplied | Must be numeric and non-negative. |
| `max_tx_bps` | Peak transmit rate when supplied | Must be numeric and non-negative. |
| `port_id` | Source WAN port | Must match the selected port. |

Traffic samples are grouped using the requested chart range. The 1-hour traffic chart uses 10-minute buckets.

## Peer Path

| Field | Meaning | Validation |
|---|---|---|
| `peer_id` | Mist peer or tunnel identifier | Treat as an opaque identifier. |
| `site_id` | Site that owns the path | Must match the selected organization. |
| `device_id` | Gateway that owns the path | Must match the selected gateway. |
| `status` | Mist path state when supplied | Preserve unknown values. |
| `health_metrics` | Available latency, loss, and quality fields | Preserve SDK units and sample times. |

## WAN Insight

| Field | Meaning | Validation |
|---|---|---|
| `range` | Selected insight period | One of 1h, 6h, 24h, 3d, or 7d. |
| `bandwidth_samples` | Per-hour average and peak Rx/Tx | Validate numeric values and UTC timestamps. |
| `link_health` | Jitter, latency, and loss | Show unavailable values as unavailable, not zero. |
| `application_health` | SLE summary and trend | Preserve Mist's score and interval. |
| `impacted_interfaces` | Interfaces that affect the SLE | Match against the selected site's interfaces. |
| `threshold` | Site's configured SLE target when supplied | Preserve Mist's value and unit. |

## Export

An export contains only the rows selected by the current gateway, port, and range filters. The hourly port export uses the source's 12-column header order. Export values must be neutralized when they can be interpreted as spreadsheet formulas.

## Cache Record

The cache is temporary shared service data, not a second database.

| Field | Meaning | Validation |
|---|---|---|
| `cache_key` | Feature-prefixed key scoped by organization and record type | Must use the `wan-dashboard:v1:` namespace. |
| `payload` | JSON-safe Mist response data | Validate before decoding or display. |
| `expires_at` | Cache expiry | Must not exceed the source TTL for that record. |

Use a 300-second TTL for site lists and a 600-second TTL for profiles and gateway templates. A cache failure must not result in another service or database.

## Relationships

```text
Organization 1 ── * Site
Site         1 ── * Gateway
Gateway      1 ── * WAN Port
WAN Port     1 ── * Traffic Sample
Gateway      1 ── * Peer Path
WAN Port     1 ── * WAN Insight
```
