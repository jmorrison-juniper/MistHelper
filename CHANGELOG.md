# Changelog

All notable changes to MistHelper are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Version format: `YY.MM.DD.HH.MM` (UTC timestamp).

## [Unreleased]

### Menu 198: Search Site WAN Usages (spec 901 / issue #1409)

- **New menu 198 (Added)**: `SiteWanUsageExporter.wan_usages()` wraps the previously
  unreachable Mist API `searchSiteWanUsage` operation
  (`GET /api/v1/sites/{site_id}/wan_usages/search`). Operator picks a site (shared
  `SiteDeviceExporter._resolve_site_for_stats` helper), the exporter pages all rows via
  `mistapi.get_all`, flattens + escapes them with `DataProcessingUtils`, then persists
  through `DataExporter.write_with_format_selection` so CSV / SQLite / ArangoDB backends
  all work. Empty responses surface a friendly "no WAN usage data" notice instead of
  failing. `ENDPOINT_PRIMARY_KEY_STRATEGIES` already defined a composite PK on
  `(mac, port_id, peer_mac)` for this operationId, and `arango_writer` already routed it
  to the `wan_usage` collection -- no schema changes required.

### Menu 197: Client Packet Capture Downloader (issue #421)

- **New menu 197 (Added)**: `ClientPacketCaptureDownloader` guides the operator through
  a four-step interactive flow — pick a site, pick a wireless client (by index or MAC
  in any punctuation), pick a VLAN grouping, then stream every completed PCAP for that
  VLAN into `data/packet_captures/<mac>/vlan_<id>/`. Uses
  `mistapi.api.v1.sites.clients.searchSiteWirelessClients` (7-day window, paginated via
  `mistapi.get_all`) and `mistapi.api.v1.sites.pcaps.listSitePacketCaptures`
  (client-MAC-filtered). Captures still in progress (no `pcap_url`) are skipped.
  Downloads stream in 8 KiB chunks with a 300 s timeout. Menu slots 195 and 196 were
  already occupied, so this feature registers as slot 197.

### Safe, Repeatable `--test` Clean Run (feature 1020)

- **Fail-closed `OperationRegistry` default (Fixed, Security)**: `OperationRegistry.get()`
  no longer defaults unregistered menu options to `safe` (a fail-**open** default that
  would let a credentialed `--test`/`--testinteractive` run silently invoke any
  unclassified option, including destructive menu 194). Unknown options now resolve to a
  new fail-**closed** `unregistered` category (a `SKIP_CATEGORIES` member), so they are
  ineligible for both test modes and surface a loud, actionable skip reason. All 60
  previously-unregistered `menu_actions` keys received explicit classifications
  (read-only exports -> `safe`; heavy sweeps 14/18 -> `resource_intensive`; ticket
  writes 189/190/191 and clone 194 -> `destructive`; ticket view 192 -> `interactive`),
  and three pre-existing destructive entries (175/176/186) gained the required
  `DESTRUCTIVE` marker.
- **Exhaustive menu/registry coverage guardrail (Added)**: replaced the brittle 11-key
  `WAVE1_ENTRY_ROUTING_BASELINE` sample as the sole coverage mechanism with
  `tests/guardrails/test_operation_registry_menu_coverage.py`, which asserts exact
  key-parity between `menu_actions` and the new
  `OperationRegistry.registered_options()` and fails CI the instant they diverge.
- **Isolated-venv install guard (Added, Security)**: `DependencyCheckOrchestrator` now
  refuses to auto-install/upgrade dependencies into a non-isolated (system) Python
  interpreter by default, distinguishing "no `.venv`" from "broken `.venv` launcher" in
  the diagnostic text. Override with `MISTHELPER_ALLOW_SYSTEM_PYTHON_INSTALL=true`; the
  existing `DISABLE_AUTO_INSTALL` gate is unchanged.
- **Secret-safe credential/config preflight (Added)**: `_establish_mist_session()` now
  runs a host/token preflight (all modes) and `ConfigUtils` a non-interactive org-id
  guard (`--test`/`--testinteractive`) that fail closed with redacted, actionable
  messages referencing `deploy/.env.example` **before** any `mistapi`/`requests` call —
  preventing malformed-URL requests on a blank host and never leaking token contents.
- **`deploy/.env.example` clarification (Docs)**: documented that the non-interactive
  org-id path reads `org_id`/`ORG_ID` (not `MIST_ORG_ID`).
- **Gateway test runtime wiring (Fixed)**: menus 33 and 34 now configure the
  gateway runtime dependencies before either gateway inventory lookup or
  site-result service delegation. This fixes the credentialed menu-33
  systematic-test failure caused by an uninitialized `APICoreFetchUtils`.
- **Windows type-check compatibility (Fixed)**: the Unix-only container user
  detector now explicitly skips non-POSIX platforms and dynamically resolves
  Unix account APIs after that guard, preserving container behavior while
  allowing the configured `mypy src` check to pass on Windows.
- **Formatting baseline (Fixed)**: applied the repository's Black formatting to
  `MistHelper.py` and `tests/unit/test_lint_diagram_refs.py`.
- **Root security scan baseline (Fixed)**: replaced two runtime `assert`
  statements in dependency installation and upgrade paths with explicit
  package-specification guards, preventing optimization from removing the
  checks and leaving the root `MistHelper.py` Bandit scan clean.

### Mist API Coverage Audit

- **OpenAPI GET endpoint catalog + diff**: Added `tools/openapi_endpoint_catalog.py`
  which parses `documentation/mist-api-openapi31json.json`, emits
  `documentation/MIST_API_GET_ENDPOINTS.md` (508 GET ops across 190 tags) and
  `documentation/MIST_API_MISSING_ENDPOINTS.md` (408 GETs not yet wired into
  MistHelper.py). The tool is idempotent and runs `ruff` / `black` clean.
- **SpecKit feature scaffolds (408 specs)**: Generated `specs/500-mist-*` through
  `specs/907-mist-*` -- one feature dir per missing GET endpoint, each containing a
  `spec.md` parameterized from the OpenAPI metadata (operationId, path, tag,
  required/optional params, mistapi SDK module) and pre-checked against the
  Constitution (Inline Comments VI, Action Logging VII, 5-Item Rule, `safe_input`,
  `DataExporter`, `ENDPOINT_PRIMARY_KEY_STRATEGIES`, ASCII-only logging, README +
  CHANGELOG updates). Each spec is its own SpecKit workflow ready for
  `speckit.plan` / `speckit.tasks` / `speckit.implement`.

### Added

- Added menu `196` for `GetOrgLicenseAsyncClaimStatus` so operators can export org-level async claim-job summary data and optional per-device detail rows through `DataExporter` with composite upsert keys for SQLite/Redis/Arango backends.
- **Address audit now logs a per-phase timing breakdown (menu 195)**: a Tier-3 run
  spends 12-20 seconds per site and it was not obvious where that time went. A tiny
  always-on ``PhaseTimer`` now accumulates wall-clock time per stage (SQLite cache
  read, Tier-1 internal, Tier-2 Nominatim incl. its rate-limit sleep, Tier-3 browser
  total, and the Tier-3 sub-steps: locating the input, the human-like typing, the
  fresh-result poll incl. the suite grace, and the politeness delay). At the end of
  the run the audit logs the breakdown sorted slowest-first to ``data/script.log``,
  turning "it feels slow" into a measurement. Live data shows the human-like typing
  (``ui.type_query``) dominates -- tune it with ``UI_GEOCODE_MIN_KEY_DELAY_MS`` /
  ``UI_GEOCODE_MAX_KEY_DELAY_MS`` (faster typing trades against Google's bot
  heuristics), or lower the ``UI_GEOCODE`` politeness/timeout knobs.

- **Address audit now flags rows it cannot safely auto-correct, as review-only
  (menu 195)**: two new classification states protect against pushing a wrong or
  non-unique address to Mist, and both are **excluded from write-back** (they are
  never offered for push, and they show a blank Suggested Address so the operator
  decides by hand from the Mist/CSV/SNMP columns):
  - **`CONFLICTING_HINTS`** -- the Mist address, the customer CSV, and the SNMP
    location disagree on the **house number with no majority** (every hint names a
    different number, or only two hints have numbers and they differ). A 2-vs-1
    split still has a clear majority and is left alone (the lone dissenter is the
    outlier); a suite on a dissenting hint does not rescue it, because a suite is
    only meaningful on the agreed-upon street number. This stops the tool from
    silently picking one of several *different valid stores* for a single site --
    e.g. a real T-Mobile site whose SNMP location was stale ``1520 Route 38 ...
    Hainesport NJ`` while Mist and the CSV pointed at a Hawaii address.
  - **`DUPLICATE_ADDRESS`** -- two or more *different* sites resolve to the
    **identical** full address (same suite, or both lacking one), which would make
    them indistinguishable for shipping. Sites that share only a base street but
    carry *different* suites are the normal strip-mall case and are left untouched
    because their full addresses differ.

- **Address audit can now push corrected addresses back to Mist (menu 195)**: the
  audit was read-only; you reviewed the comparison and fixed addresses by hand.
  After saving the comparison report you are now offered an **optional write-back**.
  It is gated twice for safety: a single batch opt-in (`[y/N]`, default No), then a
  **per-site `[y/N]` confirmation** that shows the site's address BEFORE (current
  Mist value) and AFTER (the suggested correction) side by side. Only the sites you
  say yes to are written. The write is minimal and safe -- it fetches the full Mist
  site record, replaces **only** the `address` field, and PUTs the record back, so
  `latlng`, `timezone`, `country_code`, sitegroup and template IDs are all
  preserved. Each write is fail-soft: a read-only token (HTTP 403) or any API error
  is recorded as a failed outcome and never aborts the batch. Afterwards you are
  prompted to save a **before/after correction report**
  (`data/address_corrections_<timestamp>.csv`) listing every reviewed site and
  whether it was pushed, skipped, or failed. Only correctable rows are offered
  (MISSING_SUITE, MISSING_NUMBER, WRONG_STREET, CSV_BETTER, AMBIGUOUS); matches and
  Mist-better rows are never touched.

### Changed

- **Address audit suite/unit detection is consolidated and typo-tolerant (menu
  195)**: three modules (``address_resolver``, ``audit_engine``, ``ui_geocoder``)
  each defined their own suite/unit keyword regex, which drifted out of sync -- a
  real customer file spelled it ``Sute A-103`` and only some detectors recognized
  it, so that unit was dropped from the suggested address (cosmetic, but sloppy).
  All three now derive from a single ``SUITE_KEYWORDS`` constant in a shared
  ``suite_patterns`` module, so a spelling is added in exactly one place. The common
  misspelling ``sute`` is now recognized everywhere (``ste``/``Ste.`` were already
  covered); ``suit`` is deliberately excluded to avoid matching ``lawsuit`` /
  ``pursuit``. Detection/classification behavior is otherwise unchanged.

- **Address audit Source column now names Google explicitly (menu 195)**: the
  Tier-3 web authority is Google Places autocomplete, accessed by driving the Mist
  portal's address box, but the Source column labelled it only `Mist UI` -- which
  does not make it obvious that Google deduced the suggested address. It now reads
  `Google (Mist UI)` so it is unmistakable when Google found, filled in, or
  confirmed an address (the Issue Type column still says *what* changed:
  `MISSING_SUITE`/`MISSING_NUMBER`/`WRONG_STREET` mean Google corrected a blank,
  `ADDRESS_MATCH` means Google confirmed the existing value).

- **Address audit diagnostic logging no longer prints to the terminal (menu
  195)**: the audit's `logging.*` calls (e.g. the Nominatim "no result" warnings)
  were written to both `data/script.log` AND the console, where they interleaved
  with and corrupted the tqdm progress bar. The feature speaks to the operator
  exclusively through `print` (the comparison table, the prompts, the write-back
  confirmations), so its logging is purely a diagnostic trail. For the duration of
  a run a filter is attached to the root logger's CONSOLE handlers that drops only
  this package's records; the file handler is untouched, so `script.log` still
  captures everything while the terminal shows just the table, prompts, and a
  clean progress bar.

- **Address audit types into Google's box with a human-like, randomized cadence
  (menu 195)**: the Tier-3 geocoder previously typed each query at a fixed 40 ms
  cadence, which is robotic and risks Google's autocomplete throttling / bot
  heuristics. It now types one character at a time with a randomized
  inter-keystroke delay (default 60-190 ms, from an unpredictable `SystemRandom`
  source) plus an occasional longer "thinking" pause, so the input rhythm
  resembles a person. The bounds are tunable via `UI_GEOCODE_MIN_KEY_DELAY_MS` /
  `UI_GEOCODE_MAX_KEY_DELAY_MS`.

- **Address audit now flags incomplete Mist addresses (missing house number)
  (menu 195)**: a Mist site whose street had no house number (`S Federal Hwy`)
  was reported ADDRESS_MATCH against the web-resolved `2315 S Federal Hwy` --
  i.e. "no change needed" -- even though the street *number* was missing, which
  makes the address unshippable. A new ninth classification state,
  `MISSING_NUMBER`, now surfaces these so the operator can add the number the web
  found. Rows where Mist already has a house number are unaffected.

