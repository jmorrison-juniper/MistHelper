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

# Get unique session ID based on SSH connection
SESSION_ID="${SSH_CONNECTION// /_}"
SESSION_ID="${SESSION_ID//[:.]/_}"
SESSION_DIR="/tmp/misthelper_sessions"
SESSION_FILE="${SESSION_DIR}/session_${SESSION_ID}"
SESSION_PID_FILE="${SESSION_DIR}/pid_${SESSION_ID}"

# Create session directory
mkdir -p "$SESSION_DIR"

# Function to cleanup session on exit
cleanup_session() {
    echo "[SESSION] Cleaning up session $SESSION_ID" >> /app/data/ssh.log
    rm -f "$SESSION_FILE"
    exit 0
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
cd /app

# Main session loop
while true; do
    echo "[SESSION] Starting MistHelper..."
    
    # Run MistHelper and capture exit code
    python MistHelper.py
    EXIT_CODE=$?
    
    # Check if user chose to exit (option 0)
    if [[ $EXIT_CODE -eq 0 ]]; then
        echo "[SESSION] User selected exit. Closing session."
        break
    else
        echo "[SESSION] MistHelper exited with code $EXIT_CODE. Restarting..."
        sleep 2
    fi
done

echo "[SESSION] Session $SESSION_ID terminated." >> /app/data/ssh.log
