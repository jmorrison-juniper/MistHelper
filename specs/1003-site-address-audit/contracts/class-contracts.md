# Contract: Class Interfaces (`src/site/address_audit/`)

Internal contracts for the 10 classes. Each method lists signature, behavior, and
the mandated logging/error envelope. Every method MUST obey the Five-Item Rule
(<=5 params, <=25 lines, <=5 nested blocks), carry inline why-comments on every
executable line, and log `info` before / `debug` after the meaningful action.

---

## `CSVAddressIngester` (`csv_ingester.py`)

```python
def load(self, path: str) -> tuple[list[AddressRow], int]: ...
def sanitize_address(self, raw: str) -> str: ...
```

- `load(path)`: open tab-delimited UTF-8 file (no header); yield one `AddressRow`
  per valid row; return `(rows, parse_failure_count)`. Skip+count rows whose col 0
  is empty/non-numeric after strip. File-not-found -> controlled exception (logged,
  not a crash). `info` "Starting CSV ingestion from %s"; `debug` "Ingested %d rows, %d parse failures".
- `sanitize_address(raw)`: strip; replace `\n`/`\r\n`/`\r` with single space;
  collapse repeated spaces. Pure string transform.

---

## `SiteMatchingEngine` (`site_matcher.py`)

```python
def match_serial(self, serial: str) -> MatchedSite: ...
def match_fuzzy(self, address: str, sites: list[dict]) -> MatchedSite: ...
```

- `match_serial`: look up serial in Mist device inventory (via `mistapi`); resolve
  `device.site_id` -> site. Hit -> `MatchedSite(match_strategy="serial", confidence=1.0)`.
  Device found but `site_id` null -> `unmatched` (reason "device unassigned"). Miss ->
  delegate to `match_fuzzy`.
- `match_fuzzy`: `rapidfuzz.process.extractOne(query, choices, score_cutoff=THRESHOLD)`
  (default 85, `.env FUZZY_MATCH_THRESHOLD`). >=cutoff -> `match_strategy="fuzzy"`,
  `confidence=score/100`. Below -> `unmatched`. `rapidfuzz` absent -> `unmatched` +
  one startup WARNING (no per-call spam).
- Rate-limit/429 handling on inventory/site reads: back-off, retry up to 3, WARNING per retry.

---

## `SNMPLocationEnricher` (`snmp_enricher.py`)

```python
def enrich(self, site_id: str) -> str | None: ...
```

- Read `site["vars"]["snmp_location"]` and `snmp_config.location` (site settings).
  Both present -> return `snmp_config.location` (authoritative). One present ->
  return it. Neither -> `None`. MUST NOT raise on absence. `info` before fetch,
  `debug` after with which source won.

---

## `AddressResolver` (`address_resolver.py`)

```python
def resolve(self, candidates: ResolveCandidates) -> ResolverResult: ...
def _compare_internal(self, candidates) -> ResolverResult | None: ...
def _validate_nominatim(self, query_dict: dict) -> ResolverResult | None: ...
def _build_query_key(self, query: str) -> str: ...
def _from_cache(self, key: str) -> ResolverResult | None: ...
def _to_cache(self, key: str, result: ResolverResult) -> None: ...
def _ensure_cache_table(self, conn) -> None: ...
```

- `resolve(candidates)`: single config object (`ResolveCandidates` dataclass:
  `mist_address`, `csv_address`, `snmp_location`, `business_name`, `ui_geocode`) to
  honor the <=5-param rule. Order: build query key -> `_from_cache` (hit ->
  `source="cache"`, return) -> `_compare_internal` (Tier 1) -> `_validate_nominatim`
  (Tier 2) -> optional Tier 3 (delegated to `MistUIGeocoder` when `ui_geocode` and
  row warrants it) -> `_to_cache`. Any exception -> log + `ResolverResult(canonical_address=None)`
  (row classifies `NO_RESULT`) -- never abort the audit (FR-013).
