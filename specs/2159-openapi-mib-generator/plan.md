# Implementation Plan: OpenAPI MIB Generator

**Branch**: `2159-openapi-mib-generator` | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/2159-openapi-mib-generator/spec.md`

## Summary

A person writes `documentation/mibs/MISTHELPER-MIB.mib` by hand today. The hand work already made one
defect. This feature adds the package `src/mib_generator/`. The package reads three inputs and it
writes the MIB:

- `documentation/mist-api-openapi31json.json` gives the type, the description, and the proof that a
  Mist field still exists.
- `src/metrics_gateway/catalog.py` gives the truth about the readings the agent answers.
- `data/mib_generator/oid_assignments.json` gives the number of each field, so an OID never moves.

The package does not change the catalog and it does not change the agent. It reads both, and it
fails when the three inputs disagree. The command line offers three actions: `generate`, `report`,
and `check`. CI runs `check`.

## Technical Context

**Language/Version**: Python 3.13.3, the interpreter this repository already uses.

**Primary Dependencies**: The standard library only. `json`, `pathlib`, `dataclasses`, `logging`,
`argparse`, and `re` cover every need. The allow list and the assignment file are JSON, so `PyYAML`
stays out. The tests add `pytest` and `hypothesis`, which the repository already holds.

**Storage**: Two checked-in JSON files under `data/mib_generator/`. One output text file under
`documentation/mibs/`.

**Testing**: `pytest` under `tests/unit/mib_generator/`, with `hypothesis` for the descriptor rules
and for the number stability. One contract test calls `snmptranslate` and it skips when the binary
is absent.

**Target Platform**: A Windows workstation and a Linux container. The generator reads local files
only, so both hosts behave the same. Net-SNMP is absent on the workstation.

**Project Type**: A local command line tool inside the MistHelper repository.

**Performance Goals**: A generate run finishes in under 30 seconds and uses under 1 GB of memory
(SC-007). The measured load of the 16.6 MB file is 0.26 s to 0.49 s and 69.7 MB of traced Python
memory on Python 3.13.3. See [research.md](./research.md) for the measurement.

**Constraints**: The MIB root must equal `DEFAULT_BASE_OID`. A live OID must never move. The MIB
must hold no object that the agent does not answer.

**Scale/Scope**: 719 paths, 1,799 schemas, 508 GET operations, 66 statistics endpoints. The default
allow list selects 3 of them. The output MIB holds 35 live objects and 4 identity columns.

## Constitution Check

*GATE: passed before Phase 0. Re-checked after Phase 1.*

| Principle | How this plan meets it |
|---|---|
| I. Five-Item Rule | `src/mib_generator/` holds 5 modules and one `__init__.py`. No module holds more than 3 classes. No class holds more than 5 public methods. No function takes more than 5 parameters, holds more than 5 blocks, or runs past 25 lines. |
| II. Class-Based Architecture | Six classes own the work. The command line calls `MibGeneratorRunner` directly. No wrapper function exists. |
| III. Safety-First | The tool reads local files and it makes no network call. `generate` refuses to overwrite when the caller passes `--dry-run`. `check` writes nothing at all. Every stop condition raises before the writer opens a file. |
| IV. Full Deployment Pipeline | The `check` action joins CI. The generate action joins the release step that refreshes the MIB. |
| V. Observability & Logging | Each class holds a module logger. Each action logs a count on completion. |
| VI. Inline Comments | Each executable line carries a comment that states the reason. |
| VII. Action Logging | Each action logs one line before it and one line after it. |

**Gate result**: PASS. No violation. The Complexity Tracking table stays empty.

One deviation from the spec needs a record. FR-046 asks for 80 percent coverage. The repository
gate in `pyproject.toml` is `fail_under = 90`. The stricter repository gate wins, so the plan
targets 90 percent for the new package.

## Project Structure

### Documentation (this feature)

```text
specs/2159-openapi-mib-generator/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli.md
│   ├── allowlist.schema.json
│   └── oid-assignments.schema.json
└── tasks.md             # Phase 2 output, made by /speckit.tasks
```

### Source Code (repository root)

```text
src/mib_generator/
├── __init__.py          # The package docstring and the public names.
├── document.py          # Load the OpenAPI file and answer a question about one operation.
├── schema.py            # Turn one response schema into a flat list of fields.
├── assignment.py        # Hold the allow list, the descriptor rule, and the OID ledger.
├── mib.py               # Map a field to an SNMP type and write the SMIv2 text.
└── runner.py            # Run the generate action, the report action, and the check action.

