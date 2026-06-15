import importlib, sys, pprint
from pathlib import Path

print('Python executable:', sys.executable)

# Ensure parent of package dir is on sys.path so 'import MistHelper' works
repo_root = Path(__file__).resolve().parent.parent
parent_of_repo = repo_root.parent
sys.path.insert(0, str(parent_of_repo))

# Import package by name
pkg = importlib.import_module('MistHelper')
print('pkg name =', pkg.__name__)
print('pkg object =', pkg)
print('pkg dir sample =', [n for n in dir(pkg) if not n.startswith('_')])
print('pkg has ConfigUtils?', hasattr(pkg, 'ConfigUtils'))
print('pkg.ConfigUtils repr:', getattr(pkg, 'ConfigUtils', None))

heavy = None
try:
    heavy = importlib.import_module('MistHelper.MistHelper')
    print('heavy name =', heavy.__name__)
    print('heavy has ConfigUtils?', hasattr(heavy, 'ConfigUtils'))
    cfg = getattr(heavy, 'ConfigUtils', '<MISSING>')
    print('heavy.ConfigUtils repr:', cfg)
    print('heavy.ConfigUtils type:', type(cfg))
    # Inspect a handful of commonly-expected legacy symbols and their types/values
    names_to_check = [
        'ConfigUtils',
        'DataExporter',
        'SiteExportUtils',
        'SiteClientExporter',
        'OrgAlarmEventExporter',
        'get_cached_or_prompted_org_id',
        'save_data_to_output',
    ]
    for nm in names_to_check:
        val = getattr(heavy, nm, '<MISSING>')
        print(f"heavy.{nm}: present={val is not '<MISSING>'}, type={type(val)}, repr={repr(val)[:200]}")
    sample = [n for n in dir(heavy) if 'Config' in n or 'DataExporter' in n or 'SiteExport' in n or 'SiteClient' in n]
    print('heavy dir sample =', sample)
except Exception as e:
    print('heavy import failed:', repr(e))

print('sys.modules keys starting with MistHelper:', [k for k in sys.modules if k.startswith('MistHelper')][:200])
