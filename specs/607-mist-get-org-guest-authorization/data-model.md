# Phase 1 Data Model: GetOrgGuestAuthorization

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_guests_guest_mac.md` (200 OK body).
The endpoint returns a single JSON object (not a list, not paginated) describing one
guest's portal authorization record within an organization.

## Entities

The endpoint maps cleanly to a single logical entity for multi-backend persistence.
No nested arrays exist in the response, so no child-entity table is required.

### Entity 1: `GuestAuthorization`

One row per `(org_id, mac)`.

| Field | Type | Source | PK? | FK? | Notes |
|-------|------|--------|-----|-----|-------|
| `org_id` | TEXT | MistHelper context | YES | `org.id` | UUID supplied by user / `.env`; injected before write. |
| `mac` | TEXT | API `mac` | YES | -- | 12 lower-case hex chars, no separators. Normalized by MistHelper. |
| `authorized` | INTEGER | API `authorized` | -- | -- | 0 / 1 (SQLite booleans). Whether guest is currently authorized. |
| `authorized_time` | INTEGER | API `authorized_time` | -- | -- | Epoch seconds when the guest was authorized. |
| `authorized_expiring_time` | INTEGER | API `authorized_expiring_time` | -- | -- | Epoch seconds when authorization expires. |
| `minutes` | INTEGER | API `minutes` | -- | -- | Authorization duration in minutes (max 259200 = 180 days, default 1440). |
| `auth_method` | TEXT | API `auth_method` | -- | -- | Enum: `email`, `sms`, `sponsor`, `passphrase`, etc. (read-only). |
| `access_code_email` | TEXT | API `access_code_email` | -- | -- | Email the access code was sent to (only when `auth_method`==`email`). Treated as PII -- excluded from logs. |
| `ap_mac` | TEXT | API `ap_mac` | -- | `device.mac` | MAC of AP the guest was on during registration. |
| `ssid` | TEXT | API `ssid` | -- | `wlan.ssid` | Name of the SSID used to register. |
| `wlan_id` | TEXT | API `wlan_id` | -- | `wlan.id` | UUID of the WLAN. Indexed for joins. |
| `random_mac` | INTEGER | API `random_mac` | -- | -- | 0 / 1. Whether the client is using a randomized MAC. |
| `name` | TEXT | API `name` | -- | -- | User-supplied name. Treated as PII -- excluded from logs. |
| `email` | TEXT | API `email` | -- | -- | User-supplied email. Treated as PII -- excluded from logs. |
| `company` | TEXT | API `company` | -- | -- | User-supplied company. Treated as PII -- excluded from logs. |
| `field1` | TEXT | API `field1` | -- | -- | User-supplied free-text field. PII -- excluded from logs. |
| `field2` | TEXT | API `field2` | -- | -- | User-supplied free-text field. PII -- excluded from logs. |
| `field3` | TEXT | API `field3` | -- | -- | User-supplied free-text field. PII -- excluded from logs. |
| `field4` | TEXT | API `field4` | -- | -- | User-supplied free-text field. PII -- excluded from logs. |
| `polled_at_utc` | TEXT | MistHelper clock | -- | -- | ISO8601 UTC timestamp of the poll, for audit. |

## Relationships

- Logical FK from `org_id` to the `org` collection / table (populated by other
  MistHelper menu items).
- Logical FK from `wlan_id` to any `wlan`-keyed collection (e.g. the table populated
  by `listOrgWlans` or `getSiteWlanDerived`) when present.
- Logical FK from `ap_mac` to the device inventory tables. Not enforced by SQLite
  (mistapi guarantees consistency, not the local store).

## State Transitions

**N/A -- read-only endpoint.** MistHelper only fetches and persists the current
authorization snapshot. The underlying Mist resource has state (`authorized` can flip
true / false, the expiry can be extended), but MistHelper performs no transitions
through this menu item. Each successful poll **upserts** the row by the natural
composite PK `(org_id, mac)`, overwriting the prior snapshot.

## SQLite DDL

DataExporter will create this table on first run; the schema below documents the
exact shape so future migrations have a reference.

```sql
CREATE TABLE IF NOT EXISTS org_guest_authorization (
    org_id                    TEXT    NOT NULL,
    mac                       TEXT    NOT NULL,
    authorized                INTEGER,
    authorized_time           INTEGER,
    authorized_expiring_time  INTEGER,
    minutes                   INTEGER,
    auth_method               TEXT,
    access_code_email         TEXT,
    ap_mac                    TEXT,
    ssid                      TEXT,
    wlan_id                   TEXT,
    random_mac                INTEGER,
    name                      TEXT,
    email                     TEXT,
    company                   TEXT,
    field1                    TEXT,
    field2                    TEXT,
    field3                    TEXT,
    field4                    TEXT,
    polled_at_utc             TEXT,
    PRIMARY KEY (org_id, mac)
);

CREATE INDEX IF NOT EXISTS idx_org_guest_authorization_wlan_id
    ON org_guest_authorization (wlan_id);
CREATE INDEX IF NOT EXISTS idx_org_guest_authorization_ssid
    ON org_guest_authorization (ssid);
CREATE INDEX IF NOT EXISTS idx_org_guest_authorization_auth_method
    ON org_guest_authorization (auth_method);
CREATE INDEX IF NOT EXISTS idx_org_guest_authorization_authorized
    ON org_guest_authorization (authorized);
```

`INSERT OR REPLACE INTO org_guest_authorization (...) VALUES (...)` is the
upsert mode produced by the `natural_pk` strategy.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (current location near line ~1672):

```python
"getOrgGuestAuthorization": {
    "type": "natural_pk",                                       # PII record, upsert by user identity
    "primary_key": ["org_id", "mac"],                           # Composite -- same MAC may exist across orgs
    "indexes": ["wlan_id", "ssid", "auth_method", "authorized"],# Join + filter accelerators
},
```

## Validation Rules

- `org_id` must match `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`
  (case-insensitive). Failure -> `logging.warning` + early return.
- `mac` after normalization must match `^[0-9a-f]{12}$`. Failure -> `logging.warning`
  + early return.
- `authorized` is coerced from JSON `bool` to SQLite `INTEGER` (0 / 1) by
  DataExporter's existing bool-to-int adapter.
- `random_mac` is coerced the same way.
- `polled_at_utc` is generated by MistHelper as
  `datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")`.
