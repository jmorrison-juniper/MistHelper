# Contract: Serial Decomposition Wave 2

## Contract scope
Defines mandatory execution and compatibility rules for decomposition of 9 class clusters from `MistHelper.py`.

## Execution contract
1. Decomposition phases MUST execute in this exact order:
   1. SiteInventoryHealthAnalyzer + SiteAnalyticsConfigurator
   2. TroubleshootUtils + SSHRunnerManager
   3. WAN2MigrationManager + WANProbeDeviceOverrideManager
   4. SiteConfigManager
   5. SiteExportUtils
   6. OrgDeviceInventorySummary
   7. GatewayExportUtils
   8. ServicePingManager
   9. PacketCaptureManager
2. No phase overlap is allowed.
3. Every phase requires hard-gate pass before next phase starts.

## Behavioral compatibility contract
1. Menu option behavior and wording remain unchanged.
2. API interpretation semantics remain unchanged.
3. Output behavior remains unchanged for CSV/SQLite/polyglot paths.
4. Any detected behavior drift blocks progression.

## Dependency/coupling contract
1. `MistHelper.py` acts as orchestration layer only.
2. Extracted modules MUST NOT import menu registry or high-level entrypoint internals.
3. Circular imports are forbidden.
4. Hidden shared mutable state coupling across old/new boundaries is forbidden.

## Phase gate contract
A phase passes only when all are true:
- Tests pass
- Quality commands pass
- Parity checks pass
- Import-cycle checks pass
- Runtime coupling checks pass

## Documentation completion contract
After phase 9, completion requires synchronized and verified updates for:
- `README.md`
- `CHANGELOG.md`
- Mermaid/architecture diagrams
- GitHub wiki pages

All checklist items must pass before final sign-off.
