# Retry scope route contract

## Save

`POST /api/org-upgrades/options` retains the response `{"next": "/upgrade/org/confirm"}`.
For a retry with only an access point at B after family filtering, the saved parent names B only.
Its names map and child targets must also name B only.
The operator selection remains A and B.

## Confirmation

`GET /upgrade/org/confirm` shows one site and one device for that saved retry.
Only B has a pre-check row and capture read.
The existing single-site warning text follows the effective count without a template change.

## Submission

`POST /api/org-upgrades` still requires the signed session, enabled writes, correct nonce, and exact `CONFIRM`.
The pre-check reader, existing-lock checks, and lock acquisition use B only.
The lock record retains its token and operation identity.
Existing claims, audit calls, durable transitions, and replay safeguards remain in place.

## Preservation

Plain saves and complete retries keep two sites when both have a target.
Removing or reordering a planned site prevents an exact-context match.
The contract tests reject any external socket connection.
