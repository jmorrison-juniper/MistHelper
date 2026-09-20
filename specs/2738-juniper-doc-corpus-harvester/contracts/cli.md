# Contract: Command-Line Entry

The harvester runs as one command-line batch tool. This contract defines the entry
class, the arguments, the exit behavior, and the reuse boundary.

## Entry class

`HarvestRunner` in `src/juniper_docs/harvest/runner.py` drives the whole harvest. A
thin entry block builds one runner and calls its `run` method. There is no wrapper
function that only delegates to the class.

```python
if __name__ == "__main__":          # Run the harvest when called as a script
    HarvestRunner(HarvestConfig.from_args()).run()   # Build config, then run
```

## Arguments

The tool reads a small config object, `HarvestConfig`, built from command-line
arguments. Each argument has a safe default so a cold run needs no argument.

| Argument | Type | Default | Purpose |
|----------|------|---------|---------|
| `--output-dir` | path | `data/juniper_corpus` | The output root under `data/`. |
| `--delay-seconds` | float | `1.0` | The minimum delay between two requests (FR-016). |
| `--timeout-seconds` | int | `90` | The per-request timeout. Generous for a large PDF. |
| `--max-sample-pages` | int | `8` | The page cap for the bounded content sample. |
| `--confidence-threshold` | float | `2.0` | The minimum score for a non-fallback sub-category. |
| `--tls-mode` | choice | `auto` | `auto`, `verify`, or `insecure`. See the TLS rule below. |
| `--retry-failed` | flag | off | Reprocess documents whose stage is `failed`. |
| `--sitemap-source` | path or url | live index | A recorded subset for a test run (Independent Test). |

`HarvestConfig` has at most 5 attributes per group. When the argument count grows, the
config splits into nested config objects so each class stays within the Five-Item Rule.

## TLS mode

| Mode | Behavior |
|------|----------|
| `auto` | Use `zscaler-root-ca.crt` when present and verify. Otherwise fall back to insecure with a loud warning. |
| `verify` | Always verify. Fail if no trusted CA validates the chain. |
| `insecure` | Disable verification. Log a warning. This path carries one justified `# nosec B323`. |

## Exit behavior

| Condition | Exit code | Notes |
|-----------|-----------|-------|
| The run finishes and every document reaches a final stage. | 0 | Failures may exist and are recorded. The run still exits 0 (SC-006, SC-010). |
| The store is locked or damaged, or the disk is full. | 1 | The tool fails closed and reports the error. No false progress. |
| An invalid argument. | 2 | The tool reports the bad argument and exits. |

A single document failure never changes the exit code. The run records the failure and
continues (FR-017).

## Progress and summary

- During the run, the tool logs the current stage and the count of completed documents
  out of the total (FR-035).
- At the end, the tool prints a summary. The summary shows the count for each category
  and sub-category. It shows the downloaded, skipped, failed, and dropped counts and
  the total bytes (FR-036).

## Reuse boundary

`scripts/crawl_jvd.py` imports `JvdCatalogClient`, `JvdPdfResolver`, and
`JvdDownloader` from `src/juniper_docs/acquire`. It keeps `JvdCatalogWalker` and
`JvdCrawlRunner` for the validated-designs crawl. The JVD crawl entry still runs:

```python
JvdCrawlRunner().run()              # The validated-designs crawl keeps working
```
