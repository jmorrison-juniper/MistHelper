# Contract: Extraction PR Shape

**Feature**: 1010-misthelper-refactor-extraction
**Producer**: Refactor engineer (opens PR)
**Consumer**: GitHub Actions CI + code reviewers + `main` branch protection
**Artifact**: A single pull request against `main`

---

## Diff Shape Contract

An extraction PR's diff MUST match exactly one of the two shapes below.

### Shape A: Unused Deletion (PR-01, PR-02)

Exactly one file changed:

- `MistHelper.py` — the candidate's definition (class or function body) is removed. Nothing added.

Additionally required:
- PR description contains a repo-wide grep confirming zero remaining references to the symbol (FR-004).

Prohibited in this shape:
- Any new file.
- Any callsite rewrite (there are none by definition).
- Any wrapper shim or forwarding function.

### Shape B: Single-Use Extraction (PR-03 through PR-13)

Exactly three files changed (or two for the `AddressComparisonCounters` fold-in):

1. **`MistHelper.py`** — the candidate's definition is removed. Nothing added.
2. **The target module**:
   - For 10 of 11 Single-Use PRs: a NEW file under `src/refactors/{snake_name}.py` containing the candidate as a cohesive class (or as a class method for module-level function candidates per FR-005).
   - For `AddressComparisonCounters` (PR-07 exception per FR-015): the EXISTING `src/inventory/csv_comparator.py` is modified — the counter folds into `CsvComparatorManager` (no new file).
3. **The caller's file** — the single callsite is rewritten. This may be the same file as #2 (for `AddressComparisonCounters`, since the sole caller already lives in `csv_comparator.py`), collapsing to two files.

Additionally allowed:
- `refactor_candidates.md` regeneration diff in the same PR (documents Step 6 verification per `quickstart.md`).
- `data/full_repo_compliance_current.md` update if the extraction improved the baseline snapshot.

Prohibited in this shape:
- More than one candidate per PR (FR-002).
- Wrapper shim, forwarding function, or backward-compatibility alias anywhere in the diff (FR-003, SC-008).
- Preserving a module-level function candidate as a bare `def` at module scope in the new file (FR-005).
- Deferring `guideline_flags` resolution to a follow-up PR (FR-006).
- Modifying `tools/refactor_analyzer/` (FR-018).
- Modifying any symbol in the `SKIP_ALWAYS` bucket (FR-008).
- Modifying any symbol in the Hot bucket (FR-009).

---

## Commit Contract

- PRs are squash-merged. The squash-merge commit message is the single conventional-commit message on `main`.
- Convention: `refactor: extract {SymbolName} to {target_path} (#PR)` for Shape B; `refactor: delete unused {SymbolName} (#PR)` for Shape A. Follows the repo's existing pattern (see recent commits e50a524, 4176bc8, 6c2e0b6).
- Branch is auto-deleted on merge (`gh pr merge --squash --delete-branch`).

---

## Merge Contract

An extraction PR MUST NOT be merged unless ALL of the following hold:

1. **All 15 functional CI jobs report green** (FR-011, SC-006).
2. **`mergeStateStatus == CLEAN`** (per `feedback_no_admin_bypass.md` guidance).
3. **Compliance analyzer output**:
   - Target module (if any) scored A+/100 (FR-012, SC-007).
   - Zero previously-A+ files regressed below A+ (SC-005).
   - Repo-wide baseline ≥ 99.6/A+ (FR-013, SC-004).
4. **Refactor analyzer output**:
   - The candidate has been removed from its bucket in the regenerated catalog.
   - No new NEEDS CLARIFICATION-equivalent surprises (e.g. new dynamic-dispatch call to the moved symbol).

`--admin` merge bypass MUST NOT be used as a routine unblock. Bypass is acceptable only when `mergeStateStatus` is genuinely `BLOCKED`, `DIRTY`, or `BEHIND` for a documented reason unrelated to the merge readiness of the extraction itself (e.g. an unrelated required check is transiently unavailable). Root cause MUST be documented in the PR description in that case.

---

## Guideline-Flag Resolution Contract

For every `guideline_flag` the analyzer reported on the extracted code, the flag MUST be resolved within THIS PR (FR-006, SC-012). No forward-carry.

| Flag | Resolution in the extracted module |
|------|-----------------------------------|
| `oversize_25_lines` | Refactor the offending method into smaller helpers before landing. |
| `missing_inline_comments` | Add inline comments every 5-10 lines (Principle VI, NON-NEGOTIABLE). |
| `missing_action_logging` | Add action logging before every non-trivial action with `[MENU]`/`[EXECUTE]`/`[SUCCESS]`/`[FAILURE]` prefixes (Principle VII, NON-NEGOTIABLE). |
| `non_ascii_logs` | Replace non-ASCII characters with ASCII equivalents (Principle V, FR-007). |
| `hardcoded_separator` | Replace hardcoded path separators with `pathlib.Path` or `os.sep` as appropriate; prefer `pathlib.Path` (Principle V, FR-007). |
| `raw_input_call` | Replace with `safe_input()` (Principle V, FR-007). |
| `too_many_params` | Introduce a dataclass or config object to group related parameters; use judgment on threshold. |

---

## Verification Checklist (paste into PR description)

```markdown
## Extraction PR Verification (spec 1010)

- [ ] Exactly one candidate (Unused shape or Single-Use shape) — no batching (FR-002)
- [ ] No wrapper shim / forwarding fn / backward-compat alias in MistHelper.py (FR-003, SC-008)
- [ ] Module-level function candidates land as class methods, not bare defs (FR-005, if applicable)
- [ ] All analyzer guideline_flags on extracted code resolved in-flight (FR-006, SC-012)
- [ ] ASCII-only logs, safe_input(), pathlib.Path in extracted module (FR-007)
- [ ] No SKIP_ALWAYS symbol touched (FR-008)
- [ ] No Hot-bucket symbol touched (FR-009)
- [ ] refactor_candidates.md regenerated on post-preceding-merge main head (FR-010, SC-011)
- [ ] 15/15 CI jobs green, mergeStateStatus CLEAN, no --admin bypass (FR-011, SC-006)
- [ ] Target module A+/100 (or existing sibling module preserved A+) (FR-012, SC-007)
- [ ] Repo baseline ≥99.6/A+, zero A+ regressions (FR-013, SC-004, SC-005)
- [ ] Manual grep of symbol name pasted (mandatory for Unused, recommended for Single-Use)
```
