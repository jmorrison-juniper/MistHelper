# Quickstart: Add explicit gateway role and hardware selection

This guide gives the reproduction steps and the verification commands for issue 4638. Run each command from the repository root in the worktree for `feat/4638-gateway-role-hardware-selection`. Use the environment that `.github/copilot-instructions.md` describes in its Language and environment section.

## Prerequisites

- Issues 4634, 4636, and 4637 merged (T001).
- The worktree has `.venv` from `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`.
- Test data uses synthetic files only. No credential is needed.

## Scenario 1: Reproduce the current gap

On main, the only hardware-like control is the template type select.

1. Open `src/interfaces/portals/cisco_config_converter/presentation/converter.html`.
2. Confirm that lines 14 to 18 define one select with the id `cisco-type`. The options are `standalone` and `spoke`.
3. Confirm that no role, family, model, or port control exists. Search for `cisco-role`, `cisco-family`, `cisco-model`, and `cisco-port-usage`. The search finds no match.
4. Run the current unit test. It passes on main.

`python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`

## Scenario 2: Run the hardware tests before implementation

Before T005 to T007, the seventeen hardware tests fail. The failures show the missing register and mapping modules.

`python -m pytest tests/integration/web_portal/cisco_config_converter/test_hardware.py`

## Scenario 3: Verified standalone review

1. Start the converter route test client with the fixture in `test_routes.py`.
2. Post a synthetic file with the lines `interface GigabitEthernet0/7` and `interface GigabitEthernet0/3`.
3. Post `role` = `standalone`, `family` = `srx`, `model` = `SRX300`, and `ports` = a JSON list with `ge-0/0/7` as `wan` from `GigabitEthernet0/7` and `ge-0/0/3` as `lan` from `GigabitEthernet0/3`.
4. Confirm `hardware.status` = `verified` and `gateway_template.type` = `standalone`.
5. Post the proposal to `/review`. Expect HTTP 200. Post it to `/export`. Expect HTTP 200 and the attachment name `cisco-proposal.json`.

`python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`

## Scenario 4: Blocked selections

1. Post `role` = `branch` with the same synthetic file. Confirm blocker `role_unverified` and no `gateway_template.type`.
2. Post `role` = `hub`. Confirm blocker `role_without_deployment_type`.
3. Post `family` = `ssr` and `model` = `SSR120`. Confirm blocker `port_evidence_absent`.
4. Post `model` = `SRX340`. Confirm blocker `model_without_inventory_sample`.
5. Post `/review` for each blocked proposal. Expect HTTP 409 and the message "Resolve each hardware blocker before review."

`python -m pytest tests/integration/web_portal/cisco_config_converter/test_hardware.py`

## Scenario 5: Invalidation and the retired field

1. Review a verified proposal. Change the model to `SRX320`. Post the earlier proposal to `/export`. Expect HTTP 409.
2. Post the old form with the field `type`. Expect HTTP 400 and the message that names the role field.

`python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`

## Scenario 6: Stable selectors

Read the page from `GET /cisco-config-converter/`. Confirm each `data-testid` value in `contracts/portal-selection.md`, section Stable selectors.

`python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`

## Scenario 7: Gates for the change

Run each gate from the local gates table that applies. The table in `.github/copilot-instructions.md` lists the exact commands (lines 57 to 76 on main).

1. `python -m py_compile MistHelper.py`
2. `python -m ruff check .`
3. `python -m black --check .`
4. `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`
5. `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
6. `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
7. `bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q`
8. `pylint src/ --fail-under=9.5`
9. `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`
10. `pydocstyle src/ wsgi.py web_portal`
11. `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`
12. `symbol-diff --base origin/main src/interfaces/portals/cisco_config_converter/conversion/common/dns.py`
13. `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4638-gateway-role-hardware-selection.md`
