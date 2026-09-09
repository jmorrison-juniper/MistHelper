# Quickstart: searchOrgDevices

1. Run `python MistHelper.py --menu 249`.
2. Select or provide the organization ID when prompted.
3. Confirm that `data/OrgDevices.csv` contains the returned rows.
4. Run the command again and confirm that SQLite does not create duplicate
   rows for the same `id` and `mac`.

Run the focused tests:

```powershell
python -m pytest tests/unit/export/test_org_search_exporter.py
```

Run the quality gates:

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py src/export/org_search_exporter.py src/utils/operation_registry.py tests/unit/export/test_org_search_exporter.py
python -m black --check MistHelper.py src/export/org_search_exporter.py src/utils/operation_registry.py tests/unit/export/test_org_search_exporter.py
```
