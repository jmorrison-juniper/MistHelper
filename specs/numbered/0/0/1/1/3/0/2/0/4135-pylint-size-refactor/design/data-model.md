# Data Model: Function and module size for Pylint limits (issue 4135)

This change moves code and names. It adds no database table, no record type, and no persisted value. The entities below describe the values that the moved code holds. Each value keeps its content and its order.

## Registry row

- Meaning: One menu row in the portal parameter registry.
- Natural key: The menu number, a string such as `"31"`.
- Fields: `category`, `parameters` (an ordered list), and the optional fields that each row already carries.
- Owner after the change: `PortalRegistryBuilder.build()` in `src/foundation/support/portal_operations/registry.py`, which merges the group rows.
- Constraint: The merged mapping holds the same keys and values as the mapping on `main`. The SHA-256 constant from Task T001 checks this.

## Group rows

- Meaning: The rows that one group builder returns.
- Natural key: The menu number inside the group.
- Owner after the change: One class per group in `src/foundation/support/portal_operations/groups/`.
- Constraint: The union of the four group classes and the site, client, and CLI groups equals the registry before the change.

## Endpoint strategy

- Meaning: The primary key strategy of one Mist API function.
- Natural key: The API function name, such as `listSiteDevices`.
- Fields: `type` (one of `natural_pk`, `composite_pk`, or `auto_increment_with_unique`) and `primary_key` (an ordered list of fields).
- Owner after the change: Six block dictionaries under `src/foundation/persistence/db/endpoint_strategies/`. The public dictionary in `src/foundation/support/refactors/endpoint_primary_key_strategies.py` merges them.
- Constraint: The public dictionary holds 612 keys in the original order. Block `n` holds positions `(n - 1) * 102 + 1` to `n * 102`.

## Menu entry

- Meaning: One operation in `menu_actions`, keyed by the menu number.
- Natural key: The menu number, a string from `"0"` to `"309"`.
- Fields: The `MenuEntry` fields, which keep their names and values.
- Owner after the change: Four block modules under `src/interfaces/cli/menu/`. `MENU_ACTIONS` merges them. `MistHelper.py` binds `menu_actions` to `MENU_ACTIONS`.
- Constraint: The key order equals the order on `main`. The SHA-256 constant from Task T001 checks the order.

## Module budget

- Meaning: One source file, its LF line count, and the child count of its directory.
- Natural key: The repository path.
- Fields: `path`, `lf_lines`, `limit` (1,000 for each module), `directory_children` (by the ratchet definition).
- Owner: `design/research.md`, the budget table.
- Constraint: Each named module has `lf_lines` of 1,000 or fewer after the change. Each grown directory has `directory_children` of five or fewer.

## Remote check

- Meaning: One claim that the change depends on, with its evidence.
- Natural key: The row number in `design/research.md`, from 1 to 62.
- Fields: `claim`, `path`, `ref`, `blob_sha`, `result` (present, absent, partial, or stale), and `line`.
- Owner: `design/research.md` and `STATUS.json`. The two lists hold the same 62 rows in the same order.

## State transitions

Not applicable: the change holds no runtime state, and no value changes state. The only transition is the move of a value from one module to another. The hash tests confirm that each value keeps its content and its order.
