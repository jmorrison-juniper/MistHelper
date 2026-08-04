# Feature Specification: Replace Legacy Console-Echo WARNINGs With an INFO-Level `echo()` Helper

**Feature Branch**: `1031-warning-echo-refactor`

**Created**: 2026-07-27

**Status**: Implemented and merged in pull request #1694. Four tasks stay open. Three of them argue their outcome by construction, because the team never captured the baseline. One of them needs a manual launch.

**Input**: User description: "Replace ~170 legacy WARNING-level user-facing console echoes with a new `echo()` helper that prints the message to stdout so users still see it, and records it in the log at INFO level so we retain an audit trail of what was shown to the user. This removes semantic pollution from the log's WARNING channel without changing any user-visible behavior or altering any legitimate warning."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Restore signal in `data/script.log` for on-call operators (Priority: P1)

An on-call engineer opens `data/script.log` after a MistHelper run to find out whether anything went wrong. Today the file is dominated by thousands of `WARNING - N:` lines that are just menu items being printed to the console; real warnings (matplotlib import failure, UV package-manager error, mistapi access denied, tqdm fallback) are buried in the noise. After this change, the same run produces a `script.log` where every WARNING line is a genuine warning and menu / prompt / progress text appears at INFO.

**Why this priority**: This is the direct reason the feature exists. Semantic pollution of the WARNING channel is what the ticket asks us to fix. Once the 170 legacy call sites emit at INFO instead of WARNING, an on-call engineer scanning `script.log` for "WARNING" sees only genuine warnings and can act on them immediately.

**Independent Test**: Run MistHelper end-to-end (open the main menu, pick one non-destructive report, exit). Grep `data/script.log` for `WARNING -`. Before this change the count is in the thousands and dominated by menu items and prompts. After this change the count is small (only genuine warnings such as matplotlib import failure, UV errors, mistapi access errors, tqdm fallback) and no line matches a menu render, prompt render, or progress message.

**Acceptance Scenarios**:

1. **Given** a MistHelper run that renders the main menu and exits, **When** the operator opens `data/script.log`, **Then** zero lines at level `WARNING` contain menu-item text, prompt text, or progress text.
2. **Given** the same run, **When** the operator opens `data/script.log`, **Then** every menu-item, prompt, and progress line that was shown on the console also appears in the log at level `INFO` with the same message text.
3. **Given** a MistHelper run in which `mistapi` raises an access-denied error, **When** the operator opens `data/script.log`, **Then** the access-denied line is still at level `WARNING` (it is a real warning and MUST NOT be downgraded).

---

### User Story 2 - Preserve byte-identical console output for interactive users (Priority: P1)

A network engineer using MistHelper interactively must not see any change in what appears on the console. Every menu prompt, every progress message, every input prompt line that appeared before must still appear, with the same text, in the same place, in the same order. The refactor is invisible from the console side.

**Why this priority**: This is co-P1 with Story 1 because a regression here would break the tool for every interactive user. There is no partial credit: if a single legacy echo stops printing to stdout, an interactive menu becomes unusable.

**Independent Test**: Capture stdout of a scripted MistHelper run (main menu render, pick one report, exit) both before and after the change. Diff the two captures. The diff must be empty.

**Acceptance Scenarios**:

1. **Given** an identical scripted MistHelper session recorded before and after the refactor, **When** the two stdout captures are diffed, **Then** the diff is empty.
2. **Given** an interactive menu that previously showed "N:  Report name" via a legacy WARNING echo, **When** the same menu renders after the refactor, **Then** the same line appears on stdout with identical text, identical whitespace, and identical trailing newline.
3. **Given** a legacy call site that used positional args (for example `logging.warning("Site %s has %d APs", name, count)`), **When** the same site is rewritten to `echo("Site %s has %d APs", name, count)`, **Then** the console line is the fully formatted string with `name` and `count` substituted, matching the pre-refactor output byte for byte.

