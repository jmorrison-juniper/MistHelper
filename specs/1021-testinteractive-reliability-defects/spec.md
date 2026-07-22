# Feature Specification: `--testinteractive` Reliability Defects

**Feature Branch**: `1021-testinteractive-reliability-defects` (not created — see Extension Hooks note in completion report; existing branch `copilot/test-interactive-morrison-org-run` was retained)

**Created**: 2026-07-22

**Status**: Draft

**Input**: User description: "In the current workspace, create exactly one planning-only SpecKit feature specification for the user's verified --testinteractive reliability defects... [seven verified defects: telemetry masking, site selector silent fallback, site_id injection coverage gap, wan_client_events AttributeError, unsupported --test-interactive flag, --help side effects, and test-suite coverage gap]"

## Summary

`MistHelper.py --testinteractive` is the operator-facing smoke-test harness that walks every operation registered as `interactive_safe` in `OperationRegistry` and reports a pass/fail telemetry summary. A verified, reproducible investigation of this harness found **seven independent reliability defects** that together mean the harness's "PASS" result is not trustworthy evidence that interactive operations work correctly against a real Mist org/site. This specification documents each defect as an independently deliverable user story with precise observed behavior, required corrected behavior, acceptance criteria, and test coverage intent. **This is a planning-only specification.** No source code, tests, configuration, GitHub issues/PRs/branches, or commits are created or modified as part of this spec; it exists to scope and sequence future fix work.

## Verified Evidence (as reported by the user)

- Running `MistHelper.py --testinteractive` walks `OperationRegistry.interactive_safe_options` and exits with code `0`, reporting telemetry `pass_count=44`, `fail_count=0` — while the run's own log output contains **32 `ERROR` lines spanning 31 distinct operations**.
- Setting `MIST_INTERACTIVE_TEST_SITE='Morrison House Site'` (exact site name) correctly resolves to site id `cf36153a-97bb-4974-8f8f-e9cc25d64d83`. Setting the shorthand `MIST_INTERACTIVE_TEST_SITE='Morrison House'` (partial name) does **not** match, and the harness **silently** falls back to a different site, `ArchangelMichael`, without a clear, prominent, run-terminating signal that the requested site could not be resolved.
- Of the 44 `interactive_safe` handlers exercised, only **4** accept a `site_id` parameter in their signature. The runner injects `site_id` only when the handler's signature exposes that parameter; for the remaining 40 handlers, the runner invokes them with no site context. Handlers that prompt for input, receive a cancellation/EOF, and then `return` normally are tallied as a **pass** — identical telemetry to a handler that genuinely succeeded.
- Interactive-safe menu option 203 (`SiteClientExporter.wan_client_events`, backed by `WanClientEventsExporter`) raises `AttributeError: module 'mistapi.api.v1.sites.wan_clients' has no attribute 'events'` against the installed SDK version `mistapi==0.63.3`. The code path calls `mistapi.api.v1.sites.wan_clients.events.search.searchSiteWanClientEvents`; the installed SDK instead exposes `searchSiteWanClientEvents` directly on `mistapi.api.v1.sites.wan_clients`.
- The documented, supported flag is `--testinteractive` (no hyphen). A user invoking `--test-interactive` (hyphenated) does not receive the interactive test harness and is not told the flag is invalid/misspelled.
- Invoking `MistHelper.py --help` triggers automatic dependency installation/import initialization **before** the help text is printed and the process exits — i.e., `--help` is not side-effect-free.
- The existing focused unit-test suite for the interactive test runner (`tests/unit/troubleshooting/test_interactive_test_runner.py` and related guardrail tests) passes 20/20 tests, none of which reproduce or detect any of the six behavioral defects above.
- All investigation was performed against a **read-only** Mist org/site. Any future fix/verification work for these defects **must** preserve remote read-only access; only local log/artifact files may be created or modified, and only in clearly isolated, explicitly controlled locations.

## User Scenarios & Testing *(mandatory)*

