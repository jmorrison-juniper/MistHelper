# Phase 0 Research: Test Quality Analysis Engine

**Feature**: 1019-test-quality-analyzer
**Date**: 2026-07-14

All five outstanding `NEEDS CLARIFICATION` questions were resolved during the
`/speckit.clarify` session recorded in `spec.md`. This document captures the
supporting research and rationale that backs those decisions plus the smaller
implementation decisions that did not warrant a clarification round.

## Decision 1 — AST parsing strategy

**Decision**: Use the standard-library `ast` module with
`ast.parse(source, filename=path, type_comments=False)` and walk each tree
with a custom `ast.NodeVisitor` per rule. Cache the parsed tree per file so
each detector reuses the same AST rather than re-parsing.

**Rationale**:
- Zero external dependency, aligning with the "stdlib-only for engine core"
  constraint from the plan's Technical Context.
- `ast.parse` handles Python 3.13 syntax natively; matches the project's binding
  minimum from the constitution.
- Per-file cache reduces cold-parse cost by ~5x when five detectors run over
  the same tree, keeping the SC-001 60-second budget achievable.

**Alternatives considered**:
- **LibCST / RedBaron / parso** — third-party parsers with concrete-syntax fidelity.
  Rejected because the engine does not modify source; it only reads it, and the
  round-trip fidelity of CST is unused here.
- **Regex-only scanning** — considered for weak-assertion detection. Rejected
  because tautological-test detection (FR-007) fundamentally requires binding
  tracking, which regex cannot do accurately.
- **Reusing `pytest` collection** — considered but explicitly rejected by FR-014
  ("MUST NOT import any test module at runtime"). Import-time side effects in
  test modules would defeat the safety guarantee.

## Decision 2 — Config format and location

**Decision**: TOML file at `tools/test_quality_analyzer/config.toml`, parsed
with the stdlib `tomllib` (Python 3.11+, available on 3.13). Three top-level
tables: `[rules]`, `[severity]`, `[exclusions]`. All keys have documented
defaults inside the file as comments.

**Rationale** (from Clarification Q5, recorded here for implementation reference):
- TOML matches the `pyproject.toml` idiom already established in the repo, so
  contributors do not need to learn a new format.
- `tomllib` ships with the stdlib in 3.11+; no third-party dependency.
- Deterministic key ordering when written by `tomllib`'s companion writer
  (though this engine only *reads* config — writers are not needed).
- Chose a dedicated file over `[tool.test_quality_analyzer]` in `pyproject.toml`
  so the analyzer's schema can evolve without contaminating the project's build
  config.

**Alternatives considered**:
- **YAML** — rejected because it would add `pyyaml` as a dependency for one use.
- **JSON** — rejected because comments (required by FR-021 for self-documentation)
  are not part of the JSON standard.
- **`pyproject.toml` embedded table** — rejected as noted above.

## Decision 3 — Baseline canonicalization

**Decision** (from Clarification Q2): Baseline is a JSON document whose payload
is the `findings` array from a full engine run, canonicalized. Canonicalization
means:
1. Findings sorted by `(severity_rank_desc, category, file_path, line_number, rule_id)`.
2. All string fields UTF-8 with LF line endings.
3. `json.dumps(..., ensure_ascii=True, indent=2, sort_keys=True, separators=(",", ": "))`.
4. Trailing newline appended for POSIX-friendly diffs.
5. Run metadata (timestamp, engine version, commit SHA) **excluded** — that
   context lives in Git provenance and PR descriptions, not in the payload.

**Rationale**:
- Eliminates a second parser (baseline uses the same JSON reader as the report).
- Guarantees byte-identical output across runs given byte-identical inputs
  (SC-005), because both `json.dumps` args and sort key are fully specified.
- Diff-friendly per-finding: one finding per record block in the JSON, so a
  new/removed finding shows as a discrete diff hunk.

