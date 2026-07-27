# Phase 0 Research: Menu 206 Probe-Emission Log Quality & Correctness Fixes

**Feature**: `1025-probe-emission-log-fixes`
**Date**: 2026-07-26
**Status**: Complete — all NEEDS CLARIFICATION resolved

This document captures the five design decisions taken before touching code.
Each decision was extracted from a NEEDS CLARIFICATION in the plan's Technical
Context or from an open architectural question the spec leaves to the
implementation. Decisions are recorded in the format Decision / Rationale /
Alternatives so a future reader can audit the trade-offs.

---

## R1. Region-value naming: `"americas"` (not `"amer"`)

**Decision**: LATAM/Caribbean codes added to `_COUNTRY_CODE_TO_REGION` are
mapped to the string literal `"americas"`. The spec text uses the shorthand
`amer` (matching typical Zscaler operator vocabulary), but the module already
uses the longer form `"americas"` for US/CA/MX and the six South American
codes it currently ships. The full spelling is what downstream role-name
lookups (`samsung_elm_activation_americas`, etc.) match against.

**Rationale**:
- INV-1 (byte-stability from spec 1024) requires that emitted probe payloads
  do not change for the existing US/CA/MX/AR/BR/CL/CO/PE/VE sites. Those
  sites resolve to `"americas"` today; any code path that keys off the
  resolved region string must continue to see the same literal.
- The three Samsung ELM role variants baked into the catalogue expect
  `americas` / `china` / `emea` — introducing `amer` would either break
  role-selection or force a translation shim (extra code, extra Principle II
  target).
- The spec text is a human-facing shorthand; FR-005 lists the codes and the
  target region concept, and does not pin the literal string.

**Alternatives considered**:
1. **Introduce `_REGION_ALIASES` translation dict** to accept both `amer` and
   `americas`. Rejected: adds indirection, violates Principle I (five-item
   rule) for no user-visible gain.
2. **Rename the existing constant values to `amer` / `apac` / `emea`.**
   Rejected: breaks INV-1 byte-stability for the 9 existing codes, and
   requires touching every Samsung-ELM role lookup site — well beyond the
   scoped blast radius of 1025.

---

## R2. Per-run dedup state: function parameter (not class attribute)

**Decision**: The two ephemeral per-run dedup sets (`warned_cenr_hosts` and
`warned_unmapped_codes`) are constructed inside `manage_org_synthetic_probes`
as local `set[str]` objects and threaded to `_probe_target` and the
region-resolver as an explicit `dedup_state` parameter (or as two positional
`frozenset`-refs — final shape decided at data-model time).

**Rationale**:
- The target module `src/org/org_synthetic_probes_manager.py` is entirely
  function-based today. Introducing a class solely to hold two sets would
  be inconsistent with the module's established idiom and would trivially
  wrap a dict — a direct Principle II violation ("no wrapper classes").
- Ephemeral state maps naturally to a function parameter: lifetime is bounded
  by `manage_org_synthetic_probes()`, and passing it explicitly makes the
  data flow visible in call sites (no hidden singleton).
- FR-012 is satisfied by construction: fresh set per invocation.
- Testing is easier: a test can construct the set, invoke the helper, and
  inspect the mutations.

**Alternatives considered**:
1. **Module-level global set cleared on function entry.** Rejected: hidden
   global state, violates the "no global mutable module state" guidance in
   the constitution's Principle III, and creates a thread-safety hazard if
   two operators ever run menu 206 concurrently against different orgs.
2. **New `_ProbeEmissionRun` context-object class.** Rejected: would require
   refactoring 5+ existing helpers to accept `self`, exceeding the scoped
   blast radius and violating Principle II's own "no wrappers" clause. This
   is documented in `plan.md` Complexity Tracking.
3. **`functools.lru_cache` on the WARNING emitter.** Rejected: cache is
   process-wide by default and would fail FR-012 (state must not persist
   across invocations); custom cache instance re-invents the parameter-
   thread pattern with more machinery.

---

## R3. ISO-3166 alpha-2 completeness: checked-in static fixture (not `pycountry`)

**Decision**: The 249-code ISO-3166-1 alpha-2 reference list used by the
coverage regression test lives in
`tests/unit/org/fixtures/iso_3166_alpha2.json`, checked into the repository.
No new dependency on `pycountry` (or any other country-code library) is
added.

**Rationale**:
- Adds zero new runtime dependency (Constitution's dependency-minimization
  stance).
- Determinism: a checked-in fixture cannot drift when a third-party library
  publishes a new release with revised codes.
- The ISO-3166-1 alpha-2 code list is quasi-static (roughly one change per
  decade). If a code is ever added or officially deprecated, the fixture is
  updated in a targeted PR with a link to the ISO amendment.
- File size: 249 two-letter strings + JSON overhead is ~2 KB — trivial.
- CI cost is O(249) set-membership checks, well inside SC-007's 5-second
  budget.

**Alternatives considered**:
1. **Add `pycountry` as a test-only dep.** Rejected: introduces a maintained
   third-party dependency for a fixture that changes ~once/decade; increases
   supply-chain surface; requires a new `pip-tools` regeneration.
2. **Generate the fixture at test collection time from `pycountry`.**
   Rejected: still requires the dep, and makes the "which codes did we
   validate against" question un-answerable from `git show`.
