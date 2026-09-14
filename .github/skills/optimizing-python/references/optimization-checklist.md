# Optimization checklist

Use this checklist to investigate measured candidates, not to start an automatic
rewrite. Benchmark typical, worst-case, cold, and warm workloads where relevant.
Preserve behavior and explain the memory and maintenance costs of each change.

## 1. Algorithms and repeated work

- Find growing nested loops, repeated linear scans, repeated sorting, and
  unnecessary graph or tree traversals.
- Find repeated parsing, normalization, validation, hashing, encoding, decoding,
  schema discovery, and representation conversion.
- Check repeated route or topology calculations against the actual input
  identity and freshness requirements.
- Move invariant work outside a loop only when the inputs cannot change during
  that loop. Measure both construction and reuse costs.
- Consider incremental processing when the operation does not require a complete
  materialized dataset.

For `n` queries over `m` records, repeated scans can cost `O(n * m)`. A reusable
hash index can give expected `O(m + n)` time with `O(m)` additional storage.
State hashing assumptions and index lifetime. Measure small collections too.

A dictionary index can change first-match behavior to last-match behavior when
keys repeat. A set can remove duplicates or lose required order. Check unhashable
values, custom equality, missing keys, and duplicate handling before replacing
a scan.

For repeated sorting, compare a heap, maintained sorted data, or one initial
sort. Preserve ties and output order. Do not assume that a new structure improves
the complete workload.

Python's `re` module already caches recent patterns. Confirm repeated compilation
or cache pressure before retaining an explicit compiled-pattern change.

Estimate the end-to-end limit. If fraction `f` of baseline time receives speedup
`s`, the ideal total speedup is `1 / ((1 - f) + f / s)`. This is an estimate,
not a measured result. Include new conversion and setup costs in the benchmark.

## 2. I/O counts and sequential batching

- Inspect one query per item, one Redis request per field, repeated connection
  creation, and repeated small file reads or writes.
- Inspect unnecessary columns, payload fields, ORM objects, serialization
  boundaries, parsing passes, and `flush()` calls.
- Compare bounded database batches, Redis batches, buffered files, streaming,
  and sequential reuse of clients or connection pools.
- Consider server-side filtering, aggregation, and suitable indexes when query
  plans support the change. Preserve parameterized queries.
- Measure request counts, round trips, bytes, server costs, and wall time.
  Separate external waiting from Python CPU work.

Preserve transaction boundaries, durability, ordering, retry behavior,
idempotency, partial-failure handling, pagination, and service limits. Bound batch
sizes and memory. A Redis pipeline is not automatically equivalent to a
transaction. A bulk call can still perform many server operations.

Do not add asynchronous requests or extra workers. Do not remove rate limits or
timeouts for a benchmark. A missing index is a hypothesis until a query plan and
representative measurement support it. Follow schema-change review rules.

For logging, prefer deferred `%s` formatting where the logging API supports it.
Guard expensive debug argument construction when necessary. Group only optional
events when the operational contract permits it. Never remove required action,
audit, failure, or safety logs to meet a performance target.

## 3. Data structures

| Operation | Candidate | Check before retention |
| --- | --- | --- |
| Repeated membership or lookup | Compare `set`, `frozenset`, or `dict`. | Include construction, hashing, cardinality, duplicates, and required order. |
| Queue access at both ends | Compare `collections.deque`. | Middle indexing is not its strength. Preserve capacity behavior. |
| Repeated minimum or maximum selection | Compare `heapq`. | Preserve ties, comparison rules, and output order. |
| Lookup in a maintained sorted sequence | Compare `bisect`. | Search is `O(log n)`, but list insertion remains `O(n)`. |
| Homogeneous numeric or binary data | Compare `array`, packed records, or `memoryview`. | Check widths, overflow, byte order, ownership, and conversion costs. |
| Single-pass consumption | Compare iterators or generators. | Check complete consumption, repeat traversal, and exception timing. |
| Immutable internal records | Compare tuples or immutable records. | Preserve public types, field access, and meaningful validation. |

Measure locality, allocation pressure, and the total footprint. A tiny list can
outperform a newly constructed set. A compact representation can lose its benefit
through repeated conversion at its boundaries.

