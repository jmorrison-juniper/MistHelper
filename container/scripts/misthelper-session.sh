#!/bin/bash
# MistHelper SSH Session Manager
# This script is executed via ForceCommand when users SSH into the container.
# It provides session isolation and automatic MistHelper startup.

set -e

# Container environment variables (SSH sessions don't inherit Docker ENV)
export PYTHONUNBUFFERED=1
export OUTPUT_FORMAT=sqlite
export DATABASE_PATH=/app/data/mist_data.db
export DISABLE_UV_CHECK=true
export DISABLE_AUTO_INSTALL=true
export AUTO_UPGRADE_UV=false
export AUTO_UPGRADE_DEPENDENCIES=false

# Restart controls.
# A failed start repeats when the cause stays, such as a missing dependency or
# a bad configuration file. An unlimited restart loop burns container CPU and
# fills the log file, so the loop stops after a small number of attempts.
# An operator can override each value with an environment variable.

# Largest number of failed starts in a row before the session closes.
# Five attempts take about 30 seconds with the backoff below. That time covers
# a short transient fault, such as a locked database file. It also stops a
# permanent fault quickly.
MAX_START_ATTEMPTS="${MISTHELPER_MAX_START_ATTEMPTS:-5}"

# Smallest run time in seconds that counts as a real session.
# A start that fails at once ends in about one second, so the script counts it
# as a crash. A run that lasts 30 seconds or more shows that MistHelper started
# and served the operator, so that run clears the crash count.
MIN_HEALTHY_SECONDS="${MISTHELPER_MIN_HEALTHY_SECONDS:-30}"

# First delay in seconds before a restart.
# The delay doubles after each failed start. Two seconds keeps the first retry
# fast, which recovers a transient fault without a long wait.
RESTART_DELAY_SECONDS="${MISTHELPER_RESTART_DELAY_SECONDS:-2}"

# Largest delay in seconds between two restarts.
# The cap holds the wait at a value that an operator can watch. The cap also
# stops the delay from growing without a limit.
MAX_RESTART_DELAY_SECONDS="${MISTHELPER_MAX_RESTART_DELAY_SECONDS:-60}"

# Application paths and the Python command.
# The container defaults apply when no override is present. A test harness sets
# these values to run the session loop outside the container.
APP_DIR="${MISTHELPER_APP_DIR:-/app}"
LOG_FILE="${MISTHELPER_LOG_FILE:-${APP_DIR}/data/ssh.log}"
RUNTIME_LOG_FILE="${MISTHELPER_RUNTIME_LOG_FILE:-${APP_DIR}/data/script.log}"
PYTHON_COMMAND="${MISTHELPER_PYTHON:-python}"

# The configuration that the entrypoint carried into this session.
# The SSH daemon starts a fresh environment, so no credential of the container
# reaches this script on its own. `start.sh` writes this file as root, and this
# script is its one reader. Issue #2181 holds the report of the login loop that
# the missing file caused.
SESSION_ENV_FILE="${MISTHELPER_SESSION_ENV_FILE:-/etc/misthelper/session.env}"

# Get unique session ID based on SSH connection
SESSION_ID="${SSH_CONNECTION// /_}"
SESSION_ID="${SESSION_ID//[:.]/_}"
SESSION_DIR="${MISTHELPER_SESSION_DIR:-/tmp/misthelper_sessions}"
SESSION_FILE="${SESSION_DIR}/session_${SESSION_ID}"
SESSION_PID_FILE="${SESSION_DIR}/pid_${SESSION_ID}"

# Create session directory
mkdir -p "$SESSION_DIR"

# Write one line to the operator screen and to the session log.
# The operator loses the screen when the SSH session closes, so the log keeps
# the cause of a failure.
log_session_line() {
    echo "$1"  # Show the line on the terminal, because the operator watches the terminal.
    { echo "$1" >> "$LOG_FILE"; } 2>/dev/null || true  # Keep a copy in the log, and never fail the session on a log write error.
}

# Function to cleanup session on exit
cleanup_session() {
    SESSION_EXIT_STATUS=$?  # Keep the status of the last command, because the session must report a failure to the SSH client.
    { echo "[SESSION] Cleaning up session $SESSION_ID" >> "$LOG_FILE"; } 2>/dev/null || true  # Record the end of the session, and ignore a log write error.
    rm -f "$SESSION_FILE"  # Delete the session marker, because the session is over.
    exit "$SESSION_EXIT_STATUS"  # Report the original status, because a fixed status of 0 hides a crash loop.
}

# Set up signal handlers
trap cleanup_session EXIT INT TERM

# Welcome message
echo "================================================"
echo "    Welcome to MistHelper SSH Service"
echo "    Session ID: $SESSION_ID"
echo "================================================"
echo ""

# Change to application directory
cd "$APP_DIR"

