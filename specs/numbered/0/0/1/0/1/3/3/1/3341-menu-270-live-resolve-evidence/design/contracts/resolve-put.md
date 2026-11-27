# Contract: Resolve Request

This contract describes the one request that the live check sends to Mist. The client sends it through `MarvisActionsClient.resolve_action`. Research rows 5, 6, 7, 15, 16, and 43 support each claim.

## Request

- **Method**: PUT.
- **Path**: `/api/v1/labs/orgs/{org_id}/suggestions`. The `{org_id}` value comes from the organization of the run (row 5).
- **Transport**: `APISession.mist_put(uri, body)` from the pinned mistapi package (row 43).
- **Count**: one request for each action. The live check sends exactly one request (FR-002).

| Field | Type | Value |
| - | - | - |
| `row_key` | text | The `row_key` of the action. The API finds the action by this key. |
| `status` | text | The fixed value `resolved` (row 16). |
| `label` | text | The key of the resolution code (row 15). |
| `comment` | text | The comment of the run. It can be empty. |
| `resolve_time` | integer | Epoch milliseconds. One value serves the whole run (row 15). |

The body holds no `suggestion_id` field. A test asserts this rule (test 21 in the test set of `tasks.md`).

## Response Handling

- **Any HTTP 2xx status**: Mist accepted the request. The row keeps the interim outcome `sent` until the verify read decides (rows 7, 9, and 12).
- **Any other HTTP status**: the outcome is `error`. The results row holds the HTTP status and the error text (rows 7 and 12). A test covers a refused request and a server error (tests 4 and 5 in the test set).
- **No HTTP answer**: the status is empty. The error text points to `data\script.log` (test 6 in the test set).
- **Long error text**: the error text is shortened for one results cell. A test covers this rule (`test_a_long_error_body_is_shortened` in `test_client.py`, covered by row 20).

## Compatibility

The path is a beta path. The OpenAPI document does not describe it (row 42). The mistapi package holds no method for it (row 50). A change of the path or the body fails the path test and the body test (tests 1 and 2 in the test set).
