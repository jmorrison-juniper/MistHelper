# MistHelper SSH Remote Access Guide

## Overview
MistHelper now supports remote SSH access when running in container mode. This enables you to connect to a running MistHelper container over SSH and interact with it remotely.

## SSH Server Features
- Custom SSH port: 2200 (avoids conflicts with host SSH)
- Dedicated user account: `misthelper`
- Password authentication for ease of use
- Sudo privileges for administrative tasks
- Persistent container mode (runs until stopped)

## Quick Start

### 1. Start SSH Container
```bash
python run-misthelper.py --ssh
```

This will:
- Build the MistHelper container with SSH server
- Start the container in detached mode
- Expose SSH on port 2200
- Display connection instructions

### 2. Connect via SSH
```bash
ssh -p 2200 misthelper@localhost
```

**Default password:** `misthelper123!`

### 3. Use MistHelper
Once connected via SSH, MistHelper starts automatically:
- **Automatic Launch**: MistHelper menu appears immediately upon SSH connection
- **Session Persistence**: Each SSH connection gets its own isolated session
- **Bounded Auto-Restart**: MistHelper restarts after each operation. After five crashes in a row, the session closes and names the cause.
- **Clean Exit**: Use option "0" to properly exit and close SSH session
- **No Shell Access**: You cannot access the container's command line for security

**Note**: You never need to manually run commands - MistHelper starts automatically and manages the session for you.

## Container Management

### Check Container Status
```bash
podman ps
```

### View Container Logs
```bash
podman logs misthelper-ssh
```

### Find Container IP Address
```bash
# Get container IP
podman inspect misthelper-ssh --format "{{.NetworkSettings.IPAddress}}"

# Get detailed network info
podman inspect misthelper-ssh | grep -A 10 "NetworkSettings"

# Alternative: check from inside container
podman exec misthelper-ssh hostname -I
```

### Stop SSH Container
```bash
podman stop misthelper-ssh
```

### Remove SSH Container
```bash
podman rm misthelper-ssh
```

## Session Restart Behavior

The script `container/scripts/misthelper-session.sh` restarts MistHelper after a
failed run. The restart stops at a limit, so a permanent fault cannot hold the
SSH session open and fill the log file.

| Control | Default | Purpose |
|---------|---------|---------|
| `MISTHELPER_MAX_START_ATTEMPTS` | 5 | Largest number of failed starts in a row before the session closes |
| `MISTHELPER_MIN_HEALTHY_SECONDS` | 30 | Smallest run time that counts as a real session and clears the crash count |
| `MISTHELPER_RESTART_DELAY_SECONDS` | 2 | First delay before a restart. The delay doubles after each failed start |
| `MISTHELPER_MAX_RESTART_DELAY_SECONDS` | 60 | Largest delay between two restarts |

With the default values, the delays run 2, 4, 8, and 16 seconds. Five failed
starts therefore take about 30 seconds. The session then closes with a failure
status and prints the last exit code, the attempt count, and the two log paths
to read.

### How to Change a Control Value

**Caution:** A `podman run -e` value will not reach the session script, and the
script will keep the default value. The SSH daemon does not pass the container
environment to a session. The same limit applies to `docker run -e` and to an
`Environment=` line in a Quadlet unit file.

Use one of these two methods instead.

1. Edit the assignment at the top of `container/scripts/misthelper-session.sh`
   and rebuild the image. Use this method for a permanent change.
2. Add the name and the value to `/etc/environment` inside the container. The
   SSH daemon reads that file at each login through PAM. Use this method for a
   test on a running container.

```bash
# Method 2: raise the attempt limit to 8 on a running container
podman exec -u root misthelper sh -c 'echo "MISTHELPER_MAX_START_ATTEMPTS=8" >> /etc/environment'
```

The new value applies to the next SSH login. An open session keeps the old
value.

## SSH Configuration Details

### Server Configuration
- **Port:** 2200
- **Authentication:** Password-based
- **Forced Command:** Automatic MistHelper session launcher
- **User:** misthelper (restricted to MistHelper only)
- **Session Management:** Each connection gets an isolated session with a bounded auto-restart

