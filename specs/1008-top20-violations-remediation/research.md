# Phase 0 Research: Top-20 Compliance Violations Remediation

**Date**: 2026-07-02
**Feature**: Top-20 Compliance Violations Remediation
**Baseline**: `compliance_report.md` regenerated 2026-07-02; overall repo score 89.8/100
(B+); 554 files analyzed.

## Decisions

### D-001: Ordering strategy - worst-first (rank 1 -> rank 20)

- **Decision**: PRs merge in strict rank order 1 -> 20, so the file with the largest
  violation count merges first.
- **Rationale**: (1) maximizes early gain on repo-wide score (SC-002 requires +2.0
  points minimum); (2) removes the loudest offenders from the "worst files" list
  quickly; (3) prevents late-initiative churn if analyzer weights shift; (4) matches
  the pattern of PRs #578-#583 which addressed the largest files in their tier first.
- **Alternatives considered**:
  - *Easy-first (rank 20 -> rank 1)*: Rejected. Delivers small early wins but leaves
    the worst files exposed longest, contrary to SC-002 impact target.
  - *Alphabetical*: Rejected. No relationship to score impact; arbitrary.
  - *Cluster by directory*: Rejected. Would batch `src/maps/*` together but skew the
    initiative's cadence and delay the P2/P3 wins that clear D and C grades.

### D-002: A+/>=95.0 is a hard gate, not "best effort"

- **Decision**: Every PR MUST clear score >=95.0 (grade A+). Anything below is a
  non-merge event; the PR is either rescoped, split, or escalated to human review.
- **Rationale**: FR-001 and SC-001 contractually require it. The alternative -
  "accept 93.0 if we tried our best" - creates a slippery-slope where subsequent PRs
  reference the earlier deviation as precedent.
- **Alternatives considered**:
  - *Grade A (>=93.0) floor*: Rejected. Spec explicitly says A+/>=95.0.
  - *Per-tier floor (A+ for P1, A for P2, A- for P3)*: Rejected. Introduces
    complexity and undermines the "close out the top-20" success criterion (SC-008).

### D-003: `pathlib` preferred over `os.path.join` for new helper code

- **Decision**: New helpers extracted during refactor use `pathlib.Path`. Existing
  `os.path.join` usage is preserved where behaviorally correct (touching only lines
  that also have other refactor changes).
- **Rationale**: Constitution Technology Constraints allow both, but `pathlib` is more
  readable and less error-prone. Existing `os.path.join` is not a violation - the
  analyzer flags hard-coded separators (`/`, `\\`) only.
- **Alternatives considered**:
  - *Force-migrate all `os.path.join` -> `pathlib`*: Rejected. Expands scope beyond
    the touched lines and risks behavior changes.

### D-004: Split modules >500 LOC only when a natural boundary exists

- **Decision**: For target files that remain >500 LOC after internal decomposition,
  split into sibling modules named for the real responsibility being extracted. Do
  not split when the split would require leaving a wrapper/delegator in the old
  location.
- **Rationale**: Constitution II forbids wrappers. FR-007 forbids thin forwarders at
  the old symbol location. Splitting for its own sake without a clean callsite
  update is a wrapper in disguise.
- **Alternatives considered**:
  - *Split every file that exceeds 500 LOC*: Rejected - forces wrappers on files
    with tightly coupled internals.
  - *Never split, decompose in place*: Rejected - `maps_manager.py` at 7243 LOC will
    never reach A+ in one file if the analyzer's per-file metrics include size or
    top-level symbol count.

### D-005: Wrappers/delegators/aliases/shims are strictly forbidden - no exceptions

- **Decision**: If a target file's structure appears to need a thin forwarder to
  preserve import compatibility, the correct action is to update the importing
  callsites in the same PR, not to leave a forwarder. Callsite changes that are
  strictly required by the move are permitted by FR-007 provided they hit the real
  new home directly.
- **Rationale**: Constitution II is a non-negotiable principle. Wrappers hide
  responsibility and pollute the class-based architecture.
- **Alternatives considered**:
  - *Deprecation forwarders*: Rejected - creates a two-step migration and violates
    Constitution II.

