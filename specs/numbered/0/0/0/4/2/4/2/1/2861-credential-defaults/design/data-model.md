# Data Model: Credential default audit

## Entities

- **Candidate**: One Python expression that supplies a default for a credential-bearing name. Natural key: path, enclosing scope, kind, and fingerprint. Line is informational.
- **Baseline entry**: One reviewed candidate in the candidate section, or one reviewed candidate in the accepted section. Fields: path, scope, kind, fingerprint, group, and reason. Reason is required in the accepted section.
- **Database credential field**: One field of `DatabaseConfig`. Natural key: field name. Allowed value: empty string, or a value that is not in `_KNOWN_SAMPLE_CREDENTIALS`.
- **Credential source**: One ordered input for a Mist token. Natural key: source name. Order for the command line is the canonical environment name, the legacy environment name, then a terminal prompt.
- **Refusal**: One stop of a run with status 1. Fields: reason name and affected variable names. A refusal never includes a value.

## State Transitions

- **Candidate**: `open` moves to `accepted` when the group is B or C and the reason is recorded. `open` moves to `removed` when the fix removes the expression. A removed entry leaves the candidate section in the same change.
- **Database credential field**: `default-literal` moves to `empty` in batch 1. `empty` stays `empty` after a standalone load.
- **Token source**: `unread` moves to `usable` or `rejected` after a read. `rejected` never becomes `usable` in the same run.
