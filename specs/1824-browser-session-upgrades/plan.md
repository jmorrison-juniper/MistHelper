# Implementation Plan: Browser Token and Safe Device Selection

## Summary

The portal will accept a browser-provided Mist token only when no environment
token existed when the portal started. It will build an in-memory Mist session,
read a safe token name through `GetSelf`, and use that session for every
operator request. The portal will preserve complete captures while it filters
upgrade targets by selected device types. It will calculate safe targets by
compatible model and mark only known different running versions.

## Project Structure

```text
src/upgrade_portal/
├── app/
│   ├── config.py
│   ├── routes/auth.py
│   ├── routes/upgrade.py
│   └── assets/templates/
│       ├── auth/signin.html
│       └── upgrade/options.html
├── runtime/identity.py
└── upgrade/options.py
tests/
├── unit/upgrade_portal/
│   ├── test_auth.py
│   ├── test_identity.py
│   └── test_upgrade_options.py
└── contract/upgrade_portal/
    ├── test_auth.py
    ├── test_no_credential_leak.py
    └── test_upgrade_options.py
documentation/upgrade_capture_portal.md
```

**Structure Decision**: Extend the existing authentication, identity, options,
and route seams. Do not create a second credential store or a second target
calculation path.

## Constitution Check

| Principle | Assessment | Plan response |
| --- | --- | --- |
| Five-Item Rule | PASS | Extract small helpers where a route gains a new decision. |
| Class-Based Architecture | PASS | Keep state in the existing settings, session, and selection classes. |
| Safety-First | PASS | Validate all browser input and do not call an upgrade start path. |
| Full Deployment Pipeline | PASS | Run focused checks, push, wait for checks, update the image, restart, and verify. |
| Observability and Logging | PASS | Log safe identity names or digests only. Never log a token or a session object. |
| Inline Comments | PASS | Add required same-line comments to generated Python changes. |
| Action Logging | PASS | Put safe before-and-after logs around new Mist calls and state changes. |

The plan adds behavior across existing modules. It does not add a new service,
store, or unbounded hierarchy.

## Phase 0: Research

See [research.md](research.md). The existing `SessionRegistry` can hold a Mist
session object without serializing it. The existing options layer already
obtains model versions and validates target availability. The new selection
must become a server-side rule before target records are stored.

## Phase 1: Design

See [data-model.md](data-model.md) and
[browser-token-and-options.md](contracts/browser-token-and-options.md).

The design adds a startup availability fact, a safe token-derived identity,
selected type state, and a calculated mismatch flag. It uses the existing
server-side session registry and existing typed confirmation boundary.

## Test and Deployment Plan

Add unit tests for startup gating, safe identity derivation, session use,
selected-type validation, compatible targets, and unknown running versions.
Add contract tests for page controls and safe response data. Run focused unit,
contract, syntax, and browser checks without sending an upgrade request.

Create a pull request that closes #2133, #2134, and #2135. Add feature,
web-portal, upgrade-portal, firmware, testing, and in-progress labels. Wait
for CI and CodeQL. Squash merge only after checks pass. Pull the updated
container image, restart the container, and verify its health and the local
capture portal.
