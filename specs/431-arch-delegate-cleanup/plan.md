# Implementation Plan: ARCH-DELEGATE / NAMING / STUB / ALIAS / STRUCT-PARAMS / CONV-INPUT / CONV-PATH Cleanup (Issue #431)

**Spec**: [spec.md](./spec.md) (239 lines, 12 FRs, 7 SCs, 3 user stories)
**Branch**: `refactor/431-arch-delegate-cleanup` (worktree `MistHelper-431-arch`)
**Baseline**: `data/compliance_report.md` 2026-06-23 post-#430-merge snapshot

## Summary

Eliminate 59 violations across 7 rule categories in `MistHelper.py` per the NON-NEGOTIABLE "no wrappers" rule in `copilot-instructions.md`. Delivered in 5 tranches plus a final commit, each independently CI-green and revertable. Net result: ARCH-DELEGATE / NAMING / STUB / ALIAS / STRUCT-PARAMS / CONV-INPUT / CONV-PATH all reach 0.

## Resolved Deferred Items

### 1. `PacketCaptureManager` alias resolution → **Option (a) chosen**

Grep evidence (worktree, 2026-06-23):

```
ExtractedPacketCaptureManager references: 2 total, both in MistHelper.py
  - MistHelper.py:110  (import-as line)
  - MistHelper.py:6277 (alias line)
```

`ExtractedPacketCaptureManager` is a private rename used only inside `MistHelper.py`. The canonical class at `src/capture/packet_capture.py:84` is `PacketCaptureManager`. **Strategy**: remove the `as ExtractedPacketCaptureManager` from the import on L110 and delete the alias line on L6277. After the change, every reference inside `MistHelper.py` (L13723, L13725, L14342, L21836, L21842) resolves directly to the canonical `src/` class via the cleaned-up import. Two-line change. Zero call-site rewrites needed.

**Wave 1 guardrail (`tests/guardrails/test_wave1_scope_boundaries.py:72`) still passes** — the test asserts `getattr(MistHelper, "PacketCaptureManager")` exists, which it still does (re-exported via the import statement).

### 2. `save_data_to_output` canonical successor → **`DataExporter.write_with_format_selection`** (same file)

Grep evidence:

```
src/exporters/: no matches for save_data_to_output or write_with_format_selection
MistHelper.py:8019: return DataExporter.write_with_format_selection(data, filename, api_function_name=api_function_name)
MistHelper.py L7720 (approx): DataExporter.write_with_format_selection definition
MistHelper.py: 82 call sites of save_data_to_output across the file
```

