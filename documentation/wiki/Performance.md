# Rate Limiting & Performance

- Adaptive delays stored in `delay_metrics.json`
- Safe concurrency mediated by semaphores + environment-driven thread limits (`FAST_MODE_MAX_CONCURRENT_CONNECTIONS`)
- Heavy operations log progress early, large loops chunked
- Fallback strategies engage when optional performance libraries are unavailable

## Fast Mode

Enable with `--fast` flag:

```bash
python MistHelper.py -M 16 --fast
```

Fast mode reduces retries and increases concurrency. Tune the maximum concurrent connections via environment variable:

```bash
FAST_MODE_MAX_CONCURRENT_CONNECTIONS=8
```

## Persistence Files

| File | Purpose |
|------|---------|
| `delay_metrics.json` | Adaptive delay control (PID-like) |
| `tuning_data.json` | Endpoint-specific learning data |

## Default Page Size

`DEFAULT_API_PAGE_LIMIT=1000` (configurable via `MIST_PAGE_LIMIT` environment variable).
