# Phase 0 Research: getOrgSslProxyCert

Source enriched doc:
`documentation/api/orgs/GET_orgs_org_id_ssl_proxy_cert.md`.
Constitution:
`.specify/memory/constitution.md`.

## Research Task 1: SDK function signature & behaviour

**Decision**: Invoke the endpoint via
`mistapi.api.v1.orgs.cert.getOrgSslProxyCert(session, org_id)` where
`session` is the shared `mistapi.APISession` MistHelper already builds from
`.env` credentials, and `org_id` is a validated Mist UUID string. The call
returns a `mistapi.APIResponse` whose `.data` is a single JSON object of the
shape `{"cert": "<PEM-encoded string>"}` (per the 200 example in
`documentation/api/orgs/GET_orgs_org_id_ssl_proxy_cert.md`). No query
parameters, no request body, not paginated. Errors: 400 (bad syntax), 401
(unauthorized), 403 (permission denied), 404 (org or cert missing), 429
(rate limit).

**Rationale**: The enriched endpoint doc names the SDK module
`mistapi.api.v1.orgs.cert.getOrgSslProxyCert`. The spec header names the
module `mistapi.api.v1.orgs.ssl_proxy_cert`; the enriched doc (regenerated
directly from the mistapi package) is authoritative because it reflects the
current 0.59+ module layout where org-level certificate operations
(`getOrgCert`, `getOrgSslProxyCert`) are grouped under a single `cert`
sub-package. Using the authoritative import avoids an `ImportError` at run
time. The single-object response shape means no pagination loop is needed
and no `get_all_pages` helper is invoked.

**Alternatives Considered**:

- *Direct `requests.get` against the raw URL.* Rejected: violates the
  Constitution-level dependency rule that all Mist Cloud calls go through
  the `mistapi` SDK so that auth, retry, and adaptive-delay handling remain
  centralised.
- *Trust the spec's module path (`ssl_proxy_cert`).* Rejected: verified
  incorrect against the enriched doc. Following the spec verbatim would
  ship an import error to production.
- *Add a query for a `raw=true` flag to skip PEM parsing.* Rejected: no
  such parameter exists on this endpoint; the response is a single field
  either present or absent.

## Research Task 2: Primary Key Strategy

