# Feature Specification: Convert F-String Logging to Lazy %s Formatting (CONV-LOG-FSTRING Sweep)

**Feature Branch**: `refactor/429-conv-log-fstring-sweep`
**Created**: 2026-06-23
**Status**: Draft
**Issue**: [#429](https://github.com/jmorrison-juniper/MistHelper/issues/429)
**Input**: User description: "Convert every f-string-formatted logging call and adjacent eager-formatting pattern in `MistHelper.py` to lazy `%s`-style argument formatting, sweeping ruff rules G003, G004, and G201 to zero, then enable the `G` rule family in ruff to prevent regressions."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Eliminate Eager Logging Formatting Cost (Priority: P1)

As a maintainer running MistHelper at INFO/WARNING/ERROR level in production, I need every `logging.*` call site to defer argument formatting to the logging framework so that disabled log levels incur near-zero CPU cost, and so that future log handlers (structured JSON, OpenTelemetry, etc.) receive the message template plus arguments separately rather than a pre-rendered string.

**Why this priority**: 1,142 eager-formatting violations are the single largest open lint category. They cost CPU on hot paths and block adoption of any structured-logging handler. Removing them unblocks downstream observability work.

**Independent Test**: Run `python -m ruff check --select G MistHelper.py`; result MUST be `All checks passed!` with 0 violations. Run `python tools/check_compliance.py MistHelper.py`; CONV-LOG-FSTRING count MUST be 0.

**Acceptance Scenarios**:

1. **Given** the current `MistHelper.py` baseline with 1,142 G-rule violations, **When** the sweep completes, **Then** `ruff check --select G003,G004,G201 MistHelper.py` reports exactly 0 violations.
2. **Given** a refactored call site `logging.info("x=%s", x)`, **When** the effective log level is WARNING, **Then** the argument formatting is not executed (verified via a sentinel object whose `__str__` raises).
3. **Given** the `pyproject.toml` `[tool.ruff.lint] select` list, **When** the sweep is merged, **Then** `"G"` is present in the list and CI fails on any future G-rule reintroduction.

---

### User Story 2 - Preserve Rendered Log Output Byte-for-Byte (Priority: P1)

As a NOC engineer reading logs, log-aggregation pipelines parsing fixtures, and CI tests asserting log content, I need the rendered text of every refactored log message to be byte-identical to the pre-refactor baseline so that runbooks, regex alerts, and log-fixture tests continue to work without modification.

**Why this priority**: This is a behavior-preserving refactor. Any rendered-string drift would constitute a silent regression for operators and downstream log consumers.

**Independent Test**: Capture log output from a representative cross-section of refactored call sites using `caplog`/`assertLogs`, compare each rendered message against a frozen baseline captured from `main`, assert byte equality.

**Acceptance Scenarios**:

1. **Given** a refactored call site that previously rendered `"Site abc123 has 5 APs"`, **When** the same code path executes post-refactor, **Then** the captured `LogRecord.getMessage()` returns the exact same string.
2. **Given** an f-string with format spec like `f"{rate:.2f}"`, **When** converted to `"%.2f", rate`, **Then** the rendered output matches the original for all numeric inputs in the hypothesis property test.
3. **Given** an f-string using `!r` or `!s` conversion, **When** converted to `%r` / `%s`, **Then** the rendered output matches the original.

---

### User Story 3 - Reviewable Tranched Delivery (Priority: P2)

As a reviewer of a 1,142-site mechanical refactor, I need the work split into reviewable, independently CI-green commits (~200 sites per tranche) so that a faulty conversion can be bisected and reverted without losing the entire sweep.

**Why this priority**: A single 1,142-site PR is unreviewable in practice. Tranching enables real human review and minimizes blast radius.

**Independent Test**: Inspect commit history on `refactor/429-conv-log-fstring-sweep`; each commit MUST pass full CI (ruff, black, mypy, pytest+cov, bandit, pip-audit, CodeQL, Playwright) independently.

**Acceptance Scenarios**:

1. **Given** ~1,142 sites to convert, **When** the work is committed, **Then** there are roughly 6 tranche commits (≤ 200 sites each) plus a final commit that flips ruff config.
2. **Given** any single tranche commit, **When** CI runs against that commit alone, **Then** all quality gates pass.

### Edge Cases

The codemod MUST handle every form of f-string and adjacent eager-formatting pattern found in `MistHelper.py`. Enumeration:

- **Plain interpolation**: `f"x={x}"` → `"x=%s", x`
- **Format spec — numeric precision**: `f"{rate:.2f}"` → `"%.2f", rate`
- **Format spec — width/fill/align**: `f"{n:>10}"`, `f"{n:05d}"` → equivalent `%`-style spec; document any spec that has no `%`-style equivalent and switch to pre-format in a local var.
- **Conversion repr**: `f"{x!r}"` → `"%r", x`
- **Conversion str**: `f"{x!s}"` → `"%s", x`
- **Conversion ascii**: `f"{x!a}"` → `"%a", x`
- **Nested attribute / subscript / call**: `f"{obj.attr[key].method()}"` → extract to local `val = obj.attr[key].method()` then `"%s", val`, OR inline as positional arg if side-effect-free.
- **Ternary inside expression**: `f"{'yes' if x else 'no'}"` → extract to local var first, then `"%s", val` (lazy-eval semantics preserved because the local is computed unconditionally just like before).
- **Multi-line f-strings** (implicit string concatenation / parenthesized): re-flow as multi-line `("...%s..." "...%s...", arg1, arg2)`.
- **G003 string concatenation**: `logging.info("a=" + str(a))` → `logging.info("a=%s", a)`.
- **G003 `.format()` call**: `logging.info("a={}".format(a))` → `logging.info("a=%s", a)`.
- **G003 `%`-pre-format**: `logging.info("a=%s" % a)` → `logging.info("a=%s", a)`.
- **G201 `logging.error(..., exc_info=True)`** inside an `except:` block → `logging.exception(...)` (and strip f-string from the message argument per G004 rules).
- **G201 outside `except:`**: leave `exc_info=True` in place (G201 only applies inside `except`); still convert the message to lazy form per G004.
- **Logger methods on a named logger**: `logger.debug(f"…")`, `self.log.warning(f"…")` — convert identically; the codemod MUST recognize any attribute access whose method name is one of `debug|info|warning|warn|error|critical|exception|log`.
- **`logging.log(level, f"…")` with explicit level**: convert the message arg only; preserve the level arg.
- **F-strings whose only content is a literal expression with no substitutions** (`f"hello"`): convert to plain `"hello"` (Ruff still flags these under G004).
- **F-strings used to build values that are then passed elsewhere** (not directly to a `logging.*` call): OUT OF SCOPE — G004 only fires on logging-call positional message args.
- **`%` literal**: any literal `%` already in the message text MUST be escaped to `%%` after conversion.
- **Walrus operator inside f-string** (`f"{(x := compute())}"`): extract to a preceding statement, then `"%s", x`; preserves assignment side effect.
- **F-strings in `assert` messages, `raise X(f"…")`, `print(f"…")`**: OUT OF SCOPE.
- **String literals constructed for logger formatters/handlers** (e.g., `Formatter(fmt="%(asctime)s …")`): OUT OF SCOPE — those are framework-side format strings, not call-site messages.

## Requirements *(mandatory)*

### 1. Problem / Goal

**Problem**: `MistHelper.py` contains 1,142 ruff G-rule violations — 1,099 G004 (`logging-f-string`), 7 G003 (`logging-string-concat`), and 36 G201 (`logging-exc-info`) — counted in `data/compliance_report.md` (generated 2026-06-23). Eager formatting in disabled log levels wastes CPU on hot paths, and pre-rendered strings prevent adoption of structured-logging handlers. Ruff's `G` rule family is currently *not* in the `select` list of `pyproject.toml`, so new violations are merged routinely.

**Goal**: Convert all 1,142 call sites in `MistHelper.py` to lazy `%s`-style argument formatting via an AST-based codemod, then enable the `G` rule family in ruff to lock the gain in. The refactor is behavior-preserving: rendered log strings MUST be byte-identical pre/post.

**Non-goals**:

- Refactoring f-string logging in any file other than `MistHelper.py` (other files may have their own issues but are out of scope for #429).
- Changing log levels, logger names, handler config, formatter strings, or log routing.
- Converting non-logging f-strings (in `assert`, `raise`, `print`, return values, etc.).
- Adopting structured / JSON / OpenTelemetry logging (unblocked by this work but not done here).
- Performance benchmarking the gain (assumed positive but not measured in this scope).

### 2. Interfaces & Behavior

- **No public interface change.** No new functions, classes, or modules. No menu, CLI, or HTTP route change.
- **Per-call-site behavior contract**: For every refactored call `logging.<level>(template, *args)`, the rendered string `template % args` MUST equal the original f-string evaluation for all reachable inputs.
- **Lazy-evaluation semantics**: Argument expressions are still evaluated eagerly at the call site (Python semantics — function args are always evaluated). What becomes lazy is the *string interpolation*. If a logging argument has a side effect or a costly `__str__`, the side effect still occurs but `__str__` is deferred. This matches the documented standard-library behavior and is intentional.
- **G201 conversion changes the call name** (`error` → `exception`) inside `except:` blocks. The rendered message and traceback emission are identical because `logging.exception` is defined as `logging.error(..., exc_info=True)` per stdlib.

### 3. Constraints / Performance

- **File scope**: `MistHelper.py` only. Lines: 32,640.
- **Approach**: AST-based codemod using **libcst** (preserves comments, whitespace, trailing commas) or `ast.unparse` as fallback. Regex is explicitly forbidden — f-strings nest and break under text substitution (e.g., `f"{x[f'{k}']}"`).
- **Tranching**: ~200 sites per commit, ~6 commits total + 1 config commit. Each commit MUST pass full CI independently.
- **Performance**: Codemod runs offline; no runtime perf budget. Expected runtime gain at production INFO+ levels is non-zero but unmeasured.
- **Determinism**: Codemod MUST be idempotent — re-running on already-converted output produces no diff.

### 4. Security & Secrets

- **Manual security audit required.** Any logging call whose argument expression contains a variable whose name matches the regex `(?i)(token|password|secret|cred|key)` MUST be flagged and reviewed by hand before that tranche is committed.
- Reviewer MUST confirm the value is either (a) already redacted upstream, (b) a non-sensitive identifier despite the suspicious name (e.g., `api_key_id`, `public_key_fingerprint`), or (c) removed from the log call entirely.
- The audit checklist (`specs/429-conv-log-fstring-sweep/checklists/security-audit.md`) MUST list every flagged call site with reviewer initials and disposition before the final tranche merges.
- No new secret-bearing variables are introduced by this refactor (no new code paths, no new variables — pure call-site rewrite).

### 5. Test Plan

**Existing coverage**:

- All existing pytest unit and integration suites MUST continue to pass on each tranche commit.
- Coverage threshold ≥ 70% maintained (current project gate).

**New regression coverage**:

- **Frozen baseline fixture**: Capture rendered log output (`LogRecord.getMessage()`) from a representative cross-section of refactored sites on `main` (pre-refactor). Store as a JSON fixture under `tests/fixtures/issue_429_log_baseline.json`.
- **Parity test** (`tests/test_issue_429_log_parity.py`): Re-exercise the same code paths post-refactor, capture via `caplog`, assert byte equality against the baseline.
- **Hypothesis property test**: For each refactored call template, generate inputs via `hypothesis.strategies` and assert `template % args == original_f_string_expr` over the input space. Focus on numeric format specs, repr/str conversions, and edge values (empty string, None, large ints, NaN, multi-byte unicode).
- **Idempotency test**: Run the codemod twice; assert second run produces zero diff.
- **Lint regression test**: CI step asserting `ruff check --select G MistHelper.py` exits 0.

**Sentinel test for laziness**: One unit test installs a sentinel argument whose `__str__` raises `AssertionError`, sets logger level to WARNING, calls `logger.debug(template, sentinel)`, and asserts no exception fires — proving lazy formatting works.

### 6. Migration / Compatibility

- **No data migration.** Pure code refactor.
- **No config change for operators.** Log levels, handler routing, formatter strings unchanged.
- **No downstream consumer change.** Log aggregators that parse rendered text see byte-identical output.
- **pyproject.toml change**: `[tool.ruff.lint] select` list grows by one entry (`"G"`). Current value `["E", "F", "W", "I", "UP", "B"]` → new value `["E", "F", "W", "I", "UP", "B", "G"]`. This is the final commit in the series.
- **Rollback plan**: Each tranche is a single commit; revert is `git revert <sha>`. The ruff config commit must be reverted *before* any tranche revert to avoid CI failure on partially-rolled-back state.

### 7. Acceptance Criteria

The following criteria MUST all be true before #429 closes. Each is independently verifiable.

1. `python -m ruff check --select G MistHelper.py` reports **0 errors**.
2. `python tools/check_compliance.py MistHelper.py` shows **0 CONV-LOG-FSTRING violations**.
3. `pyproject.toml` `[tool.ruff.lint] select` includes `"G"`.
4. All existing CI quality gates pass: ruff, black, mypy, pytest+cov, bandit, pip-audit, CodeQL, Playwright.
5. Coverage ≥ **70%**.
6. No log-rendered text changes; captured fixture strings byte-identical to baseline (parity test green).
7. No secret-bearing variables in any logging call site (manual audit checklist signed off in evidence).
8. CHANGELOG.md entry added with UTC timestamp in `YY.MM.DD.HH.MM` format describing the sweep.

### 8. Implementation Notes (AI hints)

- **Tool choice**: Prefer **libcst** (`pip install libcst`) over `ast`+`ast.unparse` because libcst preserves comments, blank lines, and trailing commas. `ast.unparse` reformats the entire file and would produce a noisy unreviewable diff.
- **Call-site detection**: Match `cst.Call` where the callee is one of:
  - `cst.Attribute(value=cst.Name("logging"|"logger"|"log"|"LOG"|"_logger"), attr=cst.Name("debug"|"info"|"warning"|"warn"|"error"|"critical"|"exception"|"log"))`
  - `cst.Attribute(value=cst.Attribute(..., attr=cst.Name("logger"|"log")), attr=...)` — covers `self.logger.info(...)`, `cls.log.debug(...)`.
  - Bare `cst.Name("logging")` followed by attribute access at module level.
- **F-string conversion algorithm**:
  1. Walk the `FormattedString` node; collect each `FormattedStringExpression`.
  2. For each expression, emit a `%`-spec based on `conversion` (`r` → `%r`, `s` → `%s`, `a` → `%a`, none → `%s`) combined with `format_spec` (e.g., `.2f` → `%.2f`).
  3. Concatenate literal parts (escaping any literal `%` to `%%`) and `%`-specs to build the new template string.
  4. Emit each expression as a positional arg in left-to-right order.
- **G003 patterns**: Detect `BinaryOperation(operator=Add)` and `Call(func=Attribute(attr=Name("format")))` and `BinaryOperation(operator=Modulo)` (where left is `SimpleString`) and rewrite identically.
- **G201 transform**: When in an `except` block (detect via parent chain) AND the call is `.error(...)` AND `exc_info=True` is in kwargs → rename to `.exception(...)` and drop `exc_info` kwarg. Combine with G004 rewrite if message is an f-string.
- **Side-effecting expressions**: If an f-string contains a call expression (`f"{compute()}"`), preserve evaluation order — extract to a local `_tmp = compute()` statement immediately before the logging call, then pass `_tmp` as the positional arg. This guarantees evaluation parity.
- **Walrus**: Lift the walrus assignment out of the f-string into a preceding statement.
- **Idempotency**: Skip any logging call whose message arg is already a `SimpleString` (no `FormattedString`, no `BinaryOperation`, no `.format()`).
- **Tranche boundary**: Tranche by line number (sorted ascending). After applying ~200 conversions, write the file and commit. Re-run codemod from scratch on next tranche — the idempotency guarantee makes already-converted sites no-ops.
- **Compliance tool**: `tools/check_compliance.py` already detects CONV-LOG-FSTRING. Use its output to count remaining sites between tranches.
- **Black + ruff format**: Run `python -m black MistHelper.py` and `python -m ruff format MistHelper.py` after each tranche to normalize line wrapping of the newly-spread argument lists.

### 9. UI Behavior & Automated Testing

**N/A** — This refactor touches zero web UI, zero CLI prompts, zero menu items, zero HTTP routes. No Playwright assertions are added or modified. The existing Playwright suite MUST continue to pass unchanged as a regression gate, but no UI-behavior contract is defined or modified by #429.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ruff G-rule violation count in `MistHelper.py` drops from **1,142 → 0**.
- **SC-002**: CONV-LOG-FSTRING count in `tools/check_compliance.py` output drops from **1,142 → 0**.
- **SC-003**: 100% of refactored call sites produce byte-identical rendered log output vs. baseline (parity test green).
- **SC-004**: 100% of CI quality gates pass on every tranche commit (no partial-state failures).
- **SC-005**: 0 secret-bearing variables identified in audit remain unredacted in any logging call.
- **SC-006**: Coverage ≥ 70% maintained throughout the sweep.
- **SC-007**: Codemod is idempotent — a second pass produces a 0-byte diff.
- **SC-008**: `"G"` appears in `pyproject.toml` `[tool.ruff.lint] select` after the final commit; CI fails any subsequent PR that reintroduces a G-rule violation.

## Assumptions

- `libcst` is available or installable (pure-Python; already a transitive dep of several project tools).
- `data/compliance_report.md` count of 1,142 (1,099 + 7 + 36) is authoritative as of 2026-06-23.
- Existing logger objects (`logging.getLogger(...)`, module-level `logger = …`, `self.logger`, etc.) behave per stdlib — they accept `(template, *args)` and defer interpolation when level is disabled.
- All in-scope call sites use a finite, enumerable set of logger access patterns matchable by libcst node patterns (verified by spot-check of `data/compliance_report.md` line numbers).
- No call site uses `logging.LoggerAdapter` with a non-standard `process()` override that would change the args contract. (If discovered, that site is flagged and handled case-by-case.)
- Project quality gates currently passing on `main` will remain the floor — this refactor does not introduce new gates beyond enabling ruff `G`.
- The CHANGELOG `YY.MM.DD.HH.MM` UTC format is already in use elsewhere in the repo and is treated as the project standard.

## Key Entities

- **LoggingCallSite**: A single `logging.*` or `<logger>.*` call in `MistHelper.py`. Identified by (file, line, column). Has attributes: logger access pattern, level method, original message expression form (f-string / concat / format / mod), arg list, enclosing `except` (for G201), security-flagged (bool).
- **RenderedLogBaseline**: The frozen pre-refactor fixture mapping (test-case-id → expected rendered string).
- **Tranche**: A commit converting ~200 call sites; passes full CI; revertable in isolation.
- **SecurityAuditEntry**: One row in the audit checklist — call site, suspicious variable name, reviewer disposition (safe / redacted / removed), reviewer initials.

## References

- Compliance report: `data/compliance_report.md` (generated 2026-06-23, 454 KB, lists all 1,099 G004 line numbers plus G003 / G201 sites).
- Ruff rule docs:
  - G003 `logging-string-concat`: https://docs.astral.sh/ruff/rules/logging-string-concat/
  - G004 `logging-f-string`: https://docs.astral.sh/ruff/rules/logging-f-string/
  - G201 `logging-exc-info`: https://docs.astral.sh/ruff/rules/logging-exc-info/
- Python stdlib logging optimization guide: https://docs.python.org/3/howto/logging.html#optimization
- Reference specs (template style): `specs/192-compliance-decomposition-wave1/spec.md`, `specs/195-decompose-top5-functions/spec.md`, `specs/198-radon-complexity-decomposition/spec.md`.
