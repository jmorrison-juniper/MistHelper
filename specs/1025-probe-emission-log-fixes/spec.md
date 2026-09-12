# Feature Specification: Menu 206 Probe-Emission Log Quality & Correctness Fixes

**Feature Branch**: `1025-probe-emission-log-fixes`

**Created**: 2026-07-26

**Status**: Implemented and merged in pull request #1674. Issues #1667 and #1668 are resolved. Task T039 stays open, because it needs a live organization.

**Input**: User description: "Menu 206 probe-emission log quality & correctness fixes. Two issues surfaced during a post-1024 log review: (1) CENR probe-population gap for SecB2B b2c/gslb hosts causing ~1,261 duplicate WARNINGs per menu 206 run on a ~315-site org; (2) `_COUNTRY_CODE_TO_REGION` missing LATAM/Caribbean codes, causing Central America / Caribbean sites to be mislabeled as `emea` and emitting per-site WARNINGs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Silence the CENR duplicate-warning storm (Priority: P1)

An operator runs menu 206 (`manage_org_synthetic_probes`) against a large org (~315 sites) that has SecB2B b2c/gslb probe hosts in its dispatch catalogue. Today the operator sees ~1,261 near-identical WARNING lines in `data/script.log` — one per site, per host, for each of ~4 hosts the Central ENR observation cache (CENR) does not have an observed URL for. The warnings drown out genuinely-actionable log lines and force the operator to grep past thousands of duplicates when triaging a run.

After this change, the same run emits at most one WARNING per unique missing CENR host (a set typically bounded by the number of catalogue-declared hosts, single-digit in practice), logged once at cache/map load time rather than at every per-site emission. Probe payloads themselves are unchanged — the catalogue's default `https://<host>` fallback URL is still applied, and every probe still executes correctly.

**Why this priority**: This is the loudest symptom operators see; every menu 206 run on a large org today generates ~1,261 duplicate warnings that make the log effectively unreadable. Fixing it unblocks real diagnostic use of `data/script.log` during menu 206 triage.

**Independent Test**: Run menu 206 against a fixture org whose CENR cache is missing observations for the 7 known SecB2B hosts (`gslb.secb2b.com`, `us-elm.secb2b.com`, `us-prod-klm-b2c.secb2b.com`, `us-prod-klm.secb2b.com`, `eu-elm.secb2b.com`, `eu-prod-klm-b2c.secb2b.com`, `eu-prod-klm.secb2b.com`) across 315 simulated sites. Assert that the log contains at most `N` "missing CENR observation" WARNINGs where `N == len(unique_missing_hosts)` (≤7 in the fixture), not `N × site_count`. Assert the emitted probe payloads are byte-identical to the pre-change baseline captured for the same fixture.

**Acceptance Scenarios**:

1. **Given** a fixture org with 315 sites and a CENR cache missing observations for 7 SecB2B hosts, **When** menu 206 runs to emission completion, **Then** the log contains exactly 7 "missing CENR observation" WARNING records (one per unique host), not ~1,261.
2. **Given** the same fixture, **When** the emitted probe payloads are diffed against the pre-change baseline for every non-VPN probe target, **Then** the diff is empty (byte-for-byte identical).
3. **Given** a fixture org where CENR *does* have observations for every catalogue host, **When** menu 206 runs, **Then** zero "missing CENR observation" WARNINGs are emitted.
4. **Given** a fixture where a previously-observed CENR host later drops out of the cache, **When** menu 206 runs, **Then** the WARNING for that host is emitted exactly once (not per-site).

---

### User Story 2 - Correctly region-classify LATAM & Caribbean sites (Priority: P1)

An operator runs menu 206 against an org that includes Mist sites in Panama, Bahamas, Haiti, Dominican Republic, Guatemala, Cuba, Costa Rica, or Honduras. Today those sites' `country_code` values are absent from `_COUNTRY_CODE_TO_REGION`, so they silently default to the `emea` region label. This is wrong (Central America / Caribbean belong under the `"americas"` Zscaler region — the canonical literal per `research.md` R1; the shorthand "amer" is used colloquially but never in code) and each unmapped site emits a per-site WARNING adding to the log-noise storm. Probes still succeed via nearest-2-global-ZEN geodesic fallback, so this hasn't broken anything user-visible — but any downstream logic keyed off `region` will be incorrect, and the log-noise compounds Issue #1.

