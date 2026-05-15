# Implementation Plan: Org Config Export/Import (Cross-Org Migration)

**Branch**: `feat/191-org-config-export-import` | **Date**: 2026-05-14 | **Spec**: `specs/191-org-config-export-import/spec.md`
**Input**: Feature specification from `/specs/191-org-config-export-import/spec.md`

## Summary

Two new menu operations (176 = export, 177 = import) that enable cross-org migration of WAN/gateway configuration. Menu 176 fetches all 6 org-level config types (networks, services, VPNs, gateway templates, device profiles, service policies) into a single timestamped JSON bundle. Menu 177 imports that bundle into a different org with conflict detection (name match, IP/subnet overlap), dependency-ordered creation, and cross-reference ID remapping.

**Technical approach**: A new `OrgConfigMigrationManager` class encapsulates all export/import/conflict/remapping logic. Export uses existing `listOrg*` API calls. Import uses confirmed `createOrg*` endpoints. IP overlap detection uses Python's `ipaddress` module (already imported). The class follows the established pattern of `WAN2MigrationManager` — init with org_id, public entry points for each menu, private helpers for subsections.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi 0.59+ (all 6 list + 6 create endpoints confirmed)
**Storage**: JSON files in `data/` directory (export bundles); no database storage needed for this feature
**Testing**: `python MistHelper.py --test` (menu 176 = safe read-only; menu 177 = destructive, skip in auto-test)
**Target Platform**: Windows 11 local dev + Linux container (Podman)
**Project Type**: CLI menu-driven tool (single-file: MistHelper.py)
**Performance Goals**: Complete export/import of ≤50 objects in <10 minutes (SC-001)
**Constraints**: Existing adaptive rate limiting handles API throttling; max 5 params/function, max 25 lines/function
**Scale/Scope**: Typical deployment: 5-50 config objects across 6 types

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | Class decomposed into ≤5 public methods; each method ≤25 lines via private helpers |
| II. Class-Based Architecture | PASS | All logic in `OrgConfigMigrationManager`; no standalone wrappers |
| III. Safety-First | PASS | `safe_input()` for all prompts; typed "IMPORT" confirmation; dry-run before actual import |
| IV. Full Deployment Pipeline | PASS | Standard pipeline applies; no special deployment considerations |
| V. Observability & Logging | PASS | ASCII-only logging; debug for API responses, info for progress, error with traceback |
| PK Strategy Required | PASS | All 6 `listOrg*` endpoints already have PK strategies defined in `ENDPOINT_PRIMARY_KEY_STRATEGIES` |
| Technology Constraints | PASS | Uses mistapi SDK exclusively; `os.path.join()` for paths; output to `data/` |
| Security: Fix Over Suppress | PASS | No new security patterns introduced; input validation on file path selection |

## Project Structure

### Documentation (this feature)

```text
specs/191-org-config-export-import/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── export-bundle-schema.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # Single main file — add OrgConfigMigrationManager class
                         # Add menu entries 176, 177
                         # Add test metadata entries
```

**Structure Decision**: All code lives in MistHelper.py (single-file architecture). The new class `OrgConfigMigrationManager` is added alongside existing manager classes (near `WAN2MigrationManager` at line ~22783). No new files or modules needed.

## Complexity Tracking

No constitution violations. The feature fits within existing patterns.

---

## Phase 0: Research

### R1: mistapi Create Endpoint Signatures

**Decision**: All 6 create endpoints exist and follow a consistent signature pattern:
```python
createOrg*(apisession, org_id, body=<dict>)
```

Confirmed endpoints:

| Endpoint | Module |
| - | - |
| `createOrgNetwork` | `mistapi.api.v1.orgs.networks` |
| `createOrgService` | `mistapi.api.v1.orgs.services` |
| `createOrgVpn` | `mistapi.api.v1.orgs.vpns` |
| `createOrgGatewayTemplate` | `mistapi.api.v1.orgs.gatewaytemplates` |
| `createOrgDeviceProfile` | `mistapi.api.v1.orgs.deviceprofiles` |
| `createOrgServicePolicy` | `mistapi.api.v1.orgs.servicepolicies` |

