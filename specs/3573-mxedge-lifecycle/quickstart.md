# Quickstart: Mist Edge Lifecycle Operation

## Local validation

Run the package gates before a commit.

```powershell
C:\Users\jmorrison\mh-fleet\3573-mxedge-lifecycle\.venv\Scripts\python.exe -m py_compile src\org\mxedge_lifecycle\__init__.py src\org\mxedge_lifecycle\client.py src\org\mxedge_lifecycle\models.py src\org\mxedge_lifecycle\operation.py
C:\Users\jmorrison\mh-fleet\3573-mxedge-lifecycle\.venv\Scripts\python.exe -m ruff check src\org\mxedge_lifecycle tests\unit\org\mxedge_lifecycle
C:\Users\jmorrison\mh-fleet\3573-mxedge-lifecycle\.venv\Scripts\python.exe -m black --check src\org\mxedge_lifecycle tests\unit\org\mxedge_lifecycle
C:\Users\jmorrison\mh-fleet\3573-mxedge-lifecycle\.venv\Scripts\python.exe -m mypy src\org\mxedge_lifecycle --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3573-mxedge-lifecycle\.venv\Scripts\python.exe -m pydocstyle src\org\mxedge_lifecycle
C:\Users\jmorrison\mh-fleet\3573-mxedge-lifecycle\.venv\Scripts\python.exe -m pytest tests\unit\org\mxedge_lifecycle -q --timeout=120
```

## Manual dry-run

After the integration pull request wires menu `293`, start MistHelper and choose the Mist Edge lifecycle operation. Select each sub-menu step with dry-run enabled. Confirm that `data/MxEdgeLifecycleLog.csv` has one row for each dry-run and that no Mist request is sent.

## Human review

Warning: Each live step changes Mist Edge state in the Mist cloud. A human must review the pull request before merge.
