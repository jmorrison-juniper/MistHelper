# Quickstart: God Class Decomposition

**Feature**: 004-god-class-decomposition  
**Date**: 2026-03-04

## Prerequisites

- Python 3.13+ installed
- Virtual environment activated: `.venv\Scripts\Activate.ps1`
- On branch `004-god-class-decomposition`
- All current tests passing: `python MistHelper.py --test` (49/49, 0 failures)

## Step-by-Step Extraction Process

### For Each God Class (repeat 25 times, in order)

#### Step 1: Analyze the Class

```powershell
# Count current methods
grep -c "def " MistHelper.py | Select-String "{ClassName}"

# List all methods with line numbers
Select-String -Path MistHelper.py -Pattern "def .*self|@staticmethod" -Context 0 | 
  Where-Object { $_ -match "{ClassName}" }
```

Identify semantic groups of up to 5 public methods each. Reference `research.md` for pre-analyzed groupings.

#### Step 2: Create the Sub-Class

For **Pattern A** (stateless @staticmethod):
```python
class OrgDeviceExporter:
    """
    Extracted from OrgExportUtils -- device-related organization exports.

    Extraction Pattern (6-step process from Feature 003):
    1. Identified semantic group: device inventory, stats, and config exports
    2. Created OrgDeviceExporter with {Scope}{Domain}{Action} naming
    3. Moved 5 methods preserving exact signatures
    4. Duplicated _export_data private helper
    5. Updated menu_actions entries for device export menus
    6. Validated via py_compile + Pylance + --test
    """

    @staticmethod
    def _export_data(api_call, data_type, sort_key, **api_kwargs):
        """Duplicated helper -- same implementation as OrgExportUtils._export_data."""
        # exact copy of implementation
        pass

    @staticmethod
    def device_inventory():
        """Export organization device inventory."""
        # exact copy from OrgExportUtils.device_inventory
        pass
```

For **Pattern B** (instance-based):
```python
class APFirmwareSiteSelector:
    """
    Extracted from BulkAPFirmwareUpgrader -- site selection for firmware upgrades.

    Extraction Pattern (6-step process from Feature 003):
    1. Identified semantic group: site selection and filtering
    2. Created APFirmwareSiteSelector with {Scope}{Domain}{Action} naming
    3. Moved 5 methods preserving exact signatures
    4. Constructor receives only org_id and sites_override
    5. Updated BulkAPFirmwareUpgrader.execute() to use this class
    6. Validated via py_compile + Pylance + --test
    """

    def __init__(self, org_id, sites_override=None):
        self.org_id = org_id
        self.sites_override = sites_override
```

#### Step 3: Move Methods

- Copy each method exactly (same parameters, same body, same return value)
- For `self` methods: update `self.xxx` references to use constructor-injected params
- For shared private helpers: duplicate into the new class

#### Step 4: Update References

```powershell
# Find all references to the old class.method
Select-String -Path MistHelper.py -Pattern "OrgExportUtils\.device_inventory"

# Update menu_actions
# Before: "11": (OrgExportUtils.device_inventory, "Export Org Device Inventory")
# After:  "11": (OrgDeviceExporter.device_inventory, "Export Org Device Inventory")

# Update cross-references
# Check _refresh_support_data tuples
# Check internal class-to-class calls
```

#### Step 5: Remove from Parent

Delete the moved methods from the original god class. Verify the parent now has fewer methods.

#### Step 6: Validate

```powershell
# Syntax check
python -m py_compile MistHelper.py

# Type check (Pylance in VS Code -- zero errors)

# Full test suite
python MistHelper.py --test
# Expected: 49/49 pass, 0 failures
```

If any validation fails: fix before proceeding to next extraction group.

### After All Groups Extracted from One Class

Verify the residual parent has at most 5 public methods. If not, continue extracting until compliant.

### After All 25 Classes Complete

```powershell
# Final validation
python -m py_compile MistHelper.py
python MistHelper.py --test

# Verify class method counts
Select-String -Path MistHelper.py -Pattern "class \w+" | ForEach-Object {
    $className = ($_ -match 'class (\w+)') | Out-Null; $Matches[1]
}
```

## Deployment (After All 25 Classes)

```powershell
# Step 1: Validate syntax
python -m py_compile MistHelper.py

# Step 2: Commit and push
git add MistHelper.py README.md
git commit -m "version YY.MM.DD.HH.MM - God class decomposition: all 25 classes compliant"
git push origin main

# Step 3: Wait for container build
gh run list --workflow=container-build.yml --limit 1
gh run watch <run-id>

# Step 4: Pull new image
podman pull ghcr.io/jmorrison-juniper/misthelper:latest

# Step 5: Restart container
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" ghcr.io/jmorrison-juniper/misthelper:latest

# Step 6: Verify
podman ps
```

## Common Pitfalls

1. **Forgetting to update menu_actions**: Every moved public method that appears in `menu_actions` must have its reference updated
2. **Missing cross-references**: grep for the class name AND each method name individually
3. **Breaking `self` references**: When moving instance methods, ensure all `self.xxx` references exist in the new class's constructor
4. **Shared helpers**: Always duplicate, never share. Two classes having identical `_export_data` is correct.
5. **Residual parent exceeds 5**: Keep extracting groups until compliant. No exemptions per FR-013.
6. **Circular imports within single file**: Not possible (single file), but watch for circular method calls between new sub-classes.
