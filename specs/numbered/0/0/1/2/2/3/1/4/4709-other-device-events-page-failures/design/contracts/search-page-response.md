# Contract: Search Page Response

**Scope**: Request and response rules for `GET /api/v1/sites/{site_id}/otherdevices/events/search` as menu 258 uses it.

## 1. Request

- **First request**: `mistapi.api.v1.sites.otherdevices.searchSiteOtherDeviceEvents(session, site_id)`. The SDK file is `.venv\Lib\site-packages\mistapi\api\v1\sites\otherdevices.py`. Its signature starts at line 144, and its request call is at line 221 (RC-70). This change adds no query parameter (FR-016).
- **Later requests**: `mistapi.get_next(mist_session=session, response=previous_page)`. The helper requests the body `next` value through `mist_get`. The file is `.venv\Lib\site-packages\mistapi\__pagination.py`, line 34 (RC-67).
- **Path**: `/api/v1/sites/{site_id}/otherdevices/events/search`. The OpenAPI file is `documentation/mist-api-openapi31yaml.yaml`, line 35577 (RC-22).

## 2. Response Body for HTTP 2xx

The schema is in `documentation/mist-api-openapi31yaml.yaml`. Its fields appear at the lines below.

| Field | Type | Rule in this change | Schema line |
| - | - | - | - |
| `results` | List of objects | Required for an object body (FR-004). | 94504 to 94505, and 94516 to 94519 |
| `total` | Integer | Optional. When present, it must equal the row count at the end of the read (FR-007). | 94511 (RC-23) |
| `next` | String or null | Optional. An absent or empty value ends the read. A repeated value fails the read (FR-006). | 94500 (RC-24) |
| `end` | Integer | Not used. | 94492 to 94495 |
| `limit` | Integer | Not used. | 94496 to 94499 |
| `start` | Integer | Not used. | 94507 to 94510 |

The schema sets `additionalProperties` to `false` and names no required field (lines 94488 to 94515).

## 3. Response Headers for List Pages

The SDK reads these headers in `_check_next`, in `.venv\Lib\site-packages\mistapi\__api_response.py`, lines 75 to 80 (RC-69).

| Header | Type | Rule in this change |
| - | - | - |
| `X-Page-Total` | Integer | When present, it sets the expected total when the body has no `total` (FR-008). |
| `X-Page-Limit` | Integer | When present, it must parse as an integer (FR-008). |
| `X-Page-Page` | Integer | When present, it must parse as an integer (FR-008). |

## 4. Acceptance Rules

| Condition | Result |
| - | - |
| Integer status from 200 through 299, an object body with a list `results`, object rows, integer headers when present | Accept the page. |
| Status is `None` | Reject. The page has no integer status (FR-003). |
| Status is outside 200 through 299 | Reject (FR-001, FR-002, FR-003). |
| Status is 2xx and the body text is empty | Reject. The page is unusable (FR-004). |
| Status is 2xx and the body text is malformed JSON | Reject. The body is malformed (FR-004). |
| Status is 2xx and the body is an object without a list `results` | Reject (FR-004). |
| A row is not an object | Reject (FR-004). |
| `next` is absent or empty | Last page. The read goes to the total check. |
| `next` repeats an earlier value | Reject (FR-006). |
| `total` is present and is not an integer | Reject (FR-007). |
| `total` is present and differs from the row count at the end | Reject (FR-007). |
| An `X-Page-*` header is present and is not an integer | Reject (FR-008). |

## 5. Transport and Retry

- A connection failure returns an `APIResponse` with status `None` (`__api_request.py` line 258, RC-72). The rule above rejects that page.
- The SDK retries HTTP 429 inside the request layer, starting at `__api_request.py` line 228 (C-4). This change adds no retry. A 429 that remains after the SDK retries is a rejected page.

## 6. Synthetic Examples

These examples use invented values. They contain no credential.

- **Accept**: a 200 response with `results` holding one object and `total` 1, and no `next` value.
- **Reject**: a 200 response with `results` holding one object, `total` 2, and no `next` value. The row count differs from the total.
- **Reject**: a 503 response with an empty body. The status is outside 2xx, and the body is unusable.
