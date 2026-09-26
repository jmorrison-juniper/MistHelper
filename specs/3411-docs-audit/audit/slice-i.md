# Slice I documentation audit

Slice I covers the other root files, the platform documents, and the tool README files.

| File | Old claim | New claim | Evidence |
| - | - | - | - |
| `SECURITY.md` | The policy had no supported-version rule. | The policy supports `main` and the latest tagged release. | `pyproject.toml` has version `2.1.0`. `git tag --sort=-creatordate` shows `v26.05.21.19.37` as the latest release tag. |
| `PHASE1_COMPLETION_REPORT.md` | The report read like current implementation status. | The report is historical, and current issue #1823 facts live in `src/upgrade_portal/` and `specs/1823-upgrade-capture-portal/`. | `glob src/upgrade_portal/**` found 138 paths. `glob specs/1823-upgrade-capture-portal/**` found 35 paths. |
| `PHASE1_EXECUTION_REPORT.md` | The report read like current work status. | The report is historical, and the current files are `src/maps/plotly_map_templates.py` and `tests/maps/test_plotly_map_templates.py`. | `glob` confirmed both paths exist. |
| `fiber-optic-catalog.md` | The document did not state whether MistHelper reads it. | It is a planning reference, and no MistHelper Python file reads it at run time. | `rg "fiber-optic-catalog" .` found only `HANDOFF.md` and the catalog files. |
| `network-node-device-catalog.md` | The document did not state whether MistHelper reads it. | It is a planning reference, and no MistHelper Python file reads it at run time. | `rg "network-node-device-catalog" .` found only `HANDOFF.md` and the catalog file. |
| `refactor_candidates.md` | The report used an old worktree path, old file counts, and old line ranges. | It now gives relative paths and current line ranges for `GlobalImportManager` and `menu_actions`. | AST measurement reported `GlobalImportManager` lines 1083-2306 and `menu_actions` lines 3690-6165. |
| `mist-ops-platform/docs/architecture.md` | The API layer listed rate limiting and authentication as middleware. | It now states that structured logging is middleware, and authentication plus rate limiting run through dependencies. | `mist-ops-platform/src/api/main.py` mounts `StructuredLoggingMiddleware`. `mist-ops-platform/src/api/deps.py` calls `get_org_rate_limiter()`. |
| `mist-ops-platform/docs/operations.md` | Quick start used a Compose command without the actual file path. | Quick start uses `docker compose -f deploy/compose.yml`. | `mist-ops-platform/deploy/compose.yml` is the compose file. |
| `mist-ops-platform/docs/operations.md` | The metrics endpoint was documented as current Prometheus metrics. | The endpoint is reserved and returns 501 until real series exist. | `mist-ops-platform/src/api/routes/health.py` defines `/metrics` and raises 501. |
| `mist-ops-platform/docs/ruff-ratchet.md` | The full configuration reported 393 findings from an old commit. | The full configuration reports 394 findings from commit `16e5d560`. | `ruff check . --statistics` under `mist-ops-platform` reported `Found 394 errors.` |
| `tools/ste_linter/README.md` | The option table omitted `--config` and `--version`. | The option table includes both options. | `tools/ste_linter/cli.py` adds `--config` and `--version`. |
| `tools/test_quality_analyzer/README.md` | The README said a console script is registered in `pyproject.toml`. | The README says the local tree runs with `python -m tools.test_quality_analyzer`. | `pyproject.toml` says issue #3404 removed the tool script entries. |

## Open questions

None.
