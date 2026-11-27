# Contract: Mist verifySelfEmail for the menu 247 interactive path

## Endpoint

- Method and path: `GET /api/v1/self/update/verify/{token}` (OpenAPI lines 25910 to 25911, RC-43).
- Operation: `verifySelfEmail`, with the summary `verifySelfEmail` and the description `Verify Email change` (OpenAPI lines 25912 to 25913, RC-44).
- Responses: 200 (`SelfVerifyEmailSuccess`), 400 (`SelfVerifyEmailFailed`), 401, 403, 404, and 429 (OpenAPI lines 25915 to 25926, RC-44).

Source file: `documentation/mist-api-openapi31yaml.yaml` in the repository.

## SDK Function

- Installed package: mistapi 0.64.1 (`.venv\Lib\site-packages\mistapi`, the local install).
- Function: `verifySelfEmail(mist_session, token)` in `api\v1\self\update.py` (line 42, RC-51).
- URI: `/api/v1/self/update/verify/{token}`, built at line 61 (RC-52). The function sends the request with `mist_session.mist_get`.

## Caller in This Repository

- `SelfAccountExporter._verify` calls the function once (exporter line 92, RC-15). The call belongs to the interactive path.

## Unattended Rule (FR-007)

- The unattended run never calls this function for option 247.
- The operator-only stop ends the option before the call. The stop happens inside the token prompt (RC-13 and RC-14 show the prompt and the empty branch).
- The unattended run never writes the verification audit row for option 247 (FR-008). The audit write follows the call in the interactive path only.

## Token Rule

- The token is a single-use credential. No log line, record, STATUS file, or summary holds a token value.
- The regression uses an empty answer. No fabricated token appears in any test.

## Response Handling (Interactive Path, Unchanged)

The interactive path keeps its existing response handling. The exporter tests (RC-28) cover the cancel path and the SDK call path.