**Alternatives considered**:
- **Plain-text baseline** (as `.suppression-baseline.txt` uses) — rejected
  because findings carry structured metadata (severity, category, remediation)
  that a text list would either drop or ad-hoc encode.
- **SQLite baseline** — rejected as overkill and Git-hostile.

## Decision 4 — JSON Schema authoring

**Decision**: Hand-author `report.schema.json` conforming to JSON Schema
Draft 2020-12. Ship it in `tools/test_quality_analyzer/report.schema.json` and
mirror it in `specs/1019-test-quality-analyzer/contracts/report.schema.json`.
Validate the engine's output against it using a small hand-rolled validator
implemented in `reporting.py` — the validator only needs to check the subset
of Draft 2020-12 used by the schema (type, required, enum, items,
additionalProperties, minLength). No `jsonschema` third-party dependency.

**Rationale**:
- Publishes the schema so downstream tooling can validate reports independently.
- Avoids adding a dependency for a single internal use.
- The self-hosted validator is < 100 lines because the schema is narrow.

**Alternatives considered**:
- **`jsonschema` library** — rejected to keep the engine stdlib-only.
- **No schema, ad-hoc contract** — rejected because FR-011 explicitly requires
  a published schema.

## Decision 5 — Determinism strategy

**Decision**: All engine output is deterministic given a byte-identical repo
state and byte-identical config. The single non-deterministic field is the
run timestamp, which is captured **once** at CLI entry using
`datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")` and
recorded in the report envelope only (never inside findings, never inside the
baseline). All other order-dependent output is sorted with an explicit,
documented sort key.

**Rationale**:
- Meets SC-005 (byte-identical outputs given byte-identical inputs).
- Baseline diffing works cleanly because the baseline never sees the timestamp.
- Test infrastructure can freeze time via a `--fixed-timestamp` CLI flag used
  only in the engine's own tests.

**Alternatives considered**:
- **Zero timestamps** — rejected because operators want to know when a report
  was generated; removing it from the report is unfriendly.
- **Timestamp inside findings** — rejected because it would defeat the baseline.

## Decision 6 — Mist-API exclusion predicate

**Decision**: Two-part rule from FR-002:
1. Test file imports `mistapi` at module scope, OR
2. Test file's inferred subject-under-test (SUT) resides under `src/api/`.

SUT inference algorithm:
- Walk imports in the test file.
- Collect all `from src.X import ...` and `import src.X` names.
- If any resolves to a module under `src/api/`, the test is excluded.
- If none resolve to `src/api/` but `mistapi` is imported, the test is excluded.
- Otherwise the test is analyzed.

The predicate is implemented as a class (`MistApiExcluder`) with the two rules
each isolated as methods, so future scope changes swap methods without editing
call sites. Predicate parameters (exclusion path globs, module-name allowlist)
live under `[exclusions]` in `config.toml` (Clarification Q5).

**Rationale**:
- Precisely matches Clarification Q2 (from the source spec) about which surface
  the engine must not audit.
- Configurable, so a future refactor that renames `src/api/` does not require
  code edits (Assumption 1 in spec.md).

**Alternatives considered**:
- **Import-graph analysis** — considered for transitive Mist-API exposure.
  Rejected per Edge Case 3 in spec.md: transitive exclusion is *not* a goal.
- **Runtime import inspection** — rejected because FR-014 bans runtime imports
  of test modules.

## Decision 7 — Edge-case heuristic scope

**Decision** (from FR-006): The edge-case detector fires only on public
functions whose signatures declare `str`, `list`, `dict`, or `Optional[...]`
parameters. It looks for at least one test that exercises each of:
- Empty value (`""`, `[]`, `{}`).
- `None`.
- Oversized value (list/string length > 1000 as a heuristic threshold; final
  threshold configurable).
- Unicode / control-character values (any non-ASCII test literal counts).

Findings from this detector carry a `"heuristic": true` flag per FR-006, so
consumers can treat them with appropriate false-positive tolerance.

