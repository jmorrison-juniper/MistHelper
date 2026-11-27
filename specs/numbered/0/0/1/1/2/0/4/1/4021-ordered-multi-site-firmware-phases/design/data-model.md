# Data Model: Ordered Multi-Site Firmware Families

This model describes the durable parent record that the aggregate service writes. It adds three fields. The change adds no collection and no index.

## Entities

### Parent Record

- **Natural key**: `operation_id`, a string that starts with `org-run-`. The key also appears as `run_id` for the store (row 1 context in `design/research.md`).
- **Fields**: `state`, `record_version`, `children`, `site_names`, `site_locks`, `family_gates`, `family_wait_refreshed_at`, `family_stop`, `cancellation`, `errors`, `created_at`, `updated_at`.
- **Change**: Add `family_gates`, `family_wait_refreshed_at`, and `family_stop`. The other fields keep their current meaning.
- **Rule**: `record_version` increases by one for each accepted write. A write with a stale version is refused.

### Child

- **Natural key**: `child_id`, a string that starts with `child-`. The cloud identity is `upgrade_id`. The site identity is `site_id`. The device identity is the MAC address in `target_ids`.
- **Fields**: `route`, `scope`, `org_id`, `site_id`, `device_family`, `upgrade_id`, `status`, `raw_status`, `error`, `targets`, `body`, `submission_claim_id`, `submission_claimed_at`.
- **Change**: No new field. The `device_family` of an SSR child stays `ssr`. Its family rank is `gateway` (decision D-1).

### Family

- **Natural key**: the family name `gateway`, `switch`, or `ap`. Clients have no family in the submission model.
- **Fields**: the rank, the children list, and the gate result.
- **Rule**: The rank order is `gateway`, then `switch`, then `ap`. The rank reads `upgrade_service.PLAN_FAMILY_ORDER` (row 9 in `design/research.md`).

### Family Gate Result

- **Natural key**: the pair of `operation_id` and family name. The record holds at most one result for each family.
- **Fields**: `state` (`settled`, `failed`, or `unknown`), `not_returned` (a count), `recorded_at` (UTC ISO 8601 text).
- **Rule**: A result replaces no earlier result. A second result for one family is refused.

### Family Stop

- **Natural key**: the `operation_id`. The record holds at most one stop.
- **Fields**: `family`, `reason_code`, `child_ids`, `gate_state`, `sentence`, `stopped_at`.
- **Rule**: A stop is one-way. After a stop, the run writes no firmware and accepts no new family.

## Family Gate States

The states of one family follow this order.

```text
pending -> submitting -> waiting -> settled
                     \-> stopped
pending -> skipped          (no child in the family)
```

- `pending`: The family has children and the run has not reached it.
- `submitting`: The parent claim covers the family send.
- `waiting`: The parent claim is released. The family gate runs. The wait marker refreshes every 20 seconds.
- `settled`: The gate returned `settled`. The next family may start.
- `stopped`: A stop record names the family. No later family starts.
- `skipped`: The family has no child. It records no gate call.

## Child States

```text
planned -> submission_claimed -> accepted
                              -> rejected            (proven refusal)
                              -> submission_unknown  (unknown outcome)
planned -> not_submitted                             (stop before the child claim)
submission_claimed -> submission_unknown             (stale claim, no resend)
```

- `planned`: No cloud call left the portal.
- `submission_claimed`: One cloud call is in progress for this child.
- `accepted`: The cloud accepted the child and returned an identity.
- `rejected`: The cloud refused the child. The family and every later family stop.
- `submission_unknown`: The cloud reply cannot prove acceptance or refusal. The run stops. The child never resends.
- `not_submitted`: The run stopped before the child claim. No cloud call occurred.

## Parent States

- `planned`: The record exists, and no family is sent.
- `submission_claimed`: The parent claim covers one family send.
- `family_waiting`: The parent claim is released. A family gate wait runs. The status page shows this state as `running`.
- `running`, `partial`, `completed`, `cancelled`, `failed`: Existing aggregate states (rows 1 to 8 context).
- `attention_required`: A stop record exists. The operator reads the record before any new action.

## Validation Rules

- The record stores each accepted family gate result before the next family starts.
- The record stores the stop record before the background run ends.
- A process restart reads the stored state. A stale wait marker produces a `process_lost` stop. No child receives a new cloud call.
- The site locks stay in `site_locks` until a final state (row 87 in `design/research.md`).
