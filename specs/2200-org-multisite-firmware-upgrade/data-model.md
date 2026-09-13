# Data Model: Organization Multi-Site Firmware Upgrade

**Issue**: #2475
**Storage**: Durable portal storage

## 1. Aggregate Operation

One aggregate operation represents one confirmed user action.

| Field | Type | Rule |
| - | - | - |
| `operation_id` | `str` | A durable unique identifier |
| `schema_version` | `int` | The stored model version |
| `owner_id` | `str` | The authenticated user identity |
| `org_id` | `str` | The selected organization |
| `site_ids` | `list[str]` | Unique selected sites in display order |
| `mode` | `str` | `multi_site` |
| `state` | `str` | The aggregate display state |
| `plan_hash` | `str` | A digest of the confirmed child plan |
| `confirmation_at` | `str` | The confirmation time |
| `cancel_requested_at` | `str` or `null` | The first cancel request time |
| `created_at` | `str` | The creation time |
| `updated_at` | `str` | The last durable change time |
| `error` | `object` or `null` | An aggregate error |

The aggregate stores no API token. The aggregate keeps child records as durable
records or embedded durable entries.

## 2. Child Operation

Each child represents one cloud write plan.

| Field | Type | Rule |
| - | - | - |
| `child_id` | `str` | Stable before confirmation |
| `operation_id` | `str` | The owning aggregate |
| `ordinal` | `int` | The confirmed display and submit order |
| `route` | `str` | The exact SDK operation name |
| `scope` | `str` | `org` or `site` |
| `org_id` | `str` | The aggregate organization |
| `site_id` | `str` or `null` | Required for a site route |
| `ui_family` | `str` | `ap`, `switch`, or `gateway` |
| `planned_family` | `str` | `ap`, `switch`, `junos`, or `ssr` |
| `target_ids` | `list[str]` | The immutable target device identifiers |
| `target_macs` | `list[str]` | Optional display identifiers |
| `request_body` | `object` | The confirmed cloud body |
| `status` | `str` | The child submit status |
| `claim_id` | `str` or `null` | The replay prevention token |
| `claimed_at` | `str` or `null` | The first claim time |
| `write_attempts` | `int` | Zero or one |
| `cloud_job_id` | `str` or `null` | The returned cloud identity |
| `raw_status` | `int` or `null` | The cloud HTTP status |
| `error` | `object` or `null` | The submit error |
| `cancel_status` | `str` | The child cancel status |
| `cancel_claim_id` | `str` or `null` | The cancel replay token |
| `cancel_raw_status` | `int` or `null` | The cancel HTTP status |
| `cancel_error` | `object` or `null` | The cancel error |
| `created_at` | `str` | The creation time |
| `updated_at` | `str` | The last durable change time |

## 3. Route Values

| Planned family | Route | Scope |
| - | - | - |
| `ap` | `upgradeOrgDevices` | `org` |
| `switch` | `upgradeSiteDevices` or `upgradeDevice` | `site` |
| `junos` | `upgradeSiteDevices` or `upgradeDevice` | `site` |
| `ssr` | `upgradeOrgSsrs` | `org` |

The data model contains no Mist Edge route.

## 4. Child Submit States

| State | Meaning |
| - | - |
| `planned` | The child has no write claim |
| `claimed` | The durable claim exists |
| `accepted` | The cloud accepted the write |
| `running` | A status read shows active work |
| `complete` | A status read shows completion |
| `failed` | The cloud rejected or failed the write |
| `unknown` | The write can exist, but the result is uncertain |
| `not_submitted` | The sequence stopped before this child claim |

A recovery process treats `claimed` as `unknown` when no final submit result
exists.

## 5. Child Cancel States

| State | Meaning |
| - | - |
| `not_requested` | The aggregate has no cancel request |
| `not_available` | The child has no valid cancel route |
| `cancel_claimed` | The durable cancel claim exists |
| `cancelled` | The cloud accepted the cancel request |
| `cancel_failed` | The cloud rejected the cancel request |
| `cancel_unknown` | The cancel outcome is uncertain |

The `cancelled` state does not mean that firmware returned to an earlier
version.

## 6. Aggregate States

| State | Rule |
| - | - |
| `planned` | All children are `planned` |
| `confirmed` | The plan hash and confirmation exist |
| `submitting` | A child submit sequence is active |
| `running` | Submitted children are active and none need attention |
| `partial` | Children have mixed terminal results |
| `attention_required` | A submit or cancel result is unknown |
| `complete` | Every child completed |
| `cancelling` | A child cancel sequence is active |
| `cancelled` | All cancellable children accepted cancellation |
| `failed` | No child succeeded and no result is unknown |

The aggregate state is a display summary. The child records remain the source
of truth.

## 7. Confirmation Snapshot

The confirmation snapshot contains:

- The organization identifier.
- The ordered site identifiers.
- The selected UI families.
- The target identifiers of each child.
- The route and scope of each child.
- The firmware options of each child.
- The warnings.

The server creates `plan_hash` from a canonical form of this snapshot. A submit
request must match the stored hash.

## 8. Claim Rules

The store uses an atomic conditional update.

For a submit claim:

1. The child status must be `planned`.
2. The child claim must be empty.
3. The store writes the claim and increments `write_attempts`.
4. The value of `write_attempts` must become one.

For a cancel claim:

1. The child must have a submitted cloud identity or a valid cancel context.
2. The cancel state must be `not_requested`.
3. The cancel claim must be empty.
4. The store writes one cancel claim.

A failed conditional update sends no cloud request.

## 9. Ownership and Scope Rules

- The authenticated user must equal `owner_id`.
- The active organization must equal `org_id`.
- Every `site_id` must belong to `org_id`.
- Every target must belong to its recorded site and organization.
- Every site route must hold a `site_id`.
- Every organization route must hold the aggregate `org_id`.
- Every required site lock must belong to the owner and operation.

## 10. Error Shape

```json
{
  "code": "upgrade_outcome_unknown",
  "message": "The cloud write outcome is unknown.",
  "stage": "submit",
  "retryable": false,
  "observed_at": "2026-09-11T19:00:00Z"
}
```

The model stores no secret, cookie, authorization header, or CSRF token.
