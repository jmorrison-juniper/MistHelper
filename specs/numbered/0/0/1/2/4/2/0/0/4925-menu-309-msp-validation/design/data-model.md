# Data Model: Validate menu 309 with an MSP login

## 1. Overview

This record stores no database rows. The entities below describe the counts that the owner posts for each live check. The code entities are defined in the 4920 record and in `src/operations/exporting/ex_hardware_inventory/`. Section 4 cites the code rules.

## 2. LiveCheckRun

One live check is one run of menu 309 by the owner, with the counts of that run.

| Field | Type | Source | Rule |
| - | - | - | - |
| check_id | text | owner | `CLI` or `PORTAL`. |
| recorded_utc | text | owner | UTC time in ISO 8601 form, `YYYY-MM-DDTHH:MM:SSZ`. |
| checkout_sha | text | owner | Forty hexadecimal characters. Equal to the SHA of `main`. |
| scope | text | step 1 | `msp` or `organization`. Only `msp` passes task 5. |
| organizations_in_scope | integer | step 1 | The number in the line `Organizations in scope`. |
| step2_lines | integer | step 2 | The count of step 2 lines. Equal to `organizations_in_scope`. |
| step2_unread_lines | integer | step 2 | The count of step 2 lines that say `was not read`. |
| outcome_rows_unread | integer | CSV report | The count of outcome rows with an empty `site_id` and `collection_status` `failed`. Equal to `step2_unread_lines`. |
| xml_failed_organizations | integer | master XML file | The count of organization elements with `status="failed"`. Equal to `step2_unread_lines`. |
| step4_organizations | integer | step 4 | The count of step 4 lines. |
| confirmed_targets | integer | step 3 | The number in the phrase `RUN N TARGETS`. |
| report_rows | integer | step 4 | The number in the line `Report` for the CSV report. |
| master_xml_devices | integer | step 4 | The number in the line `Master XML` for the master XML file. |
| run_status | text | step 4 | `complete` or `partial`. |
| secret_hits_report | integer | owner search | Must be 0. |
| secret_hits_xml | integer | owner search | Must be 0. |
| secret_hits_run_folder | integer | owner search | Must be 0. |
| secret_hits_log | integer | owner search | Must be 0. |
| result | text | owner | `pass` or `fail`. |
| new_issue | integer | owner | The issue number for a failure. Empty for a pass. |

The natural key is `check_id` with `recorded_utc`. Each check posts once.

## 3. Step 1 and step 2 values

The console provides these values. They are not stored as rows.

- `scope` is `msp` when the console prints `Scope: MSP`. The console prints `Scope: organization` otherwise.
- Each step 2 line names one organization. The record stores no name. It stores the count only.
- A step 2 line that says `was not read` names one failed organization. It is counted in `step2_unread_lines`.

## 4. OrganizationOutcome (existing rules)

The code and the 4920 contracts define these rules.

| Field | Source | Rule |
| - | - | - |
| org_id | CSV column `org_id` | Never recorded in evidence. |
| record_type | CSV column `record_type` | `device_outcome` for an unread organization (`operation.py` line 130). |
| collection_status | CSV column `collection_status` | `failed` for an unread organization (`report/columns.py` line 52). |
| site_id, site_name, device_id, device_name | CSV columns | Empty for an unread organization. |
| organization element | master XML file | One `organization` element with `status="failed"` and no site (`run/master_xml.py` lines 414 and 416). |

The CSV natural key is `org_id`, `device_id`, and `item_path`. The 4920 contract `report-csv.md` (research row R-91) states it.

## 5. EvidenceRecord

| Field | Rule |
| - | - |
| evidence_id | One value for each LiveCheckRun. |
| counts | The fields of section 2. |
| posted_on | The time of the issue #4925 comment. |
| contract | `design/contracts/live-msp-evidence.md`. |

## 6. State transitions

LiveCheckRun moves through these states:

1. `planned`: the owner has the checkout SHA and the steps of `design/quickstart.md`.
2. `started`: the owner runs `python MistHelper.py --login --menu 309` or `--web-portal`.
3. `counted`: the owner has read the step 1 and step 2 lines and the files.
4. `passed`: every rule of section 2 holds. The secret hits are 0 in all four locations.
5. `failed`: a rule does not hold. The owner opens a new issue (FR-010). The new issue number goes in `new_issue`.

A LiveCheckRun never moves to `passed` when a count does not match.
