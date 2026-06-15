# Feature Specification: E911 Reporting Menu Operations

**Feature Branch**: `202-e911-menu-ops`
**Created**: 2026-06-11
**Status**: Draft
**Input**: Wire upstream mistapi (>=0.59) E911 endpoints (`getOrgE911Report`, `enableOrgE911Report`, `disableOrgE911Report`) as MistHelper menu operations with multi-backend output and NASA/JPL destructive confirmation patterns.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export E911 Report (Priority: P1)

NOC engineer needs to audit the current Enhanced 911 (E911) location reporting status across the org — which sites, APs, switches, and BSSIDs are participating in dispatchable-location reporting, and which are missing or stale — so they can prove regulatory compliance (RAY BAUM'S Act / Kari's Law) or hand the data to facilities.

**Why this priority**: Read-only, safe for all environments, satisfies the most common operator need (audit/report). Delivers value with zero risk; the toggle operations are useless without first being able to see current state.

**Independent Test**: Run the new "Export Org E911 Report" menu op against a real org. Confirm CSV/SQLite/ArangoDB output contains expected E911 status columns (site_id, device_mac, address, etc.), row count matches `mist_get_configuration_objects` baseline, and re-running the export performs an upsert (no duplicate rows) using the natural primary key.

**Acceptance Scenarios**:

1. **Given** a valid org_id with E911 reporting enabled on one or more sites, **When** operator selects the new E911 export menu op, **Then** the system fetches the report, flattens nested JSON, writes to the selected backend(s) (CSV / SQLite / ArangoDB+Redis), and prints a "wrote N records" summary.
2. **Given** the same op is re-run later, **When** the SQLite/ArangoDB backend is in use, **Then** existing rows are updated in place via the natural PK (no duplicates) and new rows are inserted.
3. **Given** an org with E911 disabled everywhere, **When** the export runs, **Then** the op completes successfully with zero rows written and an informational message ("No E911 report data returned for this org").

---

### User Story 2 - Enable E911 Reporting (Priority: P2)

NOC engineer needs to turn on E911 location reporting for an org that hasn't enabled it yet (e.g., a newly onboarded customer site that just received a compliance audit finding).

**Why this priority**: Destructive (changes regulatory posture and may trigger billing/feature gating), but operationally important. Lower than the export because the export is what operators reach for daily; enable is a one-shot remediation action.

**Independent Test**: Against a non-production org with E911 currently disabled, run the new "Enable Org E911 Reporting" menu op. Confirm the typed confirmation prompt appears, confirm the API call fires only after `ENABLE` is typed exactly, and confirm follow-up export (User Story 1) shows the new enabled state.

**Acceptance Scenarios**:

1. **Given** operator selects the enable op, **When** the destructive confirmation prompt appears, **Then** the system requires the operator to type the literal string `ENABLE` (case-sensitive) before any API call is made.
2. **Given** the operator types anything other than `ENABLE` (including empty input, `enable`, `y`, or EOF), **When** confirmation fails, **Then** the system logs "Operation cancelled - confirmation failed" and returns to the menu without contacting the Mist API.
3. **Given** the operator types `ENABLE` exactly, **When** the API call succeeds, **Then** the system logs success with org_id and prints a user-facing confirmation message including a reminder to re-run the export op to verify.

---

### User Story 3 - Disable E911 Reporting (Priority: P3)

NOC engineer needs to turn off E911 reporting for an org (e.g., decommissioning a tenant, customer requested opt-out, or troubleshooting a misconfigured dispatchable-location feed).

**Why this priority**: Destructive and high-impact (disabling E911 reporting may create regulatory exposure). Rare action; lowest priority because most operators will never invoke it, but symmetry with Enable means we ship both together.

**Independent Test**: Against a non-production org with E911 enabled, run the disable op. Confirm the typed confirmation prompt requires `DISABLE`, confirm API call only fires on exact match, and confirm follow-up export shows the disabled state.

**Acceptance Scenarios**:

1. **Given** operator selects the disable op, **When** the destructive confirmation prompt appears, **Then** the system requires the operator to type the literal string `DISABLE` (case-sensitive).
2. **Given** confirmation passes, **When** the API call fires and returns success, **Then** the system logs the org_id and the action, and prints a warning reminding the operator that any active E911 dependencies (PSAP routing, dispatchable-location feeds) are now disabled.

---

### Edge Cases