---

### User Story 3 - Remove self-documented tech debt from the codebase (Priority: P2)

A MistHelper contributor opens `MistHelper.py` or one of the six affected reports and sees no more `# Legacy console echo routed via logger.` markers. The pattern that admitted "this is a workaround because the console handler is at WARNING level" is gone from the tree. A new contributor can no longer copy the legacy pattern by mistake, because the pattern no longer exists.

**Why this priority**: This is important for long-term maintainability but is not a runtime concern. Stories 1 and 2 already deliver the operational value. Story 3 is what makes the fix stick in the codebase and prevents regression by copy-paste.

**Independent Test**: Run `grep -R "Legacy console echo routed via logger" src MistHelper.py`. It must return zero matches.

**Acceptance Scenarios**:

1. **Given** the refactor is complete, **When** a contributor searches the tree for the literal string `# Legacy console echo routed via logger.`, **Then** zero matches are returned.
2. **Given** the refactor is complete, **When** a contributor searches the tree for `logging.warning` in the seven affected files, **Then** every remaining match is a genuine warning (matplotlib import failure, UV error, requirements-file parse error, mistapi access error, tqdm fallback, or similar).

---

### Edge Cases

- A legacy call site uses `%s` / `%d` positional formatting args. The new `echo(msg, *args)` MUST accept and forward args so that the console line and the INFO log line both contain the fully formatted message.
- A legacy call site uses no args at all (plain literal string). `echo("Menu")` MUST print `Menu` and log `Menu` at INFO with no formatting attempt (no crash on stray `%` characters in the literal).
- A legacy call site passes an already-formatted f-string (no `%` args). Same as above: no double-format, no crash on `%` in the literal.
- A non-marker `logging.warning(...)` call is textually similar to a legacy one but lacks the `# Legacy console echo routed via logger.` marker comment. The refactor MUST NOT touch it. This is what the marker is for.
- A marker comment appears on the line above the `logging.warning(...)` call instead of trailing it. The refactor MUST still identify and migrate the call, or the tool MUST fail loudly rather than silently leaving the site unmigrated. (Planning must decide whether the marker is same-line-only or also above-line; see Assumptions.)
- A legacy call site is inside a `try/except` block that swallows exceptions. The `echo()` helper MUST NOT raise on any input the legacy call would have accepted; behavior on malformed args stays at least as tolerant as `logging.warning` was.
- The root logger's console handler configuration is unchanged. The `echo()` helper achieves stdout output by calling `print()` (or an equivalent stdout write), not by re-elevating an INFO record to WARNING at the handler layer.
- Two legacy sites on adjacent lines: rewriting one MUST not shift line numbers in a way that breaks the migration of the other. (This is a mechanical concern for the refactor tooling.)

## Requirements *(mandatory)*

### Functional Requirements

#### The `echo()` helper

- **FR-001**: The codebase MUST expose a single `echo(msg, *args)` helper function. It lives in a project utility module (either a new module or an existing `src/utils/` module chosen in planning; see Assumptions).
- **FR-002**: `echo(msg, *args)` MUST write the fully formatted message to stdout so that interactive users see it, matching the pre-refactor console output byte for byte.
- **FR-003**: `echo(msg, *args)` MUST also emit a log record at level `INFO` with the same message and args, using the standard `logging` module, so the audit trail of what was shown to the user is preserved.
- **FR-004**: `echo(msg, *args)` MUST NOT emit at level `WARNING` under any circumstance. Emitting at WARNING is what this feature is deleting; regressing on this defeats the purpose.
- **FR-005**: `echo(msg, *args)` MUST accept both plain literal strings (no args) and printf-style format strings with args (`%s`, `%d`, etc.), and MUST NOT crash on a literal string that contains a `%` character when no args are passed.
- **FR-006**: `echo(msg, *args)` MUST carry a docstring that follows the project DOCS.md rules: one-line summary, a Why section explaining why the helper exists (replaces the WARNING-level console-echo workaround), and Args / Returns sections. STE applies to all prose.

