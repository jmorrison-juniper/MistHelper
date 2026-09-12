# Strategy matrix

This guide lists every practical way to run Python work in parallel or to
overlap waiting. Each section states the memory model, the data transfer cost,
and the main risk.

The baseline is a stock CPython interpreter from python.org. Every entry works
through the standard library or through a normal package install. Read
[the runtime and version guide](./runtime-and-versions.md) for the rules that
change between Python 3.13 and Python 3.14.

Definitions:

- **Concurrency** means the program makes progress on many tasks by overlapping
  the waiting. One core is enough.
- **Parallelism** means the program runs work at the same instant on many cores.
- **GIL** means the global interpreter lock. The lock allows one thread to run
  Python bytecode at a time inside one interpreter.

## Section 1. Standard library and core runtime

| # | Strategy | Unit | GIL behavior | Memory model | Transfer cost | Start cost | Scales to cores |
| - | - | - | - | - | - | - | - |
| 1 | `threading` | Operating system thread | Held for bytecode. Released for input and output, and inside many C calls. | Shared heap | None | Low | No for processor work. Yes for waiting. |
| 2 | `concurrent.futures.ThreadPoolExecutor` | Operating system thread | Same as `threading` | Shared heap | None | Pool is reused | Same as `threading` |
| 3 | `multiprocessing.Process` and `Pool` | Operating system process | One lock for each process | Isolated | High. Every value is pickled. | Medium to high | Yes |
| 4 | `concurrent.futures.ProcessPoolExecutor` | Operating system process | One lock for each process | Isolated | High. Every value is pickled. | Pool is reused | Yes |
| 5 | `multiprocessing.shared_memory` | Supports entries 3 and 4 | Not applicable | Explicit shared buffer | None for the buffer | Low | Yes |
| 6 | `mmap` and `numpy.memmap` | Supports any model | Not applicable | File-backed shared pages | None for the pages | Low | Yes |
| 7 | `multiprocessing.Manager` | Proxy server process | Not applicable | Proxied objects | Medium. One round trip for each access. | Medium | Yes |
| 8 | `multiprocessing.Value` and `Array` | Supports entries 3 and 4 | Not applicable | Shared C types with an optional lock | None for the buffer | Low | Yes |
| 9 | `asyncio` | Coroutine on one thread | Held. The lock yields at each `await`. | Shared, single thread | None | Very low | No. This is concurrency. |
| 10 | `asyncio.to_thread` and `run_in_executor` | Thread or process | Connects async code to blocking code | Depends on the executor | Depends on the executor | Pool is reused | Yes through a process pool |
| 11 | `subprocess` fan-out | External process | Not applicable | Isolated | Standard streams or files | Medium | Yes |
| 12 | `asyncio.create_subprocess_exec` | External process | Not applicable | Isolated | Standard streams | Medium | Yes |
| 13 | `os.fork` on POSIX | Process | One lock for each child | Copy on write | Free for reads | Low | Yes |
| 14 | `concurrent.interpreters` and `InterpreterPoolExecutor` | Subinterpreter | One lock for each interpreter | Isolated, in one process | Limited sharing | Medium | Yes on Python 3.14 |
| 15 | Free-threaded build | Operating system thread | No lock | Shared heap | None | Low | Yes on a free-threaded build |

Warning: entry 13 is unsafe in a program that holds threads. A child of `fork`
inherits a lock in whatever state the lock held at the moment of the call, so
the child can deadlock forever. Python 3.12 and later raise a
`DeprecationWarning` for `os.fork` in a multi-threaded process.

Warning: entries 3 and 4 hold no shared state by default. A global that a worker
writes is lost when the worker exits. Return the value instead.

## Section 2. Compiled extensions that release the lock

A compiled extension can release the global interpreter lock. Threads then run
that compiled code in parallel.

