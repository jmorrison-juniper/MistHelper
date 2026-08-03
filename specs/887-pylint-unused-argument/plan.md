# Implementation Plan: Narrow the pylint W0613 unused-argument suppression

**Branch**: `887-pylint-unused-argument` (not created. This plan creates no branch and no commit.)

**Date**: 2026-07-29

**Spec**: [spec.md](spec.md)

**Source Issue**: #887, part 1 of 3

**Input**: Feature specification from `specs/887-pylint-unused-argument/spec.md`

---

## Summary

The file `pyproject.toml` disables the pylint check `W0613` for the whole
repository. The committed reason covers WebSocket protocol callbacks only. Every
other unused argument stays hidden.

This feature triages all 21 findings, fixes the source tree, and then removes
`W0613` from the `disable` list.

The triage is complete. It is not deferred to implementation. Section 5 of
[research.md](research.md) holds one final outcome for each of the 21 findings.

| Outcome | Count | Meaning |
| - | - | - |
| A | 15 | Remove the parameter and every call site. |
| B | 5 | Keep the parameter with a site-local disable and a specific reason. |
| C | 1 | A real defect. Record it, file an issue, keep the parameter. |

The technical approach has three parts.

1. **Resolve each parameter thread as one unit.** The research found four
   threads where a caller passes a parameter down without reading it. A partial
   removal moves the finding up one level instead of clearing it. Five cascade
   functions that the baseline does not report must change with their leaves.
2. **Reject the "preserved for tests" reason.** Six parameters already carry a
   ruff `ARG` suppression. Each reason names a test or a future plan. FR-013
   needs a real contract, so these six take Outcome A. The feature updates the
   tests and deletes the dead comments.
3. **Change the gate last.** The edit to `pyproject.toml` is the final source
   change. An earlier edit turns the gate red for every open branch.

---

## Technical Context

**Language/Version**: Python 3.13 or newer. The constitution binds this minimum.
The measured environment used Python 3.13.3.

**Primary Dependencies**: None added. The feature uses pylint 4.0.6 and astroid
4.0.4 as the measuring tool. It touches no runtime dependency.

**Storage**: N/A. The feature stores no runtime data. It changes source files
and one configuration file.

**Testing**: pytest. The feature updates 24 existing test call sites. It adds no
test and removes no test.

**Target Platform**: The source runs on Windows for local development and on
Linux inside the container. The gate runs on `ubuntu-latest`.

**Project Type**: A single Python project. The package tree sits under `src/`.

**Performance Goals**: N/A. No runtime path changes behavior.

**Constraints**:

- FR-025 forbids a runtime behavior change at any Outcome A site and at any
  Outcome B site.
- FR-019 makes the `pyproject.toml` edit the final source change.
- FR-023 rejects a local Windows score as proof. Only a run on the Linux runner
  proves the gate.
- FR-024 forbids a lower threshold and forbids a restored repository-wide
  disable.

**Scale/Scope**: 21 findings across 13 files. 19 functions lose a parameter. 17
production call sites and 24 test call sites change. 6 sites gain a comment. 6
dead `noqa` comments go away. One line of `pyproject.toml` changes.

**Tooling note**: Use `.venv\Scripts\python.exe` for every Python command. The
global interpreter on the development machine is broken, and the virtual
environment holds no `pip`.

---

## Constitution Check

*Gate: this section passed before Phase 0. It passed again after Phase 1.*

| Principle | Status | Evidence |
| - | - | - |
| I. Five-Item Rule | Improves | The feature only removes parameters. Two functions drop from six parameters to five. `BulkAPFirmwareUpgrader._upgrade_version_group` and `AddressResolver._combine` both move into the limit. |
| II. Class-Based Architecture, No Wrappers | Pass | FR-032 forbids a wrapper. FR-033 forbids a shim. The feature updates real call sites instead. |
| III. Safety-First | Pass | `AppRunner._prompt_for_commands` keeps its `InputUtils.safe_input` call. No destructive operation changes. No input validation changes. |
| IV. Full Deployment Pipeline | Pass | The pipeline runs after merge, as it does for every change. |
| V. Observability and Logging | Pass | No log call is removed. The `source` thread keeps its two `logging.debug` calls, because `_geocode_address` keeps the parameter. |
| VI. Inline Comments | Pass | FR-030 requires a why-comment on every changed line. The tasks phase must budget for this work. |
| VII. Action Logging | Pass with a note | See Complexity Tracking, row 1. |
| Fix Over Suppress | Pass | The feature deletes six dead `noqa` comments and adds only six narrow, reasoned disables. FR-012 forbids a wide disable. |
| Simplified Technical English | Pass | FR-031 covers the plan, the research, the comments, the issues, and the pull request text. Step 12 of the quickstart holds the check command. |