### D-006: Log calls use lazy `%` formatting

- **Decision**: All log calls touched during a refactor are converted to
  `logging.info("count=%d", count)` form. Untouched log calls are left alone (do not
  expand PR scope).
- **Rationale**: Constitution VII explicitly requires `%s` style formatting.
  Analyzer's `LOG-LAZY` rule enforces this.
- **Alternatives considered**:
  - *Sweep all f-string logs in a file*: Rejected - inflates diff size and risks
    accidental behavior change on log messages that carry data downstream.

### D-007: Inline WHY comments on every touched line

- **Decision**: Every line the refactor introduces or modifies gets a same-line
  comment explaining WHY the line exists. Adjacent uncommented lines in the same
  touched block also get comments (Constitution VI explicit rule).
- **Rationale**: Constitution VI is non-negotiable. The analyzer's inline-comment
  rules encode this at the AST level.
- **Alternatives considered**:
  - *Comments only on non-obvious lines*: Rejected - "obvious" is subjective;
    Constitution mandates every executable line.

### D-008: Test file refactors preserve test IDs and coverage

- **Decision**: `tests/unit/test_arango_writer.py` is refactored by splitting large
  parametrizations, extracting fixtures, and grouping scenarios - not by deleting
  tests or weakening assertions.
- **Rationale**: FR-006 requires identical test outcomes. Assumption in spec.md line
  154 restates this.
- **Alternatives considered**:
  - *Rewrite for coverage equivalence but different test IDs*: Rejected - CI job
    names reference test IDs; changing them creates orphan status checks.

### D-009: Codemod tool refactor requires a round-trip test

- **Decision**: `tools/codemod_logging_lazy.py` is a codemod that transforms other
  files. Its refactor PR includes a round-trip regression: run the pre-refactor
  codemod against a corpus, save the output, refactor, run the post-refactor codemod
  against the same corpus, `diff` the two - MUST be byte-identical.
- **Rationale**: FR-006 requires observable behavior parity; for a codemod, output
  bytes ARE the behavior. Spec Acceptance Scenario 2 in User Story 3 codifies this.
- **Alternatives considered**:
  - *Rely on unit tests only*: Rejected - unit tests may not cover every
    transformation edge case the codemod handles in practice.

## Per-file predicted class-of-fix mix

Derived from the current violation category breakdown in `compliance_report.md` and the
patterns observed in PRs #578-#583. Each file's dominant categories drive the primary
fix template.

| Rank | File | Grade | Violations | Predicted primary fix classes |
|------|------|-------|------------|------------------------------|
| 1  | `src/maps/maps_manager.py`                        | F  | 149 | Module split (7243 LOC), function decomposition, class extraction, inline-comment sweep, `LOG-LAZY` conversion |
| 2  | `src/maps/launcher/viewer_callbacks.py`           | F  | 96  | Callback decomposition (Plotly event handlers), state extraction, complexity reduction |
| 3  | `src/capture/packet_capture.py`                   | F  | 68  | Threading lifecycle refactor, resource-management extraction, safe-input hardening |
| 4  | `src/network/routing_utils.py`                    | F  | 67  | Long-function decomposition, portable-path adoption where hard-coded seps exist |
| 5  | `src/device/utility_commands.py`                  | F  | 65  | Destructive-op confirmation review (menu 90-100 territory), function split |
| 6  | `src/ssid_consolidation/ssid_template_consolidation.py` | F  | 53 | Iteration/aggregation function decomposition, inline comments |
| 7  | `scripts/mist_ideas_analyzer.py`                  | F  | 46  | Script-to-class extraction; extract business logic into `src/` if reused |
| 8  | `tests/unit/test_arango_writer.py`                | D- | 39  | Fixture extraction, parametrize split; preserve test IDs |
| 9  | `scripts/mist_ideas_distiller_v2.py`              | F  | 34  | Same pattern as rank 7 |
| 10 | `src/gateway/wan2_variable.py`                    | D- | 32  | Variable-substitution logic decomposition, `LOG-LAZY` |
| 11 | `src/audit/renderer.py`                           | D- | 29  | Template-render function split, inline comments |
| 12 | `src/site/site_config_manager.py`                 | D  | 29  | Config-mutation function split, safety guards preserved |
| 13 | `starlink_dashboard.py`                           | D  | 28  | Root-level script -> extract to `src/`, minimal `__main__` if externally referenced |
| 14 | `src/analytics/zone_analyzer.py`                  | D  | 26  | Aggregation/statistics function decomposition |
| 15 | `src/inventory/csv_comparator.py`                 | D  | 26  | Diff-comparison function decomposition; portable paths |
| 16 | `src/device/prompt_utils.py`                      | D  | 25  | Prompt-parsing decomposition; `safe_input` review |
| 17 | `src/gateway/template_config.py`                  | D  | 25  | Config-template function split |
| 18 | `tools/codemod_logging_lazy.py`                   | D- | 23  | Codemod visitor decomposition; round-trip regression test |
| 19 | `src/reports/e911_bssid.py`                       | D  | 23  | Report-generation function split, `LOG-LAZY` |
| 20 | `scripts/menu_regroup.py`                         | C  | 22  | Script-to-class extraction; extract to `src/` if reused |

