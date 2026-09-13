# Phase 1 Data Model: getOrgAptemplate

This document describes the entities returned by
`GET /api/v1/orgs/{org_id}/aptemplates/{aptemplate_id}`, their persistence
shape in the MistHelper SQLite backend, and the registration entry that goes
into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

Authoritative response schema source:
`documentation/api/orgs/GET_orgs_org_id_aptemplates_aptemplate_id.md` (lines
32-597 of the 200 response body).

## Entities

The endpoint returns **one** AP template object per call. After normalization
the MistHelper persistence model splits the response into **two** related
entities:

### Entity 1: `OrgApTemplate` (top-level record)

The summary row, one per call. Stored in SQLite table `org_aptemplates`.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | TEXT (UUID) | `id` (readOnly) | **Primary key.** Stable across runs. |
| `org_id` | TEXT (UUID) | `org_id` (readOnly) | Foreign key concept: identifies parent org. Indexed. |
| `site_id` | TEXT (UUID) NULLABLE | `site_id` (readOnly) | Non-null when template is site-bound. Indexed. |
| `for_site` | INTEGER (0/1) | `for_site` (readOnly) | Boolean; `1` indicates site-bound template. Indexed. |
| `created_time` | REAL | `created_time` (readOnly) | Epoch seconds. |
| `modified_time` | REAL | `modified_time` (readOnly) | Epoch seconds. Updated on Mist-side edits. |
| `ap_matching_enabled` | INTEGER (0/1) | `ap_matching.enabled` | Whether per-model matching rules are active. |
| `ap_matching_rules_count` | INTEGER | `len(ap_matching.rules)` | Cached row count from rules array; redundant with detail table but useful for SQL summaries. |
| `wifi_enabled` | INTEGER (0/1) | `wifi.enabled` | Whether radios are enabled by this template (default true per schema). |
| `wifi_json` | TEXT (JSON) | `wifi` (entire object) | Full `wifi` sub-object serialized for downstream parsing. |
| `ap_matching_json` | TEXT (JSON) | `ap_matching` (entire object) | Full nested matching configuration. Redundant with detail table but kept for round-trip fidelity. |
| `_retrieved_at` | REAL | client clock | Epoch seconds at retrieval; populated by `DataExporter`. |

