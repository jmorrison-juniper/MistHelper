# Feature Specification: Unattended token skip for menu 247

**Feature Branch**: `fix/4744-unattended-token-skip`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Issue #4744: the unattended interactive run reports menu 247 as passed when the email change token prompt gets no answer."

**Issue**: #4744 (labels `bug` and `tests`). Related: #1785, #2753, #3308, #4358, #4607. Depends on: #4607, merged on 2026-11-13.

## Key Terms

- **Option**: A menu number that the interactive test runner exercises. Menu 247 is option 247.
- **Unattended run**: A `--testinteractive` run. The runner installs an input provider for each option.
- **Operator-only prompt**: A prompt whose answer only an operator can supply.
- **Token prompt**: The menu 247 prompt for the email change token. Its context is `verify_self_email.token`.
- **Skip event**: The telemetry event `test_skip` that the runner writes for one option.
- **Skip reason**: The `skip_reason` text that the operation registry holds for an option.
- **Input seam**: The `safe_input` attribute of `InputUtils`. The runner replaces it for one option.

## Clarifications

### Session 2026-11-26

- Q: The issue allows a skip or another non-success outcome. Which outcome applies? A: Skip. The unattended run never supplies the token. A skip records that known precondition. See D-1 in `design/research.md`.
- Q: May the unattended run send a token or call the endpoint? A: No. The issue requires an empty token and no endpoint call.
- Q: Does the registry category of menu 247 change? A: No. Menu 247 stays `interactive_safe`, and its skip reason stays the same.
- Q: Do empty answers to optional prompts keep their meaning? A: Yes. An optional prompt with no rule still returns an empty answer.
- Q: Are the runner and test paths current on main? A: Yes. Both paths appear in `design/research.md` with blob SHAs. Pull request #4607 is merged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a blocked menu 247 as skipped (Priority: P1)

An operator runs `--testinteractive` unattended. Menu 247 needs an email change token. Only the operator can supply that token. The runner writes one skip event for option 247. It writes no pass event.

**Why this priority**: A false pass reports coverage that did not happen. The operator then trusts a result that no test produced.

**Independent Test**: A mocked regression runs option 247 through the runner. The handler is the real `SelfAccountExporter.verify_email`. The SDK function and the writer are mocks. The regression checks the event, the counters, the skip reason, the restored input seam, and the absence of calls.

**Acceptance Scenarios**:

1. **Given** an unattended run of option 247, **When** the token prompt gets no answer, **Then** the runner writes a skip event with the skip reason.
2. **Given** the same run, **When** the option ends, **Then** the runner writes no pass event and no fail event.
3. **Given** the same run, **When** the option ends, **Then** the input seam is restored, and the SDK mock and the writer mock record no calls.

### User Story 2 - Keep the interactive token path and optional prompts unchanged (Priority: P1)

An operator runs menu 247 in an interactive session. An empty token still prints the existing cancel line. The menu makes no SDK call. An unattended run of another option still continues past an optional empty prompt.

**Why this priority**: The change must not alter a working operator flow or the outcome of other menus.

**Independent Test**: The existing exporter tests and the existing provider tests pass with their assertions unchanged.

**Acceptance Scenarios**:

1. **Given** an interactive session, **When** the operator enters an empty token, **Then** the menu prints the existing cancel line and calls no SDK function.
2. **Given** an unattended run, **When** an optional prompt has no rule, **Then** the input provider returns an empty answer, and the option continues.

### User Story 3 - Count skips apart from passes and failures (Priority: P2)

A run with a skipped option reports the skip in the summary. A run that exercises no option fails.

**Why this priority**: The summary drives the coverage decision. It must separate what ran from what did not run.

**Independent Test**: A loop test and a summary test use a fake handler. The fake handler stops at an operator-only prompt.

**Acceptance Scenarios**:

1. **Given** one passing option and one skipped option, **When** the loop runs, **Then** it returns one pass, zero failures, and one skip.
2. **Given** only a skipped option, **When** the summary runs, **Then** the summary reports one skipped operation, and the verdict is failure.

### Edge Cases

