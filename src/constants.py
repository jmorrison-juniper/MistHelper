"""MistHelper shared constants and configuration values.

This module centralizes small, commonly-used constants so callers
import values from one place instead of scattering literals.
"""

# Default page limit for Mist API paginated calls; balances throughput and rate limits.
DEFAULT_API_PAGE_LIMIT = 1000

# Name of the environment file that holds API tokens and other secrets (git-ignored).
ENV_FILE = ".env"

# Runtime data directory where CSV/DB outputs and session logs are stored.
DATA_DIR = "data"
