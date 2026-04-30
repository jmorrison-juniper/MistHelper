"""Replace VirtualChassisManager class in MistHelper.py with delegation stub."""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAIN = ROOT / "MistHelper.py"

STUB = '''\
# ============================================================================
# VIRTUAL CHASSIS MANAGER CLASS
# ============================================================================
class VirtualChassisManager:
    """Virtual chassis to virtual MAC conversion operations (Menus 92-94).

    Implementation extracted to src/device/virtual_chassis.py.
    This stub delegates to the extracted module while providing
    access to MistHelper globals (apisession, utility classes).
    """

    @staticmethod
    def convert_single(dry_run: bool = False) -> None:
        """Convert a single VC switch to virtual MAC (Menu 92)."""
        from src.device.virtual_chassis import (
            VirtualChassisManager as _VC,
        )

        _VC.convert_single(
            apisession=apisession,
            select_site_fn=PromptUtils.select_site,
            safe_input_fn=InputUtils.safe_input,
            get_csv_path_fn=FilePathUtils.get_csv_path,
            check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,
            inventory_generator=OrgInventoryExporter.inventory,
            dry_run=dry_run,
        )

    @staticmethod
    def convert_by_site_list() -> None:
        """Bulk convert VC switches from site list CSV (Menu 93)."""
        from src.device.virtual_chassis import (
            VirtualChassisManager as _VC,
        )

        _VC.convert_by_site_list(
            apisession=apisession,
            safe_input_fn=InputUtils.safe_input,
            get_csv_path_fn=FilePathUtils.get_csv_path,
            create_csv_template_fn=FilePathUtils.create_csv_template,
            check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,
            inventory_generator=OrgInventoryExporter.inventory,
            sites_generator=OrgSiteExporter.sites,
        )

    @staticmethod
    def check_status() -> None:
        """Check conversion status of all VC switches (Menu 94)."""
        from src.device.virtual_chassis import (
            VirtualChassisManager as _VC,
        )

        _VC.check_status(
            get_csv_path_fn=FilePathUtils.get_csv_path,
            check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,
            inventory_generator=OrgInventoryExporter.inventory,
            sites_generator=OrgSiteExporter.sites,
            flatten_fields_fn=DataProcessingUtils.flatten_nested_fields,
            escape_multiline_fn=DataProcessingUtils.escape_multiline,
            save_data_fn=DataExporter.save_data_to_output,
        )
'''

# Markers
CLASS_START = "# ============================================================================\n# VIRTUAL CHASSIS MANAGER CLASS\n# ============================================================================\nclass VirtualChassisManager:"
NEXT_CLASS = "# ============================================================================\n# SITE CONFIGURATION MANAGER CLASS\n# ============================================================================\nclass SiteConfigManager:"

source = MAIN.read_text(encoding="utf-8")

start_idx = source.index(CLASS_START)
end_idx = source.index(NEXT_CLASS)

# Verify we found reasonable boundaries
old_block = source[start_idx:end_idx]
old_lines = old_block.count("\n")
print(f"Found VirtualChassisManager block: {old_lines} lines")
assert 500 < old_lines < 600, f"Unexpected line count: {old_lines}"

new_source = source[:start_idx] + STUB + "\n\n" + source[end_idx:]

# Verify line count reduction
original_lines = source.count("\n")
new_lines = new_source.count("\n")
reduction = original_lines - new_lines
print(f"Original: {original_lines} lines")
print(f"New: {new_lines} lines")
print(f"Reduction: {reduction} lines")
assert reduction > 450, f"Expected significant reduction, got {reduction}"

MAIN.write_text(new_source, encoding="utf-8")
print("Replacement complete!")