No principle is violated. One principle needs a written note.

---

## Project Structure

### Documentation (this feature)

```text
specs/887-pylint-unused-argument/
├── spec.md                          # Input
├── plan.md                          # This file
├── research.md                      # Phase 0 output. Holds the triage record.
├── data-model.md                    # Phase 1 output
├── quickstart.md                    # Phase 1 output. Holds the validation steps.
├── contracts/
│   ├── signature-changes.md         # Phase 1 output. Every before and after signature.
│   └── pylint-gate.md               # Phase 1 output. The gate contract and the rollback.
├── checklists/
│   └── requirements.md              # Existing
└── tasks.md                         # Phase 2 output. Not created by this command.
```

### Source Code (repository root)

The feature touches these paths only.

```text
pyproject.toml                       # The disable list. Changed last.

src/
├── capture/packet_capture.py
├── firmware/bulk_ap_upgrader.py
├── firmware/org_ap_upgrader.py
├── inventory/inventory_summary/version_per_model_fetcher.py
├── maps/_maps_clone.py
├── maps/maps_manager.py
├── org/org_synthetic_probes_manager.py
├── site/address_audit/address_resolver.py
├── ssh/runtime/app_runner.py
├── ssid_consolidation/_ssid_template_cache.py
├── ssid_consolidation/_ssid_template_phase1.py
├── ssid_consolidation/_ssid_template_phase2.py     # Call site only
├── ssid_consolidation/_ssid_template_phase3.py     # Call site only
├── ssid_consolidation/_ssid_template_phase45.py
├── utils/address_utils.py
└── websocket/manager.py

tests/unit/
├── inventory/test_version_per_model_fetcher_wave3.py
├── test_address_utils.py
├── test_bulk_ap_upgrader.py
└── test_ssid_template_consolidation.py
```

**Structure Decision**: The feature keeps the existing single-project layout. It
adds no module, no package, and no directory. Sixteen source files change and
four test files change.

---

## Work Sequence

FR-019 fixes the last step. The order below also groups the work so that each
step ends with a clean finding count.

| Step | Work | Ends with |
| - | - | - |
| 1 | Re-measure the baseline. Confirm 21 findings. | A confirmed start point. |
| 2 | Apply the five simple Outcome A removals with no cascade: groups 1, 3, 5, 6, and 8 of the signature contract. | 6 findings cleared. |
| 3 | Apply the single-level Outcome A removals: groups 7 and 9. | 2 more findings cleared. |
| 4 | Apply the cascade threads one at a time: groups 2, 4, 10, and 12. Finish each thread before you start the next. | 7 more findings cleared. |
| 5 | Apply group 11, the `debug` parameter. | 1 more finding cleared. Total 16 cleared. |
| 6 | Add the five Outcome B comments. | 5 findings suppressed with a reason. |
| 7 | File the three companion issues. Add the Outcome C comment with the issue number. | 1 finding suppressed with an issue link. Zero findings remain. |
| 8 | Run every quality gate. Run the manual scan of `src/maps` and `src/ssh`. | A clean tree. |
| 9 | Remove `"W0613"` from `pyproject.toml`. Update the comment block. | The gate is enforced. |
| 10 | Push the branch. Read the Linux runner result. | Proof of the score. |

Warning: Do not reorder step 9. If the entry leaves the `disable` list before
step 8 reports zero findings, the gate turns red for every open branch in the
repository.

Caution: Steps 2 through 5 each change a finding count. Run the count command
after every step. The count must fall. A rise means an unfinished cascade.

---

## Risk Register

### Risk 1. The Linux score falls below 9.5

**This is the risk that broke issue #891.** A Windows checkout reported 9.71 for
a commit. The `ubuntu-latest` runner reported 9.41 for the same commit and
failed the threshold.

**Measured evidence for this feature**: The team measured the local Windows
score with the gate flags in place. The score is 9.77 today. The score is 9.77
with `W0613` enabled. The delta is smaller than the reported resolution of 0.01.
Seventeen extra warnings do not move the score, because the `src/` tree holds a
large statement count.

**Why the #891 gap is not expected here**: The #891 measurement removed the
`--ignore=maps,ssh,ui` flag and added three unaudited packages to the run. This
feature keeps that flag. Both runs cover the same package set that passes today.

**Mitigation**:

- Require a real run on the pushed branch. FR-023 and step 10 hold this rule.
- Read the job named "Pylint (score gate)". Record the score in the pull request
  body.
