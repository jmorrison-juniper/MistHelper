# Python Parallelism & Concurrency — Complete Strategy Matrix

_Baseline: **stock CPython 3.13** from python.org — no special builds, no experimental flags, no private APIs. Everything here works today via the standard library or a plain `pip install`. "GIL" = Global Interpreter Lock._

> **Deliberately excluded** (not production-ready on a standard 3.13 install): free-threaded `python3.13t` (separate experimental build), subinterpreters / PEP 734 (private `_interpreters` API in 3.13; public in 3.14), and the experimental copy-and-patch JIT (requires a custom `--enable-experimental-jit` build).

---

## 0. The Decision Tree (read this first)

```
Is your bottleneck I/O (network, disk, DB, subprocess)?
├─ YES → asyncio / trio  ..............  thousands of concurrent ops, 1 core
│         (or ThreadPoolExecutor if libs are blocking/sync-only)
└─ NO (CPU-bound)
   ├─ Is the hot loop numeric arrays?
   │   ├─ YES → NumPy / Polars / DuckDB / CuPy / PyTorch
   │   │         (already parallel in C/Rust — GIL released)
   │   └─ NO (pure-Python objects, branching, dict/str work)
   │       ├─ Independent tasks, small payloads → ProcessPoolExecutor
   │       ├─ Large shared arrays → ProcessPoolExecutor + shared_memory
   │       └─ Rewrite hot kernel → Numba / Cython / Rust(PyO3)
   └─ Doesn't fit on one machine? → Dask / Ray / Spark / MPI
```

---

## 1. Master Matrix — Stdlib & Core Runtime

| # | Strategy | Unit of parallelism | GIL behavior | Memory model | Data transfer cost | Startup cost | Scales to cores? | Stdlib? |
|---|---|---|---|---|---|---|---|---|
| 1 | `threading` | OS thread | **Held** — 1 bytecode at a time | Shared, same heap | Zero (shared objects) | ~50 µs | ❌ No (CPU) / ✅ (I/O) | ✅ |
| 2 | `concurrent.futures.ThreadPoolExecutor` | OS thread | Held | Shared | Zero | Pool reused | ❌ No (CPU) / ✅ (I/O) | ✅ |
| 3 | `multiprocessing.Process` / `Pool` | OS process | One GIL **per process** | Isolated | **High** — pickle + pipe | 10–300 ms | ✅ Yes | ✅ |
| 4 | `ProcessPoolExecutor` | OS process | One GIL per process | Isolated | High — pickle | Pool reused | ✅ Yes | ✅ |
| 5 | `multiprocessing.shared_memory` | Backs #3/#4 | n/a | Explicit shared buffer | **Zero-copy** | Low | ✅ Yes | ✅ |
| 6 | `mmap` / `numpy.memmap` | Backs any model | n/a | File-backed shared pages | Zero-copy | Low | ✅ Yes | ✅ |
| 7 | `multiprocessing.Manager` | Proxy server process | n/a | Proxied shared objects | Med — proxy round-trip | Low | ✅ Yes | ✅ |
| 8 | `asyncio` | Coroutine (1 thread) | Held, but yields on await | Shared, single thread | Zero | ~µs | ❌ (concurrency ≠ parallelism) | ✅ |
| 9 | `asyncio.to_thread` / `run_in_executor` | Thread or process | Bridges async ↔ blocking | Depends on executor | Depends | Pool reused | ✅ via process pool | ✅ |
| 10 | `subprocess` fan-out | External process | Irrelevant (not Python) | Isolated | stdin/stdout/files | 1–100 ms | ✅ Yes | ✅ |
| 11 | `os.fork()` (POSIX only) | Process | One GIL per child | Copy-on-write | CoW read = free | ~1 ms | ✅ Yes | ✅ |

---

## 2. Master Matrix — Compiled / GIL-Releasing Extensions