#### Migration of the 170 legacy call sites

- **FR-007**: Every `logging.warning(...)` call whose line carries the marker comment `# Legacy console echo routed via logger.` MUST be rewritten to `echo(...)` with message text and args preserved verbatim.
- **FR-008**: The trailing marker comment MUST be removed from every migrated line. After the refactor, zero occurrences of the literal string `# Legacy console echo routed via logger.` remain anywhere in the tree.
- **FR-009**: The refactor MUST NOT touch any `logging.warning(...)` call that does not carry the marker comment. This includes calls in the same file, on adjacent lines, or with textually similar messages.
- **FR-010**: The refactor MUST cover all 170 call sites across the seven files named in the input description (MistHelper.py, src/reports/e911_bssid.py, src/reports/offline_device_reporter.py, src/reports/global_wired_client_report_generator.py, src/reports/wired_client_manufacturer_report_generator.py, src/reports/sfp_transceiver_data_processor.py, src/auth/interactive/clouds.py).
- **FR-011**: Each migrated file MUST import the `echo` helper. The import path is a planning decision (see Assumptions) but MUST be the same across every migrated file.
- **FR-012**: The refactor MUST NOT change any surrounding code: no reordering, no message text edits, no arg reordering, no removal of adjacent comments other than the marker comment itself.

#### Preservation of legitimate warnings

- **FR-013**: The ~32 legitimate `logging.warning(...)` calls that remain in the seven affected files after the refactor MUST continue to log at level `WARNING` with no change to text, args, or surrounding code.
- **FR-014**: The refactor MUST NOT alter the root logger's handler configuration. Console handler level, file handler level, and formatter strings all remain as they are today.

#### Quality gates

- **FR-015**: New unit tests MUST cover the `echo()` helper: (a) a plain literal string prints to stdout and emits one INFO log record, (b) a `%s`/`%d` format string with args prints the formatted message to stdout and emits one INFO record with the same formatted message, (c) a literal string that contains a `%` character but no args does not raise, (d) no code path in `echo()` emits at WARNING.
- **FR-016**: All existing quality gates (ruff, black, mypy, pytest, pydocstyle, interrogate ≥90 percent, pydoclint Google style, radon CC ≤10, bandit, vulture, pip-audit, pylint) MUST remain green after the refactor. The refactor introduces no new lint waivers.
- **FR-017**: The refactor introduces no new menu entries and therefore requires no change to `src/utils/operation_registry.py`.
- **FR-018**: All new or modified prose (docstrings, unit-test docstrings, code comments) MUST follow the Simplified Technical English writing guide at `documentation/ASD-STE100_writing-guide.md` and MUST pass the existing STE lint (introduced by feature 1026).

### Key Entities

