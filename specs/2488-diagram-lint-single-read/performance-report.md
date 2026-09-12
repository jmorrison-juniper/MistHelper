# Performance report: Diagram reference lint

## 1. Executive summary

**Measured**: The objective was lower end-to-end time for the CI diagram reference lint.
The workload was the production command, `python scripts/lint_diagram_refs.py`.
The retained change replaces a full AST walk with `symtable` plus source line checks.
The timing median changed from 6.901 s to 4.385 s across 41 samples.
This is a 36.45 percent wall-time reduction.
The CPU median changed from 5.344 s to 3.531 s.
This is a 33.92 percent CPU-time reduction.
The change stayed sequential.

## 2. Environment and Python version

**Measured**: The host was Windows 11 on AMD64 with 32 logical cores.
The Python version was CPython 3.13.3.
The benchmark executable was the active `python` on the host path.
The repository root was `C:\Users\jmorrison\misthelper-opt2-diagram-refs`.
The branch was `perf/2488-diagram-lint-single-read`.
The harness asserted that `scripts.lint_diagram_refs` loaded from this worktree.
The raw artifacts used the prefix `opt2_diagram_` in the session artifact directory.

## 3. Benchmark methodology

**Measured**: The production CI job invokes `python scripts/lint_diagram_refs.py`.
The workload scanned `MistHelper.py`, `src`, `documentation\diagrams`, and `README.md` through default arguments.
The expected production result was exit code 0.
The expected message was `OK: 124 references validated across 15 diagram files`.
The harness used 7 warmups and 41 timing samples for baseline and final runs.
It used `time.perf_counter_ns()` for wall time.
It used `time.process_time_ns()` for CPU time.
It counted `Path.read_text()` calls and bytes.
It measured traced Python memory in a separate `tracemalloc` run.
It started `tracemalloc` outside the measured memory loop.
The acceptance rule was at least 5 percent end-to-end improvement with output parity.

## 4. Baseline results

**Measured**: The unmodified script passed `tests\unit\test_lint_diagram_refs.py` before the code change.

| Workload and state | Metric and unit | Median | MAD | Runs and values | Evidence artifact |
| --- | --- | --- | --- | --- | --- |
| Production command | Wall time | 6,900,566,100 ns | 1,531,178,600 ns | 41 samples, 7 warmups | `opt2_diagram_baseline_timing.json` |
| Production command | CPU time | 5,343,750,000 ns | 875,000,000 ns | 41 samples, 7 warmups | `opt2_diagram_baseline_timing.json` |
| Production command | File reads | 490 reads | 0 reads | 41 samples, 7 warmups | `opt2_diagram_baseline_timing.json` |
| Production command | Read bytes | 10,191,622 bytes | 0 bytes | 41 samples, 7 warmups | `opt2_diagram_baseline_timing.json` |
| Production command | Traced peak memory | 19,641,794 bytes | 50,702 bytes | 3 samples | `opt2_diagram_baseline_memory.json` |

## 5. Ranked hotspot list

| Rank and status | File, symbol, and lines | Measured cost and frequency | Expected gain | Risk and maintenance cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1, Measured | `scripts/lint_diagram_refs.py`, `extract_python_symbols`, lines 150-172 before change | 17.601 s cumulative under cProfile across 473 source files | High, because AST walking visited expression nodes that cannot define symbols | Medium, because symbol extraction rules must stay aligned | High |
| 2, Measured | `ast.walk` and child iteration | 8.536 s cumulative under cProfile | High in profiled runs, lower in unprofiled runs | Low if syntax checks stay active | Medium |
| 3, Measured | File reads | 490 reads per run | Low for this change, because each file was already read one time | Low | High |

## 6. Recommended optimizations

**Measured**: Replace full AST walking with `symtable.symtable()` and symbol table traversal.
The root cause was repeated traversal of expression nodes that cannot introduce class or function names.
The safe change keeps the parser step, then reads symbol table children.
The source line check excludes asynchronous function names, as the old AST rule did.
The proposed complexity stays linear in the number of definitions and symbol table children.

**Rejected**: A custom AST statement traversal reduced profiled calls but did not reduce wall time enough.
One run changed wall time by plus 12.11 percent and CPU time by minus 14.33 percent.
This did not give a clear wall-time win.

**Rejected**: A token-only scan was faster in concept but risked syntax behavior.
A token scan with parser validation was slower on the real tree.

## 7. Implemented changes

