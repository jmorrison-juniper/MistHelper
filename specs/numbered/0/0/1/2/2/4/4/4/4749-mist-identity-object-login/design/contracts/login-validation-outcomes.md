# Contract: Sign-In Validation Outcomes

## Layers

- `AuthService.validate_token` returns the privileges type (research row 10).
- The middleware rejects privileges that hold no email and no org id (research row 11).
- The login route `POST /auth/login` rejects empty privileges (research rows 14 and 15).

## Outcome Table

| Case | AuthService result | Middleware response | Login response |
|------|--------------------|---------------------|----------------|
| Valid token, 2xx identity, active token matches | Identity privileges | Request accepted | Session created |
| 2xx identity, active token does not match | Empty privileges | HTTP 401, detail "Invalid or expired token" | HTTP 401, detail "Invalid API token" |
| 2xx empty body | Empty privileges | HTTP 401, detail "Invalid or expired token" | HTTP 401, detail "Invalid API token" |
| 2xx identity, no active token | Empty privileges | HTTP 401, detail "Invalid or expired token" | HTTP 401, detail "Invalid API token" |
| 4xx response | Empty privileges | HTTP 401, detail "Invalid or expired token" | HTTP 401, detail "Invalid API token" |
| 5xx response | Unavailable error | HTTP 503 | HTTP 503 |
| Transport fault | Unavailable error | HTTP 503 | HTTP 503 |

## Notes

- The quoted detail strings do not change. They are identifiers for the operator message.
- The unavailable error does not reach the operator as a token rejection. Issue #4748 owns any change to that mapping.
- The active-token check runs only after a 2xx response (decision D-4).
