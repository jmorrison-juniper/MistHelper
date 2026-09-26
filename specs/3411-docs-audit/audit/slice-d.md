Slice D covers the operator guides.

| File | Old claim | New claim | Evidence |
| --- | --- | --- | --- |
| `documentation/SSH_GUIDE.md` | Start SSH with `python run-misthelper.py --ssh` and use container `misthelper-ssh`. | Start SSH through `.\scripts\compose.ps1 up -d --no-deps misthelper` and use container `misthelper-app`. | `compose.yml` service `misthelper` sets `container_name: misthelper-app` and publishes `2200:2200`. |
| `documentation/SSH_GUIDE.md` | The container mounts `/app/script.log` and `/app/.env`. | The stack mounts `./data` to `/app/data`, and `compose.yml` loads `.env` as an environment file. | `compose.yml` volume `./data:/app/data:rw` and `env_file: .env`. |
| `documentation/SSH_GUIDE.md` | An SSH session can start without a token. | The SSH session closes when `MIST_APITOKEN` and `MIST_API_TOKEN` are both absent. | `container/scripts/misthelper-session.sh` checks both variables before the loop. |
| `documentation/container-deployment.md` | Compose is the stack of three containers. | Compose has three required services and one optional `monitoring` profile service. | `compose.yml` defines `misthelper`, `misthelper-arangodb`, `misthelper-redis`, and `misthelper-observium`. |
| `documentation/container-deployment.md` | The service table omitted Observium. | The service table includes `misthelper-observium` as an optional SNMP monitoring service. | `compose.yml` defines `misthelper-observium` with profile `monitoring`. |
| `documentation/cli-reference.md` | The flag table omitted the MIB flags and `--standalone`. | The flag table includes `--mib-generate`, `--mib-dry-run`, `--mib-output`, `--mib-report`, `--mib-check`, and `--standalone`. | `.venv\Scripts\python.exe MistHelper.py --help` lists those flags. |
| `documentation/upgrade_capture_portal.md` | The menu start path used menu 238. | The menu start path uses menu 239. | `documentation/menu_reference.md` lists menu 239 as the upgrade capture portal. |
| `documentation/upgrade_capture_portal.md` | `REDIS_HOST` defaulted to `redis-stack`, and `REDIS_PORT` defaulted to `6379`. | `REDIS_HOST` defaults to `misthelper-redis`, and `REDIS_PORT` defaults to `9379`. | `src/upgrade_portal/app/config.py` sets `DEFAULT_REDIS_HOST` and `DEFAULT_REDIS_PORT`. |
| `documentation/upgrade_capture_portal.md` | The environment table omitted post-check mode, autostart, and default firmware variables. | The table names `CAPTURE_POST_CHECK_MODE`, `CAPTURE_AUTOSTART`, and the three `CAPTURE_DEFAULT_*_VERSION` variables. | `src/upgrade_portal/app/config.py` defines `CAPTURE_POST_CHECK_MODE`; `deploy/.env.example` documents the other variables. |
| `documentation/menu-highlights.md` | Menu 236 said 32 operations, and menus 241 through 243, 269, and 270 were absent. | Menu 236 says 33 operations, and the table includes menus 241 through 243, 269, and 270. | `documentation/menu_reference.md` lists those entries and counts. |
| `documentation/menu-highlights.md` | Menus 259 through 268 did not state operation counts. | Menus 259 through 268 state the current generated operation counts. | `documentation/menu_reference.md` lists counts for menus 259 through 268. |
| `documentation/security.md` | The destructive section did not state the current destructive menu numbers. | The destructive section states 154 through 187, 189 through 191, 194, 206 through 208, and 239. | `src/utils/operation_registry.py` has 42 `destructive` entries. |

## Open questions

- `.github\skills\ste-writing\SKILL.md` does not exist in this worktree. I used `documentation/ASD-STE100_writing-guide.md` instead.