**Rationale**: The mistapi SDK (0.59+) provides full CRUD for all 6 types. No direct HTTP calls needed.

### R2: Menu Number Assignment

**Decision**: Use menu numbers **176** (export) and **177** (import).

**Rationale**: Menu 130 and 131 are already taken by `DeviceUtilityCommands.show_bgp_summary` and `DeviceUtilityCommands.show_arp_table`. The highest currently used menu number is 175 (`CacheUtils.clear_cache`). Numbers 176-177 are the next sequential available slots.

### R3: IP/Subnet Overlap Algorithm

**Decision**: Use Python's `ipaddress.ip_network()` with `overlaps()` method from the stdlib `ipaddress` module (already imported at line 37).

**Algorithm**:
1. Collect all existing network subnets from destination org via `listOrgNetworks`
2. For each imported network, parse its `subnet` field as `ip_network(strict=False)`
3. Check `new_network.overlaps(existing_network)` against all existing subnets
4. For services with `addresses[]`, parse each as `ip_network` or `ip_address` and check containment

**Rationale**: `ipaddress` is stdlib, already imported, handles both IPv4 and IPv6, and the `overlaps()` method is purpose-built for this use case. `strict=False` handles host bits in CIDR notation gracefully.

### R4: Cross-Reference ID Fields to Remap

**Decision**: Remap top-level ID reference fields only (v1 scope).

| Object Type | Fields Containing Foreign IDs |
| - | - |
| VPNs | `networks[]` entries keyed by network name — contain `id` referencing network IDs |
| Gateway templates | Network references in `networks[]`, VPN references in various config sections |
| Device profiles | `gateway_template_id` field |
| Service policies | `services[].id` or service references in rules |
| Networks | No foreign IDs (standalone) |
| Services | No foreign IDs (standalone) |

**Known limitation**: Nested objects within gateway templates (port configs, routing policies, DHCP relay targets) are NOT remapped in v1.

**Rationale**: Top-level references cover the critical dependency chain. Nested remapping adds significant complexity for edge cases; can be added in v2 based on user feedback.

### R5: Fields to Strip Before Import

**Decision**: Strip these source-org-specific fields from each object before creating in destination org:
- `id` — will be assigned by destination org API
- `org_id` — will be the destination org's ID
- `created_time` — system-generated
- `modified_time` — system-generated
- `for_site` — org-level objects should not carry site references across orgs

**Rationale**: These are all server-managed fields. Sending them in a create request either causes errors or creates misleading metadata.

### R6: Existing Codebase Patterns

**Decision**: Follow the `WAN2MigrationManager` pattern:
- `__init__` stores `self.org_id` from `ConfigUtils.get_cached_or_prompted_org_id()`
- Public entry methods (`export_config`, `import_config`) are the menu handlers
- Private `_helpers` decompose into ≤25-line functions
- Menu registration via lambda in the operations dictionary
- Test metadata in `TEST_OPERATION_METADATA`

**Rationale**: Consistency with existing codebase patterns. The lambda-based menu registration pattern is used by all similar operations (163, 164, 165).

---

## Phase 1: Design

### Class Architecture: `OrgConfigMigrationManager`

```
OrgConfigMigrationManager
├── __init__(apisession, org_id_fn, safe_input_fn)
├── export_config()          # Menu 176 entry point
├── import_config()          # Menu 177 entry point
│
├── _ExportHelper (private methods grouped by concern)
│   ├── _fetch_config_type(config_type)
│   ├── _build_export_bundle(results)
│   └── _save_bundle_to_file(bundle)
│
├── _ImportHelper (private methods grouped by concern)
│   ├── _load_and_validate_bundle(filepath)
│   ├── _select_import_file()
│   ├── _prompt_dry_run()
│   ├── _confirm_import()
│   └── _execute_import(bundle, dry_run)
│
├── _ConflictDetector (private methods grouped by concern)
│   ├── _fetch_existing_objects()
│   ├── _detect_conflicts(new_obj, existing, type_key)
│   ├── _check_name_conflict(new_obj, existing)
│   └── _check_subnet_overlap(new_obj, existing, type_key)
│
├── _IdRemapper (private methods grouped by concern)
│   ├── _build_remap_entry(source_id, dest_id)
│   ├── _remap_object_references(obj, type_key)
│   └── _strip_source_fields(obj)
│
└── _ReportGenerator (private methods grouped by concern)
    ├── _display_export_summary(bundle)
    └── _display_import_report(results)
```

