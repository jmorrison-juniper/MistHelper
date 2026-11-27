# Contract: Stats Page Walk

## Scope

This contract covers the walk that `_fetch_device_stats_for_monitoring` runs for one status check. The method starts at `src/operations/execution/firmware/firmware_manager.py` line 637.

## Requests

| Step | SDK call | Arguments |
| - | - | - |
| First page, org branch | `mistapi.api.v1.orgs.stats.listOrgDevicesStats` | Session, `org_id`, `type="all"`, `fields="*"`, and `limit=1000`. Research RC-43. |
| First page, site branch | `mistapi.api.v1.sites.stats.listSiteDevicesStats` | Session, `site_id`, `type="all"`, and `limit=1000`. Research RC-42. |
| Later pages | `mistapi.get_next` | Session and the previous page object. The SDK sends a request to the page's next link. Research RC-55 and RC-56. |

The arguments match the current code. The change adds no SDK function and no direct HTTP request.

## Page Shape Used by the Walk

| Field | Type | Use by the walk |
| - | - | - |
| `status_code` | integer or None | Must equal 200. None or any other value fails the page. |
| `data` | list, dictionary, or an empty dictionary | Must be a list. Any other type fails the page. |
| `headers` | mapping or None | `X-Page-Total` is checked after the last page. Its value must be an integer when present. |
| `next` | string or None | Followed when set. A value that repeats within one walk fails the walk. |

## Outcomes

| Condition | Walk result | Status check result |
| - | - | - |
| Every page passes, and the row count is at least the announced total | Returns the rows | Counts the active upgrades |
| A page status is missing, is not an integer, or is not 200 | Raises `RuntimeError` | Returns no count |
| A page body is not a list | Raises `RuntimeError` | Returns no count |
| A next link repeats | Raises `RuntimeError` | Returns no count |
| The row count is lower than the announced total | Raises `RuntimeError` | Returns no count |
| The announced total is not an integer | Raises `ValueError` | Returns no count |

The status check catches every exception through the existing `except Exception` block (line 722). It never returns a partial count.

## Error Text

The error text names the HTTP status only. The text has this form: `Device statistics page returned HTTP status <status>`. The response body never appears in the text. A repeated link has its own fixed text that names no body.

## Logging

- Before each request: one `info` line that names the scope. The line carries no body.
- After each page result: one `debug` line with the status and the row count.
- On failure: the existing `logging.exception` call in `_execute_monitoring_check` (line 723) writes the traceback.
