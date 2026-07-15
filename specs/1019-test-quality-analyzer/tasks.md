---

description: "Task list for feature 1019-test-quality-analyzer"
---

# Tasks: Test Quality Analysis Engine

**Feature**: 1019-test-quality-analyzer
**Input**: Design documents from `specs/1019-test-quality-analyzer/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`, `contracts/report.schema.json`, `contracts/config.schema.md`, `quickstart.md`

**Tests**: Included and non-optional. FR-016 (golden regression set) and FR-017 (fixture meta-tests) are explicit functional requirements — the tests ARE the feature acceptance signal. TDD ordering is used inside each user story: fixtures + tests land first, detectors after.

**Organization**: Grouped by user story (P1 = baseline audit, P2 = gate mode, P3 = meta-tested engine). Phase 1 is shared setup; Phase 2 is foundational infrastructure that blocks every user story; Phase 6 is polish.

## Format

- Checklist form: `- [ ] TXXX [P?] [Story?] Description`
- `[P]` = safe to run in parallel (different files, no dependency on incomplete tasks in this phase)
- `[US1] / [US2] / [US3]` = user-story ownership (setup / foundational / polish tasks are unlabelled)
- Every task references an absolute repo-relative path where the work lives.

## Path Conventions

Analyzer code lives under `tools/test_quality_analyzer/` per plan.md §Project Structure. Analyzer tests live under `tests/tools/test_quality_analyzer/`, mirroring the analyzer tree.

## Deferred Decisions Recorded (from plan.md §Deferred to /speckit.tasks)

| # | Decision | Resolution |
|---|---|---|
| 1 | Detector implementation order | `Untested → WeakAssertion → Tautological → MissingFailureMode → MissingEdgeCase`. First two anchor SC-002 golden findings. Tautological shares mock-analysis machinery with weak-assertion. Failure-mode is enumerable (six sub-rules from FR-005). Edge-case is heuristic (FR-006) so it lands last after other detectors baseline the noise floor. |
| 2 | Fixture vs detector ordering | Interleave, TDD-style. Each detector's `bad/` + `good/` fixture pair is committed and its meta-test is failing before the detector is implemented. |
| 3 | Baseline seeding | Scripted, single polish task: run engine → review → `--write-baseline` → commit `baseline.json`. See T054. |
| 4 | Repo `.gitignore` edit | Slotted early in Setup phase so `output/` is safe to create during development. See T003. |
| 5 | `pyproject.toml [project.scripts]` | Wire in polish phase with entry `test-quality-analyzer = "tools.test_quality_analyzer.__main__:main"`. See T056. |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package skeleton, output directory git-ignoring, committed static assets (config, schema).

