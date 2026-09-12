# Feature Specification: Safe, Repeatable MistHelper `--test` Clean-Run Workflow

**Feature Branch**: `1020-safe-test-clean-run`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "Create a complete SpecKit feature specification in this repository for a safe, repeatable MistHelper `--test` clean-run workflow." Context: an observed 2026-07-16 run of `MistHelper.py --test` exited 1 after 48.5s, classified 66/197 menu options as safe but invoked zero actions and wrote zero telemetry events because no `.env`/credentials were present in the worktree; the dependency bootstrap auto-installed/upgraded packages into system Python because `.venv\Scripts\python.exe` resolved to the system interpreter; and `src/utils/operation_registry.py` was found to classify unregistered menu options as **safe** by default, which produced 120 warnings for 60 unique unregistered options — including menu **194** ("DESTRUCTIVE: Clone Device Config to Gateway Template") — meaning a credentialed `--test` run could have executed destructive code.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
-->

### User Story 1 - Unregistered menu options never run in `--test` (Priority: P1)

A NOC engineer runs `MistHelper.py --test` against a repository whose menu catalog (`menu_actions`) has grown faster than its safety classification (`OperationRegistry`). Today, any menu option that is not explicitly registered is silently treated as `safe` and would be executed and could be destructive (e.g., menu 194, "Clone Device Config to Gateway Template"). The engineer needs a guarantee that classification drift can never result in an unsafe or unknown action being invoked, in either `--test` or `--testinteractive` mode.

**Why this priority**: This is the actual safety defect described in the observed run. It is the highest-impact, highest-risk item because a credentialed run today can execute destructive operations without any explicit opt-in. It must be fixed before any other improvement in this feature is meaningful.

**Independent Test**: Can be fully tested by adding a new, unregistered menu option key to `menu_actions` (or a test double standing in for it) and running the classification/selection logic (unit-level, no live API calls, no credentials required) to confirm the option is excluded from the safe/interactive-safe sets and is instead surfaced as a loud, actionable warning/error — never executed.

**Acceptance Scenarios**:

1. **Given** a menu option key that exists in `menu_actions` but has no entry in `OperationRegistry`, **When** `--test` (systematic) classification runs, **Then** the option is excluded from the safe-options list, is not invoked, and is reported to the operator as an unregistered/unclassified option requiring attention (not silently skipped and not silently run).
2. **Given** the same unregistered-option scenario, **When** `--testinteractive` classification runs, **Then** the option is excluded from the interactive-safe list for the same reasons.
3. **Given** menu option `194` ("Clone Device Config to Gateway Template"), **When** classification is evaluated, **Then** it is explicitly classified as `destructive` in `OperationRegistry` (not defaulted) and is never selected by `--test` or `--testinteractive`.
4. **Given** the full current `menu_actions` catalog, **When** a guardrail/coverage test compares its keys against `OperationRegistry`'s registered keys, **Then** the test fails loudly (in CI and locally) if any key is missing from the registry, so future menu additions cannot silently regress to fail-open behavior.
5. **Given** a previously safe, explicitly registered option, **When** classification runs, **Then** its behavior is unchanged (no regression to existing safe automation).

---

### User Story 2 - `--test` runs inside an isolated virtual environment, not system Python (Priority: P2)

A NOC engineer runs `MistHelper.py --test` (or the validation loop that wraps it) in a fresh clone/worktree that has no `.venv`. Today, the dependency bootstrap detects missing/outdated packages and installs/upgrades them wherever the current interpreter happens to live — which can be the system Python — silently mutating a shared environment outside the project's control. The engineer needs the tool to either use a real isolated virtual environment or refuse to silently mutate system Python.

**Why this priority**: This is a real environment-integrity and reproducibility problem that was directly observed, but it is not itself a safety-to-production issue the way User Story 1 is — no destructive Mist API calls result from it. It is prioritized second because it blocks trustworthy, repeatable validation runs.

**Independent Test**: Can be fully tested by invoking the dependency-bootstrap entry point with a controlled/fake interpreter path (unit-level, dependency-injected `sys`/`os` modules, no real package installs) and asserting that: (a) when the running interpreter is not an isolated virtual environment, auto-install/upgrade is refused with a clear message and a non-zero, distinguishable outcome rather than silently proceeding; and (b) when the running interpreter is a genuine virtual environment, the existing install/upgrade behavior proceeds unchanged.