<!--
  Each user story below corresponds to exactly one verified, independently deliverable defect.
  Stories are ordered P1 (highest impact / delivered first) through P7 (delivered last), forming
  the requested serial delivery order. Each story is independently testable: fixing it in isolation
  produces an observable, valuable improvement in harness trustworthiness, even before the other
  stories are addressed.
-->

### User Story 1 - Telemetry Must Reflect Real Outcomes, Not Just Absence of Exceptions (Priority: P1)

An operator runs `--testinteractive` to get a trustworthy pass/fail signal for every interactive-safe operation before relying on the tool against a live org. Today the operator sees `pass_count=44`, `fail_count=0`, and exit code `0` — a clean bill of health — even though the run's own log contains 32 `ERROR` lines across 31 of the 44 exercised operations. The operator has no way to know, from the reported telemetry alone, that roughly 70% of exercised operations logged an error during the run. This is the single highest-impact defect because it makes the harness's headline result actively misleading rather than merely incomplete.

**Why this priority**: The telemetry is the primary (and often only) signal an operator consults after a run. If it can report a full pass while the majority of operations logged errors, every other defect in this specification is effectively invisible to normal use — this must be corrected first so that subsequent fixes are independently verifiable through trustworthy telemetry.

**Independent Test**: Can be fully tested by running `--testinteractive` against a fixture/mock set of handlers where some handlers internally log an error and then return normally, and confirming the reported `fail_count` (or an equivalent explicit "errored" tally) reflects those operations rather than reporting them as passes. Delivers value on its own: any operator re-running the harness after this fix alone gets a materially more trustworthy signal, independent of whether the other six defects are yet fixed.

**Acceptance Scenarios**:

1. **Given** an interactive-safe handler that logs one or more `ERROR`-level messages during its own execution and then returns normally (without raising), **When** `--testinteractive` runs that handler, **Then** the run's final telemetry MUST NOT classify that handler's outcome identically to a handler that completed with no logged errors.
2. **Given** a completed `--testinteractive` run, **When** the operator inspects the reported summary, **Then** the summary MUST make it possible to determine, without re-reading the full log, how many exercised operations logged at least one error during the run.
3. **Given** a completed `--testinteractive` run where one or more operations logged errors, **When** the harness determines its process exit code, **Then** the exit code MUST distinguish an all-clean run from a run containing operation-level errors.

---

### User Story 2 - Site Selector Resolution Must Not Silently Substitute a Different Site (Priority: P2)

An operator sets `MIST_INTERACTIVE_TEST_SITE` to scope `--testinteractive` to a specific, known-safe test site before running it against a live org. Today, if the operator provides a value that does not exactly match a site's id or full name (e.g., a natural shorthand like `Morrison House` instead of the full site name `Morrison House Site`), the harness silently substitutes the first available site returned by the org (observed: a completely unrelated site, `ArchangelMichael`) and proceeds to run all 44 operations against it — with no prominent signal that the intended scoping failed. Given the tool's read-only, org-facing nature, running against the wrong site undermines the operator's ability to trust *which* site was actually exercised.

**Why this priority**: This is a scope-integrity and trust defect distinct from Story 1 — even with perfect telemetry, an operator who believes they tested "Morrison House" but actually tested "ArchangelMichael" has been silently misled about what was verified. It ranks second because it directly affects the safety/trust guarantees the harness exists to provide, ahead of narrower defects.

**Independent Test**: Can be fully tested by setting `MIST_INTERACTIVE_TEST_SITE` to a value that does not exactly match any site id or full site name in a fixture/mock org, running `--testinteractive`, and confirming the run either (a) fails closed with a clear, prominent error identifying the unresolved selector, or (b) proceeds only after emitting an unmistakable (not merely debug/warning-level) notice identifying the substituted site by name/id. Delivers value independent of other stories: operators immediately regain the ability to trust which site was targeted.

**Acceptance Scenarios**:

