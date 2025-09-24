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
- **Auto-Restart**: After completing an operation, MistHelper automatically restarts
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

## SSH Configuration Details

## SSH Configuration Details

### Server Configuration
- **Port:** 2200
- **Authentication:** Password-based
- **Forced Command:** Automatic MistHelper session launcher
- **User:** misthelper (restricted to MistHelper only)
- **Session Management:** Each connection gets isolated session with auto-restart

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