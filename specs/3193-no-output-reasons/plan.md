# Implementation Plan: No-output completion reasons

## Technical Context

The issue affects the Operations portal completion evidence path in `web_portal/services/operation.py`. The browser result panel previews files from `run["output_files"]`.

## Reproduction

Local portal on port 9605 showed:

- Menu 77 completed with `SiteAnomalyEvents_AlamoSanAntonio.csv` and three rows.
- Menu 78 completed with no device anomaly rows but previewed `SiteInventory.csv`.
- Menu 82 completed with `SiteSwitchesMetrics.csv` and one row.

## Root Cause

Menu 78 refreshes `SiteInventory.csv` while it gathers device choices. When the anomaly handler logs zero records, the cache file is still the only changed file. The portal then treats it as output evidence.

## Design

Add `SiteInventory.csv` to the prompt cache marker set. Keep menu 60 as an exception, because menu 60 exports that file directly. Reuse the existing no-output reason path when the cache is the only changed file.

## Risks

- Existing file: `web_portal/services/operation.py` is large and exceeds the five-item guidance. This change stays surgical and adds no new hierarchy child.
- This branch does not edit `web_portal/services/output_scan.py`.

## Validation

Run the focused output-file tests, the lint and format checks, and a port 9605 portal proof for menus 77, 78, and 82.
