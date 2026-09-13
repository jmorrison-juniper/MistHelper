# Quickstart: Validate the OpenAPI MIB Generator

This guide proves the feature works end to end. It runs the scenarios of the four user stories and
it names the expected outcome of each one. It holds no implementation code. The interface it uses is
in [contracts/cli.md](./contracts/cli.md), and the file formats are in
[data-model.md](./data-model.md).

## Prerequisites

| Item | Need | Note |
|---|---|---|
| Python | 3.13 or newer | The repository interpreter is 3.13.3. |
| The OpenAPI file | `documentation/mist-api-openapi31json.json` | Already in the repository. 16.6 MB. |
| Net-SNMP | `snmptranslate` on the path | Optional. Needed for scenario 2 only. Absent on a Windows workstation, so that test skips there and runs in CI. |
| Mist credentials | None | The generator makes no network call. |

## Setup

```bash
python -m pip install -r requirements-dev.txt
```

## Scenario 1 - Generate the MIB (User Story 1)

```bash
python MistHelper.py --mib-generate --mib-dry-run
python MistHelper.py --mib-generate
```

**Expected**: the dry run prints the object count and writes no file. The real run writes
`documentation/mibs/MISTHELPER-MIB.mib`, it reports 39 objects, 35 live and 4 identity columns, and
it exits 0. The log holds one line before the read and one line after the write.

## Scenario 2 - Load the MIB in Net-SNMP (SC-002)

```bash
snmptranslate -Tp -m ./documentation/mibs/MISTHELPER-MIB.mib -M ./documentation/mibs MISTHELPER-MIB::mistHelperMIB
```

**Expected**: exit code 0, no parse error, no warning, and a printed tree that shows the four
subtrees. Skip this step when `snmptranslate` is absent.

## Scenario 3 - Prove the table depth (User Story 4, scenario 2)

```bash
snmptranslate -On -m ./documentation/mibs/MISTHELPER-MIB.mib -M ./documentation/mibs MISTHELPER-MIB::mistDeviceReceivedBytes
```

**Expected**: `.1.3.6.1.4.1.11.2147483646.3.1.11`. A result of `.1.3.6.1.4.1.11.2147483646.3.1.1.11`
means the table is one level too deep, which is the defect this feature fixes.

## Scenario 4 - Prove the OID stability (User Story 2, SC-005)

```bash
cp documentation/mibs/MISTHELPER-MIB.mib /tmp/first.mib
python MistHelper.py --mib-generate
diff /tmp/first.mib documentation/mibs/MISTHELPER-MIB.mib
```

**Expected**: the only difference is the `LAST-UPDATED` value. Every other byte matches (FR-025).

Then add a field to a copy of the OpenAPI file, remove another, point the run at the copy, and
compare again. **Expected**: every kept object holds its first number, the new field takes the next
free column, and the removed field keeps its number with `STATUS obsolete`.

## Scenario 5 - Change the selection without a code change (User Story 3)

```bash
python MistHelper.py --mib-report
```

**Expected**: 66 candidates, sorted by column count, with the 3 selected ones marked. Add one
`operationId` to `data/mib_generator/allowlist.json`, run `--mib-generate` again, and the MIB holds
the objects of that endpoint. **No source file changes.**

Then put a `operationId` in the allow list that the OpenAPI file does not hold.
**Expected**: the run stops, it names the missing `operationId`, and it writes no MIB.

## Scenario 6 - The drift check that CI runs (FR-039, SC-008)

```bash
python MistHelper.py --mib-check ; echo "exit=$?"
```

**Expected**: `exit=0` when the OpenAPI file, the catalog, and the MIB agree. Remove a field that
the catalog names from a copy of the OpenAPI file and run again. **Expected**: `exit=1`, and the
message names the metric and the lost path.

## Scenario 7 - Prove no object returns No Such Instance (SC-006)

Start the agent and walk it, then compare the walk with the MIB object list:

```bash
METRICS_ORG_ID=<org> python MistHelper.py --metrics-snmp
snmpwalk -v2c -c public -m ./documentation/mibs/MISTHELPER-MIB.mib localhost .1.3.6.1.4.1.11.2147483646
```

**Expected**: every name in the MIB appears in the walk. 0 `No Such Instance` results.

## Run the tests

```bash
python -m pytest tests/unit/mib_generator tests/contract -v
python -m pytest tests/unit/mib_generator --cov=src/mib_generator --cov-report=term-missing
```

**Expected**: every test passes. The `snmptranslate` test reports `SKIPPED` on a Windows workstation
and it runs in CI. Coverage of `src/mib_generator` reaches 90 percent, which is the repository gate
in `pyproject.toml`.

## Run the quality gates

```bash
python -m ruff check src/mib_generator tests/unit/mib_generator
python -m black --check src/mib_generator tests/unit/mib_generator
python -m mypy src/mib_generator
python -m bandit -r src/mib_generator
python -m pylint src/mib_generator
python -m radon cc src/mib_generator -nc
python -m vulture src/mib_generator
python -m pydocstyle src/mib_generator
python -m interrogate -v src/mib_generator
python -m tools.ste_linter src/mib_generator documentation/mibs/MISTHELPER-MIB.mib
```

**Expected**: every command exits 0. Pylint scores 9.5 or better. Radon reports no block above
complexity 10. Interrogate reaches 90 percent. The STE linter scores 80 or better on the prose and
on the generated MIB descriptions.

## Measure the performance (SC-007)

```bash
python -m pytest tests/unit/mib_generator/test_runner.py -k performance -v
```

**Expected**: the run finishes in under 30 seconds and stays under 1 GB. The measured baseline of
the JSON load alone is 0.26 s to 0.49 s and 69.7 MB of traced Python memory, so the whole run holds
a wide margin.
