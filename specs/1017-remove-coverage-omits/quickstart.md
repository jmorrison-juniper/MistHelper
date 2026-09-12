# Quickstart: Per-Story Verification Recipes

**Feature**: 1017-remove-coverage-omits
**Refs**: #878

Run these commands to verify a given PR meets the exit criteria before requesting review. All commands assume repo root as CWD and a Python 3.13 venv activated (or `uv run` prefix).

## Setup (once per shell)

```bash
python -m venv .venv && source .venv/bin/activate  # or use uv/existing .venv
pip install -e .[dev]
```

## PR-1 — Utilities (4 modules)

```bash
# Per-file coverage
pytest --cov=src.utils.environment_utils \
       --cov=src.utils.filter_operator_engine \
       --cov=src.troubleshooting.troubleshoot_utils \
       --cov=src.input.prompt_client_utils \
       --cov-report=term-missing \
       --cov-fail-under=90 \
       tests/unit/utils/ tests/unit/troubleshooting/ tests/unit/input/

# Full suite still passes
pytest --cov --cov-fail-under=90

# pyproject omit removed
grep -c "src/utils/environment_utils.py" pyproject.toml    # -> 0
grep -c "src/utils/filter_operator_engine.py" pyproject.toml  # -> 0
```

## PR-2 — Export helpers (5 modules)

```bash
pytest --cov=src.export.org_export_utils \
       --cov=src.export.license_export_utils \
       --cov=src.export.const_definitions_exporter \
       --cov=src.export.gateway_test_exporter \
       --cov=src.export.data_exporter \
       --cov-report=term-missing \
       --cov-fail-under=90 \
       tests/unit/export/
```

## PR-3 — API / DB / analytics (7 modules)

```bash
pytest --cov=src.api --cov=src.cache --cov=src.db --cov=src.analytics \
       --cov-report=term-missing --cov-fail-under=90 \
       tests/unit/api/ tests/unit/cache/ tests/unit/db/ tests/unit/analytics/

# Verify shared fixture landed in tests/conftest.py
grep -n "def mock_mistapi_session" tests/conftest.py
grep -n "def mock_config" tests/conftest.py
```

## PR-4a / PR-4b — Org exporters (3 + 4 modules)

```bash
# PR-4a
pytest --cov=src.export.org_device_stats_exporter \
       --cov=src.export.org_template_exporter \
       --cov=src.export.org_admin_exporter \
       --cov-fail-under=90 tests/unit/export/

# Verify golden-file conftest introduced
grep -n "def golden_json_writer\|def golden_csv_writer" tests/unit/export/conftest.py

# PR-4b
pytest --cov=src.export.org_config_exporter \
       --cov=src.export.org_alarm_event_exporter \
       --cov=src.export.org_client_security_exporter \
       --cov=src.export.org_site_exporter \
       --cov-fail-under=90 tests/unit/export/
```

## PR-5a / PR-5b — Site exporters + reports + inventory (5 + 5 modules)

```bash
# PR-5a
pytest --cov=src.export.site_anomaly_exporter \
       --cov=src.export.site_config_exporter \
       --cov=src.export.site_device_exporter \
       --cov=src.export.sites_by_ap_model_exporter \
       --cov=src.gateway.gateway_ha_exporter \
       --cov-fail-under=90 tests/unit/export/ tests/unit/gateway/

# PR-5b
pytest --cov=src.reports --cov=src.inventory.org_device_inventory_summary_facade \
       --cov-fail-under=90 tests/unit/reports/ tests/unit/inventory/
```

## PR-6 — State-changing managers (5 modules, Principle III)

```bash
pytest --cov=src.device.arp_command_manager \
       --cov=src.device.device_reboot_manager \
       --cov=src.firmware.firmware_manager \
       --cov=src.site.bulk_radius_wlan_config_manager \
       --cov=src.org.org_ticket_manager \
       --cov-fail-under=90 \
       tests/unit/device/ tests/unit/firmware/ tests/unit/site/ tests/unit/org/

# Confirm accept AND reject paths present for every manager
grep -rn "confirmation.*UPGRADE\|reject\|early-return\|early_return" \
  tests/unit/device/ tests/unit/firmware/ tests/unit/site/ tests/unit/org/
```

