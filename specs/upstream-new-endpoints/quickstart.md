# Quickstart: Upstream New Endpoints

**Feature**: upstream-new-endpoints | **Date**: 2026-06-11

## Prerequisites

- Python 3.13+ with venv activated
- mistapi 0.62+ installed (`pip install mistapi>=0.62`)
- Valid `.env` with `MIST_API_TOKEN` and `MIST_ORG_ID`

## Implementation Order (by priority)

### Wave 1 — P1 Safe Exports (Menu 195–196)

1. Add `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries for `getSiteChannelScores` and `searchSiteIotEndpoints`
2. Implement `export_site_channel_scores()` method (menu 195)
3. Implement `search_site_iot_endpoints()` method (menu 196)
4. Add menu dispatch entries
5. Test: `python MistHelper.py --menu 195` and `--menu 196`

### Wave 2 — P2 Interactive (Menu 197–203)

1. Add PK strategies for auto-map and CoA endpoints
2. Implement auto-map operations (menu 197–200)
3. Implement NAC CoA operations (menu 202–203)
4. Implement Zigbee join (menu 201)
5. Add menu dispatch entries
6. Test each operation interactively

### Wave 3 — P3 Destructive (Menu 204–207)

1. Add PK strategies for SSO and MxEdge upgrade endpoints
2. Implement SSO admin deletion with 'DELETE' confirmation (menu 204–205)
3. Implement MxEdge upgrade management with 'UPGRADE' confirmation (menu 206–207)
4. Add menu dispatch entries
5. Manual testing only (destructive ops excluded from `--test`)

### Finalize

1. Update README.md operation count (194 → 207)
2. Update CHANGELOG.md with version entry
3. Run full quality gates: `py_compile`, `ruff check`, `black --check`
4. Execute deployment pipeline

## Verification

```bash
# Safe operations (automated)
python MistHelper.py --test

# New safe exports (manual spot-check)
python MistHelper.py --menu 195  # Channel scores
python MistHelper.py --menu 196  # IoT endpoints

# Interactive (manual)
python MistHelper.py --menu 202  # NAC CoA

# Destructive (manual with caution)
python MistHelper.py --menu 204  # SSO admin delete (requires confirmation)
```
