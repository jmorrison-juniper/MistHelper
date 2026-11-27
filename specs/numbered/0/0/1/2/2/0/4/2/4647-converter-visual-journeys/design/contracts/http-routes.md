# Contract: Converter HTTP routes (unchanged)

This record changes no route. The page calls these routes, and the journey tests depend on their shapes.

## Routes

| Method and path | Request | Success | Failure | Evidence |
| - | - | - | - | - |
| GET `/cisco-config-converter/` | None | HTML page from `converter.html` | Not applicable | RC-18 |
| POST `/cisco-config-converter/preview` | Form data with one `file`, plus `name` and `type` fields, and the CSRF token | 200 JSON proposal | 400 JSON error with `error` text for invalid input | RC-16, RC-19, RC-22 |
| POST `/cisco-config-converter/review` | JSON proposal body, plus the `X-CSRFToken` header | 200 JSON proposal | 400 JSON error for an invalid body. 409 JSON error when the state check fails. | RC-17, RC-20, RC-23, RC-100 |
| POST `/cisco-config-converter/export` | JSON proposal body, plus the `X-CSRFToken` header | 200 JSON proposal with an attachment header | 400 JSON error for an invalid body. 409 JSON error when the review check fails. | RC-17, RC-20, RC-21, RC-100 |

## Responses

- Every converter response carries `Cache-Control: no-store` (RC-06).
- The export response names the file `cisco-proposal.json` in its `Content-Disposition` header (RC-21).
- The host guard `verify_host` rejects registration without the converter request class and CSRF protection (RC-101).

## Proposal shape

The proposal type declares three fields (RC-25):

- `gateway_template`: the template name and type, and optional DNS servers.
- `unsupported_items`: a list of source line, command text, and reason.
- `known_gaps`: a list of text entries.

The page renders each field with text APIs only. Any change to this shape belongs to issue #4641. This record does not change it.