- **Address audit now adjudicates suite *conflicts*, not just missing suites (menu
  195)**: Tier-3 was skipped whenever the Mist address already carried any suite,
  so when the customer CSV claimed a *different* unit (Mist `#204` vs CSV
  `Suite H200` at the Mall at Millenia) the audit reported MIST_BETTER without ever
  checking which unit is real. Tier-3 now also runs when the CSV unit disagrees
  with Mist's, so the web adjudicates the correct shippable unit. Identical units
  expressed differently (`Suite 100` vs `Ste 100`) still skip the lookup.

- **Address audit query is now built by house-number consensus (menu 195)**: the
  geocoding query was built SNMP-location-first, so when a site's SNMP location
  pointed at a different address -- even a different state -- the audit geocoded
  the wrong place. One real T-Mobile site in Palm Beach Gardens, FL had an SNMP
  location of `1520 Route 38 ... Hainesport NJ`, and the audit "corrected" the FL
  store to a **New Jersey** address (a shipping-safety bug). The Mist address, the
  SNMP location, and the customer CSV are now treated as equal *hints*: the audit
  votes on the house number across all three and uses the agreed-upon, cleanest,
  suite-bearing source, so one bad hint can no longer hijack the query. SNMP
  directional glue (`SFederal` -> `S Federal`, `NMilitary` -> `N Military`) is
  repaired before voting. Tier 3 also retries once **without** the business-name
  prefix when the `"<business> <address>"` query returns nothing (a store may not
  sit at that exact number), which recovers rows that previously hit NO_RESULT.

- **Address audit Tier-3 now self-spawns a browser and deduces the suite (menu 195)**:
  Two gaps stopped the Mist-portal path from ever working. (1) Tier-3 only ever
  *took over* a browser at `localhost:9222` -- which nothing was running, and
  `localhost` resolved to IPv6 `::1` (`ECONNREFUSED`). The default mode is now
  `auto`: it takes over a running debuggable browser if present, otherwise it
  **spawns Edge for you**, waits while you log into Mist and open a site's
  settings page, then takes it over (CDP endpoint fixed to `127.0.0.1`). A
  one-time readiness probe confirms the "Location Search" box is visible and
  guides you to it if not. (2) Tier-3 never ran for the rows that needed it --
  `_combine` returned the Tier-1/Tier-2 result first, so Google-via-Mist (the
  only source that knows the real suite) was skipped on every MISSING_SUITE row.
  Tier-3 now runs whenever a suite is actually missing and, when it returns a
  confident result, **acts as the authority** (overriding the internal guess);
  if it returns nothing, results are exactly as before (graceful). The single
  `ADDRESS_AUDIT_GEOCODE` knob now accepts `off | auto | attach | launch`
  (default `auto`).

- **Address audit Tier-3 web geocoding is flag-free (menu 195)**: The Tier-3
  browser geocoder no longer requires the `--ui-geocode` CLI flag (removed). The
  Mist site address, the SNMP location variable, and the customer CSV are all
  treated as *hints*, fused into one best-guess query and verified against the
  web to deduce the true, shippable address.

### Fixed

