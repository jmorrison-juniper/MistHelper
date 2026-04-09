#!/usr/bin/env python3
"""
Generate a wiki-ready Markdown file listing menu IDs, descriptions, safety, and handler names.
"""
import re, os
repo_root = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(repo_root, 'MistHelper.py')
out_dir = os.path.join(repo_root, 'documentation', 'wiki')
out_path = os.path.join(out_dir, 'Menu-Reference.md')
with open(src_path, 'r', encoding='utf-8') as fh:
    src = fh.read()
start = src.find('menu_actions = {')
if start == -1:
    raise SystemExit('menu_actions not found')
# find matching closing brace by simple counter
idx = start
brace = 0
end = None
for i, ch in enumerate(src[start:], start):
    if ch == '{':
        brace += 1
    elif ch == '}':
        brace -= 1
        if brace == 0:
            end = i
            break
if end is None:
    raise SystemExit('Could not find end of menu_actions')
block = src[start:end+1]
# regex to capture key, callable text (first arg), and description string (first string literal in tuple)
pattern = re.compile(r'"(?P<key>[^"]+)"\s*:\s*\(\s*(?P<call>[^,\n]+?)\s*,\s*"(?P<desc>(?:[^"\\]|\\.)*?)"', re.MULTILINE|re.DOTALL)
matches = list(pattern.finditer(block))
rows = []
for m in matches:
    key = m.group('key').strip()
    call = m.group('call').strip().replace('\n', ' ').replace('  ', ' ')
    desc = m.group('desc').strip().replace('\n', ' ').replace('  ', ' ')
    desc_clean = re.sub(r'\s+', ' ', desc).strip()
    call_clean = re.sub(r'\s+', ' ', call).strip()
    udesc = desc_clean.upper()
    if 'DESTRUCTIVE' in udesc or 'DESTRUCTIVE' in call_clean.upper():
        safety = 'Destructive'
    elif 'INTERACTIVE' in udesc or 'INTERACTIVE' in call_clean.upper() or 'STREAM' in udesc or 'STREAMING' in udesc:
        safety = 'Interactive'
    else:
        safety = 'Safe'
    rows.append((key, desc_clean, safety, call_clean))
# sort by numeric key when possible
def sort_key(r):
    k = r[0]
    try:
        return (int(k), k)
    except:
        try:
            return (float(k.replace('a', '.1')), k)
        except:
            return (9999, k)
rows = sorted(rows, key=sort_key)
# write markdown
os.makedirs(out_dir, exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('# Menu Reference (Auto-generated)\n\n')
    f.write('This page is generated from the canonical menu_actions mapping in MistHelper.py.\n\n')
    f.write('| Menu ID | Short description | Safety | Callable/Handler |\n')
    f.write('|---:|---|---|---|\n')
    for key, desc, safety, call in rows:
        desc2 = desc.replace('|', '\\|')
        call2 = call.replace('|', '\\|')
        f.write(f'| {key} | {desc2} | {safety} | `{call2}` |\n')
print('WROTE', out_path)
