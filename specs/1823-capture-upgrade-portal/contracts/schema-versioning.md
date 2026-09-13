# Schema Versioning Contract: Capture Upgrade Portal (Issue #1823)

This document defines strategy for evolving data model without breaking sessions.

## Versioning Strategy

Each collection carries schema_version field.

Current version: 1

## Migration Procedure

### Adding a New Field

1. Increment schema_version
2. Make new field optional with sensible default
3. Backfill existing documents during off-hours
4. Update all code to handle both old and new field versions

### Removing a Field

1. Mark field as deprecated (log warning on read)
2. Continue reading for 2 releases
3. In release 3, increment schema_version and remove field
4. Backfill to delete field

### Renaming a Field

1. Add new field with new name (optional)
2. Keep old field for 2 releases
3. In release 3, remove old field

## Rollback Procedure

1. Stop portal
2. Restore ArangoDB from pre-upgrade backup
3. Flush Redis cache
4. Restart portal
5. Operator re-accepts or re-rejects comparison

## Backward Compatibility

Portal code must handle both current and previous schema versions.
