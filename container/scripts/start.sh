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

# Repair container name resolution before any service starts.
#
# Why: the container must resolve api.mist.com. Under Podman the container gets
# one nameserver, the Podman DNS proxy on the bridge gateway. That proxy answers
# a container name, and it forwards every other name to an upstream resolver.
# When the network holds no upstream resolver, the proxy forwards nothing, and
# every Mist API call fails with "Temporary failure in name resolution".
#
# The manual repair is "podman network update <network> --dns-add <address>".
# That command is manual, and "compose down" discards the network, so the repair
# does not survive a restart. This step removes the manual work. It reads the
# resolver list of the host, which compose mounts at /etc/resolv.conf.host, and
# it adds the first address that answers.
#
# The step runs before every service, because a service that starts without name
# resolution reports a wrong fault to the operator.
#
# Warning: keep the "|| true" guard. A container that cannot resolve a name must
# still start, because the portal then names the fault. A container that never
# starts gives the operator no message at all.
DNS_PREFLIGHT_REPORT="$(cd /app && /usr/local/bin/python3.13 -m src.bootstrap.dns_preflight 2>/dev/null)" || true
if [ -n "$DNS_PREFLIGHT_REPORT" ]; then
    log_container_event "$DNS_PREFLIGHT_REPORT"  # One line, so the container log stays readable.
else
    log_container_event "[DNS] WARNING: the name resolution preflight did not run."
fi

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

# Carry the runtime configuration into every SSH session.
#
# Why: `compose.yml` supplies the credentials through `env_file`, which fills
# the environment of this process and writes no file. The SSH daemon starts each
# session with a fresh environment, and `PermitUserEnvironment` stays off. A
# session therefore reached MistHelper with no API token, the preflight refused,
# and the restart loop repeated the same permanent fault five times. Issue #2181
# holds that report.
#
# This step runs as root, so it is the one writer. `misthelper-session.sh` is
# the one reader. The helper script owns the allowlist and the file mode, so a
# test proves those rules without a container start.
SESSION_ENV_FILE="${MISTHELPER_SESSION_ENV_FILE:-/etc/misthelper/session.env}"
SESSION_ENV_WRITER="${MISTHELPER_SESSION_ENV_WRITER:-/usr/local/bin/write-session-env.sh}"

if [ -x "$SESSION_ENV_WRITER" ]; then
    if SESSION_ENV_REPORT="$("$SESSION_ENV_WRITER" "$USERNAME" "$SESSION_ENV_FILE")"; then
        log_container_event "$SESSION_ENV_REPORT"  # The helper names the variables and prints no value.
    else
        log_container_event "[SSH] WARNING: could not write $SESSION_ENV_FILE. An SSH session will find no API token."
    fi
else
    log_container_event "[SSH] WARNING: $SESSION_ENV_WRITER is missing. An SSH session will find no API token."
fi

# Determine web portal port (default 8055)
WEB_PORT="${WEB_PORT:-8055}"

# Read the grace period, so bash and the Python shutdown path share one value.
SHUTDOWN_GRACE_SECONDS="${PORTAL_OPERATION_SHUTDOWN_GRACE_SECONDS:-30}"
# Add a margin past the grace period, so bash waits longer than Gunicorn before it forces a kill.
CONTAINER_KILL_MARGIN_SECONDS=10

# Start Gunicorn web portal in the background
# Warning: do not add a dash to `su`. A dash starts a login shell, which clears
# the environment. Every runtime variable that `compose.yml` supplies is then
# lost, and the portal starts with no database address and no allow list.
log_container_event "[PORTAL] Starting the web portal on port $WEB_PORT."  # Report the start before the launch, so a failed launch has a start point in the log.
su misthelper -c "cd /app && gunicorn wsgi:app \
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
SNMPD_PID=""  # Clear the snmpd PID, because a signal can start the cleanup before the daemon starts.
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

# Determine upgrade capture portal port (default 8056)
CAPTURE_PORT="${CAPTURE_PORT:-8056}"

