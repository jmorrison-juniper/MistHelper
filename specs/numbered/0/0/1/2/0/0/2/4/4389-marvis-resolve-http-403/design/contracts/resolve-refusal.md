# Contract: Resolve refusal handling

This contract defines the interface for one resolve request, the answer classes, the error text, and the results row. It applies to `MarvisActionsClient.resolve_action` and to `MarvisBulkResolver` in mode 3.

## 1. Request (unchanged)

- Method and path: `PUT /api/v1/labs/orgs/{org_id}/suggestions`. The path comes from `RESOLVE_PATH` (`client.py` line 33).
- Transport: `mist_put` on the mistapi session (`.venv\Lib\site-packages\mistapi\__api_request.py` line 303).
- Body fields: `row_key`, `status` set to `resolved`, `label` set to the resolution code, `comment`, and `resolve_time` (`selection.py` lines 412 and 413).
- Content type: `application/json`, set by the session method.

## 2. Answer classes

| Class | HTTP status | Client result | Mode 3 behavior |
| - | - | - | - |
| Accepted | 200 through 299 | Status and an empty error text | Continue. The verify read checks the row. |
| Refused, authorization | 401 or 403 | Status and the masked error text | Warn once. Stop. Later rows become `not_sent`. |
| Refused, other | Any other status | Status and the masked error text | Continue. The row becomes `error`. |
| No answer | No status | No status and the no-answer text | Continue. The row becomes `error`. |

Mistapi retries HTTP 429 before the client sees it (`.venv\Lib\site-packages\mistapi\__api_request.py` line 229). A 429 answer therefore reaches the client only after the retries end.

## 3. Error text

The error text starts with the words `HTTP`, a space, and the status number. A space and the masked body text follow. The masked body text is the JSON text of the response body.

Masking rules, applied in this order:

1. Replace each UUID-shaped value with the marker `<uuid>`. A UUID has the form of eight, four, four, four, and twelve hexadecimal characters.
2. Replace each value that follows the word `Token` or `Bearer` with the marker `<masked>`. The word stays.
3. Replace each email address with the marker `<email>`.
4. Replace each character outside printable ASCII with a question mark.
5. Keep at most 300 characters.

Example input body: `{"detail": "Organization 5b2c7e1a-9f3d-4c8b-a6e2-1d7f0c9b8a31 refused Token abc123XYZ for ops@example.com"}`

Example masked error text for HTTP 403: `HTTP 403 {"detail": "Organization <uuid> refused Token <masked> for <email>"}`

Rules 1 to 3 apply to the JSON text, so the quote characters stay in the output. A body that holds none of these values keeps its text.

## 4. Results row for a refused request

| Column | Value |
| - | - |
| `outcome` | `error` |
| `http_status` | The status number, for example 403 |
| `message` | The error text from section 3 |
| `verified_status` | Empty |
| `alarm_ack_outcome` | Empty. The row is not resolved, so no acknowledgement runs. |

## 5. Results row for a request that the stop rule leaves unsent

| Column | Value |
| - | - |
| `outcome` | `not_sent` |
| `http_status` | Empty |
| `message` | `Mist refused an earlier request with HTTP 403. This request was not sent.` For HTTP 401, the same sentence names 401. |
| `verified_status` | Empty |

## 6. Log lines

WARNING, emitted once for each run that a refusal stops:

`Mist refused the resolve request with HTTP 403. This run sends no later resolve request. Check the role of the API token in the Mist UI.`

For HTTP 401, the same sentence names 401.

DEBUG, emitted after each request: the existing debug line of `resolve_action` stays unchanged. It names the HTTP status number after the words `The resolve request returned HTTP`.

ASCII only. No token, password, or unmasked identifier appears in a log line.
