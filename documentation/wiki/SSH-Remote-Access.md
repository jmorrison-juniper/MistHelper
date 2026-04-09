# SSH Remote Access

MistHelper supports SSH server deployment for remote access with automatic session management.

## Quick Start

```powershell
# Build and start SSH server container
podman build -t misthelper -f Containerfile .

# Ensure data directory is writable
chmod -R 777 data/

# Start container
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 \
  -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" \
  misthelper

# Connect from any SSH client
ssh -p 2200 misthelper@localhost
# Password: misthelper123!
```

## Connection Details

| Setting | Value | Notes |
|---------|-------|-------|
| **Port** | 2200 | Avoids conflict with system SSH (port 22) |
| **Username** | misthelper | Fixed username for all connections |
| **Password** | misthelper123! | Default password (change in production) |
| **Host Keys** | Auto-generated | Unique per container instance |

## Features

- **Automatic Session Management**: Each SSH connection creates an isolated MistHelper session
- **Multi-User Support**: Multiple users can connect simultaneously with session isolation
- **Session Persistence**: Sessions persist until you explicitly exit
- **Auto-Restart**: If MistHelper crashes, the session automatically restarts
- **ForceCommand Architecture**: Direct launch into MistHelper (no shell access for security)

## Session Management

Each SSH connection automatically:

1. Creates a unique session ID based on connection details
2. Sets up an isolated working directory (`/app/sessions/session_<id>/`)
3. Launches MistHelper with container detection
4. Handles clean exit and session cleanup
5. Provides session restart on unexpected termination

## Usage Examples

```bash
# Connect and run interactively
ssh -p 2200 misthelper@localhost

# Connect with specific SSH client settings
ssh -p 2200 -o StrictHostKeyChecking=no misthelper@localhost

# From Windows with built-in SSH client
ssh -p 2200 misthelper@127.0.0.1
```

## Architecture Details

- **ForceCommand**: SSH forces execution of MistHelper (no shell access)
- **Session Isolation**: Each connection gets independent session directory
- **Container Detection**: MistHelper automatically detects SSH container mode
- **Session Cleanup**: Automatic cleanup on connection termination

## Security Considerations

- SSH server runs on non-standard port 2200
- ForceCommand prevents shell access (application-only access)
- Session directories are isolated between connections
- Default credentials should be changed in production environments
- Host key verification recommended for production use

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Ensure container is running: `podman ps` |
| Wrong password | Default is `misthelper123!` |
| Permission denied (SSH) | Check SSH client settings, try `-o StrictHostKeyChecking=no` |
| Permission denied (data dir) | Run `chmod -R 777 data/` on host before starting container |
| `script.log` permission error | Data directory not writable -- fix with `chmod -R 777 data/` |
| Session not starting | Check container logs: `podman logs misthelper` |
| Port conflict | Ensure port 2200 is available |
| Multiple sessions interfering | Each connection should get unique session ID -- check logs |

Persisted artifacts appear under local `data/` bind mount.
