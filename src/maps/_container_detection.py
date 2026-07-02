"""Container-runtime detection heuristics used by the maps CLI.

Extracted from ``src/maps/maps_manager.py`` so that runtime-environment
inspection lives in one small focused module. A positive
``is_running_in_container()`` result flips the maps CLI into a
continuous-loop mode instead of exiting after one menu round.

The detection is deliberately multi-factor because no single indicator
is reliable across Docker, Podman, Kubernetes, LXC, and rootless
runtimes -- if any one heuristic fires we treat the environment as a
container and let downstream code adapt.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Truthy strings accepted from override env vars. Kept as a module
# constant so both ``_check_env_override`` and any future opt-in
# heuristics share the same acceptance set.
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})

# Explicit override vars: these let operators force container-mode
# behavior when the auto-detection heuristics fail (e.g. exotic
# runtimes, chroots, or when we want to test container UX locally).
_OVERRIDE_ENV_VARS = ("MISTHELPER_FORCE_CONTAINER_LOOP", "MISTHELPER_CONTAINER")

# Widely-set env vars that container runtimes and orchestrators inject.
# KUBERNETES_SERVICE_HOST catches k8s pods where none of the other
# markers may exist (distroless images).
_CONTAINER_ENV_VARS = (
    "CONTAINER",
    "DOCKER_CONTAINER",
    "PODMAN_CONTAINER",
    "KUBERNETES_SERVICE_HOST",
    "CONTAINERD_NAMESPACE",
)

# cgroup fingerprints that indicate we are inside a container. The
# check reads /proc/1/cgroup because init's cgroup path leaks the
# runtime's slice name on Linux.
_CGROUP_INDICATORS = ("docker", "containerd", "podman", "lxc")


def _check_env_override() -> bool:
    """Return True when an explicit override env var is set."""
    for explicit_var in _OVERRIDE_ENV_VARS:
        value = os.environ.get(explicit_var, "").strip().lower()
        if value in _TRUE_VALUES:
            logger.debug("Container detection: override via %s=%s", explicit_var, value)
            return True
    return False


def _check_sentinel_files() -> bool:
    """Return True when Docker's /.dockerenv sentinel file exists."""
    if os.path.exists("/.dockerenv"):
        logger.debug("Container detection: /.dockerenv present")
        return True
    return False


def _check_container_env_vars() -> bool:
    """Return True when any well-known container env var is present."""
    for env_var in _CONTAINER_ENV_VARS:
        if os.environ.get(env_var):
            logger.debug("Container detection: environment variable %s present", env_var)
            return True
    return False


def _check_cgroup_markers() -> bool:
    """Return True when /proc/1/cgroup mentions a container runtime."""
    try:
        with open("/proc/1/cgroup", encoding="utf-8", errors="ignore") as cgroup_file:
            cgroup_content = cgroup_file.read().lower()
    except (FileNotFoundError, PermissionError):
        return False
    for indicator in _CGROUP_INDICATORS:
        if indicator in cgroup_content:
            logger.debug("Container detection: cgroup indicator '%s' found", indicator)
            return True
    return False


def _check_runtime_user() -> bool:
    """Return True when running as the canonical 'misthelper' user (Unix only)."""
    try:
        import pwd  # Unix only; import lazily to keep Windows imports clean.

        current_user_name = pwd.getpwuid(os.getuid()).pw_name  # type: ignore[attr-defined]
    except Exception:
        logger.debug("Container detection: user lookup failed (non-Unix or unavailable)")
        return False
    if current_user_name == "misthelper":
        logger.debug("Container detection: running as user 'misthelper'")
        return True
    return False


def _check_app_path() -> bool:
    """Return True when this module lives under /app alongside sshd (container layout)."""
    try:
        this_file_dir = os.path.abspath(os.path.dirname(__file__))
    except Exception:
        logger.debug("Container detection: path heuristic check failed")
        return False
    # All three signals must align to avoid false positives on host
    # systems that happen to have a top-level /app directory.
    if not this_file_dir.startswith("/app"):
        return False
    if not os.path.exists("/app/MistHelper.py"):
        return False
    if not os.path.exists("/usr/sbin/sshd"):
        return False
    logger.debug("Container detection: /app path with MistHelper.py and sshd present")
    return True


# Ordered so cheap env checks run before the file-system probes.
_CONTAINER_CHECKS = (
    _check_env_override,
    _check_sentinel_files,
    _check_container_env_vars,
    _check_cgroup_markers,
    _check_runtime_user,
    _check_app_path,
)


def is_running_in_container() -> bool:
    """Return True when the interpreter appears to be inside a container.

    Any single positive check trips the return value. Failures inside a
    heuristic are logged and treated as "did not detect" so a broken
    probe never masks a real positive from a later probe.

    SECURITY: Result only toggles UX (continuous menu loop). No
    privileged operations are gated on this signal.
    """
    for check in _CONTAINER_CHECKS:
        try:
            if check():
                return True
        except Exception as container_detection_error:
            logger.debug("Container detection failed with exception: %s", container_detection_error)
    logger.debug("Container detection: no container indicators found - running in direct mode")
    return False
