# Contract: ExportBackendOptions Full-Batch Field

**Interface**: `ExportBackendOptions.require_full_batch: bool = False`

**Location**: `src/foundation/models/dataclasses/export_backend_options.py`

## Definition

The field joins `format_override` and `raw_data` in the frozen dataclass. The field carries an inline comment that states its scope. The module docstring lists the new field with its scope.

## Scope

| Output Format | Effect of the Field |
| - | - |
| sqlite | When True, the SQLite write uses the full-batch rule. A partial batch returns False. |
| csv | The field has no effect. The CSV branch does not read it. |
| Polyglot mirror | The field has no effect. The mirror path does not read it. |

## Compatibility

- The default value is False. Existing callers construct the same options and get the same behavior.
- Existing calls that pass `format_override` or `raw_data` need no change.
- The dataclass stays frozen and slotted, as it is today.

## Usage

The 52-week exporter builds the options in `_write_sqlite_batch` with `format_override` set to `sqlite` and `require_full_batch` set to True. No other caller sets the field in this change.
