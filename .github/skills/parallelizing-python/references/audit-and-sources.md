# Audit and sources

This guide records the audit of the source document
`documentation/python-parallelism-matrix.md` against the primary Python
documentation. It lists what the audit confirmed, what it corrected, and what
it added.

Audit date: 2026-09-09.

## Primary sources

| Source | Used for |
| - | - |
| [What is new in Python 3.13](https://docs.python.org/3/whatsnew/3.13.html) | Free-threaded build status, the just-in-time compiler, `os.process_cpu_count`, `queue.ShutDown`, default worker counts |
| [What is new in Python 3.14](https://docs.python.org/3/whatsnew/3.14.html) | Subinterpreters, `InterpreterPoolExecutor`, the start method change, free-threading support, new pool methods |
| [The multiprocessing module](https://docs.python.org/3/library/multiprocessing.html) | Start methods, the resource tracker, pickling rules, the queue and join deadlock, the terminate hazard |

Every claim in this skill that names a version comes from one of these three
pages. A claim without a version is a design judgment, and the text labels it
as one.

## Confirmed claims

The audit confirmed these statements from the source document.

1. Python 3.13 supports a free-threaded mode as an experiment only. The mode
   needs a separate executable, usually named `python3.13t`. The official
   Windows and macOS installers offer it. A source build uses `--disable-gil`.
2. Python 3.13 carries a substantial single-thread cost in that mode.
3. The Python 3.13 just-in-time compiler needs a custom build with
   `--enable-experimental-jit`, and it stays off by default.
4. `os.process_cpu_count()` is new in Python 3.13, and it respects the processor
   affinity. `concurrent.futures` and `multiprocessing` now use it for their
   default worker counts.
5. `queue.Queue.shutdown` and `queue.ShutDown` are new in Python 3.13.
6. A process pool pickles every argument and every result. A lambda expression,
   a local function, and an open handle cannot cross that boundary.
7. `spawn` is the default start method on Windows and on macOS.
8. `multiprocessing.Pool` accepts `maxtasksperchild`, which replaces a worker
   after a set number of tasks.
9. A `Manager` proxy costs one round trip for each access, so it is slower than
   a shared buffer.
10. The overhead figures are correct as orders of magnitude.

## Corrections

The audit found these defects. This skill states the corrected version.

### Correction 1. The lock does not switch for each bytecode

The source document describes the lock as "held, one bytecode at a time". That
is wrong. One thread holds the lock while it runs bytecode, and the interpreter
switches on a time interval, not on each instruction. The lock is also released
around input and output and inside many C calls.

The distinction matters. It explains why threads help a program that waits, and
why a compiled library that releases the lock gives real parallelism.

### Correction 2. The start method changed in Python 3.14

The source document implies that `fork` is the default on POSIX. That was true
through Python 3.13. Python 3.14 changed the default to `forkserver` on POSIX
platforms other than macOS, and `fork` is no longer the default anywhere.

This is the highest-risk gap in the source document. Code that relied on
inheritance under `fork` fails on Python 3.14 with a name error or a pickling
error.

### Correction 3. The fork hazard is missing

The source document lists `os.fork()` with no warning. Python 3.12 and later
raise a `DeprecationWarning` when `os.fork()` runs in a process that holds
threads, because the child can inherit a locked lock and hang forever.

### Correction 4. The exclusion note is now outdated

The source document excludes subinterpreters and free-threading, and it gives
correct reasons for a Python 3.13 baseline. Both reasons expired with Python
3.14. That version added the `concurrent.interpreters` module, added
`concurrent.futures.InterpreterPoolExecutor`, and made the free-threaded build
officially supported.

This skill includes both, and it marks the version that each one needs.

### Correction 5. The speedup columns are not sourced

The source document gives speedup ranges such as 10 to 500 times for vectorized
code and 50 to 1000 times for a graphics processor. No source supports those
numbers as general facts. A speedup depends on the code, the data, and the
hardware.

This skill removes the ranges and requires a measurement instead.

### Correction 6. The rating scale is inconsistent

The final scorecard of the source document rates one row with six stars on a
five-star scale. A rating table that breaks its own scale cannot rank anything.

This skill replaces the star ratings with named categories and a use condition.

### Correction 7. The thread-limit example does not always work

The source document sets the native thread-count variables inside a pool
initializer. That works under `spawn` and `forkserver`, because the worker
imports the library after the initializer runs. Under `fork`, the library is
already imported and has already read the variable, so the setting has no
effect.

This skill states the condition beside the example.

### Correction 8. Unverified engine claims

These claims in the source document could not be confirmed against a primary
source, so this skill does not repeat them as facts.

| Claim | Status |
| - | - |
| DuckDB has experimental graphics processor support | Unverified |
| pandas parallelizes partially through `numexpr` | Unverified |
| `SharedMemory` gained a `track` parameter in Python 3.13 | Unverified. The confirmed Python 3.13 addition in that area is the `trackfd` parameter of `mmap`. |
| Vaex and gevent maintenance status | Unverified |

This skill replaces each one with an instruction to check the current release
notes of the tool.

### Correction 9. A dead import in an example

The hybrid example in the source document imports `functools` and never uses it.
This skill does not carry that example.

## Additions

The source document covers strategy selection well. It covers almost nothing
about making a parallel program correct. The audit found nine missing subjects.
This skill adds all nine.

| Missing subject | Where this skill covers it |
| - | - |
| Race conditions and lock discipline | Correctness and safety, class 1 |
| Deadlock, including the queue and join trap | Correctness and safety, class 2 |
| Worker failure and pool recovery | Correctness and safety, class 3 |
| Backpressure and bounded queues | Correctness and safety, class 4 |
| Cancellation and graceful shutdown | Correctness and safety, class 5 |
| Resource leaks and the resource tracker | Correctness and safety, class 7 |
| Result ordering across the pool interfaces | Correctness and safety, class 8 |
| External rate limits | Correctness and safety, class 10 |
| How to prove a parallel speedup | Measuring parallel gains |

The audit also added five execution models that the source document omits.

1. `multiprocessing.Value` and `multiprocessing.Array`.
2. `asyncio.create_subprocess_exec`.
3. The `selectors` module.
4. Subinterpreters and `InterpreterPoolExecutor` on Python 3.14.
5. The free-threaded build as a first-class model, not only as an exclusion.

The audit added these Python 3.14 features, which the source document predates.

- `ProcessPoolExecutor.terminate_workers()` and `kill_workers()`.
- `Executor.map(..., buffersize=N)`, which bounds the pending results.
- `SyncManager.set()`, which shares a set across processes.
- `Process.interrupt()`, which lets a `finally` block run in the child.
- `sys.flags.thread_inherit_context`, which changes context inheritance.
- Authentication on the `forkserver` control socket.

## Judgment, not fact

These parts of the skill are engineering judgment. No documentation states them.
Treat them as this repository's policy, and change them when evidence disagrees.

1. The acceptance threshold of 1.5 times speedup.
2. The order of the decision sequence.
3. The rule that a task must exceed one millisecond to pay for a process, and
   ten microseconds to pay for a thread.
4. The ten-item pre-merge checklist.
5. The ten-section report structure.

## How to re-audit

Repeat this audit when a new Python version reaches a stable release.

1. Read the "What is new" page for the new version.
2. Search it for `multiprocessing`, `concurrent.futures`, `threading`,
   `asyncio`, `interpreters`, and `free-threading`.
3. Update the version table in the runtime guide.
4. Record the audit date and the sources in this file.
