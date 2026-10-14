# Data Model: Mist Cisco Config Converter

## Source Configuration

Represents operator-provided Cisco IOS text and its file metadata.

| Field | Meaning | Validation |
|---|---|---|
| `name` | Original file name shown to the operator | Treat as display text. Do not use it as a path. |
| `content` | Decoded Cisco IOS configuration text | Reject empty input and invalid encoding. Do not log the content. |
| `size_bytes` | Input size in bytes | Must be within the existing portal upload limit. |
| `format` | Detected supported input format | Accept only the approved Cisco IOS text format. |
| `source_id` | Identifier for this in-session input | Do not use it as a filesystem path or credential. |

## Gateway Selection

Represents the operator's selected conversion target.

| Field | Meaning | Validation |
|---|---|---|
| `role` | Gateway role used to select conversion rules | Must match an approved role mapping. |
| `hardware_model` | Gateway hardware model used to select conversion rules | Must match an approved model mapping for the selected role. |

The role and model pair must remain attached to the proposal. Reject apply if the pair changes after review.

## Conversion Proposal

Represents the output shown before export or apply.

| Field | Meaning | Validation |
|---|---|---|
| `proposal_id` | Identifier for the current preview | Scope to the active browser session. |
| `source_id` | Source configuration used for conversion | Must refer to a validated source in the same session. |
| `gateway_selection` | Role and model pair used by conversion | Must match the reviewed selection at apply time. |
| `proposed_settings` | Mist gateway template settings | Must satisfy the verified SDK request schema before cloud submission. |
| `unsupported_items` | Input commands not represented in proposed settings | Preserve in review and export. Never silently drop them. |
| `known_gaps` | Documented conversion limits that apply to this proposal | Show before export or apply. |
| `review_state` | Whether the operator has reviewed this proposal | Apply requires a reviewed state. |

## Apply Request

Represents the operator's request to create a Mist organization gateway template.

| Field | Meaning | Validation |
|---|---|---|
| `proposal_id` | Proposal selected for apply | Must exist in the current session and have a reviewed state. |
| `organization_id` | Mist organization that owns the new template | Must be present and authorized by the Mist session. |
| `confirmation` | Typed operator confirmation | Must match the required phrase before the SDK call. Never log the phrase. |
| `result_state` | Outcome of the SDK request | Use success, failure, or indeterminate. Never report success for an unknown outcome. |
| `template_id` | Identifier returned after successful creation | Present only when the SDK confirms creation. |

## State Transitions

```text
uploaded -> validated -> parsed -> proposal_ready -> reviewed
                                                  -> exported
                                                  -> apply_requested -> applied
                                                                      -> failed
                                                                      -> indeterminate
```

- Invalid input stops before `validated`.
- An empty supported result does not produce a misleading proposal.
- Export does not change the proposal's cloud state.
- Apply requires `reviewed`, valid credentials, organization access, and typed confirmation.
- An interrupted request with no definitive Mist response becomes `indeterminate`.
- Credentials are not fields of these entities and are never copied into persistent or browser-visible data.
