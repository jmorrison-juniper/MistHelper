# Refactor candidates: MistHelper.py

- Entrypoint: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`
- Module graph size: 261 first-party files
- Definitions analyzed: 2
- LOC saveable (unused + single-use): 0
- Category counts: unused=0, single-use=0, low-use=0, hot=1, skipped=1

## How to read this report

Work the report **top-down inside each category**, then move to the next category:

1. **Unused** -- zero references. Delete outright; no move, no callsite rewrite. Highest ROI per PR.
2. **Single-use** -- exactly one caller. Move alongside that caller (or into a new `/src` module when the entrypoint is the sole caller). One PR covers move + rewrite.
3. **Low-use** -- 2-3 callers. Evaluate before moving: worth it only when all callers can be rewritten in one bounded PR cluster.
4. **Hot** -- 4+ callers. Leave in place until dependencies decouple. Listed for completeness only.
5. **Skipped** -- pinned by bootstrap/module-load ordering (e.g. `GlobalImportManager`). DO NOT extract; the tool cannot detect load-order dependencies, so these are curated by hand via the `--skip NAME` CLI flag.

Within each bucket, candidates are sorted by **line_count descending** so the biggest LOC wins surface first. The `LOC saveable` headline in the metadata block sums unused + single-use lines only -- that number is your extraction budget for this pass.

Reference sites are grouped **per file** so each candidate maps cleanly to one PR per reference-holding file (move + rewrite in the same PR). When multiple single-use candidates share the same dominant caller (see `Suggested class`), bundle them into one PR that lands them in the same class body.

## SpecKit non-negotiables

1. **No wrapper shims**: do NOT create `def old(...): return NewClass().new(...)` or thin re-export modules. Move the code into a semantic class body and delete the old symbol.
2. **Rewrite every callsite**: for each candidate below, produce one PR per reference-holding file cluster. Every listed `file:lineno` must be updated in the same PR as the move.
3. **Decompose while moving**: if a candidate lists `guideline_flags`, do NOT lift-and-shift. Split into <=25-line methods with <=5 params, add inline comments on every executable line, and add `logging.info/debug` before/after every operation.
4. **Landing target is a class body**: `Suggested class` names the destination. Prefer an existing class (`WebSocketManager`, `FirmwareManager`, `SFPTransceiverDataProcessor`, `EnhancedSSHRunner`, etc.) when one already lives in the target module; otherwise create the proposed new class rather than adding a bare module-level function.
5. **ASCII-only logs, `safe_input()`, `pathlib.Path`**: any candidate flagged for non-ASCII literals, raw `input()`, or hardcoded separators must be cleaned up during the move.

## Summary

| Name | Kind | Lines | Refs | Category | Suggested class | Flags |
|---|---|---:|---:|---|---|---|
| `GlobalImportManager` | class | 1003 | 1 | skipped |  | oversize_25_lines |
| `menu_actions` | assignment | 887 | 17 | hot |  | oversize_25_lines,missing_inline_comments,missing_action_logging |

## Hot (1)

### `menu_actions` (assignment, 887 lines)

- Def site: line 3406-4292
- References: 17
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: Widely used; leave in place until dependencies decouple
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
  - [ ] missing_inline_comments
  - [ ] missing_action_logging
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 3406, 4327, 4328, 4337, 4457, 4457, 4499, 4555, 4600, 5094, 5098, 5143, 5143, 5170, 5170, 5173
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\troubleshooting\interactive_test_runner.py`: lines 43

## Skipped (1)

### `GlobalImportManager` (class, 1003 lines)

- Def site: line 893-1895
- References: 1
- Suggested class: _n/a_
- Suggested module: _n/a_
- Rationale: PINNED: `GlobalImportManager` must remain in the entrypoint because of module-load / bootstrap ordering; static analysis cannot detect this but moving it would break import wiring. Do NOT extract.
- Guideline flags (address during the move):
  - [ ] oversize_25_lines
- Reference sites (one PR cluster per file):
  - `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\MistHelper.py`: lines 1940

## Limitations

- `getattr(module, "name")` string-form lookups are not detected.
- Class-registration decorators (`@registry.register("foo")`) with literal-string wiring are invisible to static analysis.
- Runtime `importlib` / plugin discovery is not followed.
- Because `src/` files rarely `from MistHelper import ...`, external ref counts are near zero by design; the tool primarily surfaces intra-entrypoint single-use symbols that can be moved alongside their sole caller into `src/`.
- Constants inside `if TYPE_CHECKING:` or other conditional module-scope blocks are skipped.