- An operator-only prompt receives a configured default answer. The default applies, and the option continues.
- A handler wraps the token prompt in a broad exception handler. The skip signal is lost, and the option can pass. Caution: only option 247 uses an operator-only context today. The regression detects this path.
- The exporter changes the token prompt context. The input provider treats the prompt as optional. The regression fails because the option passes.
- A run contains only option 247. The run exercises zero operations, so the verdict is failure.
- A required prompt has no rule. The option fails with a prompt harness failure, as before.
- The registry holds a blank skip reason. The runner uses its existing fallback text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The runner MUST write one skip event for option 247 when the token prompt gets no answer in an unattended run.
- **FR-002**: The skip event MUST carry the skip reason that the registry holds for the option.
- **FR-003**: The skip event MUST use skip category `operator_prompt` and test mode `interactive-operator-prompt`.
- **FR-004**: The runner MUST write no pass event and no fail event for an option that an operator-only prompt ends.
- **FR-005**: The runner MUST NOT increase the prompt harness failure count for an operator-only skip.
- **FR-006**: The runner MUST count an operator-only skip only in the skipped total of the suite summary.
- **FR-007**: The unattended run MUST NOT call `mistapi.api.v1.self.update.verifySelfEmail` for option 247.
- **FR-008**: The unattended run MUST NOT write the verification audit row for option 247.
- **FR-009**: The runner MUST restore the original input seam after an operator-only skip.
- **FR-010**: An optional prompt with no rule MUST return an empty answer.
- **FR-011**: A required prompt with no rule MUST keep raising `PromptResolutionError`.
- **FR-012**: The interactive path of menu 247 MUST keep its cancel behavior for an empty token.
- **FR-013**: The suite verdict MUST be failure when a run exercises zero operations.
- **FR-014**: Each skip log line MUST use ASCII characters and MUST NOT print the token value.
- **FR-015**: The test module MUST unpack three loop tally values at its six existing call sites.
- **FR-016**: `documentation/cli-reference.md` MUST describe the operator-only skip for `--testinteractive`.
- **FR-017**: The change MUST add one changelog fragment at `changelog.d/issue-4744-unattended-token-skip.md`.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable. The change adds no Mist call. The unattended path must not call `mistapi.api.v1.self.update.verifySelfEmail`. The interactive path keeps its existing call.

Warning: a verification call with a valid token applies the email change to the operator account. The unattended run must never make that call.

### Key Entities *(include if feature involves data)*

- **Operator-only prompt context**: A prompt context that the unattended run never answers. Natural key: the context string. Current member: `verify_self_email.token`.
- **Skip event**: A telemetry record for one skipped option. Natural key: run start time and option number.
- **Suite tally**: Counts for passes, failures, skips, and prompt harness failures in one run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The mocked regression records one skip event, zero pass events, zero fail events, and zero prompt harness failures for option 247.
- **SC-002**: In the same regression, the SDK function mock and the writer mock record zero calls.
- **SC-003**: After the regression, the input seam is the same function object that it was before the option ran.
- **SC-004**: The provider test for an optional prompt returns an empty string.
- **SC-005**: Every test in the runner test module, the exporter test module, and the two action test modules passes.
- **SC-006**: Each gate in task T-LOCAL-GATES reports its expected result.

## Assumptions

- The runner installs the input provider only inside `_invoke_with_input_provider`. Runner lines 476 to 489 show this on main.
- Option 247 stays in the `interactive_safe` category. Registry lines 584 to 590 show this on main.
- The pinned SDK version 0.64.1 defines `verifySelfEmail`. The local install shows this at line 42.
- In tests, the resolver reads a test host from `sys.modules` under the name `MistHelper`. Resolver lines 283 to 285 show this on main.
- Each option in the runner loop waits one second. Runner lines 629 and 630 show this on main. The new loop tests accept the delay.
- The code search on main lists no production module other than the runner that imports the input provider.

## Out of Scope

- Changing the category or the skip reason of menu 247 in the registry.
- Enabling unattended email verification or sending a token in an unattended run.
- Changing the interactive behavior of the exporter.
- Changing the default of `allow_empty` in the input seam. Issue #2753 tracks that audit.
- Splitting the grandfathered runner, its test module, or `_run_single_option`. Remediation is a separate action in `plan.md`.
- Changing the telemetry summary status rule. `analysis.md` item A-3 records that defect.
- Editing generated pages under `documentation/menu_reference.md` and `documentation/menu-api/`.
- Building, pushing, or deploying the container. That step runs after merge under orchestrator control.
