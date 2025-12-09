# MistHelper Simple Container with SSL Bypass for Corporate Environments
# Straightforward approach using pip with trusted hosts
FROM python:3.11-slim

# Metadata following OCI standards
LABEL org.opencontainers.image.title="MistHelper"
LABEL org.opencontainers.image.description="Juniper Mist API data export tool with SSH access for corporate environments"
LABEL org.opencontainers.image.version="2.1.0"
LABEL org.opencontainers.image.vendor="Joseph Morrison"
LABEL org.opencontainers.image.authors="Joseph Morrison <jmorrison@juniper.net>"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.documentation="https://github.com/jmorrison-juniper/MistHelper"
LABEL org.opencontainers.image.source="https://github.com/jmorrison-juniper/MistHelper"
LABEL maintainer="MistHelper Development Team"

# Install minimal system dependencies including SSH server
RUN apt-get update && \
    apt-get install -y ca-certificates openssh-server sudo && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user and configure SSH access
RUN groupadd -r misthelper && useradd -r -g misthelper -m -s /bin/bash misthelper

# Configure SSH server for restricted shell access
RUN mkdir -p /var/run/sshd && \
    mkdir -p /etc/ssh/sshd_config.d && \
    echo "Port 2200" > /etc/ssh/sshd_config.d/misthelper.conf && \
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config.d/misthelper.conf && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config.d/misthelper.conf && \
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config.d/misthelper.conf && \
    echo "AuthorizedKeysFile .ssh/authorized_keys" >> /etc/ssh/sshd_config.d/misthelper.conf && \
    echo "X11Forwarding no" >> /etc/ssh/sshd_config.d/misthelper.conf && \
    echo "PermitTTY yes" >> /etc/ssh/sshd_config.d/misthelper.conf && \
    echo "PermitUserEnvironment no" >> /etc/ssh/sshd_config.d/misthelper.conf && \
    echo "UsePAM yes" >> /etc/ssh/sshd_config.d/misthelper.conf && \
    echo "AllowUsers misthelper" >> /etc/ssh/sshd_config.d/misthelper.conf && \
    echo "ForceCommand /usr/local/bin/misthelper-session" >> /etc/ssh/sshd_config.d/misthelper.conf && \
    ssh-keygen -A

# Set up misthelper user for SSH access and sudo privileges
RUN echo "misthelper:misthelper123!" | chpasswd && \
    usermod -aG sudo misthelper && \
    echo "misthelper ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create the MistHelper session manager script
RUN echo '#!/bin/bash' > /usr/local/bin/misthelper-session && \
    echo 'set -e' >> /usr/local/bin/misthelper-session && \
    echo '' >> /usr/local/bin/misthelper-session && \
    echo '# Get unique session ID based on SSH connection' >> /usr/local/bin/misthelper-session && \
    echo 'SESSION_ID="${SSH_CONNECTION// /_}"' >> /usr/local/bin/misthelper-session && \
    echo 'SESSION_ID="${SESSION_ID//[:.]/_}"' >> /usr/local/bin/misthelper-session && \
    echo 'SESSION_DIR="/tmp/misthelper_sessions"' >> /usr/local/bin/misthelper-session && \
    echo 'SESSION_FILE="${SESSION_DIR}/session_${SESSION_ID}"' >> /usr/local/bin/misthelper-session && \
    echo 'SESSION_PID_FILE="${SESSION_DIR}/pid_${SESSION_ID}"' >> /usr/local/bin/misthelper-session && \
    echo '' >> /usr/local/bin/misthelper-session && \
    echo '# Create session directory' >> /usr/local/bin/misthelper-session && \
    echo 'mkdir -p "$SESSION_DIR"' >> /usr/local/bin/misthelper-session && \
    echo '' >> /usr/local/bin/misthelper-session && \
    echo '# Function to cleanup session on exit' >> /usr/local/bin/misthelper-session && \
    echo 'cleanup_session() {' >> /usr/local/bin/misthelper-session && \
    echo '    echo "[SESSION] Cleaning up session $SESSION_ID" >> /app/data/ssh.log' >> /usr/local/bin/misthelper-session && \
    echo '    rm -f "$SESSION_FILE"' >> /usr/local/bin/misthelper-session && \
    echo '    exit 0' >> /usr/local/bin/misthelper-session && \
    echo '}' >> /usr/local/bin/misthelper-session && \
    echo '' >> /usr/local/bin/misthelper-session && \
    echo '# Set up signal handlers' >> /usr/local/bin/misthelper-session && \
    echo 'trap cleanup_session EXIT INT TERM' >> /usr/local/bin/misthelper-session && \
    echo '' >> /usr/local/bin/misthelper-session && \
    echo '# Welcome message' >> /usr/local/bin/misthelper-session && \
    echo 'echo "================================================"' >> /usr/local/bin/misthelper-session && \
    echo 'echo "    Welcome to MistHelper SSH Service"' >> /usr/local/bin/misthelper-session && \
    echo 'echo "    Session ID: $SESSION_ID"' >> /usr/local/bin/misthelper-session && \
    echo 'echo "================================================"' >> /usr/local/bin/misthelper-session && \
    echo 'echo ""' >> /usr/local/bin/misthelper-session && \
    echo '' >> /usr/local/bin/misthelper-session && \
    echo '# Change to application directory' >> /usr/local/bin/misthelper-session && \
    echo 'cd /app' >> /usr/local/bin/misthelper-session && \
    echo '' >> /usr/local/bin/misthelper-session && \
    echo '# Main session loop' >> /usr/local/bin/misthelper-session && \
    echo 'while true; do' >> /usr/local/bin/misthelper-session && \
    echo '    echo "[SESSION] Starting MistHelper..."' >> /usr/local/bin/misthelper-session && \
    echo '    ' >> /usr/local/bin/misthelper-session && \
    echo '    # Run MistHelper and capture exit code' >> /usr/local/bin/misthelper-session && \
    echo '    python MistHelper.py' >> /usr/local/bin/misthelper-session && \
    echo '    EXIT_CODE=$?' >> /usr/local/bin/misthelper-session && \
    echo '    ' >> /usr/local/bin/misthelper-session && \
    echo '    # Check if user chose to exit (option 0)' >> /usr/local/bin/misthelper-session && \
    echo '    if [[ $EXIT_CODE -eq 0 ]]; then' >> /usr/local/bin/misthelper-session && \
    echo '        echo "[SESSION] User selected exit. Closing session."' >> /usr/local/bin/misthelper-session && \
    echo '        break' >> /usr/local/bin/misthelper-session && \
    echo '    else' >> /usr/local/bin/misthelper-session && \
    echo '        echo "[SESSION] MistHelper exited with code $EXIT_CODE. Restarting..."' >> /usr/local/bin/misthelper-session && \
    echo '        sleep 2' >> /usr/local/bin/misthelper-session && \
    echo '    fi' >> /usr/local/bin/misthelper-session && \
    echo 'done' >> /usr/local/bin/misthelper-session && \
    echo '' >> /usr/local/bin/misthelper-session && \
    echo 'echo "[SESSION] Session $SESSION_ID terminated." >> /app/data/ssh.log' >> /usr/local/bin/misthelper-session && \
    chmod +x /usr/local/bin/misthelper-session

