# MistHelper Container Image
# Compatible with both Docker and Podman (OCI-compliant)
# Features: SSH access on port 2200, SQLite persistence, TLS verification on
# Usage: podman build -t misthelper . OR docker build -t misthelper .
#
# Corporate proxy support (issue #1906):
# The image verifies every TLS certificate. It never disables the check.
# If you build behind a TLS-inspecting proxy, add the proxy root certificate:
#   podman build --build-arg INSTALL_CORPORATE_CA=true -t misthelper .
# At run time, mount the proxy root certificate instead:
#   -v /path/to/corp-root-ca.crt:/usr/local/share/ca-certificates/corp-root-ca.crt:ro
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

# Optional corporate root certificate for a TLS-inspecting proxy.
# The build keeps certificate verification on. It never turns the check off.
# Set INSTALL_CORPORATE_CA=true to add the supplied root certificate to the
# system trust store. The default value of false ships a clean trust store.
ARG INSTALL_CORPORATE_CA=false
ARG CORPORATE_CA_FILE=zscaler-root-ca.crt
COPY ${CORPORATE_CA_FILE} /tmp/corporate-root-ca.crt
RUN if [ "${INSTALL_CORPORATE_CA}" = "true" ]; then \
        echo "[TLS] Adding the corporate root certificate to the trust store" && \
        cp /tmp/corporate-root-ca.crt /usr/local/share/ca-certificates/corporate-root-ca.crt && \
        update-ca-certificates ; \
    else \
        echo "[TLS] Skipping the corporate root certificate. The default trust store applies." ; \
    fi && \
    rm -f /tmp/corporate-root-ca.crt

# Copy requirements first for better Docker layer caching
COPY requirements.txt ./
COPY pyproject.toml ./

# Install Python dependencies. Every download validates the TLS certificate.
# Warning: Do not add --trusted-host. That flag disables certificate
# verification and lets an attacker replace a package during the build.
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY MistHelper.py __init__.py wsgi.py ./
COPY src/ ./src/
COPY web_portal/ ./web_portal/

# Set ownership and switch to non-root user for application files
RUN chown -R misthelper:misthelper /app

# Copy and configure container entrypoint script
COPY container/scripts/start.sh /start.sh
RUN chmod +x /start.sh

USER misthelper

# Environment variables for container-specific configurations
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_FORMAT=sqlite
ENV DATABASE_PATH=/app/data/mist_data.db
# TLS trust settings. The image verifies every certificate by default.
# update-ca-certificates writes the merged bundle to this same path, so a
# mounted corporate root certificate works without any further change.
ENV PYTHONHTTPSVERIFY=1
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
# Container-specific overrides: Disable UV and auto-installation for reliability
ENV DISABLE_UV_CHECK=true
ENV DISABLE_AUTO_INSTALL=true
ENV AUTO_UPGRADE_UV=false
ENV AUTO_UPGRADE_DEPENDENCIES=false
# Web portal port (must match EXPOSE)
ENV WEB_PORT=8055

# Volume for data persistence
VOLUME ["/app/data"]

# Expose SSH port 2200 and web portal port 8055
EXPOSE 2200 8055

# Health probe for the web portal readiness endpoint (issue #1863).
# The image installs no curl, so the probe uses the Python interpreter that
# already runs the application. A non-200 response raises HTTPError, the
# command exits non-zero, and the runtime marks the container unhealthy.
# Podman honours this instruction when it builds in the Docker format. A build
# that uses the OCI format drops the instruction instead of failing, so
# deploy/misthelper.container also defines HealthCmd for the Quadlet unit.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('WEB_PORT','8055')+'/ready',timeout=8)"]

# Start both SSH server and MistHelper
USER root
CMD ["/start.sh"]
