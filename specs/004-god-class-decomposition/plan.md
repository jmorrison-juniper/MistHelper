# Implementation Plan: God Class Decomposition

**Branch**: `004-god-class-decomposition` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/004-god-class-decomposition/spec.md`

## Summary

Decompose all 25 god classes in `MistHelper.py` that violate the Constitution's 5-Item Rule (Principle I). Classes range from 22 to 72 methods each — all must be reduced to at most 5 public methods per class. The proven extraction pattern from Feature 003 (`OrgAlarmEventExporter`) is applied systematically: identify semantic groups of up to 5 methods, extract each group into a focused sub-class with its own private helpers, update all `menu_actions` references and cross-references, and validate between each class. Processing order is by method count descending (worst offenders first). No deployment until all 25 classes are compliant.

Three distinct class patterns guide the extraction strategy:
- **Pattern A (Stateless @staticmethod)**: OrgExportUtils, RoutingUtils, SiteConfigManager, GatewayTemplateConfigManager, PromptUtils, SiteExportUtils, GatewayExportUtils — follow `OrgAlarmEventExporter` exactly: duplicate private helpers, direct `menu_actions` references
- **Pattern B (Instance-based with constructor)**: BulkAPFirmwareUpgrader, InventoryCSVComparator, FirmwareUpgradeStatusChecker, ServicePingManager, MapReplacementWizard, WLANRadiusTimerManager, BulkSwitchFirmwareUpgrader, ConstDefinitionsExporter, MapsManager, WAN2MigrationManager, FirmwareManager, GlobalImportManager, SQLiteDatabaseWriter — pass required dependencies via constructor parameters, update lambda wrappers in `menu_actions`
- **Pattern C (Mixed static + instance)**: OrgLevelAPFirmwareUpgrader, SiteAutoUpgradeConfigurator, EnhancedSSHRunner, MSPInventoryExporter, PacketCaptureManager — hybrid approach separating static entry points from instance methods

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi >= 0.59.0 (Mist API SDK), internal classes (`APIDataFetcher`, `DataExporter`, `DataProcessingUtils`, `TimeUtils`, `ConfigUtils`, `WebSocketCommands`, `FirmwareManager`)
**Storage**: CSV files in `data/` directory + SQLite (`data/mist_data.db`) via dual output backend
**Testing**: `python MistHelper.py --test` (built-in test runner, skip list: 14, 18, 63-65, 90-100)
**Target Platform**: Windows 11 (local dev), Linux container (Podman production)
**Project Type**: CLI tool (single-file, ~54K lines)
**Performance Goals**: No change — existing API rate limiting and adaptive delay system preserved
**Constraints**: Zero user-visible behavior change; all existing `--test` invocations must pass (49/49 operations). Destructive operations (90-100) validated via syntax/structure only.
**Scale/Scope**: 25 classes decomposed, estimated ~187 new focused sub-classes created (per data-model.md decomposition map), ~54K lines modified in-place within `MistHelper.py`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Pre-Design Status | Explanation |
|-----------|-------------------|-------------|
| I. 5-Item Rule | **WILL FIX** | Current: 25 classes have 22-72 methods each. Design: every class reduced to at most 5 public methods via extraction into focused sub-classes. |
| II. Class-Based Architecture | **WILL FIX** | Current: some god classes are namespaces rather than cohesive classes. Design: each extracted sub-class has a clear single responsibility. No wrappers. |
| III. Safety-First Input | PASS | Refactoring preserves all existing `safe_input()` calls and destructive confirmation patterns. No new user input paths. |
| IV. Natural Business Keys | PASS | No primary key strategy changes. All existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries preserved. |
| V. Target Audience Clarity | PASS | Code clarity improves — smaller classes are easier for junior engineers to navigate. No language/jargon changes. |
| VI. Deployment Pipeline | PASS | Standard 6-step pipeline executed once after all 25 classes complete. |

**Gate Result**: PASS — violations in Principles I and II will be addressed. No violations require justification.

### Post-Design Re-Check

| Principle | Post-Design Status | Notes |
|-----------|-------------------|-------|
| I. 5-Item Rule | **RESOLVED** | All 25 god classes decomposed. Every resulting class (original residual + new sub-classes) has at most 5 public methods. Private helpers uncounted per convention. |
| II. Class-Based Architecture | **RESOLVED** | Each new sub-class has a clear single responsibility documented via docstring. `{Scope}{Domain}{Action}` naming convention followed. No wrappers. |
| III. Safety-First Input | PASS | All `safe_input()` patterns preserved in extracted methods. Destructive confirmations remain in their original call sites. |
| IV. Natural Business Keys | PASS | No changes to PK strategies. |
| V. Target Audience Clarity | PASS | Smaller, focused classes with descriptive names improve navigability for junior NOC engineers. Each class docstring documents the 6-step extraction pattern. |
| VI. Deployment Pipeline | PASS | Single deployment after all 25 classes complete. Pipeline documented in quickstart.md. |

**Post-Design Gate Result**: PASS — All pre-existing violations resolved. No new violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/004-god-class-decomposition/
  plan.md              # This file
  spec.md              # Feature specification (25 user stories)
  research.md          # Phase 0: class patterns, wiring patterns, extraction strategy
  data-model.md        # Phase 1: class decomposition map
  quickstart.md        # Phase 1: step-by-step extraction guide
  contracts/           # Phase 1: public API contracts per class category
  checklists/
    requirements.md    # Spec quality checklist
```

