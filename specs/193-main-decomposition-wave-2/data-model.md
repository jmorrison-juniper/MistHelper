# Data Model: Main decomposition wave 2

## Entity: DecompositionPhase
- **Fields**:
  - `phase_number` (int, 1-9 for decomposition)
  - `name` (string)
  - `source_classes` (list[string])
  - `target_modules` (list[path])
  - `status` (enum: `pending|active|blocked|passed`)
  - `gate_evidence` (PhaseGateEvidence)
- **Validation rules**:
  - Phase ordering must be strict ascending.
  - `status=passed` required before next phase can enter `active`.

## Entity: ModuleExtractionMap
- **Fields**:
  - `source_file` (path, always `MistHelper.py` for this wave)
  - `source_class` (string)
  - `method_clusters` (list[string])
  - `target_module_path` (path)
  - `ownership_state` (enum: `delegated|migrated|canonical`)
- **Validation rules**:
  - Exactly one canonical owner for each migrated method cluster.
  - No duplicate canonical ownership across modules.

## Entity: PhaseGateEvidence
- **Fields**:
  - `tests_passed` (bool)
  - `quality_commands_passed` (bool)
  - `parity_checks_passed` (bool)
  - `import_cycle_check_passed` (bool)
  - `runtime_coupling_check_passed` (bool)
  - `notes` (string)
- **Validation rules**:
  - All booleans must be `true` for phase pass.

## Entity: ParityBaseline
- **Fields**:
  - `menu_paths` (list[string])
  - `api_behavior_contracts` (list[string])
  - `backend_outputs` (list[string], includes CSV/SQLite/polyglot)
  - `status` (enum: `matched|drift_detected`)
- **Validation rules**:
  - Any drift sets phase status to `blocked`.

## Entity: DependencyBoundaryRule
- **Fields**:
  - `rule_id` (string)
  - `allowed_direction` (string)
  - `forbidden_import_patterns` (list[string])
  - `check_command` (string)
- **Validation rules**:
  - Violations are hard-gate failures.

## Entity: DocumentationAuditRecord
- **Fields**:
  - `readme_synced` (bool)
  - `changelog_synced` (bool)
  - `mermaid_synced` (bool)
  - `wiki_synced` (bool)
  - `stale_reference_count` (int)
  - `links_valid` (bool)
- **Validation rules**:
  - Final completion requires all booleans true and `stale_reference_count=0`.
