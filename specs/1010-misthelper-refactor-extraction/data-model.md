# Phase 1 Data Model: Extraction Entities

**Feature**: 1010-misthelper-refactor-extraction | **Date**: 2026-07-05
**Purpose**: Formalize the entities the workflow manipulates. These are documentation entities (workflow objects), not runtime persistence models.

---

## Entity: Extraction Candidate

The unit of work. One candidate → one PR (FR-002).

| Field | Type | Constraints | Source |
|-------|------|-------------|--------|
| `name` | string | Non-empty, matches a symbol in `MistHelper.py` | analyzer |
| `kind` | enum: `class` \| `function` | Required | analyzer |
| `line_range` | tuple(int, int) | `end >= start`; both point into current `MistHelper.py` | analyzer (fresh) |
| `loc` | int | ≥ 1; `end - start + 1` | analyzer (fresh) |
| `reference_count` | int | ≥ 0 | analyzer |
| `bucket` | enum: `Unused` \| `Single-Use` \| `Low-Use` \| `Hot` \| `Skipped` | Derived from `reference_count` and `SKIP_ALWAYS` list | analyzer |
| `callsite_locations` | list[(file, line)] | Length equals `reference_count`; empty for Unused | analyzer + manual grep verification |
| `guideline_flags` | list[flag_name] | Zero or more of: `oversize_25_lines`, `missing_inline_comments`, `missing_action_logging`, `non_ascii_logs`, `hardcoded_separator`, `raw_input_call`, `too_many_params` | analyzer |
| `target_path` | string (path) | For Unused: N/A; for Single-Use: `src/refactors/{snake_name}.py` OR `src/inventory/csv_comparator.py` (AddressComparisonCounters only, per FR-015) | dispatcher decision |
| `target_class` | string \| null | For module-level function candidates: class name to wrap the function into (per FR-005); null for class candidates that keep their own name; `CsvComparatorManager` for AddressComparisonCounters | dispatcher decision |

**Validation rules**:
- If `bucket == Skipped`, this entity is never selected for a PR (FR-008).
- If `bucket == Hot`, this entity is never selected for the first pass (FR-009).
- If `bucket == Unused`, `callsite_locations` must be empty AND a manual repo-wide grep in the PR description must confirm zero references (FR-004).
- If `bucket == Single-Use`, `callsite_locations` length must be exactly 1 at PR-open time.
- Fresh analyzer data is authoritative — if the catalog is regenerated and a candidate's `bucket` changes, the dispatcher reroutes per FR-016.

**State transitions**:
```
[fresh catalog] --dispatched--> [PR open] --CI green + review approve--> [merged]
                                    |
                                    +--CI red or bucket-change--> [aborted / rerouted]
```

---

## Entity: Target Module

The destination file for a Single-Use extraction.

| Field | Type | Constraints |
|-------|------|-------------|
| `path` | string | Absolute-from-repo-root path; typically `src/refactors/{name}.py` |
| `contains_class` | string | The class name housing the extracted symbol (may be pre-existing for the AddressComparisonCounters exception) |
| `is_new_file` | boolean | True for 10 of 11 Single-Use PRs; False only for AddressComparisonCounters (folds into existing `csv_comparator.py`) |
| `compliance_grade_required` | literal | `A+/100` — non-negotiable (FR-012, SC-007) |
| `logging_convention` | literal | ASCII-only (FR-007, Principle V) |
| `input_convention` | literal | `safe_input()` for all interactive input (FR-007, Principle V) |
| `path_convention` | literal | `pathlib.Path`; no `os.path` (FR-007, Principle V) |
| `comment_cadence` | literal | Every 5-10 lines (Principle VI, NON-NEGOTIABLE) |
| `action_logging` | literal | Before every non-trivial action, with `[MENU]`/`[EXECUTE]`/`[SUCCESS]`/`[FAILURE]` prefixes as appropriate (Principle VII, NON-NEGOTIABLE) |

**Validation rules**:
- New file MUST land at A+/100 on first commit — no "fix compliance in follow-up" pattern (FR-006, FR-012).
- Module-level function candidates MUST land as class methods, not bare `def` (FR-005).
- No wrapper shim, no forwarding function, no backward-compat alias in `MistHelper.py` (FR-003, SC-008).

---

## Entity: Callsite

The single (or zero) location a candidate is invoked from.

| Field | Type | Constraints |
|-------|------|-------------|
| `file` | string | Path within the repo |
| `line` | int | Line of the invocation (may include a preceding `import` line to update) |
| `import_line` | int \| null | Line of the `from MistHelper import ...` statement, if the caller uses an explicit import; null when the caller resolves the symbol via bare name because both live in `MistHelper.py` |
| `rewrite_action` | enum: `update_import` \| `add_import_and_qualify` \| `local_to_local` | `update_import` when caller lives outside MistHelper.py and already imports the symbol; `add_import_and_qualify` when caller doesn't yet import; `local_to_local` when caller lives in MistHelper.py and rewrite is inside the same file (rare) |