# Read the configuration that the entrypoint carried into this session.
# The file holds one `name=value` line for each name of the allowlist of
# `start.sh`. The `set -a` pair exports every name that the file defines, so
# MistHelper reads them as ordinary environment variables.
if [[ -r "$SESSION_ENV_FILE" ]]; then
    set -a  # Export each name that the next line defines.
    # shellcheck source=/dev/null
    source "$SESSION_ENV_FILE"
    set +a  # Stop the export, so no later variable of this script leaks.
    { echo "[SESSION] Read the session configuration from $SESSION_ENV_FILE" >> "$LOG_FILE"; } 2>/dev/null || true
fi

# Refuse a session that holds no API token.
#
# Why: a missing token is a permanent fault of the configuration. The restart
# loop below treats a failure as a transient fault, so it repeated this one five
# times over about 30 seconds. The operator then read the same error five times
# and had to scroll to find the cause. Issue #2181 holds that report.
#
# The check names the cause once and closes the session. It never prints a token
# value, because the terminal and the log file both keep what it prints.
if [[ -z "${MIST_APITOKEN:-}" && -z "${MIST_API_TOKEN:-}" ]]; then
    log_session_line "[SESSION] This session holds no Mist API token, so MistHelper cannot start."
    log_session_line "[SESSION] The container carries the token into $SESSION_ENV_FILE at start."
    log_session_line "[SESSION] Set MIST_APITOKEN in the .env file of the container, then start the container again."
    exit 1  # Close at once, because a restart repeats a fault that no wait clears.
fi

# Main session loop
FAILED_STARTS=0  # Count the failed starts in a row, because the loop stops at the attempt limit.
RESTART_DELAY="$RESTART_DELAY_SECONDS"  # Hold the delay for the next restart, because the delay grows after each failure.

while true; do
    echo "[SESSION] Starting MistHelper..."

    RUN_START_SECONDS=$SECONDS  # Record the start time, because the run duration separates a crash from a session.

    # Run MistHelper and capture exit code.
    # The `|| EXIT_CODE=$?` form keeps the exit code. A plain command would end
    # the script at once, because `set -e` is active.
    EXIT_CODE=0  # Assume success, because the next line only sets a value on a failure.
    "$PYTHON_COMMAND" MistHelper.py || EXIT_CODE=$?  # Start MistHelper and keep the exit code for the checks below.

    RUN_SECONDS=$(( SECONDS - RUN_START_SECONDS ))  # Measure the run duration, because a long run is not a crash.

    # Check if user chose to exit (option 0)
    if [[ $EXIT_CODE -eq 0 ]]; then
        echo "[SESSION] User selected exit. Closing session."  # Tell the operator that the exit was intentional.
        break  # Leave the loop, because a clean exit needs no restart.
    fi

    # A run that lasted long enough was a real session, not a crash loop.
    if [[ $RUN_SECONDS -ge $MIN_HEALTHY_SECONDS ]]; then
        FAILED_STARTS=0  # Clear the count, because a healthy session must not spend the crash budget.
        RESTART_DELAY="$RESTART_DELAY_SECONDS"  # Restore the first delay, because the next failure starts a new sequence.
    fi

    FAILED_STARTS=$(( FAILED_STARTS + 1 ))  # Count this failure, because the limit applies to failures in a row.

    # Stop the loop at the attempt limit.
    if [[ $FAILED_STARTS -ge $MAX_START_ATTEMPTS ]]; then
        log_session_line "[SESSION] MistHelper failed $FAILED_STARTS times in a row. The last exit code was $EXIT_CODE."  # State the count and the code, because the operator needs both to find the cause.
        log_session_line "[SESSION] The session is closed. To find the cause, read $RUNTIME_LOG_FILE and $LOG_FILE."  # Name the two log files, because a junior operator needs the exact path.
        exit 1  # Close the session with a failure status, because a crash loop must not hold the SSH connection open.
    fi

    echo "[SESSION] MistHelper exited with code $EXIT_CODE. Attempt $FAILED_STARTS of $MAX_START_ATTEMPTS. Next start in $RESTART_DELAY seconds."  # Show the progress, because a silent wait looks like a hang.
    sleep "$RESTART_DELAY"  # Wait before the restart, because an immediate restart repeats the same fault and wastes CPU.

    RESTART_DELAY=$(( RESTART_DELAY * 2 ))  # Double the delay, because a repeated fault needs more time to clear.
    if [[ $RESTART_DELAY -gt $MAX_RESTART_DELAY_SECONDS ]]; then
        RESTART_DELAY="$MAX_RESTART_DELAY_SECONDS"  # Hold the delay at the cap, because an operator must not wait longer than the cap.
    fi
done

{ echo "[SESSION] Session $SESSION_ID terminated." >> "$LOG_FILE"; } 2>/dev/null || true  # Record the clean end of the session, and ignore a log write error.
