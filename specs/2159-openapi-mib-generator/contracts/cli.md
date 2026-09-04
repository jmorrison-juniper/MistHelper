# Contract: The operator interface

The generator offers one Python class and three command line actions. It offers no wrapper function.

## 1. The Python interface (FR-038)

```python
from src.mib_generator.runner import MibGeneratorRunner

runner = MibGeneratorRunner(
    openapi_path=Path("documentation/mist-api-openapi31json.json"),
    allowlist_path=Path("data/mib_generator/allowlist.json"),
    ledger_path=Path("data/mib_generator/oid_assignments.json"),
    output_path=Path("documentation/mibs/MISTHELPER-MIB.mib"),
)
```

The constructor takes 4 parameters, inside the limit of 5. It reads no file. Each action below reads
what it needs, so a caller can build the runner and then choose an action.

| Method | Signature | Returns | Writes a file |
|---|---|---|---|
| `generate` | `generate(self, dry_run: bool = False) -> int` | The count of objects written. | Yes, unless `dry_run` is true. It also appends any new entry to the ledger. |
| `report` | `report(self) -> tuple[CandidateReport, ...]` | One record for each candidate statistics endpoint, with the count of columns it would add. | No. |
| `check` | `check(self) -> tuple[str, ...]` | The drift lines. An empty tuple means no drift. | No. |

## 2. The command line

The flags follow the pattern that `--metrics-snmp` and `--capture-portal` already use in
`MistHelper.py`.

| Flag | Action | Exit code |
|---|---|---|
| `--mib-generate` | Write the MIB from the OpenAPI file, the allow list, and the ledger. | 0 on success. 1 on any stop condition. |
| `--mib-report` | Print each candidate statistics endpoint and the count of columns it would add. Write nothing. | 0 always, unless the input file is unreadable. |
| `--mib-check` | Compare the current MIB against the OpenAPI file and the catalog. Write nothing. | 0 when the three agree. 1 on any drift. CI uses this. |
| `--mib-dry-run` | A modifier for `--mib-generate`. Print the object count and write no file (FR-041). | As `--mib-generate`. |
| `--mib-output PATH` | A modifier for `--mib-generate`. Write the MIB to this path instead of the default. | As `--mib-generate`. |

Examples:

```bash
python MistHelper.py --mib-report
python MistHelper.py --mib-generate --mib-dry-run
python MistHelper.py --mib-generate
python MistHelper.py --mib-check
```

## 3. The menu

Menu entry `243`, in the same dict that holds `239` and `241`:

```python
"243": (
    lambda: _run_mib_generator_menu(),
    "Generate the SNMP MIB from the Mist OpenAPI file (issue #2159)",
),
```

The registry row in `src/utils/operation_registry.py`:

```python
"243": {"category": "safe"},
```

The category is `safe`, and not `interactive_safe`, because the action reads local files only, makes
no Mist API call, needs no operator choice, and is deterministic. An automated pass may therefore
run it.

## 4. Every stop condition

Each condition raises before the writer opens a file, so a failed run never leaves a partial MIB.

| Condition | Requirement | Message names |
|---|---|---|
| The input is not valid JSON | FR-006 | The path and the JSON error position. |
| The `openapi` field is not `3.1.x` | FR-006 | The version found. |
| The allow list names an unknown `operationId` | FR-011 | The missing `operationId`. |
| The allow list names an operation that is not a GET | FR-011 | The `operationId` and the method found. |
| The catalog names a source field the schema lost | FR-015 | The metric name and the lost path. |
| The ledger holds a duplicate number, a duplicate name, or a number outside its subtree | FR-024 | Each offending pair. |
| The ledger `base_oid` differs from `DEFAULT_BASE_OID` | FR-017 | Both values. |
| A descriptor collides 99 times | data-model 5.1 | The base name. |

## 5. Logging (FR-040, principle VII)

Each action writes one line before it and one line after it, under the prefix `MIB_GENERATOR:`, in
the same shape that `METRICS_SNMP:` and `CAPTURE_PORTAL:` already use.

```text
MIB_GENERATOR: Reading the OpenAPI file at documentation/mist-api-openapi31json.json
MIB_GENERATOR: Read 719 paths and 1799 schemas in 0.49 seconds
MIB_GENERATOR: Writing the MIB to documentation/mibs/MISTHELPER-MIB.mib
MIB_GENERATOR: Wrote 39 objects, 35 live and 4 identity columns
```

## 6. The report output (FR-010)

`--mib-report` finds a candidate by `/stats` in the path or `Stats` in a tag. It prints one line for
each, sorted by the column count, with a marker for a candidate the allow list already holds.

```text
operationId              path                              columns  selected
listOrgDevicesStats      /api/v1/orgs/{org_id}/stats/devices     61  yes
listSiteDevicesStats     /api/v1/sites/{site_id}/stats/devices   61  no
listOrgSiteStats         /api/v1/orgs/{org_id}/stats/sites       24  yes
getOrgStats              /api/v1/orgs/{org_id}/stats             18  yes
...
66 candidates. 3 selected. Edit data/mib_generator/allowlist.json to change the selection.
```
