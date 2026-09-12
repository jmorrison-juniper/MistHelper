# Correctness and safety

A parallel program can produce a wrong answer that a test never catches. This
guide lists the failure classes, the detection method, and the repair.

Work through the checklist before you merge any parallel change.

## The pre-merge checklist

1. Every shared mutable value has a lock, a queue, or a private copy.
2. Every queue and every pool has a maximum size.
3. The program handles a worker that raises, a worker that hangs, and a worker
   that the operating system kills.
4. The program stops cleanly on a cancellation and on a shutdown signal.
5. The results match the sequential run, including the order.
6. No worker writes a global and expects the parent to read it.
7. The start method is explicit.
8. The thread count of every native library is bounded.
9. Every shared memory segment and every temporary file has an owner that
   releases it.
10. Every external service call respects its rate limit.

## Failure class 1. The race condition

Two threads read and write the same value without a lock. The result depends on
timing, so it changes between runs.

Warning: a read followed by a write is not atomic, even for one line of Python.
The statement `counter += 1` reads, adds, and writes. Two threads can read the
same value and write the same result, so one increment disappears.

```python
import threading

counter = 0
counter_lock = threading.Lock()  # Guards every read and write of counter

def increment() -> None:
    global counter
    with counter_lock:  # Read, add, and write must occur as one step
        counter += 1
```

Better repairs, in order of preference:

1. Remove the sharing. Give each worker a private value, then combine the
   values in the parent after the workers finish.
2. Pass the value through a queue. A queue is already thread-safe.
3. Add a lock. A lock is correct, and it reduces parallel speed.

Detection: run the operation many thousands of times under load and compare the
result against the sequential result. A single run proves nothing.

## Failure class 2. The deadlock

Two workers each hold a lock that the other one needs. Both wait forever.

Rules that prevent most deadlocks:

1. Acquire locks in the same order everywhere in the program.
2. Hold one lock at a time when you can.
3. Never call unknown code while you hold a lock.
4. Set a timeout on every acquire in a long-running service.

Two Python-specific deadlocks deserve a warning.

Warning: a child process that puts an item on a `multiprocessing.Queue` does not
exit until a background thread flushes the item into the pipe. If the parent
calls `join()` before it drains the queue, both processes wait forever. Drain the
queue first, then join.

Warning: a nested pool deadlocks. A worker inside a pool that submits work to the
same pool waits for a free worker that never appears. Restructure the work into
one level.

## Failure class 3. Worker failure

A worker can raise an exception, exit, or die by a signal. Each case behaves
differently.

```python
from concurrent.futures import ProcessPoolExecutor, as_completed

with ProcessPoolExecutor(max_workers=4) as pool:
    futures = {pool.submit(work, item): item for item in items}
    for future in as_completed(futures):
        item = futures[future]
        try:
            results.append(future.result())  # Re-raises the worker exception here
        except Exception:
            logging.exception("Item %s failed", item)  # Record and continue
```

Three rules follow.

1. Call `result()` on every future. An exception that no one reads is lost.
2. A worker killed by the operating system raises a broken-pool error, and the
   whole pool becomes unusable. Plan for a restart of the pool.
3. Use `terminate_workers()` on Python 3.14 to stop a pool whose workers hang.
   On an earlier version, run the pool in a process that you can stop.

Set a task limit for each worker when a task leaks memory. `multiprocessing.Pool`
accepts `maxtasksperchild`. `ProcessPoolExecutor` accepts `max_tasks_per_child`.
The pool then replaces a worker after that many tasks, and the leak resets.

## Failure class 4. No backpressure

A fast producer fills a queue faster than the consumer drains it. Memory grows
until the process dies.

```python
import queue

# Wrong: unbounded. A fast producer exhausts memory.
work_queue = queue.Queue()

# Correct: bounded. put() blocks when the queue is full, so the producer waits.
work_queue = queue.Queue(maxsize=1000)
```

The same rule applies to a pool. `Executor.map` on Python 3.14 accepts
`buffersize`, which limits the pending results. On an earlier version, submit the
work in batches instead of submitting every item at once.

Warning: `Executor.map` without a limit reads the whole input iterable at once.
A generator that reads a large file therefore loads the whole file into memory.

## Failure class 5. Cancellation and shutdown

A long-running job must stop when the user asks. A process must stop when the
service restarts.

```python
import signal
import threading

stop_requested = threading.Event()  # One flag that every worker reads

def handle_stop(signal_number: int, frame: object) -> None:
    stop_requested.set()  # Signal handlers must stay small and non-blocking

signal.signal(signal.SIGTERM, handle_stop)  # Container stop sends this signal
signal.signal(signal.SIGINT, handle_stop)   # Keyboard interrupt sends this one

def worker(items: list[str]) -> list[str]:
    output = []
    for item in items:
        if stop_requested.is_set():  # Check between items, not inside one item
            break
        output.append(handle(item))
    return output
```

