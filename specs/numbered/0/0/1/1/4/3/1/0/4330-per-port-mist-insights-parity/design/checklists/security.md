# Security Checklist: Per-port Mist Insights parity in the WAN dashboard

**Purpose**: Check the secret handling, the admission path, and the request budget before implementation.
**Created**: 2026-11-26
**Feature**: `spec.md`

## Secrets

- [x] CHK001 No token, cookie, or credential value appears in the spec, plan, tasks, or design files. Explained by the record review. The record names secrets only by name.
- [x] CHK002 Logs carry no token, cookie, credential-bearing URL, or response body. Explained in FR-017, design/contracts/port-series-request.md, Logging, and TC-22.
- [x] CHK003 Errors carry the status code or the error class name only. Explained in design/contracts/port-series-response.md, Outcome States.
- [x] CHK004 Tests use no production credential. Explained in D-13 and quickstart Preconditions.

## Admission and Tenant Scope

- [x] CHK005 Each site-scoped read carries a tenant context before transport. Explained in D-7, FR-006, and TC-13.
- [x] CHK006 A site-scoped read without tenant context fails closed. Explained in R-22 and TC-14.
- [x] CHK007 Each logical read makes one SDK attempt for each token. Explained in D-7, FR-007, R-11, and R-49.
- [x] CHK008 No direct HTTP call is added. Explained in FR-006 and R-69.

## Request Budget

- [x] CHK009 The request cap is unset by default, which disables the phase. Explained in D-8 and T007.
- [x] CHK010 The planned calls stay at or below 2,500 for each token for each hour. Explained in D-8 and TC-24.
- [x] CHK011 The worker stops before the first port call when the headroom check fails. Explained in User Story 2 and TC-24.
- [x] CHK012 The worker stops before the next request when the lease is lost. Explained in the Edge Cases and TC-17.

## Data Integrity

- [x] CHK013 A malformed response never replaces a complete prior value. Explained in design/contracts/port-series-response.md, Outcome States.
- [x] CHK014 A stale value never carries the live label. Explained in FR-010 and design/data-model.md, State Transitions.
- [x] CHK015 A missing sample never becomes zero. Explained in FR-011 and TC-08.

## Provenance and License

- [x] CHK016 No source code, tests, fixtures, screenshots, or assets enter the product. Explained in FR-016 and D-11.
- [x] CHK017 The attribution text needs human approval. Explained in D-11 and the human decision list.
- [x] CHK018 The source commit and the license blob are recorded. Explained in research.md, rows R-58 and R-59.
