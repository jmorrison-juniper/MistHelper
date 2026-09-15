# Analysis: Source back-reference settings slice

## Baseline

The analyst plan recorded 376 text matches for `importlib.import_module("MistHelper")` under `src`.

The same plan recorded 366 executable calls to `importlib.import_module("MistHelper")`.

The same plan recorded 21 executable `import MistHelper` imports under `src`.

## Delivered slice

This branch moves source readers for these names:

- `DEFAULT_API_PAGE_LIMIT`
- `CSV_FRESHNESS_MINUTES`
- `API_REQUEST_MAX_RETRIES`
- `API_REQUEST_RETRY_DELAY`
- `FAST_MODE_MAX_RETRIES`
- `FAST_MODE_RETRY_DELAY`
- `FAST_MODE_RETRY_THREADS`
- `FAST_MODE_RETRY_MAX_RETRIES`
- `FAST_MODE_FALLBACK_THREADS`
- `_api_usage_cache`

## Reference count after the slice

The executable call count for `importlib.import_module("MistHelper")` is 356.

The executable import count for `import MistHelper` is 18.

The slice removes 10 executable importlib calls and 3 executable imports.

## Remaining work

Source modules still read live application state through the root facade.

The remaining high-risk work includes capture dependency objects, exporter imports, application context reads, and root alias removal.

`MistHelper.py` must remove `sys.modules["MistHelper"]` only after all source back-references are gone.

Follow-up issue #2670 tracks the root alias removal.

## Evidence

- Focused tests passed: 191 tests.
- Import checks passed for `src.api.api_data_fetcher`, `MistHelper`, and `wsgi`.
- The branch diff does not include `MistHelper.py`.