Rules:

1. Check the stop flag between units of work, never in the middle of a write.
2. A thread cannot be killed from the outside. Design the worker to return.
3. `Process.terminate()` does not run `finally` blocks, so a shared lock or a
   queue can remain broken. On Python 3.14, prefer `Process.interrupt()`, which
   raises a keyboard interrupt inside the child and lets `finally` blocks run.
4. In `asyncio`, use `TaskGroup` and `asyncio.timeout`. The group cancels the
   remaining tasks when one task fails.

Warning: `Process.terminate()` while the child holds a lock or writes to a queue
leaves that lock held and that queue corrupted. Every other process that touches
the same object then hangs or raises.

## Failure class 6. Oversubscription

A numeric library starts its own thread pool. Inside a process pool of 8
workers, 8 libraries each start 8 threads, which produces 64 threads on 8 cores.
The processor spends its time on context switches.

```python
def limit_native_threads() -> None:
    import os
    for name in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ[name] = "1"  # Each worker process uses one native thread

ProcessPoolExecutor(max_workers=worker_count, initializer=limit_native_threads)
```

Warning: this initializer works only when the worker imports the library after
the initializer runs. That holds for `spawn` and `forkserver`. Under `fork`, the
library is already imported and has already read the variable, so the setting has
no effect. Under `fork`, set the variable before the program imports the library,
or use a library that changes its thread count at run time.

Detection: watch the processor use. A run that shows high system time and low
user time points to oversubscription.

## Failure class 7. Resource leaks

A shared memory segment, a semaphore, and a temporary file each outlive the
process that made them.

On POSIX, the `spawn` and `forkserver` methods start a resource tracker process.
The tracker unlinks any named resource that a killed process left behind. A
leaked segment that the tracker misses stays until the machine restarts.

```python
from multiprocessing import shared_memory

segment = shared_memory.SharedMemory(create=True, size=size)
try:
    use(segment)
finally:
    segment.close()   # Every process that maps the segment calls this
    segment.unlink()  # Exactly one process calls this, and only once
```

Rules:

1. Every process calls `close()`. Exactly one process calls `unlink()`.
2. Use `try` and `finally`, so a failure still releases the segment.
3. Name the owner in a comment. A segment with two owners raises on the second
   `unlink()`.

## Failure class 8. Result ordering

`Pool.imap_unordered` and `as_completed` return results in completion order, not
in input order. Code that assumes input order produces a wrong answer.

| Interface | Order |
| - | - |
| `Executor.map` | Input order |
| `as_completed` | Completion order |
| `Pool.map` | Input order |
| `Pool.imap` | Input order |
| `Pool.imap_unordered` | Completion order |

When you use a completion-order interface, carry a key with each task and rebuild
the order in the parent.

## Failure class 9. Serialization limits

A process boundary pickles every argument and every result.

These values cannot be pickled:

- A lambda expression and a local function.
- An open file, a socket, a database connection, and a lock.
- A generator and most iterators.
- A class defined inside a function or inside the interactive shell.

Repairs:

1. Define the worker at module level.
2. Pass a path or a connection string, and open the resource inside the worker.
3. Use `pathos` when the value truly cannot be restructured.

Warning: a value that pickles successfully can still cost more than the work. A
task that sends 100 megabytes to compute for 10 milliseconds runs slower in
parallel than in sequence. Measure the transfer, not only the compute.

## Failure class 10. External rate limits

More workers send more requests. A remote service answers with a refusal, and
the program looks broken.

Rules:

1. Share one rate limiter across every worker. A limiter inside each worker
   multiplies the allowed rate by the worker count.
2. Prefer a bulk endpoint over one request for each item.
3. Add a retry with an increasing delay, and add a maximum attempt count.
4. Compute the request budget before you raise the worker count.

## Detection commands

| Question | Command |
| - | - |
| Does a race exist? | Run the parallel path many times and compare against the sequential result. |
| Does the program hang? | Send an interrupt and read the stack, or call `faulthandler.dump_traceback_later`. |
| Does the memory grow? | Record the peak resident size for each worker count. |
| Do threads oversubscribe? | Compare the thread count against the core count while the program runs. |
| Does a segment leak? | List the shared memory objects after the run ends. |

Add `faulthandler` to any long-running worker. It prints a stack for every
thread when the process hangs.

```python
import faulthandler

faulthandler.enable()  # Prints every thread stack on a fatal signal
faulthandler.dump_traceback_later(timeout=300, exit=True)  # Guards against a hang
```