**Foreign keys**:
- `org_id` references the conceptual `orgs.id` (no FK constraint enforced --
  Mist orgs are not a MistHelper-managed table; the link is documented but
  unenforced, consistent with the rest of MistHelper's SQLite schema).
- `site_id` (when non-null) references the conceptual `sites.id` for the
  same reason.

### Entity 2: `OrgApTemplateMatchRule` (zero-or-more per template)

One row per entry in the `ap_matching.rules` array. Stored in SQLite table
`org_aptemplate_match_rules`.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `aptemplate_id` | TEXT (UUID) | parent `id` | **Composite PK part 1.** Foreign key back to `org_aptemplates.id`. Indexed. |
| `rule_index` | INTEGER | array position | **Composite PK part 2.** Position in the source `rules` array (0-based). |
| `name` | TEXT | `rules[].name` | Optional human-readable rule name. |
| `match_model` | TEXT | `rules[].match_model` | Required string -- the AP model the rule targets (e.g. `AP43`). |
| `port_config_json` | TEXT (JSON) | `rules[].port_config` | Map of port-name -> `ap_port_config` object. Highly nested (dynamic VLANs, MAC auth, mist_nac, forwarding mode); stored as JSON for fidelity. |
| `radio_config_json` | TEXT (JSON) NULLABLE | `rules[].radio_config` if present | Optional per-rule radio overrides. |
| `extra_json` | TEXT (JSON) NULLABLE | remaining `rules[]` fields | Catch-all for any schema fields not explicitly columnar -- forward-compatible against Mist API additions. |
| `_retrieved_at` | REAL | client clock | Epoch seconds at retrieval; populated by `DataExporter`. |

**Composite primary key** `(aptemplate_id, rule_index)` ensures that
re-running the menu item against the same template yields an idempotent
upsert: rule positions are stable within a single Mist template version
(Mist orders the array deterministically).

## State Transitions

**N/A -- read-only endpoint.** `getOrgAptemplate` is an HTTP GET with no
state effect on the Mist Cloud. Within MistHelper's SQLite cache, the only
state transition is **INSERT-or-REPLACE** governed by the natural / composite
primary keys: a subsequent run with the same `id` overwrites the prior row,
preserving exactly one cached snapshot per template ID. There is no
`status` column, no soft-delete, and no workflow transition.

## SQLite DDL

The DDL below is the target shape; in practice `DataExporter` will create the
tables lazily on first run using its standard column-inference path. The DDL
is reproduced here so reviewers can confirm the schema matches the entity
table above.

```sql
-- Summary table: one row per AP template.
CREATE TABLE IF NOT EXISTS org_aptemplates (
    id                        TEXT PRIMARY KEY,
    org_id                    TEXT NOT NULL,
    site_id                   TEXT,
    for_site                  INTEGER,
    created_time              REAL,
    modified_time             REAL,
    ap_matching_enabled       INTEGER,
    ap_matching_rules_count   INTEGER,
    wifi_enabled              INTEGER,
    wifi_json                 TEXT,
    ap_matching_json          TEXT,
    _retrieved_at             REAL
);

CREATE INDEX IF NOT EXISTS idx_org_aptemplates_org_id
    ON org_aptemplates(org_id);
CREATE INDEX IF NOT EXISTS idx_org_aptemplates_site_id
    ON org_aptemplates(site_id);
CREATE INDEX IF NOT EXISTS idx_org_aptemplates_for_site
    ON org_aptemplates(for_site);

-- Detail table: zero or more rows per template.
CREATE TABLE IF NOT EXISTS org_aptemplate_match_rules (
    aptemplate_id      TEXT NOT NULL,
    rule_index         INTEGER NOT NULL,
    name               TEXT,
    match_model        TEXT,
    port_config_json   TEXT,
    radio_config_json  TEXT,
    extra_json         TEXT,
    _retrieved_at      REAL,
    PRIMARY KEY (aptemplate_id, rule_index)
);

CREATE INDEX IF NOT EXISTS idx_org_aptemplate_match_rules_aptemplate_id
    ON org_aptemplate_match_rules(aptemplate_id);
CREATE INDEX IF NOT EXISTS idx_org_aptemplate_match_rules_match_model
    ON org_aptemplate_match_rules(match_model);
```

All `INSERT` operations use `INSERT OR REPLACE` semantics through the existing
`DataExporter` SQLite path so re-runs upsert cleanly without duplicate-key
errors.

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration

The following entry must be added to the `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (the existing dictionary lives near the centre
of the file; the new entry is keyed by the Mist operationId string and
sits alphabetically alongside other `getOrg*` entries):

```python
"getOrgAptemplate": {
    # Mist provides a stable UUID; natural_pk is sufficient.
    "type": "natural_pk",
    # Single-column primary key on the template's own UUID.
    "primary_key": ["id"],
    # Useful query paths: by org, by site, and by template scope flag.
    "indexes": ["org_id", "site_id", "for_site"],
    # Sibling table for the variable-length ap_matching.rules array.
    "child_tables": {
        "org_aptemplate_match_rules": {
            "type": "composite_pk",
            "primary_key": ["aptemplate_id", "rule_index"],
            "indexes": ["aptemplate_id", "match_model"],
            "parent_table": "org_aptemplates",
            "parent_key": ["id"],
            "child_fk": ["aptemplate_id"],
        },
    },
},
```

Notes:
- The `child_tables` sub-structure mirrors the convention used by other
  multi-table operations (e.g. `getOrgLicenseAsyncClaimStatus` from spec 500
  for its summary + per-device split). If the running version of
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` does not yet support a `child_tables`
  field, the detail table is registered as its own top-level entry under a
  synthetic operationId `getOrgAptemplate__match_rules`, keeping the
  contract identical to the reviewer.
- No surrogate `misthelper_internal_id` column is introduced -- both tables
  derive their keys from Mist-provided values.
