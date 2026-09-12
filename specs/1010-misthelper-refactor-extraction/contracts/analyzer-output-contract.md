# Contract: Refactor Analyzer Output

**Feature**: 1010-misthelper-refactor-extraction
**Producer**: `tools/refactor_analyzer/` (consumed as-is per FR-018; never modified by this initiative)
**Consumer**: The extraction dispatcher (parent conversation) and per-PR verification steps in `quickstart.md`
**Artifact**: `refactor_candidates.md` at repo root

---

## Contract Guarantees the Producer MUST Make

The analyzer, when invoked as `py -m tools.refactor_analyzer MistHelper.py -o refactor_candidates.md`, MUST emit a Markdown document at the specified output path with the following structure:

1. **Summary section** containing counts per bucket (Unused, Single-Use, Low-Use, Hot, Skipped) and a total-saveable-LOC figure.
2. **Unused section** listing every candidate with 0 references. Each entry includes: symbol name, kind (class/function), source line range in `MistHelper.py`, LoC count, and any `guideline_flags`.
3. **Single-Use section** listing every candidate with exactly 1 reference. Each entry additionally includes the caller's file and line number.
4. **Low-Use section** listing candidates with 2-3 references (informational for first pass; second-pass scope).
5. **Hot section** listing candidates with 4+ references (out of scope for first pass per FR-009).
6. **Skipped section** listing symbols in the `SKIP_ALWAYS` allowlist (`GlobalImportManager` and any others; never modified per FR-008).
7. **Limitations section** documenting known analyzer blind spots (e.g. dynamic dispatch, `getattr` string lookups).

---

## Contract Guarantees the Consumer MUST Honor

1. **Bucket authority**: The consumer treats the analyzer's bucket assignment as the single source of truth for dispatch. Manual grep wins ONLY for the specific PR where a discrepancy surfaces (spec Edge Cases); the discrepancy is filed as an analyzer bug but does NOT halt the initiative.

2. **Fresh-catalog dispatch**: The consumer regenerates `refactor_candidates.md` on the current `main` head **after every merged extraction PR, before the next PR is opened** (FR-010, SC-011). No dispatch decision may be made from a stale catalog.

3. **Reclassification handling** (FR-016):
   - If a first-pass candidate is reclassified into `Low-Use` or `Hot` after a prior merge, it is rerouted to second-pass planning or Out-of-Scope; it is NOT force-extracted under its original classification.
   - If a candidate is reclassified into `Unused`, it moves to the Unused workflow (delete only, no new module).
   - If a candidate is reclassified into `Skipped`, no PR is opened for it.

4. **No analyzer modification** (FR-018): The consumer never edits `tools/refactor_analyzer/*.py`. If the analyzer emits incorrect output, the consumer files an analyzer bug for a separate initiative and works around it manually within the affected PR.

5. **LoC drift tolerance**: Because `MistHelper.py` may have unrelated commits between analyzer runs, the LoC count for any candidate is taken from the **fresh** analyzer output at Step 1 of `quickstart.md`, not from a snapshot elsewhere.

---

## Invariants

- The Skipped section content (`SKIP_ALWAYS`) never intersects with any other bucket in the same catalog.
- The Hot section content never intersects with Single-Use or Unused in the same catalog.
- Every candidate has a stable `name` that identifies a unique symbol in `MistHelper.py`.
- LoC counts are `end_line - start_line + 1`.

---

## Error Modes and Consumer Responses

| Error mode | Consumer response |
|------------|-------------------|
| Analyzer emits no output / crashes | Do not open the next PR. Investigate as an analyzer bug in a separate initiative. Do NOT modify the analyzer here (FR-018). |
| Candidate present in two buckets | Treat as an analyzer bug; take the more conservative bucket (Skipped > Hot > Low-Use > Single-Use > Unused). File the bug. |
| Candidate `reference_count == 1` but manual grep finds 2 hits (dynamic dispatch) | Reroute the candidate to Low-Use planning. Manual grep wins for that PR. File the analyzer bug. |
| Candidate `reference_count == 0` but manual grep finds 1 hit | Reclassify to Single-Use workflow for that PR (create module, rewrite callsite, delete original). Manual grep wins. |
| Fresh catalog shows a merged candidate still present | Investigate for merge/regeneration miss; regenerate again. Do NOT dispatch the next PR until the catalog reflects reality. |

---

## Verification

At the start of each PR, the operator confirms Contract compliance by:

1. Running the regeneration command from a clean checkout of `main` at the head after the last merge.
2. Diffing the new catalog against the prior one — the just-merged candidate must have been removed from its bucket.
3. Recording the catalog commit SHA (if the catalog is committed) or the regeneration timestamp in the next PR's description for the SC-011 audit trail.
