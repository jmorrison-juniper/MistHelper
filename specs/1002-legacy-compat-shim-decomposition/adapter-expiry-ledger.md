# Adapter Expiry Ledger

| Adapter | File | Introduced | Expiry | Removal Trigger | Owner | Status |
| - | - | - | - | - | - | - |
| Site capture `run()` alias | `src/capture/site_pcap_wait_download_workflow.py` | 2026-06-15 | 2026-08-31 | All tests use `execute()` path; no runtime callers of `run()` | decomposition wave 1002 | active |
| Org capture `run()` alias | `src/capture/org_pcap_wait_download_workflow.py` | 2026-06-15 | 2026-08-31 | All tests use `execute()` path; no runtime callers of `run()` | decomposition wave 1002 | active |
| Menu fallback `_noop_menu_action` | `__init__.py` | pre-existing | TBD (target 2026-08-31) | menu parity gates pass with explicit registry coverage | decomposition wave 1002 | pending review |
| Menu fallback `_ensure_menu_coverage` | `__init__.py` | pre-existing | TBD (target 2026-08-31) | parity + growth-guard tests green in US2 | decomposition wave 1002 | pending review |
