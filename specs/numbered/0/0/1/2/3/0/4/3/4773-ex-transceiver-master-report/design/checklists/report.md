# Report Checklist: EX Transceiver Master Report

**Purpose**: Check the transceiver master report output before the implementation is accepted.
**Created**: 2026-11-26
**Feature**: `contracts/transceiver-csv.md`, `data-model.md`

## Layout

- [x] CHK001 The header holds the 18 columns in the order of `contracts/transceiver-csv.md`.
- [x] CHK002 The file is UTF-8 with one header row (FR-018).
- [x] CHK003 The file passes the existing file check, `CsvVerifier.verify`, before publication (FR-018, task T007).
- [x] CHK004 A file above 64 MiB is not written, and the menu says so in one sentence (task T007).

## Rows

- [x] CHK005 The natural key `org_id`, `device_id`, and `item_path` is unique in the file (FR-009, task T003).
- [x] CHK006 Each transceiver item of each collected switch has one transceiver row (FR-007, SC-002).
- [x] CHK007 Duplicate hostnames and virtual-chassis members keep separate rows (FR-009, SC-002).
- [x] CHK008 A collected switch with no transceiver item has one no-transceiver row (FR-013).
- [x] CHK009 Each target that did not collect has one device outcome row with a status and a plain reason (FR-014).
- [x] CHK010 An organization that Mist could not read has one organization outcome row with empty switch columns (FR-015).
- [x] CHK011 A switch with a valid XML reply uses the XML rows only (FR-011).
- [x] CHK012 Rows for the same switch data match across XML, JSON, and both-format runs, except source and run time (FR-012, SC-001).

## Values

- [x] CHK013 An absent source value stays an empty cell (FR-010).
- [x] CHK014 Each text cell passes the spreadsheet formula guard before the file is written (FR-017, SC-004).
- [x] CHK015 A description with non-ASCII text keeps its UTF-8 text in the CSV (spec edge case).
- [x] CHK016 The summary counts match the number of rows for each status (FR-016).

## Publication

- [x] CHK017 The CLI file goes under the data folder with a UTC name (FR-019).
- [x] CHK018 The CLI file never overwrites an earlier file (FR-019).
- [x] CHK019 The portal file joins the manifest and the ZIP archive (FR-020).
- [x] CHK020 Native files stay unchanged, and the report never rewrites or deletes one (FR-006).
- [x] CHK021 With the portal checkbox off, every other output matches the earlier release (FR-030, SC-005).

## Notes

- CHK002 and CHK003 cite the existing renderer and verifier named in task T007.
- CHK012 uses the mocked runs of SC-001. The live comparison of task T034 covers the serial numbers only.