## PR-7 — SSH / TUI / prompt (3 modules, FR-015 candidates)

```bash
pytest --cov=src.ssh.cli_shell_manager \
       --cov=src.ui.tui \
       --cov=src.ui.prompt_utils \
       --cov-fail-under=90 \
       tests/unit/ssh/ tests/unit/ui/

# Verify at most 2 escape-hatch omits added (FR-015)
python -c "
import tomllib, pathlib
data = tomllib.loads(pathlib.Path('pyproject.toml').read_text())
retained = {'tests/*','venv/*','.venv/*','setup.py','*/site-packages/*','src/maps/*'}
hatches = [e for e in data['tool']['coverage']['run']['omit'] if e not in retained]
assert len(hatches) <= 2, f'FR-015 violated: {len(hatches)} > 2'
print(f'FR-015 OK: {len(hatches)} escape hatches remain')
"
```

## PR-8a / PR-8b / PR-8c — Websocket wildcard (5 + 4 + 5 files)

```bash
# PR-8a (toplevel)
pytest --cov=src.websocket --cov-fail-under=90 tests/unit/websocket/
grep -n "def mock_websocket_transport" tests/unit/websocket/conftest.py

# PR-8b (diagnostics)
pytest --cov=src.websocket.diagnostics --cov-fail-under=90 \
       tests/unit/websocket/diagnostics/

# PR-8c (polling)
pytest --cov=src.websocket.polling --cov-fail-under=90 \
       tests/unit/websocket/polling/
```

## T-Final — Verify SC-001 + final omit list

```bash
python -c "
import tomllib, pathlib
data = tomllib.loads(pathlib.Path('pyproject.toml').read_text())
omit = data['tool']['coverage']['run']['omit']
expected = ['tests/*','venv/*','.venv/*','setup.py','*/site-packages/*','src/maps/*']
assert sorted(omit) == sorted(expected), f'SC-001 violated: {sorted(omit)}'
print('SC-001 OK')
"

pytest --cov --cov-fail-under=90 --cov-report=term
```

## SC-007 — Zero live network calls (podman network isolation)

Run the full default suite inside a container with no network access to prove all mocks are complete.

```bash
podman run --rm --network=none \
  -v "$PWD:/app:Z" -w /app \
  python:3.13-slim \
  bash -c "pip install -e .[dev] --no-index --find-links=/app/wheels && \
           pytest --cov --cov-fail-under=90 -m 'not integration'"
```

**Exit criterion**: status 0 with no `ConnectionError`, no `socket.gaierror`, no `requests.exceptions.ConnectionError`. Any network attempt raises immediately under `--network=none`.

If wheels are not pre-staged, substitute with a locked venv baked into the image at build time — the key point is `--network=none` at runtime.

## SC-010 — Pylint gate unchanged

```bash
pylint --fail-under=9.5 src/ MistHelper.py
```

**Exit criterion**: status 0. `fail-under=9.5` MUST match `pyproject.toml [tool.pylint.main]` line unchanged.

## Cross-PR sanity: baseline coverage never regresses

```bash
# Before starting the PR
git checkout main && pytest --cov --cov-report=json:/tmp/baseline.json -q
python -c "import json; print(json.load(open('/tmp/baseline.json'))['totals']['percent_covered'])" > /tmp/baseline.txt

# After the PR
git checkout <pr-branch> && pytest --cov --cov-report=json:/tmp/postpr.json -q
python -c "
import json
b, p = float(open('/tmp/baseline.txt').read()), json.load(open('/tmp/postpr.json'))['totals']['percent_covered']
assert p >= b, f'Regressed: {p:.2f} < {b:.2f}'
print(f'{b:.2f} -> {p:.2f}')
"
```
