# Data Model: WebSockets tab in the Operations portal

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-09-29

All entities live in memory in the portal process. No entity goes to a database or a file.

## Catalog entities

### FieldSpec

One input field of a catalog entry.

| Attribute | Type | Rule |
| - | - | - |
| `name` | text | The SDK parameter name, such as `host` or `port_id`. |
| `label` | text | The label on the page. |
| `kind` | enum | `uuid`, `host`, `integer`, `text`, `choice`, `mac`, `mac_list`, `port`, `port_list`, `boolean`, or `interfaces`. |
| `required` | yes or no | A required field must hold a value. |
| `minimum`, `maximum` | integer | The range of an `integer` field. |
| `choices` | list of text | The values of a `choice` field. |
| `default` | any | The value that the page shows first. |
| `help` | text | One plain sentence for the operator. |

### ChannelDefinition

One subscribe channel. The catalog holds 18.

| Attribute | Type | Rule |
| - | - | - |
| `key` | text | Unique, such as `site.stats.devices`. |
| `scope` | enum | `organization`, `site`, `location`, or `diagnostics`. |
| `name`, `description` | text | Plain words for the page. |
| `path_template` | text | Such as `/sites/{site_id}/stats/devices`. The page never receives it. |
| `identifiers` | list of FieldSpec | The identifiers that the path needs, such as `site_id` and `map_id`. |
| `repeatable` | text or none | The one identifier that accepts up to 10 values, such as `device_id`. |

### UtilityDefinition

One device utility. The catalog holds 54, and 2 of them are shells.

| Attribute | Type | Rule |
| - | - | - |
| `key` | text | Unique, such as `ex.ping`. |
| `family` | enum | `ap`, `ex`, `srx`, `ssr`, or `mxedge`. |
| `function_name` | text | The SDK facade function, such as `ping`. |
| `name`, `description` | text | Plain words for the page. |
| `fields` | list of FieldSpec | The parameters that the operator sets. |
| `safety` | enum | `read`, `capture`, `change`, or `shell`. |
| `output` | enum | `lines`, `screen`, `packets`, or `terminal`. |
| `scope` | enum | `site` for all entries except the organization Mist Edge capture. |

## Request entities

### StartRequest

The checked form of a start request. The server builds it only after every check passes.

| Attribute | Type | Rule |
| - | - | - |
| `kind` | enum | `channel`, `utility`, or `shell`. |
| `key` | text | It must name a catalog entry of that kind. |
| `targets` | map of text | Each identifier that the entry needs, in its checked form. |
| `parameters` | map | Each parameter value, converted to its SDK type. |
| `confirmation` | text or none | The typed device name for the `change` and `shell` classes. |

**Checks**:

- An unknown key, an unknown field, or a raw path is refused.
- A UUID must match the 8-4-4-4-12 hexadecimal form.
- A MAC address must hold 12 hexadecimal digits, with or without `:` or `-`.
- A host must be an IPv4 address, an IPv6 address, or a DNS name of 253 characters or fewer.
- A port name must match the Junos form, such as `ge-0/0/1` or `ge-0/0/1.0`.
- A capture filter must hold 256 characters or fewer, from letters, digits, spaces, and `. : / - _ ( ) [ ] = ! < > & |`.
- A `change` or `shell` request is refused while its flag is off. When the flag is on, the confirmation must equal the device name.

### PickerOption

One row in a picker list.

| Attribute | Type | Rule |
| - | - | - |
| `id` | text | The Mist identifier. |
| `label` | text | The name, or the MAC address when the name is empty. |
| `family` | text or none | Devices only: `ap`, `ex`, `srx`, `ssr`, or none. |
| `detail` | text | The model, the MAC address, or the status. |

A picker answer holds `rows`, `total_count`, and a `reason` when the list is empty.

## Session entities

### StreamSession

One live connection that an operator started.

| Attribute | Type | Rule |
| - | - | - |
| `session_id` | text | A random 16-character token. |
| `request` | StartRequest | The checked request. |
| `title` | text | The catalog name with the target names. |
| `state` | SessionState | See the state machine below. |
| `reason` | text | The plain reason for the last state change. |
| `started_at`, `ended_at` | time | UTC. |
| `last_read_at` | time | Each message request updates it. |
| `counters` | SessionCounters | `received`, `dropped`, `shortened`, and `bytes`. |
| `buffer` | MessageBuffer | The newest messages. |

### SessionState

```text
connecting --> live --------> stopped
     |          |  \--------> failed
     |          |  \--------> finished
     |          |  \--------> timed out
     |          \-----------> stopping --> stopped
     \--> failed
     \--> stopping --> stopped
```

| State | Meaning | Live |
| - | - | - |
| `connecting` | The server sent the request and waits for the subscription or the first output. | Yes |
| `live` | Messages can arrive. | Yes |
| `stopping` | The operator, the reaper, or the portal asked the connection to close. | Yes |
| `stopped` | The connection closed after a stop request. | No |
| `finished` | A utility ended and sent output. | No |
| `timed out` | A utility ended and sent no output. | No |
| `failed` | Mist refused the request, refused the subscription, or closed the connection with an error. | No |

A session in a live state counts toward the session limit. An ended session stays in the list for 10 minutes.

### MessageBuffer

A ring buffer with two caps: a message count and a byte total. When a new message passes a cap, the buffer drops the oldest messages and adds them to the drop count.

### StreamMessage

| Attribute | Type | Rule |
| - | - | - |
| `seq` | integer | Starts at 1. It grows by 1 for each message in the session. |
| `received_at` | time | UTC, set by the server. |
| `channel` | text | The channel path for a channel stream. The page shows only the catalog name. |
| `kind` | enum | `json`, `event`, `text`, `screen`, or `packet`. |
| `content` | any | The decoded JSON, the text, or the packet record. |
| `summary` | text or none | Packets only: time, source, destination, protocol, and length. |
| `size` | integer | The size in bytes before shortening. |
| `shortened` | yes or no | Yes when the message was larger than 256 KB. |

## Settings entity

### StreamSettings

| Attribute | Environment variable | Default | Range |
| - | - | - | - |
| `changes_enabled` | `PORTAL_WS_ENABLE_CHANGES` | off | on or off |
| `shell_enabled` | `PORTAL_WS_ENABLE_SHELL` | off | on or off |
| `max_sessions` | `PORTAL_WS_MAX_SESSIONS` | 5 | 1 to 20 |
| `idle_seconds` | `PORTAL_WS_IDLE_SECONDS` | 120 | 30 to 3600 |
| `buffer_messages` | `PORTAL_WS_BUFFER_MESSAGES` | 500 | 50 to 5000 |
| `buffer_bytes` | `PORTAL_WS_BUFFER_MB` | 8 MB | 1 to 64 MB |
| `max_stream_seconds` | `PORTAL_WS_MAX_STREAM_MINUTES` | 30 minutes | 1 to 240 minutes |

A value outside its range, or a value that is not a number, gives the default. The server logs a warning with the variable name.
