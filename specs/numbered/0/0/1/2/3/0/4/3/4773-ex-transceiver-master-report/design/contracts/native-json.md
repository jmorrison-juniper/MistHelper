# Contract: Native JSON Reply Reader

This contract defines how the report reads a saved JSON reply of one switch. The reader does not change the file (FR-006).

## Input

- The input is one saved JSON reply, read from the run folder (task T009).
- The root object has the key `chassis-inventory`. Its value is a list that holds one object with a `chassis` list.
- Each leaf value is a list with one object that holds a `data` key. The synthetic fixture uses this form, as in `test_hardware_native_acceptance.py` line 43.
- Element names follow the XML element names of the same reply. The chassis module, sub-module, and sub-sub-module elements keep their names.
- An empty leaf can appear as `[{"data": ""}]` or as `[{}]`. The reader keeps the cell empty and invents no value (FR-010, research U-4).
- The reader rejects the JSON constants `NaN`, `Infinity`, and `-Infinity`. A reply with one of these values fails (spec edge case).
- A saved reply holds at most 1 MiB (the spec assumptions).

## Failure Rules

- Malformed JSON, truncated text, or a root that is not a chassis inventory fails the target with the reason `format_failed` (`report/builder.py` line 52).
- A failed JSON reply gives an outcome row. The reader never invents a row (spec edge case).
- A JSON failure does not replace a valid XML reply for the same switch (FR-011, decision D-7).

## Output

- The reader returns the same `FlattenedDevice` and `FlattenedItem` types that the XML walker returns (task T005).
- Field keys come from `HardwareXmlFlattener.Names.field`, as the XML walker uses them (task T005).
- The identity fields are `name`, `version`, `part-number`, `serial-number`, `description`, `clei-code`, and `model-number`. The synthetic builder uses this list at `hardware_replies.py` line 34.
- The reader holds no reference to the XML text. It builds its items from the JSON object only.

## Parity

- For the same switch data, the identity fields of the JSON reader equal the identity fields of the XML walker (task T005, SC-001).
- The parity test uses synthetic replies only (FR-031).

## Tests

- Reader and parity tests: `tests/unit/ex_hardware_inventory/report/test_hardware_flatten.py` (task T005).
- Native fixture shape: `tests/unit/websocket_streams/web/test_hardware_native_acceptance.py` (research R68).
