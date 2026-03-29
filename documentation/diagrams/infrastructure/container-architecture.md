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
block-beta
    columns 3

    block:container["MistHelper Container"]:3
        columns 3
        
        block:services["Running Services"]:3
            columns 3
            ssh["SSH Server\nPort 2200"]
            web["Gunicorn Web\nPort 8055"]
            app["MistHelper.py\nMain Process"]
        end

        block:security["Security Layer"]:3
            columns 3
            user["Non-root User\nmisthelper"]
            force["ForceCommand\nNo Shell Access"]
            isolation["Session Isolation\n/app/sessions/"]
        end

        block:application["Application Layer"]:3
            columns 3
            code["Python 3.13\nMistHelper.py"]
            deps["Dependencies\nmistapi + libs"]
            config[".env\nCredentials"]
        end

        block:base["Base Image"]:3
            columns 1
            os["Python 3.13-slim + OpenSSH"]
        end
    end

    block:volumes["Volume Mounts"]:3
        columns 3
        data["data/\nCSV + SQLite + Logs"]
        env[".env\nRead-Only Mount"]
        sessions["sessions/\nPer-Connection"]
    end

    space:3

    block:ports["External Ports"]:3
        columns 2
        p2200["Port 2200\nSSH Access"]
        p8055["Port 8055\nWeb Portal"]
    end
```

> **PNG fallback**: If the block-beta diagram does not render, see [container-architecture.png](container-architecture.png).

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
architecture-beta
    group host[Host Machine]

    group container[MistHelper Container] in host
    service sshd(server)[SSH Server 2200] in container
    service gunicorn(internet)[Gunicorn 8055] in container
    service misthelper(server)[MistHelper.py] in container
    service sqlite(database)[SQLite DB] in container

    group storage[Persistent Storage] in host
    service datadir(disk)[data/ volume] in storage
    service envfile(disk)[.env file] in storage

    group external[External Access]
    service engineer(server)[NOC Engineer] in external
    service browser(internet)[Web Browser] in external

    engineer:R --> L:sshd
    browser:R --> L:gunicorn
    sshd:R --> L:misthelper
    gunicorn:R --> L:misthelper
    misthelper:B --> T:sqlite
    sqlite:R --> L:datadir
    misthelper:R --> L:envfile
```

## Session Isolation Model

Each SSH connection gets its own isolated session directory.

| Component | Path | Purpose |
|-----------|------|---------|
| Session Directory | `/app/sessions/session_{id}/` | Per-connection isolation |
| Data Volume | `/app/data/` | Shared CSV/SQLite output |
| SSH Config | `/etc/ssh/sshd_config` | ForceCommand, port 2200 |
| Web Server | `0.0.0.0:8055` | Gunicorn with workers |
| Credentials | `/app/.env` | Read-only mounted secrets |

---

## Related Diagrams

- [Architecture Overview](../core/architecture-overview.md) - Container in system context
- [Deployment Pipeline](deployment-pipeline.md) - How container images get built and pushed
- [Network Protocols](network-protocols.md) - Packet structure for captures
