# Data Model: EX Transceiver Master Report

This model defines the rows, keys, and states of the transceiver master report. The file layout is in `contracts/transceiver-csv.md`.

## Entities

### Transceiver row

- **Meaning**: One transceiver item of one collected switch.
- **Record type**: `transceiver_item`.
- **Natural key**: `org_id`, `device_id`, and `item_path`. Each key appears once in the file (FR-009).
- **Source**: The XML reply of the switch. A switch without a valid XML reply uses its JSON reply (FR-011, FR-012).
- **Rule**: An absent source value stays an empty cell (FR-010).

### No-transceiver row

- **Meaning**: One collected switch with no transceiver item (FR-013).
- **Record type**: `no_transceiver`.
- **Natural key**: `org_id`, `device_id`, and an empty `item_path`.
- **Rule**: One row exists for each collected switch with no transceiver item.

### Device outcome row

- **Meaning**: One switch target that did not collect (FR-014).
- **Record type**: `device_outcome`, the existing record type in `report/builder.py` line 129.
- **Natural key**: `org_id`, `device_id`, and an empty `item_path`.
- **Status values**: `failed`, `skipped`, and `cancelled`. The identifier `cancelled` keeps its code spelling.
- **Reason**: A plain reason from the reason table in `report/builder.py` lines 51 to 54.

### Organization outcome row

- **Meaning**: One organization that Mist could not read (FR-015).
- **Record type**: `organization_outcome`.
- **Natural key**: `org_id`, an empty `device_id`, and an empty `item_path`.
- **Status and reason**: Status `failed`. The reason is the failure code of the organization plan, from `operation.py` lines 128 to 130.
- **Rule**: The switch columns stay empty.

## Target State Mapping

| Batch state | Reply | Status in file | Rows written |
|---|---|---|---|
| `completed` | Valid XML or valid JSON | `collected` | Transceiver rows, or one no-transceiver row |
| `completed` | No valid reply | `failed` | One device outcome row |
| `failed` | Any | `failed` | One device outcome row |
| `skipped` | Any | `skipped` | One device outcome row |
| `stopped` with reason `cancelled` | Any | `cancelled` | One device outcome row |

The mapping follows `report/builder.py` line 107, which maps `skipped` to `skipped` and `stopped` to `cancelled`. The final batch states appear in `run/watch.py` line 89.

## Native Reply

- **XML reply**: Stored as `xml_text` in `TargetResult`. The field exists at `report/builder.py` line 41.
- **JSON reply**: Stored as `json_text` in `TargetResult`. The field is new, with default `None` (task T004).
- **Size limit**: Each saved reply holds at most 1 MiB (the spec assumptions).

## Report File

| Output | Name | Written by | Rule |
|---|---|---|---|
| CLI | `data/ExTransceiverMaster_<UTC time>.csv` | Menu 310 (task T008) | Never overwrites an earlier file. Removed when the read-back check fails. |
| Portal | `hardware/transceiver-master.csv` in the run folder | Batch publish (task T020) | Joins the manifest and the ZIP archive. |
| Portal download | Name starts with `ExTransceiverMaster_` | Download route (task T021) | Served when `format=transceiver-csv`. |

The file size limit is 64 MiB. A larger report writes no file (task T007).

## Preview Binding

- **Field**: `transceiver_csv`, a boolean with default `False` (task T018).
- **Storage**: The preview record keeps the field (task T019).
- **Invalidation**: A change to the field invalidates the preview (FR-021, task T023).

## State Transitions

### Portal preview

- `none` moves to `valid` when the operator requests a preview.
- `valid` moves to `invalid` when the operator changes the checkbox.
- `invalid` moves to `valid` when the operator requests a new preview.

### CLI run

- `format prompt` moves to `confirmation` when the answer is XML, JSON, or BOTH.
- `confirmation` moves to `collecting` when the typed phrase matches exactly.
- `collecting` moves to `compiling` when every target reaches a final state.
- `compiling` moves to `writing` when the report compiles within the size limit.
- `writing` moves to `done` when the read-back check passes.
- A cancel at a prompt moves the run to `canceled`, and no file is written (FR-026).
- A failed read-back check removes the file and reports the failure.

## Uniqueness Rule

Each `(org_id, device_id, item_path)` triple appears at most once in a file. Device outcome rows and no-transceiver rows use an empty `item_path`. A switch is either collected or not collected, so each switch appears under one key group only.
