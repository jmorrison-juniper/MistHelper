#!/bin/bash
# MistHelper Container Entrypoint
# Handles dynamic SSH user provisioning and starts the SSH daemon.
#
# SECURITY: Password never echoed. Username may be echoed (not secret).
# Environment variables honored if provided:
#   MISTHELPER_SSH_USERNAME  (defaults to misthelper)
#   MISTHELPER_SSH_PASSWORD  (defaults to build-time password if omitted)

set -e
# Fail a pipeline when any stage fails, because the last stage can hide an
# earlier failure and report success. See issue #1925.
set -o pipefail

# Write one line to stderr and to the log file.
# The container log reads stderr only. The log file lives in the data volume and
# survives the container. An operator needs both sources to find a crash cause.
log_container_event() {
    echo "$1" >&2  # Send the line to stderr, so "podman logs" reports the event.
    { echo "$1" >> /app/data/ssh.log; } 2>/dev/null || true  # Keep a copy in the log file, and never stop the container on a log write error.
}

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
    # Check each file before the install.
    # Warning: update-ca-certificates exits 0 and appends the raw bytes even when
    # the file is not a certificate, so neither the exit status nor the bundle
    # content can report a bad file. Parse each file instead.
    CA_INSTALL_FAILURES=0
    for CA_FILE in "$CUSTOM_CA_DIR"/*.crt; do
        CA_NAME=$(basename "$CA_FILE")  # Name the file in every message, so the operator knows which one failed.
        # Test for the PEM header first. update-ca-certificates reads PEM only,
        # and it reports "1 added" for a DER file that it cannot use. OpenSSL 3
        # auto-detects the encoding, so a parse test alone accepts a DER file.
        if grep -q -- "-----BEGIN CERTIFICATE-----" "$CA_FILE" && openssl x509 -in "$CA_FILE" -noout >/dev/null 2>&1; then
            echo "[TLS] Read $CA_NAME as a PEM certificate." >> /app/data/ssh.log
        elif openssl x509 -in "$CA_FILE" -noout >/dev/null 2>&1; then
            # The file holds a real certificate in an encoding the trust store cannot read.
            CA_INSTALL_FAILURES=$((CA_INSTALL_FAILURES + 1))
            echo "[TLS] WARNING: $CA_NAME is not PEM. The trust store cannot use it." >> /app/data/ssh.log
            echo "[TLS] WARNING: Convert it with: openssl x509 -inform DER -in $CA_NAME -out $CA_NAME.pem" >> /app/data/ssh.log
        else
            # Count the failure, because the summary line below must not claim success.
            CA_INSTALL_FAILURES=$((CA_INSTALL_FAILURES + 1))
            echo "[TLS] WARNING: $CA_NAME is not a certificate that the trust store can read." >> /app/data/ssh.log
            echo "[TLS] WARNING: Check that $CA_NAME holds one PEM certificate." >> /app/data/ssh.log
        fi
    done
    # Keep the container alive if the command fails. The count above decides the result.
    update-ca-certificates >> /app/data/ssh.log 2>&1 || true
    if [ "$CA_INSTALL_FAILURES" -eq 0 ]; then
        # Print the success line only when every file parsed as a certificate.
        echo "[TLS] Trust store updated. Certificate verification stays on." >> /app/data/ssh.log
    else
        echo "[TLS] WARNING: $CA_INSTALL_FAILURES certificate file(s) failed to install." >> /app/data/ssh.log
        echo "[TLS] WARNING: A connection through the proxy will fail until you repair them." >> /app/data/ssh.log
    fi
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

# Read the grace period, so bash and the Python shutdown path share one value.
SHUTDOWN_GRACE_SECONDS="${PORTAL_OPERATION_SHUTDOWN_GRACE_SECONDS:-30}"
# Add a margin past the grace period, so bash waits longer than Gunicorn before it forces a kill.
CONTAINER_KILL_MARGIN_SECONDS=10

# Start Gunicorn web portal in the background
log_container_event "[PORTAL] Starting the web portal on port $WEB_PORT."  # Report the start before the launch, so a failed launch has a start point in the log.
su - misthelper -c "cd /app && gunicorn wsgi:app \
    --bind 0.0.0.0:${WEB_PORT} \
    --workers 1 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --graceful-timeout ${SHUTDOWN_GRACE_SECONDS} \
    --access-logfile /app/data/portal_access.log \
    --error-logfile /app/data/portal_error.log" &
GUNICORN_PID=$!
SSHD_PID=""  # Clear the sshd PID, because a signal can start the cleanup before the daemon starts.
log_container_event "[PORTAL] Started the web portal with PID $GUNICORN_PID."  # Name the PID, so the operator can match a later crash line to this service.

# Wait for one PID to exit on its own, then force it, so cleanup never hangs forever.
_wait_for_pid_or_kill() {
    local pid="$1"  # Process to wait for before a forced kill.
    local grace_seconds="$2"  # Seconds to wait before SIGKILL.
    local waited=0  # Counts the seconds already spent waiting.
    while kill -0 "$pid" 2>/dev/null; do
        if [ "$waited" -ge "$grace_seconds" ]; then
            # Log the forced kill, so an operator can see the grace period ran out.
            log_container_event "[CONTAINER] PID $pid did not exit in ${grace_seconds}s, sending SIGKILL"
            kill -9 "$pid" 2>/dev/null || true
            break
        fi
        sleep 1  # Poll once a second, so the check stays cheap and still responsive.
        waited=$((waited + 1))
    done
    wait "$pid" 2>/dev/null || true
}

# Trap signals to stop both processes
cleanup() {
    local final_status="${1:-0}"  # Default to 0, because an operator stop is a success and needs no restart.
    log_container_event "[CONTAINER] Shutting down. The exit status will be $final_status."  # Report the plan before the shutdown, so the operator sees the cause order.
    # Match the bash-side deadline to Gunicorn's own --graceful-timeout, plus a margin.
    local kill_wait
    kill_wait=$((SHUTDOWN_GRACE_SECONDS + CONTAINER_KILL_MARGIN_SECONDS))
    kill "$GUNICORN_PID" 2>/dev/null || true
    kill "$SSHD_PID" 2>/dev/null || true
    # Wait for a clean exit within the bound, so an in-flight operation can finish first.
    _wait_for_pid_or_kill "$GUNICORN_PID" "$kill_wait"
    _wait_for_pid_or_kill "$SSHD_PID" "$kill_wait"
    log_container_event "[CONTAINER] Shutdown complete. The container exits with status $final_status."  # Report the result after the shutdown, so the operator can match the status to the cause.
    exit "$final_status"  # Report the real status, because a fixed 0 hides a crash from every restart policy.
}
trap cleanup SIGTERM SIGINT

# Start SSH daemon in the background
/usr/sbin/sshd -D &
SSHD_PID=$!
log_container_event "[CONTAINER] Started sshd with PID $SSHD_PID."  # Name the PID, so the operator can match a later crash line to this service.

# Wait for the first service to exit, then report the exit as a fault.
# Warning: "wait -n" returns the status of the service that ended. A discarded
# status makes a crash look like a clean stop, and no restart policy fires.
# See issue #1925.
log_container_event "[CONTAINER] Supervising the web portal (PID $GUNICORN_PID) and sshd (PID $SSHD_PID)."  # Record the start of the supervision, so a later crash line has a start point.
set +e  # Turn off the exit-on-error option, so a crash reaches the report below instead of ending the script in silence.
wait -n "$GUNICORN_PID" "$SSHD_PID" 2>/dev/null
SERVICE_EXIT_STATUS=$?  # Keep the status of the service that ended, because the container must report that status.
set -e  # Restore the exit-on-error option for the rest of the script.

# Name the service that ended.
# The shell reaps the process that "wait -n" returned, so that process no longer
# answers a signal test. The other process still answers.
CRASHED_SERVICE="an unknown service"  # Hold a safe default, because a race can end both services together.
if ! kill -0 "$GUNICORN_PID" 2>/dev/null; then
    CRASHED_SERVICE="the gunicorn web portal"  # The portal no longer answers, so the portal ended first.
elif ! kill -0 "$SSHD_PID" 2>/dev/null; then
    CRASHED_SERVICE="the sshd daemon"  # The daemon no longer answers, so the daemon ended first.
fi

# Turn a status of 0 into a failure status.
# A supervised service must run for the life of the container. An exit is a
# fault even when the service itself reports success.
if [ "$SERVICE_EXIT_STATUS" -eq 0 ]; then
    SERVICE_EXIT_STATUS=1  # Report a failure, because a status of 0 tells the restart policy that the work is complete.
fi

log_container_event "[CONTAINER] ERROR: $CRASHED_SERVICE exited with status $SERVICE_EXIT_STATUS."  # Name the service and the status, because the operator needs both to find the cause.
log_container_event "[CONTAINER] ERROR: The container stops the other service and exits with a failure status."  # State the next step, so the operator knows that a restart policy can act.
cleanup "$SERVICE_EXIT_STATUS"  # Stop the other service, then exit with the captured status.
