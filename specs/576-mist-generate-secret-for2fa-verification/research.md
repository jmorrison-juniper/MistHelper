# Phase 0 Research: generateSecretFor2faVerification

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This document records the discovery work performed before Phase 1 design. Each task
follows the Decision / Rationale / Alternatives Considered format from the SpecKit
template.

## Research Task 1: SDK Function Signature and Behavior

**Source**: `documentation/api/self/GET_self_two_factor_token.md`
(enriched per-endpoint doc generated from the Mist OpenAPI 3 spec).

**Decision**: Invoke the mistapi SDK exactly as documented:

```python
import mistapi
from mistapi.api.v1.self.mfa import generateSecretFor2faVerification

response = generateSecretFor2faVerification(
    mist_session=apisession,    # mistapi.APISession built from .env (MIST_HOST, MIST_API_TOKEN)
    by=output_mode,             # optional string; "qrcode" -> PNG bytes, omitted -> JSON
)
```

- HTTP shape: `GET /api/v1/self/two_factor/token`.
- Path parameters: none. The endpoint is account-scoped via the authenticated token.
- Query parameters: `by` (optional, string). Per the doc: when `by == "qrcode"` the
  response body is a PNG image instead of JSON. When omitted, the body is the JSON
  object `{"two_factor_secret": "<base32-encoded TOTP seed>"}`.
- Headers: standard mistapi `Authorization: Token <api_token>` injected by
  `mistapi.APISession`. No additional headers required.
- Response: HTTP 200 with `Content-Type: application/json` (or `image/png` when `by ==
  "qrcode"`). Errors: 400, 401, 403, 404, 429 -- handled below.

**Rationale**: The enriched doc is the authoritative source generated from the OpenAPI
spec and explicitly lists the SDK symbol path
(`mistapi.api.v1.self.mfa.generateSecretFor2faVerification`), the single optional query
parameter, the 200 schema, and every error status code. No reverse-engineering of the
SDK source is needed.

**Alternatives Considered**:
- Calling `requests.get(...)` directly against the URL: rejected. Constitution
  Technology & Compatibility Constraints designates `mistapi` 0.59+ as the sole permitted
  interface to Mist Cloud; bypassing the SDK loses adaptive rate limiting and
  authentication handling.
- Forking the SDK to add a typed return: rejected as out of scope and unnecessary;
  the single-field response is trivially flattened.

## Research Task 2: Primary Key Strategy

**Decision**: Use `auto_increment_with_unique` with a synthetic `captured_at` UTC
timestamp as the unique key. Concretely:

```python
'generateSecretFor2faVerification': {
    'type': 'auto_increment_with_unique',
    'primary_key': ['misthelper_internal_id'],
    'unique_keys': ['captured_at'],
    'indexes': ['captured_at'],
}
```

**Rationale**: The endpoint returns a single object with exactly one business field
(`two_factor_secret`). There is no stable UUID supplied by Mist, no time-series
identifier, and the secret value itself is not a safe primary key (it rotates each time
the endpoint is called -- the very point of the endpoint is to mint a fresh TOTP seed
when an authenticator app is being re-enrolled). Using `auto_increment_with_unique` with
a `captured_at` ISO 8601 UTC timestamp gives each invocation its own row, supports
auditing of when secrets were generated, and prevents accidental upsert collisions while
still enabling idempotent re-runs within the same second (the unique constraint will
deduplicate).

**Alternatives Considered**:
- `natural_pk` on `two_factor_secret`: rejected. The secret is the very value being
  generated; using it as a PK would make audit history impossible and would leak the
  secret into SQLite index pages unnecessarily.
- `composite_pk` on `(account_id, captured_at)`: rejected. The endpoint does not return
  an account identifier in its 200 payload, and adding one would require a second API
  call (`GET /api/v1/self`) on every invocation.
- Pure `auto_increment`: rejected. Without a unique key the design loses idempotency on
  fast re-runs and violates the upsert contract documented in
  `.github/copilot-instructions.md` Database Strategy.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV filename: `data/self_two_factor_token.csv`
- SQLite table name: `self_two_factor_token`
- ArangoDB collection name: `self_two_factor_token` (vertex collection, no edges)
- Redis cache key prefix: `mist:self_two_factor_token:<captured_at>`

**Rationale**: The naming follows the established MistHelper convention -- snake_case
mirror of the OpenAPI path with `/api/v1/` stripped. This keeps the filename
self-describing for the junior NOC engineer reading `data/` listings and matches sibling
exports (e.g. `org_claim_status_summary` from spec 500). The CSV / SQLite / ArangoDB
names are kept identical so the cross-backend mental model stays simple.

