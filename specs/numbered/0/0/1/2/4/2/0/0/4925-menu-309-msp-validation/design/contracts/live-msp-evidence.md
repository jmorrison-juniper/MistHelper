# Contract: Live MSP evidence (counts only)

The owner posts this evidence as one comment on issue #4925 after each live check. The comment holds counts and the fields below. It holds no name, identifier, token, password, 2FA code, site name, or device name. The repository is public, so a posted value stays in the history.

## Fields

| Field | Type | Rule |
| - | - | - |
| check_id | text | `CLI` or `PORTAL`. |
| recorded_utc | text | The time of the check in UTC, `YYYY-MM-DDTHH:MM:SSZ`. |
| checkout_sha | text | The forty-character commit SHA of the checkout. It equals the SHA of `main`. |
| scope | text | `msp` or `organization`, from step 1. Task 5 passes only with `msp`. |
| organizations_in_scope | integer | The number in the line `Organizations in scope`. |
| step2_lines | integer | The count of step 2 lines. It equals `organizations_in_scope`. |
| step2_unread_lines | integer | The count of step 2 lines that say `was not read`. |
| outcome_rows_unread | integer | The count of CSV outcome rows for unread organizations. It equals `step2_unread_lines`. |
| xml_failed_organizations | integer | The count of organization elements with `status="failed"`. It equals `step2_unread_lines`. |
| step4_organizations | integer | The count of step 4 lines. |
| confirmed_targets | integer | The number in the phrase `RUN N TARGETS`. |
| report_rows | integer | The number of rows in the CSV report. |
| master_xml_devices | integer | The number of devices in the master XML file. |
| run_status | text | `complete` or `partial`. |
| secret_hits_report | integer | The count of matches in the CSV report. It must be 0. |
| secret_hits_xml | integer | The count of matches in the master XML file. It must be 0. |
| secret_hits_run_folder | integer | The count of matches in the run folder. It must be 0. |
| secret_hits_log | integer | The count of matches in the log. It must be 0. |
| result | text | `pass` when every rule holds. Otherwise `fail`. |
| new_issue | integer | The number of the new issue for a failure. Empty for a pass. |

## Rules

- A check passes only when `organizations_in_scope`, `step2_lines`, and `scope` meet the spec, and every secret count is 0.
- A check fails when one count does not match its rule. A failed check names its cause in the new issue (FR-010).
- The owner counts the secret hits with the command in `design/quickstart.md`, section 3, step 10. The owner types each secret at the prompt, and the secret text is never written into the record or the comment.

## Form

The owner writes one line for each field, in the order of the table above. Each line has the form `field: value`. The value is a number, or one of the listed words.
