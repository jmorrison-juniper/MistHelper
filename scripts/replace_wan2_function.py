"""One-time script to replace function in MistHelper.py with delegation stub."""

filepath = "MistHelper.py"
lines = open(filepath, encoding="utf-8").readlines()

# Verify we're replacing the right thing
assert "def update_gateway_templates_wan2_variable" in lines[32097], (
    f"Expected function def at line 32098, got: {lines[32097]!r}"
)

stub_lines = [
    'def update_gateway_templates_wan2_variable(fast: bool = False, dry_run: bool = False):  # type: ignore[no-untyped-def]\n',
    '    """Menu #104: Update Gateway Templates WAN2 Variable Migration. Delegated to src.gateway.wan2_variable."""\n',
    '    from src.gateway.wan2_variable import GatewayWan2VariableMigrator  # pylint: disable=import-outside-toplevel\n',
    '\n',
    '    migrator = GatewayWan2VariableMigrator(\n',
    '        org_id=ConfigUtils.get_cached_or_prompted_org_id(),\n',
    '        apisession=apisession,\n',
    '        site_exclude_prefix=MIST_SITE_EXCLUDE_PREFIX,\n',
    '        check_and_generate_csv_fn=CacheUtils.check_and_generate_csv,\n',
    '        generate_templates_fn=GatewayExportUtils.templates,\n',
    '        generate_sites_fn=OrgSiteExporter.sites,\n',
    '        get_csv_path_fn=FilePathUtils.get_csv_path,\n',
    '        save_data_fn=DataExporter.save_data_to_output,\n',
    '        input_fn=InputUtils.safe_input,\n',
    '        connection_pool_fn=execute_with_connection_pool_management,\n',
    '    )\n',
    '    return migrator.execute(fast=fast, dry_run=dry_run)\n',
]

# Replace lines 32098-32818 (1-indexed) = lines[32097:32818] (0-indexed slice)
new_lines = lines[:32097] + stub_lines + lines[32818:]

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

removed = 32818 - 32097
added = len(stub_lines)
print(f"Done: removed {removed} lines, added {added} lines (net {added - removed})")
