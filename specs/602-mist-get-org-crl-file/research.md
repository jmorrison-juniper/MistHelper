# Phase 0 Research: getOrgCrlFile

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_crl.md`

This document captures the design decisions made before code is written. Each
section follows the **Decision / Rationale / Alternatives Considered** format
required by the SpecKit Phase 0 contract.

## Research Task 1: SDK function signature & behavior

### Decision

Invoke the endpoint through the `mistapi` Python SDK module
`mistapi.api.v1.orgs.crl`, calling the bound function `getOrgCrlFile(apisession,
org_id)`. The return value is a `mistapi.APIResponse` whose `.data` attribute
contains the raw response body as documented: a JSON object with a single
base64-encoded `string` payload describing the CRL file. MistHelper will
treat the entire response as one logical artifact (the CRL blob) plus minimal
context fields (org_id, fetched_at, length, sha256).

### Rationale

- The enriched per-endpoint doc
  (`documentation/api/orgs/GET_orgs_org_id_crl.md`) lists the SDK as
  `mistapi.api.v1.orgs.crl.getOrgCrlFile()` directly. The URL path
  (`/orgs/{org_id}/crl`) maps cleanly to the module path
  (`mistapi.api.v1.orgs.crl`), matching the SDK's documented URL-to-module
  convention.
- The 200 OK schema is unusual for Mist: instead of a JSON list of entities,
  the body is a single object whose semantic content is a base64 string. This
  means the response is fundamentally a binary blob (a `.crl` file), not a
  collection of rows.
- The endpoint takes only one parameter (`org_id` path param) and has no
  query parameters, no request body, and no pagination -- matching the
  enriched doc.
- The endpoint is not currently used by MistHelper anywhere in the
  ~28K-line monolith (the doc's `MistHelper Notes` section confirms "Not
  currently used by MistHelper directly").

### Alternatives Considered

1. **Direct `requests.get()` call bypassing the SDK** -- Rejected. The
   constitution and project conventions mandate that all Mist API access flow
   through `mistapi` so that authentication, retry, and adaptive-delay logic
   stay centralized.
2. **Treat the response as opaque JSON and CSV-export the raw base64 string
   verbatim** -- Rejected. Storing a multi-kilobyte base64 string inside a
   CSV cell creates an unusable artifact. Better to decode once and write
   the decoded `.crl` blob to `data/` as a sibling file, with metadata in the
   tabular output.
3. **Skip the file write and store only metadata** -- Rejected. The CRL is
   the entire point of the endpoint; downstream NAC tooling needs the actual
   bytes. Metadata alone would force the user to re-fetch every time.

## Research Task 2: Primary Key Strategy

### Decision

Use a `composite_pk` strategy on `(org_id, fetched_at_utc)`.

```python
'getOrgCrlFile': {
    'type': 'composite_pk',
    'primary_key': ['org_id', 'fetched_at_utc'],
    'indexes': ['sha256'],
    'table': 'org_crl_metadata',
}
```

### Rationale

- The CRL itself has no stable natural ID -- the Mist API returns no UUID,
  no `id`, no `serial`, and no timestamp inside the payload. There is exactly
  one current CRL per org at any moment in time.
- The user value of running this menu item more than once is *snapshot
  history*: knowing when the CRL last rotated. Keying on `(org_id,
  fetched_at_utc)` preserves every poll as a row, with the SHA-256 index
  enabling fast "did the CRL actually change?" queries via
  `SELECT DISTINCT sha256 FROM org_crl_metadata WHERE org_id = ?`.
- Composite PK matches the strategy used by adjacent snapshot-style
  endpoints in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (per the documented hybrid
  PK system in `.github/copilot-instructions.md`).

### Alternatives Considered

1. **`natural_pk` on `org_id` alone** -- Rejected. Would overwrite the
   previous snapshot on every poll, losing the rotation history that makes
   the menu item useful beyond a one-shot fetch.
2. **`auto_increment_with_unique`** -- Rejected. Adds an opaque internal ID
   for no benefit; `(org_id, fetched_at_utc)` is already unique by
   construction (MistHelper generates the UTC timestamp at poll time at
   sub-second resolution), and composite_pk is the convention for snapshot
   data.
3. **Keyed on SHA-256 alone** -- Rejected. Would deduplicate identical CRLs
   across orgs, breaking per-org rotation history. Index on SHA-256 is the
   right answer; PK on SHA-256 is not.

## Research Task 3: Output filename and SQLite table

### Decision

- **Raw CRL blob**: `data/org_<short>_crl_<utcstamp>.crl` where `<short>` is
  the first 8 characters of the org UUID and `<utcstamp>` is
  `YYYYMMDDTHHMMSSZ`. Example:
  `data/org_0a1b2c3d_crl_20260629T225100Z.crl`.
- **Metadata CSV**: `data/org_<short>_crl_metadata.csv` (one row appended per
  poll).
- **SQLite table**: `org_crl_metadata` (single table, composite PK on
  `(org_id, fetched_at_utc)`).
- The metadata row contains: `org_id`, `fetched_at_utc`, `content_encoding`
  (always `"base64"`), `crl_length_bytes` (decoded byte count), `sha256`
  (lowercase hex), and `blob_path` (path to the raw `.crl` file relative to
  `data/`).

### Rationale

- The `<short>` org prefix follows the established MistHelper naming
  convention used by adjacent exporters (e.g.,
  `org_<short>_claim_status_summary.csv` from spec 500).
- The UTC timestamp in the raw-blob filename guarantees no overwrites on
  repeated polls, which preserves rotation history alongside the SQLite
  composite-PK snapshots.
- The metadata CSV pivots one wide row per snapshot, keeping the per-poll
  audit trail human-readable and grep-friendly.
- Writing the decoded `.crl` blob as a sibling file (rather than into
  SQLite as a BLOB column) keeps downstream tooling simple: any NAC
  appliance can consume the file directly with `openssl crl -in
  org_0a1b2c3d_crl_20260629T225100Z.crl -inform DER -text`.

### Alternatives Considered

1. **Single CSV with the base64 string inline** -- Rejected. Embeds a
   multi-kilobyte string inside CSV; breaks Excel and most CLI tools that
   open CSVs.
2. **SQLite BLOB column** -- Rejected. Couples raw bytes to the database
   backend choice; users on the CSV-only backend would have nowhere to put
   the blob. Sidecar file is backend-agnostic.
3. **Filename without timestamp (`org_<short>_crl.crl`)** -- Rejected.
   Overwrites prior snapshots, defeating the rotation-history purpose of
   the composite PK.

## Research Task 4: Menu category placement and next available menu number

### Decision

Propose menu number **96**, placed in the Viewers cluster (92-96) of safe
org-level read-only operations. Final number re-verified at
`/speckit.tasks` time by scanning `MistHelper.py` for the literal menu
registrations; if 96 is already taken by an in-flight 6XX-series spec the
next free integer in the same cluster is used.

### Rationale

- Per `.github/copilot-instructions.md` § Menu System & Operations, the
  range 60-96 is the Interactive Safe / Viewers band. Operation 96 is the
  documented "next available" slot before the resource-intensive cluster at
  97-101.
- The CRL endpoint is read-only, low cost, and surfaces a security artifact
  -- a perfect fit for the Viewers cluster (which already contains adjacent
  certificate / NAC viewers per the documented categorization).
- Placing it in 1-59 (Safe Org Exports) would also work, but those slots are
  earlier and more contested by the 5XX/6XX SpecKit pipeline; 96 is the
  cleaner choice.

### Alternatives Considered

1. **Slot in 1-59 (Safe Org Exports)** -- Rejected. Higher collision risk
   with concurrent specs; the cluster is also organized by data-type
   (Sites, Inventory, Stats) and CRL does not fit any of those subcategories
   cleanly.
2. **Slot in 124-150 (Interactive)** -- Rejected. That cluster is for
   destructive-adjacent diagnostic and management operations; placing a
   pure read in there muddies the safety taxonomy.
3. **Slot in 154-194 (Destructive)** -- Rejected. GET is non-destructive
   by definition; the destructive band is for write/reset/delete operations
   only.

## Research Task 5: Required user prompts (which IDs from the user, which from `.env`)

### Decision

Exactly one user prompt:

- `org_id` (UUID string) -- collected via `safe_input("Org ID (UUID): ",
  context="org_crl_file:org_id", default=os.environ.get("MIST_ORG_ID", ""))`.
  Pressing Enter accepts the `.env` default. Validated client-side with
  `is_valid_uuid()` before the SDK call.

Implicit inputs from `.env` (never prompted, never logged):

- `MIST_HOST` -- API endpoint host name.
- `MIST_API_TOKEN` -- Mist API token for `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for the prompt above.

