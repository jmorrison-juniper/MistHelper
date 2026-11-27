# Implementation Plan: Test-quality baseline identity by content

**Branch**: `fix/3102-test-quality-baseline-identity` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric specification at `specs/numbered/0/0/0/4/4/4/0/2/3102-test-quality-baseline-identity/spec.md`. The route digits are the base-5 form of 3102, which is `44402`, padded to eight levels (R-18).

## Summary

The gate compares each baseline entry by its line number. The change replaces the line number with a content anchor in the identity key. The anchor is the SHA-256 digest of the normalized flagged line, or the sentinel `file-level` for a file-level finding. The comparison counts occurrences instead of collapsing them into a set. The prune command removes unmatched occurrences in analyzed files. The migration regenerates the baseline file from current findings.

The analyzer lives in misthelper-devtools. The change therefore spans two repositories. The release comes first. The MistHelper pin, the baseline migration, the tests, the documentation, and the changelog fragment follow.

## Technical Context

**Language/Version**: Python 3.15 for MistHelper (`copilot-instructions.md` lines 18-49). The misthelper-devtools version follows its own `pyproject.toml`.

**Primary Dependencies**: misthelper-devtools 0.7.0 (new release) and pytest for MistHelper tests. The pin is `requirements-dev.txt` line 197 (R-06).

**Storage**: One JSON array file, `.github/test-quality-baseline.json`, of 733 entries on main (R-01).

**Testing**: pytest in misthelper-devtools (`tests/tools/test_quality_analyzer`) and in MistHelper (`tests/guardrails/local_test_quality_loop/test_scope.py`).

**Target Platform**: Windows 11 for local runs. The `test_quality_gate` job runs on `ubuntu-latest` (R-03).

**Project Type**: A command-line gate inside a CI workflow. No web or mobile surface.

**Performance Goals**: The gate keeps its current runtime. The change reads each flagged source file once. The analyzer already reads each analyzed file.

**Constraints**: Output is ASCII only. The gate fails closed on bad input. The command text of the CI job stays unchanged.

**Scale/Scope**: 733 baseline entries, 202 distinct file paths, and one missing file (R-24). The reported drift affects every pull request that moves a line above a finding.

## Constitution Check

The constitution (`.specify/memory/constitution.md`, version 1.9.0) and `AGENTS.md` apply. Each rule has a result and a reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule, direct children | Pass | No file joins `tests/guardrails/local_test_quality_loop` (five children, R-15). No module joins the misthelper-devtools package root (12 children, R-55). New MistHelper tests go into `test_scope.py`. |
| I. Five-Item Rule, spec record | Pass | The record folder holds five children. `design` holds five children. `contracts` holds two files. `checklists` holds one file. The route folder uses the managed root `specs/numbered/` (R-18). |
| I. Five-Item Rule, function limits | Pass, with a plan rule | Each new helper takes at most five parameters and at most 25 lines. The identity resolver is a class method in `baseline.py`. |
| II. Class-based architecture | Pass | The change adds `ContentAnchorResolver` to `baseline.py`. It adds no wrapper function. |
| III. Safety-first | Pass | The loader fails closed (D-7). Prune keeps entries of parse-error files (D-6). The change edits a repository file only. It touches no Mist cloud object and no device. The typed confirmation rule covers Mist cloud and device changes, so it does not apply here. |
| IV. Full deployment pipeline | Pass, with planned steps | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run the local gates, the pull request, the remote checks, and the squash merge. T-MERGE also waits for `container-build.yml` on the merged revision and checks the revision label (Principle IV steps 10 and 11). |
| V. Observability and logging | Pass | Each new output line is ASCII (`gate-output.md`). No secret is printed. |
| VI. Inline comments | Pass, planned | Each new code line in misthelper-devtools and MistHelper carries an inline comment that gives its purpose. |
| VII. Action logging | Pass, planned | Each new action in misthelper-devtools logs at info before it runs and at debug after it runs. |
| Mist API and mistapi | Not applicable | The change calls no Mist API endpoint. |
| Podman and test containers | Not applicable | The change starts no container. |
| File paths | Pass | The analyzer uses `pathlib.Path` (`baseline.py`, blob `a5b505cd`, R-31). |
| Output backends and operational store | Not applicable | The change exports no data. |
| Database keys | Not applicable | No database table changes. |
| Data directory | Pass | The analyzer writes its report into `test_quality_analyzer_output/` (R-50). The change writes no product output. |
| Documentation and release notes | Pass | `copilot-instructions.md` and `quality-gates.md` change. One changelog fragment is added (T017). |
| README | Not applicable | The change alters no operator menu and no README behavior. |
| Pull request governance | Pass, planned | The branch uses the `fix/` type. The title uses Conventional Commits. The body contains `Closes #3102`. The merge is a squash merge. |

