# Phase 0 Research: `echo()` Helper and Legacy Console-Echo Migration

**Feature**: `1031-warning-echo-refactor`
**Date**: 2026-07-27

This document consolidates the research that resolved every open decision in the plan. No `NEEDS CLARIFICATION` marker remains.

## R-1: Formatting style (`%`-style vs f-string)

**Decision**: Use `%`-style deferred formatting throughout `echo()`. Signature is `echo(msg: str, *args: object) -> None`. The stdout write uses `msg % args if args else msg`. The log call uses `logger.info(msg, *args)`.

**Rationale**:

- The 170 legacy call sites already use `logging.warning("%s: %s", key, description)` form. Preserving `%`-style means the migration is a single-token substitution (`logging.warning` -> `echo`) with zero argument reshaping. This is what makes the mechanical rewrite safe (FR-012).
- `logger.info(msg, *args)` defers formatting until a handler chooses to emit, which is what principle VII of the constitution requires ("Use `%s` style formatting in logging calls (not f-strings) for performance and security").
- FR-005 requires that a plain literal containing a `%` character does not crash when no args are passed. The `msg % args if args else msg` guard delivers this directly: when `args` is empty, no formatting attempt is made.

**Alternatives considered**:

- **f-string / `.format()` inside `echo()`**: rejected. Would require every migrated call site to convert its args into a formatted literal, violating FR-012 and requiring 170 individual manual edits rather than a mechanical rewrite.
- **Auto-detect `%` and skip formatting when none present**: rejected. Fragile: a message like `"100% signal"` would incorrectly opt into formatting if any args were passed. The explicit `args` check is honest and predictable.

## R-2: Output destination (stdout vs stderr)

**Decision**: `echo()` writes to `sys.stdout` (via `print(...)`). Never to `sys.stderr`.

**Rationale**:

- The spec's Edge Cases section explicitly states: "Console output uses `print(msg % args if args else msg)` or an equivalent stdout write. The helper does not write to stderr."
- Today's legacy behavior via `logging.warning` writes to the root logger's console handler, which is configured to `sys.stdout` for MistHelper. Preserving stdout keeps SC-003 (byte-identical stdout diff) achievable.
- Interactive users pipe or redirect MistHelper's stdout for scripting. A stderr switch would silently break those scripts.

**Alternatives considered**:

- **stderr**: rejected. Would break SC-003 and every existing pipe / redirection.
- **Configurable via env var**: rejected. Adds a knob that nobody asked for and nobody will tune. Violates the spec's "intentionally minimal" language for the helper.

## R-3: Logger identity (root vs named)

**Decision**: `echo()` uses a module-level named logger: `_LOGGER = logging.getLogger(__name__)` where `__name__` resolves to `src.utils.console` (or `utils.console` depending on invocation, matching how other `src/utils/` modules bind their loggers).

**Rationale**:

- Greppability: an operator investigating `data/script.log` can filter for the `console:` origin if they want to see only user-facing echoes.
- Consistency: `src/utils/logger_utils.py`, `src/utils/input_utils.py`, and `src/utils/subprocess_runner.py` all bind to their module logger. `echo()` follows the same convention.
- Propagation: named loggers propagate to the root logger's handlers by default. File handler capture in `data/script.log` continues to work with no configuration change (FR-014).

**Alternatives considered**:

- **Root logger (`logging.getLogger()`)**: rejected. Loses greppability. Also inconsistent with the rest of `src/utils/`.
- **Custom logger named `"echo"`**: rejected. Wins nothing over `__name__` and hides the module of origin.

## R-4: Helper location (`src/utils/console.py`)

**Decision**: New module at `src/utils/console.py`. Import path is `from src.utils.console import echo` in every migrated file.

**Rationale**:

- The repo's `src/utils/` directory holds cross-cutting primitives (`logger_utils`, `input_utils`, `subprocess_runner`, `tqdm_wrapper`, `environment_utils`, `file_path_utils`). `console.py` fits the naming and role of that layer.
- Existing symbols were surveyed: no `console.py`, no `echo` symbol, no import path collision. `src.utils.console` is a green field.
- Placing the helper in a new module keeps the diff auditable. Adding it to an existing utility module would mix a public helper with pre-existing internals and complicate CODEOWNERS review.
- Every migrated file imports from the same path, satisfying FR-011.

**Alternatives considered**:

- **Add to `src/utils/logger_utils.py`**: rejected. That module is about logger configuration; `echo()` is about user-facing output. Mixing concerns is a smell and would bury the helper.
- **New top-level `src/console.py`**: rejected. Would fragment `src/` and set a precedent for top-level primitives that the current layout does not follow.
- **`MistHelper.py` itself**: rejected. Import cycles: many `src/reports/*.py` cannot import from `MistHelper.py` cleanly.

## R-5: Marker discriminator and multi-line variant

