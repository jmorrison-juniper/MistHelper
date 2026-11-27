# Security Checklist: EX Transceiver Master Report

**Purpose**: Check the security controls of the CLI menu, the portal checkbox, and the report before acceptance.
**Created**: 2026-11-26
**Feature**: `contracts/cli-menu-310.md`, `contracts/portal.md`, `contracts/transceiver-csv.md`

## Commands and Transport

- [x] CHK001 Both front ends reuse the existing fixed read-only commands, and no device command is added (FR-003).
- [x] CHK002 The feature adds no REST call, and the owned WebSocket transport stays unchanged (spec Mist Cloud section, decision D-18).
- [x] CHK003 The menu 310 typed confirmation is exact and case sensitive (FR-004, `console.py` line 93).
- [x] CHK004 The menu 310 connected-only filter and offline exclusion match menu 309 (FR-004).

## Prompts and Cancel

- [x] CHK005 Each prompt treats end of input and an interrupt as a cancel (FR-026).
- [x] CHK006 A cancel at a prompt opens no shell and writes no file (FR-026).
- [x] CHK007 A cancel during collection writes only the collected rows and the rows with the status `cancelled` (spec edge case).

## Data Handling

- [x] CHK008 Output stays under the data folder (FR-025).
- [x] CHK009 The data folder is ignored by git (`.gitignore` line 95, research R85).
- [x] CHK010 Screenshots and traces from failed browser checks stay under the test-artifacts folder (FR-025, task T023).
- [x] CHK011 Each text cell passes the spreadsheet formula guard (FR-017, SC-004).
- [x] CHK012 A file above 64 MiB is not written (task T007).
- [x] CHK013 The CLI never overwrites an earlier file (FR-019).
- [x] CHK014 The menu removes a file that fails the read-back check (task T008).

## Logging and Secrets

- [x] CHK015 Log lines are ASCII only (FR-024).
- [x] CHK016 Log lines hold no token, password, or serial number (FR-024).
- [x] CHK017 Each action writes an info line before it and a debug line after it (FR-024).
- [x] CHK018 Fixtures and examples use synthetic values only (FR-031).
- [x] CHK019 The issue body forbids committing device names, identifiers, serials, credentials, and live examples. The plan follows that rule (issue body line 11).

## Review Gates

- [x] CHK020 Bandit reports no finding, and no finding is suppressed (task T031, global rule on security findings).
- [x] CHK021 The security review covers the new reader for JSON constants that break parsing (`native-json.md`, failure rules).
- [x] CHK022 The owned transport contract tests stay green (task T028).

## Notes

- CHK021 names the rejected JSON constants. The reader rejects them before it builds any row.
- CHK019 cites the issue body. The live check of task T034 records counts only.
