# Feature Specification: LogSanitizer Integration for MistHelper Logging

**Feature Branch**: `200-logsanitizer-integration`
**Created**: 2026-06-11
**Status**: Draft
**Input**: User description: "Integrate upstream `mistapi.__logger.LogSanitizer` into MistHelper's main logging configuration so all log output (file + stdout/stderr) consistently redacts tokens, PSKs, cookies, and Authorization headers."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - NOC engineer shares log file safely (Priority: P1)

A junior NOC engineer hits an error while running a menu operation, captures `data/script.log`, and pastes it into a support ticket or Slack channel. Every Mist API token, PSK value, session cookie, and `Authorization:` header value in that log is replaced with `[REDACTED]` before the engineer ever sees it on disk.

**Why this priority**: This is the entire reason for the feature. Today, an engineer who shares a log can accidentally leak the org-wide Mist API token, which has full read/write authority across every site. One bad paste = full org compromise. P1 because it directly prevents credential exposure.

**Independent Test**: Run any menu operation that produces API traffic with `LOG_LEVEL=DEBUG`. Inspect `data/script.log` and console output. Search the captured text for the known token value, any known PSK string, any cookie value, and the literal string `Authorization: Bearer`. None of those values should appear in plaintext; every occurrence should be `[REDACTED]`.

**Acceptance Scenarios**:

1. **Given** `MIST_TOKEN` is set in the environment and the user runs any data-export menu, **When** the script logs an HTTP request at DEBUG level, **Then** the token value never appears in `data/script.log` or in stdout — only `[REDACTED]` appears in its place.
2. **Given** the user runs a PSK export menu and a PSK value would otherwise appear in a debug log line, **When** the line is written, **Then** the PSK value is replaced with `[REDACTED]`.
3. **Given** an HTTP error response includes a `Set-Cookie` header that the SDK logs, **When** the log record is emitted, **Then** the cookie value is replaced with `[REDACTED]` while the cookie name remains visible for debuggability.
4. **Given** an exception traceback contains a stringified `Authorization: Bearer <token>` header, **When** the traceback is logged, **Then** the token portion is `[REDACTED]` and the rest of the traceback is preserved verbatim.

---

### User Story 2 - Developer verifies redaction with unit tests (Priority: P1)

A maintainer adding a new menu operation can run the test suite locally and immediately see whether their code paths leak secrets to logs. The test suite includes deterministic fixtures that feed known-secret strings through the production logger and assert the output is redacted.

**Why this priority**: Without automated tests, redaction silently regresses the next time someone adds a `logging.debug(f"response={raw}")` line. P1 because regression protection is the only way this feature stays true after the initial implementation.

**Independent Test**: `pytest tests/unit/test_log_sanitizer.py -v` passes. Each test constructs a real `logging.LogRecord`, runs it through the configured MistHelper logger handlers, captures the formatted output, and asserts secrets are absent and `[REDACTED]` is present.

**Acceptance Scenarios**:

1. **Given** the test logger is configured identically to production, **When** a record containing `MIST_TOKEN=abcd1234efgh5678` is logged, **Then** the captured output contains `[REDACTED]` and does not contain `abcd1234efgh5678`.
2. **Given** the same logger, **When** a record contains a PSK in the form `"psk": "supersecret123"`, **Then** the output contains `[REDACTED]` and does not contain `supersecret123`.
3. **Given** the same logger, **When** a record contains `Authorization: Bearer eyJhbGciOi...`, **Then** the output contains `[REDACTED]` and does not contain the bearer value.
4. **Given** the same logger, **When** a record contains an ordinary debug message with no secrets, **Then** the output is byte-identical to what the logger produced before the LogSanitizer filter was added (no false-positive redactions of normal text).

---

### User Story 3 - Existing log format is preserved (Priority: P2)

A maintainer who already greps `data/script.log` for timestamps, log levels, function names, or device MAC addresses sees the exact same line layout after this feature ships. Only secret substrings change; nothing else moves.

**Why this priority**: Operations runbooks, log-shipping pipelines, and grep aliases all depend on the current format. P2 because correctness of redaction (P1) outweighs format stability, but format stability is a hard non-regression requirement.

**Independent Test**: Capture a baseline `data/script.log` from a fixed scenario before the change, then capture another from the same scenario after the change. Diff the two files. The only differences are secret values being replaced by `[REDACTED]` — timestamps, log levels, logger names, message templates, and line counts must otherwise match.

**Acceptance Scenarios**:

1. **Given** a fixture log capture from before the change, **When** the same scenario is rerun after the change, **Then** every non-secret token in every log line is unchanged.
2. **Given** the existing log line prefix format (date, level, logger name, message), **When** any log line is written, **Then** the prefix structure is unmodified.

---

### Edge Cases

