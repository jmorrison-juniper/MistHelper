import re
import inspect
import sys
import os

OUT_FILE = os.path.join('analysis', 'mistapi_docstrings.txt')

try:
    with open('MistHelper.py', 'r', encoding='utf-8') as fh:
        content = fh.read()
except FileNotFoundError:
    print('MistHelper.py not found in cwd')
    sys.exit(2)

# Find candidate mistapi references
names = set(re.findall(r"(mistapi\.api\.v1\.[A-Za-z0-9_\.]+)", content))

lines = []
lines.append(f"Found {len(names)} unique mistapi references")

try:
    import mistapi
except Exception as e:
    lines.append(f"ERROR: could not import mistapi: {e}")
    with open(OUT_FILE, 'w', encoding='utf-8') as out:
        out.write('\n'.join(lines))
    print(f"WROTE {OUT_FILE}")
    sys.exit(0)

for name in sorted(names):
    lines.append('\n' + ('-' * 80))
    lines.append(name)
    parts = name.split('.')
    obj = mistapi
    found = True
    for p in parts[1:]:
        if hasattr(obj, p):
            obj = getattr(obj, p)
        else:
            found = False
            break
    if not found:
        lines.append('NOT FOUND in installed mistapi')
        continue
    # Now obj is found
    if inspect.ismodule(obj):
        lines.append('MODULE')
        doc = inspect.getdoc(obj)
        lines.append(doc or 'No docstring')
        continue
    if callable(obj):
        try:
            sig = str(inspect.signature(obj))
        except Exception as e:
            sig = f'signature not available: {e}'
        lines.append('Signature: ' + sig)
        doc = inspect.getdoc(obj)
        lines.append('Docstring:\n' + (doc or 'No docstring'))
        continue
    lines.append(f'Object type: {type(obj)}')
    doc = inspect.getdoc(obj)
    lines.append(doc or 'No docstring')

with open(OUT_FILE, 'w', encoding='utf-8') as out:
    out.write('\n'.join(lines))

print(f"WROTE {OUT_FILE}")
