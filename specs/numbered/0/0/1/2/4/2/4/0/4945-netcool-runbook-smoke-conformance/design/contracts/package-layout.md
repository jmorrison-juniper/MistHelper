# Contract: Package Layout

This contract lists each public name that moves, with its old and new import path. Each call site and each test changes in the same pull request (FR-009). No old path remains after the change, and no alias or shim exists (FR-008).

## Entry point

| Name | Path | Rule |
| - | - | - |
| Command | `python -m scripts.netcool_runbook_smoke` | Unchanged. The entry point stays `scripts/netcool_runbook_smoke/__main__.py`. |
| Session default | `mistapi.APISession` | Stays in `SmokeCommand`, in `__main__.py`. |

## Moved names

| Name | Old import path | New import path |
| - | - | - |
| `SmokeSettings` | `scripts.netcool_runbook_smoke.__main__` | `scripts.netcool_runbook_smoke.settings.smoke_settings` |
| `SettingsLoader` | `scripts.netcool_runbook_smoke.__main__` | `scripts.netcool_runbook_smoke.settings.settings_loader` |
| `EnvFileReader` | `scripts.netcool_runbook_smoke.command` | `scripts.netcool_runbook_smoke.settings.settings_loader` |
| `IdentityRules` | `scripts.netcool_runbook_smoke.__main__` | `scripts.netcool_runbook_smoke.settings.identity_rules` |
| `CheckSequence` | `scripts.netcool_runbook_smoke.__main__` | `scripts.netcool_runbook_smoke.__main__` (unchanged) |
| `SmokeCommand` | `scripts.netcool_runbook_smoke.__main__` | `scripts.netcool_runbook_smoke.__main__` (unchanged) |
| `RunReport` | `scripts.netcool_runbook_smoke.command` | `scripts.netcool_runbook_smoke.__main__` |
| `CallRecord` | `scripts.netcool_runbook_smoke.client` | `scripts.netcool_runbook_smoke.transport.call_record` |
| `PageSet` | `scripts.netcool_runbook_smoke.client` | `scripts.netcool_runbook_smoke.transport.pages` |
| `PageWalker` | `scripts.netcool_runbook_smoke.client` | `scripts.netcool_runbook_smoke.transport.pages` |
| `CallGovernor` | `scripts.netcool_runbook_smoke.client` | `scripts.netcool_runbook_smoke.transport.call_governor` |
| `TimedCall` | not present (new class) | `scripts.netcool_runbook_smoke.transport.timed_call` |
| `ReadOnlyMistClient` | `scripts.netcool_runbook_smoke.client` | `scripts.netcool_runbook_smoke.transport.read_client` |
| `MarkdownTables` | `scripts.netcool_runbook_smoke.documents` | `scripts.netcool_runbook_smoke.reporting.sources` |
| `RunbookClaims` | `scripts.netcool_runbook_smoke.documents` | `scripts.netcool_runbook_smoke.reporting.sources` |
| `OpenApiIndex` | `scripts.netcool_runbook_smoke.documents` | `scripts.netcool_runbook_smoke.reporting.sources` |
| `EvidenceRedactor` | `scripts.netcool_runbook_smoke.documents` | `scripts.netcool_runbook_smoke.reporting.redaction` |
| `EvidenceWriter` | `scripts.netcool_runbook_smoke.documents` | `scripts.netcool_runbook_smoke.reporting.evidence` |
| `TracebackFreeFormatter` | `scripts.netcool_runbook_smoke.command` | `scripts.netcool_runbook_smoke.reporting.logging_setup` |
| `StandardLogging` | `scripts.netcool_runbook_smoke.command` | `scripts.netcool_runbook_smoke.reporting.logging_setup` |
| `LogSetup` | `scripts.netcool_runbook_smoke.command` | `scripts.netcool_runbook_smoke.reporting.logging_setup` |
| `CheckStatus` | `scripts.netcool_runbook_smoke.checks` | `scripts.netcool_runbook_smoke.checks.core.results` |
| `CheckResult` | `scripts.netcool_runbook_smoke.checks` | `scripts.netcool_runbook_smoke.checks.core.results` |
| `StopRun` | `scripts.netcool_runbook_smoke.checks` | `scripts.netcool_runbook_smoke.checks.core.results` |
| `CheckContext` | `scripts.netcool_runbook_smoke.checks` | `scripts.netcool_runbook_smoke.checks.core.context` |
| `EvidenceBuilder` | `scripts.netcool_runbook_smoke.checks` | `scripts.netcool_runbook_smoke.checks.core.context` |
| `SessionOpener` | `scripts.netcool_runbook_smoke.checks.support` | `scripts.netcool_runbook_smoke.checks.core.support` |
| `RequestTrail` | `scripts.netcool_runbook_smoke.checks.support` | `scripts.netcool_runbook_smoke.checks.core.support` |
| `CatalogStore` | `scripts.netcool_runbook_smoke.checks.catalogs` | unchanged |
| `NameComparison` | `scripts.netcool_runbook_smoke.checks.catalogs` | unchanged |
| `CatalogChecks` | `scripts.netcool_runbook_smoke.checks.catalogs` | unchanged |
| `DocumentLoader` | `scripts.netcool_runbook_smoke.checks.identity` | `scripts.netcool_runbook_smoke.checks.identity.loading` |
| `RunbookStructure` | `scripts.netcool_runbook_smoke.checks.identity` | `scripts.netcool_runbook_smoke.checks.identity.loading` |
| `PrivilegeReader` | `scripts.netcool_runbook_smoke.checks.identity` | `scripts.netcool_runbook_smoke.checks.identity.privilege` |
| `UsageReader` | `scripts.netcool_runbook_smoke.checks.identity` | `scripts.netcool_runbook_smoke.checks.identity.usage` |
| `IdentityChecks` | `scripts.netcool_runbook_smoke.checks.identity` | `scripts.netcool_runbook_smoke.checks.identity.identity_checks` |
| `FilterProbes` | `scripts.netcool_runbook_smoke.checks.scope` | `scripts.netcool_runbook_smoke.checks.scope.filters` |
| `ScopeChecks` | `scripts.netcool_runbook_smoke.checks.scope` | `scripts.netcool_runbook_smoke.checks.scope.sites` |
| `SiteListing` | `scripts.netcool_runbook_smoke.checks.scope` | `scripts.netcool_runbook_smoke.checks.scope.sites` |
| `InventoryReader` | `scripts.netcool_runbook_smoke.checks.scope` | `scripts.netcool_runbook_smoke.checks.scope.inventory` |
| `InventoryChecks` | `scripts.netcool_runbook_smoke.checks.scope` | `scripts.netcool_runbook_smoke.checks.scope.inventory` |
| `SearchObservations` | `scripts.netcool_runbook_smoke.checks.searches` | `scripts.netcool_runbook_smoke.checks.searches.observations` |
| `FamilyJudge` | `scripts.netcool_runbook_smoke.checks.searches` | `scripts.netcool_runbook_smoke.checks.searches.families` |
| `CountComparison` | `scripts.netcool_runbook_smoke.checks.searches` | `scripts.netcool_runbook_smoke.checks.searches.counts` |
| `CountVerdict` | `scripts.netcool_runbook_smoke.checks.searches` | `scripts.netcool_runbook_smoke.checks.searches.counts` |
| `SearchChecks` | `scripts.netcool_runbook_smoke.checks.searches` | `scripts.netcool_runbook_smoke.checks.searches.search_checks` |

## Rules

1. Each `__init__.py` file holds no class, no function, and no import of a name from another module.
2. Each moved class keeps its name and its public methods. A new helper method has a leading underscore, unless the helper is public by design.
3. Each module keeps its module logger as `logger = structlog.get_logger(__name__)`.
4. The package logger prefix `scripts.netcool_runbook_smoke` stays in `LogSetup.PACKAGE_LOGGERS` (TEST-10).
5. Each new helper class appears in the table of `plan.md`. A helper class that the table does not name is a defect.