1. **Given** `MIST_INTERACTIVE_TEST_SITE` is set to a value that does not exactly match any candidate site's `id` or full `name`, **When** `--testinteractive` resolves the target site, **Then** the harness MUST clearly and prominently report that the requested selector did not resolve, before any operation is executed against a substituted site.
2. **Given** the harness selects a fallback site because the requested selector did not resolve, **When** the run's summary/report is produced, **Then** it MUST name the actual site (id and name) that was used, adjacent to the reported selector value that failed to match.
3. **Given** `MIST_INTERACTIVE_TEST_SITE` exactly matches a site's `id` or full `name`, **When** `--testinteractive` resolves the target site, **Then** the harness MUST use that exact site with no fallback substitution.

---

### User Story 3 - Site-Scoped Coverage Must Be Representative, Not Silently Degraded (Priority: P3)

Of the 44 `interactive_safe` operations exercised by `--testinteractive`, only 4 handler signatures accept a `site_id` parameter that the runner can inject. The remaining 40 are invoked with no site context; many of these prompt interactively for input and, upon receiving a cancellation or EOF (as happens in a non-interactive/scripted test run), return normally. The runner currently cannot distinguish "this operation ran meaningfully against the resolved test site" from "this operation was invoked, immediately hit a cancelled prompt, and returned" — both currently register as an identical pass.

**Why this priority**: This defect is the structural reason Story 1's masking is so severe (40/44 handlers have no reliable way to exercise real site-scoped behavior), but it is independently deliverable and independently valuable: even before telemetry semantics change, simply knowing *which* of the 44 operations were genuinely site-scoped versus merely invoked-and-returned materially improves an operator's ability to trust the result.

**Independent Test**: Can be fully tested by running `--testinteractive` against a fixture set containing both `site_id`-aware and non-`site_id`-aware handlers, some of which simulate a cancelled prompt, and confirming the run's report distinguishes "invoked with site context and completed" from "invoked without site context / exited via prompt cancellation" for each of the 44 operations. Delivers value independent of the other stories.

**Acceptance Scenarios**:

1. **Given** an interactive-safe handler whose signature does not accept `site_id`, **When** `--testinteractive` invokes it, **Then** the run's report MUST record that this operation was exercised without site context, distinguishably from operations that were.
2. **Given** a handler that prompts for input and receives a cancellation/EOF in the non-interactive test context, **When** the handler returns normally after that cancellation, **Then** the run's report MUST NOT record this outcome identically to a handler that completed a full, uncancelled execution.
3. **Given** a completed `--testinteractive` run, **When** the operator reviews the summary, **Then** they MUST be able to determine, per operation, whether it was genuinely exercised against the resolved test site or merely invoked without site scope.

---

### User Story 4 - `SiteClientExporter.wan_client_events` Must Call a Callable That Exists in the Installed SDK (Priority: P4)

Interactive-safe menu option 203, `SiteClientExporter.wan_client_events` (backed by `WanClientEventsExporter`), unconditionally raises `AttributeError: module 'mistapi.api.v1.sites.wan_clients' has no attribute 'events'` when run against the currently installed `mistapi==0.63.3`. The code references a nested attribute path (`wan_clients.events.search.searchSiteWanClientEvents`) that does not exist in this SDK version; the installed SDK instead exposes `searchSiteWanClientEvents` directly on `mistapi.api.v1.sites.wan_clients`.

**Why this priority**: This is a concrete, single-operation crash with a clear, narrow fix surface — lower systemic priority than Stories 1-3 (which affect trust in the harness as a whole) but it is a fully reproducible, unconditional failure of one specific interactive-safe operation and should be corrected before broader flag/UX polish.

**Independent Test**: Can be fully tested by invoking option 203 (`SiteClientExporter.wan_client_events`) against a mocked/stubbed `mistapi` client exposing only the `0.63.3` surface (`countSiteWanClients`, `searchSiteWanClients`, `searchSiteWanClientEvents` directly on `sites.wan_clients`) and confirming the call succeeds without `AttributeError`. Delivers value independently: this option becomes usable regardless of whether other stories are fixed.

**Acceptance Scenarios**:

