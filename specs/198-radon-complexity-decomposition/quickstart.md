# Quickstart: Per-Tier Execution Runbook

**Feature**: 198-radon-complexity-decomposition
**Phase**: 1 (Design & Contracts)
**Audience**: The agent (or human) executing the refactor.

This runbook is the single source for *how to actually do the work* once `/speckit.tasks` and `/speckit.implement` are run. Follow the loop top-to-bottom for each tier.

---

## Prerequisites (once, at session start)

```powershell
# Confirm working branch
git status                                                   # expect: feat/391-clone-device-config-to-gateway-template
git pull origin feat/391-clone-device-config-to-gateway-template

# Activate venv
.venv\Scripts\Activate.ps1

# Capture pre-refactor radon baseline (for diff comparison after each tier)
python -m radon cc src\ -j > specs\198-radon-complexity-decomposition\radon-baseline.json
python -m radon cc src\ -n C > specs\198-radon-complexity-decomposition\radon-baseline.txt
```

---

## Per-File Refactor Loop

Apply this loop for every file in the tier's file list. One commit per file at the end.

1. **Read the file** end-to-end before touching it. Note: which methods exceed CC=10 (cross-check against `radon-baseline.txt`), which public methods are called from outside `src/` (grep), what user-facing strings and log lines exist.
2. **Plan the file's decomposition** using the tier table in [plan.md](plan.md) and the class catalog in [data-model.md](data-model.md).
3. **Create the new submodule directory** (if applicable) with an empty `__init__.py`. Each directory must hold ≤ 5 files (5-Item Rule).
4. **Create the new collaborator class file(s)** with:
   - Inline comment on every executable line (NON-NEGOTIABLE).
   - `logging.info(...)` before / `logging.debug(...)` after every meaningful action (NON-NEGOTIABLE).
   - User-facing strings and log lines preserved verbatim from the original.
   - Max 5 params per method; max 25 lines per method; max 5 blocks per method.
5. **Refactor the original file** into a façade: each public method body becomes a 2–5-line delegation to the collaborator. Preserve public method names + signatures exactly.
6. **Update test imports** if any test referenced a relocated private helper:
   ```powershell
   git grep -n "from src\..* import _" tests/
   ```
   Update import paths in the same commit; do not change test behavior or assertions.
7. **Run per-file gates**:
   ```powershell
   python -m radon cc -n C <changed_files>      # expect: empty
   python -m ruff check <changed_files>
   python -m black --check <changed_files>
   python -m mypy <changed_files>
   python -m pytest tests/guardrails/ -q -k <relevant_keyword>   # smoke
   ```
8. **Commit** with the project commit message format:
   ```powershell
   git add <changed_files>
   git commit -m "refactor(<module>): decompose <Class>.<method> CC=<N> -> <=10

   Extract:
   - <new_class_1> in <new_submodule>/<file_1>.py
   - <new_class_2> in <new_submodule>/<file_2>.py
   Facade <Class> preserves public method names/signatures.
   User-facing strings and log lines preserved verbatim.
   Inline comments + action logging on all new lines.
   "
   ```

Repeat for the next file in the tier.

---

## Per-Tier Push Gate

After all files in a tier are refactored locally, run the full tier-level gate **before pushing**.

### Tier 1 push gate

```powershell
# Worst-offender files must have NO D/E/F-grade blocks
python -m radon cc -n D src\websocket src\ui\tui.py src\ssh\ssh_runner.py src\auth\interactive_session.py src\gateway\gateway_override_analyzer.py
# expect: NO OUTPUT

# Same files must have NO C-grade blocks either
python -m radon cc -n C src\websocket src\ui\tui.py src\ssh\ssh_runner.py src\auth\interactive_session.py src\gateway\gateway_override_analyzer.py
# expect: NO OUTPUT

# Full local quality gates
python -m ruff check .
python -m black --check .
python -m mypy src/ --config-file pyproject.toml
python -m pytest tests/guardrails/ -q

# Manual smoke matrix (5–10 min)
#   1. Launch TUI; arrow-key navigate menus 1 / 60 / 154 / 175; press Enter; confirm rendering identical to baseline.
#   2. Run --menu 102 (websocket show mac-table) on one device; confirm output unchanged.
#   3. Run --menu 175 SSH runner against one host; cancel at confirmation; confirm prompts verbatim.
#   4. Re-launch with multi-org token; confirm MSP/org selection flow unchanged.
#   5. Trigger --menu 154 firmware upgrade; cancel at the 'UPGRADE' confirmation; confirm prompt verbatim.

# Push tier
git push origin feat/391-clone-device-config-to-gateway-template
```