## 4. Allocations and copying

- Find temporary lists consumed once, reconstructed dictionaries, materialized
  `dict.items()` views, and lists created only for one later traversal.
- Find unnecessary `deepcopy`, model construction, large slices, and repeated
  conversions between bytes and text.
- Inspect potentially quadratic string or byte concatenation. Compare
  `"".join(parts)`, collection extension, or buffered output as appropriate.
- Compare a single transformation pass, generators, `yield from`, streaming,
  reusable buffers, and `memoryview` where ownership permits them.
- Measure traced allocation sites, peak memory, retained objects, and the full
  workload. Use allocation-event measurements when temporary churn matters.

Do not assume every `+=` operation is quadratic on every interpreter. Benchmark
the actual expression and data sizes.

Preserve object identity, aliasing, copy isolation, lifetime, and mutability.
A `memoryview` can retain a large backing buffer or expose later mutations.
A generator can defer validation, exceptions, and file closure. A reused buffer
must not change data that a caller still owns.

Do not replace a repeatedly traversed collection with a one-use iterator. Do not
replace a public model with a tuple merely because the tuple allocates less.

## 5. Serialization and validation

- Measure repeated serialization of unchanged objects, model-to-dictionary
  conversion, dataclass conversion, and validation-model construction.
- Inspect pretty printing, sorted JSON keys, duplicate encoding or decoding,
  intermediate dictionaries, and full serialization for a partial update.
- Compare standard `json` with a compatible native-backed implementation only
  when serialization is a measured cost.
- Consider MessagePack or another binary format only when the protocol and
  storage contracts explicitly permit it.
- Reuse validated immutable representations only when external boundaries still
  validate and mutation cannot invalidate the result.

Preserve integer ranges, floating-point behavior, NaN and infinity rules, Unicode,
escaping, byte or string output types, key handling, ordering, and custom hooks.
Check malformed inputs, exception types, duplicate keys, and resource limits.
Keep canonical formatting when signatures or consumers depend on it.

Never replace validation with a trust assumption. Do not weaken authorization,
security limits, or error handling. Include serialization boundaries and any
new compatibility conversions in the benchmark.

## 6. Bounded caching and memoization

Consider pure deterministic calculations, stable schema metadata, parsed
configuration, compiled patterns, immutable properties, and normalized
identifiers. Topology results require versioned inputs and safe invalidation.

Before adding a cache, document these five points:

1. Define the key, equality behavior, input identity, and result ownership.
2. Bound key cardinality, entry size, total memory, and lifetime.
3. Define invalidation for every input or external-state change.
4. Measure hit rate, misses, hashing, lookup, population, and eviction costs.
5. Test freshness, eviction, mutation isolation, release, and sustained growth.

Prefer a bounded `functools.lru_cache` when the measured workload justifies it.
A size bound counts entries, not bytes. It does not provide freshness or expiry.
Use `cache_info()` and an explicit invalidation mechanism such as `cache_clear()`
when appropriate. Neither method creates a correct lifecycle automatically.

`functools.cache` and `lru_cache(maxsize=None)` are unbounded. Use them only when
finite key cardinality, entry size, and a controlled lifecycle prove acceptable
memory use. Cached arguments and results remain referenced. Cached methods can
retain `self` and its object graph.

Reject caching when recomputation is cheap, keys grow without control, or cache
overhead exceeds the saved work. Reject unsafe caching of mutable, user-specific,
or time-sensitive results. Do not cache authorization decisions under this skill.
Do not substitute stale operational state for a required current reading.

`cached_property` needs an instance dictionary and can increase its memory use.
Check its interaction with `__slots__`, invalidation, and object lifetime.

## 7. Measured Python loops

- Hoist invariants, combine passes, and compare suitable built-ins with Python
  loops only after the profile identifies a significant loop cost.
- Investigate deep attribute chains, expensive properties, callbacks, repeated
  method resolution, and excessive call boundaries in proven hot paths.
- Compare a direct loop with callback-heavy processing when readability and
  public boundaries permit the change.
