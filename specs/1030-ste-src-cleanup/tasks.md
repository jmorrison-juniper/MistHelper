# Tasks: STE Compliance for src/ Comments and Docstrings

**Feature**: 1030-ste-src-cleanup | **Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Issue**: #1687

## Conventions

- `[P]` marks tasks that can run in parallel (different files, no dependency).
- Each phase is a separate pull request. Each pull request links to issue #1687.
- Run all edits from the worktree with `.venv\Scripts\python.exe`.
- Verify each phase with the full CI gate set before the auto-merge label.
- Every touched code line keeps its inline comment.

## Gate Command Reference

Run these from the worktree root before each pull request:

```powershell
& ".venv\Scripts\python.exe" -m ruff check .
& ".venv\Scripts\python.exe" -m black --check .
& ".venv\Scripts\python.exe" -m mypy src/ --config-file pyproject.toml
& ".venv\Scripts\python.exe" -m radon cc src/ -n C
& ".venv\Scripts\python.exe" -m pytest --cov=src --cov-fail-under=80
```

Per-rule linter check across `src/` (adjust `--ignore` to isolate a rule group):

```powershell
& ".venv\Scripts\python.exe" -m tools.ste_linter --format json src/**/*.py
```

---

## Phase 1: Mechanical Fixes (User Story 1, P1)

**Goal**: Zero violations for the six mechanical rules across `src/`.

**Pull request**: `1030-ste-src-cleanup` Phase 1.

- [X] T001 Regenerate the dictionary if missing: (delivered: tools/ste_linter/dictionary/extract.py)
  `& ".venv\Scripts\python.exe" -m tools.ste_linter.dictionary.extract documentation/ASD-STE100_ISSUE9.pdf`.
- [X] T002 Produce the Phase 1 target list. Run the linter across `src/` and (delivered: specs/1030-ste-src-cleanup/spec.md)
  filter to STE-S9-LATIN, STE-S4-CONTRACTION, STE-S9-PHRASAL, STE-S9-GENDER,
  STE-S7-WARNING, and STE-S6-PARA. Save the file and line list.
- [X] T003 [P] Fix STE-S9-LATIN (167). Replace "e.g." with "for example". (delivered: src)
  Replace "i.e." with "that is". Replace "etc." with "and so on". Replace
  "vs." with "versus".
- [X] T004 [P] Fix STE-S4-CONTRACTION (117). Expand each contraction. For (delivered: src)
  example, "does not" for "doesn't".
- [X] T005 [P] Fix STE-S9-PHRASAL (9). Replace each phrasal verb with a single (delivered: src)
  verb. For example, "start" for "kick off".
- [X] T006 [P] Fix STE-S7-WARNING (10). Add the consequence after the signal (delivered: src)
  word. For example, "Warning: this step can delete data."
- [X] T007 [P] Fix STE-S6-PARA (4). Split the long paragraph into shorter ones. (delivered: src)
- [X] T008 [P] Fix STE-S9-GENDER (2). Replace the gendered term with a neutral (delivered: src)
  term.
- [X] T009 Re-run the linter on `src/`. Confirm the six mechanical rules report (delivered: specs/1030-ste-src-cleanup/spec.md)
  zero violations.
- [X] T010 Run the full CI gate set. Confirm all gates pass. (delivered: .github/workflows/ci.yml)
- [X] T011 Open the Phase 1 pull request. Link issue #1687. Wait for CodeQL. (delivered: specs/1030-ste-src-cleanup/spec.md)
  Add the auto-merge label after all checks pass.

**Checkpoint**: Phase 1 merged. Mechanical rules at zero.

---

## Phase 2: Prose Semicolons (User Story 2, P2)

**Goal**: Remove prose semicolons. Keep code examples in docstrings.

**Pull request**: one per module cluster, or a small set of clusters.

- [X] T012 Produce the Phase 2 target list. Run the linter across `src/` and (delivered: specs/1030-ste-src-cleanup/spec.md)
  filter to STE-S8-SEMICOLON. Group by module cluster.
- [X] T013 [P] Cluster `firmware`. Review each semicolon. Split prose into two (delivered: src/firmware)
  sentences. Keep shell and Python examples unchanged.
