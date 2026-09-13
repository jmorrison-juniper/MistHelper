### Performance monitoring modules

- **Added**: `src/utils/performance/` holds the recorder, the bounded sink, the
  stopwatch, the event contract, and the privacy filter. A span measures one
  boundary, and the level gate decides whether the span emits an event. The
  sink bounds its memory and opens a circuit after repeated write failures.
- **Added**: `tests/test_performance_monitoring.py` covers the level gate, the
  sampler, the bounded queue, the circuit, and the privacy filter with 71
  tests.
