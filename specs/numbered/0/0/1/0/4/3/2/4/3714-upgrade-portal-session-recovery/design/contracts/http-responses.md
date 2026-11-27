# Contract: HTTP Responses for Protected Requests

This contract states the response for each protected request outcome after the change. Rows that repeat existing behavior cite the source line.

## Outcomes

| Outcome | Client | Status | Response | Source |
| - | - | - | - | - |
| Valid session, registry hit or recovery succeeded | Any | The route status | The route body | Unchanged route logic |
| No session, unknown owner key, mismatch, expiry, or failed validation | JSON client | 401 | `{"error": {"code": "not_authenticated", "message": "Sign in before you continue."}}` | `identity.py:843` (unchanged) |
| No session on a protected page | Browser page | 303 | `Location: /auth/signin` | `identity.py:72` and `identity.py:73` (unchanged) |
| Store read failure during recovery | JSON client | 503 | `{"error": {"code": "session_store_unavailable", "message": "The session store is unavailable. Try again later."}}` | New in this feature (D-9) |
| Store read failure during recovery | Browser page | 503 | Plain text body `The session store is unavailable. Try again later.` with no redirect | New in this feature (D-9) |
| Store write failure during environment token sign-in | JSON client | 503 | The same JSON envelope as the row above | New in this feature (FR-010) |
| Store write failure during environment token sign-in | Browser page | 503 | The same plain text body as the row above | New in this feature (FR-010) |
| Sign-out | Any | The route status | The route body. The browser session clears. A failed store delete does not change the body. | `identity.py:800` (behavior changes only inside the store delete, D-10) |

## Rules

- The error code `session_store_unavailable` appears only for a store failure. No other failure uses this code.
- A failed validation during recovery returns the same response as a missing session. The client cannot tell the two cases apart (D-9).
- A store failure never changes the signed cookie (FR-010 and FR-011).
- No response body contains a credential, an encryption key, the owner key, or the browser identifier (FR-014).
- Status 303 keeps the existing sign-in redirect for pages (FR-017).
