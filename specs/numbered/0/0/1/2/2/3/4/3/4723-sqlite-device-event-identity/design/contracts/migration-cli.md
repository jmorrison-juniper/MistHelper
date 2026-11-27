# Contract: Legacy Device Event Migration (command line)

## Command

```text
python -m src.foundation.persistence.device_events.legacy_migration --db <path> [--table <name>] [--apply]
```

## Options

| Option | Required | Meaning |
| - | - | - |
| `--db <path>` | Yes | Path to the SQLite file. A relative path is resolved from the repository root. |
| `--table <name>` | No, repeatable | Table to inspect. Without this option, the command inspects `OrgDeviceEvents` and `OrgDeviceEvents_52w`. |
| `--apply` | No | Run the migration. Without this option, the command runs a dry run only. |

## Dry run output

The command prints one line for each table.

```text
table=<name> state=<identity|legacy|absent> primary_key=<comma list> rows=<count> distinct_identities=<count>
```

- `state=identity` means the table already uses the identity key. The command makes no change.
- `state=legacy` means the table needs the migration.
- `state=absent` means the table does not exist. The command makes no change.

The dry run opens the database with a read-only URI. It changes no file.

## Apply flow

1. The command prints the dry run report for each named table.
2. The command asks: `Type MIGRATE to rebuild the legacy tables. Any other word stops the run:`
3. Any answer other than `MIGRATE` stops the run with exit code 1. No file changes.
4. The command writes a backup. The backup name is the database name, a UTC timestamp, and `.bak`.
5. The command checks the backup with `PRAGMA integrity_check`. A result other than `ok` stops the run with exit code 1.
6. The command opens one `BEGIN IMMEDIATE` transaction for each table.
7. The command renames the legacy table to `<table>_legacy_<UTC stamp>`.
8. The command creates the identity table and copies each distinct row.
9. The command compares the counts. A mismatch discards the transaction and stops the run with exit code 1.
10. The command commits and prints one `migrated` line for each table.

## Exit codes

| Code | Meaning |
| - | - |
| 0 | Dry run completed, or each named table is migrated or already migrated. |
| 1 | A refusal or failure occurred. No table changed. |
| 2 | Usage error, such as a missing `--db` option. |

## Log lines

Each action writes an info line before it. Each result writes a debug line after it. Log text uses ASCII only.

## Printed warning and caution

The command prints this warning before the apply prompt:

```text
Warning: rows that the old key overwrote before the fix stay lost. This migration cannot restore them.
```

The command prints this caution before the apply prompt:

```text
Caution: stop every export before you apply the migration. A running export holds the database lock.
```
