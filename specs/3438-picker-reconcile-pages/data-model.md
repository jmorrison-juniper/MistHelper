# Data model: The site picker and the reconciliation read name a lost page

**Issue**: #3438 | **Plan**: [plan.md](plan.md)

This change adds no stored field. The three types below live in memory for
one request.

## Picker read

The picker read reuses `DeviceRead` from `src/upgrade_portal/capture/devices.py`.

| Field | Type | Rule |
| - | - | - |
| `section` | text | The read name, such as `listOrgSites`. |
| `records` | list of maps | The rows of each page that arrived. |
| `partial_reasons` | list of maps | One entry for each fault. Empty after a whole read. |

Each entry of `partial_reasons` holds `section`, `reason`, and `http_status`.
A lost later page gives the reason `page_count_mismatch`. A read that cannot
run gives the reason `read_not_run` and the status 0.

A read is whole when `partial_reasons` is empty. The cache keeps a whole read
only.

## Site list

`SiteList` is a new frozen type in `src/upgrade_portal/app/routes/select.py`.

| Field | Type | Rule |
| - | - | - |
| `rows` | list of maps | One row for each site, in cloud order. The row shape does not change. |
| `sites_complete` | true or false | True when the site read is whole. |
| `counts_complete` | true or false | True when the device count read is whole. |

An answer with no `partial_reasons` field reads as whole. A stand-in that
answers a plain list therefore gives two true flags.

## Unread target

An unread target is one evidence row of the reconciliation reader. It holds
these values before the stored fallbacks apply.

| Field | Value |
| - | - |
| `task_state` | `unavailable` |
| `write_state` | `unavailable` |
| `running_version` | empty text |
| `fwupdate_status` | empty text |
| `sources` | `stored` |
| `observed_at` | null |
| `firmware_success` | false |
| `is_complete` | false |

The stored fallbacks then add `target_id`, `stored_stop_result`, `task_id`,
`driver_state`, and `version_target`. A fallback never replaces a value in the
table above.
