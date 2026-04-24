# Output & Data Model

## CSV

- Written under `data/` automatically (code ensures directory exists)
- Multiline fields sanitized (line breaks replaced with `\n`)
- Nested structures flattened: dotted/hierarchical keys converted with underscores + index suffixes

## SQLite

Set `--output-format sqlite` or `OUTPUT_FORMAT=sqlite` environment variable.

Adaptive strategy (see `ENDPOINT_PRIMARY_KEY_STRATEGIES` mapping):

1. **Natural Primary Key**: Entities with stable `id` (sites, devices, templates)
2. **Composite Primary Key**: Event/time-series metrics (e.g., `device_id + timestamp`)
3. **Auto-Increment w/ Unique Constraint**: Aggregated license or summary endpoints lacking stable identity

Upserts use `INSERT OR REPLACE` when natural/composite keys are in effect. Index selection is dynamic per endpoint (org/site/device/time fields prioritized). Metadata fields `misthelper_created_time` & `misthelper_updated_time` are appended for auditing.

### Inspecting the Database

```bash
sqlite3 data/mist_data.db
.tables
.schema getOrgInventory
SELECT COUNT(*) FROM listOrgSites;
```

## Working with Output Files

MistHelper creates organized output in the `data/` directory:

- **CSV files:** Easy to open in Excel or import elsewhere
- **SQLite database:** Use `data/mist_data.db` for complex queries
- **ArangoDB:** Document storage for config entities (optional polyglot backend)
- **Redis Stack:** Time-series metrics and JSON event cache (optional polyglot backend)
- **Weekly inventory:** Time-series data in `CombinedInventory_ByWeek/`
