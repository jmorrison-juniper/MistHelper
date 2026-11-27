# Data Model: Add explicit gateway role and hardware selection

This record adds in-memory types only. It stores nothing on disk and writes no record. The review digest stays in the Flask session, as it does on main.

## HardwareSelection (`GatewaySelection`)

| Field | Type | Rule |
| --- | --- | --- |
| `role` | string | One of `branch`, `hub`, or `standalone`. |
| `family` | string | One of `srx` or `ssr`. |
| `model` | string | 1 to 32 visible characters. The register decides whether the row exists. |
| `port_assignments` | list of `HardwarePortAssignment` | At most 16 items. An empty list is valid input and yields blocker `port_missing_usage`. |

## HardwarePortAssignment

| Field | Type | Rule |
| --- | --- | --- |
| `mist_port` | string | Matches `^(ge\|xe)-[0-9]+/[0-9]+/[0-9]+$`. Must name a WAN or LAN port of the row. |
| `usage` | string | `wan` or `lan`. Mist term from the OpenAPI enum `gateway_port_usage` (line 80464). |
| `source_interface` | string | 1 to 64 characters. No whitespace and no control character. Must match a line `interface <name>` in the uploaded file. |

Identity rules:

- A Mist port appears at most one time in `port_assignments`. A second occurrence yields `port_duplicate`.
- A Cisco interface appears at most one time in `port_assignments`. A second occurrence yields `source_interface_duplicate`.
- The pair of a Mist port and a usage defines one physical mapping. The same port with a second usage is a duplicate.

## EvidenceRow

Rows exist in `conversion/hardware/register.py` only. Each row holds these values.

| Field | Type | Rule |
| --- | --- | --- |
| `family` | string | `srx` or `ssr`. |
| `model` | string | The Mist model name. |
| `status` | string | `verified` or `blocked`. A verified row has at least one WAN or LAN port. |
| `ports` | map from port name to usage | Empty for a blocked row. Holds only named ports and closed ranges. |
| `blocker` | string or null | Blocker code for a blocked row. Null for a verified row. |
| `revision` | string | Equals `openapi-b7fc2bfb-mistapi-0.64.1` at the time of writing. |
| `citations` | list of strings | Local line references. Each verified row cites one inventory line and one port line. |

## HardwareDecision

The result of `HardwareMapping.attach`. It appears under `hardware` in the proposal.

| Field | Type | Rule |
| --- | --- | --- |
| `role` | string | Copied from the selection. |
| `family` | string | Copied from the selection. |
| `model` | string | Copied from the selection. |
| `port_assignments` | list | Copied from the selection, sorted by `mist_port`. |
| `evidence_revision` | string | The row revision, or the current revision when no row exists. |
| `status` | string | `verified` when `blockers` is empty. Otherwise `blocked`. |
| `blockers` | list of objects | Each object has `code` and `message`. Codes appear in `proposal-json.md`. |

The derived template type is separate from the decision. `gateway_template.type` is `standalone` when the role is `standalone`. It is absent for `branch` and `hub`.

## Review state transitions

| From | Event | To | Rule |
| --- | --- | --- | --- |
| No proposal | Preview succeeds with `status` verified | Previewed | The digest is stored. No review exists. |
| No proposal | Preview succeeds with `status` blocked | Previewed | The digest is stored. Review is refused. |
| Previewed (verified) | Review with the same digest | Reviewed | The session stores the digest as reviewed. |
| Previewed (blocked) | Review with the same digest | Previewed | HTTP 409. Nothing changes. |
| Reviewed | Export with the same digest | Exported | HTTP 200 with the JSON download. |
| Previewed or Reviewed | Any preview | Previewed | The earlier digest and review are removed. |
| Previewed or Reviewed | A changed selection in a later request | Previewed for the new digest | The earlier export fails with HTTP 409. |
| Any state | Failed preview | No proposal | The earlier digest and review are removed. Existing behavior. |

## Relationships

- `HardwareMapping.attach` reads one `HardwareSelection`, one `SourceConfiguration`, and one `EvidenceRow`. It writes one `HardwareDecision` into the proposal.
- `HardwareRegister.options` reads every `EvidenceRow` for the page. It writes no state.
- `ReviewState.publish`, `ReviewState.verify`, and `ReviewState.approve` read the complete proposal. A change to any field changes the digest.
