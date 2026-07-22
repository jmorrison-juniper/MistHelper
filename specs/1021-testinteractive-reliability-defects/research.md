# Research: `--testinteractive` Reliability Defects

## Scope and evidence

Research was limited to local source, local tests, and the already-created issue mapping. No source, test, configuration, GitHub, Mist, branch, commit, or PR state was changed.

The current runner invokes every `interactive_safe` handler in `src/troubleshooting/interactive_test_runner.py`. A normal return is emitted as `test_pass`; only an exception becomes `test_fail`. `TelemetryEmitter` derives the overall status from `TestSummary.failed`, so a handler that logs an error then returns is falsely represented as clean. The runner resolves an exact id/case-insensitive full-name selector, but falls back to the first site after a selector miss. It injects `site_id` only for signatures declaring that parameter. `InputUtils.safe_input` intentionally converts EOF and Ctrl+C to normal return values, which explains why a cancelled prompt can look like a successful no-op.

## Decisions

### 1. Treat handler-originated error logs as an operation failure (#1636)

**Decision**: Install a temporary, scoped logging observer only for the duration of one handler invocation. It records `ERROR`-and-higher records originating during that call and passes the observation into the operation outcome/telemetry summary. An observed error log yields a non-clean operation result and non-zero suite result even if no exception escapes.

**Rationale**: `_run_single_option()` is the smallest common seam around each operation. Capturing there preserves existing handler contracts, does not add network calls, and directly addresses the verified false pass. The observer must be removed in `finally` so later options cannot contaminate the outcome.

**Alternatives considered**:

- Scan `script.log` after the suite: rejected because attribution to individual operations is ambiguous and concurrent/unrelated records could be counted.
- Treat all warning records as failure: rejected because warnings include intentional operator notices, including EOF handling.
- Require every handler to raise after logging: rejected as a broad migration across approximately 44 registry entries.

### 2. Fail closed for an explicitly unmatched site selector (#1637)

**Decision**: When `MIST_INTERACTIVE_TEST_SITE` is non-empty and does not exactly match a site id or full name, stop before the operation loop and report the requested selector as unresolved. Do not select a fallback site in that path. Preserve the existing no-selector path, which is outside this feature unless it independently fails.

**Rationale**: A fail-closed result is clearer and safer than prominently announcing an unintended substitute. It guarantees no interactive operation runs against a site the operator did not select.

**Alternatives considered**:

- Keep first-site fallback with a high-visibility banner: permitted by the specification but rejected because it still executes against an unintended site.
- Partial/fuzzy matching: rejected because the requirements mandate exact id or full-name matching.

### 3. Model site context and prompt termination explicitly (#1638)

**Decision**: Add structured per-operation context/outcome observations: whether `site_id` was injected, whether the invocation observed EOF or interrupt cancellation through the canonical `InputUtils.safe_input` seam, and whether execution otherwise completed cleanly. Do not infer cancellation from an empty string or a free-form log line.

**Rationale**: The runner's `inspect.signature()` decision is already the source of truth for site-context injection. `safe_input()` is the canonical EOF/interrupt boundary and can expose a test-run-scoped structured observation. This is narrow, deterministic, and avoids changing every interactive handler.

**Alternatives considered**:

- Declare every interactive-safe handler must accept `site_id`: rejected as a broad handler/registry refactor outside the six defects.
- Infer cancellation from a handler's normal return or stdout: rejected as unreliable; both occur in valid success paths.
- Parse `[EOF]` or `[INTERRUPT]` text from logs: rejected as fragile and not a stable programmatic contract.

### 4. Use the installed WAN-client-events endpoint surface (#1639)

**Decision**: Change only the option-203 endpoint lookup to `mistapi.api.v1.sites.wan_clients.searchSiteWanClientEvents`.

**Rationale**: Local investigation and the feature evidence verify that this direct member exists in `mistapi==0.63.3`; the current nested `.events.search` member raises `AttributeError`.

**Alternatives considered**:

- Add a runtime version/namespace compatibility adapter: rejected because the supported version is known and the adapter expands scope without a current requirement.
- Upgrade the SDK: rejected as unrelated dependency work.

### 5. Reject the unsupported spelling rather than making it an alias (#1640)

**Decision**: Explicitly detect `--test-interactive` as an unsupported look-alike and exit non-zero with a message suggesting `--testinteractive`. Leave only the documented spelling as the test-harness activation flag.

**Rationale**: This meets the CLI requirement while preserving the hyphenated name for a possible future, different flag.

**Alternatives considered**:

- Register it as an alias: rejected because it silently expands the public interface and precludes the future namespace distinction called out by the specification.
- Rely on the present parser behavior: rejected because the current flow silently reaches the normal interactive menu.

### 6. Parse help before deferred initialization (#1641)

**Decision**: Introduce a minimal early help detection/parser phase that can print the full parser help and exit before `MainEntrypoint.run()` initializes deferred imports, probes tqdm, or initializes dependencies. Non-help invocations keep the normal pipeline.

**Rationale**: `MainEntrypoint.run()` currently calls deferred initialization before `parse_args()`, so argparse's built-in help exit is too late. An early, help-only path is smaller and lower risk than refactoring all entrypoint dependencies to accept pre-parsed arguments.

**Alternatives considered**:

- Pass pre-parsed arguments through a redesigned entrypoint: rejected because it changes the entrypoint contract more broadly.
- Allow imports then suppress install output: rejected because it does not meet the side-effect-free requirement.

### 7. Keep all verification local and mock-first

**Decision**: Add a focused regression with every issue. The default verification suite uses fixtures, mocks, and temporary directories. An optional smoke test may call only read-only Mist endpoints after all local tests pass and only with explicit operator-provided credentials/site selector. Telemetry files stay within a controlled `data/` subdirectory.

**Rationale**: This validates the defect classes without risking the remote Mist organization and satisfies the specification's isolated-artifact rule.

**Alternatives considered**:

- Live-org testing as the primary proof: rejected because it is slower, credential-dependent, and creates avoidable remote exposure.
- Writing telemetry beside source/test files: rejected because it violates local artifact isolation.