**Acceptance Scenarios**:

1. **Given** the process is running under an interpreter where `sys.prefix == sys.base_prefix` (i.e., not a virtual environment) and auto-install has not been explicitly force-enabled, **When** the dependency bootstrap runs, **Then** it does not install or upgrade any package, and it prints/logs a clear, actionable message telling the operator to create/activate a project virtual environment (or explicitly opt in) before continuing.
2. **Given** the process is running under a genuine virtual environment (`sys.prefix != sys.base_prefix`), **When** the dependency bootstrap runs, **Then** missing/outdated packages are installed/upgraded exactly as before (no behavior change for the supported case).
3. **Given** an operator explicitly opts in to system-Python installs via an existing or new environment-variable override, **When** the dependency bootstrap runs outside a virtual environment, **Then** it proceeds but logs a loud warning identifying that system Python is being mutated intentionally.
4. **Given** the validation loop (User Story 4) is about to invoke `MistHelper.py --test`, **When** no isolated virtual environment is present and reused per project convention, **Then** the loop fails clearly before invoking `--test`, rather than allowing an ambiguous partial run.

---

### User Story 3 - Clear, secret-safe credential/configuration preflight before a live systematic run (Priority: P3)

A NOC engineer (junior, per audience) runs `MistHelper.py --test` in a worktree with no `.env` file and no Mist credentials in the process environment. Today, the tool proceeds past this missing configuration, attempts to resolve an org id, and mistapi ends up issuing a request to a malformed URL (`https:///api/v1/self`, i.e., empty host) before finally failing. The engineer needs an early, clear, actionable failure that names exactly what is missing and how to fix it (pointing at `deploy/.env.example`), without ever fabricating credentials, discovering secrets on the machine, or writing any secret value into logs, telemetry, or spec/test artifacts.

**Why this priority**: This materially improves operator experience and prevents malformed/wasted API calls, but it is a diagnostic-clarity improvement rather than a safety-boundary fix (User Story 1) or an environment-integrity fix (User Story 2), so it is ordered after both.

**Independent Test**: Can be fully tested by unit/integration tests that unset `MIST_HOST`/`MIST_APITOKEN`/`MIST_API_TOKEN`/org id environment variables, ensure no `.env` file is discoverable in the test's working directory, and assert that the preflight check fails fast with a specific, human-readable message identifying the missing credential(s) and referencing `deploy/.env.example` — before any HTTP request is attempted and without requiring network access or real credentials.

**Acceptance Scenarios**:

1. **Given** no `.env` file and no `MIST_HOST`/`MIST_APITOKEN`/`MIST_API_TOKEN` in the process environment, **When** a live systematic `--test` run is attempted, **Then** the tool fails before issuing any HTTP request, with a message that names the specific missing variable(s) and points to `deploy/.env.example` as the template to copy and fill in.
2. **Given** an org id cannot be resolved (env var, `.env`, or cache all absent, and no interactive session is available), **When** systematic-test context resolution runs, **Then** it fails with a clear, specific message rather than attempting org resolution against an unauthenticated/malformed session.
3. **Given** the preflight check runs, **When** it reports the failure, **Then** no token, host, or org id value is printed, logged, or written into any output artifact (only variable *names* and generic guidance are shown, consistent with the existing token-redaction convention already used elsewhere in the codebase).
4. **Given** a valid `.env` (or equivalent environment variables) with real, non-placeholder credentials is supplied by the operator outside of source control, **When** the preflight check runs, **Then** it passes and the systematic run proceeds normally — this specification does not require creating, storing, or committing any real `.env` file or credential value.
5. **Given** `deploy/.env.example` is the canonical template, **When** documentation or preflight guidance is produced by this feature, **Then** it references that exact file path rather than inventing a new template or duplicating credential documentation.

---

### User Story 4 - Iterative validation loop reaches a documented "clean run" or an explicit "externally blocked" status (Priority: P4)

