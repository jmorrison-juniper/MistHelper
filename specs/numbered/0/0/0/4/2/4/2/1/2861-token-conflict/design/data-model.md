# Data Model: Mist Token Environment Values

## Token Environment Input

The input has two optional values:

- `MIST_API_TOKEN`: The canonical token variable.
- `MIST_APITOKEN`: The legacy migration variable.

Each value becomes an ordered list after comma and newline splitting and whitespace removal.

## Validation Rules

- A missing or empty normalized list is absent.
- One non-empty list is usable.
- Two equal non-empty lists are accepted during migration.
- Two different non-empty lists cause a refusal before session or organization lookup.
- Error text may name variable names. Logs must contain no token characters.

## Result

Credential validation returns either one selected token list or a refusal reason. A refusal never produces a Mist session.
