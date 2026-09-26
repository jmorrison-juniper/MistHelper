This audit covers slice A, the README and the wiki.

| File | Old claim | New claim | Evidence |
| - | - | - | - |
| `README.md` | Menus 259 through 262 cover 151 unique simple endpoint operations. | Menus 259 through 262 cover 152 unique simple endpoint operations. | `documentation/menu_reference.md` lists 29, 55, 58, and 10 operations for menus 259 through 262. |
| `README.md` | The default SNMP base OID is `.1.3.6.1.4.1.11.2147483646`. | The default SNMP base OID is `.1.3.6.1.4.1.8072.9999.9999`. | `src/metrics_gateway/snmp.py` sets `DEFAULT_BASE_OID = ".1.3.6.1.4.1.8072.9999.9999"`. |
| `README.md` | The quality-gates page holds 14 checks. | The quality-gates page describes the quality gates without a stale count. | `.github/workflows/ci.yml` lists the current gate jobs. |
| `README.md` | No link named the menu API endpoint map. | The documentation table links to `documentation/menu-api/README.md`. | Issue #3411 requires this link. The lead owns that page. |
| `documentation/wiki/Home.md` | MistHelper provides 209 menu-driven operations. | MistHelper provides 269 actionable menu operations. | `documentation/menu_reference.md` states 269 actionable menu entries. |
| `documentation/wiki/Home.md` | The quick links had no menu API endpoint map. | The quick links include `Menu-API-Endpoints`. | Issue #3411 requires this link. The lead owns that page. |
| `documentation/wiki/_Sidebar.md` | The sidebar had no menu API endpoint map. | The sidebar includes `Menu-API-Endpoints`. | Issue #3411 requires this link. The lead owns that page. |
| `documentation/wiki/History.md` | The history page said MistHelper now has 209 actionable menu entries. | The page has a dated status note and states the current 269 actionable entries. | `documentation/menu_reference.md` states 269 actionable menu entries. |
| `documentation/wiki/Development.md` | `MistHelper.py` had 6,169 lines and `src/` held 124,675 lines across 363 files. | `MistHelper.py` has 8,071 lines and `src/` holds 223,491 lines across 621 Python files. | `rtk .venv\Scripts\python.exe -c ...` printed `MistHelper lines 8071`, `src py files 621`, and `src py lines 223491`. |
| `documentation/wiki/Development.md` | The page recommended future extraction to `api_ops/`, `output/`, and `ssh/`. | The page names the current packages `src/api/`, `src/export/`, and `src/ssh/`. | `src/` contains those packages. |
| `documentation/wiki/Testing.md` | The test page described WIP skips and a three-job CI pipeline with `build-and-push`. | The test page says `--test` uses 73 `safe` entries and CI uses separate quality-gate and container-build workflows. | `src/utils/operation_registry.py` and `.github/workflows/ci.yml` define those facts. |
| `documentation/wiki/Troubleshooting.md` | Menus 63 through 65 were WIP and non-stable. | Endpoint drift points to the menu API endpoint map. | `documentation/menu_reference.md` lists menus 63 through 65 as interactive safe. |
| `documentation/wiki/Support.md` | `python MistHelper.py --version` checks the version. | `python MistHelper.py --help` shows supported command-line flags. | `MistHelper.py` argument parser does not define `--version` and does define help through `argparse`. |
| `documentation/wiki/Maps-Manager.md` | Standalone maps documented `MISTAPI_API_TOKEN` and `MISTAPI_ORG_ID`. | Standalone maps uses `mistapi.APISession(env_file=".env")` and `org_id`, `ORG_ID`, or `MIST_ORG_ID`. | `src/maps/maps_manager.py` calls `mistapi.APISession(env_file=env_file)` and `_resolve_org_id()` reads those org variables. |
| `documentation/wiki/Address-Normalization.md` | Menu 61 uses optional address packages and a future threshold variable. | Menu 195 uses installed address packages and reads `ADDRESS_MATCH_THRESHOLD`. | `requirements.txt` lists `usaddress-scourgify` and `rapidfuzz`. `MistHelper.py` menu 195 names `ADDRESS_MATCH_THRESHOLD`. |
| `documentation/wiki/Web-Portal.md` | The portal runs non-destructive operations in menus 1 through 89. | The portal runs operations whose registry category is `safe` or `interactive_safe`. | `web_portal/services/operation.py` sets `PORTAL_RUNNABLE_CATEGORIES = frozenset({"safe", "interactive_safe"})`. |
| `documentation/wiki/Data-Model.md` | The primary key text used shorthand and an example abbreviation. | The primary key text uses full terms and the same strategy names. | `scripts/migrate_sqlite_to_polyglot.py` and tests name `natural_pk`, `composite_pk`, and `auto_increment_with_unique`. |
| `documentation/wiki/SSH-Runner.md` | The SSH runner page used `&` in a feature row. | The SSH runner page uses `and`. | `src/ssh/ssh_runner.py` implements adaptive reading and timeout handling. |

## Open questions

- `documentation/menu-api/README.md` and the wiki page `Menu-API-Endpoints` are not present in this worktree. Issue #3411 says the lead writes them before merge.
