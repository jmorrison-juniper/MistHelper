# Contract: Restore Decisions

## Inputs

- One verified `BackupManifest` for one object family, as defined in `design/data-model.md`.
- The current listing of that family for the organization, read across all pages.
- One current read for each backup ID that appears in the listing, or that a read confirms as absent.
- The list of overrides that an operator recorded. Each override names one backup object ID.

## Outputs

- One `ObjectDecision` for each backup object.
- One `ObjectDecision` with decision `preserve` for each current object that has no backup entry.
- The ordered write list. It holds the decisions `create` and `update` only.
- The proposal digest and the scope digest.
- The write count. A count above 100 refuses the proposal (decision D-15).

## Rule order

The first rule that matches wins.

1. If the manifest fails validation, refuse the proposal. Make no decision.
2. If the backup ID is absent from the current listing:
   - A read of the ID that returns a status other than 404 gives `conflict` with `lookup-unavailable`.
   - A current object with the same name gives `conflict` with `duplicate-name`.
   - A reference that does not resolve gives `conflict` with `unresolved-reference`.
   - Otherwise the decision is `create` with `absent-free-name`.
3. If the backup ID is present:
   - A current organization that differs gives `conflict` with `wrong-organization`.
   - A read that fails gives `conflict` with `lookup-unavailable`.
   - Equal normalized digests give `unchanged` with `identical`.
   - Different normalized digests with a recorded override give `update` with `override-recorded`.
   - Different normalized digests without an override give `conflict` with `changed-after-backup`.
4. If a current object has no backup entry, give `preserve` with `absent-from-backup`. The object is never written and never deleted.

## Digests

- A normalized digest is the SHA-256 hex digest of the canonical JSON of the normalized body (`design/data-model.md`, Conventions).
- The proposal digest covers the ordered list of `family`, `backup_object_id`, `current_object_id`, `decision`, `override`, `before_digest`, and `target_digest` for each decision.
- The scope digest covers the `organization_id`, the `source_backup_id`, the ordered write list, and the sorted overrides.
- A change to any covered field changes the digest. A changed digest invalidates an approval (decision D-21).

## Order of writes

The ordered write list sorts the decisions in this order:

1. Family: `network`, then `service`, then `service-policy` (decision D-12).
2. Natural ID: ascending, within each family.

## Duplicate names

A duplicate name is an exact match between the backup name and a current object name in the same family. The comparison uses the stored string without case changes. Unverified item U-6 covers the Mist rule. A duplicate gives a conflict. The only resolution is exclusion from the proposal (decision D-10).

## References

For each `service-policy`, each value in `services` and `tenants` must resolve. For each `network`, each value in `routed_for_networks` must resolve. A value resolves when it equals the name of a current object in the same family. It also resolves when it equals the name of an object earlier in the ordered write list. Unverified item U-1 covers the meaning of these values. An unresolved value gives a conflict for the object that holds it.

## Overrides

- An override names one backup object ID.
- An override applies only under rule 3d. An override on any other decision is refused with `invalid_request`.
- Each override enters the proposal digest and the scope digest.
- An override does not permit a delete. Deletion needs decision D-20.

## Safety

- The decision function makes no write call. It reads only.
- The decision function refuses an unknown decision value.
- The decision function returns the same output for the same inputs. The tests compare two runs.
