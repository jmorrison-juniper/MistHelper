# Phase 1 Menu Parity Evidence (Operations 7 and 169)

Date: 2026-05-26

## Operation 7 - Site Inventory Health Analysis

- Menu entry remains option `7` with unchanged description text.
- Behavior preserved: menu now delegates to `ExtractedSiteInventoryHealthAnalyzer.analyze(...)` with equivalent dependencies (`apisession`, org selection, site fetch, exporter).
- Unit coverage added in `tests/unit/analytics/test_site_inventory_health_analyzer.py` to validate core analysis/report paths.

## Operation 169 - Site Analytics Configuration

- Menu entry remains option `169` with unchanged destructive warning description text.
- Behavior preserved: menu now delegates to `ExtractedSiteAnalyticsConfigurator.execute(...)` with equivalent dependencies (`apisession`, org selection, stop-signal, safe input, site fetch, exporter, progress iterator).
- Unit coverage added in `tests/unit/analytics/test_site_analytics_configurator.py` to validate comparison, confirmation, and apply behavior.

## Conclusion

- Menu routing identifiers and descriptions for operations `7` and `169` are unchanged.
- Runtime invocation now targets extracted modules while preserving operation semantics.