## Known-tricky patterns (recurring lessons from PRs #578-#583)

1. **`mistapi` session lifecycle**: `firmware_manager.py` (#580) surfaced the pattern
   that `mistapi.APISession` context is held across long-running orchestration
   loops. Extracting helpers that "just take the session" is preferred over
   wrappers that reconstruct it.
2. **Bulk-operation progress reporting**: `bulk_ap_upgrader.py` (#579) and
   `org_ap_upgrader.py` (#581) both needed a `ProgressReporter` class extracted from
   inline print/log calls. Reuse that pattern where applicable in `maps_manager.py`
   long-running operations.
3. **Menu-item entry points**: `site_auto_upgrade.py` (#582) preserved the module
   `__main__` behavior by keeping only the CLI parser + a single dispatch call at
   module top-level, moving all business logic into a class.
4. **Confirmation prompts for destructive ops**: `device/utility_commands.py` is
   likely to contain menu 90-100 destructive operations. The refactor MUST retain
   the typed-confirmation pattern (`safe_input("Type 'X' to proceed: ")`) unchanged.
5. **Plotly callback event tangles**: `viewer_callbacks.py` (rank 2) is expected to
   contain deeply nested Dash callback handlers. Prior experience refactoring Plotly
   callbacks: extract state machines into a dedicated class, keep callback signatures
   as thin dispatch to that class's methods.
6. **Large data literals**: `maps_manager.py` may contain map-tile or color-palette
   data literals that the analyzer flags for line count. These are moved to a
   sibling `_data.py` (or `_constants.py`) module when isolation is clean.

## Import-graph edges among the twenty target files

Preliminary analysis of the import graph (to be verified by `grep -R "from src\.maps"`
style checks during Phase 2 task generation):

- `src/maps/launcher/viewer_callbacks.py` (rank 2) imports from
  `src/maps/maps_manager.py` (rank 1). Rank 1 merges first; rank 2 rebases.
- `src/gateway/wan2_variable.py` (rank 10) and `src/gateway/template_config.py`
  (rank 17) likely share helpers in `src/gateway/`. Sequential merge (10 first)
  should avoid conflict.
- `scripts/mist_ideas_analyzer.py` (rank 7) and `scripts/mist_ideas_distiller_v2.py`
  (rank 9) may share helper functions. Rank 7 merges first; if helpers are extracted
  to `src/`, rank 9 imports them from their new home.
- `tests/unit/test_arango_writer.py` (rank 8) has no runtime callers; its refactor
  cannot break any of the other 19 files.
- `tools/codemod_logging_lazy.py` (rank 18) is a codemod - it does not appear at
  runtime, so its refactor does not affect the other 19.

## Open items (none - all NEEDS CLARIFICATION resolved)

No NEEDS CLARIFICATION items remain. Every technical unknown flagged during plan
drafting has been resolved above.
