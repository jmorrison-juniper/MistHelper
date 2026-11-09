# Data Model: Upgrade Lock Retention

This change uses existing operation records. It adds no field, table, or migration.

## Operation Child

- `status`: The existing child state. A confirmed refusal remains `rejected`. An unaccepted response without refusal proof becomes `submission_unknown`.
- `raw_status`: The existing HTTP status value. The shared refusal rule accepts only integer values from 400 through 499.
- `upgrade_id`: The existing cloud job identity. A valid accepted response requires the identity expected by the existing route.
- `cloud_status`: The existing status read result. It distinguishes a reported cloud job state from an unaccepted submission response.

## Site Lock

- `site_locks`: The existing map of site identifiers to lock records.
- Release condition: Every child has a proven terminal write state, every rejected submission has refusal evidence or a known cloud status, and the existing phase watch is final.
- Uncertain condition: An ambiguous submission remains unsettled. The existing lock lease and read behavior remain unchanged.

## State Transitions

```text
accepted response with valid identity -> accepted
unaccepted response with HTTP 4xx      -> rejected
other unaccepted response              -> submission_unknown
submission_unknown                      -> remains unsettled under current behavior
known final cloud status                -> existing final-state handling
```
