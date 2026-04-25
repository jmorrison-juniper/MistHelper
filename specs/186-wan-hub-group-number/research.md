# Research: WAN Hub Group Number Manager

**Feature**: 186-wan-hub-group-number | **Date**: 2025-07-17

## R1: Menu Number Assignment

**Question**: What menu number should this operation use?

**Decision**: `"163"` — the next sequential number after `"162"` (Wired Client Manufacturer Report).

**Rationale**: The current highest menu number is `"162"`. This operation is non-destructive in the traditional sense (it writes pod values via API, but pod changes are easily reversible by setting back to the original value). It does NOT belong in the 90-100 destructive range (firmware, reboots, VC conversions). It fits in the "advanced operations" category alongside other template/config management operations (103-114 range). However, following sequential ordering from the current maximum is simplest.

**Alternatives considered**:
- Placing in 103-114 range (gateway template operations): Rejected — those numbers are already allocated, and this is not a gateway template operation (it modifies VPN objects, not device profiles).
- Placing in 90-100 range: Rejected — pod updates are trivially reversible (set back to original value), no confirmation keyword needed. Standard `safe_input` with y/N confirmation suffices.

## R2: External Module Pattern

**Question**: How should the external module integrate with MistHelper.py?

**Decision**: Create `src/wan_hub_group_manager.py` with a `WanHubGroupNumberManager` class. Import in MistHelper.py alongside existing `src.db` imports. Register in `menu_actions` dict with a lambda that instantiates and calls `execute()`.

**Rationale**: MistHelper.py already imports from `src/`:
```python
from src.db import DatabaseConfig, configure_db_logging
from src.db.router import DatabaseRouter
```
The pattern is established. The new module follows the same convention. The class uses a static `execute()` entry point matching `SSIDTemplateConsolidationManager.execute`, `E911BSSIDReportGenerator.execute`, etc.

**Alternatives considered**:
- Inline in MistHelper.py: Rejected — spec explicitly requires external module (FR-008) to establish the pattern.
- Separate package under `src/wan_hub/`: Rejected — over-engineering for a single-file module. The 5-Item Rule is not violated by adding one more file to `src/`.

## R3: API Call Strategy

**Question**: How should the module call mistapi APIs?

**Decision**: Accept `apisession` (the global mistapi session) as a constructor parameter. Use `ConfigUtils.get_cached_or_prompted_org_id()` for org_id resolution (same as all other operations). Call `mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(apisession, org_id, type="gateway")` for profiles and `mistapi.api.v1.orgs.vpns.listOrgVpns(apisession, org_id)` for VPNs.

**Rationale**: This is identical to how `PacketCaptureManager`, `FirmwareManager`, and other classes work — they receive `apisession` and call mistapi directly. No abstraction layer needed.

**API calls required**:
1. `listOrgDeviceProfiles(apisession, org_id, type="gateway")` — list all gateway profiles
2. `listOrgVpns(apisession, org_id)` — list all org VPNs (filter to `hub_spoke` type in code)
3. `mistapi.get_all(response=response, mist_session=apisession)` — pagination helper
4. `mistapi.api.v1.orgs.vpns.updateOrgVpn(apisession, org_id, vpn_id, body=updated_vpn)` — update pod values

**Alternatives considered**:
- Creating an API abstraction: Rejected — adds complexity with no benefit. All existing operations call mistapi directly.
- Using `updateOrgDeviceProfile`: Rejected — pod values live on VPN path objects, not device profiles.

## R4: Input Handling Pattern

**Question**: How should user input be handled?

**Decision**: Use the existing `safe_input()` function from MistHelper.py (lines 2263-2296). The module imports it from MistHelper's global scope. For the pod update confirmation, use a simple y/N prompt (not a typed keyword like "UPGRADE") because pod changes are trivially reversible.

**Rationale**: `safe_input()` handles EOF (container/SSH disconnect), provides context logging, and supports default values. This is the mandated pattern per Constitution Principle III.

**Alternatives considered**:
- Requiring typed confirmation ("SET"): Rejected — pod changes are easily reversible (set back to original). Reserve typed confirmations for irreversible operations (firmware, reboots).
- Duplicating `safe_input` in the module: Rejected — FR-009 requires reusing existing infrastructure.

## R5: Module Dependencies from MistHelper.py

**Question**: What does the external module need from MistHelper.py?

**Decision**: The module needs:
1. `apisession` — global mistapi session (passed as constructor param)
2. `ConfigUtils.get_cached_or_prompted_org_id()` — org_id resolution (called directly from module)
3. `safe_input()` — EOF-safe input (imported from MistHelper)
4. `mistapi` — the SDK itself (imported directly in the module)
5. Standard library: `logging`

**Rationale**: The module should be as self-contained as possible while reusing the shared session and utilities. `ConfigUtils` and `safe_input` are the minimal dependencies from MistHelper.py.

**Import approach**: Since MistHelper.py is a monolith (not a package), the module will receive `apisession` and utility references as constructor parameters or via a simple initialization function, avoiding circular imports.

## R6: Error Handling Strategy

**Question**: How should API errors be handled?

**Decision**: Wrap API calls in try/except, log errors at Error level with traceback, display user-friendly messages, and return gracefully (never crash). Specific handling:
- Auth failure / 401: "API session may have expired. Please restart MistHelper."
- Rate limit / 429: Let mistapi's built-in retry handle it (the SDK has retry logic).
- Network timeout: "Network error communicating with Mist API. Please check connectivity."
- Permission denied / 403: "Your API token does not have permission to modify VPN objects."
- No matching paths: "No VPN paths found for profile '{name}'. The profile may not be part of any hub-spoke VPN."

**Rationale**: Matches existing error handling patterns across all MistHelper operations. The mistapi SDK handles retries for transient errors; the module handles non-retryable errors.

## R7: Inconsistent Pod Values

**Question**: How should the system handle profiles where VPN paths have different pod values?

**Decision**: Display a warning showing the inconsistent values, then proceed with the batch update to normalize all paths. Example: "Warning: Paths for VREIRV65 have mixed pod values (1, 5, 65). All will be updated to the new value."

**Rationale**: Per spec edge case and production data confirmation, all paths per profile should share the same pod. Inconsistency is a data anomaly, not a blocker. Batch-updating resolves the inconsistency.

## R8: Test Strategy

**Question**: How should this be tested?

**Decision**:
1. **Unit tests** in `tests/unit/test_wan_hub_group_manager.py` — mock mistapi calls, test input validation, prefix matching, batch update logic.
2. **Menu integration** — add `"163"` to the test harness skip list (it requires interactive input and live API) OR make it testable with `--test` flag by checking for test mode and using mock data.
3. **Manual testing** — run interactively against a real Mist org during development.

**Rationale**: Unit tests cover the logic. Interactive operations like this are typically in the test skip list because they require user input and live API state.
