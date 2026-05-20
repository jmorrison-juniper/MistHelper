"""One-off script: diff pk_strategy_suggestions.py vs ENDPOINT_PRIMARY_KEY_STRATEGIES."""
import re

with open("MistHelper.py", "r", encoding="utf-8") as f:
    src = f.read()

start = src.index("ENDPOINT_PRIMARY_KEY_STRATEGIES = {")
depth, pos = 0, start + len("ENDPOINT_PRIMARY_KEY_STRATEGIES = {") - 1
while pos < len(src):
    if src[pos] == "{":
        depth += 1
    elif src[pos] == "}":
        depth -= 1
        if depth == 0:
            break
    pos += 1
existing_keys = set(re.findall(r'"([\w]+)":', src[start : pos + 1]))

with open("scripts/pk_strategy_suggestions.py", "r", encoding="utf-8") as f:
    src2 = f.read()

suggested = {}
for m in re.finditer(r'"([\w]+)":\s*\{[^}]*?"type":\s*"([^"]+)"', src2, re.DOTALL):
    suggested[m.group(1)] = m.group(2)

new_entries = {k: v for k, v in suggested.items() if k not in existing_keys}
print(f"Existing keys: {len(existing_keys)}")
print(f"Suggested keys: {len(suggested)}")
print(f"NET NEW: {len(new_entries)}")
print()
for strat in ["natural_pk", "composite_pk", "timeseries_pk", "auto_increment_with_unique"]:
    group = sorted([k for k, v in new_entries.items() if v == strat])
    if group:
        print(f"  {strat} ({len(group)}):")
        for k in group:
            print(f"    {k}")
