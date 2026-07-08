# Quickstart: Single Extraction PR — Operator Recipe

**Feature**: 1010-misthelper-refactor-extraction | **Date**: 2026-07-05
**Purpose**: The 8-step loop a refactor engineer executes for each of the 13 first-pass PRs.

This is the recipe. `spec.md` is the contract, `plan.md` is the queue, `data-model.md` is the entity glossary, `contracts/*` are the interface rules. This file tells you what to *do*.

---

## Preconditions

- Working tree on `main`, clean (`git status` shows no changes).
- No other extraction PR currently open (serial-only per spec Edge Cases).
- Previous extraction PR (if any) merged AND `refactor_candidates.md` has been regenerated on the post-merge `main` head.

If any precondition fails: stop, resolve, then restart at Step 1.

---

## Step 1 — Regenerate the catalog

Run the analyzer on the current `main` head:

```bash
py -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md
```

Inspect the diff. If a first-pass candidate has drifted out of Unused/Single-Use into Low-Use/Hot, reroute per FR-016 (skip and reschedule). If Single-Use → Unused, reclassify to the Unused workflow (delete only, no new module).

---

## Step 2 — Select the next candidate

Per FR-001: process Unused first (LOC-DESC within), then Single-Use (LOC-DESC within).

Given the 13-candidate first-pass budget (FR-014), the dispatch order is fixed:

1. `PerformanceMonitor` (Unused, 40 LoC) — delete
2. `MapViewerConfig` (Unused, 9 LoC) — delete
3. `SQLiteDatabaseWriter` (Single-Use, 316 LoC) — extract
4. `TUILauncher` (Single-Use, 154 LoC) — extract
5. `DataDirectoryChecker` (Single-Use, 74 LoC) — extract
6. `MapsManagerLauncher` (Single-Use, 64 LoC) — extract
7. `AddressComparisonCounters` (Single-Use, 62 LoC) — fold into `CsvComparatorManager` (FR-015)
8. `ServicePingManager` (Single-Use, 50 LoC) — extract
9. `WAN2MigrationManager` (Single-Use, 48 LoC) — extract
10. `run_systematic_test` (Single-Use, ~35 LoC) — extract as class method (FR-005)
11. `switch_to_interactive_login` (Single-Use, ~30 LoC) — extract as class method
12. `run_interactive_test` (Single-Use, ~28 LoC) — extract as class method
13. `listen_keyboard` (Single-Use, ~24 LoC) — extract as class method

The next slot after PR-N-merge is always PR-(N+1) unless the Step 1 catalog says otherwise.

---

## Step 3 — Verify the analyzer's caller claim

For **Unused** candidates:

```bash
grep -RIn "\bSymbolName\b" --include="*.py" .
```

Zero non-definition hits required. Paste the grep output into the PR description as manual verification (FR-004). If a hit appears, it is dynamic dispatch (or an analyzer bug): investigate, and if it's a real reference, reroute the candidate to Single-Use workflow instead.

For **Single-Use** candidates:

```bash
grep -RIn "\bSymbolName\b" --include="*.py" .
```

Expect exactly two contexts: the definition in `MistHelper.py` and the single caller. If a third context appears, reroute to Low-Use or Hot planning per FR-016. Recommended (not mandatory) to paste the grep in the PR description as belt-and-suspenders.

---

## Step 4 — Create the branch and open the working PR (draft)

```bash
git checkout -b refactor/extract-{snake_name}
```

For **Unused**: no new file. Skip to Step 5.

For **Single-Use**: create the target module file per the queue in `plan.md`. Land the class with:

- ASCII-only logs (Principle V, FR-007).
- `safe_input()` for interactive input.
- `pathlib.Path` in place of `os.path`.
- Inline comments every 5-10 lines (Principle VI, NON-NEGOTIABLE).
- Action logging before every non-trivial action with the correct prefix (Principle VII, NON-NEGOTIABLE).
- Module-level function candidates land as **class methods** on a new cohesive class (FR-005).
- `AddressComparisonCounters` folds into `src/inventory/csv_comparator.py::CsvComparatorManager` (FR-015 — no new file).
- Every `guideline_flag` the analyzer reported on the extracted code is resolved in this file (FR-006, SC-012).

---

## Step 5 — Rewrite the single callsite and delete the original

In the **same commit**:

