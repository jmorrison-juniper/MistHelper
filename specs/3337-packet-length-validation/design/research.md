# Research: Packet Length Validation

**Issue**: #3337

**Scope**: Supplied evidence and the completed local source review only.
The research needs no agent, capture request, or Mist cloud contact.

## Decision 1: Use the Supplied Maximum

**Decision**: Both existing prompts use 1536 bytes as their inclusive maximum.

**Rationale**: The user verified public changelog `2609.1.0` through the GitHub API.
That release explicitly sets 1536 for both contracts.
[spec.md](../spec.md) records the required range and unchanged defaults.

**Alternatives considered**: Retain 2048, make the maximum configurable, or wait for issue #3338.
Each alternative conflicts with the bounded correction or adds an unnecessary dependency.
The research needs no new upstream verification.

## Decision 2: Change Six Existing Literals

**Decision**: Change three literals in the shared prompt and three in wireless `_MAX_PKT_LEN_SPEC`.

**Rationale**: Both paths convert text to integers and enforce inclusive bounds.
Their existing helpers provide the required rejection behavior.
The minimum, defaults, input context, errors, and EOF handling need no production edit.

**Alternatives considered**: Introduce a shared constant, new validator, wrapper, or specification type.
These changes add production declarations or refactors beyond the approved manifest.

## Decision 3: Use Two Functions in the Existing Capture Test File

**Decision**: Restore `tests/unit/test_packet_capture.py` exactly to base `9148155c95e1f502abb0a09fd69f5a928b3bf22f`.
Append two parameterized offline functions to existing `tests/unit/capture/test_multi_ap_scan_workflow.py`.
Use `test_packet_length_prompt_limits` and `test_packet_length_prompt_defaults`.
Parameterize each function for `shared` and `wireless`.

**Rationale**: `tests/unit/capture/` already has eight files.
A new test file would increase structural debt.
The final file has three definitions and zero quality findings before these additions.
Adding two functions keeps five definitions and adds no directory child.
Preserve its existing tests apart from necessary imports and the module docstring.
Keep each new function within five parameters and 25 lines.

The rejected large-file edit passed 4010 focused cases and 4369 adjacent cases.
All three measured regions reached 100% coverage.
However, the configured ratchet identified 23 new findings after existing weak assertions changed line numbers.
The file still had exactly 24 findings, with zero semantic new findings.
The baseline identifies findings by line.
The user prohibits baseline changes, suppressions, and unrelated repairs.
The final manifest avoids those line changes.
Those earlier results did not verify the final manifest.
The parent supplied final red, green, coverage, adjacent, and configured gate results.
The final matrix passed 4010 green cases and 4373 adjacent cases.
Its base-identical red run executed 4010 failures with zero errors or skips.
The final ratchet checked 944 files and 728 existing findings.
It reported zero new findings, 42 configured skips, and zero parse errors.
The final test file contains five functions.
The new functions use 23 and 21 lines, with four and three parameters.
The normal requirements audit failed during macOS ensurepip with SIGABRT before scanning.
The local audit alternative found no known vulnerabilities in audited installed packages.
The Git-pinned `misthelper-devtools` version `0.5.2` remained explicitly unaudited because PyPI does not contain it.
The normal requirements audit remains a delivery check.

**Alternatives considered**: Retain the large-file class edit, add a new test module, or edit the wireless test module.
None belongs to the final test manifest.
Do not add a class, fixture, helper, wrapper, module-level test-data declaration, or production construct.
Supplied live open-pull-request checks show no overlap.
The parent notified the coordinator and refined the ownership comment.

## Decision 4: Test Real Input Handling

**Decision**: Substitute only `builtins.input`.
Execute the real shared prompt and `SiteWirelessClientCaptureService._collect_bounded_ints(InputUtils)`.

**Rationale**: The real `InputUtils.safe_input` strips whitespace and supplies blank or EOF defaults.
It returns an empty string after `KeyboardInterrupt`.
The existing validators then return `None` for that interruption.
The shared validator prints errors.
The wireless validator logs each warning.

The shared resolver maps `InputUtils` to `src.utils.input_utils`.
No new dependency seam or production wrapper is necessary.
The limits-case parameter groups raw input, expected length, and exact diagnostic.
The defaults function covers both packet-length EOF and complete wireless blank or EOF sequences.
The supplied final matrix executed 4010 items, with 2005 per real path.
Each path executed 1473 supported integers, 513 required rejected integers, and 19 additional cases.

**Alternatives considered**: Stub `safe_input`, mock returned settings, or inspect literals instead of testing behavior.
These methods would not prove the real defaults, messages, or collection behavior.

## Decision 5: Preserve Reviewed Senders

**Decision**: Do not edit the capture senders or bundled OpenAPI artifacts.

**Rationale**: The named sender review is complete.
`multi_ap_scan_workflow._DEFAULT_MAX_PKT_LEN` and `start_site_scan_capture._MAX_PKT_LEN` use fixed 1300.
`packet_capture` uses fixed 1300 or 1500 and delegates interactive entry to the shared prompt.
The organization workflow reaches that shared prompt and stops before payload creation on `None`.

**Alternatives considered**: Change valid fixed lengths or refresh bundled contracts in this issue.
The fixed lengths already satisfy the maximum.
Issue #3338 owns the independent contract refresh.

## Decision 6: Keep Planning Local and Small

**Decision**: Keep supporting artifacts under `design/` and preserve all shared configuration and instructions.

**Rationale**: The requirements checklist resides under `design/checklists/`.
The feature root and design directory each contain five direct children.
This layout preserves the structural limit without another source or test file.
The existing template supplies the plan sections without a new configuration.
PowerShell is unavailable, and its setup helper can write shared feature selection.

**Alternatives considered**: Add every artifact at the issue root, install tools, or change shared feature selection.
These actions increase the structural debt or exceed this phase's permissions.

## Research Result

The research resolves all technical decisions.
No new dependency or integration research remains.
Tooling limits affect the workflow automation, not the six-literal design.
The plan records those limits separately.
Use the existing coverage API for the final focused run.
Measure the three actual AST regions separately without a new helper file.
Require nonzero statements and at least 80% coverage in each region.
The repository's global coverage threshold remains unchanged and required in CI.
The supplied final measurements confirmed shared 11/11, wireless bounded 12/12, and collector 8/8 statements, each at 100%.
T030 remains pending for the parent after cross-artifact analysis.
T031 through T038 remain blocked by coordinator queue position 9.