- Do not add the `auto-merge` label until that job and CodeQL both pass.

**Rollback position**: Section 7 of [contracts/pylint-gate.md](contracts/pylint-gate.md)
holds the full procedure. The short form is:

1. Confirm that zero `W0613` messages remain. If any remain, fix that site.
2. Do not lower `fail-under`. Do not restore the repository-wide disable.
3. If the score still cannot reach 9.5, revert the `pyproject.toml` commit only.
   Keep every source fix and keep the triage record. The gate change then waits
   for a follow-up branch, and the source work holds its value.

### Risk 2. A cascade adds a finding that the baseline does not hold

Five functions read a parameter only to pass it down. They are not in the
baseline. They become findings after their leaf changes.

**Mitigation**: The signature contract marks each one as a cascade level and
names the stop condition. Step 4 of the work sequence treats each thread as one
unit. The count command after each step catches a partial removal.

### Risk 3. A positional removal binds an argument to the wrong parameter

Four removals are not at the end of a signature.

| Function | Position of the removed parameter |
| - | - |
| `VersionPerModelFetcher._rows_for_model` | First of four |
| `VersionPerModelFetcher._expand_model_rows` | First of four |
| `MapsManager._render_site_maps_table` | First of two |
| `AddressResolver._combine` | Fourth of five |

**Mitigation**: The research checked every call site. No caller passes any
Outcome A parameter by keyword, so no caller raises a `TypeError`. The signature
contract names every call site for these four functions. Change the signature
and every call site in one edit.

### Risk 4. Four findings sit in packages that the gate hides

`src/maps` and `src/ssh` hold four findings. The `--ignore` flag hides them, so
the gate cannot prove them.

**Mitigation**: Step 4 of the quickstart runs a manual scan of those two
packages. FR-004 requires the triage anyway, and the research assigned an
outcome to all four.

### Risk 5. The baseline drifts before the work starts

**Mitigation**: Step 1 re-measures. The team re-measured on 2026-07-29 and found
no drift. If a later measurement differs, add each new finding to the triage
record and assign an outcome before you continue.

### Risk 6. A test asserts a signature that the feature changes

**Mitigation**: The research searched every changed function name. The signature
contract lists 24 test call sites. Two usages in
`tests/unit/test_ssid_template_consolidation.py` use `patch.object` by name.
A patch by name survives a signature change, so those two lines stay unchanged.
Step 6 of the quickstart runs the full suite to catch any call that the search
missed.

---

## Complexity Tracking

| Item | Why it is needed | Simpler alternative rejected because |
| - | - | - |
| Principle VII asks the team to add action logging to a touched block that lacks it. This feature adds none. | Every edit in this feature is a signature edit or a comment edit. It adds no action, removes no action, and changes no data flow. Principle VII binds a "meaningful action". No new action appears. FR-025 also forbids a behavior change, and new output at a touched line risks a test that asserts captured output. | Adding a log line to each touched block would widen the change beyond the audit, raise the review cost, and put FR-025 at risk for no observability gain. |
| Row 13 keeps an unused parameter behind a disable comment instead of a removal. | FR-015 forbids a removal at an Outcome C site. The parameter is the seam that the future fix needs. Deleting it hides an operator-facing defect. | Removing `resolutions` would clear the finding and hide the fact that Phase 4 discards every operator answer. |
| Group 10 leaves `_build_sitegroup_lookup` and the `_SiteLookups.sitegroup_lookup` field in place, although both lose their last reader. | Removing a dataclass field and a back-compat re-export is dead-code work. The Out of Scope list excludes it, and the module re-exports the function by name. | Removing them inside this feature would change a documented back-compat surface without a specification for that change. |
| The feature deletes six `noqa: ARG00x` comments rather than converting them into pylint disables. | The stated reasons name a test or a future plan. FR-013 needs a real contract. FR-026 requires the test update instead. The `debug` reason is also factually wrong, because no caller passes `debug`. | Converting them would keep 6 dead parameters and would set a precedent that a test freezes a private signature. |

---

## Phase Status

| Phase | Output | Status |
| - | - | - |
| Phase 0, research | [research.md](research.md) | Complete. All 21 findings hold a final outcome. Zero items read "NEEDS CLARIFICATION". |
| Phase 1, design | [data-model.md](data-model.md), [contracts/signature-changes.md](contracts/signature-changes.md), [contracts/pylint-gate.md](contracts/pylint-gate.md), [quickstart.md](quickstart.md) | Complete. |
| Phase 2, tasks | `tasks.md` | Not started. The `/speckit.tasks` command creates it. |