### Source Code (repository root)

```text
MistHelper.py          # Single-file CLI (all changes in this file)
  # PATTERN A - Stateless @staticmethod classes:
  class OrgExportUtils               # MODIFIED: reduced from 51 to <=5 methods
  class OrgAlarmEventExporter        # EXISTING: reference pattern (5 methods)
  class Org{Domain}Exporter          # NEW: ~10 sub-classes from OrgExportUtils
  class PromptUtils                  # MODIFIED: reduced from 28 to <=5 methods
  class {Domain}PromptHelper         # NEW: ~5 sub-classes from PromptUtils
  class ConstDefinitionsExporter     # MODIFIED: reduced from 36 to <=5 methods
  class {Domain}ConstExporter        # NEW: ~7 sub-classes
  class SiteExportUtils              # MODIFIED: reduced from 22 to <=5 methods
  class Site{Domain}Exporter         # NEW: ~4 sub-classes
  class GatewayExportUtils           # MODIFIED: reduced from 22 to <=5 methods
  class Gateway{Domain}Exporter      # NEW: ~4 sub-classes

  # PATTERN B - Instance-based classes:
  class BulkAPFirmwareUpgrader       # MODIFIED: reduced from 72 to <=5 methods
  class APFirmware{Step}Manager      # NEW: ~14 sub-classes
  class OrgLevelAPFirmwareUpgrader   # MODIFIED: reduced from 66 to <=5 methods
  class OrgAPFirmware{Step}Manager   # NEW: ~13 sub-classes
  class InventoryCSVComparator       # MODIFIED: reduced from 65 to <=5 methods
  class Inventory{Step}Processor     # NEW: ~13 sub-classes
  class FirmwareUpgradeStatusChecker # MODIFIED: reduced from 53 to <=5 methods
  class FirmwareStatus{Domain}       # NEW: ~10 sub-classes
  class ServicePingManager           # MODIFIED: reduced from 51 to <=5 methods
  class ServicePing{Step}Manager     # NEW: ~10 sub-classes
  # ... (similar for remaining 15 Pattern B classes)

  # PATTERN C - Infrastructure classes (no menu_actions):
  class GlobalImportManager          # MODIFIED: reduced from 27 to <=5 methods
  class {Domain}ImportHandler        # NEW: ~5 sub-classes
  class SQLiteDatabaseWriter         # MODIFIED: reduced from 26 to <=5 methods
  class SQLite{Domain}Handler        # NEW: ~5 sub-classes

  menu_actions dict                  # MODIFIED: all entries updated to new class names
```

**Structure Decision**: Single-file architecture per project convention. All changes are in `MistHelper.py`. No new files, directories, or modules created. Estimated ~100-150 new classes added, each with at most 5 public methods + private helpers.

## Complexity Tracking

> No violations to justify — all constitutional violations are being fixed, not introduced.
