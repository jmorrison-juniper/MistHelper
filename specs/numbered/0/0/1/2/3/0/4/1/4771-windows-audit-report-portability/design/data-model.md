# Data Model: Windows Audit Report Portability

## Audit report pair

- **Fields**: `report.json` contains the existing restricted JSON record. `report.md` contains its existing sanitized summary.
- **Validation**: Keep the current inventory, field allowlist, status, and redaction checks.
- **Relationship**: Both files represent one isolated audit run and share the same approved directory.

## Approved report directory

- **Value**: `test-artifacts/websocket-dialog-audit` under the current worktree.
- **Validation**: Reject a different path, a symbolic link, a reparse point, or a non-directory path component.
- **Access**: Permit the current owner only. Fail if the platform cannot enforce that rule.

## Staging file

- **Purpose**: Hold one complete report before replacing its destination.
- **Validation**: Create it exclusively in the approved directory. Apply owner-only access before writing.
- **Lifecycle**: Remove it after a successful replacement or any failure.
