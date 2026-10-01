# Specification Quality Checklist: Packet Length Validation

**Purpose**: Validate specification completeness and quality before planning.

**Created**: 2026-09-30

**Feature**: [spec.md](../../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

Specification review is complete.
All 16 quality items pass.
These items measure document quality, not implementation results.
Incomplete items require specification updates before `/speckit.clarify` or `/speckit.plan`.

### Validation Results

The review found one initial readiness gap.
Initial `FR-012` text: "The correction MUST preserve fixed packet lengths of 1300 and 1500 bytes."
The first draft described this result only under edge cases.
The review added User Story 3, scenario 7, and `SC-009` to state this acceptance result directly.
The final review found no remaining quality failure.

| Requirements | Acceptance evidence in the specification | Measurable outcomes |
| --- | --- | --- |
| `FR-001` through `FR-004` | Stories 1 and 2 define accepted integers, rejected integers, non-integer errors, and displayed limits. | `SC-001`, `SC-002`, `SC-003`, `SC-005` |
| `FR-005` through `FR-009` | Story 3, scenarios 1 through 6, define defaults, whitespace, EOF, caller defaults, and interruption. | `SC-004`, `SC-005` |
| `FR-010` and `FR-011` | Story 2 defines complete settings and early rejection. Story 1 defines rejection without clamping or default substitution. | `SC-002`, `SC-006` |
| `FR-012` | Story 3, scenario 7, defines unchanged fixed lengths and unrelated settings. | `SC-009` |

`SC-007` defines clear operator guidance and completion with one valid entry.
`SC-008` requires offline evidence with no real capture requests or Mist cloud contact.
The specification has 12 functional requirements, nine measurable outcomes, and no clarification marker.
Its main sections retain the resolved repository template order.
The specification describes required behavior, not a proposed technical design.
The external release contract provides a limit, not an implementation strategy.

No substantive requirement remains unresolved.
The existing specification, plan, and tasks define the bounded correction.
The parent supplied verified final red and green tests, coverage, and configured local gate results.
T001 through T029 are complete from that supplied evidence.
Cross-artifact analysis is complete.
T030 is complete in local implementation commit `e74a996777d9fffb163c1be904f497132cbb7081`.
T031 through T038 remain blocked.
The normal requirements audit failed before scanning, and its documented local alternative left the Git pin unaudited.

### Issue Ownership and Source Evidence

- Issue: [MistHelper #3337](https://github.com/jmorrison-juniper/MistHelper/issues/3337).
- The user confirmed that the issue is open and assigned to `jmorrison-juniper`.
  Its labels are `bug`, `tests`, `in-progress`, and `src/api`.
- App session: `25e19be4-7155-4623-ad9c-50ca52cc6585`.
- CLI session: `8709155b-5b4b-4372-b7f6-603845459534`.
- Existing branch: `jmorrison-juniper-packet-length-validation`.
- Source base: `9148155c95e1f502abb0a09fd69f5a928b3bf22f`.
  The local source review used this revision.
- The user confirmed that no open pull request conflicts with the two prompt files.
  Supplied live checks also show no overlap with the final test file.
  The parent notified the coordinator and refined the ownership comment.
- The issue supplies the release `2609.1.0` maximum for site `capture_max_pkt_length` and organization `capture_mxedge`.
  No Mist cloud verification is necessary for this specification.
- Issue #3338 owns the independent bundled-specification refresh.
  It is not a prerequisite for this correction.

### Approved Final Implementation Manifest

The implementation owns these files only:

1. `src/capture/_packet_capture_prompts.py`.
   The affected method is `PacketCapturePrompts.prompt_max_packet_length`.
2. `src/refactors/serial_cc/start_site_client_capture_wireless.py`.
   The affected value is `_MAX_PKT_LEN_SPEC`.
   Existing methods `_prompt_bounded_int` and `_collect_bounded_ints` perform its validation.
3. `tests/unit/capture/test_multi_ap_scan_workflow.py`.
   Append `test_packet_length_prompt_limits` and `test_packet_length_prompt_defaults`.
   Parameterize each function for `shared` and `wireless`.
   Preserve existing tests apart from necessary imports and the module docstring.
4. Issue-owned documents under `specs/3337-packet-length-validation/`.
5. `changelog.d/issue-3337-packet-length-validation.md`.
   The parent owns this fragment, not the documentation owner.

The capture test directory already has eight children.
A new direct test file would violate Constitution Principle I.
The selected existing test file has three definitions and zero quality findings before the additions.
Two appended functions keep five definitions and add no directory child.
Keep each function within five parameters and 25 lines.
Do not add a class, fixture, helper, wrapper, module, or production construct.

Restore `tests/unit/test_packet_capture.py` exactly to base `9148155c95e1f502abb0a09fd69f5a928b3bf22f`.
`tests/unit/serial_cc/test_start_site_client_capture_wireless.py` remains a read-only regression target.
No other test file belongs to the edit manifest.
Do not create `tests/unit/capture/test_packet_capture_prompt_limits.py`.

The rejected large-file manifest passed 4010 focused and 4369 adjacent cases.
All three measured regions reached 100%.
The ratchet reported 23 new line-sensitive `weak_zero_assertions` findings after existing assertions moved.
The large file still had exactly 24 findings, with zero semantic new findings.
The user prohibits baseline changes, suppressions, and unrelated test repairs.
The final manifest preserves that file exactly and requires new validation.

The affected source directories already have structural debt.
`src/capture/` has 13 children, and `src/refactors/serial_cc/` has nine children.
The existing plan records grandfathered violations and separate incremental remediation actions.
This issue does not authorize unrelated restructuring.

Limit production edits to exactly six `2048` to `1536` literal changes.
Reuse the existing helpers.
Do not add production classes, wrappers, compatibility shims, environment variables, schemas, or menu entries.
Do not add unrelated capture changes.
Preserve existing input safety, comments, and logging.

Do not modify these files or areas:

- Bundled OpenAPI artifacts or SDK dependencies.
- `README.md`, requirements files, or bootstrap files.
- `CHANGELOG.md`, title guards, or unrelated history.
- Shared `.specify/feature.json` or extension configuration.
- Named sender files reviewed below.

### Sender Review Without Edits

| Reviewed sender | Local source evidence | Scope decision |
| --- | --- | --- |
| `src/capture/multi_ap_scan_workflow.py` | `_DEFAULT_MAX_PKT_LEN` supplies fixed 1300. | Preserve the sender. |
| `src/refactors/serial_cc/start_site_scan_capture.py` | `_MAX_PKT_LEN` supplies fixed 1300. | Preserve the sender. |
| `src/capture/packet_capture.py` | Fixed lengths are 1300 or 1500. Interactive paths delegate to the shared prompt. | Preserve the sender. |
| `src/capture/org_capture_workflow.py` | `_collect_capture_config` calls `manager._gather_org_capture_params`. | Preserve the sender. |
| `src/capture/_packet_capture_org.py` | `gather_org_capture_params` reaches the shared prompt through `_prompt_max_packet_length`. | Preserve the sender. |

All reviewed fixed lengths satisfy the 1536-byte maximum.
The organization path uses the shared prompt, not a third independent length validator.

### Offline Verification Requirements

The two final functions must execute these existing production validation paths:

- `PacketCapturePrompts.prompt_max_packet_length`.
- `SiteWirelessClientCaptureService._prompt_bounded_int` with the real `_MAX_PKT_LEN_SPEC`.
- `SiteWirelessClientCaptureService._collect_bounded_ints` with the real prompt specifications.

Drive controlled terminal input through the real `InputUtils.safe_input` from `src/utils/input_utils.py`.
Do not replace `safe_input` with a stub.
Do not mock validator returns or replace the collection sequence.
Substitute only `builtins.input`.
The shared prompt resolves the real `InputUtils`.
Pass the real `InputUtils` to the wireless collector without starting a capture workflow.
The limits-case parameter groups raw input, expected length, and exact diagnostic.

The tests must prove these results:

- Every integer from 64 through 1536 returns unchanged from both prompts.
- Input 63 and every integer from 1537 through 2048 return `None`.
- Inputs 0, -1, 2049, and 9999 also return `None`.
- Non-integer examples `64.0`, `1e3`, and `text` return `None` with an invalid-length diagnostic.
- Both actual prompt messages show maximum 1536 and the applicable default.
- Actual range errors show 64 and 1536, not the former 2048 maximum.
- Empty and whitespace-only input return shared default 128 or wireless default 1300.
- Padded 64 and 1536 preserve the selected value.
- EOF preserves the applicable default and the existing notice for context `max_pkt_len`.
- The shared caller-supplied default 1300 remains unchanged.
- An operator interrupt preserves the existing cancellation notice and returns `None`.
- The wireless collection sequence returns the actual duration, packet count, and packet length for valid input.
- With invalid packet length, the wireless collection sequence returns `None`.
- Blank or EOF input preserves the wireless collection defaults `(60, 1024, 1300)`.

Assert observed return values, inclusive ranges, and actual prompt and error messages.
Do not substitute source-text searches or literal inspections for behavior tests.
Do not start a real capture, contact Mist cloud, or require Mist credentials.

Record a focused red run against the unchanged source.
The red run must fail on the old maximum or its messages, not an import or environment error.
After the bounded correction, record the same focused tests as green.
Report test counts and coverage for the affected validation behavior.
The supplied final matrix executed 4010 items, with 2005 per path.
Each path executed 1473 supported integers, 513 required rejected integers, and 19 additional cases.
Use both final function nodes in `tests/unit/capture/test_multi_ap_scan_workflow.py`, or select that file with `-k packet_length_prompt`.
Each parameterized item executes one real path.
The final red run recorded 4010 failures with zero errors or skips against base-identical source.
Shared input 1537 returned `1537`, and wireless input 1537 returned `(120, 7, 1537)`.
The final green run passed 4010 cases with zero failures, errors, or skips.
The final adjacent run passed 4373 cases with zero failures or skips.
Final region coverage measured shared 11/11, wireless bounded 12/12, and collector 8/8 statements, each at 100%.
The final test file contains five functions.
The new functions use 23 and 21 lines, with four and three parameters.
Documentation alignment performs no production edit, test edit, or test execution.

### Future Quality and Delivery Requirements

The future implementation must use Python `3.13.13`.
Its local gates include:

- Focused pytest red and green runs with coverage's existing run and JSON APIs.
- Syntax validation of both prompt files, the final test file, and `MistHelper.py`.
- Repository-scope Ruff and Black.
- mypy with the exact `MYPY_PATHS` from CI.
- Bandit and pip-audit.
- `test-quality-analyzer` with `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`.

Use the existing repository configuration for these gates.
Do not edit a baseline, add a suppression, or weaken a gate.
Measure all three actual AST regions separately.
Each region must contain measured statements and reach at least 80% coverage.
Do not apply pytest-cov's whole-module 90% threshold to a focused function run.
Do not set `--cov-fail-under=0`, change configuration, or create a coverage helper file.
The repository's global coverage threshold remains unchanged and required in CI.
Record the normal pip-audit ensurepip SIGABRT and copy error before the documented local alternative.
Use `rtk proxy .venv/bin/python -m pip_audit --local --skip-editable` for the local macOS alternative.
The Git-pinned `misthelper-devtools` version `0.5.2` remains explicitly unaudited because PyPI does not contain it.
The normal requirements audit remains required for delivery.
Future delivery must also pass all applicable repository checks, including CodeQL.
No implementation gate runs during documentation alignment.
The final compile check passed four files.
The full Black check passed 1882 files without changes.
Repository-scope Ruff and configured mypy passed, with mypy checking 608 source files.
Configured Bandit found zero findings across 206617 lines in `data/issue-3337/bandit.json`.
The configured ratchet checked 944 files and 728 existing findings.
It reported zero new findings, 42 configured skips, and zero parse errors.
The normal requirements audit failed during macOS ensurepip with SIGABRT before scanning.
The final local alternative found no known vulnerabilities in audited installed packages.
It did not audit the Git-pinned package.

This issue occupies parent queue position 9.
Coordinator `6d71fd26-57c2-48c0-abc8-607af98f75d0` must provide a verified stable `main` SHA before any push or pull request.
The recorded source base is not that release permission.

Future delivery must preserve every section and checklist in `.github/PULL_REQUEST_TEMPLATE.md`.
The pull request body must include `Closes #3337`.
Use a Conventional Commit with the exact Copilot trailer from `tasks.md`.
Protected delivery requires all checks, including title and CodeQL, with a strictly up-to-date branch.
Use a protected squash merge and offline local testing of the exact resulting `main` revision.
These requirements do not authorize a commit, push, pull request, workflow run, or merge in this phase.

### Current Session Boundaries

This phase updates existing issue-owned documents only.
The parent independently owns source, tests, release notes, final gate counts, and delivery.
Do not create a document or summary.
Do not read source or tests, execute gates, or contact Mist cloud.
It does not create, switch, or rename a branch.
It does not commit, push, create a pull request, or run a delivery workflow.
The app workspace excludes branch-creation and commit hooks.
Skip unavailable PowerShell and companion commands and optional Git commit hooks.
Update only this feature's `.spec-context.json` directly.
Keep implementation in progress and record supplied verified local validation with the documented audit alternative.
Record the verified local implementation commit and keep delivery blocked.
Shared feature selection and extension configuration remain unchanged.
Future specification commands must use the explicit directory `specs/3337-packet-length-validation/`.