| Field | Required content |
| --- | --- |
| Change ID and location | `diagram-symbol-table`, `scripts/lint_diagram_refs.py`, `extract_python_symbols` and helpers |
| Evidence | `opt2_diagram_baseline_timing.json`, `opt2_diagram_final_timing.json`, `opt2_diagram_baseline_capture.json`, `opt2_diagram_final_capture.json` |
| Root cause | The old path parsed each file to AST and walked every node. Most nodes could not add a symbol. |
| Change | Use `symtable.symtable()` for syntax checks and symbol tables. Add source line checks for class and sync function names. |
| Before result | Wall median 6,900,566,100 ns, MAD 1,531,178,600 ns, 41 samples. |
| After result | Wall median 4,385,129,900 ns, MAD 1,311,086,600 ns, 41 samples. |
| Percentage change | `100 * (after - before) / before = -36.45%` for wall time. |
| Memory change | Traced peak memory changed from 19,641,794 bytes to 14,620,753 bytes. This is a reduction of 5,021,041 bytes. |
| Test coverage | Added tests for nested definitions, asynchronous omission, and definition words in strings and comments. |
| Risks | The helper reads source lines to exclude asynchronous functions. Tests cover this rule. |
| Confidence level | High, because production output and exit code match exactly. |
| Retention decision | Retained. The end-to-end wall-time reduction exceeds 5 percent and clears the measured noise. |

## 8. Before-and-after measurements

| Change and workload | Metric and unit | Before median and spread | After median and spread | Sample counts | Signed change | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `diagram-symbol-table`, production command | Wall time | 6,900,566,100 ns, MAD 1,531,178,600 ns | 4,385,129,900 ns, MAD 1,311,086,600 ns | 41 before, 41 after | -36.45 percent | Retained |
| `diagram-symbol-table`, production command | CPU time | 5,343,750,000 ns, MAD 875,000,000 ns | 3,531,250,000 ns, MAD 812,500,000 ns | 41 before, 41 after | -33.92 percent | Retained |
| `diagram-symbol-table`, production command | File reads | 490 reads, MAD 0 | 490 reads, MAD 0 | 41 before, 41 after | 0.00 percent | Neutral |
| `diagram-symbol-table`, production command | Read bytes | 10,191,622 bytes, MAD 0 | 10,191,622 bytes, MAD 0 | 41 before, 41 after | 0.00 percent | Neutral |

## 9. Memory impact

**Measured**: The memory metric was traced Python peak bytes from `tracemalloc`.
Baseline peak memory was 19,641,794 bytes with a 50,702 byte MAD across 3 samples.
Final peak memory was 14,620,753 bytes with a 62,104 byte MAD across 5 samples.
The peak traced memory changed by -5,021,041 bytes.
This is a 25.56 percent reduction.
The live traced current delta changed from 57,992 bytes to 59,067 bytes.
This is a 1,075 byte increase.
No cache was added.

## 10. Correctness and regression validation

| Check | Command or test | Actual result | Limitation or artifact |
| --- | --- | --- | --- |
| Unit tests | `rtk python -m pytest tests\unit\test_lint_diagram_refs.py -q` | 31 passed | Local CPython 3.13.3 only |
| Syntax | `rtk python -m py_compile scripts\lint_diagram_refs.py tests\unit\test_lint_diagram_refs.py` | Passed | No output on success |
| Ruff | `rtk python -m ruff check scripts\lint_diagram_refs.py tests\unit\test_lint_diagram_refs.py` | Passed | Explicit script check |
| Black | `rtk python -m black --check scripts\lint_diagram_refs.py tests\unit\test_lint_diagram_refs.py` | Passed | Explicit script check |
| pydocstyle | `rtk python -m pydocstyle scripts\lint_diagram_refs.py tests\unit\test_lint_diagram_refs.py` | Passed | No output on success |
| Bandit | `rtk python -m bandit -q scripts\lint_diagram_refs.py` | Passed | No output on success |
| Diff whitespace | `rtk git diff --check` | Passed | No output on success |
| Production output | Harness capture before and after | Exit code, stdout, and stderr matched exactly | `opt2_diagram_baseline_capture.json`, `opt2_diagram_final_capture.json` |
| Symbol parity | Local comparison script against the prior AST rule | 8,693 old symbols and 8,693 new symbols matched | Real repository tree only |

## 11. Rejected ideas and why they were rejected

| Idea and location | Evidence | Reason for rejection | Reverted or never implemented |
| --- | --- | --- | --- |
| Statement-only AST traversal in `extract_python_symbols` | `opt2_diagram_candidate3_timing.json` | Wall time did not clear the threshold in the final form. | Reverted by replacement |
| Token scan with parser validation | Local timing showed 9.513 s for symbol extraction | The token scan added cost and raised behavior risk. | Reverted by replacement |
| Skip source files after all diagram symbols resolve | Not measured | This would change syntax error logging for later files. | Never implemented |

## 12. Remaining opportunities

| Opportunity and status | Missing evidence or blocker | Exact next benchmark | Expected value and risk |
| --- | --- | --- | --- |
| Stale-reference hotspot, Hypothesis | The production tree has no stale references, so edit distance cost is cold. | Add a safe fixture with known stale references and compare full messages and order. | It can reduce failure-path time, but it risks report ordering. |
| Markdown identifier order, Hypothesis | The current code converts identifiers through `set`. | Use a fixture with duplicate stale references and compare ordered output. | It can improve determinism, but it can change message order. |
| File read reduction, Blocked | The current production path already reads each required file one time. | Use filesystem tracing to confirm no hidden repeated reads outside `Path.read_text()`. | Low expected value. |
