# Contract: CLI Behavior

The feature is reachable as one numbered menu option in the safe-export range
(1-59) bound to `AddressAuditEngine.run`. All input via `InputUtils.safe_input()`.

---

## Entry

```
<N>: Audit site addresses from CSV -- compare Mist vs. customer data vs. web
```
- `<N>` = an unoccupied key in range 1-59 (assigned at implementation; startup
  collision check enforces uniqueness). Bound to `AddressAuditEngine.run`.
- Optional flag `--ui-geocode` enables Tier 3 (default OFF).

---

## Flow

### 1. CSV file selection (`data/`)
- Zero CSV/TSV files -> error message, return cleanly.
- Exactly one -> auto-selected (no prompt).
- Multiple -> indexed prompt:
```
Available CSV files in data/:
  [1] audit_sites_june.tsv
  [2] addresses_boca_raton.tsv
Select file number: _
```
- Invalid (non-integer/out-of-range) -> `Invalid selection. Please enter a number between 1 and {n}: ` (loop).

### 2. Business name (only if `.env BUSINESS_NAME` blank)
```
Enter business name for geocoding queries (e.g. "Starbucks"), or press Enter to skip: _
```
- Shown once/run; runtime-only; not logged at INFO. Enter -> raw-address query.

### 3. Processing
- Per row: serial match -> fuzzy fallback -> SNMP enrich -> tiered resolve -> classify.
- `tqdm` bar (suppressed when stdout is piped/non-interactive):
  `Geocoding sites: 45/200 [00:22, 2.1 site/s]`.
- Per-row failures log + classify `NO_RESULT`; audit continues (FR-013).

### 4. Comparison table (prettytable, 7 columns)
```
Site Name | Current Mist Address | CSV Address | SNMP Location | Suggested Address | Source | Issue Type
```
- SNMP Location + Suggested Address truncated to 40 chars in terminal (full in CSV).
- Every CSV row has exactly one of the 8 Issue Type values.

### 5. Post-table prompt
```
Audit complete. 4 sites processed: 0 ADDRESS_MATCH, 2 MISSING_SUITE, 1 CSV_BETTER, ...

[1] Save comparison as CSV to data/ for review
[q] Quit without saving
Choice: _
```
- `[1]` -> `Saved to data/address_audit_YYYYMMDD_HHMMSS.csv`.
- `[q]` -> `No file saved. Exiting address audit.`
- Invalid -> one-line error, re-prompt. No other options this release.

---

## Invariants (acceptance-mapped)

| Invariant | Spec ref |
|-----------|----------|
| 100% of CSV rows appear in output; none silently dropped | SC-002, FR-008 |
| Exactly one of 8 Issue Types per row | FR-008 |
| Zero Mist site writes in any path | FR-012, SC-004 |
| No dependency on a Mist geocoding endpoint (none exists) | FR-006 |
| Nominatim <= 1 req/sec; identifies User-Agent | FR-014 |
| Tier 3 OFF by default; selective; bounded; fail-soft | FR-006a |
| Cache hit -> zero external calls (DEBUG-visible) | FR-007, SC-003 |
| All prompts via `safe_input()`; no bare `input()` | CR-003 |
| Output CSV in `data/`, timestamped, full values, header row | FR-010 |