### Security Notes
- SSH server only accepts connections for user `misthelper`
- Root login is disabled for security
- ForceCommand prevents access to container shell
- Each user gets isolated session directory
- Automatic session cleanup on disconnect
- Password authentication is enabled for convenience
- Consider using SSH keys for production environments

## File Persistence

The SSH container maintains access to:
- `/app/data/` - Mounted from host `./data/` directory
- `/app/script.log` - Mounted from host `./script.log`
- `/app/.env` - Mounted from host `./.env` (if exists)

All MistHelper data files and logs persist on the host system.

## Troubleshooting

### Connection Refused
- Verify container is running: `podman ps`
- Check port mapping: should show `0.0.0.0:2200->2200/tcp`
- View container logs: `podman logs misthelper-ssh`

### Authentication Failed
- Verify username: `misthelper`
- Verify password: `misthelper123!`
- Check SSH server status inside container

### Container Won't Start
- Check Podman/Docker installation
- Verify Containerfile syntax
- Review build logs for errors

### The SSH Session Closes Right After the Connection
MistHelper failed to start five times in a row. The session prints a message
before it closes. The message names the last exit code, the attempt count, and
the two log paths. Read that message first.

```text
[SESSION] MistHelper failed 5 times in a row. The last exit code was 1.
[SESSION] The session is closed. To find the cause, read /app/data/script.log and /app/data/ssh.log.
```

The same two lines go to `/app/data/ssh.log`, so the message stays after the
terminal closes. Read `/app/data/script.log` for the MistHelper error. A missing
dependency, a bad `.env` file, and a data directory without write permission are
the common causes. To fix a permission error, run `chmod -R 777 data/` on the
host.

## Advanced Usage

### Custom SSH Configuration
To modify SSH settings, edit the Containerfile and rebuild:
1. Modify SSH configuration in Containerfile
2. Rebuild: `podman build -t misthelper .`
3. Restart with SSH: `python run-misthelper.py --ssh`

### Port Forwarding
To use a different host port:
```bash
podman run -p 2222:2200 misthelper
```

### Network Access
For remote access from other machines, ensure:
1. Host firewall allows port 2200
2. Network routing permits SSH traffic
3. Consider security implications of remote access

**Finding Container IP for Remote Access:**
```bash
# Get container IP for direct access
podman inspect misthelper-ssh --format "{{.NetworkSettings.IPAddress}}"

# Connect directly to container IP (if needed)
ssh -p 2200 misthelper@<container-ip>

# Or use host IP from remote machine
ssh -p 2200 misthelper@<host-machine-ip>
```

## Integration with Development

### VS Code Remote SSH
You can connect VS Code to the SSH container:
1. Install "Remote - SSH" extension
2. Add SSH host: `misthelper@localhost:2200`
3. Connect and work directly in container environment

### Automated Workflows
Use SSH for automated MistHelper operations:
```bash
ssh -p 2200 misthelper@localhost "python MistHelper.py --menu 5 --test"
```

## Security Considerations

### Development vs Production
- **Development:** Password authentication acceptable
- **Production:** Consider SSH key authentication
- **Network:** Restrict SSH access to trusted networks

### Password Security
- Default password is for development convenience
- Change password for production use:
  ```bash
  ssh -p 2200 misthelper@localhost
  passwd
  ```

### Container Security
- Container runs as non-root user
- Sudo requires password confirmation
- SSH server configuration hardened

---

## Example Session

```bash
# Start SSH container
$ python run-misthelper.py --ssh
[BUILD] Building Podman image...
[SUCCESS] Smart Podman image built successfully!
[SSH] Starting container with SSH server...
[SUCCESS] SSH container started successfully!
[INFO] Connect with: ssh -p 2200 misthelper@localhost
[INFO] Password: misthelper123!

# Connect via SSH
$ ssh -p 2200 misthelper@localhost
misthelper@localhost's password: [misthelper123!]

# Now inside container
misthelper@container:~$ cd /app
misthelper@container:/app$ python MistHelper.py
[MistHelper menu appears...]

# Run specific operation
misthelper@container:/app$ python MistHelper.py --menu 1
[Operation executes...]

# Exit SSH session
misthelper@container:/app$ exit

# Stop container when done
$ podman stop misthelper-ssh
```

This SSH integration provides powerful remote access capabilities while maintaining all existing MistHelper functionality and security practices.