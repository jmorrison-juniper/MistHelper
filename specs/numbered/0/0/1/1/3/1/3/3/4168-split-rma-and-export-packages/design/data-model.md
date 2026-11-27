# Data Model: Split the Juniper RMA and export packages

This change has no database. The entities below are repository artifacts. Each entity has a natural key, its attributes, and the rules that the guard or a gate checks.

## Entity: Moved module

- Natural key: the old dotted path, for example `src.operations.exporting.export.org_site_exporter`.
- Attributes: the old file path, the new file path, the new package, the module-level names, the logger name, and the `__module__` value of each class.
- Rules:
  - Each old path maps to exactly one new path.
  - No file remains at an old path after the move.
  - Module-level names stay unchanged (FR-009).
  - The logger name equals the new dotted path, because the logger uses `__name__`.
- State transitions: `present at old path` changes to `moved` by a rename. A moved module never returns to an old path.

## Entity: Baseline entry

- Natural key: the repository path under `src/`, for example `src/operations/exporting/juniper_rma/model`.
- Attributes: `path`, `child_count`, and `remediation_issue`.
- Rules:
  - The entries are sorted by path.
  - Each `child_count` is greater than five.
  - Each entry matches a measured directory with more than five children.
- State transitions:
  - `violation` means the entry is present, and its directory holds more than five children.
  - `removed` means the entry is deleted, because its directory holds five children or fewer.
  - A present entry whose directory holds five children or fewer fails the guard as stale.

## Entity: Measured directory

- Natural key: the repository path under `src/`.
- Attributes: the child count. The count equals the number of child modules, excluding `__init__.py`, plus the number of child directories that hold tracked Python files.
- Rules:
  - A compliant directory holds five children or fewer.
  - A directory with more than five children must have a baseline entry.
  - A new directory with more than five children fails the guard as unknown.

## Entity: Domain package

- Natural key: the directory path, for example `src/operations/exporting/export/site/events`.
- Attributes: one `__init__.py` file that holds one docstring.
- Rules:
  - The package exports no name through `__init__.py`.
  - The package holds five children or fewer.
  - The package uses absolute imports for its modules.

## Entity: Dated record

- Natural key: the repository path.
- Attributes: the path and the record type (`specs/`, `changelog.d/`, `.specify/bugs/`, or `CHANGELOG.md`).
- Rules:
  - A dated record keeps its content.
  - The old-path search excludes each dated record (D-9).

## Validation summary

| Entity | Check | Command |
| - | - | - |
| Measured directory | Count and baseline match | `design/quickstart.md`, step 1 |
| Baseline entry | Valid JSON and sorted paths | `design/quickstart.md`, step 2 |
| Moved module | Old path absent and new path importable | `design/quickstart.md`, steps 3 and 5 |
| Domain package | Compile each marker | `T002` in `tasks.md` |
