# Contract: Editor Evidence Row

This contract defines the output columns for each live or terminal observation. One row covers one current path. The owner posts the rows as a comment on issue #4126. The rows are not committed to the repository.

## Output Columns

| Column | Type | Rule |
| - | - | - |
| `issue` | integer | Always `4126`. |
| `current_path` | text | The current repository path. Use forward slashes, as in research row R01. |
| `listed_path` | text | The path in the issue. Equal to `current_path` when the file did not move. |
| `blob_sha` | text | The blob SHA from research rows R01 to R27. |
| `observed_utc` | text | The UTC time in ISO 8601 form, for example `2026-12-01T14:30:00Z`. |
| `check_type` | text | `live` for the editor check or `terminal` for the command check. |
| `vscode_version` | text | The Visual Studio Code version from the About dialog. |
| `pylint_extension_version` | text | The version of `ms-python.pylint` in the editor. |
| `workspace_root` | text | The worktree root as a relative path, `.`. Do not record the user-profile segment. |
| `interpreter` | text | The worktree interpreter as a relative path, for example `.venv\Scripts\python.exe`. |
| `pylint_command_source` | text | `pylint.path`, `importStrategy fromEnvironment`, or `unknown` with the cause. |
| `e0401_count` | integer | The number of E0401 diagnostics from the Pylint source. |
| `e0611_count` | integer | The number of E0611 diagnostics from the Pylint source. |
| `result` | text | `pass`, `fail`, or `unverified`. |
| `cause` | text | Empty for `pass`. Otherwise, the reason for `fail` or `unverified`. |

## Rules

- A row reports `pass` only when `e0401_count` and `e0611_count` are both zero, `check_type` is `live`, and `pylint_command_source` is known.
- A `terminal` row never reports `pass` for the live check (FR-011).
- A row with a missing native permission reports `unverified` and names the permission in `cause` (FR-015).
- Each row omits credentials, environment variable values, and user-profile path segments (FR-014).
- Each row uses one current path. A moved path uses its current path in `current_path` (decision D-7).