- What happens when `LogSanitizer` is not available because `mistapi` is older than 0.59? System MUST detect this at startup and fall back to a built-in no-op-with-warning sanitizer that logs a one-time warning telling the operator to upgrade `mistapi`.
- What happens when a third-party library MistHelper depends on (e.g., `urllib3`, `requests`) logs a secret via its own logger? The filter MUST be attached to the root logger so child loggers inherit it; library logs are also sanitized.
- What happens when a secret appears in `extra={}` kwargs to `logging.*` rather than in the message string? Sanitizer MUST inspect the rendered message (post-formatting), so it catches secrets regardless of how they were passed.
- What happens when a log record contains structured args (e.g., `logging.info("user=%s token=%s", user, token)`)? Sanitizer MUST act on the formatted string after `%`-substitution, not on the raw template.
- What happens when log output is redirected to a pipe (e.g., `| tee` or `| less`)? Redaction MUST apply equally to all stream handlers, not just the file handler.
- What happens when an exception traceback is logged via `logging.exception(...)`? Sanitizer MUST process the rendered traceback string, not just the message.
- What happens when a secret value happens to equal a common English word (false-positive risk)? Out of scope — sanitizer trusts upstream `mistapi.LogSanitizer` patterns; we do not add custom patterns in this feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST install `mistapi.__logger.LogSanitizer` as a `logging.Filter` on the root Python logger during MistHelper startup, before any other log line is emitted.
- **FR-002**: System MUST also attach the same `LogSanitizer` filter to every named `logging.Handler` MistHelper creates (file handler for `data/script.log`, stream handler for stdout/stderr, any additional handlers added by managers like `WebSocketManager` or `SSH` runners).
- **FR-003**: System MUST sanitize the fully rendered log message — including `%`-substituted args, `extra` fields, and exception tracebacks — not just the raw format string.
- **FR-004**: System MUST replace each detected secret value with the literal string `[REDACTED]` and MUST leave all surrounding context (timestamps, log level, logger name, line numbers, non-secret message text) byte-identical to pre-feature output.
- **FR-005**: System MUST work transparently for child loggers used elsewhere in the code (e.g., `logging.getLogger(__name__)` in any module under `src/`); operators MUST NOT need to attach the filter manually in new modules.
- **FR-006**: System MUST detect at startup whether `mistapi.__logger.LogSanitizer` is importable. If unavailable (older `mistapi` versions), system MUST log a single WARNING line ("LogSanitizer unavailable; upgrade mistapi>=0.59 to enable secret redaction") and continue running without a filter rather than crashing.
- **FR-007**: System MUST NOT introduce any new CLI flag, environment variable, or menu option to enable/disable redaction — redaction is always on whenever the dependency is present.
- **FR-008**: System MUST NOT change the log file path (`data/script.log`), log level defaults, log formatter format string, or log rotation behavior.
- **FR-009**: System MUST include the LogSanitizer filter installation in the same code path used by both interactive (`python MistHelper.py`) and non-interactive (`--menu N`, `--test`) invocations.
- **FR-010**: System MUST provide a unit test module (`tests/unit/test_log_sanitizer.py`) with at minimum: one test per secret category (token, PSK, cookie, Authorization header), one negative test verifying non-secret text passes through untouched, and one test verifying tracebacks are sanitized.
- **FR-011**: System MUST remove the no-op `LogSanitizer` shim currently embedded in `tests/conftest.py` (lines ~211–221) once the real upstream class is wired in, OR adapt that shim to import the real class when available so tests reflect production behavior.
- **FR-012**: System MUST keep total line coverage of the logging-configuration code path at or above 70% as measured by `pytest --cov`.

### Key Entities

- **Logging configuration entry point**: The single function or block in `MistHelper.py` that calls `logging.basicConfig(...)` (or equivalent handler setup) at startup. This is the integration site.
- **LogSanitizer filter**: An instance of `mistapi.__logger.LogSanitizer`. Implements `logging.Filter` protocol (has a `filter(record)` method that mutates `record.msg` and `record.args` in place and returns `True`).
- **Log handlers**: The set of `logging.Handler` instances MistHelper installs — currently a `FileHandler` for `data/script.log` plus a `StreamHandler` for console. Any new manager that adds its own handler is a downstream consumer of this feature.
- **Secret categories**: Token (Mist API token), PSK (pre-shared key for WLAN), Cookie (session cookie value), Authorization header value (Bearer / Basic). These are the four classes upstream `LogSanitizer` already recognizes; this feature does not add new categories.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After this feature ships, zero plaintext Mist API tokens, PSK values, session cookies, or Authorization header values appear in `data/script.log` across all 194 menu operations when each is exercised with valid credentials and DEBUG-level logging.
- **SC-002**: Unit test suite `tests/unit/test_log_sanitizer.py` runs in under 5 seconds locally and passes on every CI run with zero flaky failures over a rolling 30-day window.
- **SC-003**: Side-by-side diff of `data/script.log` from a fixed scenario, before vs after the change, shows differences ONLY on lines where redaction occurred — no spurious format changes, no line-count drift.
- **SC-004**: A maintainer adding a new menu operation does not need to take any explicit action to get log redaction; the next time they run their feature, secrets in their new debug lines are already redacted because the filter is on the root logger.
- **SC-005**: When `mistapi` is downgraded to a version that lacks `LogSanitizer`, MistHelper starts successfully, emits exactly one WARNING about the missing dependency, and runs normally (just without redaction).

## Assumptions

- The version of `mistapi` pinned in `requirements.txt` and `pyproject.toml` is >= 0.59 and therefore ships `LogSanitizer`. If a future pin downgrades below this, FR-006 graceful fallback applies.
- Upstream `LogSanitizer` correctly identifies all four secret categories (token, PSK, cookie, Authorization) without producing meaningful false positives on normal MistHelper log content. We trust upstream pattern accuracy rather than re-validating each pattern in this feature.
- All MistHelper code uses the standard `logging` module via `logging.*` or `logging.getLogger(__name__)`. There is no parallel logging system (e.g., a custom print-based logger) that bypasses Python `logging`.
- The current logging configuration is centralized — there is a single `logging.basicConfig` call (or equivalent) early in `MistHelper.py` startup. If decentralized logger setup exists in submodules, the implementation phase will add filter installation to each site.
- The `tests/conftest.py` shim was added only to keep the test suite green while production code lacked any LogSanitizer reference. Removing it (FR-011) does not affect any test that does not directly assert on redaction.
- Coverage measurement uses the existing `pytest --cov` configuration in `pyproject.toml`; no new coverage tooling is required.
- The 194-operation count is current as of CHANGELOG entry for menu 194. If new menus are added before this ships, the SC-001 wording should be updated to match the then-current count.