# Create welcome script and add to bashrc for automatic display on SSH login
RUN echo '#!/bin/bash' > /home/misthelper/welcome.sh && \
    echo 'echo ""' >> /home/misthelper/welcome.sh && \
    echo 'echo "======================================"' >> /home/misthelper/welcome.sh && \
    echo 'echo "  Welcome to MistHelper SSH Container"' >> /home/misthelper/welcome.sh && \
    echo 'echo "======================================"' >> /home/misthelper/welcome.sh && \
    echo 'echo ""' >> /home/misthelper/welcome.sh && \
    echo 'echo "Quick Commands:"' >> /home/misthelper/welcome.sh && \
    echo 'echo "  Run MistHelper:     cd /app && python MistHelper.py"' >> /home/misthelper/welcome.sh && \
    echo 'echo "  Run specific menu:  cd /app && python MistHelper.py --menu 11"' >> /home/misthelper/welcome.sh && \
    echo 'echo "  Test mode:          cd /app && python MistHelper.py --test"' >> /home/misthelper/welcome.sh && \
    echo 'echo ""' >> /home/misthelper/welcome.sh && \
    echo 'echo "Data Location: /app/data"' >> /home/misthelper/welcome.sh && \
    echo 'echo "Logs Location: /app/script.log"' >> /home/misthelper/welcome.sh && \
    echo 'echo ""' >> /home/misthelper/welcome.sh && \
    chmod +x /home/misthelper/welcome.sh && \
    echo '~/welcome.sh' >> /home/misthelper/.bashrc && \
    chown misthelper:misthelper /home/misthelper/welcome.sh /home/misthelper/.bashrc

# Set working directory
WORKDIR /app

# Create data directory with proper permissions
RUN mkdir -p /app/data && chown -R misthelper:misthelper /app/data

# Create SSH directory for the misthelper user (needed for paramiko)
RUN mkdir -p /home/misthelper/.ssh && \
    touch /home/misthelper/.ssh/known_hosts && \
    chown -R misthelper:misthelper /home/misthelper/.ssh && \
    chmod 700 /home/misthelper/.ssh && \
    chmod 600 /home/misthelper/.ssh/known_hosts

# Copy requirements first for better Docker layer caching
COPY requirements.txt ./
COPY pyproject.toml ./

# Install Python dependencies with SSL bypass for corporate environments
RUN pip install --no-cache-dir -r requirements.txt \
        --trusted-host pypi.org \
        --trusted-host pypi.python.org \
        --trusted-host files.pythonhosted.org

# Copy application files
COPY MistHelper.py __init__.py ./

# Set ownership and switch to non-root user for application files
RUN chown -R misthelper:misthelper /app

