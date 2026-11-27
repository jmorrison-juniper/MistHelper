# Data Model: Safe Cisco Input and Structured Review

This model covers the entities that the change adds or changes. It names each natural key or explains each identifier. It also defines the state transitions for the review and for the stored input.

## Entities

| Entity | Fields | Key | Persistence | States |
| --- | --- | --- | --- | --- |
| SourceSelection | origin (`upload` or `stored`), suffix, byte count, SHA-256 digest, name, kind | None. Each request creates one selection. | Memory only | received, validated, rejected |
| StoredInput | identifier, suffix, byte count, creation time (UTC from the modification time) | Identifier. A surrogate key with reason in decision D-5. | One file under `data/cisco_config_converter/input/` when retention is enabled | absent, written, listed, resolved |
| ObservationSection | family key, title, status (`observed` or `not-observed`), items | Family key. The eleven keys are fixed. | Memory only | Built for each response |
| ObservationItem | line, family, label, value, value state (`shown` or `omitted`), status | Family and line, within one source. | Memory only | observed, ambiguous, duplicate, malformed |
| UnsupportedLine | line, command category, reason | Line, within one source. | Memory only | Built for each response |
| ReviewDigest | SHA-256 digest of the canonical proposal JSON | Digest of the proposal | Signed session cookie (existing) | published, reviewed, revoked |

## Identifiers and Natural Keys

- A stored input uses a random identifier from `uuid.uuid4().hex`. Decision D-5 explains why the content digest is not the key. A digest would let a person test whether a known configuration exists in the folder.
- The review digest uses the existing canonical JSON digest in `ReviewState.digest`. The digest binds each field of the proposal.
- An observation item uses the family and the line number as its natural key. The source digest is not stored with the observations.
- Duplicate content gets two identifiers. Each save stays explicit, and no deduplication runs.

## State Transitions

### Review

1. A preview clears any earlier review. The review state becomes `none`.
2. A successful preview publishes the proposal digest. The state becomes `published`.
3. A review request for the same digest changes the state to `reviewed`.
4. An export request requires the `reviewed` state.
5. A change to the selection, name, type, or retain flag clears the review. The state returns to `none`.
6. A failed preview leaves the state at `none`.
7. An observation request changes no state.

Caution: A changed selection clears the review. The operator must preview again before export.

### Stored input

1. The state starts as `absent`.
2. A successful exclusive create and write changes the state to `written`.
3. The catalog lists a written input. The state becomes `listed`.
4. A preview with the identifier resolves the input. The state becomes `resolved`.
5. A failed write removes the created file. The state returns to `absent`.
6. No transition deletes a listed input in this change. Deletion waits for an owner-approved purge task.

## Validation Rules

- A selection must pass the suffix, size, encoding, text, and name rules in `SourceConfiguration`.
- A stored identifier must match `^[0-9a-f]{32}$`.
- A stored file name must be the identifier followed by one of the six allowed suffixes.
- A stored file must be a regular file and must not be a symbolic link.
- A timestamp must use UTC in ISO 8601 form.