- [X] T014 [P] Cluster `org`. Same review and fix pattern. (delivered: src/org)
- [X] T015 [P] Cluster `maps`. Same review and fix pattern. (delivered: src/maps)
- [X] T016 [P] Cluster `site` (includes `address_audit`). Same pattern. (delivered: src/site)
- [X] T017 [P] Cluster `analytics`. Same pattern. (delivered: src/analytics)
- [X] T018 [P] Cluster `export`. Same pattern. (delivered: src/export)
- [X] T019 [P] Cluster `refactors`. Same pattern. (delivered: src/refactors)
- [X] T020 [P] Remaining clusters (`utils`, `device`, `capture`, `network`, (delivered: src/utils)
  `websocket`, `troubleshooting`, `gateway`, `inventory`, and others). Same
  pattern.
- [X] T021 Re-run the linter with the semicolon rule on the changed files. (delivered: specs/1030-ste-src-cleanup/spec.md)
  Confirm prose semicolons are gone. Confirm code examples still work.
- [X] T022 Run the full CI gate set for each cluster pull request. Confirm pass. (delivered: .github/workflows/ci.yml)
- [X] T023 Open each cluster pull request. Link issue #1687. Wait for CodeQL. (delivered: specs/1030-ste-src-cleanup/spec.md)
  Add the auto-merge label after all checks pass.

**Checkpoint**: Phase 2 merged. Prose semicolons removed. Code examples kept.

---

## Phase 3: Passive, Length, and Tense (User Story 3, P3)

**Goal**: Reduce passive voice, long sentences, and past tense by module.
Keep the meaning.

**Pull request**: one per module cluster. Take the worst clusters first.

- [X] T024 Produce the Phase 3 target list. Run the linter across `src/` and (delivered: specs/1030-ste-src-cleanup/spec.md)
  filter to STE-S3-PASSIVE, STE-S4-LEN, and STE-S3-TENSE. Group by cluster.
- [X] T025 [P] Cluster `org` (worst: org_synthetic_probes_manager.py). Rewrite (delivered: src/org)
  passive to active when the actor is known. Split long sentences. Use present
  tense for instructions.
- [X] T026 [P] Cluster `firmware` (org_ap_upgrader.py, firmware_manager.py, (delivered: src/firmware)
  bulk_ap_upgrader.py). Same fix pattern.
- [X] T027 [P] Cluster `maps` (maps_manager.py). Same fix pattern. (delivered: src/maps)
- [X] T028 [P] Cluster `site` and `address_audit`. Same fix pattern. (delivered: src/site)
- [X] T029 [P] Cluster `utils` (zscaler_catalogue.py, zscaler_probe.py, (delivered: src/utils)
  address_utils.py). Same fix pattern.
- [X] T030 [P] Cluster `export`, `analytics`, `refactors`. Same fix pattern. (delivered: src/export)
- [X] T031 [P] Remaining clusters. Same fix pattern. (delivered: src)
- [X] T032 Re-run the linter with the three judgment rules on each changed (delivered: specs/1030-ste-src-cleanup/spec.md)
  module. Confirm the counts drop and no meaning is lost.
- [X] T033 Run the full CI gate set for each cluster pull request. Confirm pass. (delivered: .github/workflows/ci.yml)
- [X] T034 Open each cluster pull request. Link issue #1687. Wait for CodeQL. (delivered: specs/1030-ste-src-cleanup/spec.md)
  Add the auto-merge label after all checks pass.

**Checkpoint**: Phase 3 merged. Judgment rules reduced. Meaning kept.

---

## Final Verification

- [X] T035 Run the full linter on `src/`. Confirm the six mechanical rules stay (delivered: specs/1030-ste-src-cleanup/spec.md)
  at zero. Confirm the judgment counts dropped.
- [X] T036 Confirm STE-S1-WORD, STE-S1-POS, and STE-S2-NOUNCLUSTER counts did (delivered: specs/1030-ste-src-cleanup/spec.md)
  not change (no edits to false positives).
- [X] T037 Confirm every phase pull request touched comments and docstrings (delivered: specs/1030-ste-src-cleanup/spec.md)
  only. No code behavior change.
- [X] T038 Close issue #1687 when all phases are merged. (delivered: specs/1030-ste-src-cleanup/spec.md)

## Dependencies

- Phase 1 has no dependency. It can start first.
- Phase 2 depends on Phase 1 merged, to avoid overlap on the same files.
- Phase 3 depends on Phase 2 merged, for the same reason.
- Within a phase, tasks marked `[P]` touch different clusters and can run in
  parallel. One agent should hold one cluster at a time to avoid a hot-file
  conflict.

## Notes on Scope

- Total in scope: about 4,313 fixes (309 mechanical plus about 4,004 judgment).
- Out of scope: STE-S1-WORD, STE-S1-POS, STE-S2-NOUNCLUSTER (false positives).
- Every touched code line keeps its inline comment (project mandate).
