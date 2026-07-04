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

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: debug logs on every detection branch
import os  # WHY: env vars + file existence probes

logger = logging.getLogger(__name__)  # Module-scoped logger for detection tracing

# Truthy strings accepted from override env vars. Kept as a module
# constant so both ``_check_env_override`` and any future opt-in
# heuristics share the same acceptance set.
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})  # WHY: shared truthy set for env overrides

# Explicit override vars: these let operators force container-mode
# behavior when the auto-detection heuristics fail (e.g. exotic
# runtimes, chroots, or when we want to test container UX locally).
_OVERRIDE_ENV_VARS = ("MISTHELPER_FORCE_CONTAINER_LOOP", "MISTHELPER_CONTAINER")  # WHY: operator escape hatch

# Widely-set env vars that container runtimes and orchestrators inject.
# KUBERNETES_SERVICE_HOST catches k8s pods where none of the other
# markers may exist (distroless images).
_CONTAINER_ENV_VARS = (  # WHY: multi-runtime env-var whitelist
    "CONTAINER",
    "DOCKER_CONTAINER",
    "PODMAN_CONTAINER",
    "KUBERNETES_SERVICE_HOST",
    "CONTAINERD_NAMESPACE",
)

# cgroup fingerprints that indicate we are inside a container. The
# check reads /proc/1/cgroup because init's cgroup path leaks the
# runtime's slice name on Linux.
_CGROUP_INDICATORS = ("docker", "containerd", "podman", "lxc")  # WHY: init cgroup substrings we treat as positive


def _check_env_override() -> bool:  # WHY: explicit operator opt-in fires first
    """Return True when an explicit override env var is set."""
    for explicit_var in _OVERRIDE_ENV_VARS:  # Walk each configured override name
        value = os.environ.get(explicit_var, "").strip().lower()  # Normalize for the truthy set
        if value in _TRUE_VALUES:  # Explicit opt-in matched
            logger.debug("Container detection: override via %s=%s", explicit_var, value)  # Trace which var fired
            return True  # WHY: caller only needs a single positive signal
    return False  # No override set


def _check_sentinel_files() -> bool:  # WHY: cheap file-existence probe for docker sentinel
    """Return True when Docker's /.dockerenv sentinel file exists."""
    if os.path.exists("/.dockerenv"):  # Docker injects this marker on every container
        logger.debug("Container detection: /.dockerenv present")  # Trace the positive hit
        return True  # WHY: single positive signal is enough for detection
    return False  # No sentinel found


def _check_container_env_vars() -> bool:  # WHY: runtime/orchestrator env-var scan
    """Return True when any well-known container env var is present."""
    for env_var in _CONTAINER_ENV_VARS:  # Walk each known runtime/orchestrator marker
        if os.environ.get(env_var):  # Presence alone is the signal
            logger.debug("Container detection: environment variable %s present", env_var)  # Trace which var fired
            return True  # WHY: single positive signal is enough for detection
    return False  # No matching env var set


def _check_cgroup_markers() -> bool:  # WHY: Linux init cgroup fingerprint scan
    """Return True when /proc/1/cgroup mentions a container runtime."""
    try:  # /proc/1/cgroup absent on non-Linux; permission may be restricted
        with open("/proc/1/cgroup", encoding="utf-8", errors="ignore") as cgroup_file:  # Read init's cgroup path
            cgroup_content = cgroup_file.read().lower()  # Normalize case for substring match
    except (FileNotFoundError, PermissionError):  # Non-Linux or restricted env
        return False  # WHY: treat unreadable cgroup as "not a container"
    for indicator in _CGROUP_INDICATORS:  # Walk each configured runtime substring
        if indicator in cgroup_content:  # Presence of runtime slice name -> container
            logger.debug("Container detection: cgroup indicator '%s' found", indicator)  # Trace matched runtime
            return True  # WHY: single positive signal is enough for detection
    return False  # No indicator found in cgroup content


def _check_runtime_user() -> bool:  # WHY: image-conventional user identity probe
    """Return True when running as the canonical 'misthelper' user (Unix only)."""
    try:  # pwd is Unix-only; getuid absent on Windows
        import pwd  # Unix only; import lazily to keep Windows imports clean.

        current_user_name = pwd.getpwuid(os.getuid()).pw_name  # type: ignore[attr-defined]
    except Exception:  # Non-Unix or lookup failure
        logger.debug("Container detection: user lookup failed (non-Unix or unavailable)")  # Trace fallback
        return False  # WHY: cannot confirm without a valid uid
    if current_user_name == "misthelper":  # Canonical account name baked into our image
        logger.debug("Container detection: running as user 'misthelper'")  # Trace image-user match
        return True  # WHY: single positive signal is enough for detection
    return False  # Different user -> not our container


def _check_app_path() -> bool:  # WHY: composite /app + sshd layout fingerprint
    """Return True when this module lives under /app alongside sshd (container layout)."""
    try:  # Some importers (frozen apps) may not expose __file__
        this_file_dir = os.path.abspath(os.path.dirname(__file__))  # Absolute path of this module
    except Exception:  # __file__ missing or unreadable
        logger.debug("Container detection: path heuristic check failed")  # Trace fallback
        return False  # WHY: cannot evaluate layout without a real path
    # All three signals must align to avoid false positives on host
    # systems that happen to have a top-level /app directory.
    if not this_file_dir.startswith("/app"):  # Not the image install prefix
        return False  # First signal missing
    if not os.path.exists("/app/MistHelper.py"):  # Image-only entrypoint marker
        return False  # Second signal missing
    if not os.path.exists("/usr/sbin/sshd"):  # sshd is bundled in the container image
        return False  # Third signal missing
    logger.debug("Container detection: /app path with MistHelper.py and sshd present")  # Trace composite match
    return True  # WHY: all three layout signals aligned


# Ordered so cheap env checks run before the file-system probes.
_CONTAINER_CHECKS = (  # WHY: ordered probe list runs cheap checks first
    _check_env_override,
    _check_sentinel_files,
    _check_container_env_vars,
    _check_cgroup_markers,
    _check_runtime_user,
    _check_app_path,
)


def is_running_in_container() -> bool:  # WHY: public orchestrator across all detection probes
    """Return True when the interpreter appears to be inside a container.

    Any single positive check trips the return value. Failures inside a
    heuristic are logged and treated as "did not detect" so a broken
    probe never masks a real positive from a later probe.

    SECURITY: Result only toggles UX (continuous menu loop). No
    privileged operations are gated on this signal.
    """
    for check in _CONTAINER_CHECKS:  # Walk each probe in configured order
        try:  # Isolate per-probe failures so one broken check cannot mask others
            if check():  # Positive result short-circuits the scan
                return True  # WHY: any single positive signal is enough
        except Exception as container_detection_error:  # Broken probe -> treat as "did not detect"
            logger.debug("Container detection failed with exception: %s", container_detection_error)  # Trace the fault
    logger.debug("Container detection: no container indicators - direct mode")  # Trace negative outcome
    return False  # WHY: no probe reported a positive signal