3. **Hard-code the list inside the test file.** Rejected: 249 strings in a
   test file bloat it and mix data with logic; a JSON fixture cleanly
   separates them.

---

## R4. Intentional-gap marker: separate `frozenset` with per-code inline comments

**Decision**: A new module-level constant
`_COUNTRY_CODE_INTENTIONAL_GAPS: frozenset[str]` is introduced alongside
`_COUNTRY_CODE_TO_REGION`. Every alpha-2 code deliberately excluded from the
region map is listed as a member, each with a same-line `#` comment
explaining why (per Constitution VI). The coverage regression test asserts
that the two collections are disjoint and their union covers every ISO-3166
alpha-2 code.

**Rationale**:
- Explicit is better than implicit: a code that is *deliberately* omitted
  from the region map is distinguishable from a code that was *forgotten*.
  The gap set carries operator intent.
- `frozenset` (not `set`) advertises immutability at module scope, aligning
  with the constant-naming convention (`_UPPER_SNAKE`).
- Placing it in the same module keeps the two collections co-located, so a
  future contributor editing the region map cannot miss the gap-set
  invariant.
- Inline rationale per member satisfies Constitution VI without needing a
  separate design doc; the rationale lives next to the code it explains.

**Alternatives considered**:
1. **Sentinel value inside the region map** (e.g., map to `None` or a
   special string like `"__intentional_gap__"`). Rejected: conflates two
   semantically different states in one collection, forces every consumer to
   filter, and makes the "what does this map return for X" question
   ambiguous.
2. **External YAML/JSON gap file.** Rejected: separates rationale from code,
   and the coverage test would need to load and parse it at collection time
   — added complexity for no observable benefit.
3. **Comment-only convention** ("codes not listed here are intentional
   gaps"). Rejected: unenforceable by CI; the whole point of the gap set is
   the machine-checkable disjoint-union invariant.

---

## R5. Log-level and emission-site strategy for the deduplicated WARNINGs

**Decision**:
- **CENR path (US1)**: The `logger.warning("no observation for %s, using
  catalogue default %s", ...)` is *moved* out of `_probe_target()` and
  *replaced* with a single load-time `logging.warning("CENR observation
  missing for %d catalogue host(s): %s; catalogue default URLs will be
  used", len(missing), sorted(missing))` emitted immediately after CENR
  observations are loaded but before any site iteration begins. Emission
  site: helper newly added / consolidated near `_load_probe_sources` (data
  ingest boundary). The set of "missing hosts" is computed as
  `catalogue_hosts − cenr_observed_hosts` once per run.
- **Region path (US2)**: The per-site `logging.warning("country_code %r not
  mapped; defaulting to region %r", ...)` is *moved* to a load-time helper
  that inspects every site's `country_code` up front, computes the set of
  unmapped codes present, and emits one WARNING per unique unmapped code
  (or a single WARNING listing all unmapped codes — decided at
  implementation time based on readability; contract only requires ≤K).
- **Log level stays WARNING** for both. INFO would be silent by default in
  production log config, defeating the operator-visibility goal.

**Rationale**:
- Load-time emission is *deterministic* (per FR-002) — the missing-host set
  is known the moment both files are parsed; delaying the warning to
  per-site emission was a historical accident, not a design.
- Preserving WARNING level (rather than demoting to INFO) means the message
  still shows up under the default logger config, matching operator
  expectations (SC-006).
- FR-013 requires that the diagnostic tokens operators grep for (host name,
  country code) remain in the message. Both proposed wordings include the
  underlying identifiers, so existing grep patterns continue to match.
- Emission counts:
  - Before: `~len(missing) × len(sites)` (~1,261 for the reference org)
  - After (single-consolidated): 1 WARNING (`≤ 1`)
  - After (per-unique-item): `len(missing)` (`≤ 7` for reference org)
  - Both satisfy SC-001; the implementation may pick either shape as long as
    the count contract in `contracts/log_record_shape.md` holds.

**Alternatives considered**:
1. **Demote to INFO or DEBUG.** Rejected: silences the diagnostic under
   default log config; operators would need to opt in with `--verbose` to
   see it, defeating the point.
2. **Keep at per-site emission but throttle via `logging.Filter`.**
   Rejected: filters are opaque, hard to unit-test, and the throttle state
   would need to be reset per run — reinventing R2's dedup-set pattern with
   more machinery.
3. **Emit only if a `--strict` flag is passed.** Rejected: introduces a new
   CLI switch and a two-state observability contract; the whole point is to
   make the log usable *by default*.

---

## Summary of decisions

| ID | Topic | Decision |
|----|-------|----------|
| R1 | Region value literal | Use `"americas"` (preserve existing spelling) |
| R2 | Dedup state ownership | Function parameter, not class attribute |
| R3 | ISO alpha-2 source | Checked-in `iso_3166_alpha2.json` fixture, no `pycountry` |
| R4 | Intentional-gap marker | `frozenset` `_COUNTRY_CODE_INTENTIONAL_GAPS` with inline rationale |
| R5 | Log-level / emission site | Move WARNINGs to load-time; keep WARNING level; dedup at load |

All NEEDS CLARIFICATION items from Technical Context are resolved. Proceed to
Phase 1.
