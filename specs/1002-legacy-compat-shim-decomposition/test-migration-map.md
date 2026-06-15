# Test Migration Map (US3)

## Completed migrations

| Test file | Legacy dependency removed | Canonical replacement |
| - | - | - |
| `tests/unit/test_exports.py` | monkeypatch on `InsightMetricsUtils.export_legacy` | rely on scoped metric lookup (`get_by_scope`) + canonical cache refresh path in runtime |
| `tests/integration/test_mistapi_sdk_compatibility.py` | monkeypatch on `InsightMetricsUtils.export_legacy` | rely on scoped metric lookup (`get_by_scope`) + canonical cache refresh path in runtime |
| `tests/unit/test_no_export_legacy_callsites.py` | none (new guard) | static enforcement of no internal `InsightMetricsUtils.export_legacy(` callsites |

## Remaining migrations (target)

| Test file | Current legacy/facade dependency | Planned migration |
| - | - | - |
| `tests/unit/test_exports.py` | direct facade use: `MistHelper.SiteExportUtils`, `MistHelper.InsightMetricsUtils` | migrate assertions to canonical `src.export.site_export_utils.SiteExportUtils` / local helper functions where possible |
| `tests/unit/test_menu_13_device_stats.py` | direct facade use: `MistHelper.TimeUtils` | migrate to direct canonical helper import once stable module path is locked |
| `tests/guardrails/test_wave1_*` | direct facade use: `MistHelper.OperationRegistry` | migrate to canonical menu registry module when extraction complete |

## Notes

- Full `__init__.py` shim-branch retirement is blocked by missing or not-yet-stabilized canonical module replacements for several facades.
- Continue replacing legacy references in tests first to reduce risk before branch deletion.
