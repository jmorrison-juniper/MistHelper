# Contract: Module move map

**Scope**: The 59 moved modules in `plan.md`, section A. The table in that section is the only source of the mapping.

**Input**: One old dotted path from the table, for example `src.operations.exporting.export.org_site_exporter`.

**Output**: The one new dotted path from the same row, for example `src.operations.exporting.export.org.config.org_site_exporter`.

## Rules

1. The mapping is one to one. No old dotted path remains as an alias, a re-export, or a stub.
2. The moved module keeps each module-level name and each function and class name.
3. The module logger name equals `__name__` at the new dotted path.
4. Each class in the module reports the new dotted path as its `__module__` value.
5. Each import inside the moved packages uses an absolute dotted path.
6. `src.operations.exporting.export.data_exporter` keeps its dotted path.
7. `src.operations.exporting.juniper_rma.model.run_record`, `src.operations.exporting.juniper_rma.workflows.access_check`, and `src.operations.exporting.juniper_rma.workflows.correlation` keep their dotted paths.

## Failure behavior

- An import of an old dotted path raises `ModuleNotFoundError`.
- An import of a new dotted path that has no file raises `ModuleNotFoundError`, and the import smoke step reports it.

## Verification

Run `design/quickstart.md`, step 3 for the old paths and step 5 for the import smoke check. Expected result: no line is printed.