## Architecture

The data flow has five steps.

1. A detector emits a finding with a file path, a line number, a rule, and an explanation. A file-level finding carries the sentinel anchor from the `_finding` helper.
2. The pipeline assigns a content anchor to every other finding. It reads the flagged line from the analyzed source file or from the untested source module. A missing or unreadable file stops the run with exit code 2.
3. `BaselineDiffer` builds an identity key for each finding and for each baseline entry. It counts occurrences of each key in both multisets.
4. The gate prints the `gate_scope` line, the `gate_new` lines, the `gate_removed` count, and the `gate` line. It exits 1 when a new occurrence exists. It exits 2 for an input error.
5. The prune and write commands use the same counts. Prune removes unmatched occurrences in analyzed files without parse errors. Write regenerates the file with anchors.

The resolver is `ContentAnchorResolver` in `baseline.py`. The package root cannot take a new module (R-55), so the resolver stays in an existing file.

## File-by-File Change Map

Upstream repository `jmorrison-juniper/misthelper-devtools`, released as 0.7.0:

| Action | Path | Change |
| - | - | - |
| Modify | `src/misthelper_devtools/test_quality_analyzer/detection/types.py` | Add the optional `content_anchor` field to `Finding` after `related_source` (class at line 53, R-43). |
| Modify | `src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py` | Set `content_anchor` to `file-level` in the `_finding` helper (lines 747-760, R-45). |
| Modify | `src/misthelper_devtools/test_quality_analyzer/baseline.py` | Change `_canonical_key` (R-31, R-32). Replace the dictionary and set diff with multiset counts (R-33, R-34). Change prune (R-35). Serialize and validate `content_anchor` (R-31, same blob). Add `ContentAnchorResolver`. Update the module docstring (R-31, same blob). |
| Modify | `src/misthelper_devtools/test_quality_analyzer/__main__.py` | Call the resolver in `_run_pipeline`, after step 6. Build the analyzed and retained file sets (R-39). Print the `gate_removed` count near the gate scope call (line 377, R-38). Change `_prune_baseline` (R-41). Keep `_emit_gate_scope` (lines 848-851, R-37). |
| Modify | `tests/tools/test_quality_analyzer/test_baseline_differ.py` | Update the round-trip key (R-47). Add the duplicate, line-move, and removal cases. |
| Modify | `tests/tools/test_quality_analyzer/test_gate_decision.py` | Update the helper that takes a line number (line 20, R-48). Add the changed-line, missing-anchor, file-level, and three-configuration cases. |
| Modify | `tests/tools/test_quality_analyzer/test_cli.py` | Add the prune, parse-error retention, removed-count, and unreadable-source cases. |
| Modify | `pyproject.toml` | Change the version on line 3 from 0.6.4 to 0.7.0 (R-49). |

MistHelper repository `jmorrison-juniper/MistHelper`:

