"""One-time script to replace E911BSSIDReportGenerator with a stub."""

import pathlib

MISTHELPER = pathlib.Path(__file__).resolve().parent.parent / "MistHelper.py"

lines = MISTHELPER.read_text(encoding="utf-8").splitlines(keepends=True)

# Find boundaries
start = None
end = None
for i, line in enumerate(lines):
    if line.strip() == "class E911BSSIDReportGenerator:":
        start = i
    if start is not None and i > start and line.strip() == "class OrgTemplateExporter:":
        end = i
        break

if start is None or end is None:
    raise RuntimeError(f"Could not find boundaries: start={start}, end={end}")

print(f"Replacing lines {start + 1} through {end} (0-indexed: {start}:{end})")

stub = [
    "class E911BSSIDReportGenerator:\n",
    '    """E911 BSSID Compliance Report (Menu 160).\n',
    "\n",
    "    Implementation extracted to src/reports/e911_bssid.py.\n",
    "    This stub delegates to the extracted module while providing\n",
    "    access to MistHelper globals (apisession, ConfigUtils, etc.).\n",
    '    """\n',
    "\n",
    "    @staticmethod\n",
    "    def execute() -> None:\n",
    '        """Generate E911 BSSID compliance report (Menu 160)."""\n',
    "        from src.reports.e911_bssid import (\n",
    "            E911BSSIDReportGenerator as _E911,\n",
    "        )\n",
    "\n",
    "        current_org_id = ConfigUtils.get_cached_or_prompted_org_id()\n",
    "        if not current_org_id:\n",
    '            print("! No organization selected. Exiting.")\n',
    "            return\n",
    "        _E911.execute(\n",
    "            apisession=apisession,\n",
    "            page_limit=DEFAULT_API_PAGE_LIMIT,\n",
    "            org_id=current_org_id,\n",
    "            safe_input_fn=InputUtils.safe_input,\n",
    "            write_data_fn=DataExporter.write_with_format_selection,\n",
    "        )\n",
    "\n",
    "\n",
]

new_lines = lines[:start] + stub + lines[end:]
MISTHELPER.write_text("".join(new_lines), encoding="utf-8")

print(f"Done. Old lines: {len(lines)}, New lines: {len(new_lines)}")
print(f"Removed {len(lines) - len(new_lines)} lines")
