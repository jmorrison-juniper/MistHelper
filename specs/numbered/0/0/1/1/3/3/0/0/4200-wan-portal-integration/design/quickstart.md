# Quickstart: WAN Performance portal integration

Use these steps to check the current state and to run each verification command. Run each command from the repository root. Read-only commands do not change the repository.

## 1. Confirm the dependency state

Run each command in PowerShell. Set the GitHub host and token first. Never print the token.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh pr view 4208 -R jmorrison-juniper/MistHelper --json state,isDraft,mergeStateStatus,headRefOid
```

Expected result: state `OPEN`, draft `true`, merge state `DIRTY`, and head `843be63bc837513b4442dae69da9f0db922e0ed1` (R01, R37).

## 2. Confirm the 11 add/add files on main

```powershell
rtk proxy git ls-tree main -- src/interfaces/wan_performance/__init__.py src/interfaces/wan_performance/collection/peer_insights.py src/interfaces/wan_performance/integration/refresh_store.py
```

Expected result: each path appears with its blob SHA from rows R56 to R66.

## 3. Reproduce the navigation gate defect

1. Open `web_portal/app.py` at the PR 4208 head and read the lines that set `WAN_PERFORMANCE_NAV_ENABLED` (line 221).
2. Compare the endpoint name with `web_portal/templates/base.html` line 82 onward.
3. Expected result: the gate checks `wan_performance.overview` and the link targets `wan_performance.live.overview` (R97, R98).

## 4. Confirm the five-child violation

```powershell
rtk proxy git ls-tree --name-only 843be63bc837513b4442dae69da9f0db922e0ed1 -- src/interfaces/wan_performance/
```

Expected result: six children. The limit is five (R106).

## 5. Run the local verification commands after implementation

Run each command from the local gates table in `.github/copilot-instructions.md` line 50 onward.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m pytest tests/unit/wan_performance/collection/test_snapshot_client.py
python -m pytest tests/e2e/web_portal/test_wan_performance_offline.py
python -m pytest tests/e2e/web_portal/test_wan_dashboard_cache_only.py
python -m pytest tests/guardrails
```

Expected result: each command exits with code 0. Each pytest command prints a summary with zero failures.

## 6. Start the portal for a manual check

Use the compose group. Publish no new port.

```powershell
.\scripts\compose.ps1 up -d --no-deps misthelper
```

Open `http://127.0.0.1:8055/wan-performance/preview/` for the synthetic preview. Open `http://127.0.0.1:8055/wan-performance/live/` for the live overview. The live page shows "no data" when the Mist session is absent.

## 7. Remove the test container when the check ends

Use the container name pattern from `documentation/container-deployment.md` (line 168 onward). Remove the container, its volume, and its network by exact name.

```powershell
podman rm -f misthelper-tmp-issue4200-wan-portal
podman volume rm misthelper-tmp-issue4200-wan-portal
podman network rm misthelper-tmp-issue4200-wan-portal
podman ps -a --filter "name=misthelper-tmp-" --format "{{.Names}} {{.Status}}"
```

Expected result: the last command prints no container name for this issue.
