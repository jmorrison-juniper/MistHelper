import tempfile
import importlib
import sys
from pathlib import Path

# Ensure repo parent on sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root.parent))

import MistHelper
import os

print('types before patch:')
print('MistHelper.mistapi:', type(MistHelper.mistapi))
print('MistHelper.mistapi.api:', type(getattr(MistHelper.mistapi,'api',None)))
print('MistHelper.mistapi.api.v1:', type(getattr(MistHelper.mistapi.api,'v1',None)))

# patch ConfigUtils
if hasattr(MistHelper, 'ConfigUtils'):
    try:
        MistHelper.ConfigUtils.get_cached_or_prompted_org_id = staticmethod(lambda: 'org1')
        print('patched ConfigUtils.get_cached_or_prompted_org_id')
    except Exception as e:
        print('failed patch ConfigUtils:', e)
else:
    print('No ConfigUtils on package')

# tmp dir
with tempfile.TemporaryDirectory() as td:
    os.chdir(td)
    print('cwd:', os.getcwd())
    # define stub
    def search_stub(session, org_id, device_type, limit, duration, search_after=None):
        return None

    try:
        orgs = MistHelper.mistapi.api.v1.orgs
        print('orgs type:', type(orgs))
        devices = getattr(orgs, 'devices', None)
        print('devices type:', type(devices))
        # attempt to set attribute
        setattr(devices, 'searchOrgDeviceEvents', search_stub)
        print('set attribute OK')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('Exception during patch:', e)

print('done')
