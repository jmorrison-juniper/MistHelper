# Contract: Session terminal routes

**Scope**: The terminal read route, the resize route, and the client rule for batch parents. This contract restates existing server behavior. This record changes no server behavior.

## Routes

| Route | Method | Purpose | Source |
| - | - | - | - |
| `/api/websockets/sessions/<session_id>/terminal` | Not named in the registration line | Read terminal output after a position | `registry.py` line 83 (R-30) |
| `/api/websockets/sessions/<session_id>/resize` | POST | Send the terminal size | `registry.py` line 86 (R-31) |

## Request and response

### Resize request

- Body: a JSON object with `cols` and `rows`. The page sends `{ cols: cols, rows: rows }` (`transport.js` line 20, R-26).
- Server parsing of the body: Unverified (U-5).

### Resize success response

- Body: `{"cols": <int>, "rows": <int>}`. `TerminalGateway.resize` returns this object (`gateway.py` line 176, R-36).

### Terminal read success response

- Keys of the body: Unverified (U-4).
- The page reads the route at `reader.js` line 88 (R-25).

### Refusal for a non-terminal session

- The terminal lookup raises code `not_terminal` for a session with no terminal state (`gateway.py` line 68, R-34).
- The resize path reaches the terminal lookup through `input_context` (`gateway.py` line 73, R-35).
- Code `not_terminal` maps to HTTP status 409 (`error.py` line 22, R-37).
- The error body shape is not restated in this contract.

## Client rule

- The page MUST NOT call the terminal read route or the resize route for a session whose `mode` is `multi_site` (FR-001, FR-002).
- The guard that enforces the rule is `isTerminalSession` (`websockets.js` line 1894, R-17).
- The server sets `mode` to `multi_site` on the batch session payload (`session.py` line 106, R-38).

## Compatibility

- No change to the route paths, the registered methods, the request body, the success body, or the 409 response.

## Test evidence

- The batch parent test (R-48, R-49) checks the client rule for the hardware batch parent.
- The reload test (`spec.md`, User Story 2) checks the same rule after a restore.
- The terminal journeys (R-50, R-51) check the terminal behavior and the `not_terminal` case.
