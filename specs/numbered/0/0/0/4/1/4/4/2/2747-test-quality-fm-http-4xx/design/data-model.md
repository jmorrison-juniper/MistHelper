# Data Model: Test quality: repair remaining missing_fm_http_4xx findings

This feature has no product data. The model covers the analyzer records that the triage reads and writes. Each entity names its natural key and its states.

## Entities

### Finding

- **Source**: The `findings` array of the census report (`report.schema.json` in the installed misthelper-devtools package).
- **Natural key**: `rule_id`, `file_path`, and `line_number`.
- **Fields**: `category`, `rule_id`, `severity`, `file_path`, `line_number`, `explanation`, `remediation`, `heuristic`, and `related_source`.
- **Rule of this record**: Only `rule_id` equal to `missing_fm_http_4xx` is in scope.

### BaselineEntry

- **Source**: `.github/test-quality-baseline.json` on `main` (blob 512da22b0769e8343a4b5b734c507d6aa3969ac6).
- **Natural key**: `rule_id`, `file_path`, and `line_number`.
- **Fields**: `category`, `explanation`, `file_path`, `heuristic`, `line_number`, `related_source`, `remediation`, `rule_id`, and `severity`.
- **Counts on `main`**: 733 entries. 38 entries hold `missing_fm_http_4xx`. 42 entries hold `missing_fm_http_5xx` (research R-17).

### StaleBaselineEntry

- **Source**: The `stale_baseline_entries` array of the census report.
- **Meaning**: A baseline entry that matches no current finding.
- **Use**: T004 counts the 4xx stale entries. T012 removes them.

### Family

- **Values**: F1 (real gap), F2 (applicability noise), F3 (coverage miss), and F4 (stale or held).
- **Constraint**: Each triage row holds one family, or the pair F2 and F3 for row 1.
- **Constraint**: An F1 row requires one native 4xx test in its existing module (FR-003).

### TriageRow

- **Fields**: `index`, `baseline_line`, `file_path`, `status_evidence`, `source_import`, `family`, `census_outcome`, and `repair_task`.
- `baseline_line` is the line of the `rule_id` field. `census_outcome` is `present` or `stale`. `repair_task` is T006, T007, T011, T012, or hold.
- **Constraint**: The row count equals the baseline 4xx entry count plus each census finding that has no baseline entry (SC-001).

### RemoteCheck

- **Fields**: `claim`, `path`, `ref`, `blob_sha`, `result` (`present`, `absent`, `partial`, or `stale`), and `line`.
- **Constraint**: The count equals the `remote_checks` array in STATUS and the row count of the research table (85).

### Decision

- **Fields**: `id` (D-1 to D-10), `decision`, and `human_decision_required` (false for every row).

### Task

- **Fields**: `id`, `requirements` (FR and SC identifiers), `paths`, `verification`, `status` (`open`, `verified-present`, `partial`, or `absent`), and `depends`.

## State Transitions

```text
Census finding (rule 4xx, file F, line L)
  matches a BaselineEntry        -> retained (no change)
  matches no BaselineEntry       -> new (the gate fails. Add a TriageRow before merge)

BaselineEntry (rule 4xx)
  matches a census finding       -> retained
  matches no census finding      -> stale -> removed by the T012 write command

Family F1 path
  census finding present         -> T011 adds one native 4xx test -> census rerun -> finding absent
                                    -> stale BaselineEntry -> removed by T012

Family F2 or F3 path
  census finding present         -> T006 or T007 repairs the detector -> T008 release
                                    -> T009 pin -> T010 census rerun -> finding absent
                                    -> stale BaselineEntry -> removed by T012

Held file (FR-013)
  census finding present         -> hold while PR #4208 is open -> no edit
```

## Invariants

- No transition adds a `missing_fm_http_4xx` entry to the baseline. T012 requires zero added entries.
- No transition removes a baseline entry for a rule other than 4xx. T012 restores each such entry.
- Each TriageRow holds one census outcome and one family.
- Each Decision holds `human_decision_required` set to false.