| # | Strategy | Mechanism | GIL | Parallel API | Typical speedup | Learning curve |
|---|---|---|---|---|---|---|
| 12 | **NumPy / SciPy** | Vectorized C + SIMD + BLAS threads | Released in C loops | Implicit; `OMP_NUM_THREADS` | 10–500× vs. loops | 🟢 Low |
| 13 | **Numba** `@njit(parallel=True)` | LLVM JIT | Released via `nogil=True` | `prange`, auto-parallel | 10–200× | 🟡 Medium |
| 14 | **Numba CUDA** | GPU kernels | Released | `@cuda.jit` | 50–1000× | 🔴 High |
| 15 | **Cython** | C transpile | `with nogil:` | `prange` (OpenMP) | 10–150× | 🟡 Medium |
| 16 | **Rust via PyO3/maturin** | Native ext | `Python::allow_threads` | `rayon` | 10–200× | 🔴 High |
| 17 | **C/C++ via pybind11** | Native ext | `gil_scoped_release` | OpenMP / std::thread | 10–200× | 🔴 High |
| 18 | **ctypes / cffi** | FFI to existing .dll/.so | Released during call | Whatever the lib does | Varies | 🟡 Medium |
| 19 | **mypyc** | Compile typed Python | Held | — | 1.5–4× | 🟢 Low |
| 20 | **Nuitka** | Whole-program C compile | Held | — | 1.2–3× | 🟢 Low |

---

## 3. Master Matrix — Data Engines (parallel for free)

| # | Tool | Engine | Parallelism | Out-of-core? | GPU? | Best for |
|---|---|---|---|---|---|---|
| 21 | **Polars** | Rust + Arrow | All cores, auto | ✅ (lazy/streaming) | ⚠️ GPU engine | DataFrames — usually fastest CPU option |
| 22 | **DuckDB** | C++ vectorized | All cores, auto | ✅ | ⚠️ experimental | SQL over Parquet/CSV/Arrow |
| 23 | **PyArrow** | C++ Arrow | Multi-threaded compute | ✅ datasets | ❌ | Zero-copy interchange, IPC |
| 24 | **pandas 2.x + PyArrow backend** | Mixed | Partial (`numexpr`) | ❌ | ❌ | Legacy compat |
| 25 | **Dask** | Task graph | Threads/processes/cluster | ✅ | via RAPIDS | Scaling pandas/NumPy code |
| 26 | **Ray Core / Ray Data** | Actor + task | Cores → cluster | ✅ | ✅ | Stateful actors, ML pipelines |
| 27 | **PySpark** | JVM + Arrow | Cluster | ✅ | ✅ | Huge datasets, existing Spark infra |
| 28 | **cuDF / RAPIDS** | CUDA | GPU threads | ⚠️ | ✅ | GPU DataFrames, pandas API |
| 29 | **Vaex** | Memory-mapped | Multi-core lazy | ✅ | ⚠️ | Billion-row viz/exploration |

---

## 4. Master Matrix — Distributed & Job Systems

| # | Tool | Model | Broker needed | Durability | Best for |
|---|---|---|---|---|---|
| 30 | **joblib** | `Parallel`/`delayed`, loky backend | ❌ | ❌ | Drop-in embarrassingly-parallel loops (sklearn uses it) |
| 31 | **Celery** | Distributed task queue | Redis/RabbitMQ | ✅ | Background jobs, retries, schedules |
| 32 | **Dramatiq** | Task queue | Redis/RabbitMQ | ✅ | Simpler Celery alternative |
| 33 | **RQ** | Task queue | Redis | ✅ | Minimal setup |
| 34 | **mpi4py** | MPI ranks | ❌ (MPI runtime) | ❌ | HPC clusters, tight-coupled numerics |
| 35 | **pathos / multiprocess** | mp with `dill` | ❌ | ❌ | When pickling fails (lambdas, closures) |
| 36 | **Prefect / Airflow** | Workflow DAG | varies | ✅ | Orchestrated pipelines |

---

## 5. Master Matrix — GPU / Accelerator

| # | Tool | Abstraction | Parallel primitives | Notes |
|---|---|---|---|---|
| 37 | **CuPy** | NumPy-compatible on CUDA | Drop-in `import cupy as np` | Easiest NumPy→GPU port |
| 38 | **PyTorch** | Tensors + autograd | `DataParallel`, `DDP`, `torch.compile` | Also great as a plain array lib |
| 39 | **JAX** | Functional arrays | `jit`, `vmap`, `pmap`, `shard_map` | Best-in-class auto-parallel/sharding |
| 40 | **Triton** | Python→GPU kernels | Block-level programming | Custom fused kernels |
| 41 | **OpenCL/PyOpenCL, Taichi** | Kernel DSLs | Explicit | Cross-vendor GPU |

---

## 6. Master Matrix — Concurrency (I/O, not CPU parallelism)

| # | Tool | Model | Cancellation | Ecosystem |
|---|---|---|---|---|
| 42 | **asyncio** | Event loop, `async def` | `TaskGroup` (3.11+) | Largest |
| 43 | **trio** | Structured concurrency | Nurseries — best-in-class | Smaller, excellent design |
| 44 | **anyio** | Abstraction over asyncio/trio | Structured | Write once, run on both |
| 45 | **gevent / eventlet** | Monkey-patched greenlets | Weak | Legacy sync codebases |

