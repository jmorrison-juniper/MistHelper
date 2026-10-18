# Data Model: Mist Cisco Config Converter

## Source Configuration

Represents operator-provided Cisco IOS text and its file metadata.

| Field | Meaning | Validation |
|---|---|---|
| `name` | Original file name shown to the operator | Treat as display text. Do not use it as a path. |
| `content` | Uploaded Cisco IOS configuration bytes | Require non-empty UTF-8 text. Do not log the content. |
| `size_bytes` | Input size in bytes | Limit to 16 MiB. |
| `format` | Supported text-file suffix | Accept `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, or `.log`. |
| `template_name` | Proposed gateway template name | Require 1 to 120 non-whitespace characters. |
| `template_type` | Mist gateway template type | Accept only `standalone` or `spoke`. |

Process uploaded bytes in memory. Do not create a server-side path or a persistent source record.

## Conversion Proposal

Represents the output shown before export.

| Field | Meaning | Validation |
|---|---|---|
| `gateway_template` | Proposed Mist template request object | Contains `name`, `type`, and `dns_servers` only when supported input provides values. |
| `unsupported_items` | Input commands not represented in proposed settings | Preserve in review and export. Never silently drop them. |
| `known_gaps` | Limits of the supported conversion subset | Show during review and include in export. |

The converter maps only global IPv4 `ip name-server` directives to `dns_servers`. It does not
map gateway roles, hardware models, IPv6 commands, malformed directives, or other settings.

## Review State

The signed Flask session stores a digest of the current proposal and a digest for the reviewed
proposal. Export requires both digests to match the submitted proposal.

## State Transitions

```text
uploaded -> validated -> parsed -> proposal_ready -> reviewed -> exported
```

- Invalid input stops before `validated`.
- An empty supported result does not add a `dns_servers` field.
- Unknown, IPv6, and malformed commands remain unsupported items.
- Export does not change Mist cloud state.
- Cloud apply is outside the first release.
- Credentials are not fields of these entities and are never copied into persistent or
  browser-visible data.
