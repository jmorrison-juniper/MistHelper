# Data Model: Other-Device Event Export Fails Closed on Failed Pages

**Scope**: Entities and state transitions for menu 258. The change reads search pages and writes one export outcome. It adds no stored state, no table, and no schema.

## 1. Entities

### 1.1 Search page

One response from `searchSiteOtherDeviceEvents` or from `mistapi.get_next`. The SDK fills these fields.

| Field | Source | Meaning |
| - | - | - |
| `status_code` | SDK response | HTTP status as an integer. `None` after a connection failure (RC-72). |
| `data` | SDK response | Parsed body. An object with `results`, or a list. The default is `{}`, which also marks a body that did not parse (RC-68). |
| `raw_data` | SDK response | Body text. Used to tell an empty body from a malformed body. |
| `next` | SDK response | Cursor or URL for the next page. The default is `None`, which marks the last page (RC-68). |
| `headers` | SDK response | Holds `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` for list responses (RC-69). May be `None`. |

Schema reference: the OpenAPI schema `response_events_other_devices_search` (lines 94488 to 94515) lists `end`, `limit`, `next`, `results`, `start`, and `total`. It sets `additionalProperties` to `false` and names no required field (RC-23, RC-24). Each item of `results` refers to `event_otherdevice` (lines 94516 to 94519).

Validity rules for one search page:

- The status is an integer from 200 through 299 (FR-001 to FR-003).
- The data is a list, or an object with a list `results` (FR-004).
- Each row is an object (FR-004).
- `total`, when present, is an integer (FR-007).
- Each `X-Page-*` header, when present, is an integer (FR-008).

### 1.2 Event row

One object from `results`. Each row becomes one CSV row through the existing flattening and escaping steps.

- **Natural key**: `mac` with `timestamp` (strategy lines 527 to 532, RC-12).
- **Uniqueness**: the writer owns the key behavior. This change does not alter it (FR-017).

### 1.3 Read

One pass over the pages for one site.

| Attribute | Rule |
| - | - |
| Pages | Ordered. Page 1 comes from the SDK search call. Later pages come from `mistapi.get_next`. |
| Accepted rows | Rows of accepted pages only. A rejected page contributes no rows (FR-009). |
| Expected total | From body `total` when present, otherwise `X-Page-Total` when present, otherwise none (A-2). |
| Requested cursors | Set of every `next` value that the read requested. A repeated value ends the read (FR-006). |

### 1.4 Export outcome

The final result of one read. Each value gives one action.

| Value | Condition | Action |
| - | - | - |
| `written` | Complete read with at least one row. | One writer call with every row (FR-013). |
| `no_data` | Complete read with zero rows. | Print the no-data message. No writer call (FR-012). |
| `failed` | Any rejected page, cursor, or total check. | ERROR lines. No writer call (FR-009). The outer guard prints the operator summary (FR-014). |

### 1.5 Site

- **Natural key**: `site_id` from the site resolver (RC-14).
- **Output name**: `SiteOtherDeviceEvents_<site name with spaces replaced by underscores>.csv`. The name rule is unchanged (FR-017).

## 2. State Transitions

1. **Requested first page** moves to **Page accepted** when the status and body pass. It moves to **Failed** when either check fails.
2. **Page accepted** moves to **Requested next page** when `next` holds a non-empty value that the read has not requested. It moves to **Complete check** when `next` is absent or empty. It moves to **Failed** when `next` repeats an earlier value.
3. **Requested next page** moves to **Page accepted** or **Failed**, in the same way as step 1.
4. **Complete check** moves to **Outcome written** or **Outcome no data** when the row count matches the expected total, or when no total exists and the row count is zero or positive. It moves to **Failed** when a total is not an integer, a header is not an integer, or the row count differs from the total.
5. **Outcome written** calls the writer once. **Outcome no data** prints the no-data message.
6. **Failed** calls no writer. It leaves the menu loop by return, and the outer guard logs the summary.

Each path ends in exactly one of three outcomes: written, no data, or failed. No path writes a partial file.

## 3. Invariants

- The writer call count is zero or one for each read.
- The writer call count is one only when the outcome is written.
- Every rejected read logs at least one ERROR line that names the page or the check.
- No log line contains a body, a cursor value, a URL, or a credential (FR-011).
- The export filename and the composite key stay unchanged (FR-017).
