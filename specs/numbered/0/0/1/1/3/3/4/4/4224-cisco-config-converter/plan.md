# Implementation Plan: Mist Cisco Config Converter

**Branch**: `jmorrison-juniper-4224-cisco-config-converter` | **Date**: 2026-10-18 | **Spec**: [spec.md](spec.md)

**Input**: Numeric feature specification from `/specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md`

## Summary

Build an isolated preview and export slice for Cisco IOS text. Convert only global IPv4
`ip name-server` directives to Mist `dns_servers`, accept template types `standalone` and
`spoke`, and show unsupported input. Do not make a cloud change in this release.

## Technical Context

**Language/Version**: Python 3.13 or newer, with HTML and JavaScript for the existing portal.

**Primary Dependencies**: Flask and the existing portal. Preview and export do not use the Mist SDK.

**Storage**: No new database or Redis service. Process uploads in memory and return exports as downloads.

**Testing**: pytest for unit and integration coverage, plus the existing Playwright browser suite for the portal.

**Target Platform**: The existing MistHelper web portal on Windows 11, macOS, Linux, and the product container.

**Project Type**: Flask web application integrated with the MistHelper runtime.

**Performance Goals**: Limit uploaded files to 16 MiB and multipart overhead to 16 KiB. This feature adds no separate latency target.

**Constraints**: Accept `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, and `.log` files. Decode UTF-8 strictly, reject path-like names, and process uploads in memory. Preserve unsupported commands. Use original code and public contracts only. Do not copy protected source material. Do not add a database, Redis service, or Compose group. Do not implement cloud apply in this release.

**Scale/Scope**: One operator at a time per browser session. The first release handles global IPv4 `ip name-server` commands and template types `standalone` and `spoke`. Require a template name with 1 to 120 non-whitespace characters. Do not map hardware roles or models.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Managed specification route**: Pass. This record uses the required eight-level base-5 route for issue 4224.
- **Process-folder policy**: Pass. The feature record is under `specs/numbered/` and adds no unmanaged direct child to `specs/`. Keep the process-folder baseline guard readable and use its incremental ratchet for later folder cleanup.
- **Five-item structure rule**: Keep the feature package at five direct children or fewer. Do not add a child to an overfull parent. Place unit tests in the existing gateway overrides test directory and route tests in the feature integration package.
- **Existing structure debt**: The repository has established overfull test and portal directories. This feature must not increase their direct-child counts. Track existing debt through the process-folder and nested-package guard baselines. Remediate it separately.
- **Mist API contract**: The OpenAPI and installed SDK verify `createOrgGatewayTemplate(mist_session, org_id, body)`. This contract is documentation only in this release and does not authorize cloud apply.
- **Safety and secrets**: Preview and export make no cloud request and write no configuration file. Do not log credentials or store them in client-side state.
- **Class-based architecture**: Keep parsing, conversion, routes, and browser behavior in semantically named classes. Do not add standalone behavior wrappers.
- **Inline comments and action logging**: Follow the constitution for generated executable lines, meaningful action logs, ASCII log output, and secret exclusion.
- **Compatibility**: Integrate the Cisco blueprint and navigation entry through the shared portal. Reconcile edits to shared portal files with their current owner before implementation changes are published.
- **Deployment**: Add no service, volume, network, database, Redis instance, or Compose group.
- **Release notes**: The issue-specific fragment is `changelog.d/issue-4224-cisco-config-converter.md`.
- **Workflow scope**: Implement preview, review, export, and portal registration. Keep cloud apply deferred.

No constitution violation is required by this plan. Use original implementation and verified public contract facts. SDK verification is complete, but cloud apply is deferred.

## Phase 0: Research

See [research.md](research.md). The design uses original conversion rules, in-memory upload handling, and verified public schema facts. Cloud apply remains deferred.

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/portal.md](contracts/portal.md), [contracts/mist-apply.md](contracts/mist-apply.md), and [quickstart.md](quickstart.md).

### Project Structure

#### Documentation (this feature)

```text
specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/
├── checklists/requirements.md
├── contracts/
├── data-model.md
├── plan.md
├── quickstart.md
├── research.md
├── spec.md
└── tasks.md
```

#### Source Code

```text
src/interfaces/portals/cisco_config_converter/
├── __init__.py
├── conversion.py
├── models.py
├── routes.py
└── presentation/
    ├── converter.html
    └── converter.js

web_portal/
├── app.py
└── templates/
    └── base.html

tests/unit/gateway/overrides/
└── test_cisco_config_converter.py

tests/integration/web_portal/cisco_config_converter/
├── __init__.py
├── test_routes.py
└── test_sdk_contract.py

tests/e2e/web_portal/
└── test_portal_smoke.py
```

Keep the feature package at five direct children. Keep its page and script in the presentation directory and expose them through its blueprint. Extend the existing portal smoke test instead of adding a child under the overfull browser-test directory.

**Structure Decision**: Keep parsing, conversion, models, routes, and presentation in one feature-owned package under `src/interfaces/portals/`. Test the blueprint in an isolated Flask app. Reconcile shared portal registration and browser acceptance with the owner of those files before publishing implementation changes.

## Complexity Tracking

No complexity exception is proposed. Keep each feature package at five direct children or fewer. Use existing portal services and test fixtures rather than adding another service layer or runtime.

## Implementation Gates

1. Use original code and verified public contract facts only.
2. Enforce the 16 MiB upload boundary, allowed suffixes, strict UTF-8, and in-memory processing.
3. Convert only global IPv4 `ip name-server` commands to `dns_servers`.
4. Accept only template types `standalone` and `spoke`. Do not infer hardware mappings.
5. Reconcile edits to shared portal files with their current owner before implementation changes are published.
6. Prove preview and export need no credentials, make no Mist request, and write no configuration file.
7. Keep cloud apply deferred until it has separate scope and approval.