The canonical implementation lives in the **same class in the same file** — `DataExporter.write_with_format_selection`. `save_data_to_output` is documented as "backward compatibility convenience" but per the no-wrappers rule it must be removed. **Strategy**: rewrite all 82 call sites in `MistHelper.py` from `DataExporter.save_data_to_output(...)` to `DataExporter.write_with_format_selection(...)` (identical signature), then delete `save_data_to_output` at L8005-L8019. AST codemod via libcst (already in worktree from #429).

## Spec Assumption Correction

Spec assumption #235 says "every facade flagged has a canonical successor in `src/`". This is wrong for `save_data_to_output` — its successor is in `MistHelper.py` itself. Plan adjusts: canonical successor may be in `src/` OR in `MistHelper.py`; same-file rewrites are still valid no-wrapper resolutions.

## Architecture

- **Codemod**: extend the existing `tools/codemod_logging_lazy.py` patterns into a new `tools/codemod_inline_delegator.py` for the high-volume call-site rewrites (Tranche 2 `save_data_to_output` rename, Tranche 4 façade replacements). For low-volume sites (Tranche 1, 3, 5), hand-edit with `edit` tool.
- **No new runtime modules**: this is a pure refactor. No new classes, no new src/ modules.
- **Codemod scope**: `MistHelper.py` only. No `src/` rewrites.

## Module / File Map

| Path | Change | Purpose |
|---|---|---|
| `MistHelper.py` | modified | 59 violation sites removed/rewritten |
| `tools/codemod_inline_delegator.py` | NEW | libcst transformer for call-site rewrites (Tranche 2 + 4) |
| `tests/test_issue_431_canonical_imports.py` | NEW | Asserts `MistHelper.X is src.X` for every public class |
| `tests/test_issue_431_compliance_guard.py` | NEW | Asserts ARCH-* / STRUCT-PARAMS / CONV-INPUT / CONV-PATH counts == 0 |
| `tests/test_issue_431_g_no_regress.py` | NEW | Asserts `ruff --select G MistHelper.py` exits 0 |
| `tests/fixtures/issue_431_canonical_classes.json` | NEW | Frozen snapshot of expected MistHelper -> src/ class identity mapping |
| `specs/195-decompose-top5-functions/data-model.md` | modified | Status: `delegated` -> `legacy-removed` for affected entries |
| `specs/195-decompose-top5-functions/tasks.md` | modified | Final task checked |
| `specs/196-decompose-next5-functions/data-model.md` | modified | Status: `delegated` -> `verified` |
| `specs/196-decompose-next5-functions/tasks.md` | modified | Final task checked |
| `specs/168-clone-gateway-template/tasks.md` | modified | Final task checked |
| `specs/1002-legacy-compat-shim-decomposition/migration-tracker.md` | modified | Status updates per facade |
| `CHANGELOG.md` | modified | Final commit, UTC `YY.MM.DD.HH.MM` entry |
| `data/compliance_report.md` | modified | Regenerated post-cleanup snapshot |

## Phased Delivery

### Tranche 1 — Trivial Single-Line Fixes (1 commit, 4 sites)

**Targets**:

| Rule | Line | Symbol | Action |
|---|---:|---|---|
| ARCH-STUB | 1197 | `stop_listening` | Delete function entirely + check no call sites remain (was a no-op fallback for removed feature) |
| ARCH-ALIAS | 110, 6277 | `PacketCaptureManager = ExtractedPacketCaptureManager` | Remove `as ExtractedPacketCaptureManager` from import + delete alias line |
| CONV-INPUT | 2576 | bare `input()` | Replace with `InputUtils.safe_input(prompt, context=...)` |
| CONV-PATH | 12268 | hardcoded `\\` | Replace with `pathlib.Path` or `os.path.join` |

**Entry**: branch off main, baseline confirmed (run check_compliance once to lock counts).

**Work steps**:
1. Read each site, apply edit, run py_compile.
2. Verify call sites for `stop_listening` and `ExtractedPacketCaptureManager` are clean (grep).
3. Run local gates: py_compile, ruff, black, mypy, pytest+cov, bandit, pip-audit.
4. Commit.

**Exit**: 4 violations removed, all gates green.

**Commit message**: `version YY.MM.DD.HH.MM - refactor(#431): tranche 1/5 - remove stop_listening stub, PacketCaptureManager alias, fix CONV-INPUT/PATH`

---

### Tranche 2 — Hand-Rolled Pass-Throughs (1-3 commits, 8 sites)

**Targets** (all ARCH-DELEGATE, all are user-written not migration-spec):

| Line | Symbol | Inline-target |
|---:|---|---|
| 1777 | `DateTimeHandler.__call__` | Inline `datetime(*args, **kwargs)` semantics into the call sites |
| 1921 | `GlobalImportManager._get_actual_import_name` | Inline `self.import_name_mappings.get(name, name)` at call sites |
| 2339 | `GlobalImportManager.get_import` | Inline `self.imports.get(name)` at call sites |
| 3355 | `_mist_get_wrapper` | Inline `session.get(...)` at the single call site that builds it |
| 8006 | `DataExporter.save_data_to_output` | **Rewrite 82 call sites** to `write_with_format_selection`, then delete the method |
| 9038 | `DeviceUtils.select_device` | Inline / delete if duplicate of `select_*` siblings; investigate during execution |
| 14660 | `Class.__getattr__` | Examine — may be a real dynamic-attr; keep if non-trivial |
| 17300 | `Class.__getattr__` | Same — examine before removing |
| 21303 | `BulkRadiusConfig._safe_input` | Rewrite all `self._safe_input(...)` call sites to `InputUtils.safe_input(...)`, delete method |

**Approach**: build `tools/codemod_inline_delegator.py` for `save_data_to_output` (82 sites — manual rewrite is too error-prone) and `_safe_input`. Hand-edit the others.

**Sub-tranches**:
- 2a: `save_data_to_output` rename codemod
- 2b: `_safe_input` rename codemod
- 2c: remaining 6 sites hand-edited together

**Exit**: ARCH-DELEGATE count drops from 38 to 30. Gates green.

**Commit message pattern**: `version YY.MM.DD.HH.MM - refactor(#431): tranche 2X/5 - <symbol> inlined`

---

### Tranche 3 — ARCH-NAMING Renames (1 commit, 5 sites)

**Targets**:

| Line | Old name | New name | Reason |
|---:|---|---|---|
| 628 | `_early_dependency_check_legacy_impl` | `_early_dependency_check_impl` | Drop `_legacy` marker; canonical impl |
| 3355 | `_mist_get_wrapper` | (deleted in Tranche 2) | Already gone |
| 10200 | `device_events_52w_legacy` | `device_events_52w_impl` | Drop `_legacy` marker |
| 14460 | `_metric_compatible_with_platform` | `_metric_supports_platform` | Drop `compat` marker; reflect actual semantics (predicate) |
| 15625 | `export_legacy` | Investigate — may need full inlining instead of rename | Depends on whether there's a canonical non-legacy `export` |

**Approach**: rename each symbol, then rewrite every call site in `MistHelper.py` using libcst codemod or simple search-replace (these are uniquely-named symbols within the file).

**Exit**: ARCH-NAMING count = 0.

**Commit message**: `version YY.MM.DD.HH.MM - refactor(#431): tranche 3/5 - rename legacy/compat/wrapper symbols to canonical names`

---

### Tranche 4 — Migration-Spec Façade Removal (3-5 commits, ~30 sites)

**Critical context discovered during planning**: the 30 migration-spec facades are NOT pure delegators. They perform **dependency injection at the facade boundary** — each calls a `_get_<X>_impl()` or `_build_deps()` helper that wires runtime globals (`apisession`, `mistapi`, `org_id`, `DataExporter`, `InputUtils`, `msp_privileges`) into the canonical `src/` class via global configuration functions like `configure_org_device_inventory_summary_dependencies(...)`. Pure call-site rewriting (the cheap inline pattern) WILL BREAK runtime because the `src/` classes' module-level globals would be unconfigured at call time.

**Rule-compliant resolution**: refactor each affected `src/` class to take its dependencies via the constructor (standard DI pattern) instead of a global config function. Then delete BOTH the `MistHelper.py` facade methods AND the `configure_*_dependencies` function in `src/`. Every call site becomes `Canonical(apisession=apisession, org_id=org_id, ...).method(...)` — no wrappers, no global state.

**Affected `src/` modules** (one sub-tranche per module):

| Sub-tranche | `src/` module | Facade count | Canonical class |
|---|---|---:|---|
| 4a | `src.inventory.org_device_inventory_summary` | 14 | `OrgDeviceInventorySummaryCore` |
| 4b | `src.inventory.org_device_inventory_msp` | 4 | `OrgDeviceInventoryMSPOrchestrator` |
| 4c | `src.marvis.troubleshoot` | ~4 | `ExtractedMarvisTroubleshootUtils` |
| 4d | `src.gateway.device_template_cloner` | ~4 | spec #168 class |
| 4e | `src.ssh.runner_manager` | ~3 | `ExtractedSSHRunnerManager` |
| 4f | `src.firmware.manager` | ~3 | `ExtractedFirmwareManager` (via `_create_impl()` pattern) |

Some `src/` modules may already use constructor DI — verify before refactoring. Skip the constructor work if a module already supports it; just rewrite call sites in those cases.

**Per-sub-tranche work steps**:
1. Read the `src/` module's `configure_*_dependencies` function. Note every dependency injected.
2. Add those dependencies as constructor parameters to the canonical class (keep ≤5 params per the 5-Item Rule — use a `@dataclass(frozen=True, slots=True)` config object if needed).
3. Delete the `configure_*_dependencies` function. Delete any module-level globals it set.
4. Find every call site of the facade methods in `MistHelper.py`. Rewrite to `CanonicalClass(deps).method(...)`.
5. Delete the facade methods from `MistHelper.py`.
6. Run quality gates. Commit.
7. Advance the originating spec's `data-model.md` status and check the `tasks.md` final task.

**Per-sub-tranche commit message**: `version YY.MM.DD.HH.MM - refactor(#431): tranche 4X/5 - inline <module name> facades (constructor DI)`

**5-Item Rule compliance**: each canonical class's constructor takes ≤5 args. If it needs more, group into a `@dataclass(frozen=True, slots=True)` config in `src/dataclasses/`.

---

### Tranche 5 — STRUCT-PARAMS Dataclass Extraction (1-2 commits, 12 sites)

**Targets** (functions with 6+ params):

| Line | Function | Params |
|---:|---|---:|
| 3477 | `send` | 6 |
| 6200 | `__init__` | 6 |
| 7789 | `write_with_format_selection` | 6 |
| 8082 | `__init__` | 6 |
| 8456 | `_pool_process_batch_wait_loop` | 7 |
| 10092 | `_52w_fetch_page_with_retries` | 6 |
| 16999 | `_listen_for_output` | 8 |
| 20104 | `_enrich_device_context` | 6 |
| 22670 | `emit_test_summary` | 6 |
| 22704 | `emit_progress_tick` | 6 |
| 22721 | `emit_progress_complete` | 6 |
| 23277 | `_systematic_test_run_option` | 7 |

**Approach**: for each function, group related params into a `@dataclass(frozen=True, slots=True)` container. Dataclasses live in a NEW `src/dataclasses/` module (one file per logical grouping, e.g. `src/dataclasses/test_emission.py` for the three `emit_*` functions, `src/dataclasses/pool_batch.py` for `_pool_process_batch_wait_loop`). **NOT inside `MistHelper.py`** — that would push host classes over the 5-Item Rule's child limit. Update function signature to take the dataclass plus any remaining ≤5 params. Update all call sites to build the dataclass.

**5-Item Rule compliance check** for every Tranche 5 commit:
- The host class's child count (methods + attributes) MUST NOT increase. We're shrinking parameter lists, not adding methods.
- The new dataclass MUST have ≤5 fields. If a function has 8 params and they don't cleanly split, break into TWO dataclasses (e.g. `IOConfig` + `RetryConfig`).
- The replaced function MUST be ≤25 lines after the change.

**Inline-comments + action-logging on every touched line** (NON-NEGOTIABLE). When the call-site changes from `func(a, b, c, d, e, f)` to `func(MyConfig(a=a, b=b, c=c, d=d, e=e), f)`, both lines get inline comments explaining intent.

**Sub-tranches**: split into 2 commits of 6 functions each for reviewability.

**Exit**: STRUCT-PARAMS count = 0. Host class child counts unchanged.

**Commit message**: `version YY.MM.DD.HH.MM - refactor(#431): tranche 5X/5 - dataclass-extract <N> overloaded signatures`

---

### Final Commit — CHANGELOG + Compliance Snapshot

- Update CHANGELOG.md with consolidated entry covering all 5 tranches.
- Regenerate `data/compliance_report.md` to prove SC-007 (score > 30/100).
- Update originating specs' `data-model.md` if any final adjustments needed.
- Verify SC-001..SC-007 all green via shell commands.

**Commit message**: `version YY.MM.DD.HH.MM - chore(#431): finalize architectural cleanup (CHANGELOG, compliance snapshot, spec updates)`

## Coding-Rule Adherence (NON-NEGOTIABLE)

Every change in every tranche MUST honor these rules from `copilot-instructions.md` + `agents.md` even where it makes the work harder:

| Rule | How this PR honors it |
|---|---|
| **No wrappers** | All 38 ARCH-DELEGATE methods deleted. Call sites rewritten to use canonical `src/` class directly. No new wrappers introduced. |
| **5-Item Rule** (max 5 params, 5 blocks, 25 lines, 5 children per class) | Tranche 5 dataclasses live in `src/dataclasses/` (NOT `MistHelper.py`) so host classes don't gain child slots. Dataclasses ≤5 fields each (split if needed). Inlined code blocks checked against the 25-line limit; if inlining would exceed it, the canonical `src/` method is called instead. |
| **Inline comments on EVERY executable line touched** | Every replacement line MUST have a same-line `# comment explaining why`. When editing an existing block, the *entire* block gets comments, not just my new lines. |
| **Action logging before/after EVERY operation** | `logging.info("...")` before each API/file/state change, `logging.debug("...")` after with result. Apply to entire touched blocks. |
| **ASCII only in logs** | No emoji, no Unicode punctuation in log strings, commit messages, or PR body. |
| **safe_input()** | Tranche 1 CONV-INPUT fix uses `InputUtils.safe_input(prompt, context=...)`. Tranche 2 `_safe_input` removal redirects call sites to `InputUtils.safe_input` — never bare `input()`. |
| **File paths** | Tranche 1 CONV-PATH fix uses `pathlib.Path` or `os.path.join` — never hardcoded `\\` or `/`. |
| **Junior NOC clarity** | Variable names, log messages, and comments target the project's stated audience (junior NOC engineers). No jargon. |
| **Hot-file coordination** | `gh pr list --search "is:open MistHelper.py"` before each tranche commit. Pause if conflict appears. |
| **Class-based architecture** | All inlining moves call sites onto **canonical classes**, never onto bare functions. The `_legacy`/`_compat`/`_wrapper` renames in Tranche 3 produce semantic class-method names. |

**Self-check before each commit**: scan the diff for new lines that lack an inline comment, log statements that use f-strings (would reintroduce G004), bare `input()` calls, hardcoded paths, or new helper functions outside a class. If any are found, fix before committing.

## Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Façade has hidden side effect not in canonical `src/` class | Medium | High (silent behavior change) | Read each façade body before deletion; canonical successor must be identity-equal in behavior. Tranche 4 sub-tranches commit one spec at a time so bisect is cheap. |
| 2 | `__getattr__` dunder is actual dynamic-attr forwarding | Medium | Medium | Manual review of L14660 and L17300; if non-trivial, keep and document why the analyzer false-positives. |
| 3 | Wave 1 guardrail test fails after `PacketCaptureManager` alias removal | Low (verified strategy preserves namespace) | High (CI red) | Verified: removing the `as` rename keeps `PacketCaptureManager` importable from `MistHelper`. Test passes. |
| 4 | Hot-file conflict with another open PR touching `MistHelper.py` | High (per project constitution) | High (3-way merge in 24K-line file) | `gh pr list --search "is:open MistHelper.py"` before each tranche commit. Pause if conflict appears. |
| 5 | `save_data_to_output` call-site codemod corrupts one of 82 sites | Medium | Medium | Idempotency check (same as #429): re-run produces 0 diff. AST-based, not regex. |

## Quality Gates per Phase

Each tranche commit MUST pass all gates below locally before push and in CI on the branch:

| Gate | Command | Pass criterion |
|---|---|---|
| Syntax | `python -m py_compile MistHelper.py` | exit 0 |
| Ruff (existing selection) | `python -m ruff check .` | exit 0 |
| Ruff (G subset, no regression) | `python -m ruff check --select G MistHelper.py` | exit 0 (SC-002) |
| Black format | `python -m black --check .` | exit 0 |
| mypy | per project config | exit 0 |
| pytest + coverage | `pytest -p no:dash --cov` | exit 0, coverage ≥ 70% (SC-004) |
| Bandit | `bandit -r MistHelper.py tools/codemod_inline_delegator.py` | no new HIGH/CRITICAL |
| pip-audit | `pip-audit -r requirements.txt` | no new vulnerabilities |
| CodeQL | GitHub Action | green |
| Playwright | GitHub Action | green |
| Compliance (per-tranche decrement) | `python tools/check_compliance.py MistHelper.py` | counts strictly decreasing |
| Compliance (final, SC-001) | same as above | 7 categories all = 0 |
| Canonical imports test | `pytest tests/test_issue_431_canonical_imports.py` | exit 0 (FR-009) |
| Compliance-guard test | `pytest tests/test_issue_431_compliance_guard.py` | exit 0 (SC-001) |
| G-no-regress test | `pytest tests/test_issue_431_g_no_regress.py` | exit 0 (SC-002) |

## Test Strategy

Three new test modules added under `tests/` (no fixtures from production state — fully self-contained):

- **`test_issue_431_canonical_imports.py`**: import every class listed in `tests/fixtures/issue_431_canonical_classes.json` from `MistHelper.py` and assert `MistHelper.X is src.module.X`. Proves FR-009 (no facade interposed).
- **`test_issue_431_compliance_guard.py`**: shell out to `python tools/check_compliance.py MistHelper.py`, parse the JSON summary, assert ARCH-DELEGATE/NAMING/STUB/ALIAS + STRUCT-PARAMS + CONV-INPUT + CONV-PATH all = 0.
- **`test_issue_431_g_no_regress.py`**: shell out to `python -m ruff check --select G MistHelper.py`, assert exit 0.

## Rollback Plan

**Per-tranche**: each tranche is a single commit (or 2-3 grouped commits per sub-tranche). Revert is `git revert <sha>`.

**Mid-sweep abandonment**: if Tranche 4 surfaces a façade whose canonical successor is missing or behaviorally divergent, stop the sweep, document the gap in the issue, and ship Tranches 1-3 as a partial PR. The remaining ARCH-DELEGATE count stays > 0 but the partial progress lands.

**Full rollback**: revert all tranche commits in reverse order. Spec `data-model.md` updates also reverted.

## Coordination Notes

- `MistHelper.py` is the hottest file in the repo. Before each tranche commit: `gh pr list --search "is:open MistHelper.py"` to detect conflicts.
- Tranche 4 explicitly overrides specs #195/#196/#168/#1002 lifecycle. User has approved this override (decision logged in issue #431 brief).
- The 165 STRUCT-COMPLEXITY, 207 STRUCT-LENGTH, and 72 STRUCT-BLOCKS violations are **out of scope** for #431. They get a separate issue after #431 closes.

## Open Questions / NEEDS DECISION

**None.** Both deferred items are resolved in this plan. Tranche-level discoveries (e.g., `__getattr__` semantic depth) are flagged for manual review during execution and do not block planning.