- Inspect exception frequency and dynamic dispatch costs. Preserve all required
  checks and error behavior.
- Test on the actual supported interpreter versions and representative types.

CPython 3.12 inlines list, set, and dictionary comprehensions through PEP 709.
This is not a universal guarantee that a comprehension beats a loop. Adaptive
specialization also changes the value of manual lookup optimizations.

Do not automatically retain aliases such as `append = result.append` or
`local_value = self.value`. Do not replace readable code with a clever one-liner.
Measure the complete path after any isolated gain.

## 8. Object layout and garbage collection

Consider `dataclass(slots=True)` or `__slots__` for a measured large population of
small objects. Measure construction, access, and total memory. Test inheritance,
weak references, dynamic attributes, introspection, serializers, and properties.
Do not convert all classes to slotted classes.

Inspect cycles, global caches, closures, callbacks, registries, back-references,
and large temporary graphs. Remove unnecessary retention before adjusting GC.
Distinguish cyclic collection costs from reference counting and allocator costs.

Test GC thresholds or a temporary cyclic-GC suspension only when collection
overhead is significant and the object graph is understood. Bound the operation.
Save the previous enabled state and thresholds. Restore both in `try/finally`,
including failure paths. Do not unconditionally enable GC if it was disabled.

Measure sustained memory growth and collection behavior. Reject a timing gain
that causes unacceptable retention or delayed resource release. Do not change
process-wide GC policy without the required review.

## 9. Startup and imports

- Inspect heavy optional imports, import-time configuration discovery, network
  or database access, and large global object construction.
- Inspect plugin scans, eager schema generation, circular imports, and dynamic
  imports inside measured hot paths.
- Compare explicit initialization with operational work at module import time.
- Defer genuinely optional imports only when failure timing and first-use costs
  remain acceptable. Do not make every import lazy.
- Consider safe on-disk metadata or bytecode preparation when deployment permits
  it. Define cache invalidation and measure the complete startup path.

Measure fresh process startup, warm startup conditions, and useful completion
separately. Recheck platform-specific commands and import side effects.
Do not optimize insignificant test or startup paths instead of the stated
objective. Do not use `-O`, `-OO`, or `os._exit()` to bypass checks or cleanup.

## 10. Native acceleration

Escalate only for an isolated, stable, measured CPU hotspot. Reject native
compilation for network waiting, cold code, dynamic orchestration, or thin
calls into libraries that already perform the expensive work natively.

| Candidate | Suitable evidence | Required checks |
| --- | --- | --- |
| Cython | Numeric, parsing, binary, geometry, or graph loops have stable types. | Measure typed regions. Check boxing, integer overflow, division, bounds, and Python-visible APIs. |
| mypyc | Typed modules consume a meaningful share of runtime. | Check current maturity, runtime type checks, binding, introspection, generators, and compiled imports. |
| NumPy | Dense numeric arrays match the workload. | Include array conversion, copies, dtype widths, overflow, and memory use. |
| Numba | Compatible numerical functions dominate execution. | Include compilation and warmup costs. Exclude parallel mode, `prange`, and GPU execution. |
| PyO3, C, or C++ extensions | A narrow native boundary removes a proven CPU cost. | Check ownership, conversions, exceptions, build tools, and supported platform wheels. |

Cython pure Python mode can keep `.py` source, but static typing is not free.
Declarations can introduce checks and conversions. Preserve the public API and
numeric behavior. Do not disable safety checks as a shortcut.

Check the installed mypyc version against its documentation. The sources checked
for this skill describe it as alpha. Test interpreted and compiled behavior.
Compiled execution can change introspection, runtime checks, and evaluation
behavior. Verify that the benchmark imports the compiled artifact.

Evaluate build complexity, compiler availability, ABI and wheel support,
portability, debugging, security maintenance, deployment size, and startup costs.
Define unsupported-platform behavior. If an optional fallback is appropriate,
test it separately and respect repository rules against compatibility shims.

Do not enable parallel kernels, hidden BLAS thread pools, or GPU work. Verify
documented sequential execution. Do not enable relaxed numeric modes that change
correctness. Benchmark the full Python-to-native-to-Python boundary.