After this change, all ISO-3166 alpha-2 country codes that can plausibly appear as a Mist site `country_code` are covered — either by an explicit region mapping, or by an explicit intentional-gap marker (documented in-source with rationale) — and a regression test asserts full ISO coverage so silent additions cannot slip in. Central America / Caribbean codes specifically map to `"americas"`. Per-site "unknown country code" WARNINGs are replaced by a single load-time WARNING listing any codes present in the loaded site set that resolve to the intentional-gap marker.

**Why this priority**: Correctness of region labeling matters for any current or future logic keyed off `region` (dashboards, telemetry aggregation, geodesic fallback pre-filtering). Combined with US1 this eliminates the two documented log-noise sources for menu 206.

**Independent Test**: Run menu 206 against a fixture org containing at least one site each in PA, BS, HT, DO, GT, CU, CR, HN. Assert the resolved region for each such site is `"americas"`, not `emea`. Assert exactly zero "unknown country code" WARNINGs are emitted for those codes. Separately, run a unit test that iterates every ISO-3166 alpha-2 code and asserts either an explicit region mapping or an explicit gap marker exists for each.

**Acceptance Scenarios**:

1. **Given** a fixture org with sites in PA, BS, HT, DO, GT, CU, CR, HN, **When** menu 206 resolves each site's region, **Then** every one of those sites resolves to `"americas"`.
2. **Given** the same fixture, **When** menu 206 runs to emission completion, **Then** zero per-site "unknown country code" WARNINGs are emitted for the 8 covered codes.
3. **Given** the `_COUNTRY_CODE_TO_REGION` map and the intentional-gap marker set, **When** a regression test iterates every ISO-3166 alpha-2 country code, **Then** every code is present in exactly one of the two collections.
4. **Given** a hypothetical future site with a country_code that is *not* in either the region map or the intentional-gap set, **When** menu 206 loads that site, **Then** a single load-time WARNING is emitted naming the unmapped code (and the CI regression test would have flagged the omission before merge).

---

### User Story 3 - Fixture-backed regression coverage for both log-noise sources (Priority: P2)

A future contributor modifies emission logic without realising the log-noise pattern has been fixed. Today there is no test that would fail if a warning were reintroduced at the per-site-per-host emission site or per-site country-code resolution site. This story adds fixture-backed tests that capture the *log record count* (not just probe payload content) for a representative fixture org, so any regression producing >K warnings per run for a fixed K fails CI.

**Why this priority**: Without the guard, US1 and US2 wins are one refactor away from regressing. The tests are cheap (fixture already exists for probe payload byte-stability from 1024) and give durable protection.

**Independent Test**: Delete the log-deduplication code paths introduced by US1/US2 on a scratch branch, re-run the new regression tests, and confirm they fail with a clear diagnostic naming the count that exceeded threshold.

**Acceptance Scenarios**:

1. **Given** the fixture from US1, **When** the regression test runs menu 206 and counts "missing CENR observation" WARNINGs, **Then** the count is asserted `<= unique_missing_hosts_count` and the test fails with a diagnostic including the observed count if exceeded.
2. **Given** the fixture from US2, **When** the regression test runs menu 206 and counts "unknown country code" WARNINGs, **Then** the count is asserted `<= unique_unmapped_codes_count` and the test fails with a diagnostic if exceeded.
3. **Given** an ISO alpha-2 coverage test, **When** run in CI on any branch, **Then** absence of an ISO code from both `_COUNTRY_CODE_TO_REGION` and the intentional-gap set fails the test with a diagnostic naming the missing code(s).

---

### Edge Cases

