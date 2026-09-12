# Implementation Plan: Bulk RADIUS WLAN Configuration

**Branch**: `001-radius-wlan-config` | **Date**: 2026-03-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-radius-wlan-config/spec.md`

## Summary

Add Menu 122 to scan all organization WLANs, identify those using RADIUS authentication, and bulk-configure optimal `auth_servers_timeout`, `auth_servers_retries`, and `fast_dot1x_timers` settings. Values are read from `.env` with sensible defaults, displayed at runtime, and applied after explicit user confirmation with CSV audit trail.

## Technical Context

**Language/Version**: Python 3.13+ (per pyproject.toml `requires-python = ">=3.13"`)  
**Primary Dependencies**: mistapi >= 0.59.0 (Mist API SDK), python-dotenv >= 1.0.0  
**Storage**: CSV export to `data/` directory for audit trail  
**Testing**: pytest + existing MistHelper test harness (`--test` mode)  
**Target Platform**: Windows 11 local development, Linux container (Podman)  
**Project Type**: CLI menu-driven tool - single ~53K line module (MistHelper.py)  
**Performance Goals**: Process 500+ WLANs without timeout using adaptive rate limiting  
**Constraints**: Must use existing MistHelper patterns, no additional dependencies  
**Scale/Scope**: Organizations with up to 1,000 WLANs across multiple sites

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. 5-Item Rule | PASS | New class `BulkRadiusWLANConfigManager` will have ≤5 public methods, each ≤25 lines. Internal helpers will be extracted as needed. |
| II. Class-Based Architecture | PASS | All functionality in `BulkRadiusWLANConfigManager` class, no wrapper functions. |
| III. Safety-First Input | PASS | Uses `safe_input()` for EOF handling, DESTRUCTIVE confirmation pattern ("Type 'APPLY' to proceed:"), validate-early approach. |
| IV. Natural Business Keys | PASS | Uses WLAN `id` and `site_id` from API as natural keys for change records. |
| V. Target Audience Clarity | PASS | Clear numbered display, explicit preview, configurable values shown at startup. Fred Rogers clarity for NOC engineers. |
| Naming Conventions | PASS | Full variable names (`wlan_config` not `wc`), no AI markers. |
| Logging Standards | PASS | ASCII-only logging, redact any sensitive data. |
| Deployment Pipeline | PASS | Will execute full 6-step pipeline after implementation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-radius-wlan-config/
├── plan.md              # This file
├── research.md          # Phase 0 output - API patterns, .env practices
├── data-model.md        # Phase 1 output - entity definitions
├── quickstart.md        # Phase 1 output - user guide for Menu 122
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

MistHelper uses a single-file architecture. All code lives in `MistHelper.py` (~53K lines).

```text
MistHelper.py
├── BulkRadiusWLANConfigManager  # NEW: After line ~46060 (after WLANRadiusTimerManager)
│   ├── __init__()               # Load .env config, initialize state
│   ├── manage()                 # Main entry point - orchestrates workflow
│   ├── _load_env_config()       # Read RADIUS_* values from .env
│   ├── _display_config()        # Show loaded .env values at startup
│   ├── _scan_org_wlans()        # Fetch all org WLANs
│   ├── _filter_radius_wlans()   # Identify RADIUS-enabled WLANs
│   ├── _display_wlans()         # Numbered list with current settings
│   ├── _parse_selection()       # Parse "all", ranges, comma-separated
│   ├── _display_preview()       # Show current vs proposed changes
│   ├── _apply_changes()         # Bulk update with rate limiting
│   └── _export_audit_trail()    # CSV export to data/
│
├── menu_actions dict            # Line ~50400 - Register Menu 122
│   └── "122": (lambda: BulkRadiusWLANConfigManager().manage(), "Bulk configure RADIUS...")
│
└── data/                        # Output directory
    └── BulkRadiusWLANConfig_YYYYMMDD_HHMMSS.csv  # Audit trail export
```

**Structure Decision**: Single-file architecture maintained per MistHelper conventions. New `BulkRadiusWLANConfigManager` class follows existing `WLANRadiusTimerManager` pattern, inserted after line ~46060.

## Complexity Tracking

> No constitution violations. All principles satisfied.

## Post-Design Constitution Re-Check

*Gate passed. Design verified against all principles after Phase 1 completion.*

| Principle | Verification |
|-----------|-------------|
| I. 5-Item Rule | VERIFIED: `BulkRadiusWLANConfigManager` has ~10 methods but only 2 public (`__init__`, `manage`). Internal helpers are ≤25 lines each. |
| II. Class-Based | VERIFIED: All functionality encapsulated in single class. No wrapper functions. |
| III. Safety-First | VERIFIED: EOF handling via `safe_input()`, DESTRUCTIVE confirmation with "APPLY" keyword, preview before apply. |
| IV. Natural Keys | VERIFIED: Using WLAN `id` from API as primary identifier in change records. |
| V. Target Audience | VERIFIED: Clear numbered display, loaded config shown at startup, explicit SSID names in preview. |

## Generated Artifacts

- [spec.md](spec.md) - Feature specification with requirements and user stories
- [research.md](research.md) - API patterns, .env practices, selection parsing
- [data-model.md](data-model.md) - WLANConfig, TargetConfig, ChangeRecord entities
- [quickstart.md](quickstart.md) - User guide for Menu 122

## Next Steps

Run `/speckit.tasks` to generate implementation task breakdown.