- [x] T001 Create analyzer package skeleton at `tools/test_quality_analyzer/`: create `tools/test_quality_analyzer/__init__.py` exporting `__version__ = "0.1.0"`, and empty stub `tools/test_quality_analyzer/__main__.py` with a `main()` no-op returning 0. Acceptance: `python -c "import tools.test_quality_analyzer; print(tools.test_quality_analyzer.__version__)"` prints `0.1.0`.
- [x] T002 [P] Create detection sub-package at `tools/test_quality_analyzer/detection/__init__.py` (empty). Acceptance: `python -c "import tools.test_quality_analyzer.detection"` runs clean.
- [x] T003 Add `tools/test_quality_analyzer/output/` to the repo root `.gitignore` (deferred decision #4). Add the single line `tools/test_quality_analyzer/output/`. Acceptance: `git check-ignore tools/test_quality_analyzer/output/anything.json` prints the path.
- [x] T004 [P] Copy the committed JSON Schema from `specs/1019-test-quality-analyzer/contracts/report.schema.json` to `tools/test_quality_analyzer/report.schema.json` so the tool ships alongside its contract (FR-011). Acceptance: `python -c "import json,pathlib; json.loads(pathlib.Path('tools/test_quality_analyzer/report.schema.json').read_text())"` succeeds.
- [x] T005 [P] Author committed default config at `tools/test_quality_analyzer/config.toml` matching `contracts/config.schema.md` exactly (three tables: `[rules]`, `[severity]`, `[exclusions]`), with every default documented as an inline comment (FR-021 self-describing requirement). Acceptance: `python -c "import tomllib,pathlib; tomllib.loads(pathlib.Path('tools/test_quality_analyzer/config.toml').read_text())"` succeeds and returns three top-level keys.
- [x] T006 [P] Create analyzer test tree at `tests/tools/test_quality_analyzer/__init__.py` (empty) and `tests/tools/test_quality_analyzer/conftest.py` (defines a `repo_root` fixture returning the repo top-level `Path` and a `run_engine` fixture that invokes the CLI in-process via `TestQualityCLI` once foundational is complete). Acceptance: `pytest tests/tools/test_quality_analyzer/ --collect-only` runs without collection errors (zero tests is fine at this stage).
- [x] T007 [P] Create fixture directory skeleton at `tools/test_quality_analyzer/fixtures/bad/` and `tools/test_quality_analyzer/fixtures/good/` with `.gitkeep` placeholders. Acceptance: `ls tools/test_quality_analyzer/fixtures/bad/ tools/test_quality_analyzer/fixtures/good/` both list `.gitkeep`.

**Checkpoint**: Package importable, output ignored, contracts committed, test tree collectable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data model, config, discovery, exclusion, and reporting scaffolding. No detection rule can be written until these are green. Meta-tests are written alongside so the foundation itself is validated.

- [X] T008 Implement enums `Severity` and `Category` at `tools/test_quality_analyzer/detection/__init__.py` (or a shared `types.py` — pick whichever keeps the sub-package at ≤5 children) matching data-model.md verbatim, including the `severity_rank` mapping documented in the sort key. Acceptance: `python -c "from tools.test_quality_analyzer.detection import Severity, Category; assert Severity.CRITICAL.value == 'critical'"`.
- [X] T009 [P] Implement dataclasses `Finding`, `SkippedFile`, `ParseError`, `MistApiPredicate`, `ConfigSnapshot`, `Report`, `Baseline`, `BaselineDiff` at `tools/test_quality_analyzer/detection/types.py` (or extend T008 module), all `frozen=True`, per data-model.md field-for-field. Include the `_sort_key` helper from data-model.md §Sort Keys. Acceptance: import them, construct a `Finding` with `line_number=1`, `heuristic=False`, `related_source=None`, and assert equality via `dataclasses.replace`.
- [X] T010 [P] Unit test the data model at `tests/tools/test_quality_analyzer/test_types.py`: cover frozen-ness (`FrozenInstanceError` on mutation), sort-key ordering (a critical finding sorts before a low finding), and POSIX-path invariant. Acceptance: `pytest tests/tools/test_quality_analyzer/test_types.py -v` all-green.
- [X] T011 Implement `ConfigLoader` at `tools/test_quality_analyzer/config.py` using `tomllib`. Class exposes `load(path: Path) -> ConfigSnapshot`. Fail-fast on unknown rule ids, non-boolean values in `[rules]`, non-taxonomy strings in `[severity]`, invalid TOML. Match FR-021 exit-2 semantics by raising a distinct `ConfigError` exception (CLI translates to exit code). Log `info` before load and `debug` after with rule count. Acceptance: valid config loads to a `ConfigSnapshot` whose `rules_enabled` has 18 keys.
- [X] T012 [P] [P] Unit tests for `ConfigLoader` at `tests/tools/test_quality_analyzer/test_config_loader.py`: missing file falls back to defaults; empty file falls back to defaults; unknown rule id raises `ConfigError`; non-taxonomy severity raises `ConfigError`; malformed TOML raises `ConfigError`. Acceptance: `pytest tests/tools/test_quality_analyzer/test_config_loader.py -v` all-green.
- [X] T013 Implement `TestFileDiscoverer` at `tools/test_quality_analyzer/discovery.py`. Class exposes `discover(roots: Sequence[Path]) -> list[Path]` — walks each root, returns Python files whose name starts with `test_` or ends with `_test.py`, POSIX-normalized repo-relative. Log `info` before walk and `debug` after with file count. Acceptance: pointing it at `tests/` returns ≥190 paths on the current repo.
- [X] T014 [P] Implement `MistApiExcluder` at `tools/test_quality_analyzer/discovery.py` (same module, second class — the module holds exactly two classes). Class exposes `classify(test_path: Path, tree: ast.Module) -> SkippedFile | None`. Returns `SkippedFile(reason="mist_api_excluded")` when `mistapi` is imported at module scope OR when any module-scope `from src.api. …` import is present (FR-002). Uses `MistApiPredicate` parameters, not hard-coded strings. Golden anchor: `src/api/api_data_fetcher.py` — verify this file's parent module import path causes any test that imports it to be excluded. Acceptance: given a synthetic AST containing `import mistapi`, returns a `SkippedFile`; given `import requests`, returns `None`.
- [X] T015 [P] Unit tests for discovery + exclusion at `tests/tools/test_quality_analyzer/test_discovery.py`: walk a `tmp_path` tree, assert file count and sort order; feed synthetic ASTs (via `ast.parse` on string literals) covering `import mistapi`, `from mistapi import x`, `from src.api.foo import bar`, `import requests`, empty module. Regression anchor: include one synthetic test whose top-level import is `from src.api.api_data_fetcher import fetch` and assert it is classified `mist_api_excluded`. Acceptance: all four exclusion cases classified correctly; discovery returns POSIX paths.
- [X] T016 Implement `ReportBuilder` at `tools/test_quality_analyzer/reporting.py`: takes findings + skipped + parse-errors + stale-baseline + config-snapshot + engine-version + timestamp, produces canonical `Report`. Uses `_sort_key` from T009 for findings, `file_path` ascending for skipped/parse/stale. Emits JSON via `json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True, separators=(",", ": "))` with trailing newline. Log `info` before build, `debug` after with finding count. Acceptance: given a fixed input, two consecutive calls produce byte-identical JSON.
- [X] T017 [P] Implement `MarkdownRenderer` at `tools/test_quality_analyzer/reporting.py` (same module, second class). Groups findings by severity descending (CRITICAL → LOW), then by category, then file:line ascending. Uses ASCII-only characters (Constitution Principle V). Acceptance: rendering the same findings twice yields byte-identical Markdown.
- [X] T018 [P] Unit tests for reporting determinism at `tests/tools/test_quality_analyzer/test_reporting.py`: build a `Report` twice from identical inputs with a fixed timestamp, hash both JSON strings, assert equal. Also validate produced JSON against `tools/test_quality_analyzer/report.schema.json` using an inline hand-rolled validator (no jsonschema dep — plan.md §Primary Dependencies). Covers SC-005 and SC-007. Acceptance: `pytest tests/tools/test_quality_analyzer/test_reporting.py -v` all-green.
- [X] T019 Implement a `Detector` protocol (or ABC) at `tools/test_quality_analyzer/detection/__init__.py` — every rule class exposes `detect(test_path: Path, tree: ast.Module, source: str) -> list[Finding]`. Also introduce a `DetectorRegistry` list in the same module. Acceptance: importing all five (currently-empty) detector modules and registering placeholder classes yields five entries.
- [X] T020 Implement inline JSON Schema validator at `tools/test_quality_analyzer/reporting.py` (private helper method on `ReportBuilder`) — supports `type`, `required`, `properties`, `items`, `enum`, `pattern`, `minimum`. Enough coverage to validate `report.schema.json`. Acceptance: valid report validates; a report missing `engine_version` fails validation with a diagnostic message naming the missing field.

**Checkpoint**: Foundation complete. Every user story can start; detectors plug into the registry.

---

## Phase 3: User Story 1 — Baseline audit of the current test suite (Priority: P1) 🎯 MVP

**Goal**: Deliver a working single-shot audit CLI. Running `python -m tools.test_quality_analyzer` on the current repo yields a JSON report + Markdown summary in under 60 s, containing all SC-002 golden findings, byte-deterministic under `--fixed-timestamp`, with `src/api/api_data_fetcher.py` in the `skipped_files` block.

**Independent Test**: Run the CLI on a fresh checkout, assert exit 0, assert `output/report.json` validates against schema, assert golden findings present at exact file:line. Quickstart Scenario A.

**Deferred-decision anchor**: Detector order is fixed here — Untested first, WeakAssertion second, then Tautological, then MissingFailureMode, then MissingEdgeCase. Each detector: fixture-bad → fixture-good → meta-test → detector implementation.

### Detector 1 — UntestedDetector

- [X] T021 [P] [US1] Author bad fixture `tools/test_quality_analyzer/fixtures/bad/test_untested_source_module_source.py` — a synthetic source module (fixture "source under test") and a `README` note showing the untested public function scenario (no corresponding test file). Acceptance: file exists and is syntactically valid Python (`python -m py_compile`).
- [X] T022 [P] [US1] Author good fixture `tools/test_quality_analyzer/fixtures/good/test_untested_good.py` — a synthetic test that imports the source module and references its public functions. Acceptance: `python -m py_compile` on the file succeeds.
- [X] T023 [US1] Meta-test skeleton at `tests/tools/test_quality_analyzer/test_meta_fixtures.py` gains an `UntestedDetector` block: expected finding present against bad fixture, zero findings against good fixture. Test must FAIL until T024 lands. Acceptance: `pytest tests/tools/test_quality_analyzer/test_meta_fixtures.py::test_untested_detector -v` fails with a "not implemented" or empty-findings signal.
- [X] T024 [US1] Implement `UntestedDetector` at `tools/test_quality_analyzer/detection/untested.py`. Class walks `src/*.py` + `MistHelper.py`, extracts public function names (name does NOT start with `_`), then diffs against the set of `(module, name)` pairs referenced anywhere in analyzed test files. Emits `Finding(category=UNTESTED, rule_id="untested_public_function", severity=HIGH, ...)`. Registers itself in `DetectorRegistry`. Log `info` before scan, `debug` after with untested count. Acceptance: `pytest tests/tools/test_quality_analyzer/test_meta_fixtures.py::test_untested_detector -v` passes.

### Detector 2 — WeakAssertionDetector

- [X] T025 [P] [US1] Author bad fixture `tools/test_quality_analyzer/fixtures/bad/test_weak_assertion_bad.py` covering each weak sub-rule from FR-004: bare `assert result`, `assert x is not None`, `mock.assert_called()` with no argument check, `pytest.raises(Exception)`, zero-assertion test function, self-mock-echo assertion. Add an inline comment on each case pointing to the sub-rule id so the meta-test can locate exact line numbers. Acceptance: `python -m py_compile` succeeds.
- [X] T026 [P] [US1] Author good fixture `tools/test_quality_analyzer/fixtures/good/test_weak_assertion_good.py` — well-formed strong assertions: `assert x == expected`, `mock.assert_called_once_with(...)`, `with pytest.raises(SpecificError): ...`. Acceptance: `python -m py_compile` succeeds.
- [X] T027 [US1] Extend `test_meta_fixtures.py` with a `WeakAssertionDetector` block asserting one finding per weak sub-rule against the bad fixture and zero findings against the good fixture. Test must FAIL until T028. Acceptance: block fails on first run.
- [X] T028 [US1] Implement `WeakAssertionDetector` at `tools/test_quality_analyzer/detection/weak_assertion.py`. AST walker recognizes each FR-004 pattern; downgrade severity if a strong assertion coexists on the same code path (per spec.md Edge Cases). Emits `Finding(category=WEAK_ASSERTION, rule_id in {weak_bare_truthy, weak_assert_not_none, weak_mock_called, weak_broad_raises, weak_no_assertions, weak_self_mock}, severity=HIGH|MEDIUM, ...)`. Log `info` before scan, `debug` after with count per rule id. **Regression anchors (SC-002)**: this detector MUST flag `tests/unit/ssh/test_shell_executor.py:110` and `tests/maps/test_viewer_callbacks_wave_b_c.py:526` when run against the real repo. Acceptance: `pytest tests/tools/test_quality_analyzer/test_meta_fixtures.py::test_weak_assertion_detector -v` passes.

### Detector 3 — TautologicalTestDetector

- [X] T029 [P] [US1] Author bad fixture `tools/test_quality_analyzer/fixtures/bad/test_tautological_bad.py` with the FR-007 pattern: `foo.bar = Mock(return_value=X)` followed by `assert foo.bar() == X` as sole verification. Acceptance: `python -m py_compile` succeeds.
- [X] T030 [P] [US1] Author good fixture `tools/test_quality_analyzer/fixtures/good/test_tautological_good.py` — a test that mocks a dependency but asserts on the *caller's* observed behavior, not the mock's echoed return. Acceptance: `python -m py_compile` succeeds.
- [X] T031 [US1] Extend `test_meta_fixtures.py` with a `TautologicalDetector` block. Test must FAIL until T032. Acceptance: block fails on first run.
- [X] T032 [US1] Implement `TautologicalTestDetector` at `tools/test_quality_analyzer/detection/tautological.py`. Detects `Mock(return_value=X)` (or `.return_value = X`) followed by an assertion whose only comparison-RHS is the same literal `X`, with no intervening call whose result differs. Rule id `tautological_return_echo`, severity HIGH. Log `info` before scan, `debug` after. Acceptance: meta-test block passes.

### Detector 4 — MissingFailureModeDetector

- [X] T033 [P] [US1] Author bad fixture `tools/test_quality_analyzer/fixtures/bad/test_failure_mode_bad.py` — a synthetic test file for a synthetic source module that calls `requests.get(...)` but exercises only the happy path (no timeout, no connection error, no HTTP 4xx/5xx, no malformed JSON, no empty body). Acceptance: `python -m py_compile` succeeds.
- [X] T034 [P] [US1] Author good fixture `tools/test_quality_analyzer/fixtures/good/test_failure_mode_good.py` — same synthetic SUT but tests that cover each of the six failure modes listed in FR-005. Acceptance: `python -m py_compile` succeeds.
- [X] T035 [US1] Extend `test_meta_fixtures.py` with a `MissingFailureModeDetector` block: bad fixture yields six findings (one per missing sub-rule), good fixture yields zero. Test must FAIL until T036. Acceptance: block fails on first run.
- [X] T036 [US1] Implement `MissingFailureModeDetector` at `tools/test_quality_analyzer/detection/failure_mode.py`. Scans source modules for calls to `requests.*`, `httpx.*`, `urllib.*`, and SSH/socket APIs; for each such module checks the analyzed test corpus for coverage of: connection timeout, connection error, HTTP 401/403/404, HTTP 5xx, malformed JSON, empty body. Emits one finding per missing sub-rule with rule ids `missing_timeout | missing_connection_error | missing_http_4xx | missing_http_5xx | missing_malformed_json | missing_empty_body`. Log `info` before scan, `debug` after. Acceptance: meta-test block passes.

### Detector 5 — MissingEdgeCaseDetector

- [X] T037 [P] [US1] Author bad fixture `tools/test_quality_analyzer/fixtures/bad/test_edge_case_bad.py` — a synthetic SUT with a public function taking `str`, `list`, `dict`, and `Optional[...]` parameters, tested only with happy-path values (no empty, None, oversized, or unicode). Acceptance: `python -m py_compile` succeeds.
- [X] T038 [P] [US1] Author good fixture `tools/test_quality_analyzer/fixtures/good/test_edge_case_good.py` — tests that exercise `""`, `[]`, `{}`, `None`, an oversized value, and a Unicode/control-character value. Acceptance: `python -m py_compile` succeeds.
- [X] T039 [US1] Extend `test_meta_fixtures.py` with a `MissingEdgeCaseDetector` block. Every finding from this detector must have `heuristic=True` (FR-006). Test must FAIL until T040. Acceptance: block fails on first run.
- [X] T040 [US1] Implement `MissingEdgeCaseDetector` at `tools/test_quality_analyzer/detection/edge_case.py`. Walks public function signatures under `src/*` and `MistHelper.py`; where a parameter is annotated `str | list | dict | Optional[...]`, checks the test corpus for parametrize cases or literal arguments covering empty/None/oversized/unicode. Emits findings with rule ids `edge_empty_value | edge_none_value | edge_oversized_value | edge_unicode_value`, severity LOW, `heuristic=True`. Log `info` before scan, `debug` after. Acceptance: meta-test block passes.

### CLI + Integration for US1

- [x] T041 [US1] Implement `TestQualityCLI` at `tools/test_quality_analyzer/__main__.py` — replaces the T001 stub. `argparse` surface matches `contracts/cli.md` exactly (`--roots`, `--config`, `--report`, `--summary`, `--disable-rule`, `--include-mist-api`, `--fixed-timestamp`, `--log-level`, `--baseline` [default `""` = disabled]; `--gate` and `--write-baseline` land in US2). Orchestrates: config load → discovery → exclusion → parse → run each registered detector → build report → write JSON + Markdown → print one-line stdout summary. Log `info` before each phase, `debug` after with counts. Exit 0 on success. Acceptance: `python -m tools.test_quality_analyzer --help` prints the flag table; running against `tools/test_quality_analyzer/fixtures/bad/` (with `--baseline ""` and Mist-API disabled) writes a report containing findings from all five detectors.
- [x] T042 [US1] Aggregate meta-test at `tests/tools/test_quality_analyzer/test_meta_fixtures.py::test_all_detectors_together` — runs the CLI over `fixtures/bad/` and asserts every fixture's expected finding is present; runs over `fixtures/good/` and asserts zero findings. Validates SC-003 end-to-end. Acceptance: `pytest tests/tools/test_quality_analyzer/test_meta_fixtures.py -v` all-green.
- [x] T043 [US1] Golden regression test at `tests/tools/test_quality_analyzer/test_golden_repo.py` — runs the CLI against the real repo (`--roots tests/`), loads the JSON report, asserts SC-002 anchors: `src/api/api_data_fetcher.py` appears in `skipped_files` with reason `mist_api_excluded`; `('tests/unit/ssh/test_shell_executor.py', 110, 'weak_assertion')` present in `findings`; `('tests/maps/test_viewer_callbacks_wave_b_c.py', 526, 'weak_assertion')` present in `findings`; at least one `tautological` finding present; at least one `missing_failure_mode` finding present. Test is marked `@pytest.mark.slow` so it does not run in the default fast pytest invocation. Acceptance: `pytest tests/tools/test_quality_analyzer/test_golden_repo.py -v` passes.
- [x] T044 [P] [US1] Zero-network test at `tests/tools/test_quality_analyzer/test_cli.py::test_no_network` — monkey-patches `socket.socket` to raise on instantiation, runs the CLI end-to-end against `fixtures/bad/`, asserts exit 0 and no `RuntimeError` from the socket monkey-patch (SC-006, FR-014). Acceptance: test passes.
- [x] T045 [P] [US1] Determinism test at `tests/tools/test_quality_analyzer/test_reporting.py::test_determinism_full_run` — runs the CLI twice with `--fixed-timestamp 2026-07-14T00:00:00+00:00` against the fixture tree, hashes both `report.json` and `summary.md`, asserts equal. Validates SC-005. Acceptance: test passes.

**Checkpoint (MVP)**: US1 complete. `python -m tools.test_quality_analyzer` on the real repo produces a valid report with all golden anchors. Feature is deliverable at this checkpoint.

---

## Phase 4: User Story 2 — Gate mode that blocks NEW findings (Priority: P2)

**Goal**: Add baseline comparison, gate exit codes 0/1/2, parse-error handling per FR-018, and stale-baseline advisory per FR-019.

**Independent Test**: With a committed baseline and a synthetic diff that adds one new weak assertion, the CLI exits 1 and lists exactly one new finding; reverting the diff yields exit 0. Quickstart Scenario C.

- [x] T046 [US2] Implement `BaselineDiffer` at `tools/test_quality_analyzer/baseline.py`. Class exposes `load(path: Path) -> Baseline` (JSON findings-array subset per FR-012), `diff(current: tuple[Finding, ...], baseline: Baseline) -> BaselineDiff` (set difference on the canonical key `(category, rule_id, file_path, line_number, explanation)` per data-model.md §Relationships), and `write(path: Path, findings: tuple[Finding, ...]) -> None` (canonicalized JSON, no envelope). Log `info` before diff, `debug` after with counts. Acceptance: round-trip test — write findings, read them back, assert equality via canonical key.
- [x] T047 [P] [US2] Unit tests for `BaselineDiffer` at `tests/tools/test_quality_analyzer/test_baseline_differ.py`: round-trip; new-finding detection; removed-finding detection; unchanged-count; canonical-key insensitivity to `severity` and `remediation` changes; stale-baseline advisory when a baseline entry names a file that no longer exists (FR-019). Acceptance: `pytest tests/tools/test_quality_analyzer/test_baseline_differ.py -v` all-green.
- [x] T048 [US2] Extend `TestQualityCLI` at `tools/test_quality_analyzer/__main__.py` with `--gate` and `--write-baseline` flags per `contracts/cli.md` (the `--baseline` flag was already added in T041). Behavior: `--gate` runs the full analysis, compares against baseline, prints `gate: <N> new findings vs baseline`, exits 1 if `new_findings` non-empty, 0 otherwise. `--write-baseline` writes the current findings array to the baseline path and exits 0. `--baseline ""` disables baseline comparison. Exit code 2 raised from any `ConfigError`, `ParseError` in gate mode (FR-018), or IO error. Acceptance: help output shows the two new flags; `--gate` and `--write-baseline` are mutually exclusive at argparse level.
- [x] T049 [US2] Parse-error handling: `TestFileDiscoverer` (or a new `TestFileParser` step in `discovery.py`) wraps `ast.parse` and yields a `ParseError` record on failure with `file_path`, `line_number` (from `SyntaxError.lineno`), and ASCII-normalized `msg`. `ReportBuilder` includes these in `Report.parse_errors`. In `--gate` mode, any non-empty `parse_errors` triggers exit code 2 with a stderr message. Acceptance: create a `tmp_path` test tree containing one intentionally malformed test file; run CLI in gate mode; assert exit code 2 and the file appears in `report['parse_errors']`.
- [x] T050 [P] [US2] CLI tests at `tests/tools/test_quality_analyzer/test_cli.py`: gate-clean case (baseline matches current) → exit 0; gate-new-finding case (introduce one new weak assertion in `tmp_path`) → exit 1 with the new finding listed distinctly; gate-parse-error case → exit 2; `--write-baseline` writes canonical JSON and exits 0; `--baseline ""` skips comparison. Validates SC-004. Acceptance: all five subtests pass.
- [x] T051 [P] [US2] Stale-baseline test at `tests/tools/test_quality_analyzer/test_baseline_differ.py::test_stale_advisory` — baseline references a file that does not exist in the working tree; assert the file appears in `Report.stale_baseline_entries`, gate does NOT fail (exit 0 if no new findings), stderr surfaces the advisory. Validates FR-019. Acceptance: test passes.

**Checkpoint**: US2 complete. Gate mode is functional and CI-ready (wiring deferred per Clarification Q3).

---

## Phase 5: User Story 3 — Meta-tested engine that itself does not regress (Priority: P3)

**Goal**: Prove engine durability. Every detection rule can be toggled off via config, and doing so silences only that rule's fixture findings.

**Independent Test**: Given the shipped fixture directories, meta-test suite runs standalone and produces exit code 0 when every bad fixture is caught and every good fixture is silent. Disabling one rule via `--disable-rule` silences only that rule's fixtures. Quickstart Scenario D.

Most fixture-based validation already landed in Phase 3 (T023, T027, T031, T035, T039, T042). Phase 5 adds the disable-rule interlock (Acceptance Scenario 3 of US3) and formalizes the SC-003 assertion.

- [x] T052 [P] [US3] Rule-disable interlock test at `tests/tools/test_quality_analyzer/test_meta_fixtures.py::test_disable_rule_isolates`: for each of the 18 rule ids in `config.toml` `[rules]`, run the CLI over `fixtures/bad/` with `--disable-rule <id>`, assert that findings for that specific rule id are absent AND findings for every other rule id are unchanged from the baseline meta-run. Validates US3 Acceptance Scenario 3. Acceptance: test passes across all 18 rule ids.
- [x] T053 [P] [US3] SC-003 assertion test at `tests/tools/test_quality_analyzer/test_meta_fixtures.py::test_sc003_zero_false_positives`: runs the CLI over `fixtures/good/` with the full default rule set, asserts `len(report['findings']) == 0`. Validates SC-003 zero-false-positive requirement. Acceptance: test passes.

**Checkpoint**: US3 complete. Engine is self-regression-tested and durable to detector-code changes.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Baseline seeding on the real repo, `pyproject.toml` script entry, quickstart validation, lint/format cleanup.

- [x] T054 Baseline seeding (deferred decision #3). Sequence: (1) run `python -m tools.test_quality_analyzer` against the real repo; (2) manually review `output/report.json` and confirm SC-002 anchors present, no glaring false positives; (3) run `python -m tools.test_quality_analyzer --write-baseline`; (4) verify `tools/test_quality_analyzer/baseline.json` written and canonicalized; (5) `git add tools/test_quality_analyzer/baseline.json`. Acceptance: `git status` shows the baseline staged; running `python -m tools.test_quality_analyzer --gate` on the same tree exits 0 with `gate: 0 new findings vs baseline`.
- [x] T055 [P] Verify `.gitignore` (from T003) suppresses `output/` after the first real-repo run. Sequence: run engine once, then `git status` should NOT list `tools/test_quality_analyzer/output/report.json` or `summary.md`. Acceptance: `git status --porcelain | grep 'test_quality_analyzer/output' | wc -l` returns `0`.
- [x] T056 [P] Wire `pyproject.toml [project.scripts]` (deferred decision #5). Add entry `test-quality-analyzer = "tools.test_quality_analyzer.__main__:main"` under `[project.scripts]` in `pyproject.toml`. Acceptance: after `pip install -e .` (or `uv sync`), invoking `test-quality-analyzer --help` prints the same help text as `python -m tools.test_quality_analyzer --help`.
- [x] T057 [P] Full quickstart walk-through. Execute every scenario in `specs/1019-test-quality-analyzer/quickstart.md` (A through F) in order; record wall-clock for Scenario A (must be < 60 s → validates SC-001); record the `SC-005 pass` output for Scenario E. Acceptance: every scenario's "Expected" block observed; wall-clock recorded in a PR comment or CHANGELOG note.
- [x] T058 [P] Lint + format sweep on the whole analyzer tree. Run `black tools/test_quality_analyzer/ tests/tools/test_quality_analyzer/` and `ruff check tools/test_quality_analyzer/ tests/tools/test_quality_analyzer/ --fix`. Verify Constitution Principle VI (inline comments on every executable line) with a spot-check on `discovery.py`, `weak_assertion.py`, and `__main__.py`. Acceptance: both tools exit 0 with no changes on a re-run (idempotent).
- [x] T059 [P] README stub at `tools/test_quality_analyzer/README.md` — one-page maintainer reference pointing at `specs/1019-test-quality-analyzer/quickstart.md` for canonical usage and at `contracts/cli.md` for the flag surface. Do NOT duplicate the quickstart; link only. Acceptance: file exists and renders in `markdown.pyi` preview without dead links.
- [x] T060 [P] Performance validation. Time three consecutive full-repo runs (`--fixed-timestamp` to remove clock noise); assert median wall-clock < 60 s (SC-001). Log to CHANGELOG or PR body. Acceptance: recorded number.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies; can start immediately.
- **Phase 2 (Foundational)**: depends on Phase 1; blocks every user story.
- **Phase 3 (US1)**: depends on Phase 2; delivers MVP.
- **Phase 4 (US2)**: depends on Phase 3 (needs `Report.findings` and `TestQualityCLI` to exist).
- **Phase 5 (US3)**: depends on Phase 3 fixtures and Phase 4 rule-disable machinery (T048 introduced `--disable-rule`).
- **Phase 6 (Polish)**: depends on Phases 1–5.

### Within-Phase Ordering

- Detectors in Phase 3 land in the fixed order `T021→T024, T025→T028, T029→T032, T033→T036, T037→T040`; each detector's four tasks (bad fixture, good fixture, failing meta-test, implementation) are strictly sequential.
- Different detectors CAN be worked in parallel by separate contributors once T019 (Detector protocol) is in place — see Parallel Opportunities below.

### Parallel Opportunities

- **Phase 1**: T002, T004, T005, T006, T007 can all run in parallel after T001.
- **Phase 2**: T009 and T010 in parallel with each other; T012 in parallel with T014 and T015; T017 and T018 in parallel with T020.
- **Phase 3**: after T019 lands, five contributors can each own one detector's four-task sequence (T021–T024 || T025–T028 || T029–T032 || T033–T036 || T037–T040). Then T042/T043/T044/T045 all in parallel.
- **Phase 4**: T047, T050, T051 in parallel after T046 + T048 land.
- **Phase 5**: T052 and T053 in parallel.
- **Phase 6**: T055, T056, T057, T058, T059, T060 all in parallel after T054.

### Regression Anchors Reference (SC-002)

The following golden findings from spec.md §Success Criteria SC-002 are referenced as regression anchors in specific tasks — do not merge without them appearing in the real-repo report:

| Anchor | Category / classification | Referenced in |
|---|---|---|
| `src/api/api_data_fetcher.py` | `skipped_files` with reason `mist_api_excluded` | T014, T015, T043 |
| `tests/unit/ssh/test_shell_executor.py:110` | `weak_assertion` finding | T028, T043 |
| `tests/maps/test_viewer_callbacks_wave_b_c.py:526` | `weak_assertion` finding | T028, T043 |
| At least one `tautological` finding on the real repo | any file | T032 (behaviorally) + T043 (assertion) |
| At least one `missing_failure_mode` finding on the real repo | any HTTP/SSH-touching file | T036 (behaviorally) + T043 (assertion) |

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup (T001–T007).
2. Complete Phase 2: Foundational (T008–T020) — BLOCKS every user story.
3. Complete Phase 3: US1 (T021–T045).
4. **STOP and VALIDATE**: run `python -m tools.test_quality_analyzer` on the real repo, confirm SC-001 wall-clock and SC-002 anchors. Feature is shippable at this checkpoint.

### Incremental Delivery

1. Phase 1 + 2 → Foundation.
2. Phase 3 → MVP (US1). Ship, gather feedback.
3. Phase 4 → Gate mode (US2). Ship a second increment.
4. Phase 5 → Meta-test durability (US3).
5. Phase 6 → Polish, baseline seed, script entry.

### Parallel Team Strategy

- One contributor takes Phase 1 + Phase 2 solo (~10 tasks, foundational).
- Once T019 lands, up to five contributors run detectors in parallel (T021–T040).
- One contributor takes the CLI and cross-cutting integration tests (T041–T045).
- After MVP, US2 and US3 can proceed in parallel because their dependencies (Report + CLI) are already in place.

---

## Notes

- `[P]` tasks touch different files. Two tasks with `[P]` in the same phase can run in parallel unless the task text explicitly says "extends" or "same module".
- Fixture files are executable Python but MUST NOT contribute to any pytest run — they live under `tools/test_quality_analyzer/fixtures/`, not under `tests/`. `conftest.py` at the test tree root explicitly avoids collection there.
- Timestamps embedded in `Report.generated_at` are the only non-deterministic field per plan.md §Constraints; `--fixed-timestamp` freezes them for tests (T045).
- No CI wiring in this feature. Gate mode ships and is CI-ready, but the GitHub Actions integration is a follow-up feature per Clarification Q3.
- Golden anchors move over time. If T043 fails because the anchor findings have been remediated, update the anchor list to the next stable set — this is a win, not a regression (documented in `quickstart.md` §Troubleshooting).
