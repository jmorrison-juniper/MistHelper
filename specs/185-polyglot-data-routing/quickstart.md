# Quickstart: Polyglot Data Routing Refactor

**Feature**: 185-polyglot-data-routing | **Date**: 2026-04-22

## Prerequisites

1. **Infrastructure running** (via `podman compose up -d arangodb redis-stack`)
2. **Environment variables set**:
   ```powershell
   $env:ARANGO_HOST = "http://localhost:8529"
   $env:ARANGO_ROOT_PASSWORD = "changeme"
   $env:REDIS_HOST = "localhost"
   $env:REDIS_PORT = "6379"
   $env:REDIS_PASSWORD = "changeme"
   ```
3. **Python venv activated**: `.venv\Scripts\Activate.ps1`

## Verification Commands

### After each implementation task, verify:

```powershell
# Quality gates (must all pass)
python -m py_compile MistHelper.py
python -m py_compile src/db/router.py
python -m py_compile src/db/redis_writer.py
python -m ruff check MistHelper.py src/db/
python -m black --check MistHelper.py src/db/

# Smoke test (menu 11 = Org Sites → natural_pk → ArangoDB raw)
python MistHelper.py --menu 11

# Verify ArangoDB has nested documents
$auth = "Basic $([Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes('root:changeme')))"
Invoke-RestMethod -Uri "http://localhost:8529/_db/misthelper/_api/cursor" `
  -Method Post -Headers @{Authorization=$auth} `
  -ContentType "application/json" `
  -Body '{"query":"FOR doc IN listOrgSites LIMIT 1 RETURN doc"}'

# Verify Redis JSON (after composite_pk task)
redis-cli -h localhost -p 6379 -a changeme JSON.GET "searchOrgDeviceEvents:example-key" $
```

## File Change Map

| File | Changes | Task |
|---|---|---|
| `MistHelper.py` | Add `raw_data` param to `write_with_format_selection`, update callers, reclassify strategies | T1, T4 |
| `src/db/router.py` | Update routing constants, add dual-write dispatch, add `timeseries_pk` routing | T2, T3 |
| `src/db/redis_writer.py` | Add `RedisJSONWriter` class, keep `RedisTimeSeriesWriter` unchanged | T2 |
| `src/db/__init__.py` | Export `RedisJSONWriter` | T2 |

## Task Execution Order

```
T1 (raw_data pipeline) → T2 (RedisJSONWriter + dual-write) → T3 (timeseries_pk routing) → T4 (endpoint reclassification)
```

Each task is independently testable. T1 must complete before T2-T4 since it provides the raw data path.
