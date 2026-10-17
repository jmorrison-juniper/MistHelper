# Data Model: Multi-site WebSocket operations

**Issue**: #4259

## Model Boundary

The batch extends the existing process-local session model.
It introduces no database table or migration.
It uses natural Mist keys for target identity.
The existing session ID identifies the public batch and its artifact directory.
All timestamps use UTC ISO 8601.

## 1. Operation Reference

| Field | Type | Rule |
| - | - | - |
| `kind` | string | Existing channel or utility kind |
| `key` | string | Existing catalog key |
| `scope` | string | Catalog organization, site, or resource scope |
| `target_fields` | field list | Derived from `identifiers` or `targets` |
| `family` | string or null | Catalog utility family |
| `parameters` | object | Validated catalog fields only |
| `safety` | string | Existing read, capture, change, or shell class |
| `output` | string | Existing catalog output type |

Do not accept a raw REST path, channel path, SDK method name, or WebSocket URL.
Do not let a browser-provided family override the catalog.
A channel retains its current repeatable path limit of 10.
A channel batch subscribes to all selected target paths through one owned connection.
Utility and shell targets use separate bounded executions.

## 2. Discovery Snapshot and Preview

| Field | Type | Rule |
| - | - | - |
| `preview_id` | opaque string | Server-issued identifier |
| `org_id` | UUID | Configured organization only |
| `owner_scope` | private value | Current portal authentication and authorization context |
| `operation` | operation reference | One validated operation |
| `targets` | target list | Complete, deduplicated, ordered natural-key tuples |
| `commands` | ordered string list | Shell only |
| `parameters` | object | Fixed validated parameters |
| `scope_revision` | integer | Browser selection revision |
| `discovery` | private object | Complete fetched lists and verified associations |
| `fingerprint` | private digest | Canonical operation, parameters, commands, organization, and target set |
| `confirmation_phrase` | string or null | Server phrase for a change or shell batch |
| `created_at` | timestamp | Server creation time |
| `expires_at` | timestamp | Creation plus 300 seconds |
| `consumed` | boolean | True after successful atomic batch admission |

Sort targets by canonical natural key before computing the fingerprint.
Keep command order exact.
Exclude display labels from the execution fingerprint.
Keep at most five previews per portal authorization scope.
Expire old previews and remove their command text.

`all` selection resolves into explicit targets once.
No admitted batch performs a second expansion.
Changing operation, commands, parameters, scope, or target selection requires a new preview.
An expired or consumed preview cannot start work.
The server must compare the stored fingerprint and authorization scope during admission.
For change and shell batches, require the phrase `RUN <target_count> TARGETS`.
The phrase alone is not sufficient.
Keep the existing Single Site confirmation rule unchanged.

## 3. Target

| Field | Type | Rule |
| - | - | - |
| `target_key` | canonical string | Stable encoding of the natural-key tuple |
| `org_id` | UUID | Current organization |
| `site_id` | UUID or null | Verified site, or null for organization scope |
| `site_label` | string or null | Display text only |
| `target_type` | enum | `organization`, `site`, `device`, `mxedge`, `map`, `asset`, or `client` |
| `target_id` | UUID or normalized MAC | Source identity for the selected target type |
| `device_id` | UUID or null | Verified device scope for device and wired-client work |
| `device_type` | string or null | Catalog-compatible family |
| `map_id` | UUID or null | Required for SDK clients scoped to a map |
| `client_mac` | normalized MAC or null | Required for a MAC-based client target |
| `label` | string | Display text only |

Natural-key tuples include organization, site, target type, resource ID, and required parent IDs.
A client tuple includes its site and associated device or map.
Do not merge identical client MACs from different sites or devices.
Normalize MAC addresses before deduplication.
Never use an array index or display label as target identity.

Validate organization membership, site membership, device family, and resource association.
Reject targets that cannot prove required membership.
An organization-only operation has one organization target with `site_id: null`.
Do not run an organization channel once per site.

## 4. Batch Session and Target Execution

### Batch session

| Field | Type | Rule |
| - | - | - |
| `session_id` | existing session ID | One public session registry entry |
| `mode` | string | `multi_site` |
| `operation` | operation reference | Frozen preview operation |
| `targets` | execution map | One entry per admitted target |
| `status` | enum | Batch status described below |
| `concurrency` | integer | 1 for channel batches; 1 through 5 for utility and shell targets, default 3 |
| `cancel_requested` | boolean | Monotonic false-to-true change |
| `counts` | object | Queued, running, completed, stopped, and failed counts |
| `started_at` | timestamp | Existing session start |
| `ended_at` | timestamp or null | Set once after target termination |
| `output` | output layout | Frozen file selection |
| `artifact_status` | enum | `writing`, `ready`, `partial`, `failed`, or `expired` |

