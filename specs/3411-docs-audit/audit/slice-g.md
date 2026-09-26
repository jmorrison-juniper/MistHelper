Slice G covers the NOC runbooks and the CodeQL verdict register.

| File | Old claim | New claim | Evidence |
| - | - | - | - |
| `documentation/security/codeql-verdict-register.md` | The check compares all eleven row fields, including line and anchor. | The check compares every decision field and ignores line-only or anchor-only drift. | `scripts/codeql_verdict_register.py`, `RegisterReconciler._changed_decision_columns`; local read confirmed `POSITIONAL_COLUMNS` are not decision fields. |
| `documentation/security/codeql-verdict-register.md` | The register check job location needed verification. | The job is `CodeQL verdict register check`, and it runs `python scripts/codeql_verdict_register.py check`. | `.github/workflows/ci.yml`; `tests/guardrails/test_codeql_register_gate.py`. |
| `documentation/security/codeql-verdict-register.md` | Register table paths needed verification. | Eighty-six row file paths exist in this tree. Alerts 193 and 194 still name the removed `starlink_dashboard.py` path from the live CodeQL alerts. | Command result: `codeql_rows 88`, `missing_codeql_paths 2`; `gh api` returned path `starlink_dashboard.py` for alerts 193 and 194. |
| `documentation/noc-runbooks/*.md` | The runbooks might name stale MistHelper menu numbers or titles. | The runbooks do not name exact MistHelper menu numbers. No menu-number edit was required. | Command result: `rg "Menu [0-9]\|menu [0-9]\|option [0-9]\|#[0-9]{2,3}" documentation\noc-runbooks` returned no matches. |
| `documentation/noc-runbooks/*.md` | The runbooks might contain broken relative Markdown links. | All relative Markdown links in the runbooks resolve in this tree. | Command result: `missing_links 0`. |
| `documentation/noc-runbooks/*.md` | WebSocket command rows needed verification against the current menu registry. | WebSocket menu entries are options 102 through 123 with the titles in `documentation/menu_reference.md`. | `MistHelper.py` `menu_actions`; `documentation/menu_reference.md`; command result: `count=270 min=0 max=270 missing=[152]`. |

## Open questions

- None.
