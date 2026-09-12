# Contract: Definition of Done (per file, per initiative)

**Feature**: 1009-compliance-backlog-remediation
**Scope**: The binary predicates that determine whether a single file is "done" and whether the entire initiative is "done".

---

## Per-file done predicate

A `BacklogRow` is retired (state: `Retired`) when ALL of the following hold on a fresh scan produced after its `RemediationPR` squash-merged:

| # | Predicate | Source |
|---|-----------|--------|
| D1 | `ComplianceScan.per_file[path].score >= 94.0` | FR-011 / SC-001 |
| D2 | Analyzer inline-comment coverage on `path` is >= 80% | FR-012 / SC-007 |
| D3 | No `# noqa: STRUCT-*`, `# noqa: CONV-*`, `# type: ignore`, or `# pragma: no cover` marker exists in the file's current text (grep against the file's HEAD) | FR-010 / SC-006 |
| D4 | The matching `RemediationPR` merged with `merge_cmd == "gh pr merge <n> --squash --delete-branch --admin"` and every one of the 13 gates was `pass` at merge time | FR-008 / FR-009 / SC-005 |
| D5 | Diff scope: the merged commit touched exactly one file whose path matched the picked `BacklogRow.path` | FR-003 / SC-004 |
| D6 | Behavior preservation: public signatures, `__all__`, class hierarchies, observable side effects, and test assertions are unchanged relative to the pre-refactor HEAD of the file (spec Out of Scope) | FR-019 |

If ANY predicate fails, the row is not retired. Remediation continues in a follow-up PR that fixes the failing predicate; that follow-up PR occupies the next serial slot (I2).

## Initiative done predicate

The entire initiative is complete (state: `Terminated`) when ALL of the following hold on a fresh recursive scan (`py -m tools.compliance_analyzer src -r -o <out> -q`) produced after the final backlog file's PR squash-merged:

| # | Predicate | Source |
|---|-----------|--------|
| T1 | Every path listed in the most recent `data/compliance_backlog.tsv` has `score >= 94.0` on the fresh scan | FR-018 / SC-001 |
| T2 | The fresh recursive scan's `overall_score` is `>= 94.0` | FR-018 / SC-002 |
| T3 | No file that was at A+ (100.0) at initiative start is below A+ on the fresh scan | FR-017 / SC-003 |
| T4 | The refreshed backlog TSV, produced by re-running the split-parser on the fresh scan, is empty (no sub-A rows) | FR-016 / FR-018 |
| T5 | No open `RemediationPR` remains; the last merged PR's branch is deleted | FR-004 / FR-008 |

If ANY predicate fails, the initiative continues. The operator identifies which predicate is unmet and opens the necessary remediation PRs (which MUST follow the same per-file contract).

## Escalation triggers (initiative pauses, not terminates)

The initiative is paused and reviewed with the compliance owner when:

- **E1**: A file cannot reach A/94.0 via helper extraction + `# WHY:` anchors alone (would require a behavior change). The operator files a separate issue per FR-019, deferring that file's remediation to a non-remediation PR that carries proper review depth.
- **E2**: The analyzer's scoring changes mid-flight (spec Risks: "Analyzer instability"). The operator halts, re-baselines the backlog from a fresh recursive scan, and resumes.
- **E3**: A merged PR silently regresses a previously-A+ file (SC-003 breach detected on refresh). The operator opens a blocker PR to restore A+ before picking any new `BacklogRow`.
- **E4**: The rank-1 file's provenance decision (FR-015) is contested or reversed. The operator halts rank-1 work, records the revised decision, and resumes with the correct action (commit, delete, or relocate).
