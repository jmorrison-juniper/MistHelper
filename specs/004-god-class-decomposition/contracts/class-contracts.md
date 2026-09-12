# Contracts: God Class Decomposition

**Feature**: 004-god-class-decomposition  
**Date**: 2026-03-04

## Overview

MistHelper is a CLI tool — it has no external API, library interface, or protocol contract. The "contracts" for this feature are the **public method signatures** that each sub-class exposes as its API surface.

These contracts ensure:
1. Every new sub-class has at most 5 public methods
2. Method signatures preserve exact parameter lists and return types
3. `menu_actions` wiring is documented for each class

## Contract Template

Every extracted sub-class follows this contract:

```python
class {Scope}{Domain}{Action}:
    """
    Extracted from {ParentClass} — {semantic_group_description}.

    Extraction Pattern (6-step process from Feature 003):
    1. Identified semantic group: {group_description}
    2. Created this class with {Scope}{Domain}{Action} naming
    3. Moved {N} methods preserving exact signatures
    4. Duplicated private helpers as needed
    5. Updated menu_actions and cross-references
    6. Validated via py_compile + Pylance + --test
    """

    # Pattern A: No __init__, all @staticmethod
    # Pattern B: __init__ with only required dependencies
    # Pattern C: Mix — static utilities + instance lifecycle

    # At most 5 public methods
    # Private helpers as needed (uncounted)
```

## Pattern A Contract (Stateless @staticmethod)

Applies to: OrgExportUtils, SiteExportUtils, GatewayExportUtils, PromptUtils, RoutingUtils, SiteConfigManager, GatewayTemplateConfigManager

```python
class {Scope}{Domain}{Action}:
    """Docstring with 6-step extraction pattern."""

    @staticmethod
    def method_1(...) -> ...: ...  # Preserved signature

    @staticmethod
    def method_2(...) -> ...: ...

    # ... up to 5 public methods

    @staticmethod
    def _private_helper(...) -> ...: ...  # Duplicated as needed
```

**menu_actions wiring**:
```python
"NN": ({Scope}{Domain}{Action}.method_name, "Description")
```

## Pattern B Contract (Instance-based)

Applies to: BulkAPFirmwareUpgrader, InventoryCSVComparator, FirmwareUpgradeStatusChecker, ServicePingManager, WAN2MigrationManager, MapReplacementWizard, MapsManager, WLANRadiusTimerManager, BulkSwitchFirmwareUpgrader, ConstDefinitionsExporter, FirmwareManager, SQLiteDatabaseWriter, GlobalImportManager

```python
class {Scope}{Domain}{Action}:
    """Docstring with 6-step extraction pattern."""

    def __init__(self, param1, param2):
        """Only the dependencies this sub-class needs."""
        self.param1 = param1
        self.param2 = param2

    def method_1(self, ...) -> ...: ...  # Preserved signature

    # ... up to 5 public methods

    def _private_helper(self, ...) -> ...: ...
```

**menu_actions wiring**:
```python
"NN": (lambda: {Scope}{Domain}{Action}(dep1, dep2).entry_method(), "Description")
```

## Pattern C Contract (Mixed static + instance)

Applies to: PacketCaptureManager, MSPInventoryExporter, SiteAutoUpgradeConfigurator, OrgLevelAPFirmwareUpgrader, EnhancedSSHRunner

```python
class {Scope}{Domain}{Action}:
    """Docstring with 6-step extraction pattern."""

    @staticmethod
    def static_utility(...) -> ...: ...

    def __init__(self, param1):
        self.param1 = param1

    def instance_method(self, ...) -> ...: ...

    # ... up to 5 public methods total (static + instance)
```

## Residual Parent Contract

After extraction, the original god class becomes a thin orchestrator:

```python
class {OriginalClassName}:
    """
    Residual parent after god class decomposition.
    
    Sub-classes:
    - {SubClass1}: {responsibility}
    - {SubClass2}: {responsibility}
    - ...
    
    This class retains at most 5 public methods that orchestrate
    the sub-classes or provide shared entry points.
    """

    # At most 5 public methods
    # Typically: execute/run + 1-4 orchestration methods
```

## Invariants

1. **No sub-class exceeds 5 public methods** — absolute limit, no exceptions
2. **No residual parent exceeds 5 public methods** — per FR-013
3. **Method signatures are preserved exactly** — parameters, return types, error handling
4. **Each sub-class is self-contained** — no shared state between sub-classes
5. **Private helpers are duplicated, not shared** — per FR-005
6. **Every sub-class has a 6-step docstring** — per FR-007
7. **All menu_actions references resolve** — verified via grep after each class
