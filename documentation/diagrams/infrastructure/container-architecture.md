[<- Back to Diagram Index](../README.md)

# Container Architecture

Container layers, session isolation, and access paths for the compose deployment.

## Container Layers

Internal structure of the MistHelper container from base image to running services.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'fontFamily': 'ui-monospace, monospace'
}}}%%
flowchart TB
    subgraph container["MistHelper Container"]
        subgraph services["Running Services"]
            ssh["SSH Server<br/>Port 2200"]
            web["Web portal<br/>Port 8055"]
            capture["Upgrade portal<br/>Port 8056"]
            metrics["Metrics gateway<br/>Port 8057"]
            snmp["SNMP service<br/>UDP 1161"]
            app["MistHelper.py<br/>Main Process"]
        end

        subgraph security["Security Layer"]
            user["Non-root User<br/>misthelper"]
            force["ForceCommand<br/>No Shell Access"]
            isolation["Session Isolation<br/>/app/sessions/"]
        end

        subgraph application["Application Layer"]
            code["Python 3.13<br/>MistHelper.py + src/"]
            deps["Dependencies<br/>mistapi >=0.64,<0.65"]
            config[".env<br/>Credentials"]
        end

        os["Python 3.13-slim + OpenSSH"]
    end

    subgraph volumes["Volume Mounts"]
        data["data/<br/>CSV + SQLite + Logs"]
        env[".env<br/>Read-Only Mount"]
        sessions["sessions/<br/>Per-Connection"]
    end

    subgraph polyglot["Compose Services"]
        arango["ArangoDB<br/>:9529"]
        redis["Redis Stack<br/>:9379"]
        redis_ui["RedisInsight<br/>:9526"]
        observium["Observium<br/>:8668 and UDP 1514"]
    end

    subgraph ports["External Ports"]
        p2200["Port 2200 - SSH Access"]
        p8055["Port 8055 - Web Portal"]
        p8056["Port 8056 - Upgrade Portal"]
        p8057["Port 8057 - Metrics Gateway"]
        p1161["UDP 1161 - SNMP"]
    end

    services --> security --> application --> os
    p2200 --> ssh
    p8055 --> web
    p8056 --> capture
    p8057 --> metrics
    p1161 --> snmp
    app --> data
    app --> env
    app --> sessions
    app --> arango
    app --> redis
```

> **PNG fallback**: If this diagram does not render, see [container-architecture.png](container-architecture.png).

## External Access Architecture

How NOC engineers reach MistHelper through SSH and HTTP paths.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'fontFamily': 'ui-monospace, monospace'
}}}%%
flowchart LR
    subgraph external["External Access"]
        engineer["NOC Engineer"]
        browser["Web Browser"]
    end

    subgraph host["Host Machine"]
        subgraph container["MistHelper Container"]
            sshd["SSH Server<br/>Port 2200"]
            gunicorn["Web portal<br/>Port 8055"]
            capture["Upgrade portal<br/>Port 8056"]
            metrics["Metrics gateway<br/>Port 8057"]
            misthelper["MistHelper.py"]
            sqlite["SQLite DB"]
        end

        subgraph storage["Persistent Storage"]
            datadir["data/ volume"]
            envfile[".env file"]
        end

        subgraph polyglot["Compose Services"]
            arango["ArangoDB<br/>:9529"]
            redis["Redis Stack<br/>:9379"]
            observium["Observium<br/>:8668"]
        end
    end

    engineer --> sshd
    browser --> gunicorn
    browser --> capture
    browser --> metrics
    sshd --> misthelper
    gunicorn --> misthelper
    capture --> misthelper
    metrics --> misthelper
    misthelper --> sqlite
    misthelper --> arango
    misthelper --> redis
    sqlite --> datadir
    misthelper --> envfile
```

## Session Isolation Model

Each SSH connection gets its own isolated session directory.

Phase-9 decomposition note: packet capture runtime ownership is split between
`src/capture/packet_capture.py` (orchestration) and
`src/capture/packet_capture_download.py` (poll/download helpers), while
container entrypoint behavior remains unchanged.

| Component | Path | Purpose |
|-----------|------|---------|
| Session Directory | `/app/sessions/session_{id}/` | Per-connection isolation |
| Data Volume | `/app/data/` | Shared CSV/SQLite output |
| ArangoDB | `misthelper-arangodb:9529` | Document storage (optional polyglot backend) |
| Redis Stack | `misthelper-redis:9379` | Redis JSON and Redis TimeSeries backend |
| RedisInsight | `localhost:9526` | Redis browser from the Redis Stack image |
| Observium | `localhost:8668`, `localhost:1514/udp` | Optional monitoring profile |
| SSH Config | `/etc/ssh/sshd_config` | ForceCommand, port 2200 |
| Web Server | `0.0.0.0:8055` | Gunicorn with workers |
| Capture Portal | `0.0.0.0:8056` | Separate portal process for upgrade captures |
| Metrics Gateway | `0.0.0.0:8057` | Prometheus endpoint and SNMP data source |
| Credentials | `/app/.env` | Read-only mounted secrets |

---

## Related Diagrams

- [Architecture Overview](../core/architecture-overview.md) - Container in system context
- [Deployment Pipeline](deployment-pipeline.md) - How container images get built and pushed
- [Network Protocols](network-protocols.md) - Packet structure for captures