# Determine the unprivileged SNMP service port and community.
SNMP_PORT="${SNMP_PORT:-1161}"
SNMP_COMMUNITY="${SNMP_COMMUNITY:-misthelper}"
SNMP_BASE_OID="${SNMP_BASE_OID:-${METRICS_SNMP_BASE_OID:-.1.3.6.1.4.1.11.2147483646}}"
SNMP_CONFIG="/etc/snmp/snmpd.conf"
if ! [[ "$SNMP_PORT" =~ ^[0-9]+$ ]] || [ "$SNMP_PORT" -lt 1024 ] || [ "$SNMP_PORT" -gt 65535 ]; then
    log_container_event "[SNMP] ERROR: SNMP_PORT must be between 1024 and 65535."
    exit 1
fi
if ! [[ "$SNMP_COMMUNITY" =~ ^[A-Za-z0-9_.-]+$ ]]; then
    log_container_event "[SNMP] ERROR: SNMP_COMMUNITY contains unsupported characters."
    exit 1
fi
printf '%s\n' \
    "agentAddress udp:${SNMP_PORT}" \
    "rocommunity ${SNMP_COMMUNITY} 0.0.0.0/0" \
    "pass_persist ${SNMP_BASE_OID} /usr/local/bin/python3.13 /app/MistHelper.py --metrics-snmp" \
    > "$SNMP_CONFIG"

# Stop Net-SNMP from loading a MIB file at startup.
#
# Why: Debian ships no IETF or IANA MIB file, because the license does not
# permit redistribution. Net-SNMP still tries to load every module, so it prints
# about 520 parse errors such as "Cannot find module (SNMPv2-SMI)" and
# "Undefined identifier: enterprises". The errors flood the container log on
# every start, and they hide a real fault.
#
# The agent needs no MIB file. A MIB translates a number into a name, and that
# translation belongs to the monitoring system. Observium loads
# documentation/mibs/MISTHELPER-MIB.mib for that purpose.
#
# This file serves the command line tools that an operator runs inside the
# container, such as snmpget and snmpwalk. The token is the value Debian ships
# in its own snmp.conf for the same reason.
printf '%s\n' \
    "# The agent serves numeric OIDs only, so it loads no MIB file." \
    "mibs :" \
    > /etc/snmp/snmp.conf

# Warning: the file above does not reach snmpd. The daemon starts with -C, which
# tells Net-SNMP to read the one named file and to skip every default file,
# including snmp.conf. An empty MIBS value is the only setting that reaches the
# daemon, so export it here. Removing this line returns about 520 error lines to
# the container log.
export MIBS=

# Start the capture portal in a second Gunicorn process.
# A separate process keeps a long upgrade run away from the data browsing
# portal, so a fault in one portal cannot stop the other.
# Warning: `su` carries no dash here for the reason given above. With a dash,
# CAPTURE_ALLOWED_IPS never reaches the portal and every client address passes.
log_container_event "[CAPTURE] Starting the upgrade capture portal on port $CAPTURE_PORT."  # Report the start before the launch, so a failed launch has a start point in the log.
su misthelper -c "cd /app && gunicorn wsgi_capture:app \
    --bind 0.0.0.0:${CAPTURE_PORT} \
    --workers 1 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --access-logfile /app/data/capture_access.log \
    --error-logfile /app/data/capture_error.log" &
CAPTURE_PID=$!
log_container_event "[CAPTURE] Started the upgrade capture portal with PID $CAPTURE_PID."  # Name the PID, so the operator can match a later crash line to this service.