| Action | Path | Change |
| - | - | - |
| Modify | `requirements-dev.txt` | Change the pin on line 197 to the 0.7.0 release commit (R-06). |
| Modify | `.github/test-quality-baseline.json` | Regenerate the file with anchors. Drop each entry that no current finding matches (R-01, R-24). |
| Modify | `tests/guardrails/local_test_quality_loop/test_scope.py` | Add the class `TestBaselineIdentity` at the end of the file (R-13 shows the class layout). It holds four cases. |
| Modify | `.github/copilot-instructions.md` | Update the paragraph at lines 148 to 150 (R-09, R-10). Keep every command unchanged. |
| Modify | `documentation/quality-gates.md` | Update lines 21 to 43 for the identity key, prune, and migration (R-07, R-08). |
| Add | `changelog.d/issue-3102-test-quality-baseline-identity.md` | One fragment. Rename it to the pull request pattern after the pull request opens (R-19). |
| Add | `specs/numbered/0/0/0/4/4/4/0/2/3102-test-quality-baseline-identity/` | The spec record, copied from the draft folder in T-PR. |

Unchanged on purpose:

- `.github/workflows/ci.yml` keeps the job and its command (R-03, R-04).
- `.github/test-quality-config.toml` keeps the rule settings (R-02).
- `tests/guardrails/local_test_quality_loop/test_guidance.py` keeps its guard (R-12).
- `tests/guardrails/local_test_quality_loop/fixtures.py` keeps its fixture (R-14).
- `documentation/development-tooling-migration.md` keeps its history (R-30).

Deleted: no file.

## Dependencies

- The misthelper-devtools release 0.7.0 must exist before T013 changes the pin.
- The pin change and the baseline migration merge in one pull request. A pin change alone fails the gate, because the loader rejects the old format (D-7).
- Issue 4142 may move test files. A move after this change merges requires a second migration for the moved entries.
- The reusable workflow pins stay at v0.6.4 (R-53, D-14).

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| The upstream release is delayed | MistHelper implementation waits | Tasks T001 to T009 run first. The record stays complete. |
| Count-based prune removes an entry that a detector stopped producing | A baseline entry is lost | Prune keeps parse-error and skipped files. The pull request lists each dropped entry. Git restores removed entries. |
| An identical statement replaces a removed statement in the same file | The net count stays zero, and the change is not reported | Caution: residual risk, recorded in D-4. The `gate_removed` count shows the removal. |
| A test signature changes in a test with no assertions | The flagged `def` line changes, so the gate reports a new finding | By design (FR-003). The reviewer regenerates the entry through the migration rule. |
| A test file moves | The moved entries become new and removed | Coordinate with issue 4142. Run the migration after the move. |
| A file-level detector emits a finding without the sentinel | The anchor depends on line 1, so a header change breaks the gate | T002 adds a test for the sentinel. The detector list is in `analysis.md`. |
| An untested source module is unreadable | The gate exits 2 | The error names the path. T004 adds a test for the exit code. |
| The migration diff is large | Review takes longer | The diff adds one anchor line per retained entry. The pull request body lists dropped entries and counts. |
| The gate output format changes | A log reader breaks | The `test_quality_gate` job reads only the exit code (R-04). Other readers are unverified. |

## Rollback

1. Revert the MistHelper pull request, or set `requirements-dev.txt` line 197 back to `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
2. Restore `.github/test-quality-baseline.json` from the commit before the migration.
3. Run the full-suite gate. Expect `gate: 0 new findings vs baseline` with the old pin.
4. Leave the 0.7.0 release in place. Publish a fix release if a defect appears.

Warning: a pushed release tag is public. Do not delete or move the tag v0.7.0.

## Contracts

The folder `design/contracts` holds two files:

- `baseline-schema.md` defines the baseline entry fields, the identity key, the anchor algorithm, and the validation rules.
- `gate-output.md` defines the stdout lines and the exit codes for the gate and the prune commands.

No Mist API contract applies.

## Checklists

`design/checklists/requirements.md` holds twenty items. Each item is checked and cites its evidence.

## Structure Decision

The spec record uses the route `specs\numbered\0\0\0\4\4\4\0\2`, which the spec-route script defines with width 8 and base 5 (R-18). The record keeps `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Supporting files go in `design`, as the constitution requires for new bounded records.

## Complexity Tracking

No violation needs justification. Existing debt stays in place:

- The package root of misthelper-devtools holds 12 children (R-55). The change adds no child.
- The MistHelper folder `tests/guardrails/local_test_quality_loop` holds five children (R-15). The change adds no child.
- The legacy debt is not changed by this record. A separate remediation issue owns it.
