# Phase 1 Data Model: getOrgAosRegisterCmd

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_aos_register_cmd.md` (200 OK body):

```json
{
  "type": "object",
  "properties": {
    "cli_commands": {
      "type": "string",
      "description": "AOS-specific CLI commands that can be copied and pasted directly into an AOS device to register it with Mist. Includes registration code and configuration commands."
    }
  },
  "description": "AOS Brownfield Registration Commands"
}
```

## Entities

The endpoint returns a single JSON object with one string property describing a
time-sensitive registration command block. MistHelper persists this as a single
flattened entity, augmented with caller-side context (org and poll timestamp).

### Entity: `AosRegisterCommand`

One row per invocation of the endpoint. Each invocation produces a fresh, distinct
command (the registration challenge token is time-sensitive per the enriched doc),
so successive invocations against the same org append historical rows rather than
upsert in place.

| Field                    | Type     | Source                | PK?       | FK?           | Notes |
|--------------------------|----------|-----------------------|-----------|---------------|-------|
| `misthelper_internal_id` | INTEGER  | SQLite ROWID          | YES (surrogate) | --      | Auto-increment surrogate primary key. |
| `org_id`                 | TEXT     | MistHelper context    | UNIQUE(2) | sites.org_id  | UUID supplied by user; injected before write. |
| `generated_at_utc`       | TEXT     | MistHelper clock      | UNIQUE(2) | --            | ISO8601 UTC timestamp at which MistHelper invoked the endpoint. Pair `(org_id, generated_at_utc)` is unique. |
| `cli_commands`           | TEXT     | API `cli_commands`    | --        | --            | Raw AOS CLI command block returned by Mist. Time-sensitive registration token. **Never logged.** |
| `cli_commands_length`    | INTEGER  | len(API `cli_commands`) | --      | --            | Convenience length for observability and DataExporter logs (the only field summarizing the command that may be safely logged). |
| `mist_host`              | TEXT     | `os.environ["MIST_HOST"]` | --    | --            | Mist API host the request was made against (e.g., `api.mist.com`). Helps disambiguate multi-region deployments. |
| `http_status_code`       | INTEGER  | `response.status_code`| --        | --            | HTTP status from the SDK response (200 on success, 404 if org has no AOS context, etc.). |

The `(org_id, generated_at_utc)` UNIQUE constraint is the de-dup guard described in
Research Task 2. The surrogate `misthelper_internal_id` is the PK so that the legal
case of multiple historical rows for the same org can coexist.

## State Transitions

N/A -- this is a read-only endpoint with no state machine on the MistHelper side.
The underlying AOS device transitions through its own onboarding state when an
operator pastes `cli_commands` into the device CLI, but MistHelper does not observe
or model those transitions; it merely captures the issued command snapshot. Each
invocation appends a new historical row.

## SQLite DDL

```sql
-- One row per invocation of getOrgAosRegisterCmd.
-- Surrogate PK + UNIQUE(org_id, generated_at_utc) per Research Task 2.
CREATE TABLE IF NOT EXISTS org_aos_register_cmd (
    misthelper_internal_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id                  TEXT     NOT NULL,
    generated_at_utc        TEXT     NOT NULL,
    cli_commands            TEXT,
    cli_commands_length     INTEGER,
    mist_host               TEXT,
    http_status_code        INTEGER,
    UNIQUE (org_id, generated_at_utc)
);

CREATE INDEX IF NOT EXISTS idx_aos_register_cmd_org
    ON org_aos_register_cmd (org_id);

CREATE INDEX IF NOT EXISTS idx_aos_register_cmd_generated_at
    ON org_aos_register_cmd (generated_at_utc);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper does not run
the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change to the dictionary or surrounding code):

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Each invocation produces a fresh time-sensitive registration command.
    # Auto-increment surrogate PK preserves historical rows; UNIQUE constraint
    # guards against accidental rapid re-invocation in the same UTC second.
    'getOrgAosRegisterCmd': {                                                       # operationId from OpenAPI
        'type': 'auto_increment_with_unique',                                       # PK strategy per research task 2
        'primary_key': ['misthelper_internal_id'],                                  # surrogate auto-increment PK
        'unique_keys': ['org_id', 'generated_at_utc'],                              # soft de-dup guard
        'indexes': ['org_id', 'generated_at_utc'],                                  # fast filter by org and time
        'table': 'org_aos_register_cmd',                                            # target SQLite table
    },
}
```

The MistHelper code that builds each row injects `org_id` (the prompt value) and
`generated_at_utc` (a fresh `datetime.utcnow().isoformat() + "Z"` at call time)
before passing the row list to `DataExporter.write_with_format_selection()`.

## Field-Level Logging Policy

Per Constitution Principle V and the Spec's gotcha that the registration command is
time-sensitive, the following per-field logging rules apply:

| Field                    | Safe to log? | Notes |
|--------------------------|--------------|-------|
| `misthelper_internal_id` | YES          | Surrogate integer, no PII or token content. |
| `org_id`                 | YES          | UUID; already used in other log lines. |
| `generated_at_utc`       | YES          | Wall-clock UTC timestamp. |
| `cli_commands`           | **NO**       | Contains the time-sensitive registration token. Never log at any level. |
| `cli_commands_length`    | YES          | Integer length only; safe to log at DEBUG. |
| `mist_host`              | YES          | Host name, already in `.env` and `mistapi` logs. |
| `http_status_code`       | YES          | Integer; safe at INFO/DEBUG. |

This table is binding on the implementation step: any `logging.*` call that
attempts to render `cli_commands` (full or any substring) fails the review gate.