1. Delete the original symbol definition from `MistHelper.py` (do not leave a wrapper, forwarding function, or backward-compat alias — FR-003, SC-008).
2. For **Single-Use**: update the caller's `from MistHelper import SymbolName` (or bare-name reference) to `from src.refactors.new_module import SymbolName` (or the equivalent for the AddressComparisonCounters fold-in).
3. For module-level function candidates rewritten as class methods, update the caller from `func(args)` to `NewClass().func(args)` or the domain-appropriate method name.

Verify no intermediate commit on the branch leaves a dangling import or dangling definition.

---

## Step 6 — Local gate check

Before pushing:

```bash
py -m tools.compliance_analyzer
```

Confirm:
- New module (if any) scored A+/100 (FR-012, SC-007).
- `MistHelper.py` grade did not regress.
- Zero previously-A+ files dropped below A+ (SC-005).
- Repo-wide score ≥ 99.6/A+ (FR-013, SC-004).

Then re-run the refactor analyzer:

```bash
py -m tools.refactor_analyzer MistHelper.py
```

Confirm the just-extracted symbol has been removed from the appropriate bucket. Include the regenerated `refactor_candidates.md` in the PR diff.

Run whatever local test/lint invocations correspond to the 15 CI jobs.

---

## Step 7 — Push, open PR, wait for CI

```bash
git push -u origin refactor/extract-{snake_name}
gh pr create --title "refactor: extract {SymbolName} ({loc} lines)" \
  --body "$(cat <<'EOF'
Extracts {SymbolName} from MistHelper.py into {target_path}.

- Source: MistHelper.py:{line_range}
- Callsite rewritten: {caller_file}:{caller_line}
- Compliance: {target_module} A+/100, MistHelper.py unchanged grade, repo ≥99.6/A+
- Guideline flags resolved in-flight: {list}

Manual grep verification:
```
{grep output here}
```
EOF
)"
```

Wait for all 15 functional CI jobs to report green. Consult `mergeStateStatus`:

- `CLEAN` → proceed to Step 8.
- `BLOCKED` / `DIRTY` / `BEHIND` → rebase against `main`, push, re-run CI. Do NOT use `--admin` bypass as a routine unblock (FR-011). Only invoke `--admin` when the root cause is genuinely a required-check-that-doesn't-apply scenario, and document it in the PR body per `feedback_no_admin_bypass.md`.

---

## Step 8 — Squash-merge and delete branch

```bash
gh pr merge --squash --delete-branch
```

Confirm on `main`:

```bash
git checkout main
git pull
```

Then immediately loop back to Step 1 for the next candidate. The catalog must be regenerated on this fresh `main` head before PR-(N+1) is opened (FR-010, SC-011).

---

## After PR-13

- `refactor_candidates.md` Unused bucket should show 0 entries (SC-001).
- `refactor_candidates.md` Single-Use bucket should show 0 entries (SC-002).
- `MistHelper.py` physical line count should have dropped by ≥600 lines (SC-003).
- Zero wrapper shims remain (SC-008).
- Zero `SKIP_ALWAYS` symbols were modified (SC-009).
- Zero Hot-bucket symbols were extracted in this pass (SC-010).
- Every new `src/refactors/*.py` scored A+/100 (SC-007).
- Repo-wide compliance ≥ 99.6/A+ (SC-004), zero A+ regressions (SC-005).

Report the aggregate LoC reduction and file the initiative's closeout note. Second-pass Low-Use planning is a **separate initiative** — do not roll into this one (Assumption 6).

---

## Cheat Sheet

```bash
# Full loop, condensed
py -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md   # Step 1
# (select candidate — Step 2)
grep -RIn "\bSymbolName\b" --include="*.py" .                            # Step 3
git checkout -b refactor/extract-{snake_name}                            # Step 4
# (create module, land class, resolve guideline_flags — Step 4)
# (delete original + rewrite callsite in same commit — Step 5)
py -m tools.compliance_analyzer                                          # Step 6
py -m tools.refactor_analyzer MistHelper.py                              # Step 6
git push -u origin refactor/extract-{snake_name}                         # Step 7
gh pr create --title "..." --body "..."                                  # Step 7
# (wait for 15 CI jobs green, mergeStateStatus=CLEAN — Step 7)
gh pr merge --squash --delete-branch                                     # Step 8
git checkout main && git pull                                            # Step 8
# loop to Step 1
```