- **`echo()` helper**: The new single function that replaces the legacy pattern. It has two responsibilities: (1) write the formatted message to stdout so interactive users see it, (2) emit a log record at INFO so the audit trail records what the user was shown. It is intentionally minimal, has no I/O of its own beyond stdout and the logger, and is trivially testable.
- **Legacy console-echo call site**: Any line in the seven affected files that (a) calls `logging.warning(...)` and (b) carries the marker comment `# Legacy console echo routed via logger.`. There are exactly 170 of them today. Each one becomes an `echo(...)` call after the refactor.
- **Legitimate warning call site**: Any line in the tree that calls `logging.warning(...)` without the marker comment. There are approximately 32 such lines in MistHelper.py and a handful in the reports. These lines are intentionally left alone.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A `grep -R "# Legacy console echo routed via logger." src MistHelper.py` after the refactor returns exactly zero matches.
- **SC-002**: A `grep -R "logging.warning" src MistHelper.py | grep "Legacy console echo"` after the refactor returns exactly zero matches.
- **SC-003**: A stdout capture of a scripted MistHelper run (main menu render, pick one report, exit) diffed against the same capture taken before the refactor produces an empty diff (byte-identical console output).
- **SC-004**: The same scripted run produces a `data/script.log` in which zero WARNING-level lines contain menu-item, prompt, or progress text. The count of WARNING-level lines drops from the current baseline (roughly 7,900 per sample run) to a small number bounded above by the count of genuine warnings actually raised during the run.
- **SC-005**: 100 percent of the 170 legacy sites listed in the input description are migrated. The per-file counts after the refactor are exactly zero legacy markers in each of: MistHelper.py, src/reports/e911_bssid.py, src/reports/offline_device_reporter.py, src/reports/global_wired_client_report_generator.py, src/reports/wired_client_manufacturer_report_generator.py, src/reports/sfp_transceiver_data_processor.py, src/auth/interactive/clouds.py.
- **SC-006**: The full local quality-gate suite (ruff, black, mypy, pytest with the new `echo()` unit tests, pydocstyle, interrogate ≥90 percent, pydoclint, radon CC ≤10, bandit, vulture, pip-audit, pylint, STE lint) passes with zero new failures introduced by the refactor.
- **SC-007**: An operator scanning `data/script.log` after a real MistHelper run can identify every genuine warning by grepping for `WARNING` without having to filter out menu-render noise.

## Assumptions

- The helper name is `echo`. If planning finds a naming collision with an existing symbol in the target import path, planning may rename to `echo_stdout` or `echo_to_user`; the name change is a planning decision and does not affect this spec's behavior contract.
- The helper lives in an existing utility module under `src/utils/`. Planning picks the exact module. The important property for this spec is that every migrated file imports `echo` from the same path.
- The marker comment `# Legacy console echo routed via logger.` appears on the same line as the `logging.warning(...)` call it marks (trailing-comment form). If planning finds any occurrence where the marker sits on the line above instead, planning MUST decide whether to (a) treat both forms as valid markers or (b) fail loudly on the above-line form so a human can migrate it. Either choice satisfies FR-009 as long as the tool does not silently skip a marked site.
- Console output uses `print(msg % args if args else msg)` or an equivalent stdout write. The helper does not write to stderr. The current legacy behavior via `logging.warning` writes to the root logger's console handler (which is on stdout for MistHelper) so this preserves the destination.
- The helper does not add its own logger name; it uses the standard `logging` module at INFO on the module-level or root logger consistent with how the legacy `logging.warning` calls resolved. Planning picks whether to bind to a named logger for greppability.
- The refactor is mechanical and can be done with a scripted edit driven by the marker comment (planning may write a one-off migration script or use ruff-fix-style tooling). The spec does not mandate a particular tool; the required outcome is what the 170 lines look like after, not how they got there.
- The ~32 remaining `logging.warning` call sites in MistHelper.py that are legitimate warnings (matplotlib import failure, UV package-manager errors, requirements-file parse errors, mistapi access errors, tqdm fallback) are correctly untouched. Planning verifies this count against the tree at implementation time; if the count differs, the discrepancy is investigated before the refactor is landed (a mismatched count would suggest a legacy site is missing its marker comment).
- Docstring for the new helper follows DOCS.md: one-line summary of what it does, a Why block explaining that it replaces the legacy WARNING-level console-echo pattern that was polluting the WARNING channel with menu-render noise, and Args / Returns sections. STE applies to the prose.
- No change to `src/utils/operation_registry.py` because the refactor does not add any menu entry. If planning discovers a reason to add one (for example a debug menu for the helper), the registry entry is added at that time; today the spec's expectation is no registry change.
- Unit tests for `echo()` use `capsys` (or the project's existing stdout-capture pattern) plus `caplog` at INFO to assert both the stdout write and the log-record level. The tests live alongside the other util tests under `tests/`.
