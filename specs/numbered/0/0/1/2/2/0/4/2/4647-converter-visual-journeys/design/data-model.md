# Data Model: Add independently authored converter visual journeys

This record adds no persistent data. The entities below describe browser state and test fixtures for the journeys in `spec.md`.

## Entities

| Entity | Lives in | Attributes | Natural key |
| - | - | - | - |
| Converter page state | Browser memory | Current state (see transitions), proposal object, typed word, status text | Page instance (not stored) |
| Proposal | Browser memory and server response | `gateway_template` (name, type, optional `dns_servers`), `unsupported_items` (line, command, reason), `known_gaps` (list of text) | SHA-256 digest of the canonical JSON (`ReviewState.digest`, RC-24) |
| Review approval | Server session | `cisco_proposal` digest and `cisco_reviewed` digest (RC-24) | Session cookie and proposal digest |
| Typed confirmation | Browser memory | Exact text value of `cisco-confirm` | None (compared with `EXPORT`) |
| Status message | Browser memory | Text in `cisco-status` with a word label | None |
| Test host | Test process | Portal app, loopback server, stop function | Test class |
| Shipped theme | Host file set | Name and theme file under `web_portal/static/css/themes/` | Theme name (`magenta`, `dark`, `light`, `high-contrast`) |
| Viewport profile | Test constant | Width and height | Name (`PHONE`, `DESKTOP`) |

## Natural keys

- The review binds to the proposal digest. A changed proposal has a different digest, so the review no longer matches (RC-17).
- The shipped theme name is the key for the theme file and for the host storage value (RC-32).
- The viewport profile name is the key for each responsive case (RC-40).

## State transitions

| From | Trigger | To | Page effect |
| - | - | - | - |
| Idle | Submit preview with a file and a name | Previewing | Status: `Preparing the proposal.` |
| Previewing | Newest preview succeeds | Proposal shown | Structured review renders. Review control enables. Focus moves to the review heading. |
| Previewing | Newest preview fails | Idle | Proposal clears. Status starts with `Error:`. |
| Previewing | An older response arrives | Previewing | Older response is ignored. |
| Proposal shown | Review succeeds | Reviewed | Typed confirmation field enables. Focus moves to it. |
| Reviewed | Typed word equals `EXPORT` | Confirmed | Export control enables. |
| Reviewed or Confirmed | Typed word differs | Reviewed | Export control disables. Status names the required word. |
| Confirmed | Export succeeds | Exported | Download starts. Status confirms the export. |
| Reviewed or Confirmed | Cancel selected | Reviewed | Typed word clears. Review remains. |
| Any state with a proposal | Reset selected | Idle | All fields and proposal clear. Focus moves to the file input. |
| Any state with a proposal | File, name, or type changes | Idle | Proposal and review clear. |
| Any state | Page hides | Idle | Proposal clears. |

Each transition changes only the browser state. Server review state changes only through the review and export routes (RC-17, RC-20).