- **CENR cache is completely empty (e.g., first-run before any observation ingest)**: The catalogue-declared host set is the effective "missing" set. Load-time WARNING lists every catalogue host once. No per-site duplication.
- **CENR cache gains an observation for a host mid-scope (between site iterations within one run)**: Deduplication is scoped to the run's initial "missing set" snapshot taken at cache load; a host that becomes observed mid-run is simply not re-warned. Byte-stability of already-emitted probes is preserved.
- **A country code appears in the intentional-gap set AND in `_COUNTRY_CODE_TO_REGION`**: The coverage regression test fails with a "double-declared code" diagnostic; the two sets must be disjoint.
- **A site's `country_code` field is missing, empty string, or non-string**: Handled by existing pre-1025 behavior (unchanged). This spec does not modify null-country handling.
- **A run touches zero SecB2B / LATAM sites**: Zero WARNINGs of either flavor emitted (no regression from today's baseline for orgs that don't trigger the issue).
- **Operator runs menu 206 twice in the same session**: Load-time WARNINGs re-emit on the second run (cache/map are re-loaded per invocation); still O(unique-missing) per run, not O(sites × hosts).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CENR-fallback WARNING for a host with no observed URL MUST be emitted at most once per menu 206 run, regardless of how many sites reference that host. Deduplication scope is a single run of `manage_org_synthetic_probes`.
- **FR-002**: The CENR-fallback WARNING MUST be emitted at cache/map load time (or the earliest deterministic point after the missing-host set is known), NOT at per-site emission time.
- **FR-003**: The catalogue-default fallback URL behavior (`https://<host>`) MUST remain unchanged; probes still emit and still function correctly when CENR has no observation.
- **FR-004**: The "unknown country code" WARNING for a site whose `country_code` is not in `_COUNTRY_CODE_TO_REGION` MUST be emitted at most once per unique unmapped code per run, NOT per site.
- **FR-005**: `_COUNTRY_CODE_TO_REGION` MUST include entries for at minimum: PA, BS, HT, DO, GT, CU, CR, HN, mapped to `"americas"` (the Zscaler literal per `research.md` R1; colloquially "amer").
- **FR-006**: `_COUNTRY_CODE_TO_REGION` SHOULD be extended to cover the full Latin America and Caribbean subset of ISO-3166 alpha-2 codes that can plausibly appear as a Mist site `country_code`, all mapped to `"americas"` unless a specific country's Zscaler PoP topology dictates otherwise.
- **FR-007**: An intentional-gap set (or equivalent explicit marker mechanism) MUST exist for ISO alpha-2 codes that are deliberately excluded from region mapping (e.g., codes for uninhabited territories, codes for which no Mist site can plausibly exist, or codes deliberately routed via geodesic fallback only). Each entry MUST have an inline comment explaining why.
- **FR-008**: A regression test MUST iterate every ISO-3166 alpha-2 country code and assert that each code is present in exactly one of `_COUNTRY_CODE_TO_REGION` or the intentional-gap set (the two sets MUST be disjoint AND their union MUST cover all valid ISO alpha-2 codes).
- **FR-009**: A regression test MUST assert that for a fixture org with N sites where M unique CENR hosts are unobserved, the count of "missing CENR observation" WARNINGs emitted is `<= M`, not `N × M`.
- **FR-010**: A regression test MUST assert that for a fixture org with N sites in K unique unmapped countries, the count of "unknown country code" WARNINGs is `<= K`, not `<= N`.
- **FR-011**: All emitted probe payloads for non-VPN targets MUST remain byte-identical to the pre-change baseline (INV-1 from spec 1024). An existing or new fixture-comparison test MUST assert this.
- **FR-012**: Deduplication state (the set of missing hosts already warned about, the set of unmapped country codes already warned about) MUST NOT persist across runs — each invocation of `manage_org_synthetic_probes` starts with an empty dedup set. This preserves signal: a genuinely-new missing host in a later run is not suppressed by a stale flag from an earlier run.
- **FR-013**: Log lines for the deduplicated WARNINGs MUST include the same diagnostic content operators rely on today (host name for CENR, country code for region gap), so an operator can still identify the missing item from a single log line.
- **FR-014**: If any run-summary telemetry is added, it MUST use the existing `TelemetryEmitter` / JSONL pattern under `data/`; no new sinks and no schema-breaking changes to existing telemetry.

### Key Entities *(include if feature involves data)*

