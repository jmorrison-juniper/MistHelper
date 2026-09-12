"""Build menu-to-API-call mapping for the audit."""

import json
import re

with open("MistHelper.py", encoding="utf-8") as f:
    lines = f.readlines()

# Extract menu entries
menu_map = {}
in_menu = False
for _i, line in enumerate(lines):
    if "menu_actions = {" in line:
        in_menu = True
        continue
    if in_menu:
        if line.strip() == "}":
            break
        m = re.match(r'\s*"(\d+)"\s*:\s*\((.+?),\s*"(.+?)"', line)
        if m:
            menu_num = int(m.group(1))
            handler = m.group(2).strip()
            desc = m.group(3).strip()
            menu_map[menu_num] = {"handler": handler, "description": desc}

print(f"Menu entries parsed: {len(menu_map)}")

# Build function ranges to find containing function for each line
func_ranges = []
current_class = None
for i, line in enumerate(lines):
    cls_match = re.match(r"^class\s+(\w+)", line)
    if cls_match:
        current_class = cls_match.group(1)
    fn_match = re.match(r"^(\s*)def\s+(\w+)", line)
    if fn_match:
        indent = len(fn_match.group(1))
        func_name = fn_match.group(2)
        if indent > 0 and current_class:
            full_name = f"{current_class}.{func_name}"
        else:
            full_name = func_name
            if indent == 0:
                current_class = None
        func_ranges.append({"name": full_name, "start": i + 1, "class": current_class})

# Load catalog
with open("specs/010-endpoint-usage-audit/catalog_matched.json", encoding="utf-8") as f:
    catalog = json.load(f)

# For each MistHelper call site, find containing function
for cs in catalog:
    if cs["source_file"] != "MistHelper.py":
        continue
    line_num = cs["line"]
    containing = None
    for fr in func_ranges:
        if fr["start"] <= line_num:
            containing = fr["name"]
    cs["containing_function"] = containing

# Build handler -> class lookup from menu_map
# Extract a mapping from menu handler class names to menu numbers
handler_to_menus: dict[str, list[int]] = {}
for mn, info in menu_map.items():
    handler = info["handler"]
    # Clean up lambda wrappers
    handler_clean = handler.replace("lambda:", "").replace("lambda ", "")
    # Extract class.method pattern
    parts = re.findall(r"(\w+)\.(\w+)", handler_clean)
    for cls, method in parts:
        if cls in ("sys", "fast", "dry_run", "address_check", "debug", "skip_ssl_verify"):
            continue
        key = f"{cls}.{method}"
        if key not in handler_to_menus:
            handler_to_menus[key] = []
        handler_to_menus[key].append(mn)

# Now map each call site to menu operations
for cs in catalog:
    if cs["source_file"] != "MistHelper.py":
        cs["menu_operations"] = []
        continue
    containing = cs.get("containing_function", "")
    matched_menus = []
    if containing:
        # Check if this function's class.method is directly in handler_to_menus
        if containing in handler_to_menus:
            matched_menus = handler_to_menus[containing]
        else:
            # Check if class matches any handler class
            cls_name = containing.split(".")[0] if "." in containing else containing
            for key, menus in handler_to_menus.items():
                if key.startswith(cls_name + "."):
                    matched_menus.extend(menus)
            matched_menus = sorted(set(matched_menus))
    cs["menu_operations"] = matched_menus

# Save
with open("specs/010-endpoint-usage-audit/catalog_matched.json", "w", encoding="utf-8") as f:
    json.dump(catalog, f, indent=2)

# Save menu map
with open("specs/010-endpoint-usage-audit/menu_map.json", "w", encoding="utf-8") as f:
    json.dump({str(k): v for k, v in sorted(menu_map.items())}, f, indent=2)

# Stats
with_menus = sum(1 for cs in catalog if cs.get("menu_operations"))
print(f"Call sites with menu mapping: {with_menus} / {len(catalog)}")
print("Saved catalog_matched.json and menu_map.json")

# Show unmapped call sites
unmapped = [cs for cs in catalog if not cs.get("menu_operations") and cs["source_file"] == "MistHelper.py"]
unmapped_funcs = set(cs.get("containing_function", "unknown") for cs in unmapped)
print(f"\nUnmapped containing functions ({len(unmapped_funcs)} unique, {len(unmapped)} call sites):")
for fn in sorted(unmapped_funcs)[:15]:
    count = sum(1 for cs in unmapped if cs.get("containing_function") == fn)
    print(f"  {fn} ({count})")
