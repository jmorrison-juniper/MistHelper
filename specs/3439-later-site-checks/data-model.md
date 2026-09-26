# Data model: A later site check names an incomplete site list

**Issue**: #3439 | **Plan**: [plan.md](plan.md)

The change adds no stored field. It adds one method to one type, one error
type, and one error answer.

## `SiteList` (changed)

The type is in `src/upgrade_portal/app/routes/select.py`. Issue #3438 added it.

| Member | Type | Meaning |
| - | - | - |
| `rows` | list of site rows | One row for each site, in cloud order. No change. |
| `sites_complete` | bool | False when the site read lost a page. No change. |
| `counts_complete` | bool | False when the device count read lost a page. No change. |
| `read_is_whole(answer)` | static method | True when one read answer names no fault. No change. |
| `missing_sites(site_ids)` | method | New. Each named site identifier that no row holds, in the order of the request. |

## `SiteListIncompleteError` (new)

The type is in `src/upgrade_portal/app/routes/select.py`. The base class is
`Exception`.

| Member | Type | Meaning |
| - | - | - |
| `missing_count` | int | The count of named sites that the list does not hold. The log records it. |
| `raise_for_missing(missing_count, list_is_whole)` | class method | Raise the error when the count is above zero and the list is not whole. |

## The error answer (new)

| Field | Value |
| - | - |
| Status | 503 |
| Code | `site_list_incomplete` |
| Sentence | The portal did not read the complete site list, so it cannot check your site choice. Try again. |
| Page heading | The portal did not read the complete site list |

A script and a JSON client receive the shared error envelope.

```json
{
  "error": {
    "code": "site_list_incomplete",
    "message": "The portal did not read the complete site list, so it cannot check your site choice. Try again."
  }
}
```

A browser page receives the shared error page with the same code and the same
sentence. A refused form post also receives the link back to the form.

## State rules

- A refused check stores no site choice, no plan, no saved options, and no
  retry reference.
- A refused check starts no capture and takes no site lock.
- The portal never keeps a site read that lost a page. The next attempt
  therefore reads the cloud again.
