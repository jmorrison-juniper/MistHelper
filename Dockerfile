# MistHelper Container Image
# Compatible with both Docker and Podman (OCI-compliant)
# Features: SSH access on port 2200, SQLite persistence, corporate SSL bypass
# Usage: podman build -t misthelper . OR docker build -t misthelper .
FROM python:3.13-slim

# Metadata following OCI standards
LABEL org.opencontainers.image.title="MistHelper"
LABEL org.opencontainers.image.description="Juniper Mist API data export tool with SSH access for corporate environments"
LABEL org.opencontainers.image.version="2.1.0"
LABEL org.opencontainers.image.vendor="Joseph Morrison"
LABEL org.opencontainers.image.authors="Joseph Morrison <jmorrison@juniper.net>"
LABEL org.opencontainers.image.licenses="CC-BY-NC-SA-4.0"
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

# Copy container scripts from maintainable source files
COPY container/scripts/misthelper-session.sh /usr/local/bin/misthelper-session
COPY container/scripts/welcome.sh /home/misthelper/welcome.sh
RUN chmod +x /usr/local/bin/misthelper-session /home/misthelper/welcome.sh && \
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

# Copy and configure container entrypoint script
COPY container/scripts/start.sh /start.sh
RUN chmod +x /start.sh

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

# Expose SSH port 2200 and Dash web viewer port 8050
EXPOSE 2200 8050

# Note: HEALTHCHECK removed for OCI/Podman compatibility
# For health monitoring, use external tools or docker format

# Start both SSH server and MistHelper
USER root
CMD ["/start.sh"]
