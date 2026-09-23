# Implementation Plan: Honest operation output files

## Technical Context

Python 3.13. The change is limited to `web_portal/services/operation.py` and unit tests. The run record already owns `output_files`, so the final evidence check is the least-risk place to repair both defects.

## Root Cause

- `web_portal/services/operation.py` keeps log-scraped output names even when the file does not exist at run end.
- The same run record order lets a prompt cache refresh place `SiteList.csv` before the real site-scoped output.

## Design

1. After the operation finishes and after the scanner merge runs, finalize `run["output_files"]`.
2. Remove each output name whose path does not exist under the scanner root.
3. For non-menu-1 runs with more than one output, move `SiteList.csv` behind the other files.
4. Leave menu 1 unchanged, because menu 1 is the site list export.

## Risk

The log scraper stays broad, so existing real log-discovered files remain supported. The final existence check reduces false positives without changing scanner behavior.

## Verification

- Add unit guards for phantom log files and cache ordering.
- Run the focused unit tests.
- Run local portal browser checks on port 9612 for menus 4 and 69.
