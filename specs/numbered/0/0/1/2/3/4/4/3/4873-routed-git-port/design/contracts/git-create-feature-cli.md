# Contract: Git extension 1.0.8 numbering scripts

**Scope**: `.specify/extensions/git/scripts/powershell/create-new-feature-branch.ps1` and `.specify/extensions/git/scripts/bash/create-new-feature-branch.sh`. Both files come from upstream v1.4.3, with the routed numbering of FR-008 and FR-009.

## Invocation

- PowerShell: `create-new-feature-branch.ps1 [-Json] [-DryRun] [-AllowExistingBranch] [-ShortName <name>] [-Number <long>] [-Timestamp] [-Help] <feature description>`
- Bash: `create-new-feature-branch.sh --json --short-name "<name>" "<feature description>"`, with the `--timestamp` and `--number` flags. The full bash flag list follows the 1.0.8 usage block, which this record did not read (U-4).

The environment variable `GIT_BRANCH_NAME` sets an exact branch name. It bypasses all numbering. Its UTF-8 length must be 244 bytes or fewer.

## JSON Output (PowerShell `-Json`)

| Key | Type | Meaning |
|-----|------|---------|
| `BRANCH_NAME` | string | The branch name, for example `4874-routed-check`. |
| `FEATURE_NUM` | string | The number or the timestamp prefix. |
| `HAS_GIT` | boolean | `false` when the folder is not a git repository. |
| `DRY_RUN` | boolean | Present, and `true`, only in a dry run. |

The 1.0.0 script returns these keys (`create-new-feature.ps1`, final output block, local view). The 1.0.8 change keeps them.

## Numbering Rule

1. Read the highest number from the names under `specs\`, using the same recursive scan and exclusions as the routed core (see `core-create-feature-cli.md`).
2. Read the highest number from the local and remote branch names that match the same pattern.
3. Use the larger of the two values plus one.
4. An explicit `-Number` value replaces the calculation.

## Route Rule

This script creates no record. The core `create-new-feature.ps1` step creates the record under `specs\numbered\` (decision D-8). FR-011 tests the sequence.

## Errors and Warnings

- A branch that exists, without `-AllowExistingBranch`, prints an error and exits 1.
- No git repository: `HAS_GIT` is `false`. A warning goes to stderr. The number is still computed.
- A name over 244 bytes is shortened. A warning names the original and the shortened value.

## Example

```text
create-new-feature-branch.ps1 -Json -DryRun -ShortName "routed-check" "routed check"
```

The output names `FEATURE_NUM` from the routed records. The exact value depends on the repository state.
