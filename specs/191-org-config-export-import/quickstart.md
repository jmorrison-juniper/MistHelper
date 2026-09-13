# Quickstart: Org Config Export/Import

**Feature**: specs/191-org-config-export-import

## Prerequisites

- MistHelper running with valid `.env` credentials
- Source org has WAN/gateway configuration (networks, services, VPNs, gateway templates, device profiles, service policies)
- Destination org has API write access

## Export (Menu 176)

1. Start MistHelper (interactive or `--menu 176`)
2. Select Menu 176
3. Export runs automatically against the configured org
4. Output: `data/OrgConfig_Export_{org_name}_{timestamp}.json`
5. Summary table shows object counts per type

## Import (Menu 177)

1. Copy the export JSON file to `data/` directory on the destination system
2. Update `.env` to point to the destination org (or re-login)
3. Start MistHelper, select Menu 177
4. Select the export file from the numbered list
5. Choose dry-run (Y) or live import (n)
6. If live: type "IMPORT" to confirm
7. Review the import report (imported / skipped / failed)

## Common Workflows

### Full Migration

```text
1. Configure .env for SOURCE org
2. Run Menu 176 → produces export bundle
3. Configure .env for DESTINATION org
4. Run Menu 177 → dry-run first → then live import
5. Verify objects in Mist dashboard
```

### Verify Idempotency

```text
1. Run Menu 177 with same bundle a second time
2. All objects should show as "skipped (name conflict)"
3. Zero new objects created
```

## Key Behaviors

- **Dry-run**: Preview what would happen without making API calls
- **Conflict detection**: Objects with matching names or overlapping subnets are skipped
- **ID remapping**: Cross-references (e.g., service policies → services) are automatically updated
- **Partial failure**: If one type fails, remaining types still process
- **Empty types**: Types with zero objects in the bundle are silently skipped
