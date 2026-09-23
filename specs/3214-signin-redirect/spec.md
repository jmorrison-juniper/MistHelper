# Feature Specification: Send a browser page with no session to the sign-in form

**Issue**: #3214
**Feature Branch**: `fix/3214-signin-redirect`
**Status**: Implemented
**Found by**: the live read-only journey of #3200

## Problem

After sign-out, or after a session expires, a browser visit to a portal page
showed `{"error":{"code":"not_authenticated","message":"Sign in before you
continue."}}` as the whole page. The operator got no link to the sign-in form.
The live access log holds 21 answers of 401.

## User Story (P2): An operator with no session gets back to the sign-in form

**Acceptance scenarios**:

1. **Given** a browser with no session, **When** the operator opens a portal
   page, **Then** the portal answers 303 and the browser opens `/auth/signin`.
2. **Given** a script request with no session (`fetch`, a JSON client, or no
   Accept header), **When** it reaches a guarded route, **Then** the portal
   keeps the 401 `not_authenticated` envelope.

## Requirements

- **FR-001**: A GET request that prefers `text/html` over `application/json`
  MUST get a 303 redirect to `/auth/signin`.
- **FR-002**: Every other request MUST keep the envelope of
  `contracts/README.md:31-39`.
- **FR-003**: The rule MUST live in `identity._refusal_for_request`, so every
  guarded route follows it.

## Non-goals

- The form does not yet return the operator to the page that they opened. A
  return path needs an open-redirect check and a separate issue.