**5-Item Rule compliance**: The class has 2 public methods + constructor (3 items). Private helpers are logically grouped by concern with each ≤25 lines. Constructor takes 3 params.

### Config Type Registry

A class-level constant defines the 6 config types with their API mappings:

```python
CONFIG_TYPES = [
    {
        "key": "networks",
        "list_fn": mistapi.api.v1.orgs.networks.listOrgNetworks,
        "create_fn": mistapi.api.v1.orgs.networks.createOrgNetwork,
        "import_order": 0,
        "display_name": "Networks",
        "has_subnet": True,
    },
    {
        "key": "services",
        "list_fn": mistapi.api.v1.orgs.services.listOrgServices,
        "create_fn": mistapi.api.v1.orgs.services.createOrgService,
        "import_order": 0,
        "display_name": "Services",
        "has_addresses": True,
    },
    {
        "key": "vpns",
        "list_fn": mistapi.api.v1.orgs.vpns.listOrgVpns,
        "create_fn": mistapi.api.v1.orgs.vpns.createOrgVpn,
        "import_order": 1,
        "display_name": "VPNs",
    },
    {
        "key": "gateway_templates",
        "list_fn": mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates,
        "create_fn": mistapi.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate,
        "import_order": 1,
        "display_name": "Gateway Templates",
    },
    {
        "key": "device_profiles",
        "list_fn": mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles,
        "create_fn": mistapi.api.v1.orgs.deviceprofiles.createOrgDeviceProfile,
        "import_order": 2,
        "display_name": "Device Profiles",
        "list_kwargs": {"type": "gateway"},
    },
    {
        "key": "service_policies",
        "list_fn": mistapi.api.v1.orgs.servicepolicies.listOrgServicePolicies,
        "create_fn": mistapi.api.v1.orgs.servicepolicies.createOrgServicePolicy,
        "import_order": 2,
        "display_name": "Service Policies",
    },
]
```

### Export Flow

1. User selects Menu 176
2. `export_config()` gets org_id, iterates CONFIG_TYPES sorted by key
3. For each type: calls `list_fn(apisession, org_id, limit=1000, **list_kwargs)`
4. Handles API errors per-type (continue on failure, log error)
5. `_build_export_bundle()` wraps data with metadata:
   - `source_org_id`, `source_org_name`, `export_timestamp`, `misthelper_version`
   - Per-type object counts
   - The raw API responses per type
6. `_save_bundle_to_file()` writes to `data/OrgConfig_Export_{org_name}_{timestamp}.json`
7. `_display_export_summary()` prints table of counts

### Import Flow

1. User selects Menu 177
2. `_select_import_file()` globs `data/OrgConfig_Export_*.json`, numbers them, user picks
3. `_load_and_validate_bundle()` parses JSON, checks required keys exist
4. Version mismatch → warning (proceed if user confirms)
5. `_prompt_dry_run()` → "[Y/n]"
6. `_fetch_existing_objects()` retrieves current state for all 6 types from destination org
7. For each type (sorted by `import_order`):
   a. For each object in that type's array:
      - `_strip_source_fields()` removes id/org_id/timestamps
      - `_detect_conflicts()` checks name + subnet overlap
      - If conflict: record skip reason, continue
      - If no conflict: `_remap_object_references()` updates foreign IDs
      - If dry-run: record "would import", continue
      - If live: call `create_fn(apisession, org_id, body=obj)`
      - Record new ID in remap table via `_build_remap_entry()`
8. `_confirm_import()` requires "IMPORT" typed confirmation (before step 7 API calls)
9. `_display_import_report()` shows three-section table: imported / skipped / failed

### IP/Subnet Overlap Detection

