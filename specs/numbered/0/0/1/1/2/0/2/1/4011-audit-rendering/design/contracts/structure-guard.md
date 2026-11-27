# Contract: Structure guard

This contract defines the counting rule, the expected counts, the retired-path scan, and the failure messages of `tests/guardrails/test_audit_rendering_structure.py`.

## Scope

The guard reads the tracked files under `src/mist/access/audit`. It reads them with `git ls-files -z -- src/mist/access/audit`. The guard does not read the working tree, so cache folders and untracked files do not count.

## Counting rule

- A direct module is a tracked file that ends with `.py` in the directory. The file `__init__.py` does not count.
- A direct child directory counts when it holds at least one tracked Python file at any depth.
- The guard reports the child count of each directory that holds a tracked Python file.

This rule matches the counting rule of the nested guard (`_child_count` in row RC-31).

## Expected counts

| Directory | Expected children | Children that the count holds |
|-----------|-------------------|-------------------------------|
| `src/mist/access/audit` | 5 | Modules `analyzer.py`, `audit_analysis_ops.py`, `filter.py`, and `time_parser.py`, and directory `rendering` |
| `src/mist/access/audit/rendering` | 2 | Module `renderer.py` and directory `helpers` |
| `src/mist/access/audit/rendering/helpers` | 5 | Modules `_renderer_delta.py`, `_renderer_format.py`, `_renderer_html.py`, `_renderer_mermaid.py`, and `_renderer_time.py` |
| `src/mist/access/audit/rendering/clusters` | 0 | The directory is absent from the tracked tree |

## Retired-path scan

- The scan searches for the dotted and slash forms of each retired path in `python-imports.md`. It also searches for `rendering.clusters` and `rendering/clusters`.
- The scan reads each tracked file as UTF-8. A file that fails to decode is skipped and counted.
- The scan allows these files to name a retired path:
  - `tests/guardrails/test_audit_rendering_structure.py`, because it holds the search patterns.
  - `tests/guardrails/test_src_public_symbol_preservation.py`, because its six rows name the baseline paths of the 3824 layout.
  - `tests/unit/marvis/mist/access/audit/test_renderer_structure_issue_3824.py`, because its retired-import list names the retired paths on purpose.
  - Each tracked file under `specs/`, because the historical records keep their original text.

## Failure messages

Each message names the measured values. Each message uses ASCII only.

- Count mismatch: the message names the directory, the expected count, the measured count, and the number of tracked files that the guard examined.
- Unreadable root: the message names the audit root and states that the guard examined 0 files.
- Retired path found: the message names the number of active files, lists each file, and states the number of tracked files that the guard examined.
- Pass: the message states the number of tracked files that the guard examined, and it prints the three counts 5, 2, and 5.

## Failure proofs

Each proof uses a fixture in the pytest temporary folder. The proof passes when the guard raises the expected message.

- TS-03: A fixture helpers package with six direct modules fails the count rule.
- TS-04: A fixture with a missing audit root fails with the unreadable message.
- TS-05: A fixture file that names a retired path fails the retired-path scan.
