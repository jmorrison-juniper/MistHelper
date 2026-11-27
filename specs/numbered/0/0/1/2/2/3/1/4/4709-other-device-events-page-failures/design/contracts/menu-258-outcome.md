# Contract: Menu 258 Outcome Messages

**Scope**: Operator-visible output of menu 258. The handler is registered at `MistHelper.py` line 4998. The menu title at line 4999 does not change.

## 1. Message Table

All messages use ASCII characters. The `%d` and `%s` markers stand for values that the code supplies at run time.

| Event | Level | Message | File written | Menu returns |
| - | - | - | - | - |
| Operation starts | INFO | `Starting searchSiteOtherDeviceEvents export` | No | Yes |
| First request starts | INFO | `Calling searchSiteOtherDeviceEvents for site_id=%s (%s)` | No | Yes |
| Later request starts | INFO | `Requesting other-device event page %d for site %s` | No | Yes |
| Page answered | DEBUG | `Other-device event page %d returned HTTP %s with %d rows` | No | Yes |
| Complete read with zero rows | INFO | `! No other-device event data found for this site` | No | Yes |
| Complete read with rows | INFO | `! %d other-device event records exported to %s` | Yes | Yes |
| Page with an integer failure status | ERROR | `Other-device event page %d failed with HTTP %s for site %s` | No | Yes |
| Page with no integer status | ERROR | `Other-device event page %d returned no integer HTTP status for site %s` | No | Yes |
| Page with an empty or unusable body | ERROR | `Other-device event page %d has an unusable body for site %s` | No | Yes |
| Page with malformed JSON | ERROR | `Other-device event page %d returned malformed JSON for site %s` | No | Yes |
| Repeated cursor | ERROR | `Other-device event pagination repeated a cursor for site %s` | No | Yes |
| Total mismatch | ERROR | `Other-device event rows (%d) do not match the reported total (%d) for site %s` | No | Yes |
| Non-integer total or header | ERROR | `Other-device event total or header is not an integer for site %s` | No | Yes |
| Outer guard summary | ERROR | `Error fetching other-device events for site %s: %s` | No | Yes |
| Operator summary | INFO | `! Error fetching other-device event data: %s` | No | Yes |

The outer summary and the operator summary use the `RuntimeError` text of this change: `Other-device event export is incomplete. No file was written.`

## 2. Rules

1. The menu returns to its loop after every row. No exception leaves the operation (FR-014).
2. A rejected read prints one page ERROR line, one outer ERROR line, and one operator INFO line.
3. No message contains a response body, a cursor value, a URL, or a credential (FR-011).
4. Each page message names the page number and the site name.
5. The success message, the no-data message, and the start messages keep their current text.

## 3. Example Output for a Rejected Read

These lines show the expected text for a later page that returns HTTP 503. The site name `Branch` is synthetic.

```text
Other-device event page 2 failed with HTTP 503 for site Branch
Error fetching other-device events for site Branch: Other-device event export is incomplete. No file was written.
! Error fetching other-device event data: Other-device event export is incomplete. No file was written.
```

## 4. Test Links

| Message | Test |
| - | - |
| No-data message | Test 12 |
| Success message | Test 13 |
| Page with an HTTP failure status | Tests 3, 4, 6, 7a, 7b |
| Page with no integer status | Test 5 |
| Page with an empty, malformed, or non-object body | Tests 1, 2, 8 |
| Repeated cursor | Test 9 |
| Total mismatch | Test 10 |
| Non-integer header | Test 11 |
| Log redaction | Test 14 |
| Page-level INFO and DEBUG lines | Test 15 |