- `_validate_nominatim`: compose existing `NominatimValidator.validate(mist, comp)`;
  enforce <=1 req/sec (validator's `RATE_LIMIT_DELAY` + a guarded `time.sleep`);
  reuse its User-Agent.
- `_build_query_key`: lowercase + collapse whitespace.
- Cache I/O: `_ensure_cache_table` (CREATE IF NOT EXISTS), `_from_cache` SELECT,
  `_to_cache` INSERT OR REPLACE. DB path resolves to `data/mist_data.db` (constitution).

---

## `MistUIGeocoder` (`ui_geocoder.py`) -- OPTIONAL Tier 3

```python
def geocode_via_ui(self, query: str) -> ResolverResult | None: ...
def _capture_autocomplete(self, page) -> list[str]: ...
```

- OFF unless `--ui-geocode`. Drives the live dashboard site-edit address field via
  Playwright, types `query`, reads top suggestion(s). Multiple suggestions ->
  `ambiguous=True`. Bounded by per-lookup timeout (default 20 s) and max lookups/run
  (default 50). Fail-soft: any selector/timeout/exception -> WARNING + return `None`
  (row -> `NO_RESULT`/`AMBIGUOUS`), never crash. See `ui-geocoder-contract.md`.

---

## `AddressAuditEngine` (`audit_engine.py`) -- orchestrator + menu entry

```python
def run(self, apisession, org_id) -> None: ...          # menu entry point
def _load_csv(self) -> tuple[list[AddressRow], int]: ...
def _match_sites(self, rows) -> list[MatchedSite]: ...
def _enrich_and_resolve(self, matched) -> list[ResolverResult | None]: ...
def _classify_and_render(self, ...) -> list[AuditResult]: ...
def _classify(self, mist_addr, csv_addr, snmp_loc, resolver_result) -> str: ...
def _addresses_agree(self, a, b) -> bool: ...
def _has_suite_discrepancy(self, base, candidate) -> bool: ...
def apply_corrections(self, *args, **kwargs) -> None: ...   # DEFERRED -> NotImplementedError, NOT registered
```

- `run`: the only method registered in the menu (`AddressAuditEngine.run`). Splits
  work across the private helpers to keep each <=25 lines. `tqdm` progress around
  the resolve loop (suppressed when stdout non-interactive). Zero Mist writes.
- `_classify`: returns exactly one of the 8 states; delegates to helpers to stay <=25 lines.
- `apply_corrections`: present but raises `NotImplementedError`; NOT wired to any menu key.

---

## `ComparisonTableRenderer` (`comparison_display.py`)

```python
def render(self, results: list[AuditResult]) -> str: ...
def prompt_post_table(self, results: list[AuditResult]) -> str: ...
```

- `render`: build prettytable, 7 columns (Site Name, Current Mist Address, CSV
  Address, SNMP Location, Suggested Address, Source, Issue Type); `max_width=40` on
  SNMP Location + Suggested Address; return the string (also printed).
- `prompt_post_table`: print one-line summary, then loop `safe_input()` offering
  `[1] Save CSV` / `[q] Quit`; invalid input re-prompts with a one-line error;
  returns the chosen action.

---

## `AddressAuditReporter` (`audit_reporter.py`)

```python
def save(self, results: list[AuditResult], output_dir: str) -> str: ...
```

- Write CSV to `output_dir` (default `data/`) with `os.makedirs(exist_ok=True)`;
  timestamped name `address_audit_YYYYMMDD_HHMMSS.csv`; header row matches the 7
  table columns; FULL (untruncated) values. Return the written path. Path built with
  `os.path.join`.

---

## `AddressCorrector` (`address_corrector.py`) -- STUB

```python
class AddressCorrector:
    def apply_correction(self, site_id: str, address: dict) -> None:
        raise NotImplementedError("Address write-back is not enabled in this release.")
```

- Inert. Not imported into the menu. Documents the deferred write-back surface (OQ-003).

---

## `models.py`

Defines `AddressRow`, `MatchedSite`, `ResolverResult`, `AuditResult`,
`AuditCounters`, and the `ResolveCandidates` config dataclass. No behavior.
