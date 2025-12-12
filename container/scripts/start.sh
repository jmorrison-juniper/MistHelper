#!/bin/bash
# MistHelper Container Entrypoint
# Handles dynamic SSH user provisioning and starts the SSH daemon.
#
# SECURITY: Password never echoed. Username may be echoed (not secret).
# Environment variables honored if provided:
#   MISTHELPER_SSH_USERNAME  (defaults to misthelper)
#   MISTHELPER_SSH_PASSWORD  (defaults to build-time password if omitted)

set -e

USERNAME="${MISTHELPER_SSH_USERNAME:-misthelper}"
PASSWORD="${MISTHELPER_SSH_PASSWORD:-}"

# If a different username is requested, create it (idempotent).
if ! id "$USERNAME" >/dev/null 2>&1; then
    echo "[SSH] Creating user $USERNAME" >> /app/data/ssh.log
    useradd -m -s /bin/bash "$USERNAME" || true
    usermod -aG sudo "$USERNAME" || true
    # Ensure /app readable; retain original ownership on writable paths
    chown -R "$USERNAME" /app/data 2>/dev/null || true
fi

# Update password if provided (non-empty).
if [ -n "$PASSWORD" ]; then
    echo "$USERNAME:$PASSWORD" | chpasswd
    echo "[SSH] Applied runtime password for $USERNAME" >> /app/data/ssh.log
else
    echo "[SSH] No runtime password override provided; using build-time password." >> /app/data/ssh.log
fi

# Adjust AllowUsers directive to reflect chosen username.
if [ -f /etc/ssh/sshd_config.d/misthelper.conf ]; then
    if grep -q "^AllowUsers " /etc/ssh/sshd_config.d/misthelper.conf; then
        sed -i "s/^AllowUsers .*/AllowUsers $USERNAME/" /etc/ssh/sshd_config.d/misthelper.conf
    else
        echo "AllowUsers $USERNAME" >> /etc/ssh/sshd_config.d/misthelper.conf
    fi
fi

echo "[SSH] Starting MistHelper SSH Service on port 2200..." >> /app/data/ssh.log
echo "[SSH] Each SSH connection spawns its own MistHelper session." >> /app/data/ssh.log
echo "[SSH] Connect with: ssh -p 2200 $USERNAME@<container-ip>" >> /app/data/ssh.log
echo "[SSH] Use option 0 in MistHelper to disconnect." >> /app/data/ssh.log

# Run SSH daemon in foreground
exec /usr/sbin/sshd -D