```python
def _check_subnet_overlap(self, new_obj, existing_objects, type_key):
    """Check for IP/subnet overlaps between new and existing objects."""
    if type_key == "networks":
        new_subnet = new_obj.get("subnet")
        if not new_subnet:
            return None
        try:
            new_net = ipaddress.ip_network(new_subnet, strict=False)
        except ValueError:
            return None  # Skip unparseable subnets
        for existing in existing_objects:
            existing_subnet = existing.get("subnet")
            if not existing_subnet:
                continue
            try:
                existing_net = ipaddress.ip_network(existing_subnet, strict=False)
            except ValueError:
                continue
            if new_net.overlaps(existing_net):
                return {
                    "reason": "subnet_overlap",
                    "detail": f"{new_subnet} overlaps with '{existing.get('name')}' ({existing_subnet})",
                }
    elif type_key == "services":
        # Check addresses[] for overlaps
        new_addrs = new_obj.get("addresses", [])
        if not new_addrs:
            return None
        for addr in new_addrs:
            try:
                new_net = ipaddress.ip_network(addr, strict=False)
            except ValueError:
                continue
            for existing in existing_objects:
                for ex_addr in existing.get("addresses", []):
                    try:
                        ex_net = ipaddress.ip_network(ex_addr, strict=False)
                    except ValueError:
                        continue
                    if new_net.overlaps(ex_net):
                        return {
                            "reason": "address_overlap",
                            "detail": f"{addr} overlaps with '{existing.get('name')}' ({ex_addr})",
                        }
    return None
```

### ID Remapping

The remap table is built as objects are created:

```python
# Key: source org object ID → Value: destination org new ID
self._remap_table: dict[str, str] = {}
```

Before creating each object in tier 1+, reference fields are walked and source IDs replaced with destination IDs from the remap table. For skipped objects (conflicts), the system looks up the existing object by name to populate the remap table, enabling downstream references to resolve.

### Menu Integration

```python
# In OPERATIONS dict (after entry "175"):
"176": (
    lambda: OrgConfigMigrationManager(
        apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
    ).export_config(),
    "Export Org WAN/Gateway Config (JSON bundle for cross-org migration)",
),
"177": (
    lambda: OrgConfigMigrationManager(
        apisession, ConfigUtils.get_cached_or_prompted_org_id, InputUtils.safe_input
    ).import_config(),
    "Import Org WAN/Gateway Config (cross-org migration with conflict detection)",
),
```

### Test Metadata

```python
# In TEST_OPERATION_METADATA:
"176": {"category": "safe"},  # Read-only export
"177": {
    "category": "destructive",
    "skip_reason": "DESTRUCTIVE: Creates config objects in destination org",
},
```

### Testing Strategy

| Test Type | Coverage | How |
| - | - | - |
| Export (Menu 176) | Auto-testable | Runs in `--test` suite; reads org config, writes JSON to `data/` |
| Import dry-run | Manual | Run Menu 177 with dry-run=Y against test org; verify report only |
| Import actual | Manual | Run against clean/sandbox org; verify objects created |
| Idempotent re-import | Manual | Run same bundle twice; verify second run = 100% skipped |
| Conflict detection | Manual | Import into org with overlapping names/subnets; verify skip+reason |
| ID remapping | Manual | Export config with cross-references; import into clean org; verify references |
| Corrupt file handling | Unit-testable | Feed invalid JSON to `_load_and_validate_bundle()` |
| Empty types | Auto-testable | Covered by Menu 176 test (some types may be empty) |

## Constitution Re-Check (Post-Design)

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | 2 public methods, constructor takes 3 params, all helpers ≤25 lines |
| II. Class-Based Architecture | PASS | Single class `OrgConfigMigrationManager`, no wrappers |
| III. Safety-First | PASS | `safe_input()` everywhere; "IMPORT" typed confirmation; dry-run option |
| IV. Full Deployment Pipeline | PASS | No special deployment; standard commit→push→build→pull→restart |
| V. Observability | PASS | Logging at debug/info/error levels; ASCII only |
| PK Strategies | N/A | Export/import uses JSON files, not database storage |
| Security | PASS | File path validated via glob pattern; no user-supplied paths; no secrets logged |
