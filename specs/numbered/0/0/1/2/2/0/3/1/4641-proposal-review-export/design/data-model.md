# Data Model: Versioned Proposal Review and Safe Export

This model covers the in-memory objects, the browser session values, and the state transitions of version 2. The record writes no database row and no file.

## Entities

### SourceUpload (transient)

- **Name**: The template name. It holds 1 to 120 visible characters, as in version 1.
- **Template type**: The value `standalone` or `spoke`.
- **Content**: The UTF-8 text of the file. The limit is 16 MiB. The content stays in memory for one request.
- **Suffix**: One of `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, or `.log`.
- **Persistence**: None. The content leaves memory when the request ends.
- **Natural key**: None.

### Scope

| Field | Type | Rule |
| - | - | - |
| `name` | string | The template name from the request. |
| `template_type` | string | `standalone` or `spoke`. |
| `source` | object | `bytes` (integer, the UTF-8 byte count of the content) and `suffix` (lowercase text). |
| `hardware_role` | null | Reserved for issue #4638. Always null in version 2 today. |
| `hardware_model` | null | Reserved for issue #4638. Always null in version 2 today. |
| `target` | null | Reserved for cloud target selection (issue #4642). Always null offline. |

The scope digest is `ReviewState.digest(scope)`. It is stored in the proposal as `scope_digest`.

### StructuredProposal

The object has exactly these ten keys, listed in `design/contracts/proposal-v2.md`:

`proposal_version`, `scope`, `scope_digest`, `gateway_template`, `object_changes`, `omissions`, `unresolved_mappings`, `verification`, `unsupported_items`, and `known_gaps`.

**Invariants**:

- `proposal_version` equals 2.
- `scope_digest` equals the digest of `scope`.
- `object_changes` holds one entry for the gateway template.
- `omissions` holds one entry for each unsupported item and one entry for each known gap.
- `unresolved_mappings` is a list. For the DNS subset, it is empty.
- `verification.local_schema` equals `passed`, and `verification.cloud_state` equals `unavailable`.

**Digest**: `ReviewState.digest(proposal)`. The digest covers every key, including `scope_digest`.

### ObjectChange

| Field | Value in version 2 |
| - | - |
| `object` | `gateway_template` |
| `action` | `propose_create` |
| `identity` | `name` and `template_type` from the scope |
| `fields` | The field names present in `gateway_template`, in the same order as the object |
| `existing_state` | `not_checked` |

### Omission

| Field | Present when | Value |
| - | - | - |
| `kind` | Always | `unsupported_source_line`, `known_gap`, or `no_supported_command` |
| `line` | `kind` is `unsupported_source_line` | The one-based source line number |
| `category` | `kind` is `unsupported_source_line` | The label from the version 1 converter, for example `[unsupported source line]` |
| `text` | `kind` is `known_gap` or `no_supported_command` | The known gap text or the no-command text |
| `disposition` | Always | `omitted` |

### UnresolvedMapping

Version 2 defines the item shape for issues #4638 and #4640: `field` (string), `reason` (string), and `owner_issue` (integer). The DNS subset produces no item.

### Verification

| Field | Value |
| - | - |
| `local_schema` | `passed`, after the local check of the gateway template fields |
| `cloud_state` | `unavailable` |
| `reason` | `Offline preview. No Mist request is made.` |

### ReviewBinding (browser session)

| Session key | Value | Written by |
| - | - | - |
| `cisco_proposal` | Lowercase hexadecimal digest of the last proposal | Any preview, version 1 or version 2 |
| `cisco_reviewed` | Lowercase hexadecimal digest of the reviewed proposal | A review with a matching digest |
| `cisco_proposal_at` | UTC time of the last version 2 preview, as ISO 8601 text | Version 2 preview on success |
| `cisco_reviewed_at` | UTC time of the last version 2 review, as ISO 8601 text | Version 2 review on success |

The session holds no source text, no template name, and no unsupported value. Each time value starts the lifetime `REVIEW_LIFETIME`, which is 15 minutes. The boundary is inclusive (decision D-20).

## Keys

- The proposal identity is its digest.
- The gateway template identity in a proposal is the pair `name` and `template_type`. The Mist identifier is unknown offline, so the proposal holds no identifier.
- No database row is written, so no primary key strategy applies.

## State Transitions

| From | Event | To | Response |
| - | - | - | - |
| Any | Preview with valid input | Previewed with the new digest and time. `cisco_reviewed` and `cisco_reviewed_at` are removed. | HTTP 200 with the proposal |
| Any | Preview with invalid input | No review. Both keys are removed. | HTTP 400 with an error |
| Previewed with digest D | Review with digest D | Reviewed with digest D | HTTP 200 with the same object |
| Previewed or reviewed | Review with another digest | Unchanged | HTTP 409 |
| Reviewed with digest D | Export with digest D | Unchanged | HTTP 200, attachment `cisco-proposal-v2.json` |
| Previewed with digest D | Export | Unchanged | HTTP 409 with the review message |
| No review | Review or export | Unchanged | HTTP 409 with the preview message |
| Previewed at time T | Review at T plus `REVIEW_LIFETIME` or later | Unchanged | HTTP 409 with the preview expiry message |
| Reviewed at time T | Export at T plus `REVIEW_LIFETIME` or later | Unchanged | HTTP 409 with the review expiry message |
| Any | Browser session cannot be read, for example after a restart with a new secret | No review | HTTP 409 on review and export |

Caution: A session that cannot be read clears every review. The operator must preview and review again.
