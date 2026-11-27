# Contract: Mist GET /api/v1/self Response

## Request

- Method and path: `GET /api/v1/self` (research row 80 for the SDK request, and row 32 for the OpenAPI path).
- Parameters: none.
- SDK call: `mistapi.api.v1.self.self.getSelf`, called with the SDK session only (research row 80).

## Success Response

- Status: HTTP 200, with the response `Admin` (research row 33).
- Body: the `admin` object (research row 34).
- Property used by the record: `privileges` (research row 35).
- Rule: one non-empty dictionary becomes one identity record for the object endpoint `self_identity` (decision D-1).

## Error Responses

- Status: any non-2xx status.
- Body: an error body. The list layer keeps the status and the body, and it creates no identity record (decision D-3, and research row 1 for the list rule).
- Handling: a 4xx status yields empty privileges. A 5xx status or a transport fault raises the unavailable error (spec FR-008).

## Mapping to the Service Result

| Response | Service result | Sign-in outcome |
|----------|----------------|-----------------|
| 2xx, non-empty dictionary | `ApiResult(200, [identity])` | Identity parsed when the active token matches the supplied token |
| 2xx, list | `ApiResult(200, list)` | First record parsed when the active token matches the supplied token |
| 2xx, empty dictionary | `ApiResult(200, [])` | Empty privileges, which return HTTP 401 |
| Non-2xx, 4xx | `ApiResult(status, error body)` | Empty privileges, which return HTTP 401 |
| Non-2xx, 5xx | `ApiResult(status, error body)` | Unavailable error, which returns HTTP 503 |
| Transport fault | Exception from the SDK call | Unavailable error, which returns HTTP 503 |