# Trap signals to stop every process
cleanup() {
    local final_status="${1:-0}"  # Default to 0, because an operator stop is a success and needs no restart.
    log_container_event "[CONTAINER] Shutting down. The exit status will be $final_status."  # Report the plan before the shutdown, so the operator sees the cause order.
    # Match the bash-side deadline to Gunicorn's own --graceful-timeout, plus a margin.
    local kill_wait
    kill_wait=$((SHUTDOWN_GRACE_SECONDS + CONTAINER_KILL_MARGIN_SECONDS))
    kill "$GUNICORN_PID" 2>/dev/null || true
    kill "$CAPTURE_PID" 2>/dev/null || true
    kill "$SSHD_PID" 2>/dev/null || true
    kill "$SNMPD_PID" 2>/dev/null || true
    # Wait for a clean exit within the bound, so an in-flight operation can finish first.
    _wait_for_pid_or_kill "$GUNICORN_PID" "$kill_wait"
    _wait_for_pid_or_kill "$CAPTURE_PID" "$kill_wait"
    _wait_for_pid_or_kill "$SSHD_PID" "$kill_wait"
    _wait_for_pid_or_kill "$SNMPD_PID" "$kill_wait"
    log_container_event "[CONTAINER] Shutdown complete. The container exits with status $final_status."  # Report the result after the shutdown, so the operator can match the status to the cause.
    exit "$final_status"  # Report the real status, because a fixed 0 hides a crash from every restart policy.
}
trap cleanup SIGTERM SIGINT

# Start SSH daemon in the background
/usr/sbin/sshd -D &
SSHD_PID=$!
log_container_event "[CONTAINER] Started sshd with PID $SSHD_PID."  # Name the PID, so the operator can match a later crash line to this service.

# Start Net-SNMP on the unprivileged published port.
log_container_event "[SNMP] Starting snmpd on UDP port $SNMP_PORT."
/usr/sbin/snmpd -f -Lo -C -c "$SNMP_CONFIG" &
SNMPD_PID=$!
log_container_event "[SNMP] Started snmpd with PID $SNMPD_PID."  # Name the PID for service supervision.

# Wait for the first service to exit, then report the exit as a fault.
# Warning: "wait -n" returns the status of the service that ended. A discarded
# status makes a crash look like a clean stop, and no restart policy fires.
# See issue #1925.
log_container_event "[CONTAINER] Supervising the web portal (PID $GUNICORN_PID), the capture portal (PID $CAPTURE_PID), sshd (PID $SSHD_PID), and snmpd (PID $SNMPD_PID)."  # Record the start of the supervision, so a later crash line has a start point.
set +e  # Turn off the exit-on-error option, so a crash reaches the report below instead of ending the script in silence.
wait -n "$GUNICORN_PID" "$CAPTURE_PID" "$SSHD_PID" "$SNMPD_PID" 2>/dev/null
SERVICE_EXIT_STATUS=$?  # Keep the status of the service that ended, because the container must report that status.
set -e  # Restore the exit-on-error option for the rest of the script.

# Name the service that ended.
# The shell reaps the process that "wait -n" returned, so that process no longer
# answers a signal test. The other process still answers.
CRASHED_SERVICE="an unknown service"  # Hold a safe default, because a race can end both services together.
if ! kill -0 "$GUNICORN_PID" 2>/dev/null; then
    CRASHED_SERVICE="the gunicorn web portal"  # The portal no longer answers, so the portal ended first.
elif ! kill -0 "$CAPTURE_PID" 2>/dev/null; then
    CRASHED_SERVICE="the upgrade capture portal"  # The capture portal no longer answers, so it ended first.
elif ! kill -0 "$SSHD_PID" 2>/dev/null; then
    CRASHED_SERVICE="the sshd daemon"  # The daemon no longer answers, so the daemon ended first.
elif ! kill -0 "$SNMPD_PID" 2>/dev/null; then
    CRASHED_SERVICE="the snmpd daemon"  # The daemon no longer answers, so the daemon ended first.
fi

# Turn a status of 0 into a failure status.
# A supervised service must run for the life of the container. An exit is a
# fault even when the service itself reports success.
if [ "$SERVICE_EXIT_STATUS" -eq 0 ]; then
    SERVICE_EXIT_STATUS=1  # Report a failure, because a status of 0 tells the restart policy that the work is complete.
fi

log_container_event "[CONTAINER] ERROR: $CRASHED_SERVICE exited with status $SERVICE_EXIT_STATUS."  # Name the service and the status, because the operator needs both to find the cause.
log_container_event "[CONTAINER] ERROR: The container stops the other services and exits with a failure status."  # State the next step, so the operator knows that a restart policy can act.
cleanup "$SERVICE_EXIT_STATUS"  # Stop the other services, then exit with the captured status.
