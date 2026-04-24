[<- Back to Diagram Index](../README.md)

# Container Architecture

Container layers, session isolation, and external access paths for MistHelper's containerized deployment.

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
            web["Gunicorn Web<br/>Port 8055"]
            app["MistHelper.py<br/>Main Process"]
        end

        subgraph security["Security Layer"]
            user["Non-root User<br/>misthelper"]
            force["ForceCommand<br/>No Shell Access"]
            isolation["Session Isolation<br/>/app/sessions/"]
        end

        subgraph application["Application Layer"]
            code["Python 3.13<br/>MistHelper.py"]
            deps["Dependencies<br/>mistapi + libs"]
            config[".env<br/>Credentials"]
        end

        os["Python 3.13-slim + OpenSSH"]
    end

    subgraph volumes["Volume Mounts"]
        data["data/<br/>CSV + SQLite + Logs"]
        env[".env<br/>Read-Only Mount"]
        sessions["sessions/<br/>Per-Connection"]
    end

    subgraph polyglot["Polyglot Backends (Optional)"]
        arango["ArangoDB<br/>:8529"]
        redis["Redis Stack<br/>:6379"]
    end

    subgraph ports["External Ports"]
        p2200["Port 2200 - SSH Access"]
        p8055["Port 8055 - Web Portal"]
    end

    services --> security --> application --> os
    p2200 --> ssh
    p8055 --> web
    app --> data
    app --> env
    app --> sessions
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
            gunicorn["Gunicorn<br/>Port 8055"]
            misthelper["MistHelper.py"]
            sqlite["SQLite DB"]
        end

        subgraph storage["Persistent Storage"]
            datadir["data/ volume"]
            envfile[".env file"]
        end

        subgraph polyglot["Polyglot Backends (Optional)"]
            arango["ArangoDB<br/>:8529"]
            redis["Redis Stack<br/>:6379"]
        end
    end

    engineer --> sshd
    browser --> gunicorn
    sshd --> misthelper
    gunicorn --> misthelper
    misthelper --> sqlite
    misthelper --> arango
    misthelper --> redis
    sqlite --> datadir
    misthelper --> envfile
```

## Session Isolation Model

Each SSH connection gets its own isolated session directory.

| Component | Path | Purpose |
|-----------|------|---------|
| Session Directory | `/app/sessions/session_{id}/` | Per-connection isolation |
| Data Volume | `/app/data/` | Shared CSV/SQLite output |
| ArangoDB | `arangodb:8529` | Document storage (optional polyglot backend) |
| Redis Stack | `redis-stack:6379` | Time-series + JSON cache (optional polyglot backend) |
| SSH Config | `/etc/ssh/sshd_config` | ForceCommand, port 2200 |
| Web Server | `0.0.0.0:8055` | Gunicorn with workers |
| Credentials | `/app/.env` | Read-only mounted secrets |

---

## Related Diagrams

- [Architecture Overview](../core/architecture-overview.md) - Container in system context
- [Deployment Pipeline](deployment-pipeline.md) - How container images get built and pushed
- [Network Protocols](network-protocols.md) - Packet structure for captures
