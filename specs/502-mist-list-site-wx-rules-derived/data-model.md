# Phase 1 Data Model: ListSiteWxRulesDerived

## Entities Returned by the Endpoint

The endpoint returns a JSON array. Each element is a `wxlan_rule` object (the schema
title from the OpenAPI document). There is exactly one entity type.

### Entity: `wxlan_rule`

Represents a single derived (effective) WxLAN access-control rule as enforced at the
target site. Derived rules combine the site''s own WxLAN rules with rules inherited
from any org-level WxLAN template attached to the site.

#### Fields

| Field | Type | Required | Read-Only | Description |
|-------|------|----------|-----------|-------------|
| `id` | string (UUID) | yes (server) | yes | Unique ID of the rule instance in the Mist Organization. Natural business key. |
| `site_id` | string (UUID) | yes (server) | yes | Site this derived rule applies to. Echoed by the API; also back-filled from the path parameter. |
| `org_id` | string (UUID) | yes (server) | yes | Parent organization UUID. |
| `template_id` | string (UUID) | no | no | Set only when the rule is inherited from an org-level WxLAN template. NULL for rules defined directly at the site. |
| `order` | integer | yes | no | Lookup priority. Higher value matched first; `-1` means LAST. Not required to be unique. |
| `action` | string (enum) | no | no | `allow` or `block`. The matching policy for this rule. |
| `enabled` | boolean | no | no | Defaults to `true`. Disabled rules are present in the catalog but not enforced. |
| `for_site` | boolean | no | yes | `true` if the rule applies at the site level (vs purely org-level). Server-computed. |
| `apply_tags` | array of string (UUID) | no | no | WxTag UUIDs whose policy attributes are applied when this rule matches. |
| `blocked_apps` | array of string | no | no | Application keys (e.g. `"mist"`, `"all-videos"`) that are always blocked, ignoring `action`. |
| `src_wxtags` | array of string (UUID) | yes | no | WxTag UUIDs that determine whether this rule matches. |
| `dst_wxtags` | array of string (UUID) | no | no | WxTag UUIDs identifying destinations. |
| `dst_allow_wxtags` | array of string (UUID) | no | no | WxTag UUIDs identifying destinations explicitly allowed by this rule. |
| `dst_deny_wxtags` | array of string (UUID) | no | no | WxTag UUIDs identifying destinations explicitly blocked by this rule. |
| `created_time` | number (epoch seconds) | no | yes | Creation timestamp. |
| `modified_time` | number (epoch seconds) | no | yes | Last-modified timestamp. |

#### Primary Key

Composite: `(id, site_id)`. See Research Task 2 for rationale -- a single rule instance
inherited from an org template can appear under multiple sites and the row must be
unique per `(rule_id, site_id)` pair in the local catalog.

#### Foreign Keys

| Field | References | Notes |
|-------|------------|-------|
| `site_id` | `sites(id)` | Mist site that this derived rule applies to. |
| `org_id` | `orgs(id)` | Parent organization. |
| `template_id` | `wxlan_templates(id)` | Source WxLAN template when inherited. NULL otherwise. |
| `apply_tags[*]`, `src_wxtags[*]`, `dst_wxtags[*]`, `dst_allow_wxtags[*]`, `dst_deny_wxtags[*]` | `wxtags(id)` | Many-to-many references to WxTag definitions. Stored as pipe-delimited UUID strings in the CSV / SQLite row to keep the table flat. ArangoDB backend additionally creates edge collections for graph traversal. |

#### State Transitions

N/A -- read-only endpoint. The local SQLite row is overwritten on each fetch via
`INSERT OR REPLACE` keyed on `(id, site_id)`. There are no MistHelper-side state
transitions; the upstream rule lifecycle (create/update/delete) is managed by other
endpoints.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS site_wxrules_derived (
    id              TEXT    NOT NULL,
    site_id         TEXT    NOT NULL,
    org_id          TEXT,
    template_id     TEXT,
    "order"         INTEGER NOT NULL,
    action          TEXT,
    enabled         INTEGER,                    -- 1=true, 0=false
    for_site        INTEGER,                    -- 1=true, 0=false
    apply_tags      TEXT,                       -- pipe-delimited UUID list
    blocked_apps    TEXT,                       -- pipe-delimited app keys
    src_wxtags      TEXT,                       -- pipe-delimited UUID list
    dst_wxtags      TEXT,                       -- pipe-delimited UUID list
    dst_allow_wxtags TEXT,                      -- pipe-delimited UUID list
    dst_deny_wxtags  TEXT,                      -- pipe-delimited UUID list
    created_time    REAL,                       -- epoch seconds
    modified_time   REAL,                       -- epoch seconds
    fetched_at      REAL    NOT NULL,           -- MistHelper write time (epoch seconds)
    PRIMARY KEY (id, site_id)
);

CREATE INDEX IF NOT EXISTS idx_site_wxrules_derived_org
    ON site_wxrules_derived (org_id);
CREATE INDEX IF NOT EXISTS idx_site_wxrules_derived_template
    ON site_wxrules_derived (template_id);
CREATE INDEX IF NOT EXISTS idx_site_wxrules_derived_enabled
    ON site_wxrules_derived (enabled);
```

Note: `order` is reserved in SQLite, so the column is quoted. List-valued fields are
serialized as pipe-delimited (`|`) strings -- the existing flatten convention used by
sibling site-scoped exports for array-of-uuid fields.

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Entry

```python
'ListSiteWxRulesDerived': {                    # operationId from the OpenAPI spec
    'type': 'composite_pk',                    # multiple sites can share a rule id
    'primary_key': ['id', 'site_id'],          # composite natural key
    'indexes': ['org_id', 'template_id', 'enabled'],  # common NOC filter dimensions
    'table_name': 'site_wxrules_derived',      # explicit table for cross-file lookup
},
```

This entry is added to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary (declared near
line 1672 of `MistHelper.py`). Every executable line in the dictionary literal gets an
inline comment per Constitution Principle VI, as shown above.
