# Data Model: Check Every Operation Pair in the mistapi Spec Guard

The guard holds no database. Its data lives in memory during one test run. The entities below describe the values that the guard reads, checks, and reports.

## OperationPair

- **Fields**:
  - `spec_path`: the POSIX path of the spec file, relative to the repository root.
  - `operation_id`: the text between the first pair of backticks on the operation line.
  - `operation_line`: the one-based line number of the operation line.
  - `sdk_module`: the text between the backticks on the module line, or no value.
  - `module_line`: the one-based line number of the module line, or no value.
- **Natural key**: `spec_path` and `operation_line`.
- **Rules**: The `operation_id` value must not be empty. A pair with no `sdk_module` is an orphan, unless a declared absence applies.

### Pair state transitions

The helper `_source_fields` reads the lines of one spec file in order. It holds at most one pending operation.

| Current state | Event | Next state | Result |
| - | - | - | - |
| Idle | Operation line | Awaiting module | The new operation becomes pending. |
| Idle | Module line | Idle | The module line is ignored. |
| Awaiting module | Module line | Idle | The pending operation pairs with the module. |
| Awaiting module | Operation line | Awaiting module | The previous operation becomes an orphan. The new operation becomes pending. |
| Awaiting module | End of file | End | The pending operation becomes an orphan. |

## DeclaredAbsence

- **Fields**:
  - `spec_path`: the POSIX path of the spec file, relative to the repository root.
  - `operation_id`: the operation that the spec declares as absent from the SDK.
- **Natural key**: `spec_path` and `operation_id`.
- **Entries**: Two entries exist in `ABSENT_SDK_OPERATIONS`. They cover spec file 591 and operation `getOrg128TRegistrationCommands`, and spec file 932 and operation `listOrgAuditLogsLegacy`.
- **States**:
  - Valid: the installed SDK lacks the operation. The guard reports no defect.
  - Drift: the installed SDK defines the operation. The guard reports one defect that names the defining module.

## SdkDefinition

- **Fields**:
  - `operation_id`: the name of a top-level function in the installed package.
  - `module_path`: the dotted module path that starts with `mistapi`.
- **Natural key**: `operation_id`.
- **Source**: Each top-level function definition in the installed mistapi source.
- **Duplicate rule**: When two modules define one name, the module that the scan reads last wins. The survey found one duplicate name, `show`, and no operation pair uses it.

## GuardReport

- **Fields**:
  - `examined`: the number of operation pairs that the guard examined.
  - `defects`: the number of failure messages.
- **Output**: One summary line, printed on each run.
- **Rules**: When `examined` is zero, the guard adds the defect `No operation pairs were examined.`

## Relationships

- Each operation pair belongs to one spec file.
- Each declared absence matches zero or one operation pair in one run.
- Each operation pair refers to zero or one SDK definition by `operation_id`.
- Each report counts every operation pair from every non-frozen spec file.
