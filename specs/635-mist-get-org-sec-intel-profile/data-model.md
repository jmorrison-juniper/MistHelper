# Phase 1 Data Model: getOrgSecIntelProfile

Derived from the 200 response schema in
`documentation/api/orgs/GET_orgs_org_id_secintelprofiles_secintelprofile_id.md`.

## Entities

### Entity 1: `SecIntelProfile` (summary / header row)

Represents one Security Intelligence profile owned by an org. Configures
threat-intelligence feeds consumed by SRX gateways.

| Field                | Type    | Source                | Notes                                                          |
|----------------------|---------|-----------------------|----------------------------------------------------------------|
| `secintelprofile_id` | TEXT    | Path parameter        | Natural PK. Mist UUID passed in the URL.                       |
| `org_id`             | TEXT    | Path parameter        | Foreign key to `orgs.id`. Denormalized onto every row.         |
| `name`               | TEXT    | Response `name`       | Human-readable profile name, e.g. `secintel-custom`.           |
| `rule_count`         | INTEGER | Derived (len profiles) | Convenience column for quick counts without joining details.  |
| `retrieved_at`       | TEXT    | MistHelper (ISO-8601)  | Timestamp of the export run. Not a PK component.              |

- **Primary Key**: `secintelprofile_id`
- **Foreign Keys**: `org_id` -> `orgs.id` (conceptual; enforced at
  application level, not by SQLite `FOREIGN KEY` constraint per project
  convention).
- **Indexes**: `org_id`, `name` (for quick lookups by human-readable name).

### Entity 2: `SecIntelProfileRule` (detail row -- one per element of the
nested `profiles` array)

Represents a single per-category rule inside the profile, e.g. "action =
strict for category CC".

| Field                | Type    | Source                            | Notes                                                          |
|----------------------|---------|-----------------------------------|----------------------------------------------------------------|
| `secintelprofile_id` | TEXT    | Path parameter                    | Composite PK part 1. FK to `org_secintel_profile_summary`.     |
| `org_id`             | TEXT    | Path parameter                    | Denormalized for filtering by org.                             |
| `category`           | TEXT    | Response `profiles[].category`    | Composite PK part 2. Enum: `CC`, `IH`, `DNS`.                  |
| `action`             | TEXT    | Response `profiles[].action`      | Enum: `default`, `standard`, `strict`.                         |
| `retrieved_at`       | TEXT    | MistHelper (ISO-8601)              | Timestamp of the export run. Not a PK component.              |

- **Primary Key**: `(secintelprofile_id, category)`
- **Foreign Keys**: `secintelprofile_id` -> `org_secintel_profile_summary.
  secintelprofile_id`; `org_id` -> `orgs.id`.
- **Indexes**: `org_id`, `category`.

## State Transitions

N/A -- read-only endpoint. The retrieved rows reflect the current
configuration state at the moment the API responds; MistHelper does not
model transitions. Any subsequent re-run overwrites (via `INSERT OR REPLACE`)
the existing row keyed by the natural / composite PK, which is the desired
upsert semantic.

## SQLite DDL

```sql
-- Header / summary table (one row per SecIntel profile per org)
CREATE TABLE IF NOT EXISTS org_secintel_profile_summary (
    secintelprofile_id TEXT PRIMARY KEY,   -- Natural PK from the API path parameter
    org_id             TEXT NOT NULL,      -- Owning org UUID (denormalized)
    name               TEXT,               -- Human-readable name (nullable per schema)
    rule_count         INTEGER NOT NULL DEFAULT 0,  -- len(response.profiles)
    retrieved_at       TEXT NOT NULL       -- ISO-8601 timestamp of this export
);

CREATE INDEX IF NOT EXISTS idx_org_secintel_profile_summary_org_id
    ON org_secintel_profile_summary (org_id);
CREATE INDEX IF NOT EXISTS idx_org_secintel_profile_summary_name
    ON org_secintel_profile_summary (name);

-- Detail table (one row per rule inside the profile.profiles[] array)
CREATE TABLE IF NOT EXISTS org_secintel_profile_rules (
    secintelprofile_id TEXT NOT NULL,      -- FK -> org_secintel_profile_summary.secintelprofile_id
    org_id             TEXT NOT NULL,      -- Denormalized owning org UUID
    category           TEXT NOT NULL,      -- Enum: CC, IH, DNS
    action             TEXT,               -- Enum: default, standard, strict
    retrieved_at       TEXT NOT NULL,      -- ISO-8601 timestamp of this export
    PRIMARY KEY (secintelprofile_id, category)
);

CREATE INDEX IF NOT EXISTS idx_org_secintel_profile_rules_org_id
    ON org_secintel_profile_rules (org_id);
CREATE INDEX IF NOT EXISTS idx_org_secintel_profile_rules_category
    ON org_secintel_profile_rules (category);
```

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Entry

Add the following two entries to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict
in `MistHelper.py` (around line ~1672 per `.github/copilot-instructions.md`).
Both entries share the same operationId as the outer key because
`DataExporter` dispatches on `api_function_name`; the second entry uses a
suffixed variant that the new method passes explicitly for the detail
sub-table.

```python
# Header / summary row for one SecIntel profile
'getOrgSecIntelProfile': {                                # Mist operationId as dict key
    'type': 'natural_pk',                                 # Stable UUID from path param
    'primary_key': ['secintelprofile_id'],                # Single-column natural PK
    'indexes': ['org_id', 'name'],                        # Common lookup axes
    'table': 'org_secintel_profile_summary',              # Target SQLite table
},

# Per-category rule rows inside the profile.profiles[] array
'getOrgSecIntelProfile__rules': {                         # Suffix disambiguates the detail export
    'type': 'composite_pk',                               # PK spans multiple columns
    'primary_key': ['secintelprofile_id', 'category'],    # Composite prevents duplicate rules
    'indexes': ['org_id', 'category'],                    # Common filter axes
    'table': 'org_secintel_profile_rules',                # Target SQLite table
},
```

The menu method calls `DataExporter.write_with_format_selection()` twice --
once with `api_function_name='getOrgSecIntelProfile'` for the summary row
and once with `api_function_name='getOrgSecIntelProfile__rules'` for the
flattened rule rows. This mirrors the two-table pattern established by spec
500 (async claim status).
