# Implementation Plan: Site cache output ordering

## Technical Context

The change is in the Operations portal run completion path. The scanner records files that changed during a run. Site-scoped parameter selection can refresh `SiteList.csv`, so the scanner can report a prompt cache as if it were a result file.

## Root Cause

`web_portal/services/operation.py` merged scanner output into `run["output_files"]` and the browser preview used the first name. `SiteList.csv` can sort before the operation output, so menu 69 previewed the site cache.

## Design

Use `SiteList.csv` as a prompt cache marker for all rows except menu 1. Keep the file in the output list, but order non-cache outputs first. If the cache is the only file and the handler logged a no-data reason, remove the cache so the result panel shows the reason.

Alternatives considered:

- Hide `SiteList.csv` for all operations. Rejected because menu 1 produces that file.
- Rank by file modification time. Rejected because the site prompt and operation output can finish close together.

## Risks

- Existing file: `web_portal/services/operation.py` is large and exceeds the five-item guidance. This change stays surgical and adds no new hierarchy child.
- The operation scanner is also under active work in another pull request. This plan does not edit `web_portal/services/output_scan.py`.

## Validation

Run the focused output-file tests. Then run menu 69 in the local portal on port 9605 and confirm the result panel previews the WLAN file.
