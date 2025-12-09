# MistHelper Docker-Compatible Containerfile
# This version includes HEALTHCHECK for Docker format compatibility
FROM python:3.11-slim

# Metadata
LABEL maintainer="Joseph Morrison <jmorrison@juniper.net>"
LABEL description="Smart MistHelper container with automatic UV/pip fallback (Docker format)"
LABEL version="2.1.0"
LABEL org.opencontainers.image.source="https://github.com/jmorrison-juniper/MistHelper"
LABEL org.opencontainers.image.licenses="AGPL-3.0-only"

# Install system dependencies (curl for UV, but don't fail if unavailable)
RUN apt-get update && \
    (apt-get install -y curl ca-certificates || echo "Curl not available - will use pip") && \
    rm -rf /var/lib/apt/lists/* || true

# Create application user
RUN groupadd -r misthelper && useradd -r -g misthelper misthelper
WORKDIR /app

# Create data directory
RUN mkdir -p /app/data && chown -R misthelper:misthelper /app/data

# Copy dependency files
COPY requirements.txt ./
COPY pyproject.toml ./

# Smart dependency installation with SSL fixes
RUN echo "🚀 Attempting smart dependency installation..." && \
    if curl -LsSf --cacert /etc/ssl/certs/ca-certificates.crt https://astral.sh/uv/install.sh | sh 2>/dev/null; then \
        echo "✅ UV installer downloaded successfully (with CA certs)" && \
        export PATH="/root/.cargo/bin:$PATH" && \
        export UV_SYSTEM_PYTHON=1 && \
        if uv pip install -r requirements.txt 2>/dev/null; then \
            echo "✅ Dependencies installed with UV (fast)"; \
        else \
            echo "⚠️ UV failed, falling back to pip..." && \
            pip install --no-cache-dir -r requirements.txt && \
            echo "✅ Dependencies installed with pip (fallback)"; \
        fi; \
        echo "✅ All dependencies installation completed"; \
    elif curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null; then \
        echo "✅ UV installer downloaded successfully (standard SSL)" && \
        export PATH="/root/.cargo/bin:$PATH" && \
        export UV_SYSTEM_PYTHON=1 && \
        if uv pip install -r requirements.txt 2>/dev/null; then \
            echo "✅ Dependencies installed with UV (fast)"; \
        else \
            echo "⚠️ UV failed, falling back to pip..." && \
            pip install --no-cache-dir -r requirements.txt && \
            echo "✅ Dependencies installed with pip (fallback)"; \
        fi; \
        echo "✅ All dependencies installation completed"; \
    elif curl -LsSf --insecure https://astral.sh/uv/install.sh | sh 2>/dev/null; then \
        echo "✅ UV installer downloaded successfully (SSL bypassed)" && \
        export PATH="/root/.cargo/bin:$PATH" && \
        export UV_SYSTEM_PYTHON=1 && \
        if uv pip install -r requirements.txt 2>/dev/null; then \
            echo "✅ Dependencies installed with UV (fast, SSL bypassed)"; \
        else \
            echo "⚠️ UV failed, falling back to pip..." && \
            pip install --no-cache-dir -r requirements.txt && \
            echo "✅ Dependencies installed with pip (fallback)"; \
        fi; \
        echo "✅ All dependencies installation completed"; \
    else \
        echo "⚠️ UV not available (SSL issues), using pip..." && \
        pip install --no-cache-dir -r requirements.txt && \
        echo "✅ All dependencies installation completed"; \
    fi

# Copy application files
COPY MistHelper.py __init__.py ./

# Set ownership and switch to non-root user
RUN chown -R misthelper:misthelper /app
USER misthelper

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_FORMAT=sqlite
ENV DATABASE_PATH=/app/data/mist_data.db

# Volume for data persistence
VOLUME ["/app/data"]

# Health check (Docker format compatible)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('/app/data/mist_data.db'); conn.close()" || exit 1

# Default command - show interactive menu with default output format
CMD ["python", "MistHelper.py"]