A developer (or an automated agent) implementing or validating this feature needs a repeatable procedure: run fast local checks first (targeted unit/guardrail tests, lint, type-check, syntax checks), only then run `MistHelper.py --test` under the safe preconditions established by User Stories 1-3, parse its telemetry/log/summary output, apply root-cause fixes for any problem found, and repeat — until either (a) a single run meets a precise, objective "clean run" definition, or (b) the loop determines that a live clean run is impossible in the current environment because credentials are absent, in which case it must report that status honestly rather than claim success.

**Why this priority**: This ties the other three stories together into a repeatable operational procedure and defines what "done" means, so it is the natural closing story, but it has no independent safety value of its own — it depends on Stories 1-3 existing first.

**Independent Test**: Can be fully tested by running the documented validation procedure against the current repository state (or a fixture-controlled variant of it) and confirming that: without credentials, the loop stops at the credential preflight gate (User Story 3) and reports "externally blocked - credentials required for live validation," and never claims a false clean-run success; and that the loop's static/unit-level checks (guardrail tests, lint, type-check, syntax checks) can run and pass/fail deterministically without any credentials or network access.

**Acceptance Scenarios**:

1. **Given** the repository at HEAD, **When** the validation loop's static phase runs (targeted unit/guardrail tests for `OperationRegistry` coverage, existing lint/type/syntax checks), **Then** it completes without requiring any Mist credentials or network access, and reports pass/fail per check.
2. **Given** the static phase passes, **When** the loop proceeds to invoke `MistHelper.py --test`, **Then** it only does so after confirming the User Story 2 (isolated virtualenv) and User Story 3 (credential preflight) preconditions are satisfied; if either precondition fails, the loop stops and reports which precondition blocked it instead of running `--test` in a known-bad state.
3. **Given** `MistHelper.py --test` completes, **When** the loop parses the resulting telemetry file, `script.log`, and the printed summary, **Then** it evaluates the run against the exact "clean run" definition in Success Criteria (SC-006) and reports a pass/fail verdict with the specific metric(s) that failed, if any.
4. **Given** a clean-run failure is detected (e.g., an option errored, an unsafe/unknown option was invoked, telemetry was empty), **When** the loop reports the failure, **Then** it identifies the specific root cause category (classification defect, environment defect, credential defect, functional defect) so a fix can be targeted without re-running the entire loop blindly.
5. **Given** credentials are not available in the current environment (as in the environment this specification was authored in), **When** the loop reaches the point of requiring a live, credentialed clean run, **Then** it reports the final live-validation gate as "externally blocked - operator-supplied credentials required" rather than reporting false success, and documents exactly what the operator must supply (pointing at `deploy/.env.example`) to complete live validation themselves.

---

### Edge Cases

- What happens when `menu_actions` contains an option key that is a numeric-with-suffix variant (e.g., `"26a"`) that has no registry entry? The fail-closed behavior (User Story 1) must apply identically to suffixed keys, since the existing natural-sort helper already treats them as first-class option identifiers.
- What happens when `OperationRegistry` is asked to classify an option that legitimately does not exist in `menu_actions` at all (e.g., a stale test fixture)? Fail-closed behavior must not require the option to exist in `menu_actions` to be handled safely; classification is a pure lookup and should not raise on a name it has never seen.
- How does the system handle an operator who has a `.venv` directory present, but whose `.venv\Scripts\python.exe` is a copy/junction that still resolves to the system installation (the exact condition observed on 2026-07-16, where `sys.prefix == sys.base_prefix` even though a `.venv` folder exists)? The check must rely on interpreter self-report (`sys.prefix`/`sys.base_prefix`), not merely on the presence of a `.venv` directory, so this exact failure mode is caught.
- How does the system handle `DISABLE_AUTO_INSTALL=true` combined with a non-virtualenv interpreter? Auto-install is already disabled by that flag; the new virtualenv guard must not contradict or duplicate that existing override, and the two must compose without conflicting messages.
- What happens when a `.env` file exists but is missing only one of the two required variables (token present, org id absent, or vice versa)? The preflight message must name the specific missing variable, not just say "configuration missing."
- What happens if the validation loop is run in an environment where `deploy/.env.example` itself has been deleted or renamed? The preflight/documentation guidance should degrade to a clear message that the expected template file is missing, rather than crashing or silently omitting guidance.
- What happens when a guardrail/coverage test (User Story 1, Scenario 4) is run against a `menu_actions` catalog that has been extended (e.g., a future menu 197+) without a corresponding registry update? The test must fail with a message listing exactly which option keys are unregistered, so the fix location is obvious.
- What happens to the existing guardrail test that currently expects an unregistered sentinel option (`"9999"`) to default to `safe=True` (see `tests/guardrails/test_wave1_safety_classification_guardrails.py`, `WAVE1_SAFETY_CLASSIFICATION_BASELINE["safe_true"]`)? That expectation directly encodes today's fail-open defect and must be updated as part of this change (see Assumptions and Migration/Compatibility) so the guardrail suite itself does not block the fail-closed fix.