- **CENR observation cache**: Existing in-memory data structure holding host → observed URL mappings loaded from `zscaler_cenr_hostnames.json`. Consumed by menu 206 emission logic. Not modified by this feature — only its read-time warning behavior changes.
- **Zscaler catalogue**: Existing declaration of the set of hosts that menu 206 emits probes for. Determines the "expected" host set that CENR gaps are computed against.
- **Region map (`_COUNTRY_CODE_TO_REGION`)**: Static dict in `src/org/org_synthetic_probes_manager.py` mapping ISO alpha-2 country codes to Zscaler region strings (`"americas"`, `"emea"`, `"apac"` — canonical literals per `research.md` R1). Extended by this feature.
- **Intentional-gap set**: New static set (or equivalent explicit marker) in the same module enumerating ISO alpha-2 codes deliberately excluded from region mapping, with inline rationale per entry. Introduced by this feature.
- **Menu 206 run dedup state**: Ephemeral per-run set(s) tracking which missing CENR hosts and which unmapped country codes have already been warned about in the current invocation. Discarded at run end.
- **Fixture org**: Test fixture representing a large multi-region org (targeting ~315 sites, ≥8 LATAM/Caribbean countries, ≥7 unobserved CENR hosts) used by regression tests to assert log-record counts and probe-payload byte-stability.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a ~315-site fixture org with 7 unobserved SecB2B CENR hosts, "missing CENR observation" WARNINGs in `data/script.log` drop from ~1,261 per menu 206 run to at most 7 per run (a ≥99% reduction in duplicate warning volume).
- **SC-002**: On the same fixture, "unknown country code" WARNINGs for the 8 covered LATAM/Caribbean codes drop from `N_affected_sites` to zero per run.
- **SC-003**: For every fixture site whose `country_code` is in `{PA, BS, HT, DO, GT, CU, CR, HN}`, the resolved region is `"americas"` (not `"emea"`) in 100% of cases.
- **SC-004**: Emitted probe payloads for non-VPN targets are byte-identical to the pre-change baseline in 100% of fixture comparisons (INV-1 preserved).
- **SC-005**: An ISO alpha-2 coverage test asserts that 100% of valid ISO-3166 alpha-2 codes are present in exactly one of `_COUNTRY_CODE_TO_REGION` or the intentional-gap set; the test fails CI on any silent addition or removal.
- **SC-006**: An operator triaging a menu 206 run can locate any genuinely-actionable log line without scrolling past duplicate WARNINGs — quantified as "unique WARNING lines per run" being within 10× of "unique WARNING lines per run for a run that triggers zero of the two documented issues."
- **SC-007**: `pytest` runtime for the new regression tests is under 5 seconds on the reference dev machine (fixture-driven, no network I/O). — **Verification annotation (O1 remediation)**: SC-007 is verified only after US3 (Phase 5) lands via task T029. If the MVP-first ship path is chosen (US1 only), SC-007 remains provably-unverified until T029 executes; document that gap in the ship-decision note if MVP-first is selected.

## Assumptions

- The `TelemetryEmitter` JSONL pattern under `data/` from spec 1024 remains the sanctioned mechanism for any structured run-summary output; no operator-facing dashboard is expected as part of this feature.
- The list of ISO-3166 alpha-2 codes for the coverage test is sourced from stdlib or a checked-in fixture (no network fetch at test time); either the standard 249-code alpha-2 list is embedded once, or a stable public list is checked in as a test fixture.
- Central America and Caribbean sites route via the `"americas"` Zscaler region (colloquially "amer"; see `research.md` R1 for the canonical literal used across every downstream artifact) — confirmed by the fact that today's geodesic fallback picks a US-region ZEN for them. If Zscaler tenancy specifics for a given customer dictate otherwise, that override is site-specific configuration, not a global region-map change.
- CENR observation ingest fixing (the *upstream* reason SecB2B b2c/gslb hosts have no observed URL) is out of scope for this feature and is expected to be tracked as a separate follow-up.
- The pre-change baseline for probe-payload byte-stability is captured from the current `main` HEAD (28fdfe5) or from the fixture-baseline artifacts already produced during spec 1024.
- No changes to menu 206's dispatch, prompt flow, or emission-shape logic are intended; the diff is confined to logging behavior and the region-map dict (plus the paired gap set and tests).
- The fixture org for regression testing is synthetic (no real customer data) and lives under `tests/unit/org/fixtures/` following the pattern already established by 1024.
- Warning message wording MAY change if needed to accommodate load-time emission (per-site vs per-run context), but MUST still name the missing host / unmapped code so log grep patterns operators may have set up continue to work.
