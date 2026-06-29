# Quickstart: Site Address Audit from CSV

Operator run guide + developer verification for the `1003-site-address-audit` feature.

---

## Operator: run an audit

1. **Place the CSV** in `data/` (tab-delimited, no header row, UTF-8). Columns:
   `serial  model  address  city  state  zip` (tab-separated). Example:
   ```
   2012233588	SSR130	5550 N Military Traill Unit 200	Boca Raton	FL	33431
   2012234081	SSR130	6000 Glades Rd Suite 1019A	Boca Raton	FL	33431
   ```
2. **(Optional) set a business name** in `.env`:
   ```
   BUSINESS_NAME=Starbucks
   ```
   If blank, the tool prompts once at run start (Enter to skip).
3. **Launch MistHelper** and choose the menu entry:
   `Audit site addresses from CSV -- compare Mist vs. customer data vs. web`
4. **Select the CSV** (auto-selected if only one in `data/`).
5. **Review the table**: 7 columns; each row classified into one of 8 states.
6. **Save or quit**: `[1]` writes `data/address_audit_YYYYMMDD_HHMMSS.csv` (full
   values); `[q]` exits without writing.

### Optional Tier 3 (Google-quality suite resolution)

Run with `--ui-geocode` to enable the dashboard-autocomplete tier. A browser opens;
log in to the Mist dashboard interactively, then press Enter to continue. Tier 3 is
selective (e.g. `AMBIGUOUS` rows), bounded (20 s/lookup, 50 lookups/run), and never
crashes the audit if the UI changes.

---

## What each classification means

| State | Meaning | Action |
|-------|---------|--------|
| `ADDRESS_MATCH` | Mist agrees with resolved result | none |
| `MISSING_SUITE` | CSV/SNMP/UI has suite; Mist lacks it | review |
| `WRONG_STREET` | Street differs beyond suite | review |
| `CSV_BETTER` | CSV/SNMP more specific than Mist | review |
| `MIST_BETTER` | Mist already most specific | none |
| `AMBIGUOUS` | Multiple plausible results (mall) | manual |
| `NO_RESULT` | Nothing resolved | manual |
| `UNMATCHED` | No site paired by serial/fuzzy | follow-up |

---

## Developer: verify the feature

### Quality gates (must pass)
```powershell
python -m py_compile MistHelper.py
ruff check src/site/address_audit/
black --check src/site/address_audit/
```

### Unit tests
Local venv workaround (plugin autoload only):
```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; & ".venv\Scripts\python.exe" -m pytest tests/unit/site/address_audit/ -o addopts="" -q
```
Covers: CSV ingest/sanitize, serial+fuzzy matching, SNMP enrichment, tiered
resolver + cache, 8-state classification, table rendering/truncation, CSV save.

### Smoke checklist (maps to acceptance criteria)
- [ ] Drop a multi-row TSV in `data/`; menu prompts for selection; table renders.
- [ ] A non-existent serial (`9999999999`) shows `UNMATCHED`; no geocoding attempted.
- [ ] A typo'd-serial row with a good address fuzzy-matches (`Source: Fuzzy`).
- [ ] SNMP-bearing site shows the SNMP Location column populated.
- [ ] Second run on the same CSV: DEBUG shows cache hits; zero new Nominatim calls.
- [ ] `[1]` writes a timestamped CSV with a header + one row per audited site (full values).
- [ ] No Mist site record is modified (read-only).
- [ ] `rapidfuzz` uninstalled -> audit still completes (fuzzy rows -> `UNMATCHED`, one WARNING).

---

## Boundaries (do NOT cross)

- No Mist geocoding REST call (the endpoint does not exist).
- No writes to Mist site records (`AddressCorrector` is an inert stub).
- No new required dependencies; `rapidfuzz`/`scourgify` are optional with fallbacks.
- New code only under `src/site/address_audit/`; only 2 additive lines in `MistHelper.py`.
- ASCII-only logs; `safe_input()` everywhere; every executable line commented;
  info-before/debug-after every action.
