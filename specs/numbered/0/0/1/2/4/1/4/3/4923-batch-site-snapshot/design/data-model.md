# Data Model: Batch target site snapshot

## Entity: Organization site snapshot

- **Owner**: One `BatchTargetPickerService` for one organization.
- **Natural key**: The organization identifier that the picker uses.
- **Fields**:
  - `picker`: the `StreamPickerService` that reads Mist for the organization.
  - `rows`: the complete list of site rows, or no value when the snapshot is absent.
  - `read_at`: the monotonic clock time of the last successful refresh.
  - `lock`: one `threading.Lock` that guards `refresh` and `rows`.
- **Invariants**:
  - Rows exist only after a successful refresh.
  - `read_at` holds the time of the refresh that set the rows.
  - Callers receive copies of the rows, never the stored list.

## Entity: Site row

- **Natural key**: `id`, the site identifier from Mist.
- **Fields used by the site check**: `id`, `label` (from `name`), and `detail` (from the address fields). The fields come from `ResourcePicker.sites` (`resources.py`, starting at line 71).
- **Relationship**: Each site row belongs to exactly one organization snapshot.

## States of the organization site snapshot

| State | Meaning | Entry condition |
| - | - | - |
| absent | No rows exist. | The service starts, a refresh fails, or the portal restarts. |
| fresh | Rows exist and are 300 seconds old or younger. | A successful refresh finishes. |
| expired | Rows exist and are older than 300 seconds. | Time passes after a fresh state. |

## State transitions

| From | To | Trigger |
| - | - | - |
| absent | fresh | A successful refresh from a discovery or from a site check. |
| fresh | fresh | A discovery refresh replaces the rows and resets `read_at`. |
| fresh | expired | Time passes beyond 300 seconds. |
| expired | fresh | A site check triggers a successful refresh. |
| fresh or expired | absent | A refresh fails. The rows are cleared, and the error is raised. |

## Outcomes of a site check

| Outcome | Condition | Result |
| - | - | - |
| member | The site identifier is in the rows. | The resource read starts. |
| non-member | The site identifier is not in the rows. | The check raises `bad_request` with the sentence "The site is not part of this organization." |
| read failure | The refresh raises an error. | The check raises the picker error. No rows are returned. |

## Natural keys and identifiers

- The site snapshot has no artificial identifier. Its natural key is the organization identifier of its picker.
- The change adds no table, file, or database record.