data/mib_generator/
├── allowlist.json       # The operationId of each selected endpoint and its scope.
└── oid_assignments.json # The subtree, the column, the descriptor, and the state of each field.

documentation/mibs/
└── MISTHELPER-MIB.mib   # The output. A person must not edit it after this feature merges.

tests/unit/mib_generator/
├── test_document.py     # Parse, version check, $ref depth limit.
├── test_schema.py       # allOf, oneOf with a discriminator, anyOf, nullable, empty schema.
├── test_assignment.py   # The descriptor rules and the number stability. Hypothesis lives here.
├── test_mib.py          # The type mapping and the SMIv2 text.
└── test_runner.py       # The three actions and each stop condition.

tests/contract/
├── test_mib_parses_with_snmptranslate.py  # Skips when Net-SNMP is absent.
└── test_mib_matches_catalog.py            # Moved from tests/unit/metrics_gateway/.
```

**Structure Decision**: A new package `src/mib_generator/` beside `src/metrics_gateway/`. The
generator is a build-time tool and the gateway is a run-time service. They must not share a package,
because the SNMP responder must import nothing that reads a 16.6 MB file. The generator imports the
catalog. The catalog imports nothing from the generator.

### Module responsibilities, one each

| Module | The one thing it does |
|---|---|
| `document.py` | Read the JSON file, prove it is OpenAPI 3.1, and answer "what schema does this GET return?" |
| `schema.py` | Walk one schema and return a flat, ordered list of scalar fields. |
| `assignment.py` | Decide which endpoints count, decide the name of a field, and decide its number. |
| `mib.py` | Decide the SNMP type of a field and turn the field set into SMIv2 text. |
| `runner.py` | Order the steps of an action, log them, and report the result. |

### Class set

| Class | Module | Responsibility | Public methods |
|---|---|---|---|
| `OpenApiDocument` | `document.py` | Own the parsed document and resolve a reference. | `load`, `get_operation`, `response_schema`, `resolve` |
| `FieldRecord` | `schema.py` | One frozen record of a scalar field. | Data only. Frozen dataclass with slots. |
| `SchemaFlattener` | `schema.py` | Turn one schema into `FieldRecord` values. | `flatten` |
| `AllowList` | `assignment.py` | Own the selection and prove it against the document. | `load`, `entries`, `validate` |
| `DescriptorMaker` | `assignment.py` | Turn a scope and a field path into a valid, unique descriptor. | `make` |
| `OidLedger` | `assignment.py` | Own the number of every field, live or obsolete. | `load`, `validate`, `claim`, `entries`, `save` |
| `SnmpTypeMapper` | `mib.py` | Decide the SYNTAX, the UNITS, and the scale note of one field. | `syntax_for`, `units_for` |
| `MibWriter` | `mib.py` | Turn the resolved object set into SMIv2 text. | `render` |
| `MibGeneratorRunner` | `runner.py` | Run one action end to end. | `generate`, `report`, `check` |

Nine classes across five modules. No class wraps another. `MibGeneratorRunner` holds the other
classes as collaborators and it calls their methods directly.

### The decisions the plan owes the spec

1. **Module layout**: the table above. `src/mib_generator/` holds 5 modules plus `__init__.py`, so
   the 5-Item Rule holds at the package level.
2. **Class set**: the table above. No wrapper.
3. **Data files**: `data/mib_generator/allowlist.json` and `data/mib_generator/oid_assignments.json`.
   The format, the location, and a worked example of each live in [data-model.md](./data-model.md)
   and in `contracts/`.
4. **Type mapping**: the full table, with the fractional case, the 64-bit case, and the nullable
   case, lives in [data-model.md](./data-model.md). It keeps the catalog behaviour: a ratio scales
   by 10000, and a byte count uses `Counter64`.
5. **Descriptor rule and collision rule**: [data-model.md](./data-model.md).
6. **Operator interface**: three flags, `--mib-generate`, `--mib-report`, and `--mib-check`, plus
   menu entry 243. The wiring follows `--metrics-snmp` exactly. See [contracts/cli.md](./contracts/cli.md).
7. **Test strategy**: the table in this file, expanded in [quickstart.md](./quickstart.md).
8. **Migration**: the section below.

### Operator interface, in the pattern the repository already uses

`--metrics-snmp` and `--capture-portal` follow one pattern in `MistHelper.py`:

1. `parser.add_argument(...)` in the service flag group near line 5256.
2. A `_run_<mode>` handler near line 5937.
3. A row in the `mode_table` tuple of `_dispatch_main_mode` near line 5969.
4. A menu entry in the menu dict near line 3750, through a lambda that defers the name lookup.
5. A row in `OperationRegistry._REGISTRY` in `src/utils/operation_registry.py`.

This feature adds the same five parts:

- Three flags: `--mib-generate`, `--mib-report`, `--mib-check`.
- One handler, `_run_mib_generator_mode`, that reads the three flags and calls the matching method
  of `MibGeneratorRunner`.
- One row in `mode_table`, placed after `--metrics-snmp`, because the SNMP responder owns standard
  output and must match first.
- Menu entry `243`, through `lambda: _run_mib_generator_menu()`.
- Registry row `"243": {"category": "safe"}`. The action reads local files, it makes no Mist API
  call, and it is deterministic, so an automated pass may run it.

### Test strategy

| Test | Kind | Where | Note |
|---|---|---|---|
| Parse a small fixture, reject bad JSON, reject a non-3.1 version | unit | `test_document.py` | The fixture is a hand-written 60-line OpenAPI file. |
| Stop a self `$ref` at the depth limit and log the cut | unit | `test_document.py` | |
| `allOf`, `oneOf` with a discriminator, `anyOf`, empty schema, nullable form | unit | `test_schema.py` | Covers the `stats_device` shape. |
| Skip an array of objects and a nested object | unit | `test_schema.py` | |
| The descriptor obeys the three SMIv2 rules for any input | property, Hypothesis | `test_assignment.py` | Strategy: random text, including Unicode, digits at the front, and names past 64 characters. |
| The descriptor never collides across a random field set | property, Hypothesis | `test_assignment.py` | |
| A kept field never changes its number across random add and remove runs | property, Hypothesis | `test_assignment.py` | SC-005 asks for 100 runs. |
| A duplicate number, a duplicate name, or an out-of-subtree number stops the run | unit | `test_assignment.py` | |
| Each JSON type gives the stated SNMP type, and a scaled ratio gives a whole number | unit | `test_mib.py` | |
| Two runs on one input give the same bytes, except the revision date | unit | `test_runner.py` | |
| A catalog field the OpenAPI file lost stops the run | unit | `test_runner.py` | |
| An OpenAPI field the catalog lacks is reported, not emitted | unit | `test_runner.py` | |
| `--dry-run` writes no file | unit | `test_runner.py` | |
| The generated MIB parses with `snmptranslate -Tp -m` | contract | `tests/contract/test_mib_parses_with_snmptranslate.py` | `shutil.which("snmptranslate")` gates a `pytest.mark.skipif`, so the Windows gate stays green. CI installs Net-SNMP. |
| Every MIB OID matches an OID the `OidTree` answers | contract | `tests/contract/test_mib_matches_catalog.py` | |
| The 35 hand-written objects keep their name and their OID | regression | `tests/contract/test_mib_matches_catalog.py` | |
| A generate run stays inside 30 s and 1 GB | performance | `tests/unit/mib_generator/test_runner.py`, marked `slow` | `tracemalloc` measures the memory. |

### Migration from the hand-written MIB

1. Seed `data/mib_generator/oid_assignments.json` from the current catalog. The catalog already
   holds the column of each of the 35 readings, so the seed is a copy, not a guess. Every live OID
   therefore keeps its number by construction.
2. Generate to a temporary path. Compare the object list with the hand-written MIB. The 35 names and
   the 35 OIDs must match. The table depth defect of the hand-written file is fixed in the generated
   file, and the revision history of the MIB records the fix.
3. Replace `documentation/mibs/MISTHELPER-MIB.mib` with the generated file, and add a header comment
   that tells a reader the file is generated.
4. **The fate of `tests/unit/metrics_gateway/test_mib_matches_catalog.py`**: the file **moves** to
   `tests/contract/test_mib_matches_catalog.py` and it **stays otherwise unchanged**. Its assertions
   stay correct and they gain value, because they now check a generated file against the same
   catalog from the outside. The move is right for two reasons. The test no longer tests the
   `metrics_gateway` package, and it now guards the contract between two packages. Two additions
   join it in the new location: the regression check of the 35 names and OIDs, and a check that the
   MIB holds no object that the `OidTree` does not answer (SC-006).
5. Add `--mib-check` to CI, so a drift fails the build.
6. Record in `CHANGELOG.md` that a person must not edit the MIB by hand again.

## Complexity Tracking

No constitution violation. This table stays empty.