**Decision**: Register `getOrgSslProxyCert` in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` with:

```python
'getOrgSslProxyCert': {
    'type': 'natural_pk',
    'primary_key': ['org_id'],
    'indexes': ['org_id'],
}
```

**Rationale**: The endpoint returns at most one certificate per organisation
(there is no per-site or per-device dimension in the path, and there is no
`id` field in the response). The natural business key is therefore the
organisation ID that the caller supplied. `natural_pk` triggers `INSERT OR
REPLACE` upserts so repeated runs cleanly overwrite the previous row
without duplicates -- essential when the certificate is rotated on the
gateway side. No timestamp column is required for correctness; if history
is later needed, it can be added as a separate append-only table without
changing this strategy.

**Alternatives Considered**:

- *`composite_pk` on `['org_id', 'cert_fingerprint']`.* Rejected: would
  require MistHelper to derive a SHA-256 fingerprint locally on every
  fetch, adding complexity for zero user-visible benefit; and it would
  produce an ever-growing table on every rotation (which is history, not
  current state -- out of scope per spec).
- *`auto_increment_with_unique` with unique on `org_id`.* Rejected: the
  synthetic ID adds no value because there is only ever one row per org;
  `natural_pk` is simpler and lets the schema self-document.
- *No primary key (append-only).* Rejected: violates the project's upsert
  contract and would confuse users who expect the row count to match the
  number of orgs queried.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV filename: `data/org_ssl_proxy_cert_<org_id>.csv` (one file per org
  queried, matching the convention used by adjacent org-config exports).
- SQLite table: `org_ssl_proxy_cert` (single shared table across all orgs;
  `org_id` column distinguishes rows).
- ArangoDB document collection: `org_ssl_proxy_cert` with `_key = org_id`.
- Redis cache key: `org_ssl_proxy_cert:<org_id>` with TTL managed by the
  existing polyglot backend.

**Rationale**: The filename pattern `<endpoint_snake_case>_<scope_id>.csv`
matches existing exports such as `org_licenses_summary_<org_id>.csv` and
lets NOC engineers grep the `data/` directory for "ssl_proxy_cert" and
find only rows for this endpoint. A single SQLite table (rather than
per-org) is consistent with existing multi-org backends and enables SQL
queries across orgs (`SELECT org_id, length(cert) FROM
org_ssl_proxy_cert`).

**Alternatives Considered**:

- *`data/<org_id>/ssl_proxy_cert.csv` (per-org subdirectory).* Rejected:
  no other MistHelper export uses per-org subdirectories; introducing one
  here would break the `data/` layout that automated collectors rely on.
- *Write the PEM as a `.pem` file separate from CSV.* Rejected: violates
  the multi-backend contract -- SQLite and ArangoDB users would lose the
  cert body. If a user needs a `.pem` file for OpenSSL, they can extract
  it from CSV with `awk` or from SQLite with `sqlite3 -csv`.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Propose menu **195**. Category: Config/Admin (cluster
42-50, per `.github/copilot-instructions.md`), but numerically appended at
195 (the next integer above the current top operation 194).

**Rationale**: The current top of the menu (verified via
`Select-String -Path MistHelper.py -Pattern '^\s*"\d+":\s*\('`) is 194
(`OrgTicketManager.clone_device_config_to_gateway_template`). All lower
numbers are stable and cross-referenced by README, CHANGELOG, published
runbooks, and the CI test harness's skip list (14, 18, 63-65, 90-100).
Inserting a new operation mid-range at 46 or 47 (nearest to the related
`getOrgSetting` / `getOrgCert` calls) would renumber every subsequent
operation -- a breaking change. Appending at 195 keeps existing numbers
stable and remains outside the destructive range 154-194. If a
concurrent branch has already claimed 195, the next free integer is used.

**Alternatives Considered**:

- *Insert at 46 in the Config/Admin cluster.* Rejected: renumbers all
  subsequent operations, breaks published documentation and the test
  harness.
- *Reuse an existing operation number by extending its behaviour.*
  Rejected: no adjacent operation currently exposes SSL proxy cert data;
  extending an unrelated op would violate single-responsibility.
- *Assign 200+ to leave a numbering gap.* Rejected: introduces
  discontinuity for no benefit; gaps encourage careless re-use.

## Research Task 5: Required user prompts

**Decision**: One prompt only.

1. **`org_id`** -- collected via
   `safe_input("Enter organization UUID [default: MIST_ORG_ID from .env]:
    ", context="org_ssl_proxy_cert:org_id")`. If the user presses Enter
   with no input, fall back to `os.environ.get("MIST_ORG_ID")`. If both
   are empty, log a warning and return without invoking the SDK. The
   supplied value is validated via `ValidationUtils.is_valid_uuid`
   before the API call.

No other prompts. There are no query parameters, no site scope, no
device scope, and no destructive-confirmation gate (read-only GET).

**Rationale**: The endpoint path is `orgs/{org_id}/ssl_proxy_cert`; the
only free variable is `org_id`. Existing MistHelper convention is to
default org-scoped operations to `MIST_ORG_ID` from `.env` so that
automation (SSH-driven runs, CI `--test`, cron jobs) can proceed without
interactive input. `safe_input()` is mandated by the Safety-First
principle for all `input()` calls so EOF in SSH / container sessions
exits cleanly with code 0.

**Alternatives Considered**:

- *Prompt for a confirmation to write the PEM to disk.* Rejected: not a
  destructive operation; the PEM is public-key material and the write
  target is inside `data/` which the user already owns.
- *Prompt for an output format.* Rejected: format is chosen globally by
  `DataExporter.write_with_format_selection` based on env / config; a
  per-menu prompt would violate consistency with the other 194
  operations.
- *Skip the prompt entirely and always use `MIST_ORG_ID`.* Rejected:
  breaks interactive use in multi-org environments where the operator
  needs to switch orgs without editing `.env`.