**Validation rules**:
- For Unused candidates: no callsite entity exists. Manual grep in PR description substitutes.
- For Single-Use: exactly one callsite. The rewrite happens in the same commit that deletes the definition (FR-003).
- After rewrite, no intermediate revision on the branch may leave a dangling import or a dangling definition.

---

## Entity: Extraction PR

The workflow container.

| Field | Type | Constraints |
|-------|------|-------------|
| `pr_number` | int | Assigned by GitHub |
| `candidate` | ExtractionCandidate | Exactly one (FR-002) |
| `base_branch` | literal | `main` |
| `head_branch` | string | Convention: `refactor/extract-{snake_name}` |
| `diff_contents` | derived | (a) new module file OR deletion only, (b) `MistHelper.py` deletion, (c) callsite rewrite (Single-Use only), (d) any `guideline_flags` remediation |
| `commit_style` | literal | Squash merge; single conventional-commit message on merge |
| `merge_state_status` | enum | `CLEAN` required for merge; `BLOCKED`/`DIRTY`/`BEHIND` require rebase/push and re-run |
| `admin_bypass_used` | boolean | Must be False except with documented BLOCKED/DIRTY/BEHIND root cause (FR-011) |
| `ci_jobs_required_green` | int | 15 (FR-011) |
| `manual_grep_included_in_description` | boolean | Required True for Unused PRs (FR-004); recommended for Single-Use as belt-and-suspenders |
| `catalog_regen_precedes` | boolean | True for every PR after PR-01 — the catalog must be regenerated on the post-preceding-merge `main` head before this PR is opened (FR-010, SC-011) |

**Validation rules**:
- One and only one candidate per PR (FR-002).
- No wrapper shim in the diff (SC-008).
- All `guideline_flags` on extracted code resolved in this PR (FR-006, SC-012).
- If the compliance analyzer reports any A+ file regressing below A+, PR must be reworked (FR-012, SC-005).
- If the compliance analyzer reports repo baseline < 99.6/A+, PR must be reworked (FR-013, SC-004).

---

## Entity: Refactor Candidates Catalog (`refactor_candidates.md`)

The analyzer's ranked output.

| Field | Type | Constraints |
|-------|------|-------------|
| `path` | literal | Repo root: `refactor_candidates.md` |
| `sections` | list[section] | Summary, Unused, Single-Use, Low-Use, Hot, Skipped, Limitations |
| `regeneration_command` | literal | `py -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md` |
| `regeneration_trigger` | literal | After every merged extraction PR, before next PR is opened (FR-010) |
| `authority` | literal | Single source of truth for bucket classification. Manual grep wins ONLY for the specific PR where discrepancy surfaces (spec Edge Cases). |

**Validation rules**:
- Must be regenerated on the current `main` head between PRs.
- Discrepancies with manual grep are filed as analyzer bugs in `tools/refactor_analyzer/` per Edge Cases guidance but the affected PR proceeds using the grep-verified count.
- Analyzer itself is NOT modified by this initiative (FR-018).

---

## Entity: Compliance Baseline

The repo-wide floor.

| Field | Type | Constraints |
|-------|------|-------------|
| `snapshot_path` | literal | `data/full_repo_compliance_current.md` |
| `minimum_repo_grade` | literal | `99.6/A+` (FR-013, SC-004) |
| `minimum_files_at_A_plus` | derived | Count of A+ files pre-initiative; must be preserved (SC-005) |
| `regeneration_command` | literal | `py -m tools.compliance_analyzer` |
| `check_cadence` | literal | Before every PR opens AND in CI |

**Validation rules**:
- Any PR that would push the repo below 99.6/A+ is reworked before merge.
- Any PR that would push a previously A+ file below A+ is reworked before merge.
- The snapshot file itself may be updated as part of extraction PRs when the extraction improves it, or as separate baseline-refresh commits (pattern seen in recent history: e50a524, da4ae90).

---

## Relationships

- One `ExtractionCandidate` → produces exactly one `ExtractionPR` (FR-002).
- One `ExtractionPR` → touches exactly one `TargetModule` (or zero for Unused) + `MistHelper.py`.
- One `ExtractionCandidate` (Single-Use) → has exactly one `Callsite`.
- `RefactorCandidatesCatalog` → enumerates zero or more `ExtractionCandidate` entries per section.
- `ComplianceBaseline` → constrains every `ExtractionPR`.

**Non-relationships (explicit)**:
- An `ExtractionPR` never carries multiple candidates (FR-002).
- A candidate's `guideline_flags` list is never split across PRs — all flags resolved in the one extraction PR (FR-006).
