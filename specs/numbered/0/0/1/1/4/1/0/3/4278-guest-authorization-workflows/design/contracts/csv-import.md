# Contract: CSV import

**Record**: `specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows`

**Scope**: The import creates grants and updates for one organization. Each row names its site and WLAN by identifier. Names never select a target (FR-021).

## 1. File Format

- Encoding: UTF-8. A byte order mark is allowed.
- Line endings: LF or CRLF.
- Separator: comma. A quoted cell can hold commas, quotes (doubled), and line breaks.
- The first row is the header. The header names are exact and lowercase.
- The file holds at most 262144 bytes (D-13, FR-020).
- The file holds at most 200 data rows (D-13, FR-020).

## 2. Header Names

The header holds these ten names in any order.

| Name | Required | Rule |
| --- | --- | --- |
| `site_id` | Yes | Must appear in the organization site list (`listOrgSites`) |
| `wlan_id` | Yes | Must appear in the site WLAN list (`listSiteWlans`) |
| `guest_mac` | Yes | 12 hexadecimal characters after removing `:` and `-` |
| `minutes` | Yes | Integer from 1 through 259200 |
| `company` | No | Text, at most 128 characters |
| `email` | No | Text, at most 128 characters. Not sent to DNS or to any other service |
| `field1` | No | Text, at most 128 characters |
| `field2` | No | Text, at most 128 characters |
| `field3` | No | Text, at most 128 characters |
| `field4` | No | Text, at most 128 characters |

A header that holds any other name rejects the file. A missing required name rejects the file. A duplicate name rejects the file.

## 3. Row Rules

- A row with more cells than the header rejects with category `extra_field`.
- A row with fewer cells than the header rejects with category `missing_field`.
- Two rows with the same `site_id`, `wlan_id`, and normalized MAC address both reject with category `duplicate_target` (TEST-021).
- A row with an unknown `site_id` or `wlan_id` rejects with category `unknown_scope`.
- A row with a name in place of an identifier rejects with category `name_not_allowed`.
- A text cell that starts with `=`, `+`, `-`, or `@` keeps its text. The feature exports no file, so no formula escape applies in this feature. A later export must escape it through the shared CSV helpers.

## 4. Preview

- The preview reads the file once. It checks the byte count before parsing (TEST-019).
- Each row gets a validation result. A valid row shows `valid`. A rejected row shows the category.
- The preview returns the file digest, the rows digest, the row count, and the byte count.
- The preview sends no Mist call and writes no intent row (TEST-022).

## 5. Run

- The typed word `IMPORT` and the rows digest must match the preview (D-12).
- Rows run one at a time, in row-number order (FR-023).
- Each valid row follows the write sequence in `design/contracts/audit.md` Section 3.
- A stop condition ends the run. The stop conditions are `rate_limited`, `unknown`, and `audit_failed` (FR-024).
- Each row after a stop shows `not_attempted`.
- The run reports one outcome for each row (SC-004).

## 6. Example With Fictional Values

```text
site_id,wlan_id,guest_mac,minutes,company,email,field1,field2,field3,field4
11111111-1111-4111-8111-111111111111,22222222-2222-4222-8222-222222222222,02:00:00:00:00:01,1440,Example Company,guest.one@example.invalid,,,,
33333333-3333-4333-8333-333333333333,44444444-4444-4444-8444-444444444444,02-00-00-00-00-02,60,,,,,,
```

The example uses fictional identifiers and the reserved `.invalid` domain.

## 7. Limits Not Covered by This Contract

- The issue asks maintainers to approve these limits (UR-5 in `analysis.md`). The values remain in force until the owner records a change.
- The feature does not parse a file larger than 262144 bytes.