## Requirements *(mandatory)*

### Functional Requirements

**Fail-closed classification (User Story 1)**

- **FR-001**: `OperationRegistry` MUST classify any menu option key that has no explicit registry entry as unsafe-to-run-automatically (i.e., excluded from both the `--test` safe set and the `--testinteractive` interactive-safe set), replacing the current default of implicitly treating unregistered options as `"safe"`.
- **FR-002**: When `OperationRegistry` encounters an unregistered option key, it MUST emit a clearly actionable warning/error (distinguishable from routine skip messages) that names the specific option key and states that it requires an explicit classification entry.
- **FR-003**: The system MUST provide a way to enumerate, at test/build time, every option key present in `menu_actions` and compare it against every key registered in `OperationRegistry`, so that any gap between the two is a detectable, reportable condition rather than a silent runtime default.
- **FR-004**: Menu option `"194"` (Clone Device Config to Gateway Template) MUST have an explicit `destructive` classification entry in `OperationRegistry`, consistent with its labeled behavior in `menu_actions`.
- **FR-005**: All 60 currently-unregistered option keys identified in the observed run (and any others discovered during implementation) MUST receive an explicit classification entry (`safe`, `interactive_safe`, `destructive`, `wip`, `resource_intensive`, `websocket`, `continuous_loop`, or `interactive`) reflecting their actual behavior, determined by inspecting each option's underlying handler.
- **FR-006**: Existing options that are already explicitly registered as `safe` or `interactive_safe` MUST retain their current classification and be unaffected by this change (no regression to already-correct classifications).
- **FR-007**: The fail-closed default MUST apply uniformly to both the `--test` (systematic) and `--testinteractive` code paths; no path may retain a fail-open default.

**Isolated virtual environment enforcement (User Story 2)**

