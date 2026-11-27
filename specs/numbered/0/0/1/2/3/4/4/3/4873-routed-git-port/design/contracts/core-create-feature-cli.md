# Contract: Routed core `create-new-feature.ps1`

**Scope**: `.specify/scripts/powershell/create-new-feature.ps1` on `main`. This change does not modify the script.

## Invocation

`create-new-feature.ps1 [-Json] [-DryRun] [-AllowExistingBranch] [-ShortName <name>] [-Number <long>] [-Timestamp] [-Help] <feature description>`

A dry run (`-DryRun`) computes names and paths. It writes no file and sets `DRY_RUN` to `true` in the JSON output.

## JSON Output

| Key | Type | Meaning |
|-----|------|---------|
| `BRANCH_NAME` | string | `<NNN>-<suffix>` for sequential names, or `<YYYYMMDD-HHMMSS>-<suffix>` for timestamps. |
| `SPEC_FILE` | string | `specs\numbered\<route>\<BRANCH_NAME>\spec.md`, or `specs\live\<route>\<BRANCH_NAME>\spec.md` for timestamps. |
| `FEATURE_NUM` | string | Three or more digits for sequential names, or the timestamp. |
| `DRY_RUN` | boolean | Present, and `true`, only in a dry run. |

Example, when the highest record number is 4873:

```text
create-new-feature.ps1 -Json -DryRun -ShortName "routed-check" "routed check"
```

The output names `BRANCH_NAME` `4874-routed-check`, `FEATURE_NUM` `4874`, and a `SPEC_FILE` under `specs\numbered\0\0\1\2\3\4\4\4\`.

## Numbering Rule

1. Scan `specs\` recursively for directory names that match `^(\d{3,})-`.
2. Exclude names that match `^\d{8}-\d{6}-`, which are timestamp names.
3. Use the highest matched number plus one.
4. An explicit `-Number` value replaces the scan.

## Route Rule

- A numeric route uses the base-5 digits of the number, padded to eight digits. `Get-SpecRadixSegments` computes it.
- A timestamp route uses the base-5 digits of the UTC epoch seconds, padded to 17 digits.
- `Resolve-SpecFeaturePath` in `spec-route.ps1` joins the route and the name.

## Errors

- A feature folder that exists, without `-AllowExistingBranch`, prints an error and exits 1.
- A parent folder that already holds five children throws `Feature parent exceeds five children`.
- A missing spec template prints a warning on stderr and creates an empty `spec.md`.

## Side Effects

- A run without `-DryRun` creates the record folder and `spec.md`.
- The same run writes `.specify/feature.json` through `Save-FeatureJson`.
- `SPECIFY_FEATURE_NO_PERSIST` set to `1` blocks the pointer write in the setup scripts. It does not change this script's own write.
