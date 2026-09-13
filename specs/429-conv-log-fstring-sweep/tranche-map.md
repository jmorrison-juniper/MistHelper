# Tranche Boundary Map — Issue #429

**Source of truth**: `data/compliance_report_fresh.md` regenerated 2026-06-23 in this worktree (`python tools/check_compliance.py MistHelper.py`).

**Total in-scope sites**: 695 (681 G004 + 6 G003 + 8 G201)

## Derivation

1. Extract every CONV-LOG-FSTRING (= G004) row from the compliance report markdown table; parse the first `| <line> |` column.
2. Sort ascending. Resulting list: 681 unique line numbers, range L315–L23933.
3. Divide into 4 contiguous groups of ~170 sites each (closer to the spec's "~200 per tranche" guidance than 6 groups of 114 would be — fewer commits = less CI burn, still under the reviewer-fatigue threshold).
4. Fold the 6 G003 sites and 8 G201 sites into whichever tranche contains their line number (no extra commits needed — they ride along).

## Tranche Table (G004 only — G003/G201 sites listed below for cross-reference)

| Tranche | Start line | End line | G004 count | G003 sites in range | G201 sites in range |
|---:|---:|---:|---:|---|---|
| **1** | 315 | 6970 | 171 | L6120 | (none) |
| **2** | 6988 | 10282 | 171 | L8316 | L8684, L9286 |
| **3** | 10298 | 15076 | 171 | L10898, L10991, L13421 | L12303, L12486, L12695, L14399 |
| **4** | 15088 | 23933 | 168 | L16950 | L20968, L23638 |
| **Total** |  |  | **681** | **6** | **8** |

> The G003/G201 site assignments above are derived from `ruff check --select G003,G201 MistHelper.py` run 2026-06-23 in this worktree. Re-confirm at each tranche's start because the ruff output may shift slightly as upstream sites are converted (line numbers do not change because the codemod preserves line counts; format reflows are limited to argument lines that were already wrapped).

**Verified: 2026-06-23** (T006) — re-ran `python -m ruff check --select G003,G004,G201 MistHelper.py` in worktree `MistHelper-429-fstring` on commit `358b8c8`. Exact counts: **G004=681, G003=6, G201=8 (total 695)**. L13421 confirmed **G003-only** (the earlier "(verify)" annotation against G201 was incorrect — no G201 violation reported at that line). L16950 G003 (tranche 4) and the additional G201 sites at L12486, L12695, L14399, L20968, L23638 were missing from the previous draft of this table; both have been incorporated above.

## Per-tranche acceptance gate

After each tranche commit:

```powershell
python -m ruff check --select G003,G004,G201 MistHelper.py --statistics
```

Expected G004 count decrease per tranche: 171, 171, 171, 168 (cumulative: 510, 339, 168, 0).

## Re-tranche policy

If a tranche's actual converted-site count diverges by more than ±10 from the table above (e.g., the codemod skips a site because of an unrecognized format spec), **do not auto-rebalance** mid-sweep. Instead:

1. Commit the tranche as-is (with reduced count documented in commit message).
2. Add a follow-up task in `tasks.md` to either (a) extend the codemod to handle the skipped pattern, or (b) hand-convert the skipped sites in a dedicated fix-up tranche before Phase 5 (ruff-config commit).

The Phase 5 commit MUST NOT land while any G003/G004/G201 violation remains.