- **Menu 196 prompted for `Org ID (UUID)` instead of using the configured org**:
  the async license-claim exporter
  (`LicenseExportUtils.export_org_license_async_claim_status`) was written to read a
  non-existent env var `MIST_ORG_ID` and then call `InputUtils.safe_input(...,
  default_value=...)`. `safe_input` always prompts -- `default_value` only supplies
  the fallback on empty ENTER -- so with no `MIST_ORG_ID` key set anywhere it always
  fell through to an interactive `Org ID (UUID):` prompt, ignoring the operator's
  configured org. It now uses the standard resolver
  `ConfigUtils.get_cached_or_prompted_org_id()` like every other menu operation
  (precedence: cached global -> `org_id`/`ORG_ID` env -> `.env` file -> interactive
  org picker only as a last resort). The same helpers also stopped using the
  deprecated naive `datetime.utcnow()` for their `polled_at_utc` column and now use
  timezone-aware `datetime.now(UTC)` to match the rest of the codebase. Unit tests
  updated to stub the resolver. (#576)

  (menu 195)**: Tier-3 types ``{business} {address}`` (including the suite) into the
  Mist dashboard's Google Places box, but Google's autocomplete often resolves to
  the street/establishment and drops a unit typed at the end -- and the freshness
  guard only waited for the *house number*, so it accepted the bare street without
  the unit. The unit then vanished from the suggestion, and because Mist also
  lacked it the row even read ``ADDRESS_MATCH`` ("no change needed"). A real run
  lost the unit on four sites whose CSV **and** SNMP location both confirmed it
  (FLSS2SJB ``Unit 200``, FLS01302 ``Suite 100``, FLS01501 ``Suite 98``, FLSE8677
  ``Unit 8``). Two changes fix this: (1) when a unit was typed, the freshness guard
  now waits a short bounded grace (``_SUITE_GRACE_S``) for the unit to also appear
  in the top suggestion before accepting it (Google usually catches up); and (2) if
  the unit still never appears, the unit we typed is re-appended to Google's street
  -- but only when it is safe (the suggestion carries no *other* unit, and the house
  numbers agree, so a different unit or a different building is never overwritten).
  Restored rows now correctly read ``MISSING_SUITE`` instead of a false
  ``ADDRESS_MATCH``, so the operator can add the unit.

- **Address audit suggestion glued the business name to Hawaii hyphenated house
  numbers (menu 195)**: the Tier-3 (Google-via-Mist) suggestion cleaner strips the
  establishment name that Google glues to the address (``T-Mobile931 US Highway
  ...`` -> ``931 US Highway ...``) by anchoring on the ``<house-number> <street>``
  start. Its anchor required the house number to be followed by a space, but
  Hawaii's grid addresses use a hyphenated house number (``74-5450``), so the
  anchor never matched and the business name survived in the output (real run:
  ``T-Mobile74-5450 Makala Blvd #107`` for site HIS00364). The anchor now accepts
  an optional ``-<digits>`` run in the house number, so the prefix is stripped
  (``74-5450 Makala Blvd #107``) while every non-hyphenated address and suite dash
  (``Sute A-103``) is unaffected.

- **Logging and on-screen output crashed on non-Western characters (all menus)**:
  running any operation against data containing characters outside the Windows
  console's default `cp1252` codec raised `UnicodeEncodeError` and dumped a
  `--- Logging error ---` traceback. This surfaced in the address audit (menu 195)
  with a real Hawaii dataset -- an address such as `315 East Makaʻala Street,
  Hawaiʻi County` contains the Hawaiian ʻokina (`U+02BB`), which crashed the
  `data/script.log` file handler and corrupted the progress bar. Both log file
  handlers are now opened with `encoding="utf-8"`, and `stdout`/`stderr` are
  reconfigured to UTF-8 with a `backslashreplace` fallback at startup, so the
  comparison table and any other `print` of international addresses are safe too.
  The fix is global (the logging setup lives in the root module) and fail-soft:
  if a stream cannot be reconfigured the worst case is the prior behavior, with no
  new failure introduced.

- **Address audit Nominatim suggestion leaked raw OpenStreetMap formatting (menu
  195)**: when a row was validated by Tier-2 (OpenStreetMap) rather than Tier-3,
  the "Suggested Address" showed OSM's verbose `display_name` -- e.g.
  `T-Mobile, 1200, Northwest 87th Avenue, Doral, Miami-Dade County, Florida,
  33172, United States` -- complete with the business name, county, and country.
  OSM only validates the *street*, so the suggestion is now Mist's own
  already-formatted address with the trailing country dropped
  (`1200 NW 87th Ave #1st, Doral, FL 33172`), consistent with the Tier-1/Tier-3
  outputs and never losing an existing suite. (Side effect: a row where Mist's
  address already matches now reads ADDRESS_MATCH instead of the misleading
  MIST_BETTER.)

- **Address audit MISSING_NUMBER never fired on real data (menu 195)**: the
  missing-house-number check (added in the prior release) tested the whole Mist
  address string for any digit, but Mist stores the address as one formatted
  string ending in the ZIP (`S Federal Hwy, Fort Pierce, FL 34982, USA`) -- so the
  ZIP's digits made every address look like it already had a house number, and a
  number-less street was still reported ADDRESS_MATCH. The check now inspects only
  the leading street segment (before the first comma) for a leading house number,
  so `S Federal Hwy, ...` is correctly flagged MISSING_NUMBER against the
  web-resolved `2315 S Federal Hwy`. (The unit test was strengthened to use full
  Mist-style strings so it would have caught this.)

- **Address audit suggested address glued the street/suite to the city (menu
  195)**: Google's autocomplete sometimes returned the street fused to the city
  with no separator (`2315 S Federal HwyFort Pierce`, `...suite 330Brandon`),
  leaving an un-shippable suggested address. The cleaner now splits a street-type
  suffix (`Hwy`, `Blvd`, `Dr`, ...) or a number glued directly to a following
  capitalized city word, while deliberately preserving legitimately camel-cased
  cities (`DeFuniak`) and alphanumeric street names (`A1A`) -- only street
  suffixes and digits trigger a split, never a generic lowercase->uppercase
  boundary.

- **Address audit hid wrong-side-of-street addresses as a MATCH (menu 195)**: the
  street comparison ignored directionals, so a Mist address of `1606 E Jefferson`
  was reported as ADDRESS_MATCH against the web-confirmed `1606 West Jefferson` --
  East vs West are different streets, and shipping to the wrong one is a real risk.
  The comparison now flags a conflicting *leading* directional (the one right after
  the house number, so a directional inside a city name like `West Palm Beach` is
  ignored) as WRONG_STREET, while treating abbreviations as equal (`S` = `South`,
  `NW` = `Northwest`). The street-name comparison also now includes ordinal names
  (`107th`, `A1A`), so `1455 NW 107th Ave` reliably matches `1455 Northwest 107th
  Avenue` regardless of whether Google abbreviates or spells out the directional
  and street type.

- **Address audit suggested-address still showed the business name on number-first
  streets (menu 195)**: the suggestion cleaner stripped Google's glued business
  name only when the street name began with a letter, so rows whose street starts
  with a digit kept the prefix (`T-Mobile4103 14th St W`). It now strips the
  prefix in that case too (`4103 14th St W, Bradenton, FL 34205`) and splits a
  directional fused to the city (`...Ave NLive Oak` -> `...Ave N Live Oak`).

- **Address audit Tier-3 captured the WRONG suggestion (one-row lag) (menu 195)**:
  Google Places leaves the previous query's suggestions in the dropdown until the
  new request returns, so the geocoder read each address's result one lookup late
  -- every row was shifted by one and therefore wrong (e.g. the query for
  `1701 Ohio Ave` captured `7535 North Kendall Drive`). The geocoder now anchors
  on the query's house number and polls until the TOP suggestion actually
  contains it, dismissing the stale dropdown first; on timeout it returns
  NO_RESULT rather than risk a stale, wrong address. It also cleans Google's row
  text -- stripping the glued business-name prefix (`T-Mobile931 US Highway...`)
  and trailing `, USA` -- so the suggested value is the clean, shippable street
  line with its suite preserved (`931 US Highway 331 Ste A2, DeFuniak Springs, FL
  32435`). NOTE: anyone who ran the audit before this fix should re-run it and
  discard the prior output; the cached results were shifted.

- **Address audit misleading Nominatim log (menu 195)**: The "Nominatim returned
  no result" warning printed the business-name + suite query string even though
  the actual geocode used the suite-stripped street, making it look like the
  wrong thing was searched. It now logs the street actually geocoded.

- **Address audit suggested-address cleanup (menu 195)**: Suggested addresses
  were polluted with the customer's SAP internal store-code prefix
  (e.g. `S2SJB - `, `08806 - `) and sometimes carried the SNMP field's stale ZIP.
  The SNMP enricher now strips the leading SAP store code (it is not part of the
  postal address), and Tier-1 rebuilds a clean suggestion from Mist's own
  street/city/state/ZIP plus the discovered suite -- preferring the customer CSV
  suite over the SNMP one. The suite detector was broadened to catch `#3`,
  `Space P239`, `Spc`, `Rm`, `Lot`, and `Apartment` in addition to
  Suite/Ste/Unit/Apt/Bldg. Result: `S2SJB - 5550 N Military Trl Unit 200 ... FL
  33496` now renders as the clean, shippable `5550 N Military Trl Unit 200,
  Boca Raton, FL 33431`.

- **Address audit external validation via OpenStreetMap (menu 195)**: Nominatim
  (Tier 2) silently failed for every site because the resolver verified TLS
  certificates, which Zscaler SSL inspection breaks -- so the audit only ever
  used internal CSV/SNMP comparison and the "Source" column never showed external
  validation. The resolver now skips TLS verification for the public Nominatim
  call by default (override with `MIST_SKIP_SSL_VERIFY=false`), strips the
  suite/unit before geocoding (OpenStreetMap has no US retail suites) so the base
  street can match, validates the street on **every** row, and records a
  `street_validated` flag surfaced as `Internal+OSM` / `Nominatim` in the Source
  column. The Nominatim step now logs visibly (INFO on hit, WARNING on miss).
  Verified live: real streets validate (confidence ~0.88), nonsense streets do
  not. NOTE: OpenStreetMap validates the street only; business-name + suite
  confirmation still requires the optional Tier-3 Google-Places browser tier
  (auto-engaged when a debuggable browser is available).

- **Address audit CSV delimiter (menu 195)**: The CSV ingester assumed tab
  delimiters and silently skipped every row of a comma-delimited file (the Excel
  default `.csv`), reporting "No valid rows parsed". The delimiter is now
  **auto-detected** per file (tab / comma / semicolon / pipe), an Excel BOM is
  stripped, blank lines no longer count as parse failures, and addresses that
  contain the delimiter (e.g. "6670 US Highway 129, Suite 1") are reconstructed
  by parsing on the fixed serial/model + city/state/zip anchors. Verified against
  a real 44-row customer export (44 parsed, 0 skipped).

### Added

- **Site Address Audit from CSV (menu 195, read-only)**: New `src/site/address_audit/`
  subpackage that reconciles a customer-provided tab-delimited CSV (serial, model,
  address, city, state, zip) against Mist site records and surfaces address
  discrepancies (the common strip-mall "missing suite/unit" case for retail
  fleets). Pipeline: ingest + sanitize CSV -> match each row to a Mist site by
  device **serial number** (golden key) with a rapidfuzz >=85% address fallback
  -> enrich with SNMP location (`vars.snmp_location` + `snmp_config.location`)
  -> resolve/validate the address through three **free** tiers and classify into
  one of eight states -> render an old-vs-suggested comparison table -> optionally
  save a timestamped CSV to `data/`. **Zero Mist writes**; write-back is an inert
  `AddressCorrector` stub. Address resolution tiers (no paid APIs; there is no Mist
  geocoding endpoint): (1) internal CSV/SNMP/Mist comparison, no network;
  (2) Nominatim street validation reusing `NominatimValidator`; (3) optional
  Playwright "hijack" of the live Mist dashboard Location Search field
  (`--ui-geocode`, OFF by default) that launches or takes over (CDP) the system
  browser -- the only free path to Google-quality retail suite numbers. Results
  cached in an additive `geocoding_cache` table in `data/mist_data.db`
  (`INSERT OR REPLACE`). Classification anchors on the street house number plus a
  street-name word so SNMP store-number prefixes and partial addresses do not
  cause false `WRONG_STREET` results. Adds the `--ui-geocode` CLI flag and a
  `BUSINESS_NAME` `.env` lookup (prompted at runtime when blank, skippable for
  private addresses). 11 new modules + 8 unit-test files (58 tests). Spec:
  `specs/1003-site-address-audit/`.

### Lint / Compliance

- **Issue #429 -- CONV-LOG-FSTRING sweep**: Converted all 695 eager-formatting
  logging calls in `MistHelper.py` to lazy `%s`-style arguments
  (681 G004 + 6 G003 + 8 G201 -> 0). Delivered in four ~170-site tranches with
  a frozen parity-test baseline (`tests/fixtures/issue_429_log_baseline.json`)
  and four new test modules (parity, hypothesis property, codemod idempotency,
  lazy-sentinel) gating every tranche. Enabled the `G` ruff rule family in
  `[tool.ruff.lint] select` and scoped it to `MistHelper.py` only via
  `per-file-ignores`; `src/`, `tools/`, `web_portal/`, top-level helper
  scripts, and the codemod synthetic-input fixture retain eager formatting
  pending follow-up issues. Codemod (`tools/codemod_logging_lazy.py`) +
  capture script (`tools/capture_log_baseline.py`) preserved for re-runs.

### Dependency Updates

- Raised Mist API dependency floors to `mistapi>=0.63.1` in `requirements.txt`, `pyproject.toml`, and the runtime import manager so documented, packaged, and auto-install paths stay aligned.

### Compatibility Validation

- Live compatibility validation against `mistapi 0.63.1` succeeded for MistHelper session initialization plus representative org/site read paths: self lookup, sites, inventory, wireless clients, alarms, events, SLE exports, audit logs, and support tickets.

### Changed

- **Serial CC refactor (offender #8)**: Extracted `OrgClientSecurityExporter.security_events` workflow into `src/refactors/serial_cc/security_events.py` (`SecurityEventsService`) and reduced `MistHelper.py` method to thin delegator. Post-refactor Radon complexity in `MistHelper.py` is now `A (1)` for this symbol.
- **Serial CC refactor (offender #9)**: Extracted `OrgExportUtils.sle_metrics` workflow into `src/refactors/serial_cc/sle_metrics.py` (`SLEMetricsService`) and reduced `MistHelper.py` method to thin delegator. Post-refactor Radon complexity in `MistHelper.py` is now `A (1)` for this symbol.
- **Serial CC refactor**: Delegated `_LegacyPacketCaptureManager._start_site_client_capture_wireless` to `src/refactors/serial_cc/start_site_client_capture_wireless.py` (`SiteWirelessClientCaptureService`) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Delegated `_LegacyPacketCaptureManager._start_site_scan_capture` to `src/refactors/serial_cc/start_site_scan_capture.py` (`SiteScanCaptureService`) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Extracted `GlobalImportManager._get_global_assignments` into `src/refactors/serial_cc/global_assignments_builder.py` (`GlobalAssignmentsBuilderService`) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Extracted `SiteClientExporter.client_insights` into `src/refactors/serial_cc/site_client_insights.py` (`SiteClientInsightsService`) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Extracted `GlobalImportManager.initialize_all_imports` into `src/refactors/serial_cc/import_initialization_service.py` (`ImportInitializationService`) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Decomposed `OrgInventoryExporter.combined_inventory_with_site_info` in place into class helper methods (no new delegates/wrappers) and reduced `MistHelper.py` method complexity to `A (1)`.
- **Serial CC refactor**: Decomposed `OrgDeviceStatsExporter.device_port_stats` in place into class helper methods (no new delegates/wrappers) and reduced `MistHelper.py` method complexity to `A (3)`.
- **Serial CC refactor**: Decomposed `_LegacyPacketCaptureManager._execute_site_capture_loop_legacy` in place into class helper methods (no new delegates/wrappers) and reduced `MistHelper.py` method complexity to `A (4)`.
- **Serial CC refactor**: Decomposed `OrgAlarmEventExporter.device_events_52w_legacy` in place into 7 class helper methods (no new delegates/wrappers) and reduced `MistHelper.py` method complexity from `E (38)` to `B (8)`.
- **Serial CC refactor**: Decomposed `execute_with_connection_pool_management` in place into 3 module-level helpers (`_pool_configure`, `_pool_process_batch_wait_loop`, `_pool_log_batch_exception`) and reduced complexity from `D (21)` to `B (6)`.
- **Serial CC refactor**: Decomposed `run_systematic_test` in place into 4 module-level helpers (`_systematic_test_build_safe_list`, `_systematic_test_emit_skips`, `_systematic_test_run_option`, `_systematic_test_resolve_fast_mode`) and reduced complexity from `D (21)` to `B (8)`. No D or E grade offenders remain in `MistHelper.py`.

### Removed

- **Dead legacy classes**: Removed 5 orphaned `_Legacy*` classes (`_LegacyPacketCaptureManager`, `_LegacyGatewayStatsExporter`, `_LegacyGatewayExportUtils`, `_LegacyWAN2MigrationManager`, `_LegacyWANProbeDeviceOverrideManager`) from `MistHelper.py`. These were inline implementations retained for rollback safety after their logic was migrated to canonical classes (`PacketCaptureManager` -> `src/capture/`, `GatewayStatsExporter`, `GatewayExportUtils`, `WAN2MigrationManager`, `WANProbeDeviceOverrideManager`). Verified unreferenced (no instantiations, aliases, subclasses, or dynamic forwarders reach them). Deletion removed 3,939 lines (27,666 -> 23,722) and cleared the two worst CRITICAL complexity hotspots (`start_org_packet_capture_legacy` CC 53, `with_wan_overrides_legacy` CC 46). Compliance violations dropped 1440 -> 1214; classes 101 -> 96.

### Fixed

- **Menu 13 still undercounted APs (claimed-but-never-connected APs dropped)** (#417): Even after #415, AP counts were short because the AP path used `countOrgDevices(distinct="version")`, which only returns version-keyed buckets. APs that are **claimed and assigned to a site but have never connected** report no firmware version and were silently dropped (e.g. T-Mobile_USA_Retail AP41 showed 9428 vs the portal's 9676). These APs have a `site_id`, so the #415 unassigned supplement did not catch them either. APs are now counted directly from `getOrgInventory(type="ap")` — the same source as the portal "Claim APs" screen — so every claimed AP is counted exactly once with a three-way version bucket: `unassigned` (no `site_id`), the real firmware version (assigned + connected), or `unknown` (assigned but never connected). Switches and gateways are unchanged, and the unassigned supplement is now switch-only to avoid double counting APs. Conservation is verified against real inventory data and four new unit tests cover every AP state.
- **Menu 13 undercounted devices (unassigned AP/switch inventory excluded)** (#415): The Org Device Inventory Summary counted APs via `countOrgDevices` and switches via `searchOrgDevices`, both of which return only devices **assigned to a site**. Unassigned APs and switches sitting in org inventory were therefore omitted from the model-count, firmware-summary, and version-per-model reports, understating totals and leaving the reports internally inconsistent (gateways already used `getOrgInventory`, which includes unassigned stock). A supplemental `getOrgInventory(type="ap,switch")` fetch now pulls claimed-but-unassigned APs and switches (filtered client-side on a missing `site_id`), merges them into the model counts, and surfaces them under a dedicated `unassigned` firmware column in the firmware summary and version-per-model pivot (single-org and MSP combined). The `unassigned` bucket is kept distinct from `unknown` (an assigned device that never reported firmware). Assigned-but-offline/disconnected devices were already counted (the assigned-device APIs do not filter on connection state), so no change was needed there. Gateways are intentionally excluded from the supplemental fetch to avoid double counting.

## [26.06.09.22.10] - Fix E911BSSIDReportGenerator module-level access

### Fixed

- **Tests**: `tests/integration/test_mistapi_sdk_compatibility.py::test_maps_and_wlan_helpers_are_covered` and `test_e911_report_runs_with_stubbed_maps_and_wlans` no longer fail with `AttributeError: module 'MistHelper' has no attribute 'E911BSSIDReportGenerator'`. Moved `E911BSSIDReportGenerator` import from function-local (aliased as `_E911`) to module-level so tests can access it via `MistHelper.E911BSSIDReportGenerator`. Closes #364.

## [26.06.08] - Menu 194 Clone Device Config to Gateway Template

### Added

- **Menu 194**: Clone Device Config to Gateway Template — promote a gateway device's local configuration into a reusable org-level gateway template. Selects site → selects gateway device → fetches live device config via `getSiteDevice` → strips device metadata → prompts for template name/type/model → requires typed `CREATE` confirmation → calls `createOrgGatewayTemplate` → exports result to CSV. Implemented in `src/gateway/device_template_cloner.py` with delegation stub in `MistHelper.py`.

## [26.05.27.05.29] - Decomposition Wave 2 Complete (Phases 1-9)

### Added

- **9 feature-domain packages** extracted from `MistHelper.py` into `src/`:
  - `src/analytics/` — `SiteInventoryHealthAnalyzer`, `SiteAnalyticsConfigurator`, `ZoneConfigurationAnalyzer`
  - `src/capture/` — `PacketCaptureManager`, `PacketCaptureDownloadManager`
  - `src/export/` — `SiteExportUtils`, `SiteInsightsExporter`
  - `src/gateway/` — `GatewayExportUtils`, `GatewayStatsExporter`, `GatewayOverrideAnalyzer`, `WAN2MigrationManager`, `WanProbeDeviceOverrideManager`
  - `src/inventory/` — `OrgDeviceInventorySummaryCore`, `OrgDeviceInventoryMSPOrchestrator`, `InventoryCSVComparator`
  - `src/site/` — `SiteConfigManager`
  - `src/ssh/` — `EnhancedSSHRunner`, `SSHRunnerManager`
  - `src/troubleshooting/` — `MarvisTroubleshootUtils`
  - `src/websocket/` — `ServicePingManager`, `ServicePingDiscoveryMixin`
- Hard-gate evidence checklists for all 9 phases in `specs/193-main-decomposition-wave-2/checklists/`
- Wave 2 Module Ownership table in README.md documenting phase-to-package-to-menu mapping
- Updated `src/` directory layout in README.md reflecting actual feature-domain structure

### Changed

- `MistHelper.py` entrypoint now delegates to `src/` modules while preserving compatibility surface
- README Architecture Evolution section updated with current `src/` layout and decomposition status
- Packet capture ownership moved to `src/capture/` with `MistHelper.py` orchestration compatibility

### Fixed

- Restored packet capture legacy test compatibility by keeping wrapper hook behavior for `_poll_and_download_pcap`, `_poll_for_pcap_url`, and `_save_pcap_file`
- Prevented CI `exit code 2` by replacing `MagicMock(side_effect=KeyboardInterrupt)` with plain function in `TestPollAndDownloadPcap::test_keyboard_interrupt`

## [25.05.25.05.29] - Ticket Viewer & Detail Export

### Added

- **Menu 192**: Interactive ticket detail viewer with comments (`OrgTicketManager.view_ticket`)
- **Menu 193**: Export all tickets with full details and comments to CSV/SQLite (`OrgTicketManager.export_ticket_details`)
- Primary key strategy for `getOrgTicket` endpoint (natural PK on `id`)
- Private helpers: `_select_ticket`, `_fetch_ticket_detail`, `_display_ticket_detail`
- 7 new tests for menus 192-193 and `_select_ticket` helper

### Changed

- **Menu 190** (Add Comment): Refactored to use interactive ticket selector instead of raw ID prompt
- **Menu 191** (Update Ticket): Refactored to use interactive ticket selector instead of raw ID prompt
- `OrgTicketManager` class expanded from 4 to 6 public operations (list, create, add comment, update, view, export)
- Operation count updated: 191 → 193

## [25.06.13.00.00] - Support Ticket Management

### Added

- **Menu 188**: List/export all organization support tickets to CSV/SQLite (`OrgTicketManager.list_tickets`)
- **Menu 189**: Create a new support ticket with subject, type, and optional comment (`OrgTicketManager.create_ticket`)
- **Menu 190**: Add a comment to an existing ticket with optional file attachment (`OrgTicketManager.add_comment`)
- **Menu 191**: Update ticket fields (subject, status, type) on an existing ticket (`OrgTicketManager.update_ticket`)
- New `OrgTicketManager` class with full ticket lifecycle management
- Primary key strategies for `getOrgTicket`, `createOrgTicket`, `updateOrgTicket`, `addOrgTicketComment`
- Attachment support via `addOrgTicketCommentFile` multipart API (integrated into Menu 190)
- Comprehensive test suite: `tests/test_ticket_manager.py` (14 tests covering all 4 operations + edge cases)
- Operation count updated: 187 → 191

## [26.05.21.00.00] - Menu Regrouping

### Changed (BREAKING)

All 188 menu operations (0-187) renumbered into 30 logical contiguous groups. Any scripts or aliases that hard-code a `--menu N` number must be updated. The migration script `scripts/menu_regroup.py` was used to apply all 425 touch points (menu_actions keys, _REGISTRY keys, optimized_test_order values, WAVE1 baseline keys/values, and Menu #XX logging references).

**New group structure:**

| Range | Group | Safety |
| - | - | - |
| 0 | Exit | — |
| 1–7 | Org Sites & Analysis | safe |
| 8–14 | Org Device Inventory | safe |
| 15–19 | Org Device Stats | safe / resource_intensive |
| 20–26 | Org Events & Logs | safe |
| 27–30 | Org Client Stats | safe |
| 31–36 | Org Gateway Operations | safe |
| 37–41 | Org Templates | safe |
| 42–50 | Org Config & Admin | safe |
| 51–55 | Org SLE & Insights | safe |
| 56–59 | Org Misc Exports | safe / resource_intensive |
| 60–72 | Site Device Exports | interactive_safe |
| 73–79 | Site Insights & Anomalies | interactive_safe |
| 80–91 | Site Stats & Metrics | interactive_safe |
| 92–96 | Interactive Viewers | interactive_safe |
| 97–101 | Long-Running Exports | resource_intensive |
| 102–115 | WebSocket Show Commands | websocket |
| 116–123 | WebSocket Diagnostics | websocket |
| 124–127 | Device Diagnostics | interactive |
| 128–133 | Device Management | interactive |
| 134–135 | Packet Capture | interactive |
| 136–147 | Interactive Tools | interactive |
| 148–150 | Config Management | interactive |
| 151–152 | Continuous Loops | continuous_loop |
| 153 | Bulk | resource_intensive |
| 154–157 | Destructive: Firmware | destructive |
| 158–160 | Destructive: Reboot/Reprovision | destructive |
| 161–162 | Destructive: Virtual Chassis | destructive |
| 163–167 | Destructive: Template Changes | destructive |
| 168–170 | Destructive: Site Config | destructive |
| 171–174 | Destructive: Test Data | destructive |
| 175–176 | Destructive: SSH Runners | destructive |
| 177–187 | Destructive: Clear/Reset/Import | destructive |

**Complete old→new mapping (for migration reference):**

```text
0→0   1→20  2→21  3→22  4→31  5→102 6→103 7→104 8→105 9→134 10→135
11→1  12→8  13→15 14→19 15→16 16→33 17→9  18→59 19→34 20→2
21→11 22→10 23→4  24→17 25→12 26→32 27→3  28→35 29→62 30→65
31→60 32→61 33→63 34→64 35→37 36→38 37→39 38→40 39→41 40→27
41→28 42→24 43→29 44→30 45→42 46→44 47→45 48→46 49→69 50→66
51→67 52→68 53→73 54→47 55→48 56→136 57→49 58→43 59→50
60→137 61→138 62→139 63→97 64→98 65→99 66→51 67→52 68→74
69→75 70→92 71→93 72→94 73→95 74→96 75→151 76→152 77→100
78→101 79→140 80→121 81→76 82→54 83→53 84→77 85→78 86→79
87→118 88→119 89→120 90→154 91→158 92→161 93→162 94→14 95→18
96→36 97→175 98→176 99→155 100→156 101→141 102→148 103→149
104→163 105→150 106→164 107→171 108→172 109→173 110→174 111→165
112→142 113→166 114→167 115→143 116→157 117→144 118→168 119→6
120→169 121→7 122→170 123→123 124→106 125→107 126→108 127→109
128→110 129→111 130→112 131→113 132→114 133→115 134→116 135→117
136→124 137→125 138→128 139→129 140→159 141→122 142→160 143→130
144→131 145→132 146→133 147→177 148→178 149→179 150→180 151→181
152→182 153→183 154→184 155→185 156→126 157→127 158→26 159→145
160→89 161→90 162→91 163→146 164→147 165→153 166→5 167→56
168→57 169→55 170→70 171→71 172→72 173→88 174→25 175→186
176→58 177→187 178→80 179→81 180→82 181→83 182→84 183→85
184→86 185→23 186→87 187→13
```

Closes #368

## [26.05.20.17.31]

### Refactored

- `main()` decomposed into 9 focused private helper functions: `_initialize_deferred_imports`, `_build_argument_parser`, `_setup_runtime_flags`, `_initialize_dependencies`, `_establish_mist_session`, `_configure_runtime_options`, `_run_tui_mode`, `_run_cli_mode`, `_run_interactive_mode`. Function reduced from 561 lines / CC 89 (Grade F) to 25 lines / CC 13 (Grade C). Behavior and CLI interface unchanged. Closes #353

## [26.05.20.16.57]

### Refactored

- `initialize_mist_session` decomposed into 14 focused private helper functions: `_load_mistapi_module`, `_parse_api_tokens`, `_check_token_rate_limit`, `_introspect_apisession_class`, `_build_session_attempts`, `_log_session_attempt_traceback`, `_execute_session_attempts`, `_filter_available_tokens`, `_create_session_with_available_tokens`, `_retry_with_filtered_tokens`, `_try_session_fallback`, `_ensure_mist_get_method`, `_log_session_auth_status`, `_validate_initialized_session`. Function reduced from 248 lines / CC 67 (Grade F) to 37 lines / CC 8 (Grade B). Behavior and global state management unchanged. Closes #351

## [26.05.20.16.29]

### Changed

- README: Update operation count from 184 to 185 entries and range from (1-185) to (1-186), reflecting Menu 186 added in PR #339

### Added

- Menu 178: Export site aggregate health & capacity statistics (`getSiteStats`)
- Menu 179: Export site gateway performance metrics summary (`getSiteGatewayMetrics`)
- Menu 180: Export site switch performance metrics summary (`getSiteSwitchesMetrics`)
- Menu 181: Export site BLE beacon statistics (`listSiteBeaconsStats`)
- Menu 182: Export site WxLAN rule usage statistics (`getSiteWxRulesUsage`)
- Menu 183: Export site asset statistics (`listSiteAssetsStats`)
- Menu 184: Export current RRM channel & power plan per AP radio (`getSiteCurrentChannelPlanning`)
- Menu 185: Export self (admin account) audit log (`listSelfAuditLogs`)
- Menu 186: Export HA gateway cluster info, stats & node pair for a site (`GatewayHaExporter`) -- shows is_ha, node_name, cluster MAC (vc_mac), cluster_config/cluster_stat, and per-device node0/node1 MAC pair from `GetSiteDeviceHaClusterNode`
- New `GatewayHaExporter` class for HA gateway cluster info (stats + cluster node membership)
- New `SelfExportUtils` class for account-scoped data exports (admin audit logs)
- 2 new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries: `GetSiteDeviceHaClusterNode` (composite_pk) and `listSiteGatewayHaStats` (composite_pk)
- 18 net-new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries for previously uncovered endpoints
  (15 natural_pk, 3 composite_pk, 3 auto_increment_with_unique from probe run 3)

### Changed

- `documentation/menu_reference.md` extended to include all menus 164-185 (was truncated at 163)
- README operation count updated from 176 to 184

- Menu 176: Export Org WAN/Gateway Config — exports 6 org-level config types (networks, services, VPNs, gateway templates, device profiles, service policies) to a single timestamped JSON bundle for cross-org migration (#191)
- Menu 177: Import Org WAN/Gateway Config — imports config bundle into destination org with conflict detection (name match, IP/subnet overlap), dependency-ordered creation, cross-reference ID remapping, and dry-run mode (#191)
- New `OrgConfigMigrationManager` class encapsulating all export/import/conflict/remapping logic

### Security

- Fixed CodeQL `py/stack-trace-exposure` violations in `src/maps/maps_manager.py` (#302)
  - Updated exception logging to use `type(e).__name__: {str(e)}` instead of exception objects (lines 9506, 9528, 9556)
- Fixed CodeQL `py/clear-text-logging-sensitive-data` violation in `src/device/utility_commands.py` (#302)
  - Removed `exc_info=True` from error logging in ZTP password handler (line 1302)

### Refactored

- Reduced `intelligent_map_replacement_wizard` CC from 126 to ≤10 in `src/maps/maps_manager.py` (#294)
  - Extracted `_wizard_run` (orchestration body), `_wizard_fetch_devices`, `_wizard_fetch_zones`, `_wizard_fetch_beacons`, `_wizard_scale_path_nodes`, and updated `_wizard_fetch_assets`, `_wizard_scale_geometry`, `intelligent_map_replacement_wizard` to delegate to helpers
  - All new methods CC ≤10; `src/maps/*` remains in CI radon exclusion pending #293
- Reduced `interactive_map_viewer` CC from 43 to 8 in `src/maps/maps_manager.py` (#295)
  - Extracted `_install_visualization_packages` (CC=5), `_check_visualization_packages` (CC=4), `_fetch_map_details` (CC=3), `_fetch_devices_on_map` (CC=3), `_fetch_zones_on_map` (CC=3), `_filter_clients_for_map` (CC=5), `_fetch_clients_on_map` (CC=8), `_handle_coverage_exception` (CC=3), `_fetch_map_coverage` (CC=6)
- Reduced `launch_viewer_standalone` CC from 30 to 3 in `src/maps/maps_manager.py` (#296)
- Extracted `PlotlyMapDataSerializer` into `src/maps/plotly_map_serializer.py` and integrated `_launch_plotly_viewer` store/dropdown payload construction through serializer helpers (#293, Phase 2)
  - Replaced inline `dcc.Store` payload dict/list construction for map config, available maps/sites, selected zone, refresh times, and cache bust
  - Replaced repeated dropdown/store map list serialization in site-switch and map-refresh callbacks
  - Added serializer unit tests in `tests/maps/test_plotly_map_serializer.py` (5 tests)
- Extracted `PlotlyCoverageHeatmapRenderer` into `src/maps/plotly_heatmap_renderer.py` and delegated RF heatmap trace construction from `_launch_plotly_viewer` (#293, Phase 3)
  - Replaced large inline coverage parsing/rendering block with `build_heatmap_trace(...)`
  - Added heatmap renderer unit tests in `tests/maps/test_plotly_heatmap_renderer.py` (5 tests)
- Extracted `PlotlyMapFigureBuilder` into `src/maps/plotly_map_figure_builder.py` and delegated walls/wayfinding/zones rendering from `_launch_plotly_viewer` (#293, Phase 4)
  - Replaced large inline layer rendering blocks with `add_walls(...)`, `add_wayfinding(...)`, and `add_zones(...)`
  - Added figure builder unit tests in `tests/maps/test_plotly_map_figure_builder.py` (5 tests)
- Extracted initial callback logic into `src/maps/plotly_map_callback_manager.py` and delegated `_launch_plotly_viewer` callbacks for layer toggles and click-details rendering (#293, Phase 5a)
  - Replaced inline callback bodies with `apply_layer_toggles(...)` and `build_click_details(...)`
  - Added callback manager unit tests in `tests/maps/test_plotly_map_callback_manager.py` (5 tests)

### Refactored

- Reduced cyclomatic complexity of most methods in `src/maps/maps_manager.py` (#251); remaining high-CC methods deferred to dedicated follow-on issues (#293–#296)
  - Extracted `_check_dependencies`, `_configure_logging`, `_setup_api_session`, `_filter_org_privileges`, `_prompt_org_selection`, `_detect_org_from_session`, and `_resolve_org_id` from `main()` (CC 29→7)
  - Extracted `_download_all_site_map_images`, `_select_map_from_site`, `_backup_print_summary`, and other helpers to reduce method-level CC throughout the module
  - `src/maps/*` remains in CI radon exclusion until #293–#296 are resolved (`_launch_plotly_viewer` CC=138, `intelligent_map_replacement_wizard` CC=126, `interactive_map_viewer` CC=43, `launch_viewer_standalone` CC=30)
- Extracted `WebSocketManager`, `WebSocketNetworkDiagCommands`, and `WebSocketCommands` from `MistHelper.py` into `src/websocket/` modules, reducing `MistHelper.py` by ~1,789 lines (#209)
- Added `src/websocket/context.py` with `WebSocketCmdDeps` dataclass for clean dependency injection into extracted WebSocket command classes
- Updated CI radon exclusion to include `src/websocket/manager.py` (contains complex `wait_for_command_result` method)

## [26.05.12.07.25] - 2026-05-12

### Refactored

- Eliminated 3 thin wrapper classes (`SSIDTemplateConsolidationManager`, `E911BSSIDReportGenerator`, `ZoneConfigurationAnalyzer`) and 1 standalone wrapper function (`update_gateway_templates_wan2_variable`) by moving their logic directly into appropriate existing classes: `OrgExportUtils.ssid_template_consolidation`, `OrgExportUtils.e911_bssid_compliance_report`, `SiteExportUtils.zone_config_analysis`, `GatewayExportUtils.wan2_variable_migration`. Updated dispatch entries 104, 119, 159, and 160 accordingly (#287)

## [26.05.12.06.57] - 2026-05-12

### Added

- New menu item 173: `SitesByAPModelExporter.export_sites_by_ap_model` — prompts user to select an AP model from the models present in the organisation, then exports a CSV listing every site that contains APs of that model, including site name, site address, city, state, country, AP count, and individual AP MAC addresses. Uses mistapi's paginated fetch engine for parallel multi-page retrieval (#286)

## [26.05.11.00.00] - 2026-05-11

### Refactored

- Extract `FirmwareManager` class (2327 lines) to `src/firmware/firmware_manager.py` using dependency injection pattern consistent with `BulkAPFirmwareUpgrader`, `OrgLevelAPFirmwareUpgrader`, and other extracted firmware modules. MistHelper.py retains a 50-line thin wrapper (#203)

## [26.05.07.16.34] - 2026-05-07

### Fixed

- FR-001: Renamed `searchOrgBgpPeers` → `searchOrgBgpStats` (mistapi 0.62.0 function rename; line ~16191)
- FR-002: Renamed `searchOrgTunnels` → `searchOrgTunnelsStats` (mistapi 0.62.0 function rename; line ~16198)
- FR-003: Renamed `listOrgSitesStats` → `listOrgSiteStats` (mistapi 0.62.0 function rename; line ~16205)
- All three were confirmed `AttributeError` runtime crashes. No such function names exist in mistapi 0.62.0.

### Security

- FR-004: Attached `LogSanitizer` (mistapi `__logger`) to root logger at startup. Automatically redacts API tokens, passwords, and sensitive field values from all log output. Wrapped in `try/except ImportError` for backward compatibility with pre-0.59.3 mistapi.

### Added

- FR-005: Updated `requirements.txt` to `mistapi>=0.62.0` (was `>=0.61.4`)
- FR-006: New menu 166 — Export E911 Report (`getOrgE911Report`): exports organization E911 data to CSV
- FR-007: New menu 167 — Export JSI PBN Data (`searchOrgJsiPbn`): exports JSI Product Bulletin Notifications
- FR-008: New menu 168 — Export JSI SIRT Advisories (`searchOrgJsiSirt`): exports JSI Security Incident Response Team advisories
- FR-009: New menu 169 — Export Org OSPF Stats (`searchOrgOspfStats`): org-level OSPF adjacency statistics
- New menu 170 — Export Site OSPF Stats (`searchSiteOspfStats`): site-level OSPF adjacency statistics
- FR-010: New menu 171 — Export MxEdge Upgrade Status (`listSiteMxEdgeUpgrades`): site-level MxEdge firmware upgrade records
- FR-011: New menu 172 — Export Auto-Map Assignment Status (`getSiteAutoMapAssignmentStatus`): site auto-map assignment state
- Added `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries for all 5 new API endpoints: `getOrgE911Report`, `listSiteMxEdgeUpgrades`, `getSiteAutoMapAssignmentStatus` (new); `searchOrgOspfStats`, `searchSiteOspfStats` (already present, verified)

## [26.04.26.01.53] - 2026-04-26

### Added

- Bulk Org Data Collection (Menu 165): New external module `src/org_data_collector.py` with `OrgDataCollector` class. Executes 137 org-level read API calls (64 list, 36 search, 6 get, 31 count) in a single pass to populate ArangoDB, Redis, and SQLite backends. Covers admins, API tokens, licenses, SSO/SSO roles, device profiles, network templates, RF templates, site templates, AP templates, security policies/profiles (AAMW, AV, IDP, SecIntel), PSKs, webhooks, VPNs, EVPN topologies, WxLAN rules/tags/tunnels, MxEdge/MxEdge clusters/tunnels, NAC portals/rules/tags, assets/asset filters, alarm templates, site groups, services, service policies, certificates, guest authorizations, PSK portals, tickets, dashboards, SDK invites/templates, Marvis client invites, packet captures, JSI data, firmware versions/upgrades, and 31 count endpoints. Includes per-call error handling (skip on failure, continue with remaining), categorized progress display, pagination support for non-paginated APIs, and collection summary.
- 68 additional ENDPOINT_PRIMARY_KEY_STRATEGIES entries for all new org-level API endpoints (31 count endpoints as auto_increment, entity endpoints as natural_pk, event/search data as composite_pk).

### Fixed

- Fixed `OrgExportUtils.export_data()` to accept optional `limit` parameter (default 1000). When `limit=None`, the limit parameter is omitted from API calls, fixing failures on non-paginated endpoints that reject the `limit` argument.
- Removed 4 broken/parent-dependent operations from org data collector: `listOrgSsoLatestFailures` (requires sso_id), `listOrgNacPortalSsoLatestFailures` (requires nacportal_id), `searchOrgWebhooksDeliveries` (requires webhook_id), `listOrgJsiPastPurchases` (HTTP 400).

## [26.04.23.16.39] - 2026-04-23

### Added

- WAN Hub-Spoke VPN Builder (Menu 164): New external module `src/wan_vpn_builder.py` with `WanVpnBuilder` class. Fetches gateway device profiles, lets the user assign hub/spoke roles and pod values, auto-generates full-mesh hub paths and hub-spoke paths with cross-connects, previews the VPN payload, creates the VPN via API, and optionally writes port_vpn_paths back to each profile. Supports typed CREATE confirmation (FR-007). Includes 61 unit tests covering all pure logic, API helpers, prompts, and the full workflow.

## [26.04.22.20.38] - 2026-04-22

### Added

- WAN Hub Group Number Manager (Menu 163): New external module `src/wan_hub_group_manager.py` with `WanHubGroupNumberManager` class. Lists all gateway device profiles with current pod (group number) values from hub-spoke VPN paths, lets the user select a profile, then set pod (1-128) or clear to default (1). Batch updates all matching VPN paths across multiple VPN objects. Uses trailing-hyphen prefix matching to avoid false collisions (e.g., DC1- vs DC1-BACKUP-). Warns on inconsistent pod values. Follows external module pattern with `execute(apisession, get_org_id_func, safe_input_func)` static method. Includes 33 unit tests covering all four user stories.

## [26.04.22.20.38] - 2026-04-22

### Added

- WAN Hub Group Number Manager (Menu 163): New interactive operation to view, set, and clear pod (group_number) values on WAN hub profile VPN paths. First menu operation extracted into an external module under src/wan_hub_group_manager.py following dependency-injection pattern.
- 33 unit tests for WanHubGroupNumberManager covering profile fetching, path matching, pod set/clear, input validation, and module architecture.

## [26.04.20.20.23] - 2026-04-20

### Added

- Wired Client Manufacturer Report (Menu 162): New WiredClientManufacturerReportGenerator class fetches all org wired clients, displays indexed manufacturer summary with counts sorted by frequency, and lets the user select a manufacturer to export filtered records. Supports "export all" option. Uses existing searchOrgWiredClients API with limit=1000 and standard DataExporter CSV/SQLite output.

## [26.04.09.21.30] - 2026-04-09

### Compatibility Audit

- MistAPI compatibility audit alignment: raised the documented dependency floor to `mistapi>=0.61.4` and `websocket-client>=1.8.0`, updated the site client insights workflow to call `getSiteInsightMetricsForClient(..., metrics=metric)`, and added regression coverage for alarms, device-event pagination, site client stats, site SLE summaries, client insight metrics, and the E911 BSSID report.

## [26.04.08.18.41] - 2026-04-08

### Added

- SSID Template Consolidation (Menu 159): Complete rewrite as SSIDTemplateConsolidationManager with 5-phase guided workflow. Phase 1: read-only audit builds site-template-SSID matrix with cross-cluster deviation analysis. Phase 2: auto-detect site-specific deviations and write MISTHELPER_* site variables. Phase 3: create site groups by Mist Edge cluster affinity. Phase 4: build consolidated WLAN templates with Jinja variable references for deviations. Phase 5: disable old per-site SSIDs. Includes JSON cache/resume, CONFIRM gates on all write phases, and DataExporter dual CSV/SQLite output.

## [26.04.07.22.27] - 2026-04-07

### Fixed

- E911 BSSID Report (Menu 160): Fixed radio band and SSID resolution. Radio stats now fetched from site-level listSiteDevicesStats (not org-level which omits radio_stat). SSID resolution now uses full 3-source chain: site-level WLANs (listSiteWlans), site template WLANs (getOrgSiteTemplate wlans field), and org WLANs via WLAN template assignment (listOrgTemplates applies.site_ids/sitegroup_ids/org_id -> listOrgWlans filtered by template_id). Refactored _fetch_lookups into focused helpers: _fetch_org_wlan_templates, _fetch_org_wlans, _fetch_site_maps, _fetch_site_radio_stats, _resolve_site_ssids, _resolve_site_template_wlans, _get_assigned_template_ids, _add_wlans_to_band_lookup. Site lookup now stores sitegroup_ids and sitetemplate_id for template resolution.

## [26.04.07.22.13] - 2026-04-07

### Changed

- E911 BSSID Report (Menu 160): Enhanced with radio band details and SSID names. Now parses radio_stat from listOrgDevicesStats to resolve each radio MAC to its band (2.4/5/6 GHz), channel, and power. Fetches listSiteWlans per site to build band-to-SSID lookup, mapping WLAN band config (24/5/6/both) to radio bands. New CSV columns: AP MAC, Band, Radio MAC, Channel, Power, SSIDs on Band. Sort order updated to include Band. _fetch_lookups returns dict with radio_bands and wlan_bands lookups; _build_bssid_rows accepts consolidated lookups dict (2 params vs prior 4).

## [26.04.07.21.00] - 2026-04-07

### Added

- E911 BSSID Compliance Report (Menu 160): New E911BSSIDReportGenerator class queries all AP radio MACs via listOrgApsMacs, resolves site name/address via listOrgSites, AP name/site/map via listOrgDevicesStats(type=ap), floor names via listSiteMaps per site, derives 16 BSSIDs per radio MAC (last nibble 0x0-0xF), outputs sorted CSV (Site Name, Site Address, Map Name, AP Name, BSSID) with compliance gap detection for APs missing map assignments. Classified as safe in OperationRegistry for automated --test mode.

## [26.03.28.19.09] - 2026-03-28

### Added

- Offline Device Report (Menu 158): New OfflineDeviceReporter class scans entire org via listOrgDevicesStats (type=all, status=all), filters devices offline beyond user-configurable threshold (default 48h), resolves site names via lookup dict, displays summary stats (total devices, per-type breakdown, top 5 sites) + PrettyTable (max 50 rows), saves human-readable CSV with timestamped filename to data/. Classified as safe in OperationRegistry for automated --test mode.

## [26.03.20.22.31] - 2026-03-20

### Added

- Device Utility Commands: 35 new operations (menus 123-157) covering traceroute, OSPF diagnostics, session/service-path inspection, BGP/ARP/DHCP/802.1X/EVPN show commands, DNS resolution, live traffic monitoring, device locate, port bounce, cable test, reprovision/re-adopt, ZTP password retrieval, config command export, support file upload, 7 clear/reset operations, DHCP lease release, stats polling, and device snapshots
- DeviceUtilityCommands class: Uses mistapi SDK methods (not raw requests) with WebSocket result streaming, device-type validation, port selection from live stats, and three-tier destructive confirmation (none/y-N/typed keyword)
- 14 new ENDPOINT_PRIMARY_KEY_STRATEGIES entries for dual-output (CSV/SQLite) support on all device utility results

## [26.03.05.02.49] - 2026-03-05

### Added

- Web Portal: Flask-based browser interface on port 8055 (--web-portal CLI flag)
- Data Browser: Browse, search, preview, and download CSV/SQLite output files
- Operations: Run data extraction operations (menus 1-89) with real-time SSE progress
- Map Viewer: Interactive Plotly.js floor plan viewer with device markers
- Theme System: Dark, Light, and High Contrast themes with instant switching and localStorage persistence
- Portal Branding: Customizable title, logo, and accent color via ENV variables
- Container Integration: Dual-process startup (Gunicorn + sshd) on ports 8055 and 2200
- Security: CSP headers, CSRF protection, IP allowlist, path traversal guard

### Changed

- Replaced Dash dependency with Flask + Gunicorn for lighter footprint
- Updated Containerfile: EXPOSE 8055, COPY web_portal/, bundled vendor assets
- Updated compose.yml: Port 8055:8055 replaces 8050:8050, WEB_PORT env var
- Container start.sh: Dual-process with SIGTERM trap for clean shutdown

## [26.03.04.22.30] - 2026-03-04

### Changed

- God-class decomposition: All 95 classes now comply with 5-Item Rule (max 5 public methods per class)
- 13 non-compliant classes decomposed via rename-to-private and sub-class extraction
- GlobalImportManager: 13->5 pub (8 renamed private)
- RateLimitingUtils: 6->1 pub (5 renamed private)
- APIFetchUtils: 9->3 pub (extracted APICoreFetchUtils, APITenantFetchUtils)
- AddressUtils: 9->5 pub (4 renamed private)
- WebSocketCommands: 7->4 pub (extracted WebSocketNetworkDiagCommands)
- OrgExportUtils: 51->5 pub (12 renamed private, extracted 7 sub-classes: OrgSiteExporter, OrgInventoryExporter, OrgDeviceStatsExporter, OrgTemplateExporter, OrgClientSecurityExporter, OrgAdminExporter, OrgConfigExporter)
- MapsManager: 28->0 pub (all 28 renamed private - dead/internal-only code)
- EnhancedSSHRunner: 24->5 pub (19 renamed private)
- SiteExportUtils: 22->3 pub (3 renamed private, extracted 4 sub-classes: SiteDeviceExporter, SiteClientExporter, SiteConfigExporter, SiteAnomalyExporter)
- RoutingUtils: 16->3 pub (13 renamed private)
- PromptUtils: 12->5 pub (extracted PromptNetworkDeviceUtils, PromptClientUtils)
- GatewayExportUtils: 12->4 pub (3 renamed private, extracted GatewayTestExporter, GatewayStatsExporter)
- FirmwareManager: 10->4 pub (6 renamed private)
- 16 new sub-classes created following {Scope}{Domain}{Action} naming convention
- Zero functionality changes - all tests pass (49/49) after every decomposition

## [26.03.04.00.55] - 2026-03-04

### Changed

- Extract OrgAlarmEventExporter from OrgExportUtils (5-Item Rule compliance)
- New class contains 5 alarm/event methods: alarms(), alarm_templates(), events(), device_events(), device_events_52w()
- OrgExportUtils reduced from 56 to 51 methods; documented extraction pattern for future decomposition
- Consolidated redundant logging in alarms() (two start messages merged into one)

## [26.03.03.23.35] - 2026-03-03

### Changed

- Menu 122: Show ALL RADIUS WLANs including compliant ones marked '(COMPLIANT)' for full org visibility
- Menu 122: Accept 'q', 'quit', 'cancel', 'back' at selection prompt for safe exit without changes
- Menu 122: Respect --dry-run flag (preview without API calls, DRYRUN_ CSV prefix)
- Menu 122: Respect --debug flag (verbose API response and compliance evaluation logging)
- Menu 122: DRY-RUN and DEBUG mode banners displayed at startup when flags are active

## [26.03.03.22.27] - 2026-03-03

## [26.02.18.19.30] - 2026-02-18

### Added

- Menu 121: Site Inventory Health Analysis - Find sites with APs missing switches/gateways or with offline infrastructure
- Generates two reports: SitesMissingInfrastructure and SitesWithOfflineInfrastructure
- Uses org-level APIs for efficient bulk analysis across all sites

## [26.02.09.00.33] - 2026-02-09

### Changed

- Menu 120: Added engagement hours to standard configuration (all days set to empty string)
- Detects and clears custom operating hours (sun/mon/tue/wed/thu/fri/sat) to defaults

## [26.02.08.23.58] - 2026-02-08

### Changed

- Menu 120: Added WiFi settings to standard configuration (enabled=true, locate_connected=true, locate_unconnected=false)
- SiteAnalyticsConfigurator now checks and applies STANDARD_WIFI settings across all sites

## [26.02.08.23.46] - 2026-02-08

## [26.02.08.23.37] - 2026-02-08

## [26.02.08.23.28] - 2026-02-08

### Changed

- Menu 119: Extended to analyze engagement dwell tags (passerby/bounce/engaged/stationed time ranges)
- Menu 119: Extended to analyze engagement dwell tag custom names
- Menu 119: Extended to analyze occupancy settings (min_duration, clients_enabled, etc.)
- Menu 119: Extended to analyze analytics enabled/disabled status across sites
- Menu 119: Exports 5 CSV files: Summary, AllZones, ZoneFrequency, DwellConfigs, OccupancyConfigs

## [26.02.08.23.20] - 2026-02-08

## [26.02.05.00.25] - 2026-02-05

### Fixed

- Menu 116: Add full pagination support using mistapi.get_all()
- Menu 116: Inventory fetch now retrieves ALL APs (not just first 1000)
- Menu 116: Stats fetch now retrieves ALL device stats with pagination

## [26.02.05.00.20] - 2026-02-05

### Fixed

- Menu 116: Use listOrgAvailableDeviceVersions API (not getOrgDeviceUpgrade)
- Menu 116: Fix 'Unknown' firmware version display - match by MAC address
- Menu 116: Add limit=1000 to listOrgDevicesStats call for proper pagination

## [26.02.05.00.15] - 2026-02-05

### Fixed

- Menu 116: Use getOrgInventory API instead of listOrgDevices (listOrgDevices doesn't support type filter)
- Fixed 'listOrgDevices() got an unexpected keyword argument type' error

## [26.02.04.16.35] - 2026-02-04

### Changed

- Direct interactive login without org selection flow
- Proper inventory fetch with limit=1000 pagination

### Fixed

- Menu 117: Skip MSP/Org selection after login (exports ALL, not selected)
- Menu 117: Use getOrgInventory API instead of listOrgDevices for full inventory
- Fixed device count showing '1 (unknown:1)' for every org

## [26.02.04.16.20] - 2026-02-04

### Changed

- Menu 117: Auto-prompt for interactive login when MSP privileges missing
- No longer requires user to manually run --login or Menu 115 first
- Improved UX: offers to switch authentication in-place if needed

## [26.02.05.06.15] - 2026-02-05

### Changed

- Output includes MSP/Org/Site context columns for each device
- Device type breakdown summary (ap, switch, gateway counts)
- Site name lookup for user-friendly output
- Progress display showing org-by-org processing

## [26.02.05.05.45] - 2026-02-05

### Changed

- Site scope selection: 'All sites' or specific site selection
- Version selection per model with automatic grouping by target version
- Full upgrade strategy support (big_bang, serial, canary, rrm)
- Dry-run mode with --dry-run flag
- API efficiency display showing call savings vs site-level approach

## [26.02.05.04.35] - 2026-02-05

### Changed

- API call estimate now correctly counts unique versions per site
- Upgrade output shows version with list of models being upgraded

## [26.02.05.04.20] - 2026-02-05

### Changed

- Confirmation screen now shows total upgrade API calls
- Per-site breakdown shows device count and call reason
- Note about additional auto-upgrade API calls if step 9 is used

## [26.02.05.04.02] - 2026-02-05

### Changed

- MSP selection now supports selecting multiple MSPs in one workflow
- Organization selection per MSP with consistent selection patterns
- Site selection per org with configurable ranges and pagination
- Upgrade plan summary shows MSPs, orgs, and sites before confirmation
- Dry-run mode skips confirmation and shows simulation banner

## [26.02.05.03.18] - 2026-02-05

### Changed

- FirmwareManager now detects MSP privileges and shows mode [3] when available
- Sequential processing with per-org confirmation and interrupt handling
- Upgrade summary report showing completed/failed/interrupted organizations

## [26.02.02.23.15] - 2026-02-02

### Changed

- Session-based authentication with cookie management for MSP API endpoints
- Two-factor authentication (2FA) support in interactive login flow
- Cloud selection during interactive login (Global, EU, GovCloud, Custom)
- MSP organization export includes msp_id and msp_name context fields

## [26.02.02.21.06] - 2026-02-02

### Changed

- Family-based version selection: Select one version per ap_type family, applies to all models
- AP models grouped by ap_type from /api/v1/const/device_models (ruby, jewel, aphx, etc.)
- Universal version detection aggregates firmware compatibility across all API entries
- Semantic version sorting (0.14.x now correctly sorts above 0.8.x)
- Auto-upgrade scheduling: Added day_of_week and time_of_day options

## [26.01.28.19.03] - 2026-01-28

## [26.01.28.18.55] - 2026-01-28

## [26.01.28.18.51] - 2026-01-28

### Changed

- Menu 90 'All sites' mode: Now displays full site list before confirmation prompt
- AP Discovery Summary: Enhanced to show per-site model breakdown (e.g., 'Site-A: 12 APs (AP45:8, AP34:4)')
- Clarified that sites with no APs or all APs at target will be skipped

## [26.01.28.18.46] - 2026-01-28

## [26.01.28.18.40] - 2026-01-28

## [26.01.28.18.30] - 2026-01-28

## [26.01.18.02.10] - 2026-01-18

## [26.01.17.23.15] - 2026-01-17

## [26.01.17.23.00] - 2026-01-17

## [26.01.17.22.45] - 2026-01-17

## [26.01.17.22.30] - 2026-01-17

## [26.01.17.22.15] - 2026-01-17

## [26.01.17.22.00] - 2026-01-17

## [26.01.17.21.45] - 2026-01-17

## [26.01.17.21.30] - 2026-01-17

## [26.01.17.20.45] - 2026-01-17

## [26.01.17.19.30] - 2026-01-17

## [26.01.17.19.15] - 2026-01-17

## [26.01.17.18.30] - 2026-01-17

## [26.01.17.17.53] - 2026-01-17

## [26.01.17.17.24] - 2026-01-17

## [25.07.10.08.00] - 2025-07-10

## [25.07.10.07.25] - 2025-07-10

## [25.07.10.05.30] - 2025-07-10

## [25.07.10.05.15] - 2025-07-10

## [25.07.10.05.00] - 2025-07-10

## [25.07.09.23.25] - 2025-07-09

## [25.07.09.23.15] - 2025-07-09

## [25.07.09.23.00] - 2025-07-09

## [25.07.09.22.45] - 2025-07-09

## [25.07.09.22.15] - 2025-07-09

## [25.07.09.22.08] - 2025-07-09

## [25.07.09.22.00] - 2025-07-09

## [26.01.16.21.30] - 2026-01-16

## [26.01.16.21.00] - 2026-01-16

## [26.01.16.20.30] - 2026-01-16

## [26.01.16.20.00] - 2026-01-16

## [26.01.16.19.30] - 2026-01-16

## [26.01.16.19.15] - 2026-01-16

## [26.01.16.18.45] - 2026-01-16

## [26.01.16.05.30] - 2026-01-16

## [26.01.15.22.45] - 2026-01-15

### Documentation

- Updated interactive_fetch_device_data_to_csv docstring to support config object pattern

## [26.01.15.21.30] - 2026-01-15

## [26.01.16.00.15] - 2026-01-16

### Documentation

- Added dataclasses import and config classes section near top of MistHelper.py
- Updated function docstrings to mark individual parameters as deprecated in favor of config objects

## [26.01.15.23.56] - 2026-01-15

### Documentation

- Compliance audit: Applied copilot-instructions.md naming and ASCII guidelines

## [26.01.15.16.30] - 2026-01-15

## [26.01.12.16.41] - 2026-01-12

## [26.01.09.18.45] - 2026-01-09

## [26.01.09.17.30] - 2026-01-09

## [25.01.09.19.00] - 2025-01-09

## [26.01.08.15.32] - 2026-01-08

## [25.12.22.20.30] - 2025-12-22

## [25.12.22.19.54] - 2025-12-22

## [25.12.22.19.30] - 2025-12-22

## [25.12.22.18.00] - 2025-12-22

## [25.12.22.17.30] - 2025-12-22

## [25.12.22.13.45] - 2025-12-22

### Documentation

- Added Python 3.13 and mistapi 0.59+ requirements to copilot-instructions.md
- Added Runtime Requirements section to agents.md specifying Python 3.13+ and mistapi 0.59+

## [25.01.21.15.30] - 2025-01-21

### Documentation

- Added Data Directory Permissions section to README troubleshooting
- Updated agents.md with CRITICAL permission requirements in deployment pipeline
- Updated copilot-instructions.md with permission fix between image pull and container restart

## [25.12.15.14.45] - 2025-12-15

### Documentation

- README Section 1 - Updated operation count from 97 to 112 menu entries
- README Section 1 - Updated line count from 22k to 44k lines
- README Section 1 - Updated date to 2025-12-15
- README Section 3 - Removed non-existent run-misthelper.py from directory table
- README Section 6 - Added missing CLI flags: --dry-run, --tui, --testinteractive
- README Section 8 - Fixed menu 40-44 description to mention rogue client/AP detections
- README Section 8 - Added missing menu items 101 (TUI), 111 (Clone Templates), 112 (Maps Manager)
- README Section 14 - Updated container commands to use direct podman commands instead of run-misthelper.py

## [25.12.12.17.10] - 2025-12-12

## [25.12.12.17.03] - 2025-12-12

## [25.12.12.21.55] - 2025-12-12

### Changed

- Zone name input field appears when Zone mode is selected
- Clear All Drawings button with guidance to use eraser tool
- Success/error feedback messages for all save operations

## [25.12.12.21.50] - 2025-12-12

### Changed

- Added coordinate sample logging to verify refresh data
- Added warning log if Clients trace not found during refresh
- Removed visibility toggle override during refresh to preserve user settings

## [25.12.12.21.35] - 2025-12-12

### Changed

- Changed browser tab title from 'Dash' to 'MistHelper Map Viewer'

## [25.12.12.21.30] - 2025-12-12

### Changed

- Set update_title=None on Dash app to prevent tab title flicker from 1-second countdown interval

## [25.12.12.21.20] - 2025-12-12

### Changed

- Upgraded refresh trace logging from debug to info level for visibility

## [25.12.12.17.15] - 2025-12-12

### Changed

- Moved live refresh controls from sidebar to header bar for better visibility
- Added countdown timers showing seconds until next client refresh and minutes:seconds until RF heatmap refresh
- Countdown updates every second when auto-refresh is enabled
- Compact refresh control panel with dark background in header

## [25.12.12.16.45] - 2025-12-12

### Changed

- dcc.Store component: stores site_id, map_id, PPM, and map dimensions for refresh callbacks
- dcc.Interval components: two separate intervals for clients (30s) and coverage (5min) with disabled-by-default state
- Callback architecture: separate callbacks for toggle, client refresh, and coverage refresh with proper state management
- API session reference: refresh callbacks use stored API session for authenticated requests

## [25.12.12.15.35] - 2025-12-12

### Changed

- Explicit warning in console when map_ppm is 0 or missing

## [25.12.12.15.30] - 2025-12-12

### Changed

- Uses first 10 clients with both pixel and meter coordinates to calculate average PPM
- Logs PPM validation results (pass/mismatch) with exact values for debugging

## [25.12.12.14.30] - 2025-12-12

### Changed

- Added heatmap coordinate debug logging to script.log
- Logs coverage X/Y ranges in both pixels and meters for PPM validation

## [25.12.09.14.44] - 2025-12-09

### Documentation

- README and READY_FOR_MIGRATION license references now call out AGPL-3.0-only so downstream consumers see the correct terms immediately.

## [25.12.04.14.15] - 2025-12-04

### Changed

- Heatmap interpolation: zsmooth='best' provides smooth color transitions between grid points
- Gap interpolation: connectgaps=True fills in missing grid cells for complete coverage visualization
- Debug logging: added per-device orientation logging to script.log for troubleshooting
- Coordinate system fix: corrected AP orientation angle conversion (Mist 0°=north to math coordinates with Y-axis flip)

## [25.12.04.13.15] - 2025-12-04

### Changed

- RSSI tooltip: hover over grid cells shows Max RSSI and Avg RSSI in dBm
- Grid size calculation: coverage gridsize (meters) converted to pixels for proper visualization scale
- Error handling: graceful degradation when coverage API unavailable (backend database issues, no data)
- Backend error detection: psycopg2/database errors logged as warnings, not errors (expected transient issues)

## [25.12.04.13.07] - 2025-12-04

### Changed

- Device marker colors: dynamic color array based on individual device status instead of static type-based colors
- Crosshair orientation indicators: now use status-based colors matching device state
- Device labels: border colors match device status for consistent visual feedback
- Type-specific status colors: APs (green/red/orange), Switches (cyan/red/orange), Gateways (magenta/red/orange)

## [25.12.03.17.30] - 2025-12-03

### Changed

- Larger crosshair indicators: increased from 25px to 40px for better visibility of device orientation markers
- Larger orientation dots: increased from 10px to 16px with thicker lines (3px width) for improved visual clarity
- Increased dot distance: orientation direction indicator moved from 35px to 50px from device center
- Annotation toggle control: all text labels (zones, devices, clients, beacons) now hide/show with their parent layers
- Unified visibility management: annotations and traces both controlled by layer toggle callbacks

## [25.12.03.17.15] - 2025-12-03

### Changed

- Multi-checklist architecture: 5 separate checklists for granular layer management
- Client type detection: automatic WiFi/Wired classification based on SSID field presence
- Coverage radius calculation: dynamic radius based on vBeacon power level (-12 to +4 dBm range)
- Client-AP linking: automatic AP lookup by MAC address for association line drawing
- Mesh topology detection: automatic mesh uplink discovery from device mesh_uplink field
- Layer toggle callback: enhanced to handle multiple checklist inputs with combined layer array
- Map statistics: added vBeacon and BLE beacon counts to Map Info panel
- Add vBeacon/Beacon buttons: header toolbar buttons with green/cyan color coding

### Documentation

- Layer controls now match Mist portal Location Settings panel organization
- Client separation provides visual distinction between WiFi and Wired network access

## [25.12.03.16.47] - 2025-12-03

### Changed

- Auto-Zone UI: prominent purple button with robot emoji in header utilities bar
- Zone checklist: all zones checked by default, styled with dark theme
- Zone selection feedback: green highlighted text shows selected zone details
- Edit zone placeholder: guides to Mist API updateSiteMap for vertex modification
- Remove zone warning: red destructive warning for zone deletion operations
- Click handling: detects zone clicks from hovertext and displays zone information

### Documentation

- Added Location Zones panel matching Juniper Mist portal zone management interface
- Auto-Zone feature provides AI-powered automatic zone creation from wall analysis

## [25.12.03.16.44] - 2025-12-03

### Changed

- Drawing Tools UI: color-coded buttons matching element types (magenta/cyan/orange/red)
- Tool guidance: status messages direct users to appropriate toolbar drawing tools
- Destructive warnings: delete buttons highlighted in red with bold warnings
- Sidebar reorganization: Drawing Tools section above Measurement Tools for better workflow
- Compact layout: measurement tools condensed with smaller font for space efficiency

### Documentation

- Added Drawing Tools panel matching Juniper Mist portal map editor interface
- Quick-action buttons provide shortcuts and guidance for common map editing tasks

## [25.12.03.16.41] - 2025-12-03

### Changed

- Validation path styling: magenta color (#ff00ff) with dotted line style for clear differentiation
- Hover information: shows path name and point count on mouseover
- Path naming: displays custom path names or defaults to 'Path 1', 'Path 2', etc.
- Coordinate processing: extracts x,y from path coordinate arrays with validation
- Logging integration: debug messages for path rendering with point counts

### Documentation

- Added validation paths feature matching Juniper Mist portal site survey path capability
- Validation paths used for Wi-Fi coverage testing and performance analysis along routes

## [25.12.03.16.39] - 2025-12-03

### Changed

- Utilities UI redesign: replaced dropdown with horizontal button bar for cleaner interface
- Direct action buttons: Change Image, Remove Image, Rename, Delete as individual buttons in header
- Visual hierarchy: Delete button highlighted in red (#ff4444) for critical action awareness
- Improved spacing: buttons in header bar with inline status messages
- Darker header: #2a2a2a background for better contrast with map area

## [25.12.03.16.38] - 2025-12-03

### Changed

- Utilities UI: dropdown positioned in header top-right matching Mist portal layout
- Action feedback: status messages display warnings for destructive operations
- Color coding: orange for caution (change/rename), red for destructive (remove/delete)
- Logging integration: all utility actions logged with map_id for audit trail
- Header redesign: title and utilities dropdown in flex layout with purple border separator

### Documentation

- Added Utilities dropdown matching Juniper Mist portal map management interface
- Placeholder implementations note required API integrations for full functionality

## [25.12.03.16.35] - 2025-12-03

### Changed

- Set Origin UI: toggle button with mode indicator in sidebar Tools section
- Visual feedback: button highlights in purple when origin-setting mode is active
- Status display: shows current origin coordinates and confirmation when set
- Origin initialization: loads existing origin_x/origin_y from map data if present
- Interactive workflow: click button to activate, click map to set, click button again to exit mode

### Documentation

- Added Set Origin feature matching Juniper Mist portal coordinate system alignment capability

## [25.12.03.16.32] - 2025-12-03

### Changed

- Set Scale UI: input field for length in meters + button in sidebar Tools section
- Workflow guidance: numbered steps (1. Draw line, 2. Enter length) for clear user instructions
- Dynamic PPM: measurement callback reads current PPM from figure metadata instead of static value
- Scale validation: prevents setting scale with invalid/missing length or without drawn line
- Professional styling: scale input and button match dark theme with purple accent (#667eea)

### Documentation

- Added Set Scale feature matching Juniper Mist portal UI/UX for floor plan calibration

## [25.12.03.16.30] - 2025-12-03

### Changed

- Map viewer rotation indicators: replaced triangular wedges with Mist-style crosshair + directional dot
- Crosshair: 25px horizontal and vertical lines at device center (always visible)
- Directional dot: 10px marker positioned 35px from center at orientation angle (only if angle != 0)
- Crosshair color matches device type (green for APs, orange for switches, magenta for gateways)
- Dot shows orientation angle on hover for quick reference

### Documentation

- Updated rotation indicator design to match Juniper Mist portal UI/UX patterns

## [25.12.03.16.22] - 2025-12-03

### Changed

- Map viewer text rendering: switched from mode='markers+text' to mode='markers' + separate annotations
- Annotation-based labels: support bgcolor, bordercolor, borderwidth, and borderpad for professional appearance
- Device labels: positioned 15px above markers with device-type-specific colored borders (green/orange/magenta)
- Client labels: positioned 10px above markers with smaller font and green styling
- Zone labels: automatically positioned at min(x), min(y) coordinates (upper-left bounding box corner)
- Improved label positioning: all labels use xanchor/yanchor for precise placement without overlap

### Documentation

- Added technical note in CSS explaining why text-shadow doesn't work on Plotly SVG elements
- Removed obsolete text-shadow CSS rules that had no effect on map labels

## [25.12.02.20.30] - 2025-12-02

### Changed

- Clone operation uses temporary files for image download/upload to avoid filesystem pollution
- Automatic cleanup of temporary files in all code paths (success, failure, exception)
- Enhanced error handling with separate warnings for download vs upload failures
- User-friendly progress messages at each stage: select, download, create, upload, complete
- Clone confirmation shows full plan before execution including image copy status
- Educational note: zones are site-level objects (not map objects) requiring separate cloning

### Documentation

- Added comprehensive docstring explaining full clone capability including image/walls/paths/zones
- Clone summary clearly shows which elements were successfully copied

## [25.12.02.18.00] - 2025-12-02

### Changed

- Database schema - Added natural primary key strategies for listSiteMaps and getSiteMap with proper indexes
- Interactive sub-menu - Single entry point (Menu 112) with 0 to return to main menu, organized by operation category
- Safety features - Input validation, EOF/interrupt handling, confirmation prompts for destructive operations (placeholders)
- Image handling - JWT token URL support, automatic format detection (png/jpg), organized directory structure by site
- Progress indicators - tqdm progress bars for bulk site/map operations with descriptive labels
- Error handling - Graceful per-site error logging without halting bulk operations, comprehensive exception tracking

### Documentation

- Updated operation count from 111 to 112 total menu entries
- Added Maps Manager category section to menu_actions documentation
- Documented map database strategies in ENDPOINT_PRIMARY_KEY_STRATEGIES configuration

## [25.12.02.17.15] - 2025-12-02

### Documentation

- Updated agents.md Git workflow - clarified that staging alone does not create checkpoints
- Added minimal Git workflow instructions for local commits and rollback procedures
- Removed verbose workflow examples, keeping only essential commands for AI agents

## [25.12.02.16.43] - 2025-12-02

### Documentation

- Added detailed docstrings for clone_gateway_templates_by_state_and_country() explaining address parsing logic
- Documented support for US, CA, MX, CR, PA, HN, GT, and other Central American address formats
- Updated menu option tables with entry 111 for gateway template cloning by geography
- Documented --testinteractive and --dry-run CLI flag usage in help text
- Noted limitations: Multi-word state names (e.g., 'Quintana Roo') may capture last word only

## [25.12.02.11.10] - 2025-12-02

### Documentation

- Added code comments explaining mistapi's expectation of comma-separated token string
- Documented that mistapi handles token rotation internally when configured correctly

## [25.12.02.11.05] - 2025-12-02

## [25.12.02.11.15] - 2025-12-02

### Documentation

- Identified that error occurs when mistapi library validates tokens against Mist API
- Token validation failure suggests tokens need to be refreshed or regenerated
- mistapi library bug: does not handle missing 'privileges' key in API response gracefully

## [25.12.02.11.00] - 2025-12-02

## [25.12.01.17.40] - 2025-12-01

### Changed

- Menu 14 (fast mode): Added extensive debug logging to track data type issues in parallel processing
- Added type validation logging for start_time, end_time, and duration calculations
- Added logging for successful_results and failed_sites return types from execute_with_connection_pool_management
- Added per-result type checking in flattening loop with warnings for unexpected types
- Added site tuple structure validation logging to diagnose dict vs tuple issues

## [25.12.01.17.35] - 2025-12-01

## [25.12.01.17.30] - 2025-12-01

## [25.12.01.17.20] - 2025-12-01

### Changed

- Enhanced error handling in fetch_and_display_api_data with three-layer defense against data loss
- Added response structure validation and logging for debugging unexpected API formats
- Automatic recovery attempts from alternate response structures (response.data['data'], direct lists)
- User-friendly messages explain partial data saves and recovery attempts
- Detailed debug logs capture response types and available keys for troubleshooting

### Documentation

- Updated export_device_port_stats_to_csv docstring with performance optimization notes
- Added fetch_and_display_api_data docstring explaining enhanced error handling layers
- Documented safety features: emergency saves, structure validation, graceful degradation

## [25.11.25.13.49] - 2025-11-25

## [25.11.25.13.40] - 2025-11-25

### Changed

- Pre-flight analysis shows assignment plan before execution
- Exports successful assignments to SuccessfulAPProfileAssignments.csv with AP/profile details
- Exports failed assignments to FailedAPProfileAssignments.csv for troubleshooting
- Exports skipped APs to SkippedAPsNoMatchingProfile.csv for profile creation planning
- Comprehensive summary report showing successful, failed, and skipped counts
- Detailed logging for each AP assignment with full error context
- Gracefully skips APs without model information instead of failing

### Documentation

- Menu 110 marked as DESTRUCTIVE operation requiring 'ASSIGN' confirmation
- Pre-assignment analysis shows counts of APs with/without matching profiles
- Operation count updated from 110 to 111 total menu operations
- Lists APs that will be skipped due to missing matching Device Profiles

### Security

- Requires explicit uppercase 'ASSIGN' confirmation before device assignment
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.3s delay between AP assignments

## [25.11.25.13.23] - 2025-11-25

### Changed

- Progress display shows unique AP models discovered across organization
- Exports successful creations to CreatedAPModelDeviceProfiles.csv with model/profile/ID details
- Exports failures to FailedAPModelDeviceProfiles.csv for troubleshooting
- Comprehensive summary report showing profiles created, failed, and skipped (existing)
- Detailed logging for each profile creation with full error context
- Warns about devices with missing model information for inventory visibility

### Documentation

- Menu 109 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation
- Device Profiles created with minimal payload to ensure all settings inherit/auto by default
- Operation count updated from 109 to 110 total menu operations
- Devices without model information are logged and reported but do not block execution

### Security

- Requires explicit uppercase 'CREATE' confirmation before profile creation
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.5s delay between Device Profile creations

## [25.11.25.12.28] - 2025-11-25

### Changed

- Progress display shows country distribution and site counts per country
- Exports successful assignments to SuccessfulRFTemplateAssignments.csv with site/template details
- Exports failures to FailedRFTemplateAssignments.csv for troubleshooting
- Comprehensive summary report showing templates created, sites assigned, failures, and skipped sites
- Detailed logging for each template creation and site assignment with full error context
- Template reuse logic - skips creation if RF-{country} template already exists

### Documentation

- Menu 108 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation
- RF template configuration uses default/auto settings: band_24 (20MHz auto), band_5 (40MHz auto), band_6 (80MHz auto)
- Operation count updated from 108 to 109 total menu operations
- Sites without country codes are skipped with warning message and logged

### Security

- Requires explicit uppercase 'CREATE' confirmation before template creation and site assignment
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.5s delay between template creations and 0.3s between site assignments

## [25.11.25.14.30] - 2025-11-25

### Changed

- Progress display shows site creation status with index counter
- Exports successful creations to CreatedTestSites.csv with site IDs
- Exports failures to FailedTestSites.csv for troubleshooting
- Comprehensive summary report showing total/success/failure counts
- Detailed logging for each site creation attempt with full error context

### Documentation

- Menu 107 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation
- CSV structure documented: name (required), address, country_code, lat, lng, timezone, notes
- Operation count updated from 107 to 108 total menu operations

### Security

- Requires explicit uppercase 'CREATE' confirmation before execution
- Safe input handling with EOF protection for container environments
- Rate limiting with 0.5s delay between site creations to avoid API throttling

## [25.11.25.09.30] - 2025-11-25

### Documentation

- Menu 25: Updated function docstring to document all three output files (weekly, summary, master)

## [25.11.21.17.00] - 2025-11-21

## [25.11.13.16.15] - 2025-11-13

### Documentation

- Menu 104: Updated docstring explains device override preservation critical safety feature
- Menu 104: Console output clearly shows two-phase migration: templates then device overrides
- Menu 104: Explains risk of static IP loss without device override migration

## [25.11.13.15.45] - 2025-11-13

## [25.11.13.14.30] - 2025-11-13

### Documentation

- Menu 103: CRITICAL overrides (DHCP->Static) clearly flagged for manual review priority
- Menu 103: User guidance explains static IPs will be lost if template DHCP applied without device overrides
- Menu 103: Console output shows breakdown of override severity levels with actionable next steps

## [25.10.30.17.50] - 2025-10-30

## [25.10.30.19.50] - 2025-10-30

## [25.10.29.13.55] - 2025-10-29

## [25.10.29.00.15] - 2025-10-29

### Changed

- Converted remaining progress messages to logging (only user-facing data remains as print)
- Debug logs now show template assignment determination before WLAN fetching
- Added logging for org WLAN filtering process with template_id matching

### Documentation

- Clarified architecture: WLAN templates are configuration containers, not WLAN collections
- Org WLANs exist independently and optionally reference templates for config inheritance
- Templates define what configuration to apply; WLANs reference them via template_id

## [25.10.28.23.15] - 2025-10-28

### Changed

- Debug output written to log file instead of console for cleaner user experience
- Detailed logging shows applies.site_ids, applies.sitegroup_ids, applies.wxtag_ids, applies.org_id
- Shows WLAN structure type (list vs dict) and WLAN count per template in debug logs

## [25.10.28.22.30] - 2025-10-28

### Documentation

- Site Templates (/sitetemplates): Full site configs with embedded WLANs
- WLAN Templates (/templates): WLAN-specific templates assignable to sites
- Org WLANs (/wlans): Standalone org-level WLANs (not template-based)

## [25.10.28.22.09] - 2025-10-28

## [25.10.28.21.00] - 2025-10-28

### Changed

- Enhanced WLAN inheritance detection across three levels: site, site_template, org_template
- Org WLAN template modifications now show clear impact scope (which sites affected)
- Improved warning messages distinguish between site template and org template changes
- API routing automatically selects correct update endpoint based on WLAN source level

## [25.10.21.15.00] - 2025-10-21

### Changed

- Results grid uses Rich Table with DOUBLE box style for prominence
- Columns auto-detected from first result item keys
- Scroll position tracked with results_scroll_offset state variable
- Help text dynamically shows grid controls when viewing results
- Grid appears automatically after successful API call with tabular data
- Execution state now includes 'viewing_results' for grid display mode

## [25.10.21.14.55] - 2025-10-21

### Changed

- Parameter submission logic clarified with explicit handling for required vs optional
- Debug logging differentiates between 'stored' and 'skipped' parameters
- API calls now only include parameters explicitly provided by user or auto-filled from .env

## [25.10.21.14.50] - 2025-10-21

### Changed

- Debug JSON files now include both raw_response (complete) and parsed_data (extracted)
- Object introspection via dir() and getattr() captures all non-private attributes
- Handles nested objects recursively to preserve full response hierarchy
- Graceful fallback to string representation for non-serializable types

## [25.10.21.14.45] - 2025-10-21

### Changed

- Results show structure depth with indentation (dict keys, list items, nested objects)
- Dictionary items display with type and count header (e.g., 'results: dict (5 keys)')
- List items show count and preview first N items with key-value pairs
- Nested structures recursively formatted up to 3 levels deep
- Sample item display shows first 3 key-value pairs per dict in list
- Value strings truncated to 60 chars in nested views, 200 chars at top level

## [25.10.21.14.30] - 2025-10-21

## [25.10.21.12.18] - 2025-10-21

### Changed

- Improved result display - shows sample keys and values for dict items in lists
- Better preview formatting - displays first 3 items with key-value pairs for API results
- Result metadata - shows function name, parameters (redacted), timestamp, and parsed data structure
- Debug file notifications - output panel shows where debug results were saved
- Tip messages - suggests viewing debug logs for large datasets

## [25.10.21.12.12] - 2025-10-21

### Changed

- Parameter prompts now display in prominent input boxes with clear headers
- Box-style input prompts show parameter name, requirement status, and default value
- Current input highlighted with white-on-gray background for visibility
- Previously entered parameters shown below with checkmarks
- Progress indicator shows N/M parameters completed
- Visual hierarchy: Current prompt (bold yellow box) → Previous inputs (dim with checkmarks)

## [25.10.21.12.09] - 2025-10-21

### Changed

- TUI stays active during function execution - no screen clearing or context switches
- Output panel shows execution progress (prompting → executing → completed)
- Previously entered parameters visible while prompting for next parameter
- Backspace support for editing input inline
- Escape cancels execution and returns to navigation mode
- Help text changes based on mode (navigation vs input)
- Smart result formatting in output panel (type, count, preview)
- Input mode clearly indicated with magenta Output panel border

## [25.10.21.12.04] - 2025-10-21

### Changed

- TUI now automatically uses values from .env file for function parameters
- Parameters like org_id, site_id, device_id automatically filled from environment variables
- No need to manually enter org_id when executing functions if configured in .env
- Environment values displayed with [from .env] indicator for transparency

## [25.10.21.11.58] - 2025-10-21

### Changed

- Function execution no longer interferes with TUI display refresh cycle
- Ctrl+C during execution properly returns to TUI without freezing
- Terminal mode properly managed across Live() context transitions

## [25.10.21.11.52] - 2025-10-21

### Changed

- Smart result preview system - shows type, count, and sample items without converting entire result to string
- Lists/tuples: Shows item count and first 3 items with truncation indicators
- Dicts: Shows key count and first 5 keys for large dictionaries
- Strings: Truncates at 200 characters with length indicator
- Memory-safe handling: Never converts full result to string, uses repr() with limits
- Helpful tip displayed for large results (>10 items) suggesting use of main menu CSV/SQLite export options

### Security

- Result preview limits prevent memory exhaustion attacks from malformed API responses
- Safe repr() usage with character limits prevents infinite recursion or excessive memory use

## [25.10.21.11.49] - 2025-10-21

### Changed

- Added intelligent viewport scrolling - visible window follows cursor through item list
- Viewport height automatically calculated based on available panel height (minus borders)
- Selection stays centered in viewport when possible, adjusts near top/bottom boundaries
- Debug logging for viewport calculations when --debug flag is set (selection position, scroll range, visible items)

## [25.10.21.11.43] - 2025-10-21

## [25.10.21.17.30] - 2025-10-21

### Changed

- MistHelperTUI class redesigned with hierarchical navigation state (current_path, breadcrumb)
- Dynamic discovery using Python inspect and importlib for package introspection
- Parameter prompting system with required/optional detection and default value support
- Result display with formatted preview and error handling
- Automatic apisession initialization and injection for API call execution
- Drill-down navigation (Enter on modules) and back navigation (Escape key)
- Real-time function signature and documentation display
- Educational design - learn API structure by exploring

## [25.10.14.17.00] - 2025-10-14

### Fixed

- Downloads now complete reliably without threading complexity

### Removed

- Queue-based background downloader (replaced with simpler synchronous approach)

## [25.10.07.16.15] - 2025-10-07

### Fixed

- Wired client API module - Corrected import path to mistapi.api.v1.sites.wired_clients (separate module from wireless clients)
- AttributeError on wired client fetch - Resolved 'module has no attribute searchSiteWiredClients' error
- Verified: Wireless clients use mistapi.api.v1.sites.clients.searchSiteWirelessClients
- Verified: Wired clients use mistapi.api.v1.sites.wired_clients.searchSiteWiredClients

## [25.10.06.18.30] - 2025-10-06

### Fixed

- Corrected session attribute in PCAP polling functions
- Site PCAP polling used self.apisession instead of self.mist_session (PacketCaptureManager attribute)
- Org PCAP polling used self.apisession instead of self.mist_session (PacketCaptureManager attribute)
- Changed self.apisession to self.mist_session in _wait_and_download_pcap() (line 4072)
- Changed self.apisession to self.mist_session in _wait_and_download_pcap_org() (line 4212)
- PCAP downloads now work correctly - polling no longer throws AttributeError
- Root cause: PacketCaptureManager.__init__ stores session as self.mist_session, not self.apisession

## [25.10.06.18.25] - 2025-10-06

### Changed

- Added comprehensive debug logging to PCAP download polling functions
- Site-level PCAP polling now logs every poll attempt with detailed capture state
- Org-level PCAP polling now logs every poll attempt with detailed capture state
- Logs response status code, number of captures returned, and capture found/not found status
- When capture found, logs all relevant fields: enabled, format, type, duration, expiry, timestamp, pcap_url
- Logs when pcap_url is NOT SET YET vs when it becomes available
- Logs available capture IDs when our capture is not found in the list
- Exception handling now uses exc_info=True for full traceback in logs
- Debug logs will reveal why PCAP downloads timeout (capture not found, pcap_url never set, API errors)
- Run with --debug flag to see detailed polling behavior in script.log

## [25.10.06.18.20] - 2025-10-06

### Fixed

- Corrected mistapi function names for listing packet captures
- Changed listSitePcapCaptures to correct listSitePacketCaptures (3 occurrences)
- Changed listOrgPcapCaptures to correct listOrgPacketCaptures (1 occurrence)
- Previous function names caused AttributeError when checking for existing captures
- Pre-check for existing captures now works correctly before launching new ones
- Locations: Single AP pre-check, multi-AP pre-check, site PCAP polling, org PCAP polling
- Function names now match mistapi SDK and Mist API operationId values
- operationId: listSitePacketCaptures and listOrgPacketCaptures per OpenAPI spec
