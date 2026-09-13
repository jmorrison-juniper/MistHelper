# API Contract: Organization Multi-Site Firmware Upgrade

**Issue**: #2475
**Scope**: Portal routes and Mist child routes

## 1. Source Conflict

The OpenAPI description for
`POST /api/v1/orgs/{org_id}/devices/upgrade` states that the operation supports
AP upgrades only.

The request schema permits `device_type` values `ap`, `switch`, and `gateway`.
It permits `versions[].firmware_type` values `ap` and `junos`.

The saved organization guide shows an AP version and a Junos switch version in
one request. The saved example also contains invalid JSON syntax.

The portal follows the AP-only description for this organization endpoint.

## 2. Mist Child Routes

| Child family | SDK operation | Scope | Path |
| - | - | - | - |
| AP | `upgradeOrgDevices` | Organization | `POST /api/v1/orgs/{org_id}/devices/upgrade` |
| Switch batch | `upgradeSiteDevices` | Site | The documented site device upgrade path |
| Switch single | `upgradeDevice` | Site | The documented site device path |
| Junos gateway batch | `upgradeSiteDevices` | Site | The documented site device upgrade path |
| Junos gateway single | `upgradeDevice` | Site | The documented site device path |
| SSR gateway | `upgradeOrgSsrs` | Organization | The documented organization SSR upgrade path |

`src/firmware/upgrade_service.py` selects each site route. It also selects the
organization SSR route after gateway classification.

The contract defines no Mist Edge child route.

## 3. Organization AP Body

The AP child uses one request for the selected AP sites.

```json
{
  "all_sites": false,
  "device_type": "ap",
  "site_ids": [
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222"
  ],
  "versions": [
    {
      "firmware_type": "ap",
      "version": "0.14.29538"
    }
  ],
  "strategy": "canary",
  "canary_phases": [1, 10, 50, 100]
}
```

### AP body rules

- `all_sites` must be false.
- `device_type` must be `ap`.
- `site_ids` must contain the selected AP sites only.
- Every version record must use `firmware_type` `ap`.
- The body must not contain a Junos version record.
- The body must not contain a switch or gateway target.

## 4. Site and SSR Bodies

The portal does not create new switch, Junos gateway, or SSR body rules.

It calls the existing planner in `src/firmware/upgrade_service.py`. The portal
stores the returned route and body without a family change.

The child record must keep the planned target identifiers. The service must
send the stored confirmed body.

## 5. Portal Operation Routes

The portal keeps one resource for the aggregate operation.

| Method and path | Purpose |
| - | - |
| `POST /api/org-upgrade-operations` | Create the durable aggregate plan |
| `GET /api/org-upgrade-operations/<operation_id>` | Read aggregate progress |
| `POST /api/org-upgrade-operations/<operation_id>/confirm` | Store the confirmed plan |
| `POST /api/org-upgrade-operations/<operation_id>/start` | Submit unclaimed children |
| `POST /api/org-upgrade-operations/<operation_id>/cancel` | Request child cancellation |

The implementation can preserve compatible existing paths. Each path must use
the same durable aggregate and replay rules.

## 6. Create Answer

```json
{
  "operation_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "state": "planned",
  "children": [
    {
      "child_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      "ui_family": "ap",
      "planned_family": "ap",
      "scope": "org",
      "route": "upgradeOrgDevices",
      "site_id": null,
      "target_ids": ["00000000-0000-0000-0000-000000000001"],
      "status": "planned"
    }
  ]
}
```

The answer includes every child before confirmation.

## 7. Start Request

```json
{
  "confirmation": "CONFIRM",
  "plan_hash": "<confirmed-plan-digest>"
}
```

The browser also sends the required CSRF header or form token.

### Start checks

The route verifies:

1. The authenticated owner.
2. The active organization.
3. Every selected site.
4. Every target.
5. Every required site lock.
6. The stored plan hash.
7. The exact confirmation text.
8. The CSRF token.

The route rejects a stale plan or a replay before a cloud write.

## 8. Start Answer

```json
{
  "operation_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "state": "attention_required",
  "children": [
    {
      "child_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      "status": "accepted",
      "cloud_job_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
      "raw_status": 200,
      "error": null
    },
    {
      "child_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
      "status": "unknown",
      "cloud_job_id": null,
      "raw_status": 0,
      "error": {
        "code": "upgrade_outcome_unknown",
        "retryable": false
      }
    },
    {
      "child_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
      "status": "not_submitted",
      "cloud_job_id": null,
      "raw_status": null,
      "error": null
    }
  ]
}
```

The answer preserves partial submission. It does not convert `unknown` to
failure.

## 9. Cancel Request

```json
{
  "confirmation": "CANCEL"
}
```

The route checks ownership, organization, plan identity, and CSRF protection.

The service claims each cancel action before the cloud call. It sends no retry.

## 10. Cancel Answer

The answer includes every child cancel state. A child can be `cancelled`,
`cancel_failed`, `cancel_unknown`, or `not_available`.

The answer must state that cancellation does not restore installed firmware.

## 11. Error Envelope

```json
{
  "code": "operation_replay_blocked",
  "message": "The child already has a write claim.",
  "details": {
    "operation_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "child_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
  }
}
```

Expected refusal codes include:

- `operation_not_owned`
- `organization_mismatch`
- `site_not_in_organization`
- `target_not_in_site`
- `site_locked`
- `lock_store_unreachable`
- `confirmation_required`
- `confirmation_stale`
- `csrf_invalid`
- `operation_replay_blocked`
- `mist_edge_not_supported`
- `upgrade_outcome_unknown`
- `cancel_outcome_unknown`

## 12. Write Rules

- Each child has no more than one submit claim.
- Each child has no more than one cloud write attempt.
- Each child has no more than one cancel claim.
- The SDK and transport use zero write retries.
- An uncertain write remains `unknown`.
- A read operation can reconcile an unknown outcome.
- A browser refresh cannot send a write.
