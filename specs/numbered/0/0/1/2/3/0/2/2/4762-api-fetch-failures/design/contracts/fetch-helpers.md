# Contract: Fetch Helpers

## Scope

The contract covers two static methods of `APICoreFetchUtils` in `src/mist/access/api/api_core_fetch_utils.py`:

- `all_sites_with_limit(org_id: str) -> list[dict[str, Any]]`
- `all_inventory_with_limit(org_id: str) -> list[dict[str, Any]]`

Both methods keep their signatures.

## Mist Calls

| Helper | First-page call | Arguments kept | Source |
| - | - | - | - |
| `all_sites_with_limit` | `mistapi.api.v1.orgs.sites.listOrgSites` | session, `org_id`, `limit=DEFAULT_API_PAGE_LIMIT` | Rows R02 and R87 to R88 |
| `all_inventory_with_limit` | `mistapi.api.v1.orgs.inventory.getOrgInventory` | session, `org_id`, `vc=True`, `limit=DEFAULT_API_PAGE_LIMIT` | Rows R05, R83 to R84 |

Later pages come from `mistapi.get_next` (row R94). The helper passes the session and the previous response to it.

## Response Rules

Each page follows these rules in order. The first matching rule applies.

| Condition | Result |
| - | - |
| Status is missing | Raise `APIFetchError`. The cause is `no HTTP status`. |
| Status is outside 200 to 299 | Raise `APIFetchError`. The cause is the status code, for example `HTTP status 503`. |
| 2xx payload is a list | Add its items to the result. |
| 2xx payload is a dictionary with a `results` list | Add the items of `results` to the result. |
| 2xx payload has another shape | Raise `APIFetchError`. The cause is `unexpected payload`. |
| The next link equals an earlier next link | Raise `APIFetchError`. The cause is `repeated next link`. |
| No next link | Stop paging and return the result. |

An empty list on a 2xx page is valid. A successful read with no items returns an empty list.

## Errors

- Class: `APICoreFetchUtils.APIFetchError`, a subclass of `RuntimeError`.
- Message format: the operation name, the org ID, and the cause, in that order.
- Operation names: `listOrgSites` and `getOrgInventory`.
- The error never contains a credential or a token.

## Logging

- Before the first request, log at info level. Name the operation and the org ID.
- Before each later request, log at info level. Name the page number and the org ID.
- After a successful read, log at debug level. Give the item count.
- On failure, log at error level. Give the operation, the org ID, and the cause. Then raise.
- All log text is ASCII.

## Structure Limits

- `_collect_pages` takes four parameters: the session, the first response, the operation name, and the org ID.
- `_collect_pages` has four logical blocks: the page loop, the status check, the payload check, and the repeated-link check.
- `_collect_pages` has 25 lines or fewer.
- The class `APICoreFetchUtils` has five members: `APIFetchError`, `all_sites_with_limit`, `all_inventory_with_limit`, `get_api_response_data`, and `_collect_pages`.