- **FR-008**: Before performing any automatic package install or upgrade, the dependency-bootstrap orchestrator MUST determine whether the running Python interpreter is an isolated virtual environment (using the interpreter's own `sys.prefix`/`sys.base_prefix` — or equivalent — comparison) rather than merely checking for the presence of a `.venv` directory.
- **FR-009**: When the running interpreter is not an isolated virtual environment and no explicit override is set, the orchestrator MUST skip all install/upgrade actions and MUST present a clear, actionable message instructing the operator to create/activate a project virtual environment, reusing the project's existing dependency-bootstrap and environment-variable conventions (e.g., alongside `DISABLE_AUTO_INSTALL`) rather than introducing a parallel mechanism.
- **FR-010**: An explicit, documented override MUST exist for operators who intentionally want to install/upgrade into a non-virtualenv interpreter; using it MUST produce a loud, unambiguous log/console warning identifying that system Python is being modified intentionally.
- **FR-011**: When the running interpreter is a genuine isolated virtual environment, dependency bootstrap behavior MUST be unchanged from today (missing packages installed, outdated packages upgraded per existing `AUTO_UPGRADE_TO_LATEST`/`AUTO_UPGRADE_DEPENDENCIES` semantics).
- **FR-012**: The iterative validation loop (User Story 4) MUST verify the isolated-virtual-environment precondition before invoking `MistHelper.py --test`, and MUST fail clearly, without invoking `--test`, if the precondition is not satisfied and no override is set.

**Secret-safe credential preflight (User Story 3)**

- **FR-013**: Before any live systematic run attempts to reach the Mist API, the system MUST verify that the minimum required configuration (API host and token, and a resolvable organization id) is available from environment variables, a `.env` file, or an already-authenticated session/cache — and MUST fail with a specific, human-readable message identifying exactly which item(s) are missing if not.
- **FR-014**: The preflight failure message MUST reference `deploy/.env.example` by its exact path as the template operators should copy and populate; it MUST NOT generate, guess, or write a real `.env` file, and MUST NOT attempt to discover credentials from other locations on the machine (e.g., shell history, other tools' credential stores, keychains).
- **FR-015**: The preflight check and any related logging/telemetry MUST NOT print, log, or persist any actual token, host override, or org id value; only variable names and generic guidance may appear in output, consistent with the existing redaction convention used elsewhere for tokens.
- **FR-016**: Org-id resolution for a systematic run MUST fail with a specific, actionable error before attempting any network call when no org id can be resolved by any existing precedence path (cache, environment, `.env`, or an authenticated interactive session) and no interactive session is available to prompt with.
- **FR-017**: The preflight check MUST run early enough to prevent the malformed-URL request pattern observed on 2026-07-16 (a request to an empty/blank API host) from ever being attempted.

**Iterative validation loop (User Story 4)**

- **FR-018**: A documented validation procedure MUST exist describing, in order: (1) targeted unit/guardrail tests covering `OperationRegistry` coverage and classification correctness; (2) the project's existing lint, type-check, and syntax checks; (3) the environment and credential preconditions from User Stories 2 and 3; (4) invocation of `MistHelper.py --test`; (5) parsing of the resulting telemetry file, `script.log`, and printed summary; (6) a pass/fail verdict against the clean-run definition (SC-006); (7) root-cause categorization and fix guidance when the verdict is fail; (8) repeat from step 1 until clean or until determined to be externally blocked.
- **FR-019**: The validation procedure MUST distinguish between two terminal states: "clean run achieved" (all criteria in SC-006 met) and "externally blocked" (the environment lacks operator-supplied live credentials, per User Story 3), and MUST NOT report a false "clean run achieved" result when the run was in fact blocked, skipped, or partially executed.
- **FR-020**: When the validation procedure determines the run is externally blocked, it MUST produce a clear statement of exactly what the operator must supply (referencing `deploy/.env.example`) to complete live validation themselves, without the implementer attempting to obtain or fabricate those credentials.
- **FR-021**: The static (no-credentials-required) portion of the validation procedure — guardrail/unit tests, lint, type-check, syntax checks — MUST be independently runnable and MUST NOT require `.env`, network access, or any live Mist credentials to produce a pass/fail result.

### Key Entities *(include if feature involves data)*

- **Menu Option**: A single numbered (optionally lettered-suffix, e.g. `"26a"`) entry in `menu_actions`, pairing a callable handler with a human-readable description. Identified by its string key.
- **Operation Classification**: The `OperationRegistry` entry for a given menu option: a category (`safe`, `interactive_safe`, `destructive`, `wip`, `resource_intensive`, `websocket`, `continuous_loop`, `interactive`) plus an optional skip reason. Determines whether `--test`/`--testinteractive` may invoke the option.
- **Systematic Test Run**: One execution of `MistHelper.py --test`, producing a `TestSummary` (total/passed/failed/skipped counts, elapsed time), a timestamped telemetry file under `data/`, and console/`script.log` output.
- **Credential Preflight Result**: The outcome of checking for API host, token, and org id availability before a live run; either "ready" or a specific, named list of missing items.
- **Virtual Environment Precondition**: The boolean determination of whether the current interpreter is isolated (`sys.prefix != sys.base_prefix`), used to gate dependency-bootstrap install/upgrade behavior.
- **Validation Loop Verdict**: The terminal result of one iteration of the validation procedure: clean-run-achieved, fail-with-root-cause-category, or externally-blocked.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero menu options that lack an explicit `OperationRegistry` entry can be selected for automatic invocation by `--test` or `--testinteractive`, verified by an automated coverage check that compares every `menu_actions` key against `OperationRegistry` and fails if any key is missing.
- **SC-002**: Menu option `194` is verified by an automated test to be classified `destructive` and to never appear in the `--test` or `--testinteractive` safe-option lists.
- **SC-003**: A dependency-bootstrap run performed with a non-virtualenv interpreter (no explicit override) results in zero package installs/upgrades and one clear, actionable message to the operator, verified by an automated test using a simulated non-virtualenv interpreter (no real system-Python mutation performed by the test itself).
- **SC-004**: A credential-preflight run performed with no `.env` file and no Mist environment variables present fails with a specific message naming the missing item(s) and referencing `deploy/.env.example`, before any network request is attempted, verified by an automated test that asserts zero outbound HTTP calls occur in that scenario.
- **SC-005**: No token, API host override, or organization id value ever appears in console output, `script.log`, telemetry files, or any artifact produced by this feature's tests or documentation - verified by inspection/test of the preflight and error-path output.
- **SC-006 (Clean Run Definition)**: A "clean run" of `MistHelper.py --test` is defined as: every option classified `safe` by `OperationRegistry` at the time of the run is attempted exactly once; zero options outside the `safe` category are invoked; zero unregistered/unclassified options are invoked; the run's telemetry file is non-empty and contains a final summary event; the printed summary reports zero failed operations; and the process exits with code `0`. This definition is used, unchanged, by every iteration of the validation loop in User Story 4.
- **SC-007**: When operator-supplied live Mist credentials are not available in the working environment, the final live-validation gate is reported as "externally blocked" with a specific list of what the operator must supply - never reported as a false "clean run achieved."
- **SC-008**: The full static validation phase (targeted guardrail/unit tests plus the project's existing lint, type-check, and syntax checks) completes and reports pass/fail without requiring network access or Mist credentials, on a fresh worktree with no `.env` file present.
- **SC-009**: Junior NOC engineers reading the preflight failure output, the virtual-environment guard message, or an unregistered-option warning can identify the specific missing item or defect and the exact next action to take (e.g., "copy `deploy/.env.example` to `.env` and fill in `MIST_API_TOKEN`") without needing to read source code.

## Assumptions

- The 60 unregistered option keys and their correct classifications are determined by inspecting each option's underlying handler behavior (read-only GET vs. state-changing) during implementation; this specification does not enumerate all 60 by number because that determination is an implementation-time investigation, not a specification-time decision. Menu `194` is called out explicitly because it is already unambiguously labeled destructive in `menu_actions` itself.
- The existing guardrail test `tests/guardrails/test_wave1_safety_classification_guardrails.py` currently asserts that an unregistered sentinel option (`"9999"`) defaults to `is_safe() is True` (see `WAVE1_SAFETY_CLASSIFICATION_BASELINE["safe_true"]`). This assertion directly encodes the fail-open defect this feature removes, so it is expected to require an update (e.g., moving `"9999"` to a "safe_false" / "unregistered" expectation, or replacing the sentinel) as part of implementing FR-001. This is treated as an intentional, in-scope behavior correction to an existing test, not an unrelated regression.
- "Isolated virtual environment" is determined via the interpreter's own `sys.prefix`/`sys.base_prefix` (or `sys.real_prefix` for older virtualenv implementations) comparison, which is the standard, dependency-free way to detect this in Python and matches the root cause already identified in the observed run (`.venv\Scripts\python.exe` resolving with `sys.prefix == sys.base_prefix`).
- The explicit override for installing into a non-virtualenv interpreter builds on the existing `DISABLE_AUTO_INSTALL`-style environment-variable convention already present in `src/bootstrap/dependency_check.py`, rather than introducing an unrelated new mechanism.
- `deploy/.env.example` remains the single canonical credential template referenced by all preflight/documentation guidance produced by this feature; no new template file is created.
- This specification does not require obtaining, generating, or committing real Mist credentials. Live, credentialed validation of the final "clean run" (SC-006/SC-007) is explicitly expected to be performed later by an operator who supplies real credentials outside of source control; until then, the correct and honest status for that final gate is "externally blocked."
- No destructive menu operations (including menu 194 and any other option in the `destructive` category) are exercised, invoked, or tested against a live Mist organization at any point during the implementation or validation of this feature.
- The validation loop and its tests run using only the project's existing test/lint/type-check tooling (pytest, ruff, mypy, existing guardrail-test conventions under `tests/guardrails/`); no new external dependencies are introduced unless an existing tool genuinely cannot express a required check.
- "Unregistered option" and "unclassified option" are treated as synonyms throughout this specification: a menu option key present in `menu_actions` with no corresponding entry in `OperationRegistry`.