---

## 7. Pros & Cons — In Depth

### 🧵 `threading`
**Pros:** trivial API · shared memory, zero serialization · low startup · perfect for I/O · works with any object.
**Cons:** **no CPU speedup** — GIL serializes bytecode · race conditions, needs locks · GIL contention can make CPU code *slower* than serial · hard to debug.
**Use when:** I/O-bound, or calling C libs that release the GIL (NumPy, requests, DB drivers).

### ⚙️ `multiprocessing` / `ProcessPoolExecutor`
**Pros:** true parallelism on **stable, stock Python** · full core utilization · crash isolation · mature, well documented · `max_tasks_per_child` guards leaks.
**Cons:** everything crossing the boundary must **pickle** (lambdas/closures/open handles fail) · serialization can dominate runtime · N× memory (N interpreters) · slow startup, esp. `spawn` on Windows/macOS · requires `if __name__ == "__main__":` guard · debugging/tracebacks are worse · no shared mutable state without `shared_memory`/`Manager`.
**Use when:** coarse-grained, independent tasks with small inputs/outputs. **The default safe choice.**

### 🧮 `shared_memory` / `mmap` / `Manager`
**Pros:** kills the biggest weakness of process pools — **zero-copy** handoff of large arrays · `numpy.memmap` gives larger-than-RAM arrays backed by disk · `Manager` proxies arbitrary shared dicts/lists across processes.
**Cons:** manual lifecycle — you must `close()` and `unlink()` or leak segments · no automatic locking; you coordinate writes yourself · `Manager` proxies are slow (a round-trip per attribute access) · only raw buffers are truly zero-copy, not arbitrary objects.
**Use when:** workers need the same big array. Pair with `ProcessPoolExecutor`.

### 🌊 `asyncio`
**Pros:** 10k+ concurrent sockets on one thread · no locks for most logic (single-threaded) · low memory per task · `TaskGroup`/`timeout` are excellent.
**Cons:** **zero CPU parallelism** · one blocking call stalls everything · async-colored functions infect the codebase · needs async-native libraries (`httpx`, `asyncpg`, `aiofiles`) · debugging is harder.
**Use when:** I/O-bound. Combine with `ProcessPoolExecutor` via `run_in_executor` for hybrid workloads.

### 🔢 NumPy / Polars / DuckDB
**Pros:** you often need **no parallel code at all** — the engine threads internally · orders of magnitude faster than Python loops · memory-efficient, cache-friendly · battle-tested.
**Cons:** you must express work as array/columnar ops · irregular/branchy logic doesn't vectorize · BLAS thread pools can **oversubscribe** when nested in a process pool (set `OMP_NUM_THREADS=1` in workers) · big intermediates can blow memory.
**Use when:** anything numeric or tabular. **Try this before writing any parallel code.**

### ⚡ Numba / Cython / Rust / C++
**Pros:** near-C speed on the actual hot loop · release the GIL → combine with threads freely · `prange`/`rayon` gives easy loop parallelism · often beats multiprocessing without any IPC.
**Cons:** build toolchain, compile times · restricted language subset (Numba) · type annotations / manual memory (Cython, Rust, C++) · harder debugging · packaging wheels across platforms.
**Use when:** one identifiable hot kernel dominates the profile.

### ☁️ Dask / Ray / Spark
**Pros:** scale past one machine · handle larger-than-RAM data · fault tolerance, retries, dashboards · Ray actors give stateful distributed objects.
**Cons:** big operational complexity · scheduler overhead makes small jobs *slower* than a plain pool · cluster tuning is a job in itself · debugging distributed failures.
**Use when:** data or compute genuinely exceeds one box. Not before.

---

## 8. Overhead Cheat Sheet (order-of-magnitude)

| Operation | Typical cost |
|---|---|
| Function call | ~50 ns |
| Thread context switch | ~1–10 µs |
| Coroutine `await` | ~0.1–1 µs |
| Queue put/get (threads) | ~1–5 µs |
| Pickle + IPC round-trip (small obj) | ~50–200 µs |
| Pickle 100 MB array | ~50–200 ms |
| `shared_memory` 100 MB handoff | ~0 (zero-copy) |
| `fork()` a worker | ~1 ms |
| `spawn()` a worker (Win/macOS) | ~50–300 ms |

**Rule of thumb:** a task must run **≫ 1 ms** to be worth a process, and **≫ 10 µs** to be worth a thread. Chunk your work.

---

