# Data Model: God Class Decomposition

**Feature**: 004-god-class-decomposition  
**Date**: 2026-03-04  
**Status**: Complete

## Overview

This feature is a pure refactoring operation — no new data entities, database tables, or API contracts are introduced. The "data model" for this feature is the **class decomposition map**: the mapping from each god class to its set of focused sub-classes.

## Entity: God Class

A class in `MistHelper.py` with more than 5 public methods, violating the Constitution's 5-Item Rule.

**Fields**:
- `class_name` (str): Current class name
- `method_count` (int): Total methods (public + private)
- `pattern` (enum): A (stateless @staticmethod), B (instance-based), C (mixed static + instance)
- `line_number` (int): Starting line in MistHelper.py
- `init_params` (list[str]): Constructor parameters (empty for Pattern A)

## Entity: Focused Sub-Class

A new class extracted from a god class, containing at most 5 semantically related public methods plus private helpers.

**Fields**:
- `class_name` (str): New class name following `{Scope}{Domain}{Action}` convention
- `parent_class` (str): Original god class this was extracted from
- `public_methods` (list[str]): At most 5 public method names
- `private_methods` (list[str]): Private helper methods (uncounted)
- `constructor_params` (list[str]): Only the dependencies this sub-class needs
- `semantic_group` (str): Human-readable description of the responsibility

## Entity: Extraction Group

A set of semantically related methods identified for extraction into a single focused sub-class.

**Fields**:
- `group_name` (str): Descriptive label (e.g., "Site Selection", "Version Selection")
- `methods` (list[str]): 2-5 public method names in this group
- `private_helpers` (list[str]): Private methods that support this group
- `target_class_name` (str): The focused sub-class this group becomes

## Relationships

```text
God Class (1) ──extracts──> (N) Focused Sub-Class
God Class (1) ──has──> (N) Extraction Group
Extraction Group (1) ──becomes──> (1) Focused Sub-Class
Focused Sub-Class (N) ──references──> (1) menu_actions entry
```

## State Transitions

Each god class goes through these states during decomposition:

```text
UNPROCESSED → ANALYZED → EXTRACTING → VALIDATING → COMPLIANT
```

- **UNPROCESSED**: Not yet examined (initial state for all 25)
- **ANALYZED**: Semantic groups identified, sub-class names chosen
- **EXTRACTING**: Methods being moved to new sub-classes
- **VALIDATING**: `py_compile` + Pylance + `--test` running
- **COMPLIANT**: All sub-classes have ≤5 public methods, all tests pass

## Decomposition Map

### Processing Order (by method count, descending)

| # | God Class | Methods | Pattern | Estimated Sub-classes |
|---|-----------|---------|---------|----------------------|
| 1 | BulkAPFirmwareUpgrader | 72 | B | 14 |
| 2 | OrgLevelAPFirmwareUpgrader | 66 | C | 13 |
| 3 | InventoryCSVComparator | 65 | B | 13 |
| 4 | FirmwareUpgradeStatusChecker | 53 | B | 10 |
| 5 | OrgExportUtils | 51 | A | 10 |
| 6 | ServicePingManager | 51 | B | 10 |
| 7 | MapReplacementWizard | 50 | B | 10 |
| 8 | WLANRadiusTimerManager | 47 | B | 9 |
| 9 | BulkSwitchFirmwareUpgrader | 46 | B | 9 |
| 10 | RoutingUtils | 40 | A | 8 |
| 11 | SiteAutoUpgradeConfigurator | 38 | C | 8 |
| 12 | ConstDefinitionsExporter | 36 | B | 7 |
| 13 | MapsManager | 35 | B | 7 |
| 14 | WAN2MigrationManager | 34 | B | 7 |
| 15 | SiteConfigManager | 32 | A | 7 |
| 16 | FirmwareManager | 32 | B | 6 |
| 17 | PromptUtils | 28 | A | 6 |
| 18 | GlobalImportManager | 27 | B | 5 |
| 19 | EnhancedSSHRunner | 27 | C | 5 |
| 20 | SQLiteDatabaseWriter | 26 | B | 5 |
| 21 | MSPInventoryExporter | 26 | C | 5 |
| 22 | PacketCaptureManager | 23 | C | 5 |
| 23 | GatewayTemplateConfigManager | 23 | A | 5 |
| 24 | SiteExportUtils | 22 | A | 5 |
| 25 | GatewayExportUtils | 22 | A | 5 |

**Total**: 1012 methods → ~187 new sub-classes + 25 residual parents (each ≤5 public methods)

## Validation Rules

1. Every god class residual MUST have ≤5 public methods after extraction
2. Every new sub-class MUST have ≤5 public methods
3. Private helpers are uncounted and duplicated where needed
4. No sub-class may share methods with another sub-class (no shared state)
5. Every `menu_actions` reference must resolve to an existing class.method
6. Every cross-reference must be updated (grep verification required)
