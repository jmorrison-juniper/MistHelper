# Implementation Plan: WIP target controls

**Branch**: `jmorrison-juniper-wip-target-controls` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3158-wip-target-controls/spec.md`

## Summary

Complete menu 63's target metadata and show a category-derived caution.
Keep the existing handlers, input bridge, safety registry, selector reasons, and output behavior.
Use the shipped page and script with controlled native SDK transport and real local CSV writes.
Keep the repair local and unpublished.

## Technical Context

**Language/Version**: Python 3.13.13, JavaScript, and Jinja templates.

**Primary Dependencies**: Existing Flask, mistapi 0.64.0, Bootstrap, pytest, and pytest-playwright.

**Storage**: Temporary local CSV files. A counted fake router replaces every external store.

**Testing**: New unit, native route/handler contract, and shipped-browser tests.

**Target Platform**: Current macOS host and Chromium. Native Windows and production containers remain outside this proof.

**Project Type**: Existing web portal.

**Performance Goals**: Add no endpoint request for the caution. Keep one selector request for each target change.

**Constraints**: No publication, live Mist API, source exporter change, dependency change, shared test edit, or production resource.

**Scale/Scope**: Three product files, three current WIP rows, one normal control row, and new owned tests.

## Constitution Check

The change preserves the safety registry and makes no destructive operation runnable.
The new support package has at most five files. New test methods stay short.
Existing large registry and JavaScript functions are inherited structural debt.
This repair changes only the necessary existing blocks.
Their later structural repair needs a separate owner and issue.
No standalone handler wrapper, compatibility alias, or source facade is introduced.
The parent publication restriction overrides the historical automatic deployment text.
The Conventional Commits rule overrides the historical timestamp commit text.
The directly related release note belongs in this feature's unique fragment.
README and shared CHANGELOG remain read-only.

## Project Structure

### Documentation (this feature)

```text
specs/3158-wip-target-controls/
  spec.md
  plan.md
  tasks.md
  .spec-context.json
  checklists/requirements.md
```

### Source Code (repository root)

```text
web_portal/services/operation.py
web_portal/static/js/operations.js
web_portal/templates/operations.html
tests/support/wip_target_controls/
  __init__.py
  native.py
  portal.py
  browser.py
tests/unit/web_portal/wip_target_controls/test_metadata.py
tests/contract/web_portal/wip_target_controls/test_handler_outputs.py
tests/e2e/wip_target_controls/
  conftest.py
  test_controls.py
  test_failure_recovery.py
changelog.d/issue-3158-wip-target-controls.md
```

**Structure Decision**: Keep all new support and tests in the reserved feature packages.
Use the current general portal files only for necessary metadata and presentation.

## Research and Decisions

The live issue has two release comments and no previous active owner.
The claim is [comment 5963435542](https://github.com/jmorrison-juniper/MistHelper/issues/3158#issuecomment-5963435542).
The complete paginated query returned zero open pull requests.
The old remote branch was checked by name and full SHA, without reading its draft patch or archive.

The pre-edit browser proof ran the shipped routes, template, Bootstrap, and script.
It counted three actual handler runs, three Site controls, zero switch controls, and zero cautions.
Menu 63 submitted one answer and made zero virtual chassis requests.
Its site inventory cache was not a virtual chassis result.
Menus 64 and 65 reached their real client endpoints and local writers.

Menu 64 currently writes `SiteWiFiClients.CSV.csv`.
Its title and notice name `SiteWiFiClients.CSV`.
The unchanged local CSV writer compares its suffix against lowercase `.csv`.
The parent retained the three portal source paths and requested a separate issue for the filename concern.
The separate bug is [#3738](https://github.com/jmorrison-juniper/MistHelper/issues/3738).
The product scope does not include that writer or exporter.
Do not claim the filename mismatch is repaired by target metadata.
Use `Part of #3158`, not a closure reference, while the filename acceptance remains unresolved.
Tracked control tests prove the requested logical target, actual local writer counts, rows, metadata, and cache exclusion.
They do not require the doubled filename.
The earlier wrong filename remains a diagnostic fact in private pre-edit evidence and in the companion issue.
The control tests accept the later single-suffix repair without a handler, label, or fixture change.

