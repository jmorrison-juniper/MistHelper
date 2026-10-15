# Data model: Firmware policy inspection

## Comparison

One comparison has `scope`, `id`, `snapshot_at`, optional `observed_at`,
`proposed_from`, normalization notices, and a bounded `fields` array.
Restoration distinguishes its source snapshot from its recovery snapshot.

## Field

Each field has a supported path and saved/current/proposed cells.
A cell has `present` and, only when present, `value`.
Difference flags compare presence as well as values.
Policy state rows distinguish missing organization policy, inherited site policy,
empty policy, enabled policy, disabled policy, and unspecified enablement.

## Storage and state

Complete dictionaries remain in existing private contexts and bundles.
Comparison responses are not persisted in job records or browser storage.
Ready inspection does not consume tokens or proofs.
Pending, ready, and uncertain preparation states lock the preparation control.
Definite preparation failure permits an explicit retry.
