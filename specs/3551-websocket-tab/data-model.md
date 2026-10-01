# Data Model: WebSockets tab in the Operations portal

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-09-29

All entities live in memory in the portal process. No entity goes to a database or a file.

## Catalog entities

### FieldSpec

One input field of a catalog entry.

| Attribute | Type | Rule |
| - | - | - |
| `name` | text | The SDK parameter name or the identifier name, such as `host`, `port_id`, or `site_id`. |
| `label` | text | The label on the page. |
| `kind` | enum | `uuid`, `host`, `ip`, `prefix`, `integer`, `vlan`, `choice`, `boolean`, `mac`, `mac_list`, `port`, `port_list`, `name`, `name_list`, or `filter`. |
| `required` | yes or no | A required field must hold a value. |
| `minimum`, `maximum` | integer | The range of an `integer` field. |
| `choices` | list of text | The values of a `choice` field. |
| `default` | text, integer, yes or no, or none | The value that the page shows first. |
| `hint` | text | One plain sentence for the operator. |
| `picker` | text or none | The picker list that fills an identifier field, such as `sites`, `devices`, or `maps`. |

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

Only the server builds a channel path. `build_paths` fills the template with the checked identifiers of a start request. It gives one path for each value of the repeatable identifier.

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
| `targets` | list of FieldSpec | The identifiers that name the device and the site, such as `site_id` and `device_id`. |
| `scope` | enum | `site` for all entries except the organization Mist Edge capture, which uses `organization`. |

## Request entities

### StartRequest

The checked form of a start request. The server builds it only after every check passes.

| Attribute | Type | Rule |
| - | - | - |
| `kind` | enum | `channel`, `utility`, or `shell`. |
| `definition` | ChannelDefinition or UtilityDefinition | The catalog entry. The `key` property reads its key. |
| `targets` | map of text lists | Each identifier that the entry needs, in its checked form. The server adds `org_id` from the portal settings. |
| `parameters` | map | Each parameter value in its checked, JSON-safe form. The runner converts an enum value to its SDK type. |
| `title` | text | The catalog name with the target labels, for the session card. |
| `confirmation` | text or none | The typed device name for the `change` and `shell` classes. |
| `device_name` | text or none | The device name that Mist reported. The audit log names the device with it. |

The request body can also hold a `labels` map. It maps an identifier value to a label, such as a site name. The server keeps 64 printable characters or fewer of each label and uses them only in the title.

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
| `counters` | SessionCounters | `received`, `dropped`, `shortened`, and `bytes`. The `bytes` value is the memory that the kept messages use. |
| `buffer` | MessageBuffer | The newest messages. |
| `input_ready` | yes or no | Shells only. Yes after the first output, and the server refuses input before that. |

The session payload also holds the `output` view and the `safety` class of the entry. It also holds the message rate over the last 10 seconds and the last sequence number. A channel stream has the output `json` and the safety `read`.

### SessionState

```text
connecting --> live --------> stopped
     |          |  \--------> failed
     |          |  \--------> finished
     |          |  \--------> timed_out
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
| `timed_out` | A utility ended and sent no output. | No |
| `failed` | Mist refused the request, refused the subscription, or closed the connection with an error. | No |

A session in a live state counts toward the session limit. An ended session stays in the list for 10 minutes at most. The list keeps only the 5 newest ended sessions, so the manager removes an older ended session before its 10 minutes end.

### MessageBuffer

A ring buffer with two caps: a message count and a byte total. When a new message passes a cap, the buffer drops the oldest messages and adds them to the drop count.

The buffer keeps the content of each message as compact JSON text, not as decoded objects. The byte total counts the memory of each kept message. That memory is the JSON text, the summary, the source, and a fixed cost of 320 bytes for the record. The T075 load check measured the record cost at 235 to 304 bytes. Thus a full buffer uses no more memory than the byte cap.

A read does not decode the stored text. The server joins the stored text of each message into the answer in one step.

### StreamMessage

| Attribute | Type | Rule |
| - | - | - |
| `seq` | integer | Starts at 1. It grows by 1 for each message in the session. |
| `received_at` | time | UTC, set by the server. |
| `source` | text or none | The value of the repeatable identifier that the message came from, such as a site identifier. The page labels the message with it. |
| `kind` | enum | `json`, `event`, `text`, `screen`, or `packet`. |
| `content` | any | The decoded JSON, the text, or the packet record. The buffer keeps it as compact JSON text. |
| `summary` | text or none | Packets only: time, source, destination, protocol, and length. |
| `size` | integer | The size of the compact JSON text in bytes before shortening. |
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
