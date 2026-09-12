# Contract: Deployment Templates

**Files**: `deploy/misthelper.service`, `deploy/misthelper.container`, `deploy/.env.example`
**Type**: systemd unit, Podman Quadlet, environment configuration
**Consumers**: Operations engineers deploying MistHelper

## Systemd Unit Contract (`deploy/misthelper.service`)

```ini
[Unit]
Description=MistHelper Network Operations Tool
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/misthelper/MistHelper.py
WorkingDirectory=/opt/misthelper
EnvironmentFile=/opt/misthelper/.env
User=misthelper
Group=misthelper
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Behavioral Contract
- MUST start after network is available
- MUST restart on any exit (crash, signal, etc.)
- MUST restart within 5 seconds of failure detection
- MUST run as non-root user `misthelper`
- MUST load all environment from `EnvironmentFile`

## Quadlet Contract (`deploy/misthelper.container`)

```ini
[Container]
Image=ghcr.io/jmorrison-juniper/misthelper:latest
PublishPort=2200:2200
PublishPort=8055:8055
Volume=./data:/app/data:rw
EnvironmentFile=./.env

[Service]
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

### Quadlet Behavioral Contract
- MUST pull from GHCR (same registry as CI)
- MUST expose SSH (2200) and web (8055) ports
- MUST mount `data/` for persistence
- MUST load secrets from `.env` via `EnvironmentFile`
- MUST auto-restart on failure within 5 seconds

## Environment Variable Contract (`deploy/.env.example`)

All variables MUST be documented with:
- Variable name
- Description
- Whether required or optional
- Default value (if optional)
- Example value

Minimum required variables (based on MistHelper.py `os.environ.get()` pattern):
| Variable | Required | Description |
|----------|----------|-------------|
| MIST_API_TOKEN | Yes | Juniper Mist API authentication token |
| MIST_ORG_ID | Yes | Mist organization UUID |
| MIST_PAGE_LIMIT | No | API page size (default: 1000) |
| FAST_MODE_MAX_CONCURRENT_CONNECTIONS | No | Concurrency limit in fast mode (default: 8) |
| CSV_FRESHNESS_MINUTES | No | Cache freshness for fast mode (default: 5) |