**Rationale**:
- Bounded heuristic scope means the detector is testable via fixtures.
- The `heuristic` flag makes false-positive tolerance explicit in the report
  and in the Markdown summary.

**Alternatives considered**:
- **Coverage-informed heuristics** — using `coverage.py` data to identify
  untested branches. Deferred to a future extension per Edge Case 5 in spec.md
  ("engine still runs; degrades gracefully with a note that coverage-informed
  heuristics are disabled"). For this iteration, coverage data is not consumed.
- **Mutation-testing hints** — explicitly out of scope per spec.md Assumption 7.

## Decision 8 — Performance budget allocation

**Decision**: Target < 60 s total on ~190 test files (SC-001). Allocation:
- Discovery + config load: < 500 ms.
- AST parse (once per file, cached): < 30 s aggregate (~150 ms/file average).
- Detection (five detectors × 190 files, cache-warm): < 20 s aggregate.
- Reporting + write: < 5 s.
- Slack: ~5 s for cold-start overhead and OS variance.

Single-process, single-threaded. Multiprocessing is not needed at this scale
and would complicate log ordering and determinism.

**Rationale**:
- 190 files × ~40ms avg parse is well within budget on modern hardware.
- Determinism arguments against parallelism outweigh the marginal speedup.

**Alternatives considered**:
- **Multiprocessing pool over files** — rejected for determinism and log-ordering
  complexity. Reserved for a future iteration if the file count grows > 1000.

## Decision 9 — Weak-assertion detection precision

**Decision**: The weak-assertion detector detects the exact patterns enumerated
in FR-004:
1. `assert x` where `x` is not a boolean expression (bare truthiness check).
2. `assert x is not None` on a non-Optional return.
3. `mock.assert_called()` (no `_with` variant, no argument check).
4. `pytest.raises(Exception)` (over-broad base type).
5. Test function with zero `assert` statements.
6. Test function whose sole assertion inspects a mock's own configured return
   value from the same test.

Downgrade rule per Edge Case 4 in spec.md: if a test contains at least one
strong assertion (e.g., equality/identity on a real value), the severity of any
concurrent weak-assertion finding on the same test is downgraded one step
(`high` → `medium`, `medium` → `low`). This keeps the detector honest against
tests that are mostly good but have one weak line.

**Rationale**:
- Precise pattern list from the spec, so false-positive rate is bounded.
- Downgrade rule mirrors real-world quality judgment.

**Alternatives considered**:
- **LLM-based assertion grading** — rejected: non-deterministic, expensive,
  network-dependent (violates FR-014).

## Decision 10 — Golden-set anchoring

**Decision**: The golden set (SC-002) uses the three real findings called out
in FR-016 as anchors:
- `src/api/api_data_fetcher.py` — classified as untested. Note: this file lives
  under `src/api/` which is on the exclusion list; the untested detector
  therefore also emits a `mist_api_excluded` skipped-file record, and the
  golden test asserts the presence of that skipped record rather than a
  finding on the file itself. This clarifies the interaction between FR-002
  and FR-003 that the spec left implicit.
- `tests/unit/ssh/test_shell_executor.py:110` — weak assertion.
- `tests/maps/test_viewer_callbacks_wave_b_c.py:526` — weak assertion.

Plus at least one representative each of tautological-test and
missing-failure-mode findings, chosen by running the engine once against the
real repo during implementation and pinning the first stable pair.

**Rationale**:
- Anchors the meta-tests against real-world regressions, not just synthetic
  fixtures.
- Resolves the FR-002/FR-003 interaction ambiguity explicitly.

**Alternatives considered**:
- **Synthetic-only meta-tests** — rejected because FR-016 explicitly names real
  files that must be detected.

## Open Questions

None. All five spec-level clarifications resolved during
`/speckit.clarify`; ten implementation-level decisions resolved above.
