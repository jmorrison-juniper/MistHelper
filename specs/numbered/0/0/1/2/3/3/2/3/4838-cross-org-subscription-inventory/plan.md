# Implementation Plan: Cross-Org Subscription and Stock Inventory Report

**Branch**: `feat/4838-cross-org-subscription-stock-report`
**Date**: 2026-11-19
**Spec**: [Feature specification](./spec.md)

## Summary

Add menu 308 as one read-only operation for MSP-wide renewal data.
The operation discovers accessible organizations, reads subscriptions and usage, reads inventory and JSI evidence, joins stock devices by serial, and exports linked CSV reports.
The implementation extends the existing subscription-expiry report package.
It also uses the migrated MistOrgLicensingComparison workflow and purchase-balancing concepts as inspiration.

## Technical Context

**Language/Version**: Python 3.15.2

**Primary Dependencies**: mistapi 0.64.1, MistHelper DataExporter, existing subscription report classes

**Storage**: CSV files under `data/` and optional existing SQLite or polyglot mirrors

**Testing**: pytest unit, integration, contract, and menu guardrail tests

**Target Platform**: Windows 11, macOS, Linux, and MistHelper container

**Project Type**: Read-only CLI menu operation with existing web-portal registry integration

**Performance Goals**:
- One paced request at a time
- Paginate inventory with 1000 records per page
- Paginate JSI records with the supported limit and search cursor
- Bound HTTP 429 handling to one retry after 60 seconds

**Constraints**:
- No direct HTTP when a mistapi SDK method exists
- No destructive Mist Cloud write
- No API token or password in CSV, console text, or logs
- Continue with visible partial results when one organization fails
- Keep one organization as the direct-access fallback

**Scale/Scope**:
- All organizations that the active profile and MSP grants authorize
- Every subscription record available to the organization
- Every inventory record visible to the organization
- JSI evidence matched by serial number

## Constitution Check

*Gate: Pass before implementation.*

The feature uses the existing `src/mist/intelligence/reports/subscription_expiry/` package.
The package adds no new source module or new hierarchy level.
The implementation changes existing package files and adds no compatibility adapter.
The menu row is read-only and belongs in the `safe` category.
The report writes only local CSV or database evidence.
Every source request uses supported mistapi methods.
One HTTP 429 retry waits 60 seconds and no other response is retried.
Tests cover organization authorization, pagination, failures, output shape, and secret redaction.
The required menu, registry, primary-key, and documentation updates remain in the feature manifest.
The process specification uses the existing managed numeric route.

No Constitution gate violation needs an exception.

## Project Structure

### Documentation for this feature

```text
specs/numbered/0/0/1/2/3/3/2/3/4838-cross-org-subscription-inventory/
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
  __init__.py
  client.py
  model.py
  operation.py

src/foundation/support/utils/operation_registry.py
src/foundation/support/refactors/endpoint_primary_key_strategies.py
MistHelper.py
web_portal/menu_registry.py
documentation/
changelog.d/
tests/
```

**Structure Decision**: Extend the existing bounded subscription-expiry package.
Do not create a second report package for the same subscription subject.
Keep client, model, and operation responsibilities in the existing public package.

## Phase 0: Research

Research decisions are recorded in [research.md](./design/research.md).
The live T-Mobile Validation Lab account produced 41 license records, 48 usage rows, 79 inventory records, and one unassigned SSR130.
The live active token could read the direct organization.
The live active token could not list MSP organizations or MSP licenses with HTTP 403.
Interactive MSP authentication is therefore the expected path for a complete all-org run.

## Phase 1: Design

The normalized data model is recorded in [data-model.md](./design/data-model.md).
The CLI and output contract is recorded in [report-contract.md](./design/contracts/report-contract.md).
The local and live validation guide is recorded in [quickstart.md](./design/quickstart.md).

## Complexity Tracking

No Constitution violation is known.
