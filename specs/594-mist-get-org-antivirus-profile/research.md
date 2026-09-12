# Phase 0 Research: getOrgAntivirusProfile Menu Item

**Branch**: `594-mist-get-org-antivirus-profile` | **Date**: 2026-06-29
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_avprofiles_avprofile_id.md`

This document records the five research decisions required before Phase 1
design work begins. Each decision is final -- no `NEEDS CLARIFICATION`
markers remain.

---

## Research Task 1: SDK Function Signature & Behavior

### Decision

The new menu method calls:

```python
mistapi.api.v1.orgs.avprofiles.getOrgAntivirusProfile(
    mist_session,   # mistapi.APISession built by MistHelper at startup
    org_id,         # UUID string, prompted via safe_input()
    avprofile_id,   # UUID string, prompted via safe_input()
)
```

The call returns a `mistapi.APIResponse` object. The decoded JSON payload is
read from `.data` and is a single JSON object (not a list, not paginated),
conforming to the schema in
`documentation/api/orgs/GET_orgs_org_id_avprofiles_avprofile_id.md` lines
36-127. Response fields and types are:

| Field           | Type                       | Notes                            |
|-----------------|----------------------------|----------------------------------|
| `id`            | string (uuid)              | Natural primary key              |
| `org_id`        | string (uuid)              | Owning org                       |
| `site_id`       | string (uuid) or null      | Optional site scope              |
| `name`          | string                     | Required by the API              |
| `fallback_action` | string enum              | `block`, `log-and-permit`, `permit` |
| `max_filesize` | integer (KB, 20-40000)      | Default 10000                    |
| `mime_whitelist` | array of string (unique)  | May be empty                     |
| `url_whitelist` | array of string (unique)   | May be empty                     |
| `protocols`     | array enum (>=1 item)      | Subset of `ftp,http,imap,pop3,smtp` |
| `created_time`  | number (epoch)             | Read-only                        |
| `modified_time` | number (epoch)             | Read-only                        |

The endpoint is **not paginated** -- there is no `_next` cursor and no
`limit/page` query parameter, so the existing pagination helper is not
invoked.

### Rationale

The enriched documentation file is the canonical contract. The single-object
response is materially simpler than list endpoints; the existing
`DataExporter` already accepts a single dict and emits exactly one row per
backend. Calling the SDK function directly (rather than via raw HTTP) keeps
this menu consistent with all other MistHelper menu items and benefits from
mistapi's retry / 429 handling.

### Alternatives Considered

- **Raw `requests.get()`** -- rejected. The constitution forbids bypassing
  the mistapi SDK, and we would have to re-implement adaptive delay and
  authentication.
- **Calling `listOrgAvprofiles` and filtering client-side** -- rejected. The
  per-id endpoint is cheaper, returns the same shape, and matches the spec
  user story exactly.

---

## Research Task 2: Primary Key Strategy

### Decision

**Type**: `natural_pk`. The Mist API returns a stable UUID in `id` for every
profile, and the schema marks it `readOnly: true`. That UUID is the canonical
identifier for the profile across all Mist surfaces (UI, audit logs, related
endpoints). Use it directly.

```python
"getOrgAntivirusProfile": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["org_id", "site_id", "name"],
}
```

### Rationale

A single-row read with a stable, API-provided UUID is the textbook case for
`natural_pk` per `.github/copilot-instructions.md` Database Strategy section.
Repeated runs `INSERT OR REPLACE` on the same `id`, producing zero
duplicates. `org_id` and `site_id` indexes accelerate cross-table joins with
the upcoming `getOrgIDPProfile` / `getOrgAAMWProfile` per-id reads. `name`
index supports operator search.

### Alternatives Considered

- **`composite_pk` on `(org_id, id)`** -- rejected. The `id` is already
  globally unique across orgs; composite buys nothing and bloats the table
  declaration.
- **`auto_increment_with_unique`** -- rejected. There is no missing key; the
  API gives us a real one.

---

## Research Task 3: Output Filename and SQLite Table

### Decision

- **CSV filename**: `data/org_avprofile.csv`
- **SQLite table**: `org_avprofile`
- **ArangoDB collection**: `org_avprofile` (document collection;
  graph edges to `org` and `site` handled by the existing ArangoDB exporter
  rules)
- **DataExporter call**:
  ```python
  DataExporter.write_with_format_selection(
      data=[flattened_row],
      filename="org_avprofile",
      api_function_name="getOrgAntivirusProfile",
  )
  ```

### Rationale

The singular form (`org_avprofile`, not `org_avprofiles`) signals a per-id
read returning a single record, distinct from the list export which uses the
plural `org_avprofiles`. This naming convention already exists elsewhere in
the codebase (`org_site` vs `org_sites`). Passing `api_function_name`
unlocks the `ENDPOINT_PRIMARY_KEY_STRATEGIES` lookup so the SQLite writer
chooses the correct upsert clause automatically.

### Alternatives Considered

- **`avprofile_<avprofile_id>.csv`** -- rejected. One file per profile id
  spams `data/` and breaks the upsert model.
- **Sharing the `org_avprofiles` table with the list export** -- rejected.
  The list export may project a different column set in the future; keeping
  the per-id detail in its own table preserves schema independence.

---

## Research Task 4: Menu Category Placement and Next Available Menu Number

### Decision

- **Category**: Safe Org Exports (read-only, non-destructive, no pagination
  cost).
- **Cluster**: Security profile reads -- adjacent to existing menu items
  for IDP profiles and AAMW profiles (operations in the 42-50 / config-admin
  block per `.github/copilot-instructions.md`).
- **Proposed menu number**: **96**. This is the highest currently unused
  slot below the resource-intensive block (97-101) and inside the safe
  range. If `/speckit.tasks` finds 96 occupied by another in-flight feature
  branch, the next free integer in the same cluster is selected (likely 97
  if the resource-intensive block has shifted, otherwise the operator
  promotes the next free safe slot).

### Rationale

`.github/copilot-instructions.md` documents the menu range conventions:
1-96 are Safe Org Exports / Interactive Safe; 97-101 and 153 are Resource
Intensive; 154-194 are destructive. A read-only GET against a single AV
profile belongs in the safe block. Placing the new item adjacent to the
sibling security-profile reads keeps related operations together for the
junior NOC operator scanning the menu list.

### Alternatives Considered

- **Appending at 195** -- rejected. The destructive cluster ends at 194 and
  appending past it visually groups a safe read with destructive ops.
- **Inserting at 42-50 (config-admin block)** -- rejected. Inserting in the
  middle would renumber dozens of downstream operations and break operator
  muscle memory.

---

## Research Task 5: Required User Prompts

### Decision

Two prompts, both via `safe_input()`:

1. `org_id` -- prompted with context `"org_antivirus_profile:org_id"`.
   Default value taken from `MIST_DEFAULT_ORG_ID` in `.env` when present so
   the operator can press Enter to accept.
2. `avprofile_id` -- prompted with context
   `"org_antivirus_profile:avprofile_id"`. No `.env` default -- the operator
   must supply the specific profile UUID; if they don't know it, they are
   directed to run the existing `listOrgAvprofiles` menu item first.

Both inputs are validated against the Mist UUID shape
(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`,
case-insensitive) before the SDK call. On validation failure the method logs
a `WARNING` and returns early -- no traceback, no API call burned.

### Rationale

- `org_id` is operator-stable per session, so an `.env` default is
  convenient and matches sibling menu items.
- `avprofile_id` is per-profile and varies every run, so no default is
  appropriate. Pointing the operator to the list-read menu mirrors the
  pattern used by IDP / AAMW per-id reads.
- UUID pre-validation prevents an obviously bad string from triggering a
  400/404 round-trip to Mist Cloud and wasting an API quota slot.

### Alternatives Considered

- **Single combined prompt `"<org_id>:<avprofile_id>"`** -- rejected. Two
  prompts are clearer for the junior NOC operator and easier to validate
  separately.
- **Prompting only for `avprofile_id` and assuming the default org** --
  rejected. The operator may juggle multiple orgs in one session; explicit
  org confirmation is safer.
