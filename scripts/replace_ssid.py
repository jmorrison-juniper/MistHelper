"""Replace SSIDTemplateConsolidationManager class with thin stub."""
import sys

lines = open('MistHelper.py', 'r', encoding='utf-8').readlines()
start = 14678  # 0-indexed for line 14679
end = 16124    # 0-indexed for line 16125 (E911 class line, exclusive)

stub_lines = [
    'class SSIDTemplateConsolidationManager:\n',
    '    """Thin wrapper that delegates to src.ssid_consolidation.ssid_template_consolidation."""\n',
    '\n',
    '    @staticmethod\n',
    '    def execute():  # type: ignore[no-untyped-def]\n',
    '        """Static entry point - delegates to extracted module."""\n',
    '        from src.ssid_consolidation.ssid_template_consolidation import SSIDTemplateConsolidationManager as _Impl\n',
    '\n',
    '        _Impl.execute(\n',
    '            apisession=apisession,\n',
    '            page_limit=DEFAULT_API_PAGE_LIMIT,\n',
    '            safe_input_fn=InputUtils.safe_input,\n',
    '            write_data_fn=DataExporter.write_with_format_selection,\n',
    '            get_org_id_fn=ConfigUtils.get_cached_or_prompted_org_id,\n',
    '        )\n',
    '\n',
    '\n',
]

new_lines = lines[:start] + stub_lines + lines[end:]
open('MistHelper.py', 'w', encoding='utf-8').writelines(new_lines)
print(f'Replaced lines {start+1}-{end} with stub ({len(stub_lines)} lines)')
print(f'Original: {len(lines)} lines, New: {len(new_lines)} lines')
print(f'Lines removed: {len(lines) - len(new_lines)}')
