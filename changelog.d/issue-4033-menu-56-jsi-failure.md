### Delay metrics persistence

- **Fixed**: Concurrent rate-limit telemetry writes no longer corrupt
  `delay_metrics.json` or reverse a successful export result. Issue #4033.