**Decision**: The rewrite tool identifies each legacy call by the exact trailing string `# Legacy console echo routed via logger.`. Both variants are handled:

- **Same-line**: `    logging.warning("=" * 60)  # Legacy console echo routed via logger.`
- **Closing-paren-line**: the marker rides on the line that closes the `logging.warning(...)` call across multiple lines.

For each match, the tool:

1. Locates the enclosing `logging.warning(...)` call (may span multiple lines).
2. Rewrites the `logging.warning` token to `echo`.
3. Deletes the `# Legacy console echo routed via logger.` marker and its leading whitespace (`  ` two spaces) from the trailing comment position.
4. Preserves everything else on the line, including any surrounding whitespace on non-marker positions and any adjacent inline comments (none exist in the tree today, but the tool is defensive).

If the tool cannot resolve a match (for example, malformed multi-line call), it fails loudly with the file path and line number. It never silently skips a marked site.

**Rationale**:

- Verified in the tree: both variants exist. `MistHelper.py` line 2504 shows same-line form; the block around `msp_privileges` shows closing-paren-line form.
- FR-007, FR-008, FR-009, SC-001 all key off exact marker matching. A structured AST rewrite (e.g. `libcst`) would be safer than regex but adds a heavyweight dependency for a one-off job. A carefully scoped regex plus post-condition grep (SC-001) is sufficient.

**Alternatives considered**:

- **`libcst`-based rewrite**: rejected as heavy for a one-off tool that will be deleted after the merge.
- **Manual per-file editing**: rejected. 170 sites is above the manual-error threshold; the marker exists precisely so the rewrite can be scripted.

## R-6: Helper docstring content

**Decision**: The `echo()` docstring follows the global `DOCS.md` policy exactly: one-line summary, blank line, "Why" section, `Args` / `Returns` sections in Google style. STE applies to the prose.

Draft body:

```
Print a message to stdout and record it in the log at INFO.

Why:
    Replaces the legacy pattern of routing user-facing menu, prompt,
    and progress text through `logging.warning(...)`. That pattern
    polluted the WARNING channel of `data/script.log` with thousands
    of menu-render lines and buried genuine warnings. `echo()` keeps
    interactive output on stdout for the user and records an audit
    trail at INFO so operators can still see what the user saw.

Args:
    msg: The message text. May contain `%s` / `%d` format specifiers.
    *args: Values to substitute into `msg` with `%`-style formatting.
        If empty, `msg` is used as-is with no formatting attempt.

Returns:
    None.
```

**Rationale**: DOCS.md requires the "Why" section and Google-style Args/Returns. `pydoclint --style=google` enforces the structure. `interrogate ≥90%` covers the coverage floor. The STE guide keeps the prose short and imperative.

## R-7: Unit-test structure

**Decision**: Tests live at `tests/unit/utils/test_console.py`. Use `capsys` for stdout capture and `caplog` for log record inspection. Four test cases match FR-015 exactly:

1. `test_echo_plain_literal_prints_stdout_and_logs_info` — plain string, no args, one INFO record, stdout matches.
2. `test_echo_percent_s_percent_d_formats_stdout_and_log_args` — `"Site %s has %d APs"` with args, stdout has fully formatted text, log record args are `(name, count)` with `msg` still the format string.
3. `test_echo_literal_percent_no_args_does_not_raise` — `"100% signal"` with no args, no exception, no double format.
4. `test_echo_never_emits_at_warning` — assert `all(record.levelno < logging.WARNING for record in caplog.records)` and `all(record.levelno == logging.INFO for record in caplog.records)` after several calls.

Plus one supplementary test:

5. `test_echo_multiple_calls_do_not_duplicate_handlers` — call `echo` 10 times, assert the `console` module logger's handler count is unchanged (helper does not attach any handler).

**Rationale**: `capsys` + `caplog` are already used across the tests suite. Matches the layout of neighbors `test_environment_utils.py` and `test_input_utils_wave9.py`. The five cases satisfy all FR-015 sub-clauses (a, b, c, d) plus the "does not duplicate handlers" clause from the planning inputs.

## R-8: What happens to the 32 legitimate warnings

**Decision**: They stay exactly as they are. The migration script does not touch any `logging.warning(...)` call that lacks the marker. Manual verification post-refactor: `grep -R "logging.warning" src MistHelper.py | grep -v "Legacy console echo"` — every remaining match must be inspected and confirmed as a genuine warning.

Baseline: the input description quotes ~32 legitimate calls (matplotlib import failure, UV package-manager error, requirements-file parse errors, mistapi access errors, tqdm fallback). If the post-refactor count differs materially from ~32, that is a red flag that a legacy site was missing its marker and got left behind — the human reviewer investigates before merge.

**Rationale**: FR-009 and FR-013. The count check is a cheap sanity gate that catches the "missing marker on a legacy site" failure mode that the spec's Edge Cases already flags.
