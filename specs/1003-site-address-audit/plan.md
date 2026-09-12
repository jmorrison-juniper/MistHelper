# Implementation Plan: Site Address Audit from CSV

**Branch**: `1003-site-address-audit` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/1003-site-address-audit/spec.md`

## Summary

Deliver a **read-only** CLI menu option (safe export range 1-59) that reconciles a
customer-provided tab-delimited CSV (serial -> address) against Mist Cloud site
records. The pipeline: ingest & sanitize CSV -> match each row to a Mist site by
device **serial number** (golden key) with a rapidfuzz >=85% address fallback ->
enrich with SNMP location -> resolve/validate the address through three **free**
tiers (Tier 1 internal CSV/SNMP/Mist comparison, Tier 2 Nominatim street
validation, optional Tier 3 Playwright "hijack" of the live Mist dashboard
autocomplete) -> classify into one of eight states -> render a prettytable
(old vs. suggested) -> offer to save a timestamped CSV. **Zero writes** to Mist
in this release; write-back lives in an inert `AddressCorrector` stub.

Technical approach is constrained by a verified fact: **Mist exposes no geocoding
REST endpoint** (`/api/v1/utils/geocoding` is absent from the `mistapi` SDK and
both OpenAPI specs). All resolution is therefore internal-first, then free
external validators, never a paid or non-existent API.

## Technical Context

**Language/Version**: Python 3.13+ (constitution-mandated minimum)
**Primary Dependencies**: `mistapi` 0.59+ (sole Mist API interface), `requests`,
`prettytable`, `python-dotenv`, `tqdm` (all already in `requirements.txt`);
`playwright` (already a repo dev/e2e dependency) for the optional Tier 3.
**Optional Dependencies (graceful fallback via `GlobalImportManager`)**:
`rapidfuzz` (fuzzy site match), `usaddress-scourgify` (address normalization).
**Storage**: SQLite `geocoding_cache` table inside the existing
`data/mist_data.db` (additive, `CREATE TABLE IF NOT EXISTS` + `INSERT OR REPLACE`).
Output CSV written to `data/`.
**Testing**: pytest unit tests under `tests/unit/site/address_audit/`; reuse the
existing Playwright e2e infra (`tests/e2e/`, `gunicorn_server` fixture) only where
a Tier 3 UI test is warranted. Local run workaround (corrupted venv):
`$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; & ".venv\Scripts\python.exe" -m pytest <files> -o addopts="" -q`
**Target Platform**: Windows 11 local dev + Linux container (Podman). ASCII-only
logs for cross-platform safety.
**Project Type**: Single-project CLI (MistHelper monolith + `src/` subpackages).
**Performance Goals**: 500-site audit < 15 min cold cache; < 30 s for 200 rows on
a warm cache (SC-001, SC-003). Tier 1 in-memory (instant); Tier 2 Nominatim
<= 1 req/sec; Tier 3 selective only (per-lookup timeout 20 s, max 50 lookups/run).
**Constraints**: Read-only (zero Mist writes); no new required dependencies; no
paid APIs; no Mist geocoding endpoint; ASCII-only logging; 5-Item Rule on every
method; inline comment on every executable line; `logging.info`/`debug`
before/after every meaningful action; all input via `InputUtils.safe_input()`;
class-based only; paths via `os.path.join`/`pathlib`.
**Scale/Scope**: Typical < 2000 CSV rows; peak memory negligible. New code is one
subpackage (`src/site/address_audit/`, 10 classes) + 2 additive lines in
`MistHelper.py`.

## Constitution Check

*GATE: evaluated against MistHelper Constitution v1.4.0. Re-checked after Phase 1.*

| # | Principle | Status | Evidence in this plan |
|---|-----------|--------|-----------------------|
| I | Five-Item Rule (structure + method limits) | PARTIAL | Method limits (<=5 params / 25 lines / 5 blocks) enforced in every contract; explicit split points captured in research.md. **Directory-level violation**: the subpackage holds 10 module files (> 5). Justified in Complexity Tracking; the flat one-class-per-module layout is a settled spec decision. |
| II | Class-Based Architecture (no wrappers) | PASS | Every module defines exactly one semantically named class; no standalone functions; full-word identifiers; no AI marker text. |
| III | Safety-First | PASS | Read-only feature; all prompts via `safe_input(..., context=...)`; no destructive ops; `apisession` token never logged. |
| IV | Full Deployment Pipeline | DEFERRED | Applies at implementation/commit time (tasks phase), not at planning. `py_compile` / `ruff` / `black` are wired as quality gates. |
| V | Observability & Logging | PASS | ASCII-only `%s`-style logs; info-before / debug-after pattern mandated per method in contracts. |
| VI | Inline Comments (NON-NEGOTIABLE) | PASS | Every executable line carries a why-comment; enforced as an acceptance gate (CR-001). |
| VII | Action Logging (NON-NEGOTIABLE) | PASS | info before + debug after every API/file/DB/transform/prompt; enforced (CR-002). |

**Technology constraints check**: Python 3.13+ OK; `mistapi`-only for Mist reads
OK (inventory + site reads; no direct Mist HTTP); paths via `os.path.join` OK;
data outputs to `data/` OK; no new required deps OK.

**Gate result**: PASS with one justified structural violation (see Complexity
Tracking). No blocking violations.

## Project Structure

### Documentation (this feature)

```text
specs/1003-site-address-audit/
|-- spec.md              # Approved feature spec (input)
|-- plan.md              # This file
|-- research.md          # Phase 0 output: decisions, OQ resolutions, tier design
|-- data-model.md        # Phase 1 output: dataclasses + geocoding_cache schema
|-- quickstart.md        # Phase 1 output: operator run + dev verification guide
|-- contracts/           # Phase 1 output: class + CLI + cache + UI-selector contracts
|   |-- cli-contract.md
|   |-- class-contracts.md
|   |-- geocoding-cache-contract.md
|   `-- ui-geocoder-contract.md
`-- tasks.md             # Phase 2 (created by /speckit.tasks, NOT here)
```

### Source Code (repository root)

```text
src/site/address_audit/          # NEW subpackage (all new production code here)
|-- __init__.py                  # Exports AddressAuditEngine for menu registration
|-- models.py                    # AddressRow, MatchedSite, ResolverResult, AuditResult, AuditCounters
|-- csv_ingester.py              # CSVAddressIngester  -- parse & sanitize tab-delimited input
|-- site_matcher.py              # SiteMatchingEngine  -- serial -> site_id; rapidfuzz fallback
|-- snmp_enricher.py             # SNMPLocationEnricher -- snmp_location + snmp_config.location
|-- address_resolver.py          # AddressResolver     -- Tier 1 internal + Tier 2 Nominatim + cache
|-- ui_geocoder.py               # MistUIGeocoder      -- optional Tier 3 Playwright dashboard hijack
|-- audit_engine.py              # AddressAuditEngine  -- orchestrator + menu entry point
|-- comparison_display.py        # ComparisonTableRenderer -- prettytable build/print + post-table prompt
|-- audit_reporter.py            # AddressAuditReporter -- timestamped CSV save to data/
`-- address_corrector.py         # AddressCorrector    -- STUB (NotImplementedError), NOT registered

MistHelper.py                    # +2 additive lines only: import AddressAuditEngine; one menu dict entry (1-59)

tests/unit/site/address_audit/   # NEW unit tests
|-- test_csv_ingester.py
|-- test_site_matcher.py
|-- test_snmp_enricher.py
|-- test_address_resolver.py
|-- test_audit_engine.py
|-- test_comparison_display.py
`-- test_audit_reporter.py

