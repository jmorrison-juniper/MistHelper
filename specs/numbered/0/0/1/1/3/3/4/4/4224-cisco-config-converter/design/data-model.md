# Data Model: Integrate Mist Cisco Config Converter

This model lists the converter entities, their natural keys, their validation, and their state changes. The child records own the detailed field lists. Each entity uses a natural key from the Mist API or a content digest. No entity uses an artificial sequence.

## Entities

| Entity | Natural key | Fields | Validation | Storage |
|---|---|---|---|---|
| Source Configuration | SHA-256 digest of the uploaded bytes | Display name, byte count, suffix, digest, received time in UTC | Six suffixes. At most 16 MiB. Strict UTF-8. No null character. No path-like name. | Memory only (D-8) |
| Conversion Proposal | SHA-256 digest of the canonical proposal | Template name, template type, DNS servers, gateway role, hardware model, unsupported items, known gaps, verification state | Template name has 1 to 120 visible characters (R-37). Template type is `standalone` or `spoke` (R-75). | Memory, and the digest in the signed session (R-39) |
| Review Record | Proposal digest | Reviewed flag, review time in UTC, expiry 15 minutes after review | The digest must match the current proposal | Signed session |
| Approval Record | Organization identifier and change-set digest | Site identifiers, gateway identifiers, typed word, issue time in UTC, expiry 15 minutes after issue, used flag | The typed word must match exactly. One use only. | Private file under `data/` (D-7) |
| Write Family | Family identifier F-01 to F-08 | Enabled flag, gate G2 status, gate G4 status, gate G5 status | Enabled flag defaults to false. Enabling needs the decision in D-15. | Configuration record |
| Operation Run | Run identifier | Family, object natural keys, start time in UTC, end time in UTC, outcome for each object | Each write has a 90-second bound. Each run has a 10-minute bound. | Private file under `data/` |
| Backup Record | Organization identifier, family, and object identifier | Checksum, page count, page total header, manifest version, UTC creation time | Complete pagination is required. An invalid manifest blocks recovery. | `data/.cisco-config-converter-backups/` (D-7) |
| Mist Target | Organization identifier, site identifier, and gateway template identifier | Name, assigned gateway identifiers | Read from lookup only. Lookup never creates a target. | Not stored |

## Natural Keys and Identifiers

- Mist objects use identifiers from the Mist API. Source uploads use a SHA-256 digest.
- Proposal and review records use the same digest function. The digest changes when the proposal changes.
- Run outcomes use the object natural key and the run identifier. A duplicate submission returns the existing run.

## State Transitions

Preview path:

```text
uploaded -> validated -> parsed -> proposal_ready -> reviewed -> exported
```

- Invalid input stops before `validated`.
- A proposal with no supported DNS value omits the DNS field.
- Unsupported items remain in every later state.

Apply path:

```text
reviewed -> approved -> running -> completed
                                -> partial
                                -> failed
                                -> indeterminate
```

- `approved` needs the typed word APPLY within 15 minutes.
- `failed`, `partial`, and `indeterminate` stop every later write in the run.
- An `indeterminate` write is never retried automatically.

Recovery path:

```text
backup_verified -> restore_planned -> approved -> running -> completed
                                                           -> partial
                                                           -> indeterminate
```

- A missing or incomplete backup stops at `backup_verified`.
- Recovery needs a fresh approval for each action.

Invalidation:

- A change to the source, the model, the role, the target, or the proposal moves `reviewed` or `approved` back to `proposal_ready`.
- An expired approval moves to `expired` and cannot return to `approved`.

Warning: a run that reaches `indeterminate` can leave a production change in an unknown state. Check the Mist object before any new run.
