# Contract: CSV Import

## File rules

- Encoding: UTF-8. A byte order mark is optional.
- Size: at most 262144 bytes (D-8). A larger file fails before any row parses (TC-016).
- Rows: at most 500 data rows after the header (TC-017).
- Header: an exact, case-sensitive allowlist in this order: `mac`, `minutes`, `company`, `email`, `field1`, `field2`, and `field3`. A missing or extra header rejects the file (TC-018).
- Quoted cells may contain commas.

## Cell rules

| Column | Rule | Test |
| --- | --- | --- |
| mac | One device MAC address in an accepted form | TC-001, TC-002 |
| minutes | An integer from 1 to 259200. Required. No default applies. | TC-004, TC-005, TC-020 |
| company | At most 128 characters | TC-008 |
| email | At most 254 characters and a valid address format. May be empty. | TC-003, TC-008 |
| field1, field2, field3 | At most 128 characters each | TC-008 |

The column `field4` is not part of the import. The source writes `field4` (D-6).

## Duplicates

A normalized MAC address that appears more than once rejects every row after its first occurrence (TC-019).

## Preview and run

- The preview returns one validation result for each row and the reviewed-content hash (FR-023).
- The run needs the typed word IMPORT and the matching hash (D-7). No write starts before both match (TC-021 and TC-048).
- Rows run in file order (TC-042). Each row ends with one outcome: `succeeded`, `failed`, `unknown`, `rejected`, or `not_attempted`.
- The run stops on a final 429 response, a 401 or 403 response, an unknown outcome, or a failed audit write. Every later row shows `not_attempted` (TC-043).