| # | Strategy | Mechanism | Lock behavior | Parallel interface | Effort |
| - | - | - | - | - | - |
| 16 | NumPy and SciPy | Vectorized C with single-instruction multiple-data hardware support | Released inside the C loop | Implicit. The linear algebra library threads internally. | Low |
| 17 | Numba `@njit` | Compilation at run time through LLVM | Released with `nogil=True` | `prange` with `parallel=True` | Medium |
| 18 | Numba for CUDA | Graphics processor kernels | Released | `@cuda.jit` | High |
| 19 | Cython | Translation to C | Released inside `with nogil:` | `prange` with OpenMP | Medium |
| 20 | Rust through PyO3 and maturin | Native extension | Released inside `Python::allow_threads` | The `rayon` crate | High |
| 21 | C or C++ through pybind11 | Native extension | Released inside `gil_scoped_release` | OpenMP or native threads | High |
| 22 | `ctypes` and `cffi` | Foreign function interface to an existing library | Released during the call | Whatever the library provides | Medium |
| 23 | mypyc | Compilation of typed Python | Held | None | Low |
| 24 | Nuitka | Compilation of a whole program | Held | None | Low |

Entries 23 and 24 do not release the lock. They reduce sequential time. They
belong to the `optimizing-python` skill, and this guide lists them only so that
you do not mistake them for a parallel strategy.

Warning: a speedup figure for a compiled kernel depends on the code, the data,
and the hardware. Measure the kernel yourself. Do not plan against a number that
you read in a table.

## Section 3. Data engines that parallelize for you

These engines run parallel work inside a compiled core. The calling program
stays sequential.

| # | Engine | Core | Parallel behavior | Larger than memory | Best use |
| - | - | - | - | - | - |
| 25 | Polars | Rust with Apache Arrow | All cores, automatic | Yes, through the streaming engine | Table operations on one machine |
| 26 | DuckDB | Vectorized C++ | All cores, automatic | Yes | SQL over Parquet, CSV, and Arrow |
| 27 | PyArrow | C++ Arrow | Multi-threaded compute kernels | Yes, through datasets | Zero-copy exchange between tools |
| 28 | pandas | Mixed | Limited | No | Existing code and wide library support |
| 29 | Dask | Task graph | Threads, processes, or a cluster | Yes | Scaling existing pandas or NumPy code |
| 30 | Ray | Tasks and actors | Cores, then a cluster | Yes | Stateful services and machine learning |
| 31 | PySpark | Java virtual machine with Arrow | Cluster | Yes | Very large data with existing Spark |
| 32 | cuDF and the RAPIDS suite | CUDA | Graphics processor threads | Limited | Table operations on a graphics processor |
| 33 | Vaex | Memory-mapped columns | Multi-core and lazy | Yes | Exploring very large tables |

Caution: check the release history and the open defect count of an engine before
you adopt it. An engine with slow maintenance becomes a liability. This applies
to entries 32 and 33 in particular.

## Section 4. Distributed and job systems

| # | Tool | Model | Broker | Survives a restart | Best use |
| - | - | - | - | - | - |
| 34 | joblib | `Parallel` and `delayed` over the loky backend | None | No | A simple independent loop |
| 35 | Celery | Distributed task queue | Redis or RabbitMQ | Yes | Background jobs with retries and schedules |
| 36 | Dramatiq | Task queue | Redis or RabbitMQ | Yes | A simpler alternative to Celery |
| 37 | Redis Queue | Task queue | Redis | Yes | The smallest durable queue |
| 38 | mpi4py | Message passing interface ranks | The message passing runtime | No | Tightly coupled numeric work on a cluster |
| 39 | pathos and multiprocess | Process pool that serializes with `dill` | None | No | Work that the standard pickle cannot serialize |
| 40 | Prefect and Airflow | Workflow graph | Varies | Yes | Scheduled pipelines with observation |

Warning: a durable queue changes the failure model. A task can run twice after a
broker restart. Make every task idempotent, or the retry corrupts the data.

## Section 5. Graphics processors and accelerators

| # | Tool | Abstraction | Parallel interface | Note |
| - | - | - | - | - |
| 41 | CuPy | An interface that matches NumPy on CUDA | Implicit in each array operation | The simplest move from NumPy |
| 42 | PyTorch | Tensors with automatic gradients | `DistributedDataParallel` and `torch.compile` | Also serves as a plain array library |
| 43 | JAX | Functional arrays | `jit`, `vmap`, and `shard_map` | Strong support for sharding |
| 44 | Triton | Kernels written in Python | Block-level programming | Custom combined kernels |
| 45 | PyOpenCL and Taichi | Kernel languages | Explicit | Hardware from more than one vendor |