# Create startup script that only runs SSH daemon
USER root
RUN echo '#!/bin/bash' > /start.sh && \
    echo 'set -e' >> /start.sh && \
    echo '' >> /start.sh && \
    echo '# -----------------------------------------------------------------' >> /start.sh && \
    echo '# Dynamic SSH user/password provisioning (runtime, not build time)' >> /start.sh && \
    echo '# SECURITY: Password never echoed. Username may be echoed (not secret).' >> /start.sh && \
    echo '# Variables honored if provided:' >> /start.sh && \
    echo '#   MISTHELPER_SSH_USERNAME  (defaults to misthelper)' >> /start.sh && \
    echo '#   MISTHELPER_SSH_PASSWORD  (defaults to build-time password if omitted)' >> /start.sh && \
    echo '# -----------------------------------------------------------------' >> /start.sh && \
    echo 'USERNAME="${MISTHELPER_SSH_USERNAME:-misthelper}"' >> /start.sh && \
    echo 'PASSWORD="${MISTHELPER_SSH_PASSWORD:-}"' >> /start.sh && \
    echo '' >> /start.sh && \
    echo '# If a different username is requested, create it (idempotent).' >> /start.sh && \
    echo 'if ! id "$USERNAME" >/dev/null 2>&1; then' >> /start.sh && \
    echo '  echo "[SSH] Creating user $USERNAME" >> /app/data/ssh.log' >> /start.sh && \
    echo '  useradd -m -s /bin/bash "$USERNAME" || true' >> /start.sh && \
    echo '  usermod -aG sudo "$USERNAME" || true' >> /start.sh && \
    echo '  # Ensure /app readable; retain original ownership on writable paths' >> /start.sh && \
    echo '  chown -R "$USERNAME" /app/data 2>/dev/null || true' >> /start.sh && \
    echo 'fi' >> /start.sh && \
    echo '' >> /start.sh && \
    echo '# Update password if provided (non-empty).' >> /start.sh && \
    echo 'if [ -n "$PASSWORD" ]; then' >> /start.sh && \
    echo '  echo "$USERNAME:$PASSWORD" | chpasswd' >> /start.sh && \
    echo '  echo "[SSH] Applied runtime password for $USERNAME" >> /app/data/ssh.log' >> /start.sh && \
    echo 'else' >> /start.sh && \
    echo '  echo "[SSH] No runtime password override provided; using build-time password." >> /app/data/ssh.log' >> /start.sh && \
    echo 'fi' >> /start.sh && \
    echo '' >> /start.sh && \
    echo '# Adjust AllowUsers directive to reflect chosen username.' >> /start.sh && \
    echo 'if [ -f /etc/ssh/sshd_config.d/misthelper.conf ]; then' >> /start.sh && \
    echo '  if grep -q "^AllowUsers " /etc/ssh/sshd_config.d/misthelper.conf; then' >> /start.sh && \
    echo '    sed -i "s/^AllowUsers .*/AllowUsers $USERNAME/" /etc/ssh/sshd_config.d/misthelper.conf' >> /start.sh && \
    echo '  else' >> /start.sh && \
    echo '    echo "AllowUsers $USERNAME" >> /etc/ssh/sshd_config.d/misthelper.conf' >> /start.sh && \
    echo '  fi' >> /start.sh && \
    echo 'fi' >> /start.sh && \
    echo '' >> /start.sh && \
    echo 'echo "[SSH] Starting MistHelper SSH Service on port 2200..." >> /app/data/ssh.log' >> /start.sh && \
    echo 'echo "[SSH] Each SSH connection spawns its own MistHelper session." >> /app/data/ssh.log' >> /start.sh && \
    echo 'echo "[SSH] Connect with: ssh -p 2200 $USERNAME@<container-ip>" >> /app/data/ssh.log' >> /start.sh && \
    echo 'echo "[SSH] Use option 0 in MistHelper to disconnect." >> /app/data/ssh.log' >> /start.sh && \
    echo '' >> /start.sh && \
    echo '# Run SSH daemon in foreground' >> /start.sh && \
    echo 'exec /usr/sbin/sshd -D' >> /start.sh && \
    chmod +x /start.sh

USER misthelper

# Environment variables for SSL bypass and container-specific configurations
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_FORMAT=sqlite
ENV DATABASE_PATH=/app/data/mist_data.db
ENV PYTHONHTTPSVERIFY=0
ENV SSL_VERIFY=false
ENV REQUESTS_CA_BUNDLE=""
ENV CURL_CA_BUNDLE=""
# Container-specific overrides: Disable UV and auto-installation for reliability
ENV DISABLE_UV_CHECK=true
ENV DISABLE_AUTO_INSTALL=true
ENV AUTO_UPGRADE_UV=false
ENV AUTO_UPGRADE_DEPENDENCIES=false

# Volume for data persistence
VOLUME ["/app/data"]

# Expose SSH port 2200 for remote access
EXPOSE 2200

# Note: HEALTHCHECK removed for OCI/Podman compatibility
# For health monitoring, use external tools or docker format

# Start both SSH server and MistHelper
USER root
CMD ["/start.sh"]
