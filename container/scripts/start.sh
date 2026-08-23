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

# Ensure ssh.log exists and is writable by misthelper user
touch /app/data/ssh.log
chown misthelper:misthelper /app/data/ssh.log
chmod 664 /app/data/ssh.log

# Corporate TLS trust store.
# The image verifies every TLS certificate. An operator behind a
# TLS-inspecting proxy mounts the proxy root certificate into
# /usr/local/share/ca-certificates. This step adds the mounted certificate to
# the system trust store, so the check stays on. See issue #1906.
CUSTOM_CA_DIR="/usr/local/share/ca-certificates"
if ls -A "$CUSTOM_CA_DIR"/*.crt >/dev/null 2>&1; then
    echo "[TLS] Installing operator-supplied root certificates from $CUSTOM_CA_DIR" >> /app/data/ssh.log
    update-ca-certificates >> /app/data/ssh.log 2>&1 || true
    echo "[TLS] Trust store updated. Certificate verification stays on." >> /app/data/ssh.log
else
    echo "[TLS] No operator-supplied root certificate found. The default trust store applies." >> /app/data/ssh.log
fi

# Report a run-time bypass of certificate verification.
# A bypass is never the default. An operator must pass the variable at run
# time. The container records a warning, so the operator sees the exposure.
if [ "${PYTHONHTTPSVERIFY:-1}" = "0" ]; then
    echo "[TLS] WARNING: PYTHONHTTPSVERIFY=0 turns off certificate verification." >> /app/data/ssh.log
    echo "[TLS] WARNING: An attacker on the network path can read the Mist API token." >> /app/data/ssh.log
fi
for CA_VARIABLE in REQUESTS_CA_BUNDLE CURL_CA_BUNDLE SSL_CERT_FILE; do
    # An empty value removes the trust store. An unset value keeps the default.
    CA_VALUE="${!CA_VARIABLE-unset}"
    if [ -z "$CA_VALUE" ]; then
        echo "[TLS] WARNING: $CA_VARIABLE is empty, which removes the trust store." >> /app/data/ssh.log
        echo "[TLS] WARNING: Point $CA_VARIABLE at a mounted root certificate." >> /app/data/ssh.log
    fi
done

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

# Determine web portal port (default 8055)
WEB_PORT="${WEB_PORT:-8055}"

# Start Gunicorn web portal in the background
echo "[PORTAL] Starting web portal on port $WEB_PORT..." >> /app/data/ssh.log
su - misthelper -c "cd /app && gunicorn wsgi:app \
    --bind 0.0.0.0:${WEB_PORT} \
    --workers 1 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --access-logfile /app/data/portal_access.log \
    --error-logfile /app/data/portal_error.log" &
GUNICORN_PID=$!

# Trap signals to stop both processes
cleanup() {
    echo "[CONTAINER] Shutting down..." >> /app/data/ssh.log
    kill "$GUNICORN_PID" 2>/dev/null || true
    kill "$SSHD_PID" 2>/dev/null || true
    wait "$GUNICORN_PID" 2>/dev/null || true
    wait "$SSHD_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Start SSH daemon in the background
/usr/sbin/sshd -D &
SSHD_PID=$!

# Wait for either process to exit
wait -n "$GUNICORN_PID" "$SSHD_PID" 2>/dev/null || true
echo "[CONTAINER] A service exited unexpectedly" >> /app/data/ssh.log
cleanup
