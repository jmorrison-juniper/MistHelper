# Contract: CLI Menu 310

This contract defines the terminal flow of menu 310. Menu 309 keeps its flow and output (FR-029).

## Identity

- **Menu number**: 310. The number is free on `main` (research R02 and R04).
- **Title**: `Collect EX switch transceivers into one master CSV report` (task T014).
- **Category**: `resource_intensive` (FR-027, task T015).
- **Destructive**: `false`. **Supports fast**: `false` (FR-027).

## Steps

1. The menu prints the same four steps as menu 309. Step 1 is `Step 1 of 4: Check the credential`, as in `console.py` line 43.
2. The menu shows the target counts for each organization.
3. The format prompt appears before the confirmation (FR-005). Step 3 is `Step 3 of 4: Confirm`, as in `console.py` line 83.
4. The menu collects each target and writes one CSV file.

## Format Prompt

- The prompt accepts `XML`, `JSON`, or `BOTH` (task T013).
- Enter selects `XML`.
- Any other answer cancels the run.
- The answer ignores outer spaces and letter case.
- End of input and an interrupt cancel the run (FR-026).

## Commands

The confirmation prints each command that the run sends. The commands come from `hardware_xml.py` lines 306 and 307. The menu sends no other command (FR-003).

| Format | Command lines printed |
|---|---|
| `XML` | `show chassis hardware detail \| display xml \| no-more` |
| `JSON` | `show chassis hardware detail \| display json \| no-more` |
| `BOTH` | The XML command line, then the JSON command line |

## Confirmation

- The confirmation phrase is `RUN <count> TARGETS`, as in `console.py` line 81.
- The prompt reads `Type RUN <count> TARGETS to start, or press Enter to cancel:`, as in `console.py` line 91.
- The typed answer must match the phrase exactly. Letter case counts (`console.py` line 93).
- A cancel at the confirmation opens no shell and writes no file (FR-026).

## Output

- The file is `data/ExTransceiverMaster_<UTC time>.csv` (FR-019).
- The file follows `contracts/transceiver-csv.md`.
- The menu never overwrites an earlier file.
- When the read-back check fails, the menu removes the file and reports the failure (task T008).
- A file above 64 MiB is not written. The menu prints one sentence that says so (spec edge case).
- When no connected EX switch exists, no file is written. The menu prints the menu 309 sentence for that case.

## Summary

The summary shows the count of each status: `collected`, `failed`, `skipped`, and `cancelled` (FR-016). The prose uses the word canceled. The code value keeps the spelling `cancelled`.

## Cancel During Collection

- A cancel at a prompt opens no shell and writes no file.
- A cancel during collection writes the file. Collected switches keep their rows. Each other switch gets a `cancelled` outcome row (spec edge case).

## Logging

- Each action writes an info line before it and a debug line after it (FR-024).
- Log lines are ASCII only.
- Log lines hold no token, password, or serial number.

## Tests

- Flow tests: `tests/unit/ex_hardware_inventory/test_hardware_operation.py` (task T013).
- End-to-end tests with a fake shell: `tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py` (task T017).
- Menu count and identity pins: `tests/unit/test_menu_entry_metadata.py` (task T016).
