# Data Model: History Organization Isolation

**Feature**: [spec.md](spec.md)

## Model Boundary

This repair changes read scope only.
It creates no collection, schema, persisted field, migration, database key, or lock key.
Existing retention, backup, recovery, and persistence behavior remain unchanged.

The scope described below is a transient request concept.
It does not require a new persisted model or public class.

## 1. Operator Session and Request Scope

| Existing value | Source | Rule |
| --- | --- | --- |
| Current operator session | `identity.current_session()` | The current signed session and browser cookie must identify an active registry record. |
| Selected organization | `select.resolve_org(None)` | Read the signed `selected_org_id`, not a request-supplied organization. |
| Normalized organization | Existing string, after `strip()` | A nonempty string is required. Incorrect types, empty strings, and whitespace are missing selections. |
| Permitted organizations | `identity.permitted_org_ids()` | A known set requires membership. A known empty set permits nothing. |
| Unavailable privileges | `None` from the identity authority | Preserve the current environment-token policy. Do not turn this value into a known empty set. |
| Requested site | Existing path value or history query value | An empty site means every matching site within the selected organization. |
| Page window | Existing limit and offset readers | Preserve current defaults and bounds. |

One request uses one selected organization.
The site restriction narrows that organization.
It does not select or authorize another organization.

### Scope states

| State | Next action | Source reads |
| --- | --- | --- |
| No active sign-in | Return the existing sign-in refusal or HTML redirect. | Zero. |
| No valid selection | Return `400 org_not_chosen`. | Zero. |
| Selection outside known privileges | Return `403 org_not_permitted`. | Zero. |
| Explicit selection permitted by current policy | Read matching history with the optional site restriction. | Scoped reads only. |
| Valid scope with no matching records | Return the existing empty result. | No unrestricted retry. |

Each later page request repeats the current authorization decision.
The repair adds no persisted authorization cache.

## 2. Capture History

| Existing field or value | Meaning | Read rule |
| --- | --- | --- |
| `capture_id` | Existing capture identifier. | Preserve the identifier and database key. |
| `org_id` | Organization attribution. | Must equal the selected organization. |
| `site_id`, `site_name` | Site attribution and display label. | Apply the optional site restriction before count and pagination. |
| `started_at`, `finished_at`, `duration_seconds` | Stored capture moments and duration. | Preserve current values and ordering. |
| `role`, `capture_status`, schema fields | Capture role, state, and compatibility fields. | Preserve existing shapers and compatibility rules. |
| `actor_email`, `counts`, `stored_size_bytes` | Existing operator, count, and size values. | Display matching records only. |

`CaptureQuery` already contains `org_id`, `site_id`, `run_id`, `limit`, and `offset`.
The adapter must fill `org_id`.
The repair adds no query field.

`CaptureListPage.total` counts all matching captures before the page window.
Its `captures` contain matching records in the existing descending `started_at` order.
Records with missing or mismatched `org_id` do not match.

## 3. Run History

| Existing field or value | Meaning | Read rule |
| --- | --- | --- |
| `run_id` | Existing run identifier. | Preserve the identifier and database key. |
| `org_id`, `site_id`, `site_name` | Organization and site attribution. | Apply organization and optional site before count and pagination. |
| `created_at`, `updated_at`, `state` | Run moments and state. | Preserve ordering, stale assessment, and terminal-state behavior. |
| `actor_email`, `cloud_account` | Existing operator and account labels. | Exclude foreign labels from the complete response. |
| `pre_capture_id`, `post_capture_id` | Existing capture references. | Preserve matching links and exclude foreign references. |
| `device_count` | Existing projected target count. | Preserve the current projection and displayed count. |

`RunQuery` already contains `org_id`, `site_id`, `actor_email`, `limit`, and `offset`.
The adapter must fill `org_id`.
The repair adds no query field.

`RunListPage.total` counts matching single-site runs before pagination.
The current query excludes aggregate operation records.
Keep that exclusion.
Keep descending `created_at` ordering.

## 4. Multi-site Operation History

| Existing field | Relationship or meaning | Read rule |
| --- | --- | --- |
| `operation_id`, `org_id` | Operation identifier and organization. | Read only the selected organization. |
| `site_ids`, `site_names` | Sites included in the operation. | A requested site must belong to `site_ids`. |
| `created_at`, `updated_at`, `state` | Operation moments and state. | Keep the current ordering and presentation. |
| `actor_email`, `cloud_account`, `families` | Existing display values. | Return matching operation values only. |
| `owner` | Browser-session owner key. | Use it on the server for progress-link ownership. Never output the key. |

An operation can reference multiple sites within its stored organization.
Permission for another organization does not include its operations in this request.

`OperationQuery` already requires `org_id`.
The validated selection reaches `OrgOperationHistory` and the existing operation lister.
Another browser session's same-organization operation remains visible without an owner-only progress link.

## 5. Audit Events

### Stored records

| Existing field | Meaning | Scope rule |
| --- | --- | --- |
| `org_id`, `site_id` | Organization and site attribution. | Match the selected organization and optional site before inference. |
| `action` | `take`, `release`, `takeover`, or `expire`. | A missing action keeps the legacy takeover meaning. |
| `occurred_at` | Stored event moment. | Preserve trail order rather than sorting moment text. |
| `actor_email` | Stored operator address. | Never include it in an audit response. |
| `previous_actor_email` | Previous holder's stored address. | Never include it in an audit response. |

The reader excludes records without matching organization attribution.
It does not infer ownership from site text.

### Existing output fields

The audit output remains:

- `action`
- `site_id`
- `org_id`
- `occurred_at`
- `actor_digest`
- `previous_digest`
- `inferred`

The page still adds `moment_text` through the existing shaper.
The current one-way digest rule remains unchanged.
No credential or stored audit address reaches output.

### Inference state

The transient holder map uses `(org_id, site_id)`.
Each entry contains the earlier record that opened that sequence's hold.
This grouping tuple is not a persisted primary key or a lock key.

| Current matching hold | Matching action | Inferred output | Next hold |
| --- | --- | --- | --- |
| None | `take` | No expiry. | Current take. |
| Take or takeover | `take` | One expiry immediately before the take. | Current take. |
| Any | `takeover` or legacy missing action | No expiry. | Current takeover. |
| Any | `release` or `expire` | No new expiry. | None. |
| Any | Other closing action | Keep the existing closing behavior. | None. |
| Any | Foreign or out-of-site event | No output or state change for the matching sequence. | Unchanged. |

An inferred expiry retains the earlier hold's organization, site, and actor.
Its moment is the later matching take's moment.
The existing audit shaper turns that earlier actor into the output digest.

### Result limits

For positive limits, the reader retains only matching output rows in its bounded deque.
It still scans the complete matching sequence for earlier context.
Foreign rows do not consume positions.

For the legacy path, inference uses the complete scoped sequence before the final slice.
Preserve the existing zero, negative, and `None` slice meanings.
Both paths return newest-first results.

## Synthetic Validation Relationships

Organization A contains Sites A1 and A2.
Organization B contains Site B1.
Captures and single-site runs reference one site.
Operations reference one or more sites.
Audit records reference one organization-and-site sequence.

Include records without organization attribution.
Include reused site text across the two organizations.
Keep each foreign content sentinel distinct from all selected records.
Expected counts and events must not come from the production result shaper.

See [contracts/history-scope.md](contracts/history-scope.md) for response obligations.
See [quickstart.md](quickstart.md) for validation scenarios.
