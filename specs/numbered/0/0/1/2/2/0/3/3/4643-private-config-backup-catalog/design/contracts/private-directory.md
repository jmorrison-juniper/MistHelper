# Contract: Private Backup Directory

## Purpose

This contract defines when the feature accepts the backup directory. It applies to every read and every write. It follows the owner storage policy in comment IC_kwDOQltU8c8AAAABkRDV7A.

## Location

- The parent folder is the one that the caller passes. The feature never creates the data directory (FR-005).

## POSIX Rules

| Object | Owner | Mode | Other rules |
| --- | --- | --- | --- |
| Directory | Current account | Exactly 0700 | No symbolic link. Link count is not used. |
| File | Current account | Exactly 0600 | Regular file. Link count of one. |

- The check uses `BackupAccess.verify` (R-14, R-15). The check refuses any group or other bit.
- The feature adds an exact-mode comparison. A narrower mode such as 0500 is refused (D-2).
- The feature never calls `chmod` on an existing path. The firmware writer does call it (R-16). This feature does not copy that behavior.

## Windows Rules

- The current account must own each path.
- Only the current account, SYSTEM, and the local Administrators group may hold access rules (`BackupAccess.windows`, permitted identifiers).
- A reparse point refuses the path before the ACL query on Windows (R-80).
- The ACL query runs through the fixed Windows PowerShell command in `BackupAccess`. The check refuses access when the query fails or returns an unexpected owner or rule (FR-003).

## Creation Rule

- The feature creates the backup directory only when it is missing and only under an existing data directory.
- The creation uses mode 0700 on POSIX. Windows relies on the inherited ACL check after creation.
- After creation, the feature runs the same checks as for an existing directory.

## Refusals

| Condition | Result | Test |
| --- | --- | --- |
| Symbolic link at the directory path | Refused | `test_directory_refuses_symbolic_link_root` |
| Name with traversal segments or a foreign name | Refused | `test_directory_refuses_traversal_and_foreign_file_names` |
| Hard-linked backup file | Refused | `test_directory_refuses_hard_linked_backup_file` |
| Group, other, or inexact mode | Refused, mode unchanged | `test_directory_refuses_inexact_modes_and_keeps_permissions` |
| Access check that cannot prove access | Refused | `test_directory_propagates_unprovable_access_refusal` |
| Real Windows ACL on a Windows runner | Accepted only for a private ACL | `test_directory_checks_real_windows_acl` |
| Missing data directory | Refused, nothing created | `test_directory_creates_missing_root_only_under_existing_data_directory` |

Caution: a refused permission check leaves the existing mode in place. The owner must correct the mode through the operating system. The feature does not repair permissions, because that action can widen access (FR-005).

## Error Mapping

- A refused directory check raises `PersistenceUnavailable`.
- The message names the check and omits the path contents. The message never contains a settings value.