1. **Given** the installed `mistapi` SDK version exposes `searchSiteWanClientEvents` directly on `mistapi.api.v1.sites.wan_clients` (as in `0.63.3`), **When** menu option 203 / `wan_client_events` is invoked, **Then** it MUST call that existing callable and MUST NOT raise `AttributeError` for a missing `.events` attribute.
2. **Given** option 203 is exercised as part of `--testinteractive`, **When** the run completes, **Then** this operation's outcome MUST be reported as a genuine success or failure based on the actual SDK call result, not a masked pass (see Story 1).

---

### User Story 5 - Unsupported Flag Variants Must Be Rejected Clearly, Not Silently Misrouted (Priority: P5)

The documented, supported flag for the interactive test harness is `--testinteractive` (no hyphen). A user who types the more naturally-hyphenated `--test-interactive` does not receive the interactive test harness, and receives no clear indication that the flag they typed is invalid, unrecognized, or a likely misspelling of a supported flag.

**Why this priority**: This is a CLI ergonomics/discoverability defect. It is real and reproducible but affects only the moment of invocation (a user can recover simply by re-reading the documented flag name) rather than the correctness or trust of a run that did start — ranked below Stories 1-4 accordingly.

**Independent Test**: Can be fully tested by invoking `MistHelper.py --test-interactive` and confirming the process either (a) exits with a clear, actionable error naming the unrecognized flag and suggesting `--testinteractive`, or (b) is otherwise not silently treated as equivalent to omitting the flag entirely without any notice. Delivers value independently of all other stories.

**Acceptance Scenarios**:

1. **Given** a user invokes the CLI with `--test-interactive` (hyphenated) instead of the documented `--testinteractive`, **When** argument parsing completes, **Then** the tool MUST clearly communicate that this flag is not recognized, rather than silently proceeding as if no test flag were given.
2. **Given** the tool detects an unrecognized flag that closely resembles a supported one, **When** it reports the error, **Then** the message SHOULD name the closest supported flag to reduce operator confusion.

---

### User Story 6 - `--help` Must Be Side-Effect-Free (Priority: P6)

Invoking `MistHelper.py --help` currently triggers automatic dependency installation/import initialization before the help text is printed and the process exits. An operator who only wants to see usage information is forced to incur the cost (and any side effects) of full dependency initialization first.

**Why this priority**: This is an operational-hygiene defect with a narrow, well-understood blast radius (only affects `--help` invocations) — ranked below all correctness/trust defects above.

**Independent Test**: Can be fully tested by invoking `MistHelper.py --help` in an environment instrumented to detect whether dependency installation/import initialization occurred, and confirming it does not occur before help text is printed and the process exits. Delivers value independently: `--help` becomes fast and side-effect-free regardless of the state of other stories.

**Acceptance Scenarios**:

1. **Given** a user invokes `MistHelper.py --help` (or `-h`), **When** the process runs, **Then** it MUST print usage/help text and exit without performing dependency installation or import initialization beyond what is required to parse arguments and render help.
2. **Given** `--help` is combined with other flags (e.g., `--testinteractive --help`), **When** argparse recognizes the help flag, **Then** the same side-effect-free behavior MUST apply.

---

### User Story 7 - Automated Test Coverage Must Detect These Defect Classes (Priority: P7)

The existing focused unit-test suite for the interactive test runner (`tests/unit/troubleshooting/test_interactive_test_runner.py` and related guardrail tests) currently passes 20/20 tests. None of these tests reproduce or would detect any of the six behavioral defects described in Stories 1-6. This means a regression reintroducing any of these defects in the future would pass the existing suite undetected.

**Why this priority**: This story is delivered last because it is best framed, and best written, once the required corrected behavior for Stories 1-6 is understood and (at least partially) implemented — it closes the loop by ensuring the suite can actually catch these defect classes going forward, whether as regression tests proving each fix or as tests that first demonstrate the current gap.

**Independent Test**: Can be fully tested by adding test cases to the existing suite that (a) fail against the current, unfixed behavior for each of Stories 1-6 (demonstrating the gap), and (b) pass once each corresponding story's corrected behavior is implemented. Delivers value independently: even before every story's fix lands, each new test provides a documented, automated tripwire for its corresponding defect.