tests/e2e/                       # REUSE existing infra for optional Tier 3 UI test only
```

**Reused existing assets (do NOT reinvent)**:
- `src/utils/address_utils.py` -> `NominatimValidator` (Tier 2 street validation),
  `AddressUtils` (normalization/parse), `AddressValidationConfig`.
- `src/utils/input_utils.py` -> `InputUtils.safe_input()`.
- `MistHelper.py` -> `GlobalImportManager` optional-import pattern for `rapidfuzz`
  and `scourgify`.
- `data/mist_data.db` (additive table only).

**Structure Decision**: Single-project CLI. All new production code is isolated in
the `src/site/address_audit/` subpackage with one class per module. The only edits
outside the subpackage are two additive lines in `MistHelper.py` (an import and a
menu dict entry in range 1-59). No existing file logic is modified.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Subpackage holds 10 module files (> 5, breaks Five-Item Rule at the directory level) | Spec mandates strict one-class-per-module isolation for 10 cohesive single-responsibility classes (ingest, match, enrich, resolve, UI-geocode, orchestrate, render, report, models, corrector-stub) | Collapsing classes into fewer modules would breach the stronger "one class per module" convention and produce 25+ line god-modules that violate the method-level Five-Item Rule. Adding an extra nesting layer (e.g. `ingest/`, `resolve/`) to get <=5 per directory adds import indirection and ceremony without reducing cognitive load for the junior-NOC audience. The flat, well-named, read-only subpackage is the lowest-complexity option that satisfies the method-level rules and the explicit architecture in the spec. |
| Three-tier resolver (internal + Nominatim + optional Playwright UI) inside one `AddressResolver` + one `MistUIGeocoder` | Mist has no geocoding endpoint; free Google-quality suite data only reachable by driving the live dashboard | A single-tier design cannot recover retail suite numbers (Nominatim lacks them) and a paid API is prohibited. Tiering is the minimum design that meets the requirement with zero new paid dependencies. Complexity is bounded: Tier 3 is OFF by default, gated, selective, and fail-soft. |

## Open Questions Carried Into Tasks (non-blocking)

- **OQ-001 (Tier 3 auth)** -> RESOLVED in research.md: v1 uses interactive operator
  login in the Playwright-launched browser at run start (option a). No new `.env`
  secrets. Scripted login (option b) is a documented later opt-in.
- **OQ-002 (UI selector stability)** -> Captured in `contracts/ui-geocoder-contract.md`
  with a documented re-capture procedure; tier MUST fail soft to `NO_RESULT`/`AMBIGUOUS`.
- **OQ-003 (write-back endpoint)** -> Out of scope for v1; `AddressCorrector` stub only.
- **PLAN-001 (menu number)**: The developer MUST assign an unoccupied key in range
  1-59 at implementation time and confirm no dict-key collision at startup. A flat
  scan of all quoted-integer keys in `MistHelper.py` shows dense usage; the impl
  task MUST verify the *safe-export* menu dict specifically and pick a free slot
  (or coordinate per the hot-file rule). Recorded as a tasks-phase checkpoint.
