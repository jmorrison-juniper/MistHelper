import importlib
import pprint
import sys
from pathlib import Path

print('Python executable:', sys.executable)

# Ensure repository parent is on sys.path so 'import MistHelper' resolves to local package
repo_root = Path(__file__).resolve().parent.parent
parent_of_repo = repo_root.parent
sys.path.insert(0, str(parent_of_repo))

import MistHelper

def show(obj, name):
    try:
        t = type(obj)
    except Exception:
        t = '<unreadable>'
    try:
        r = repr(obj)
    except Exception:
        r = '<unreprable>'
    print(f"{name}: type={t}, repr={r[:400]}")

show(MistHelper.mistapi, 'MistHelper.mistapi')
try:
    show(MistHelper.mistapi.api, 'MistHelper.mistapi.api')
except Exception as e:
    print('accessing MistHelper.mistapi.api raised', type(e), e)

try:
    v1 = MistHelper.mistapi.api.v1
    show(v1, 'MistHelper.mistapi.api.v1')
    try:
        show(getattr(v1, 'orgs', None), 'MistHelper.mistapi.api.v1.orgs')
    except Exception as e:
        print('accessing v1.orgs raised', type(e), e)
except Exception as e:
    print('accessing v1 raised', type(e), e)

print('\nsys.modules keys for mistapi*')
import sys
for k in sorted([k for k in sys.modules.keys() if k.startswith('mistapi')]):
    print(' -', k)
