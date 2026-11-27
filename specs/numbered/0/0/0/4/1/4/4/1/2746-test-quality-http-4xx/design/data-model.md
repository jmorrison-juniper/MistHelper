# Data Model: HTTP 4xx Test-Quality Findings

## Baseline Entry

- **Natural key**: The five-part key from misthelper-devtools: category, rule identifier, file path, line number, and explanation (`baseline.py` lines 1 to 8 and line 49).
- **Fields used**: `rule_id`, `file_path`, and `line_number`. Each `missing_fm_http_4xx` entry in this record has line number 1.
- **Count on main**: 38 entries of `missing_fm_http_4xx` among 733 entries (RC-16).

| State | Meaning | Move to next state |
| - | - | - |
| Accepted | The entry matches a current finding. | Removed by T004 when the entry is class B. Removed by T006 when the entry is class A or class C and the released analyzer omits it. |
| Class B entry | The entry matches no current finding, and its test exists on main. | Removed by T004 after T002 confirms the absence. |
| Absent-file entry | The scan cannot reach the entry file. | Removed by the prune command. No entry in this record uses this state. |

## Finding

- **Natural key**: The same five-part key, taken from a complete report.
- **Fields used**: `rule_id`, `file_path`, and `line_number`.

| State | Meaning |
| - | - |
| Reported | The complete report lists the finding. |
| Classified | The record names the class and the action. |
| Cleared | A later complete report omits the finding. |

## Test Module

- **Natural key**: The repository path on main.
- **Attributes**: Blob SHA on main, class (A, B, or C), evidence line, and the pull request that added the 4xx test, when one exists.
- **Count**: 38 test modules have one baseline entry each (RC-35 to RC-72).

## Upstream Dependency

- **Natural key**: The repository `jmorrison-juniper/misthelper-devtools` and issue number 67.
- **Pinned commit**: `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (RC-13).

| State | Meaning | Move to next state |
| - | - | - |
| Open | Issue #67 is open. | Released after the repair merges. |
| Released | A commit carries the repair. | Pinned in `requirements-dev.txt` by T006. |
| Pinned | `requirements-dev.txt` line 197 names the commit. | Complete report omits the cleared entries. |
