# Research: STE Compliance for src/ Comments and Docstrings

**Feature**: 1030-ste-src-cleanup | **Date**: 2026-07-27

This document records the scan findings and the rule-by-rule decisions. It
grounds the plan and tasks in real data, not guesses.

## Scan Method

- Tool: the STE linter in `tools/ste_linter/` on `main`.
- Backend: spaCy (`en_core_web_sm`), auto-selected when present.
- Dictionary: `data/ste_dictionary.json`, 2,136 entries, generated from the
  ASD-STE100 Issue 9 source.
- Input: all `src/**/*.py` files (359 files, 108,543 lines).
- Method: one in-process pass. The scan builds the spaCy backend once, then
  loops all files. It aggregates violations by rule and by file.

## Finding 1: All Files Already Pass the Gate

Every file scores 80 or higher. The score buckets are:

| Score band | Files |
| - | - |
| 80 to 89 | 10 |
| 90 to 99 | 321 |
| 100 | 28 |

**Decision**: This feature reduces the count of real violations. It does not
fix a failure. The value is readability, not a passing grade.

## Finding 2: Most Violations Are False Positives

The scan found 67,161 raw violations. The split is:

| Group | Count | Share |
| - | - | - |
| Dictionary (STE-S1-WORD, STE-S1-POS) | 58,994 | 88 percent |
| Noun clusters (STE-S2-NOUNCLUSTER) | 3,883 | 6 percent |
| In scope (mechanical plus judgment) | 4,313 | 6 percent |

**Decision**: The dictionary rules flag normal code words such as `api`,
`async`, and `dict`. These words are not in the ASD-STE100 vocabulary of about
875 words. The team does not edit these. It does not grow the allowlist to hide
them. Feature 1028 reached the same decision for `MistHelper.py`.

The noun-cluster rule flags legitimate technical terms such as "Live Mist API
session" and tokenizer hyphen splits such as "non - critical". About 95 percent
are false positives. The team leaves these unchanged.

## Finding 3: Mechanical Rules Are Finite and Safe

The six mechanical rules total 309 violations across 128 files.

| Rule | Count | Fix pattern |
| - | - | - |
| STE-S9-LATIN | 167 | "e.g." to "for example". "etc." to "and so on". "i.e." to "that is". "vs." to "versus". |
| STE-S4-CONTRACTION | 117 | "doesn't" to "does not". "can't" to "cannot". "it's" to "it is". |
| STE-S7-WARNING | 10 | State the consequence after the signal word. |
| STE-S9-PHRASAL | 9 | "kick off" to "start". |
| STE-S6-PARA | 4 | Split a long paragraph. |
| STE-S9-GENDER | 2 | Use a neutral term. |

**Decision**: Fix all six rules in Phase 1. Each fix is a direct swap. The
linter confirms the result. This is the safest and largest clear win.

## Finding 4: Semicolons Need Per-File Review

The scan found 2,147 STE-S8-SEMICOLON violations. Many are code examples inside
docstrings, such as PowerShell one-liners like `podman stop; podman rm`. These
are shell syntax, not prose. The linter cannot tell them apart.

**Decision**: Review each file before a fix. Split prose semicolons into two
sentences. Keep code examples unchanged. This is Phase 2.

## Finding 5: Passive, Length, and Tense Need Judgment

| Rule | Count |
| - | - |
| STE-S3-PASSIVE | 1,200 |
| STE-S4-LEN | 446 |
| STE-S3-TENSE | 182 |

**Decision**: Fix these by module cluster in Phase 3. Each fix needs a human
decision to keep the meaning. Rewrite passive voice only when the actor is
known. Split long sentences into single ideas. Change past tense to present for
instructions.

## Finding 6: Worst Files by Structural Count

The structural count excludes the dictionary and noun-cluster false positives.

| File | Structural |
| - | - |
| src/org/org_synthetic_probes_manager.py | 319 |
| src/firmware/org_ap_upgrader.py | 228 |
| src/firmware/firmware_manager.py | 210 |
| src/firmware/bulk_ap_upgrader.py | 173 |
| src/maps/maps_manager.py | 165 |

**Decision**: The `firmware` and `org` clusters carry the most work. Order the
judgment phases to take the worst clusters first.

## Finding 7: src/ Has Stricter CI Gates

Unlike `MistHelper.py` comments, `src/` files are covered by coverage (80
percent), mypy (`src/`), and radon (CC 10 or less). Comment and docstring edits
do not change code, so these gates stay green. The team verifies each phase with
the full gate set before it adds the auto-merge label.

## Alternatives Considered

- **Fix everything, including dictionary words**: Rejected. About 88 percent are
  false positives. Editing them harms readability and inflates the allowlist.
- **One large pull request**: Rejected. About 4,313 fixes in one diff is
  unreviewable. It also risks merge conflicts on hot files such as
  `firmware_manager.py`.
- **Grow the allowlist to zero the dictionary rules**: Rejected. The allowlist
  is for a small set of core code terms, not a mask for the whole code
  vocabulary.