The public session keeps its established lifecycle payload.
The additive `batch.status` carries the richer aggregate outcome.
Do not rename Single Site states.

### Target execution

| Field | Type | Rule |
| - | - | - |
| `target` | target | Frozen identity |
| `state` | enum | `queued`, `running`, `completed`, `stopped`, or `failed` |
| `started_at` | timestamp or null | Set on dispatch |
| `ended_at` | timestamp or null | Set on terminal outcome |
| `reason_code` | string or null | Safe machine-readable cause |
| `result_count` | integer | Count of accepted output records |
| `command_index` | integer or null | Current shell command |
| `completion` | string or null | `collected`, `timeout`, `cancelled`, or `unproven` |

### State transitions

```text
Target:
queued -> running -> completed
queued -> stopped
running -> failed
running -> stopped

Batch:
queued -> running -> completed
queued -> stopping -> stopped
running -> stopping -> stopped
running -> partial
running -> failed
```

`completed` means all targets completed and required artifact writes succeeded.
`partial` means terminal mixed outcomes without an operator cancellation.
`failed` means all targets failed or a required batch service failed.
`stopped` means cancellation ended the batch, including a lifetime or idle stop.
Keep successful target states when a later cancellation occurs.
Keep an `artifact_status: failed` separate from target outcomes.
Never overwrite a first terminal target state with a late callback.

The sum of target counts always equals the admitted target count.
Every admitted target reaches one terminal state.
Cancellation marks queued targets stopped under the dispatch lock.
No queued target starts after that cancellation boundary.
Active targets receive stop signals and release their transport permits.

## 5. Shell Command List

| Field | Type | Rule |
| - | - | - |
| `commands` | ordered string list | 1 through 20 nonempty single-line commands |
| `command_index` | integer | Zero-based position |
| `command_status` | enum | `pending`, `running`, `collected`, `failed`, or `not_run` |
| `output_sequence` | integer | Per-device output order |
| `completion_basis` | string or null | Recognized prompt plus quiet interval |
| `device_exit_status` | integer or null | Null unless the protocol supplies verified status |

Reject embedded line breaks, NUL, and terminal control input in a command.
Enforce UTF-8 byte limits before confirmation.
Do not trim or rewrite an accepted command after confirmation.
Do not persist command text in logs or public audit records.
Keep private command text only while execution requires it.

Wait for initial device output before the first send.
Send the next command only after the prior collection boundary.
On timeout or unproved completion, mark remaining commands `not_run`.
Close the socket on completion, failure, cancellation, idle stop, or lifetime expiry.

## 6. Result Envelope

| Field | Type | Rule |
| - | - | - |
| `schema_version` | integer | 1 |
| `session_id` | string | Public parent ID |
| `seq` | integer | Unique monotonic parent sequence |
| `target_seq` | integer | Monotonic sequence within one target |
| `timestamp` | timestamp | Server observation time |
| `operation` | object | Catalog kind and key |
| `target` | target identity | Organization, site, type, ID, and required parent IDs |
| `record_type` | enum | `output`, `error`, `status`, or `outcome` |
| `command_index` | integer or null | Shell output association |
| `payload` | JSON value | Redacted output or safe structured error |
| `truncated` | boolean | True when collection reached a limit |

The record key is `(session_id, seq)`.
Grouped copies preserve that key.
Do not deduplicate identical payload text.
Identical text can be valid output from different targets or times.
Use one terminal `outcome` record for every target, including targets with no output.
Use the same identity envelope for target errors.

## 7. Output Layout and Manifest

| Field | Type | Rule |
| - | - | - |
| `mode` | enum | `combined`, `grouped`, or `both` |
| `group_by` | enum or null | `site`, `device_type`, `device`, or `client` |
| `artifact_root` | private path | Server-owned directory under `data/` |
| `files` | manifest entries | Opaque file ID, safe relative path, bytes, records, and digest |
| `outcomes` | target summaries | One outcome per admitted target |
| `partial` | boolean | Indicates incomplete collection or writes |
| `expires_at` | timestamp | Existing session retention deadline |

Do not accept an output directory or filename from the operator.
Use stable source IDs in file names.
Keep display labels in the manifest only.
Retain the existing five-ended-session and 600-second limits.
Delete the artifact tree when the session expires or the operator deletes an ended session.
On process restart, remove abandoned session trees through the same safe boundary.
Do not resume a shell or replay commands after restart.

## Relationships

One operation reference belongs to one preview.
One consumed preview creates one batch session.
One batch session owns many target executions and one output layout.
One target execution produces many result envelopes and one terminal outcome.
One manifest indexes every saved file and target outcome.
No child target receives a public session ID.
