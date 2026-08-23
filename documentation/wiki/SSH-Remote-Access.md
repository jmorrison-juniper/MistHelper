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
- **Bounded Auto-Restart**: If MistHelper crashes, the session restarts it up to five times, then closes
- **ForceCommand Architecture**: Direct launch into MistHelper (no shell access for security)

## Session Management

Each SSH connection automatically:

1. Creates a unique session ID based on connection details
2. Sets up an isolated working directory (`/app/sessions/session_<id>/`)
3. Launches MistHelper with container detection
4. Handles clean exit and session cleanup
5. Restarts MistHelper after an unexpected exit, up to the attempt limit

### Restart Controls

The session script `container/scripts/misthelper-session.sh` restarts MistHelper
after a failed run. The restart stops at a limit, so a permanent fault cannot
hold the session open and fill the log file.

| Control | Default | Purpose |
|---------|---------|---------|
| `MISTHELPER_MAX_START_ATTEMPTS` | 5 | Largest number of failed starts in a row before the session closes |
| `MISTHELPER_MIN_HEALTHY_SECONDS` | 30 | Smallest run time that counts as a real session and clears the crash count |
| `MISTHELPER_RESTART_DELAY_SECONDS` | 2 | First delay before a restart. The delay doubles after each failed start |
| `MISTHELPER_MAX_RESTART_DELAY_SECONDS` | 60 | Largest delay between two restarts |

With the default values, five failed starts take about 30 seconds. The session
then closes with a failure status and prints the last exit code, the attempt
count, and the two log paths to read.

To change a value, edit the assignment at the top of the session script, or add
the name and the value to `/etc/environment` inside the container. The SSH
daemon uses PAM, and PAM reads that file at login. The SSH daemon does not pass
the container environment to a session, so a `podman run -e` value alone does
not reach the script.

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
