# Contract: Guard Interface

## Scope

This contract covers one test module, `tests/guardrails/test_mistapi_spec_modules.py`. The guard has no command-line, menu, portal, or API surface. Its interfaces are the helper methods, the class attribute, the summary line, and the failure messages below.

## Naming and prefixes

- The operation prefix is `- **operationId**: ` followed by a backtick. A line that begins with this prefix starts an operation pair.
- The module prefix is `- **mistapi SDK module**: ` followed by a backtick. A line that begins with this prefix supplies the module of the pending operation pair.
- Spec paths in keys and messages are POSIX paths relative to the repository root.

## Helper `_source_fields`

- **Input**: `spec_file`, a `Path` to one spec file. The file is read as UTF-8 text.
- **Output**: A list of pairs. Each pair holds the operation identifier and either the module path or no value.
- **Order**: The pairs follow the order of the operation lines in the file.
- **Orphans**: A pair holds no module when the next operation line or the end of the file comes before a module line.
- **Ignored lines**: A module line with no pending operation line is ignored.
- **Logging**: An `info` line precedes the file read. A `debug` line follows it and reports the pair count.

## Scan `spec_declarations`

- **Input**: No parameters. The method reads the module globals `_SPECS_ROOT` and `_REPO_ROOT`.
- **Output**: A list of triples. Each triple holds the absolute spec path, the operation identifier, and the module path or no value.
- **Skipped files**: The frozen spec files named in `frozen_spec_files`.
- **Order**: Sorted spec paths, so the output order is stable.

## Failure helper `failure_messages`

- **Input**: The triples from the scan, and the SDK definitions as a map from identifier to module path.
- **Output**: A list of failure strings. The list is empty when no defect exists.
- **Templates**:
  1. Zero pairs: `No operation pairs were examined.`
  2. Orphan pair: `{spec path}: {operation identifier} has no mistapi SDK module line`
  3. Mismatch: `{spec path}: {operation identifier} declares {declared module}, found {found module}`
  4. Declared absence with SDK drift: `{spec path}: {operation identifier} is declared absent, but the SDK defines it in {found module}`
- **Found module**: The text `None` appears when the SDK lacks the operation in a mismatch message.

## Summary line

- **Template**: `mistapi spec module guard: examined {examined} operation pairs, {defects} defects.`
- **Output rule**: The test prints this line on every run, with `print`.
- **Failure rule**: The assertion message begins with the same line, followed by one failure string on each line.

## Class attribute `ABSENT_SDK_OPERATIONS`

- **Type**: A dictionary from POSIX spec path to operation identifier.
- **Entries**:
  - `specs/591-mist-get-org128-t-registration-commands/spec.md` maps to `getOrg128TRegistrationCommands`.
  - `specs/932-mist-list-org-audit-logs-legacy/spec.md` maps to `listOrgAuditLogsLegacy`.
- **Match rule**: An entry applies only when both the spec path and the operation identifier match.

## Output rules

- All printed text and logged text is ASCII.
- Logging calls use the `%s` style of formatting, and they do not log a secret.
- The guard reads files only. It opens no network connection.
