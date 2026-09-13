# Quickstart: searchSiteDiscoveredSwitches

Run these commands from the repository root.

```powershell
python -m pytest -q tests/unit/export/test_site_search_exporter.py
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy src/ --config-file pyproject.toml
```

The focused test uses mocks. It does not send a request to Mist Cloud.

To run menu 228 against a real site, provide the normal Mist credentials and
select the site when prompted:

```powershell
python MistHelper.py --menu 228
```