The caution will use a boolean property only on rows whose actual displayed category is Work In Progress.
Normal rows retain their complete previous payload shape.
The accepted category-list INFO record and DEBUG count summary remain exact.
The browser uses a fixed Bootstrap alert with safe text.
The caution grants no execution permission.

Menu 63 receives the existing Site descriptor and required Device descriptor with the switch filter.
The existing input bridge continues to send the site name and switch name.
The real prompt resolves those names to the original site and device identifiers.
Menus 64 and 65 retain their current single Site descriptor.

## SpecKit Execution Limits

The current custom-agent instructions and spec, plan, and task templates were read.
The installed hooks require a branch hook before specification.
The app already owns this worktree branch.
The raw Bash hook calls `git checkout` and is refused under the app branch policy.
No raw branch hook executes.

The PowerShell branch hook, plan setup, and task setup commands each failed because `pwsh` is absent.
The failures occurred before any shared SpecKit state changed.
The file-only equivalent uses this explicit feature directory and the current template headings.
Research, data contracts, and validation steps stay in this plan to keep the feature directory bounded.
The feature-local context records the completed steps.
Shared `.specify`, agent context, optional auto-commit hooks, and companion hooks remain unchanged.
No missing hook is reported as executed.

## Data Model and Interface Contracts

| Boundary | Preserved contract |
| - | - |
| Operation list | Existing row fields remain unchanged. Only WIP rows gain `work_in_progress: true`. |
| Menu 63 parameters | Required Site, then required Switch with `device_filter="switch"` and `depends_on="site_id"`. |
| Menus 64 and 65 | One required Site descriptor each. |
| Run request | The existing `parameters.input_answers` list carries prompt answers in descriptor order. |
| Site selector | Option values remain site names. The existing data attribute retains the site identifier. |
| Switch selector | Option values remain switch names. The existing data attributes retain device ID and MAC. |
| Caution | A fixed, accessible Bootstrap warning appears before Run and hides for a normal row. |
| Selector failures | Existing HTTP, transport, payload, empty, and missing-session reasons remain unchanged. |
| Empty VC result | The existing visible no-record warning remains valid. No virtual chassis file is fabricated. |
| Output writer | Actual local CSV output and exporter endpoint metadata are measured. External routing stays controlled. |

A selection starts with Run disabled while required metadata loads.
A new site clears the old switch selection.
A selector completion applies only while its site and control remain current.
The existing validation and server safety gates remain in place.

## Validation and Local Preparation

Write acceptance tests before product edits.
Require the missing switch descriptor and missing caution proof to fail against the original source.
After the repair, select the real controlled switch through the shipped UI and run the actual handler.
Count all SDK requests, prompt answers, handler runs, output rows, router calls, and blocked live requests.
Add direct negative tests that remove the descriptor and caution metadata.
Include current general portal, destructive refusal, empty-reason, output, and logging tests in the same collection.

Run compile, Node syntax, Ruff, Black, the current configured mypy scope, Bandit, and applicable complexity checks.
Run the required six-input, three-guide preflight before either test-quality gate.
Run the complete unchanged-baseline quality gate and the clean committed-scope quality gate.
Do not change a rule, baseline, exclusion, or suppression.
Keep browser tracing, screenshots, and video off under the plugin defaults.
Required browser tests must run without skips.
Keep optional and platform skips explicit.

The copied-interpreter setup reproduced ensurepip SIGABRT and interpreter exit 134.
The recovery changed only ignored `.venv`, using uv seed, copy installation, and system certificates.
No bootstrap or peer environment was used.
The normal dependency audit must not report an abort as clean.
If that audit aborts, record the complete hashed runtime alternative and its development-tool limitation.
If the licensed STE dictionary is absent, report the STE result as partial.

Remove owned temporary data and helper resources after every proof.
Verify server threads, event subscriptions, browser resources, and exact temporary paths are absent.
Retain only private evidence under the session artifact directory.
Prepare the unchanged 23-item pull request template offline with exact results and honest limits.
Create one local Conventional Commits commit with the required Copilot App trailer.
Add `Closes #3158` only if all current issue acceptance is fulfilled.
Send the clean full SHA and evidence to the parent. Do not publish.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| Existing registry and JavaScript function sizes | The current metadata and input bridge own the behavior. | A broad source refactor would cross reserved paths and change unrelated behavior. |
