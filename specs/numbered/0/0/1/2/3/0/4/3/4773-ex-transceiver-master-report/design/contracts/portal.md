# Contract: Portal Transceiver Checkbox and Download

This contract defines the WebSockets tab changes for the transceiver master CSV. With the checkbox off, every existing output stays unchanged (FR-030).

## Page

- **Checkbox**: Element identifier `wsBatchHardwareTransceiverCsv`. The checkbox is unchecked by default (FR-002).
- **Checkbox test identifier**: `ws-batch-hardware-transceiver-csv` (FR-022, task T022).
- **Download link**: Test identifier `ws-batch-transceiver-csv-download` (task T022).
- **Link visibility**: The link appears only after the file is published (task T023).
- **Existing link**: The CSV download link `ws-batch-csv-download` at `websockets_page.html` line 305 does not change.

## Preview Request

- The request carries the field `transceiver_csv`, a boolean (task T018).
- The default value is `false`.
- A value that is not a boolean is refused with the parser error (task T018, test TC-27).
- The preview values include `transceiver_csv` (test TC-26). The exact dictionary assertion at `test_ws_web_services.py` line 662 changes with the field.
- A change to the checkbox invalidates the preview. The start control stays disabled until the operator requests a new preview (FR-021).

## Start Output and Summary

- The start output keeps `transceiver_csv` beside `format` (task T019).
- The summary payloads report `transceiver_csv` beside `format`. The existing payload fields are at `sessions.py` lines 629 and 804.

## Publication

- The file is `hardware/transceiver-master.csv` in the run folder (task T020).
- The file publishes in the same publish step as the other outputs (FR-020, decision D-12).
- The manifest lists the file. The ZIP archive holds the file (FR-020).
- With `transceiver_csv` set to `false`, the run writes no transceiver file (SC-005).

## Download

- The existing batch download route serves the file with `format=transceiver-csv` (FR-023, task T021).
- The format table is `BATCH_OUTPUTS` at `download.py` line 24.
- The response has media type `text/csv`.
- The download file name starts with `ExTransceiverMaster_`. The existing prefix `ExHardwareInventory_` at `artifacts.py` line 871 stays with the existing outputs.
- The error text for an unknown format lists `transceiver-csv` (task T021). The current text is at `download.py` line 51.
- The page offers no table preview of the file (decision D-12, spec out of scope).

## Logging

- Each action writes an info line before it and a debug line after it (FR-024).
- Log lines are ASCII only and hold no secret.

## Tests

- Preview values and parser: `tests/unit/websocket_streams/web/test_ws_web_services.py` (tasks T018 and T019).
- Publication and download: `tests/unit/websocket_streams/web/test_ws_hardware_csv.py` (tasks T020 and T021). The exact download error text at line 410 changes.
- Page checkbox, link, and preview invalidation: `tests/e2e/websockets_tab/test_websockets_page.py` (tasks T022 and T023).