### Tier 2 push gate

```powershell
# Org-wide: NO D/E/F-grade blocks anywhere in src/
python -m radon cc -n D src\
# expect: NO OUTPUT

python -m ruff check .
python -m black --check .
python -m mypy src/ --config-file pyproject.toml
python -m pytest tests/guardrails/ tests/unit/ -q

# Spot-check byte-identical CSV: capture before/after of --menu 27 export and diff
# (the pre-refactor capture should have been taken at start-of-session)

git push origin feat/391-clone-device-config-to-gateway-template
```

### Tier 3 push gate (FINAL — radon must be fully clean)

```powershell
# Final radon: NO C-or-worse blocks anywhere
python -m radon cc src\ -n C
# expect: NO OUTPUT

# Final radon parsed assertion (matches CI gate)
python -m radon cc src\ -j | python -c "import sys, json; data = json.loads(sys.stdin.read()); offenders = [(f, b['name'], b['complexity']) for f, blocks in data.items() for b in blocks if b['complexity'] > 10]; print('All functions within complexity threshold.' if not offenders else offenders); sys.exit(0 if not offenders else 1)"

# Full local CI mirror
python -m ruff check .
python -m black --check .
python -m mypy src/ --config-file pyproject.toml
python -m pytest tests/guardrails/ tests/unit/ tests/integration/ -q
python -m pytest --cov=src --cov-report=term-missing tests/
# Coverage threshold: >= 80%

# Guardrail compliance audit (inline comments + action logging, sampled)
python scripts/audit_inline_comments.py src/              # if helper exists; else manual sample
python scripts/audit_action_logging.py src/               # if helper exists; else manual sample

# Push tier
git push origin feat/391-clone-device-config-to-gateway-template

# After CodeQL completes (~2-3 min, monitor with `gh pr checks 391 --watch`):
gh pr edit 391 --add-label auto-merge
```

---

## Smoke Test Matrix (5-minute manual run before any tier push)

| Menu | What it exercises | Pre / Post check |
|---|---|---|
| TUI launch + arrow nav | `ui/tui.py`, layout, input handling | Same panes render, same items navigable |
| `--menu 102` | WebSocket show mac-table | Same output rows |
| `--menu 27` | wifi clients exporter | Byte-identical CSV (after Tier 2) |
| `--menu 93` | Plotly maps viewer | Figure renders identically (after Tier 2) |
| `--menu 175` (cancelled) | SSH runner interactive | Same prompts, cancellation works |
| `--menu 154` (cancelled) | Firmware upgrade | `'UPGRADE'` confirmation prompt verbatim |
| Multi-org login | MSP/org selector | Same prompts, same org resolution |

---

## Rollback Protocol (if a tier push reveals a regression)

```powershell
# Identify the failing commit via test failure or smoke test discrepancy
git log --oneline -20
git bisect start HEAD <last-known-good-commit>

# Once bisect identifies the offending file commit:
git revert <commit-sha>
git push origin feat/391-clone-device-config-to-gateway-template

# File a sub-issue under the original tier issue:
gh issue create --title "Regression: <Class>.<method> after refactor commit <sha>" \
                --label "bug,regression,scope:<area>" \
                --body "<details + smoke step that failed>"
```

---

## Done When

- [ ] `python -m radon cc src\ -n C` produces no output.
- [ ] `python -m radon cc src\ -j` parsed for `complexity > 10` returns zero offenders.
- [ ] All local gates green: ruff, black, mypy, pytest (guardrails + unit + integration).
- [ ] Coverage on `src/` >= 80%.
- [ ] All smoke matrix items verified pre/post identical.
- [ ] PR #391 CI is fully green.
- [ ] `auto-merge` label added **after** CodeQL completes.
- [ ] PR #391 squash-merged to `main`.
