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

- [ ] T001 Regenerate the dictionary if missing:
  `& ".venv\Scripts\python.exe" -m tools.ste_linter.dictionary.extract documentation/ASD-STE100_ISSUE9.pdf`.
- [ ] T002 Produce the Phase 1 target list. Run the linter across `src/` and
  filter to STE-S9-LATIN, STE-S4-CONTRACTION, STE-S9-PHRASAL, STE-S9-GENDER,
  STE-S7-WARNING, and STE-S6-PARA. Save the file and line list.
- [ ] T003 [P] Fix STE-S9-LATIN (167). Replace "e.g." with "for example".
  Replace "i.e." with "that is". Replace "etc." with "and so on". Replace
  "vs." with "versus".
- [ ] T004 [P] Fix STE-S4-CONTRACTION (117). Expand each contraction. For
  example, "does not" for "doesn't".
- [ ] T005 [P] Fix STE-S9-PHRASAL (9). Replace each phrasal verb with a single
  verb. For example, "start" for "kick off".
- [ ] T006 [P] Fix STE-S7-WARNING (10). Add the consequence after the signal
  word. For example, "Warning: this step can delete data."
- [ ] T007 [P] Fix STE-S6-PARA (4). Split the long paragraph into shorter ones.
- [ ] T008 [P] Fix STE-S9-GENDER (2). Replace the gendered term with a neutral
  term.
- [ ] T009 Re-run the linter on `src/`. Confirm the six mechanical rules report
  zero violations.
- [ ] T010 Run the full CI gate set. Confirm all gates pass.
- [ ] T011 Open the Phase 1 pull request. Link issue #1687. Wait for CodeQL.
  Add the auto-merge label after all checks pass.

**Checkpoint**: Phase 1 merged. Mechanical rules at zero.

---

## Phase 2: Prose Semicolons (User Story 2, P2)

**Goal**: Remove prose semicolons. Keep code examples in docstrings.

**Pull request**: one per module cluster, or a small set of clusters.

- [ ] T012 Produce the Phase 2 target list. Run the linter across `src/` and
  filter to STE-S8-SEMICOLON. Group by module cluster.
- [ ] T013 [P] Cluster `firmware`. Review each semicolon. Split prose into two
  sentences. Keep shell and Python examples unchanged.
- [ ] T014 [P] Cluster `org`. Same review and fix pattern.
- [ ] T015 [P] Cluster `maps`. Same review and fix pattern.
- [ ] T016 [P] Cluster `site` (includes `address_audit`). Same pattern.
- [ ] T017 [P] Cluster `analytics`. Same pattern.
- [ ] T018 [P] Cluster `export`. Same pattern.
- [ ] T019 [P] Cluster `refactors`. Same pattern.
- [ ] T020 [P] Remaining clusters (`utils`, `device`, `capture`, `network`,
  `websocket`, `troubleshooting`, `gateway`, `inventory`, and others). Same
  pattern.
- [ ] T021 Re-run the linter with the semicolon rule on the changed files.
  Confirm prose semicolons are gone. Confirm code examples still work.
- [ ] T022 Run the full CI gate set for each cluster pull request. Confirm pass.
- [ ] T023 Open each cluster pull request. Link issue #1687. Wait for CodeQL.
  Add the auto-merge label after all checks pass.

**Checkpoint**: Phase 2 merged. Prose semicolons removed. Code examples kept.

---

## Phase 3: Passive, Length, and Tense (User Story 3, P3)

**Goal**: Reduce passive voice, long sentences, and past tense by module.
Keep the meaning.

**Pull request**: one per module cluster. Take the worst clusters first.

- [ ] T024 Produce the Phase 3 target list. Run the linter across `src/` and
  filter to STE-S3-PASSIVE, STE-S4-LEN, and STE-S3-TENSE. Group by cluster.
- [ ] T025 [P] Cluster `org` (worst: org_synthetic_probes_manager.py). Rewrite
  passive to active when the actor is known. Split long sentences. Use present
  tense for instructions.
- [ ] T026 [P] Cluster `firmware` (org_ap_upgrader.py, firmware_manager.py,
  bulk_ap_upgrader.py). Same fix pattern.
- [ ] T027 [P] Cluster `maps` (maps_manager.py). Same fix pattern.
- [ ] T028 [P] Cluster `site` and `address_audit`. Same fix pattern.
- [ ] T029 [P] Cluster `utils` (zscaler_catalogue.py, zscaler_probe.py,
  address_utils.py). Same fix pattern.
- [ ] T030 [P] Cluster `export`, `analytics`, `refactors`. Same fix pattern.
- [ ] T031 [P] Remaining clusters. Same fix pattern.
- [ ] T032 Re-run the linter with the three judgment rules on each changed
  module. Confirm the counts drop and no meaning is lost.
- [ ] T033 Run the full CI gate set for each cluster pull request. Confirm pass.
- [ ] T034 Open each cluster pull request. Link issue #1687. Wait for CodeQL.
  Add the auto-merge label after all checks pass.

**Checkpoint**: Phase 3 merged. Judgment rules reduced. Meaning kept.

---

## Final Verification

- [ ] T035 Run the full linter on `src/`. Confirm the six mechanical rules stay
  at zero. Confirm the judgment counts dropped.
- [ ] T036 Confirm STE-S1-WORD, STE-S1-POS, and STE-S2-NOUNCLUSTER counts did
  not change (no edits to false positives).
- [ ] T037 Confirm every phase pull request touched comments and docstrings
  only. No code behavior change.
- [ ] T038 Close issue #1687 when all phases are merged.

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