**Alternatives Considered**:
- `self_mfa_token.csv` (matching the SDK module shortname `mfa`): rejected. The
  OpenAPI path uses `two_factor`; consistency with the path makes the file easier to
  trace back to the upstream contract.
- Adding the operationId as a suffix (`self_two_factor_token_generateSecret.csv`):
  rejected as redundant -- the operationId is recorded in the SQLite `_meta_endpoints`
  audit table that DataExporter already maintains.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place the new menu item at **operation number 96** in the Interactive Safe
Viewers cluster (operations 92-96). Label: `Self - Generate 2FA Setup Secret (TOTP)`.

**Rationale**: The menu category table in `.github/copilot-instructions.md` Menu System
& Operations divides the menu into clusters. The `/self/` endpoint is account-scoped and
not tied to an org or site, so it does not fit the Safe Org Exports (1-59) or the
Interactive Safe site-scoped block (60-91). The Interactive Safe Viewers cluster (92-96)
is the closest semantic match: it already holds non-destructive account-and-utility
viewers. Slot 96 is the last open position before the Resource Intensive block (97-101,
plus 153). If 96 is consumed by an in-flight feature branch at task-generation time, the
next free integer in the same cluster (or the misc 56-59 range as a fallback) is used.

**Alternatives Considered**:
- Slot inside Safe Org Exports (1-59): rejected. The endpoint has no `org_id`
  parameter; placing it next to org exports would mislead the NOC engineer about its
  scope.
- Slot inside Destructive 154-194: rejected. The endpoint is read-only; placing it in
  the destructive block would trigger unnecessary `UPGRADE`-style confirmation gates.
- Defer placement to `/speckit.tasks`: rejected. The constitution requires explicit
  menu number proposal in the plan; leaving it open creates a NEEDS CLARIFICATION
  marker that the constitution forbids.

## Research Task 5: Required User Prompts

**Decision**: Prompt the user for exactly one value -- the output mode (`json` or
`qrcode`) -- via `safe_input()`. Default to `json` on empty input. Do not prompt for
`org_id`, `site_id`, or `account_id` because the endpoint is scoped by the API token
loaded from `.env`. Do not prompt for the API token itself (loaded by `mistapi.APISession`
from `MIST_HOST` and `MIST_API_TOKEN` in `.env`).

Concrete prompt sequence:

1. `safe_input("Output mode [json|qrcode] (default: json): ", context="self_two_factor_token:output_mode")`
   - Empty / `json` -> SDK call without `by` parameter -> JSON response flattened to one row.
   - `qrcode` -> SDK call with `by="qrcode"` -> PNG bytes written to
     `data/self_two_factor_qrcode_<captured_at>.png`; the CSV / SQLite row records the
     filename in a `qrcode_path` column and leaves `two_factor_secret` NULL.

**Rationale**: The OpenAPI spec lists exactly one optional query parameter (`by`), and
the authenticated account context comes from the API token. Prompting for anything else
would create a false impression that the endpoint takes additional scope identifiers and
would violate the spec's "minimum necessary prompts" guidance. `safe_input()` is required
by Principle III for every prompt.

**Alternatives Considered**:
- No prompt at all -- always JSON: rejected. The `by=qrcode` variant is a legitimate
  user workflow (enrolling an authenticator app by scanning the QR with a phone), and a
  silent default removes it from the NOC engineer's reach.
- Hard-coded `qrcode`: rejected. The JSON variant is the more common automation case
  (export the seed to a password manager) and should remain the default.
- Reading the mode from a CLI flag (e.g. `--mode qrcode`): rejected for the initial
  implementation; the menu-driven UX is the established MistHelper pattern. A CLI flag
  can be added later without breaking the prompt.

## Resolved Unknowns Summary

| Question                                  | Answer                                                                 |
|-------------------------------------------|------------------------------------------------------------------------|
| SDK symbol path                           | `mistapi.api.v1.self.mfa.generateSecretFor2faVerification`             |
| Path parameters                           | None                                                                   |
| Query parameters                          | `by` (optional, `qrcode` or omitted)                                   |
| Primary key strategy                      | `auto_increment_with_unique` on `captured_at`                          |
| Output filename                           | `data/self_two_factor_token.csv`                                       |
| SQLite table                              | `self_two_factor_token`                                                |
| Menu number                               | 96 (Interactive Safe Viewers cluster, 92-96)                           |
| Required user prompts                     | One: output mode (json / qrcode), default json                         |
| `.env` requirements                       | `MIST_HOST`, `MIST_API_TOKEN` (already required by MistHelper)         |
| Sensitive data handling                   | Secret value written ONLY to data backend, never to logs               |

All Phase 0 unknowns are resolved. No NEEDS CLARIFICATION markers remain. Ready for
Phase 1 design.
