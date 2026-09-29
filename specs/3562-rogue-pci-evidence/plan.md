# Implementation Plan: Rogue PCI Evidence Pack

**Branch**: `3562-rogue-pci-evidence` | **Date**: 2026-09-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/3562-rogue-pci-evidence/spec.md`

## Summary

Add menu 282 as a safe operation that writes a rogue wireless PCI evidence pack. The implementation uses a new package under `src/reports/rogue_pci_evidence/` with a Mist API client, pure model builders, and one operation entry point. Menu wiring and database key registration stay deferred to [wiring.md](./wiring.md).

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, standard library `csv`, `dataclasses`, `datetime`, `logging`, `pathlib`, and existing MistHelper helpers.

**Storage**: Local files under `data/` through `DataExporter.write_with_format_selection()` for CSV output. The Markdown summary uses `FilePathUtils.get_data_path()` and `pathlib.Path`.

**Testing**: `pytest` unit tests under `tests/unit/reports/rogue_pci_evidence/`. Tests use fixtures and no network.

**Target Platform**: Windows local worktree and the MistHelper container runtime.

**Project Type**: Menu-driven CLI operation with shared export backends.

**Performance Goals**: The site setting pass makes one `getSiteSetting` request per site. The shared adaptive pacer runs before each site setting request.

**Constraints**: The operation is read-only against Mist. It does not prompt in `--test` mode. It must not log secrets. It must write all evidence under `data/`.

**Scale/Scope**: One organization, all organization WLANs, all organization sites, all site rogue AP rows, and available rogue event rows for the run window.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Five-Item Rule: Pass. The feature adds a compliant nested package with four module files.
- Class-Based Architecture: Pass. `RoguePciEvidencePack`, `RoguePciEvidenceClient`, and model dataclasses own behavior.
- Safety-First: Pass. The operation is read-only and uses the existing organization resolver.
- Full Deployment Pipeline: Pass by fleet contract. Local gates run before each implementation commit.
- Observability and Logging: Pass. Client and operation modules log before and after each action.
- Inline Comments: Pass. New code will include inline comments on executable lines.
- Action Logging: Pass. The client logs API calls, and the operation logs file writes.

## Project Structure

### Documentation (this feature)

```text
specs/3562-rogue-pci-evidence/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── wiring.md
├── contracts/
│   └── evidence-pack.md
└── tasks.md
```

### Source Code (repository root)

```text
src/reports/rogue_pci_evidence/
├── __init__.py
├── client.py
├── model.py
└── operation.py

tests/unit/reports/rogue_pci_evidence/
├── __init__.py
├── test_rogue_pci_evidence_client.py
├── test_rogue_pci_evidence_model.py
└── test_rogue_pci_evidence_operation.py
```

**Structure Decision**: Use one new report package and one matching unit test directory. The package keeps API access, pure data logic, and the menu entry point separate.

## Complexity Tracking

No constitution violation is planned.

## Phase 0 Research Output

See [research.md](./research.md).

## Phase 1 Design Output

See [data-model.md](./data-model.md), [contracts/evidence-pack.md](./contracts/evidence-pack.md), and [quickstart.md](./quickstart.md).

## Post-Design Constitution Check

- Five-Item Rule: Pass. The package has four files, and tests have four files.
- Class-Based Architecture: Pass. No standalone wrappers are planned.
- Safety-First: Pass. The operation reads only Mist data and writes local files.
- Observability and Logging: Pass. Each API call and file write has before and after logs.
- Inline Comments: Pass. Tasks require inline comments for all new executable lines.
- Action Logging: Pass. Tasks require logs around meaningful actions.