**Acceptance Scenarios**:

1. **Given** the current (pre-fix) runner behavior, **When** new tests targeting Stories 1-6 are run against it, **Then** each new test MUST fail in a way that clearly demonstrates the corresponding defect (masked telemetry, silent site substitution, non-representative site_id coverage, the option 203 `AttributeError`, the unrecognized `--test-interactive` flag, or the `--help` side effect).
2. **Given** each story's corrected behavior is implemented, **When** its corresponding new test(s) are run, **Then** they MUST pass, and the existing 20 tests MUST continue to pass unmodified in behavior (though they may need updates if they encoded the defective behavior as expected).
3. **Given** the full updated suite, **When** it is executed, **Then** it MUST run entirely against read-only Mist API interactions or fully mocked/stubbed clients — no test may perform a write/mutating call against a live Mist org or site.

---

### Edge Cases

- What happens when `MIST_INTERACTIVE_TEST_SITE` is unset entirely (no selector provided at all), as opposed to being set to a non-matching value? The harness's existing "no selector provided" path is out of scope for Story 2's fix unless it currently exhibits the same silent-substitution behavior.
- How does the harness behave when the org has zero sites available for fallback (no site to substitute)?
- How should telemetry (Story 1) and per-operation site-context reporting (Story 3) interact when a single operation both logs an internal error AND lacks site_id support — must both conditions be independently visible in the report, or is a single combined "not reliably verified" classification acceptable?
- What happens when a handler raises an exception AND has already logged an `ERROR` line internally before raising — is this already correctly counted as a fail today (per the runner's existing try/except), and if so, Story 1 must not regress that already-correct path?
- How should `--test-interactive` (Story 5) be handled if a future flag with that exact hyphenated spelling is intentionally added for an unrelated purpose? The corrected behavior must not preclude future legitimate flags that happen to resemble `--testinteractive`.
- Does the `--help` fix (Story 6) need to account for `-h` as well as `--help`, and for combinations where `--help` appears alongside other flags in any order?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `--testinteractive` harness MUST report, for each exercised interactive-safe operation, whether that operation logged one or more errors during its own execution, even when it did not raise an exception.
- **FR-002**: The `--testinteractive` harness's final telemetry (pass/fail counts and process exit code) MUST NOT report a fully clean result (all-pass, exit code 0) when one or more exercised operations logged an error during the run.
- **FR-003**: The `--testinteractive` harness MUST resolve `MIST_INTERACTIVE_TEST_SITE` such that any value not exactly matching a candidate site's `id` or full `name` is treated as an unresolved selector, and MUST prominently report this condition before proceeding.
- **FR-004**: When the harness proceeds using a fallback/substituted site (whether by design or as an explicitly permitted degraded mode), it MUST report the actual site used (id and name) in a way that is at least as visible as the originally requested selector value.
- **FR-005**: The `--testinteractive` harness's per-operation report MUST distinguish operations invoked with resolved site context from operations invoked without site context (i.e., whose handler signature does not accept `site_id`).
- **FR-006**: The `--testinteractive` harness MUST distinguish an operation that completed a full execution from one that returned early due to a cancelled/EOF interactive prompt, in its per-operation report.
- **FR-007**: The interactive-safe operation `SiteClientExporter.wan_client_events` (menu option 203) MUST invoke a callable that exists on the currently supported/pinned `mistapi` SDK version, without raising `AttributeError`.
- **FR-008**: The CLI MUST clearly reject or flag unrecognized flag variants (including but not limited to `--test-interactive`) rather than silently proceeding as though no test flag were supplied.
- **FR-009**: Invoking `MistHelper.py --help` (or `-h`) MUST print usage/help text and exit without first performing dependency installation or import initialization.
- **FR-010**: The automated test suite covering the interactive test runner MUST include test cases that detect each of the defect classes described in User Stories 1-6, in addition to the existing 20 passing tests.
- **FR-011**: All corrected behavior and all new/modified automated tests MUST interact with the remote Mist org/site in a strictly read-only manner; no functional requirement in this specification may be satisfied by introducing a write/mutating remote call.
- **FR-012**: Any new local log or report artifacts produced to satisfy these requirements (e.g., enriched telemetry output) MUST be written to clearly isolated, explicitly controlled local locations, consistent with existing artifact-handling conventions in the codebase.

### Key Entities

- **Interactive Test Run**: A single execution of `MistHelper.py --testinteractive`; has a resolved target site, an ordered list of exercised operations, and a final telemetry summary (pass/fail counts, exit code).
- **Interactive-Safe Operation**: An entry in `OperationRegistry` categorized as `interactive_safe`; identified by a menu option number/name; has a handler function whose signature may or may not accept `site_id`.
- **Operation Outcome**: The per-operation result of one Interactive Test Run; must be able to represent at minimum: clean success with site context, clean success without site context, cancelled/prompt-exited without site context, internally-logged error without a raised exception, and raised exception.
- **Site Selector**: The value of `MIST_INTERACTIVE_TEST_SITE` (or its absence); resolves to either an exact-matched site, an unresolved state, or (today, defectively) a silently substituted fallback site.
- **CLI Flag**: A recognized or unrecognized command-line argument; `--testinteractive` is the sole supported spelling for enabling the interactive test harness.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator reviewing the summary of a `--testinteractive` run can, without reading the full log, correctly determine whether any exercised operation logged an error — verified by the run's reported counts/exit code alone matching the actual number of operations that logged errors, for 100% of runs.
- **SC-002**: When `MIST_INTERACTIVE_TEST_SITE` does not exactly match any site's id or full name, 100% of `--testinteractive` runs prominently report the unresolved-selector condition before any operation executes against a substituted site.
- **SC-003**: An operator can, for every one of the 44 exercised operations in a run's report, correctly determine whether that operation was exercised with real site context, without cross-referencing source code.
- **SC-004**: Menu option 203 (`wan_client_events`) completes without raising `AttributeError` in 100% of runs against the currently pinned `mistapi` SDK version.
- **SC-005**: 100% of unrecognized test-flag variants (including `--test-interactive`) produce a clear, actionable message to the operator rather than silent misrouting.
- **SC-006**: `MistHelper.py --help` completes in a time and with a side-effect profile consistent with argument-parsing-only work (no dependency installation/import initialization observed) in 100% of invocations.
- **SC-007**: The automated test suite for the interactive test runner grows from 20 passing tests with zero coverage of these defect classes to a suite where each of the six behavioral defect classes has at least one dedicated, currently-failing-against-defective-behavior test case.
- **SC-008**: Zero write/mutating calls are made against the remote Mist org/site across all verification activity performed to satisfy this specification's stories.

## Assumptions

- The installed `mistapi` SDK version remains pinned at (or compatible with) `0.63.3` for the purposes of grounding Story 4; if the project upgrades `mistapi` in the future, Story 4's fix must be re-validated against the new version's API surface, which is outside this specification's scope.
- `OperationRegistry.interactive_safe_options` continues to expose 44 operations at the time any future implementation work begins; the exact count may drift as operations are added/removed, but the defect classes described here (masking, site scope, coverage representativeness) apply regardless of the exact count.
- The remote Mist org/site used for any future verification of these stories remains a designated read-only test org/site (as it was during the evidence-gathering that produced this specification); no story in this specification requires or permits provisioning new write access.
- `MIST_INTERACTIVE_TEST_SITE` remains the mechanism by which an operator scopes `--testinteractive` to a specific site; this specification does not propose changing that mechanism's name or introducing a new selector mechanism, only correcting its match/fallback/reporting behavior.
- This specification intentionally does not prescribe specific code changes, function signatures, or file-level diffs — only the required end-state behavior — consistent with its planning-only scope; a subsequent `/speckit.plan` phase is expected to determine implementation approach for each story.
- Fixing Stories 1-6 does not require adding new external dependencies; all corrected behavior is expected to be achievable using the existing runner architecture, logging, and telemetry mechanisms already present in the codebase.