Warning: never combine a graphics processor context with the `fork` start
method. The child inherits an invalid context, and the process crashes or hangs.
Use `spawn` or `forkserver`.

## Section 6. Concurrency for waiting work

These tools overlap waiting. They give no processor parallelism.

| # | Tool | Model | Cancellation | Note |
| - | - | - | - | - |
| 46 | `asyncio` | Event loop with `async def` | `TaskGroup` and `timeout` since Python 3.11 | The largest ecosystem |
| 47 | Trio | Structured concurrency | Nurseries with strict scope rules | A careful and small design |
| 48 | AnyIO | One interface over `asyncio` and Trio | Structured | Write once, run on either loop |
| 49 | `selectors` | Direct readiness notification | Manual | The layer below `asyncio` |
| 50 | gevent | Green threads through patched modules | Weak | Existing blocking code only |

Caution: a patched-module library such as gevent rewrites the standard library
at import time. The change affects every dependency. Prefer entries 46 to 48 for
new code.

## Overhead reference

These figures are orders of magnitude on a normal server. Measure your own
system before you plan against a number.

| Operation | Order of magnitude |
| - | - |
| A Python function call | Tens of nanoseconds |
| An `await` on a ready coroutine | Under one microsecond |
| A thread queue operation | A few microseconds |
| A thread context switch | Microseconds |
| A pickle round trip for a small object | Tens to hundreds of microseconds |
| A pickle round trip for a large array | Tens to hundreds of milliseconds |
| A `shared_memory` handoff | None. The workers map the same pages. |
| A `fork` of a worker | About a millisecond |
| A `spawn` of a worker | Tens to hundreds of milliseconds |

Two rules follow from the table.

1. A task must run much longer than a millisecond to pay for a process.
2. A task must run much longer than ten microseconds to pay for a thread.

Group small items into batches until each task passes the rule.

## Anti-patterns

| Mistake | Repair |
| - | - |
| Threads for processor-bound Python code | Use a process pool, a vectorized library, or a compiled kernel. |
| A pool over millions of tiny items | Set `chunksize`, or group the items into batches first. |
| A large table sent to every worker | Use `shared_memory`, a memory-mapped file, or a file path. |
| A linear algebra library inside a process pool | Limit the thread count in each worker. Read the correctness guide. |
| `os.cpu_count()` for the pool size | Use `os.process_cpu_count()`, which respects the processor affinity. |
| A cluster framework for two gigabytes of data | Use Polars or DuckDB on one machine. |
| `time.sleep` inside async code | Use `await asyncio.sleep(...)`. |
| A blocking driver inside an event loop | Use `asyncio.to_thread`, or use an async driver. |
| No `if __name__ == "__main__":` guard | Add the guard. The `spawn` and `forkserver` methods import the main module. |
| An unbounded queue between a fast producer and a slow consumer | Set a maximum size, so the producer waits. |
| A worker that writes a global | Return the value from the worker instead. |
| A `fork` in a program that holds threads | Set the start method to `spawn` or `forkserver`. |

## Selection summary

| Strategy | Processor scaling | Effort | Memory cost | Use it |
| - | - | - | - | - |
| Vectorized engines, entries 25 to 27 | High | Low | Low | Try this first for table and array work. |
| `ProcessPoolExecutor` | High | Low | High | The safe default for independent tasks. |
| Compiled kernels, entries 17 to 21 | Highest | High | Low | One measured hot kernel dominates. |
| `asyncio` | None | Medium | Low | Waiting work only. |
| Threads | None for Python code | Low | Low | Waiting work, or a library that releases the lock. |
| Durable queues, entries 35 to 37 | High | Medium | Medium | Work that must survive a restart. |
| Cluster frameworks, entries 29 to 31 | Highest | High | High | The data exceeds one machine. |
| Graphics processors, entries 41 to 45 | Highest | High | Medium | The work fits the hardware model. |
