"""Pytest fixtures for MistHelper E2E browser tests.

Starts a Gunicorn server on a random port for Playwright tests,
then tears it down after the test session.
"""

import socket
import subprocess
import sys
import time

import pytest


def _find_free_port() -> int:
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def gunicorn_server():
    """Start Gunicorn serving the MistHelper web UI on a random port.

    Yields the base URL (e.g., http://127.0.0.1:54321).
    Terminates the server after all tests complete.
    """
    port = _find_free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "gunicorn",
            "--bind",
            f"127.0.0.1:{port}",
            "--timeout",
            "30",
            "--workers",
            "1",
            "wsgi:app",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{port}"

    # Wait for server to be ready (max 10 seconds)
    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.5)
    else:
        process.terminate()
        raise RuntimeError(f"Gunicorn failed to start on port {port}")

    yield base_url

    process.terminate()
    process.wait(timeout=5)
