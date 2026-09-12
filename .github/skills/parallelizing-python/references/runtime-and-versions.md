# Runtime and versions

The execution rules of CPython changed between Python 3.13 and Python 3.14.
A design that is correct on one version can fail on the other. State the target
version before you choose a model.

Every statement below carries a source in
[the audit and sources guide](./audit-and-sources.md).

## Report the runtime first

Run this command and record the output in the report.

```powershell
python -c "import sys, os, platform, multiprocessing as mp; print(sys.version); print(platform.platform()); print('logical cores:', os.cpu_count()); print('usable cores:', os.process_cpu_count()); print('start method:', mp.get_start_method(allow_none=True)); print('all start methods:', mp.get_all_start_methods())"
```

On a free-threaded build, add this check.

```powershell
python -c "import sys; print(sys._is_gil_enabled())"
```

A `False` result means that the lock is off in this process.

## Worker count

Use `os.process_cpu_count()`. Python 3.13 added it. The function reports the
cores that the calling thread may use, so it respects a processor affinity mask
and a container limit. `os.cpu_count()` reports every core on the machine, which
overcommits a container.

Python 3.13 also made `concurrent.futures`, `multiprocessing`, and `compileall`
choose their default worker count with `os.process_cpu_count()`.

You can override both functions with the `PYTHON_CPU_COUNT` environment variable
or the `-X cpu_count` option. This helps when you cannot change the code.

```python
import os
from concurrent.futures import ProcessPoolExecutor

worker_count = os.process_cpu_count()  # Respects affinity, unlike os.cpu_count()
with ProcessPoolExecutor(max_workers=worker_count) as pool:
    results = list(pool.map(work, items, chunksize=64))
```

## Start methods

A start method decides how a child process begins. The three methods are
`spawn`, `fork`, and `forkserver`.

| Version | Default on Windows | Default on macOS | Default on other POSIX |
| - | - | - | - |
| Python 3.13 | `spawn` | `spawn` | `fork` |
| Python 3.14 | `spawn` | `spawn` | `forkserver` |

Python 3.14 removed `fork` as a default on every platform. Code that needs
`fork` must now ask for it through `multiprocessing.get_context("fork")`.

Warning: this change breaks code that relied on inheritance. Under `fork`, a
child inherits every global that the parent held. Under `forkserver` and
`spawn`, the child imports the main module instead, so an unpicklable argument
raises an error and a mutable global reverts to its import-time value. The
failure appears as a `NameError`, an `AttributeError`, or a pickling error from
inside the pool.

Set the method explicitly, so the code behaves the same on every version.

```python
import multiprocessing as mp

def main() -> None:
    context = mp.get_context("spawn")  # Explicit, so no version default applies
    with context.Pool(processes=4) as pool:
        print(pool.map(work, items))

if __name__ == "__main__":  # Required. spawn and forkserver import this module.
    main()
```

Python 3.14 also made the `forkserver` control socket authenticate its callers.
Before that change, only file permissions restricted which process could ask the
forkserver to run code.

## The `fork` hazard

Python 3.12 and later raise a `DeprecationWarning` when `os.fork()` runs in a
process that holds more than one thread. The child receives a copy of every lock
in its current state, so a lock that another thread held stays locked forever.

Warning: this defect appears as a hang, not as an error. A logging lock, a
memory allocator lock, or a graphics processor context is enough to cause it.
Never use `fork` in a program that starts threads, opens a graphics processor
context, or imports a threaded numeric library.

The safe replacements are `forkserver` and `spawn`.

## Free-threaded builds

The free-threaded build removes the global interpreter lock, so threads run
Python bytecode in parallel.

| Version | Status | Executable | Single-thread cost |
| - | - | - | - |
| Python 3.13 | Experimental | `python3.13t` | Substantial |
| Python 3.14 | Officially supported, still optional | `python3.14t` | About 5 to 10 percent |

Both versions ship the build in the official Windows and macOS installers as a
separate option. You can also build it from source with `--disable-gil`.

Rules for a free-threaded build:

1. Check the mode at run time with `sys._is_gil_enabled()`. Do not assume it.
2. A C extension must declare support. Importing an extension that does not
   declare support turns the lock back on for the whole process.
3. You can force the lock on with `PYTHON_GIL=1` or `-X gil=1`.
4. The just-in-time compiler does not work on a free-threaded build.
5. Removing the lock does not remove a race. Shared mutable state still needs a
   lock, a queue, or a copy.

Warning: do not adopt a free-threaded build for production without a test that
runs the real workload. The build changes the timing of every thread, so a
latent race that never appeared before can appear immediately.

## Subinterpreters

Python 3.14 added the `concurrent.interpreters` module and the
`concurrent.futures.InterpreterPoolExecutor` class. Each interpreter holds its
own lock, so interpreters run in parallel inside one process.

Interpreters sit between threads and processes. They isolate like a process and
start faster than a process. Python 3.14 lists these limits:

1. Interpreter startup is not yet optimized.
2. Each interpreter uses more memory than it needs.
3. Object sharing is limited. `memoryview` is the main path.
4. Many extension packages are not yet compatible.

Do not use subinterpreters on Python 3.13. The interface was private there.

## Version-specific features worth using

| Feature | Version | Value |
| - | - | - |
| `os.process_cpu_count()` | 3.13 | A correct worker count inside a container |
| `queue.Queue.shutdown` and `queue.ShutDown` | 3.13 | Clean worker shutdown without a sentinel value |
| `asyncio.Queue.shutdown` and `asyncio.QueueShutDown` | 3.13 | The same for async workers |
| `mmap` with `trackfd=False` | 3.13 | Avoids a duplicate file descriptor on UNIX |
| `ProcessPoolExecutor.terminate_workers()` and `kill_workers()` | 3.14 | Stops a stuck pool |
| `Executor.map(..., buffersize=N)` | 3.14 | Bounds the pending results, which bounds memory |
| `SyncManager.set()` | 3.14 | A shared set across processes |
| `Process.interrupt()` | 3.14 | Sends an interrupt signal, so `finally` blocks run |
| `sys.flags.thread_inherit_context` | 3.14 | A new thread copies the caller's context |

The clean shutdown pattern uses the queue shutdown feature.

```python
import queue

work_queue: queue.Queue[str] = queue.Queue(maxsize=100)  # Bounded, so memory is bounded

def worker() -> None:
    while True:
        try:
            item = work_queue.get()
        except queue.ShutDown:  # Python 3.13 and later. No sentinel value needed.
            return
        handle(item)
        work_queue.task_done()

work_queue.shutdown()  # Add immediate=True to drop the pending items
```

## Context variables across threads

A background thread does not inherit a thread-local value. Pass every value that
the worker needs as an argument.

Python 3.14 added the `thread_inherit_context` flag. When the flag is on, a new
thread starts with a copy of the context of the caller of `start()`. The flag
defaults to true on a free-threaded build and false on a normal build.

Warning: do not depend on the flag for correctness. The default differs between
builds, so the same code behaves differently on two interpreters of the same
version. Pass the value explicitly instead.

## The just-in-time compiler

The just-in-time compiler is not a parallel feature. It changes sequential
speed only.

| Version | Availability |
| - | - |
| Python 3.13 | Requires a custom build with `--enable-experimental-jit` |
| Python 3.14 | Present in the official macOS and Windows binaries. Enable it with `PYTHON_JIT=1`. |

Python 3.14 reports a range from 10 percent slower to 20 percent faster,
depending on the workload. Measure it. Do not enable it on the basis of the
label.
