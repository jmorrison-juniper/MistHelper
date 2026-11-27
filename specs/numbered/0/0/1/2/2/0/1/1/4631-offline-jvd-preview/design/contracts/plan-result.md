# Contract: Plan Result

## Source

The planner returns one object. The gateway passes that object to the projector. The projector accepts or rejects it. No other code reads the raw object.

## Input Shape

The input object holds exactly these keys:

| Key | Type | Rule |
| - | - | - |
| `logical_devices` | list of objects | Each object holds exactly `id` and `label`. |
| `links` | list of objects | Each object holds exactly `a_end` and `z_end`. |

Device rules:

- `id` matches `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`.
- `label` holds 1 to 80 printable ASCII characters.
- Each `id` appears once in the list.

Link rules:

- `a_end` and `z_end` each name an `id` from `logical_devices`.
- Each ordered pair appears once in the list.

## Reject Rules

The projector rejects the whole result when one rule fails. It shows no rows.

| Rule | Reason code |
| - | - |
| A key other than `logical_devices` and `links` appears | `unexpected_key` |
| A key in the authority list appears | `authority_claim` |
| A device id repeats, a link names an unknown device, or a value has the wrong type | `contract_violation` |

Authority list: `execution_authority`, `execute`, `deploy`, `deployment`, `provider`, `provider_access`, `credentials`, `apply`.

Authority matching uses the key name alone. A key in this list rejects the result even when its value is `false`.

## Output Shape

The projector returns the same two lists and one added field:

| Field | Value |
| - | - |
| `logical_devices` | Each device with `id` and `label` only, sorted by `id` |
| `links` | Each link with `a_end` and `z_end` only, sorted by `a_end`, then `z_end` |
| `fingerprint` | `sha256:` and the hex digest described in `data-model.md` |

## Evidence

- `test_projector_keeps_only_devices_and_links` (TU-03).
- `test_projector_rejects_unexpected_key` (TU-04).
- `test_projector_rejects_authority_claim_key` (TU-05).
- `test_projector_rejects_link_to_unknown_device` (TU-06).
- `test_fingerprint_matches_canonical_sha256` (TU-07).
- `test_fingerprint_ignores_input_order` (TU-08).
