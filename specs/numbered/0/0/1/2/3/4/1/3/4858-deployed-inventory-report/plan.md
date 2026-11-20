# Implementation Plan: Deployed Inventory Report

**Branch**: `fix/4858-deployed-inventory-report` | **Date**: 2026-11-19 | **Spec**: [Feature specification](./spec.md)

## Summary

Fix menu 308 to separate deployed inventory from unassigned stock. Add deployed detail and summary reports. Use paginated Mist inventory data for every authorized organization. Preserve Missing and partial failure states.

The existing 2026-11-11 MSP inventory snapshot recorded 27,030 T-Mobile USA Retail devices. The live menu 308 stock report recorded only 152 stock devices for that organization. The stock report is not a deployed inventory report. The fix must retain both views.

## Technical Context

**Language/Version**: Python 3.15.2

**Primary Dependencies**: mistapi 0.64.1, MistHelper DataExporter, existing subscription report classes

**Storage**: CSV files under `data/` and optional existing SQLite or polyglot mirrors

**Testing**: pytest unit, integration, contract, menu guardrail, and live interactive tests

**Target Platform**: Windows 11, macOS, Linux, and the MistHelper container

**Project Type**: Read-only CLI menu operation with existing web-portal registry integration

**Performance Goals**:
- Reconcile one inventory page of 1000 devices or more
- Follow every continuation page
- Keep one organization read paced at a time
- Preserve an exact count for T-Mobile USA Retail and retail kiosk organizations

**Constraints**:
- Use mistapi SDK inventory calls
- Use no direct HTTP request
- Keep deployed inventory separate from unassigned stock
- Include Virtual Chassis members when the source identifies them
- Preserve Missing for unavailable counts and identity fields
- Continue with visible partial results
- Write formula-safe CSV output

**Scale/Scope**:
- Every organization that the active profile and MSP grants authorize
- Every paginated inventory record visible to the organization
- Deployed inventory and stock inventory as separate entities
- A live T-Mobile USA Retail baseline above 27,000 devices

## Constitution Check

*Gate: Pass before implementation.*

- The feature extends the existing bounded subscription-expiry package.
- The implementation adds no new source package or hierarchy level.
- The fix changes existing package files and adds test rows.
- Menu 308 remains read-only and in the safe category.
- The report writes CSV data to `data/`.
- The inventory source uses mistapi `getOrgInventory`.
- Pagination follows the SDK continuation path.
- Virtual Chassis members remain separate inventory records.
- Missing counts remain Missing instead of false zero values.
- Primary-key strategies cover any new deployed inventory report table.
- The pull request title and commit subject use a Conventional Commits form.
- The change adds one issue change fragment under `changelog.d/`.

No Constitution gate violation requires an exception.

## Project Structure

### Documentation for this feature

```text
specs/numbered/0/0/1/2/3/4/1/3/4858-deployed-inventory-report/
  spec.md
  plan.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      report-contract.md
    checklists/
      requirements.md
```

### Source code

```text
src/mist/intelligence/reports/subscription_expiry/
  client.py
  model.py
  operation.py

src/foundation/support/refactors/endpoint_primary_key_strategies.py
tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/
documentation/cross-org-subscription-stock.md
changelog.d/
```

**Structure Decision**: Extend the existing subscription-expiry report package. Do not create a second inventory package for the same menu 308 subject.

## Complexity Tracking

No Constitution violation is known.
