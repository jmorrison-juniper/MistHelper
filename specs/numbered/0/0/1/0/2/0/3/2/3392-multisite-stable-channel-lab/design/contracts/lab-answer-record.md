# Contract: Sanitized lab answer record

Each lab check produces one lab answer. The owner posts one comment on issue #3392 for each check. The comment holds only the fields in this contract. The owner writes each field by hand.

## Fields

Write the fields in this order. Each field appears on its own line, as `field: value`.

| Field | Allowed values | Meaning |
| - | - | - |
| check_id | L-AP-STABLE, L-SSR-STABLE, L-SSR-BETA, or L-SSR-ALPHA | The lab check that the answer covers |
| utc_recorded | ISO 8601 time in UTC with the Z suffix | The time of the submit call |
| route | The route path of the check, exactly as the contract names it | The operation that the call used |
| body_fields | The field names of the body, in the order of the contract, with no values | The shape of the request |
| submit_status | An integer status code, or none when no response arrived | The status of the submit call |
| error_field | The field name that the error names, or none | The field that the error points to |
| job_read | getOrgDeviceUpgrade or listOrgSsrUpgrades | The read operation that the owner used |
| job_status | One word of the job status enum: cancelled, completed, created, downloaded, downloading, failed, queued, or upgrading | The state of the job at the read |
| resolved_value | The build or channel string that the job read shows for the device family, or none | The value that the cloud applied |
| verdict | accepted, refused, or unknown | The result of the check, by the rules below |
| note | One line of plain text with no identifier | A short remark, for example the field that the owner repeated |

The job status words come from the schema at lines 115749 to 115760 (RC-78).

## Verdict rules

Apply the first rule that fits.

1. **Accepted (V-1)**: `submit_status` is 200, `job_status` is not failed, and `resolved_value` is not none.
2. **Refused (V-2)**: `submit_status` is 400 and `error_field` names the checked field. The checked field is `versions` for L-AP-STABLE and `channel` for each router check. A job that reads failed with an error about the checked field also gives refused.
3. **Unknown (V-3)**: Any other result. Examples are a field error (EC-1), an unnamed status (EC-2), a job that still reads queued or downloading, or a job read with no value.

A router value that one lab router accepts and another lab router refuses counts as refused (EC-3). The owner records one answer for each router.

## Never post

- Organization, site, device, router, or job identifiers. This includes MAC addresses.
- Tokens, passwords, cookies, session values, and IP addresses.
- A full response body. Post only the fields above.
- A screenshot or a copy of a cloud page that shows any value in this list.

Warning: a posted identifier or token stays in the issue history, even after an edit. The owner removes the value and rotates the credential.