No additional prompts are required: the endpoint has no query parameters,
no body, and no destructive effect, so there is nothing else to ask. The
prompt count stays at one, well under the Five-Item Rule's 5-block budget
for the method.

### Rationale

- The enriched per-endpoint doc confirms exactly one path parameter
  (`org_id`) and no query parameters, no body.
- Centralizing host and token in `.env` is the constitutional pattern
  (Principle III Safety-First and the global "secrets in `.env` only" rule).
- Honoring `MIST_ORG_ID` as a prompt default matches how every other
  org-level menu item in MistHelper handles the same parameter, giving
  non-interactive runs a clean path via `echo "" | python MistHelper.py
  --menu 96`.

### Alternatives Considered

1. **Prompt for an output directory** -- Rejected. The constitution
   mandates all output under `data/`; making the directory configurable
   per-run breaks that invariant.
2. **Prompt for a download filename** -- Rejected. The deterministic
   filename pattern (`org_<short>_crl_<utcstamp>.crl`) is the audit-trail
   guarantee; letting the user override it defeats the rotation-history
   design.
3. **Prompt for "decode and write blob? y/N"** -- Rejected. Decoding is
   cheap (base64 + SHA-256 on a sub-megabyte payload is sub-second) and
   the user value of the operation *is* the decoded `.crl` file; making
   it opt-in adds friction with no benefit.