## 9. Anti-Patterns

| ❌ Mistake | ✅ Fix |
|---|---|
| Threads for CPU-bound work | Process pool, or vectorize, or Numba |
| `Pool.map` over millions of tiny items | Chunk: `chunksize=` or pre-batch into lists |
| Passing giant DataFrames to workers | `shared_memory`, memmap, or Parquet paths |
| NumPy/BLAS threads *inside* a process pool | Set `OMP_NUM_THREADS=1` in workers |
| `os.cpu_count()` for pool size | `os.process_cpu_count()` (3.13, honors affinity) |
| Reaching for Dask/Spark on 2 GB of data | Polars or DuckDB on one machine |
| `time.sleep()` inside async code | `await asyncio.sleep()` |
| Blocking DB driver in an event loop | `asyncio.to_thread()` or an async driver |
| Forgetting `if __name__ == "__main__":` | Required for `spawn` (Windows/macOS) |
---

## 10. Canonical Snippets

```python
# --- Right-sized pool (3.13) ---
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

N = os.process_cpu_count()          # NEW in 3.13: honors CPU affinity

# CPU-bound, stock CPython
with ProcessPoolExecutor(max_workers=N) as ex:
    out = list(ex.map(work, items, chunksize=64))   # chunk! amortize IPC

# I/O-bound
with ThreadPoolExecutor(max_workers=min(32, N * 5)) as ex:
    out = list(ex.map(fetch, urls))
```

```python
# --- Zero-copy array sharing across processes ---
import numpy as np
from multiprocessing import shared_memory

a = np.random.rand(50_000_000)
shm = shared_memory.SharedMemory(create=True, size=a.nbytes, track=False)  # track= NEW in 3.13
buf = np.ndarray(a.shape, dtype=a.dtype, buffer=shm.buf)
buf[:] = a
# workers attach with SharedMemory(name=shm.name) — no pickling of 400 MB
```

```python
# --- Larger-than-RAM arrays, shared by every worker for free ---
import numpy as np
big = np.memmap("data.f64", dtype="float64", mode="r", shape=(1_000_000_000,))
# Each forked/spawned worker maps the same pages; the OS handles caching.
```

```python
# --- Hybrid: async I/O + process pool for CPU ---
import asyncio, functools
from concurrent.futures import ProcessPoolExecutor

async def main():
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fetch_all(urls))                       # I/O
            tg.create_task(loop.run_in_executor(pool, crunch, d)) # CPU
```

```python
# --- Avoid BLAS oversubscription in workers ---
def init():
    import os
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[v] = "1"

ProcessPoolExecutor(max_workers=N, initializer=init)
```

```python
# --- Numba: compiled + multi-threaded, no processes needed ---
from numba import njit, prange

@njit(parallel=True, fastmath=True, cache=True)
def simulate(x):
    acc = 0.0
    for i in prange(x.size):     # OpenMP-style parallel loop
        acc += x[i] ** 0.5
    return acc
```

```python
# --- Clean worker shutdown (queue.shutdown NEW in 3.13) ---
import queue, threading
q = queue.Queue()

def worker():
    while True:
        try:
            item = q.get()
        except queue.ShutDown:      # NEW in 3.13 — no sentinel hack
            return
        handle(item); q.task_done()

q.shutdown()   # or q.shutdown(immediate=True) to drop pending items
```

---

## 11. Scorecard

| Strategy | CPU scaling | Ease | Stability | Memory eff. | Ecosystem | Overall |
|---|---|---|---|---|---|---|
| Vectorize (NumPy/Polars/DuckDB) | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★★★ | 🥇 **Try first** |
| `ProcessPoolExecutor` | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★☆☆☆ | ★★★★★ | 🥈 **Safe default** |
| Numba / Cython / Rust | ★★★★★ | ★★☆☆☆ | ★★★★☆ | ★★★★★ | ★★★☆☆ | 🥉 **Max perf** |
| `asyncio` | ☆☆☆☆☆ (I/O ★★★★★) | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★☆ | 🌊 **I/O only** |
| `threading` | ☆☆☆☆☆ (I/O ★★★★☆) | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★★★ | 🧵 **I/O only** |
| joblib | ★★★★☆ | ★★★★★ | ★★★★☆ | ★★☆☆☆ | ★★★★☆ | ⚡ **Quick win** |
| Dask / Ray | ★★★★★ (cluster) | ★★☆☆☆ | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ☁️ **Scale-out** |
| GPU (CuPy/JAX/Torch) | ★★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★☆☆ | ★★★★★ | 🎮 **If it fits** |
