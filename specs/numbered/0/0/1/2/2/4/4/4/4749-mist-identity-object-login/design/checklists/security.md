# Security Requirements Quality Checklist: Mist Identity Object Sign-In

## Credential and Secret Handling

- [x] No token value appears in a new log line (FR-010). Task T011 checks each changed line.
- [x] The environment variable names appear by name only. The record holds no variable value.
- [x] The change adds no file that stores a token.

## Token Binding

- [x] A sign-in accepts an identity only when the SDK session holds, as active, a token that the caller supplied (FR-007).
- [x] A missing active token fails closed. Test TG-03 covers the case.
- [x] A rejected supplied token does not read the identity of another active token. Test TG-02 covers the case.

## Failure Behavior

- [x] A 4xx response returns empty privileges (FR-008). Test TG-05 covers the case.
- [x] A 5xx response or a transport fault raises the unavailable error (FR-008). Test TG-06 covers the case.

## Disclosure and Review

- [x] The record names the code path at source level and gives no operating steps.
- [x] The changelog bullet is neutral (decision D-9).
- [x] The review requirement is recorded. Analysis A-12 requires the owner to review the security wording before the record is committed.