- **Read permission only**: Operator's API token has read-only scope. Export op should succeed; enable/disable should fail fast with a clear "insufficient permissions" message, not a stack trace.
- **API endpoint returns 404**: Org is on a Mist tenant that hasn't been upgraded to the E911 feature. Export should print "E911 reporting is not available for this org" and exit cleanly; enable/disable should print the same message and skip the confirmation prompt entirely.
- **Network failure mid-confirmation**: Operator types `ENABLE`, presses Enter, API call times out. Adaptive retry logic should apply (consistent with other destructive ops); on final failure, log the error with full context and tell the operator to re-run after checking connectivity.
- **EOF during confirmation prompt** (SSH session dropped): `safe_input` catches `EOFError`, logs the disconnect with context `e911_enable_confirm` / `e911_disable_confirm`, exits cleanly. No API call fires.
- **Empty report**: `getOrgE911Report` returns `[]`. Export writes zero rows, logs the count, exits with success. Backends are not asked to upsert nothing.
- **`--test` mode**: Export op (Story 1) is included in the regression sweep; enable/disable (Stories 2 & 3) are added to the existing destructive skip list alongside menu operations 154-194.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add three new menu operations corresponding to the three upstream mistapi E911 endpoints (`getOrgE911Report`, `enableOrgE911Report`, `disableOrgE911Report`).
- **FR-002**: The export operation MUST be placed in the "Safe Org Exports" range (1-59) at the next available slot; the enable and disable operations MUST be placed in the "Destructive" range (154-194 today, extended) at consecutive slots.
- **FR-003**: System MUST move/merge the existing draft primary-key strategy for `getOrgE911Report` from `scripts/pk_strategy_suggestions.py` into the canonical `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary inside `MistHelper.py`.
- **FR-004**: The export operation MUST use the multi-backend writer (`DataExporter.write_with_format_selection(..., api_function_name="getOrgE911Report")`) so the same data lands in CSV, SQLite, and ArangoDB/Redis based on operator configuration.
- **FR-005**: The export operation MUST flatten any nested JSON structures returned by the endpoint using the existing `flatten_dict()` helper before handing rows to the writer.
- **FR-006**: Enable and disable operations MUST require typed confirmation via `safe_input` (exact strings `ENABLE` and `DISABLE` respectively), following the NASA/JPL pattern already used by destructive operations.
- **FR-007**: Enable, disable, and export operations MUST emit `logging.info` before the API call and `logging.debug` (with row count or success status) after, per the project's action logging standard.
- **FR-008**: Every executable line of new code MUST carry an inline comment explaining intent, per the project's inline-comment standard.
- **FR-009**: The `--test` regression mode MUST include the export op in the standard sweep and MUST exclude enable/disable from automated execution (consistent with how menu 154-194 are skipped).
- **FR-010**: The system MUST update the README operation count (currently 207, becoming 210), update the menu category table to reflect the three new entries, and add a CHANGELOG entry in the project's `YY.MM.DD.HH.MM` UTC-timestamp format.
- **FR-011**: Failure modes (insufficient permissions, 404 not-available, network timeout, EOF) MUST be handled with user-facing messages and proper logging context, never raw stack traces.

### Key Entities

- **E911 Report Row**: A single record describing an E911 reporting status entry. Includes (at minimum) an entity identifier (site/device/BSSID), associated MAC/UUID, dispatchable location fields (address, building, floor, room), enabled/disabled flag, and a timestamp. Used as the unit of insert/upsert into the chosen backend.
- **E911 Toggle State**: An org-level boolean indicating whether E911 reporting is enabled. Not persisted by MistHelper; queried indirectly via the report endpoint and set by the enable/disable endpoints.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can produce a complete E911 status export for any reachable org in a single menu selection, with output landing in all configured backends, in under 60 seconds for orgs with up to 1,000 sites.
- **SC-002**: Re-running the export the next day produces zero duplicate rows in SQLite/ArangoDB (verified by row count equality before and after a no-change re-run) thanks to natural-key upsert.
- **SC-003**: Enable and disable operations cannot fire their API call without an exact typed confirmation; 100% of confirmation-prompt failures (wrong string, EOF, empty input) result in zero API calls and a logged cancellation message.
- **SC-004**: README operation count, menu category table, and CHANGELOG all reflect the three new operations after the change ships (verified by diff inspection at PR time).
- **SC-005**: Unit-test coverage for the new code paths (flatten + PK upsert for the export; confirmation-gate behavior for enable/disable) meets or exceeds the project's 70% coverage gate.
- **SC-006**: A NOC engineer with no prior exposure to E911 in MistHelper can locate and run the export op from the menu in under 90 seconds, given only the existing menu category labels.

## Assumptions

- The three upstream mistapi endpoints (`getOrgE911Report`, `enableOrgE911Report`, `disableOrgE911Report`) are present, stable, and accurately documented in mistapi >= 0.59; no further upstream changes are expected before this feature ships.
- The PK strategy draft in `scripts/pk_strategy_suggestions.py` line 609 is correct as-is and can be moved verbatim into `ENDPOINT_PRIMARY_KEY_STRATEGIES`; if it turns out to need refinement during implementation, that refinement is in scope.
- E911 enable/disable are org-scoped (not site-scoped) — confirmed by the endpoint name pattern. If the upstream endpoint signature requires a site_id, that becomes an additional prompt in the destructive ops (still in scope).
- The project's existing menu-numbering convention (next available slot in the appropriate category range) is the right home; no need to renumber existing ops to make room.
- The destructive confirmation strings `ENABLE` and `DISABLE` are acceptable to the operations team; they are consistent with `UPGRADE` and `CONFIRM` used elsewhere.
- A current Mist tenant with E911 actually enabled is available for smoke-testing User Stories 1 and 3; if not, the implementer falls back to mocking the API client for unit tests and defers User Story 3's manual smoke test to a follow-up.
- Out of scope: building an interactive E911 configuration wizard, replicating the Mist dashboard's E911 visualization, validating dispatchable-location field correctness, integrating with external PSAP/ALI databases.
