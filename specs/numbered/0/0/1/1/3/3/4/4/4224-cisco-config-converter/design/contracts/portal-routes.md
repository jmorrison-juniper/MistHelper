# Contract: Converter Portal Routes

**Scope**: HTTP routes of the converter blueprint. The URL prefix is `/cisco-config-converter` (R-33). Routes marked "On main" exist on `main` today (R-34). Routes marked "Planned" belong to the tasks named in the table.

## Route Table

| Route | Method | Status | Request | Success response | Error codes | Notes |
|---|---|---|---|---|---|---|
| `/cisco-config-converter/` | GET | On main | None | HTML page with `data-testid="cisco-converter"` (R-14) | None | The page loads in the isolated host. The shared tab waits for T032. |
| `/cisco-config-converter/preview` | POST | On main (R-34) | Multipart form with `csrf_token`, `file`, `name`, and `type`. The body limit is 16 MiB plus 16 KiB (R-26). | JSON proposal with a SHA-256 digest (R-39) | 400 for invalid input. 413 above the body limit (R-43). | Makes no Mist call. Writes no file. |
| `/cisco-config-converter/review` | POST | On main (R-34) | JSON with the `X-CSRFToken` header | JSON review state | 400 when no current preview exists or the digest changed | Stores the digest in the signed session. |
| `/cisco-config-converter/export` | POST | On main (R-34). Typed word EXPORT added by T018. | JSON with the `X-CSRFToken` header and the typed word EXPORT (FR-035) | JSON file of the reviewed proposal | 400 when the proposal is not reviewed, was edited, or the word is wrong | The export holds no credential and no configuration value. |
| `/cisco-config-converter/discover` | POST | Planned (T020) | JSON with the organization identifier and the CSRF header | Read-only status, sites, and gateways | 401 when no identity exists. 403 when permission fails. 429 after the SDK retries. | Read only. Makes no write. |
| `/cisco-config-converter/apply` | POST | Planned (T022) | JSON with the approval record and the typed word APPLY | Operation run record | 400 for a wrong word. 403 when the write family is disabled. 409 when state changed. 429 after the SDK retries. | Gated by gates G2, G4, and G5. Never retries a write. |
| `/cisco-config-converter/administration/` routes | POST | Planned (T026, T028) | JSON with the scope, the typed word CONFIRM, and the backup identifier | Operation run record | 400, 403, and 409 as in apply | Gated. Recovery needs a fresh approval. |

## Common Rules

- `CSRFProtect` must stay active. Each JSON POST sends the `X-CSRFToken` header (R-27).
- The host must set `ConverterRequest` before blueprint registration. Registration fails without it (R-27, R-13).
- Each response carries `Cache-Control: no-store` (R-35).
- An error message names the problem. It never shows a source value, a credential, or a traceback.
- The typed words are EXPORT, APPLY, and CONFIRM (D-5).
- A route that writes to Mist checks the write family, the approval, and the current review before the first SDK call.
- The route layer calls the state layer. The state layer calls the mistapi methods named in `mist-gateway-template.md`.

## Status Codes

| Code | Meaning in this contract |
|---|---|
| 200 | The operation finished. |
| 400 | The input is invalid, or a typed word is wrong. |
| 401 | No operator identity is available for a cloud route. |
| 403 | The permission or the write family does not allow the operation. |
| 404 | The target does not exist in the lookup result. |
| 409 | The current state changed after the review or the approval. |
| 413 | The request exceeds the body limit. |
| 429 | The SDK retried HTTP 429 and the final response is still 429. The outcome reads indeterminate for a write. |
