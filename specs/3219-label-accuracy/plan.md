# Implementation Plan: Accurate operation labels

**Branch**: `fix/3219-label-accuracy` | **Date**: 2026-09-23 | **Spec**: [spec.md](./spec.md)

## Root cause

Each chooser label holds a count that a person typed. `CountExporter._SITE_OPS` grew to 33 entries, and the label of menu 236 kept 32. No test compared the two. The tracking numbers came from the pull requests that added the rows, and they moved into the labels.

## Design

1. Edit the 15 labels in `MistHelper.py` and in `web_portal/menu_registry.py`. Join the three split titles of menus 265-267 into one string each.
2. Regenerate `documentation/menu_reference.md` and `documentation/wiki/Menu-Reference.md` with `scripts/generate_menu_wiki.py`. The drift job runs the same script.
3. Add `tests/unit/web_portal/test_portal_label_accuracy.py`. It reads both label sources, the command-line source through `ast` so the test never imports `MistHelper.py`.

## Risks

| Risk | Control |
| - | - |
| A label source is empty and the guards pass over nothing | `test_both_label_sources_were_read` requires 200 labels in each source. |
| A new chooser label promises a count with no table | `test_every_label_that_promises_a_count_has_a_known_table` fails. |
| `MistHelper.py` is a hot file | The change edits 15 title strings only, and it touches no logic. |
