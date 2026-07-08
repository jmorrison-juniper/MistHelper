"""EnvironmentUtils -- runtime/container environment detection.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 33).
Self-contained module: no live-global reads, so no lazy MistHelper import
is required. Direct imports cover stdlib only (os, logging). Callers
continue to reach the class through the ``MistHelper.EnvironmentUtils``
re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import logging  # WHY: structured trace for container detection lifecycle events.
import os  # WHY: environment variable + filesystem probes for container detection.


class EnvironmentUtils:
    """Centralized environment detection utilities.

    Handles container detection, runtime environment identification, etc.
    """

    # Constants for container detection
    TRUE_VALUES = {"1", "true", "yes", "on"}  # Strings treated as boolean-true in env vars.
    OVERRIDE_ENV_VARS = ("MISTHELPER_FORCE_CONTAINER_LOOP", "MISTHELPER_CONTAINER")  # Manual override switches.
    CONTAINER_ENV_VARS = (  # Well-known vars set by container runtimes.
        "CONTAINER",
        "DOCKER_CONTAINER",
        "PODMAN_CONTAINER",
        "KUBERNETES_SERVICE_HOST",
        "CONTAINERD_NAMESPACE",
    )
    CGROUP_INDICATORS = ("docker", "containerd", "podman", "lxc")  # Substrings that mark a container cgroup.

    @staticmethod
    def _check_override_env_vars() -> bool | None:  # Honor an explicit operator override first.
        """Check for explicit container override environment variables."""
        for explicit_var in EnvironmentUtils.OVERRIDE_ENV_VARS:  # Inspect each override switch.
            value = os.environ.get(explicit_var, "").strip().lower()  # Normalize the configured value.
            if value in EnvironmentUtils.TRUE_VALUES:  # Operator forced container mode on.
                logging.debug("Container detection: override via %s=%s", explicit_var, value)  # Trace the override.
                return True  # Short-circuit: treat as a container.
        return None  # No override set; defer to other detectors.

    @staticmethod
    def _check_dockerenv_file() -> bool:  # Detect Docker's /.dockerenv sentinel file.
        """Check for /.dockerenv sentinel file."""
        if os.path.exists("/.dockerenv"):  # Docker drops this file inside containers.
            logging.debug("Container detection: /.dockerenv present")  # Trace the positive signal.
            return True  # Sentinel present means containerized.
        return False  # Absent sentinel is inconclusive here.

    @staticmethod
    def _check_container_env_vars() -> bool:  # Detect container runtimes via env vars.
        """Check for well-known container environment variables."""
        for env_var in EnvironmentUtils.CONTAINER_ENV_VARS:  # Probe each known runtime variable.
            if os.environ.get(env_var):  # Any non-empty value signals a container.
                logging.debug("Container detection: environment variable %s present", env_var)  # Trace which one.
                return True  # Treat as containerized.
        return False  # None present; inconclusive here.

    @staticmethod
    def _check_cgroup_markers() -> bool:
        """Check cgroup file for container indicators."""
        try:
            with open("/proc/1/cgroup", encoding="utf-8", errors="ignore") as cgroup_file:
                cgroup_content = cgroup_file.read().lower()
                for indicator in EnvironmentUtils.CGROUP_INDICATORS:  # Scan cgroup text for each runtime marker.
                    if indicator in cgroup_content:  # Marker substring present in cgroup.
                        logging.debug("Container detection: cgroup indicator '%s' found", indicator)  # marker found.
                        return True  # Containerized: a marker was found.
        except (FileNotFoundError, PermissionError):  # No cgroup file or no access (host/non-Linux).
            pass  # Treat missing cgroup as not-containerized.
        return False  # No cgroup markers: not a container.

    @staticmethod
    def _check_runtime_user() -> bool:  # Detect the container's dedicated service user.
        """Check if running as the 'misthelper' user."""
        try:
            import pwd  # noqa: PLC0415  # Unix only

            current_user_name = pwd.getpwuid(os.getuid()).pw_name  # type: ignore[attr-defined]
            if current_user_name == "misthelper":  # Image runs as the misthelper user.
                logging.debug("Container detection: running as user 'misthelper'")  # Trace the user-based signal.
                return True  # Running as misthelper means containerized.
        except Exception:  # nosec B110
            pass  # Ignore lookup failures on host systems.
        return False  # User signal absent: inconclusive.

    @staticmethod
    def _check_app_path_with_sshd() -> bool:  # Detect the /app + sshd image layout.
        """Check for canonical container path /app with sshd presence."""
        try:
            this_file_dir = os.path.abspath(os.path.dirname(__file__))  # Absolute directory of this module.
            if this_file_dir.startswith("/app") and os.path.exists("/app/MistHelper.py"):  # In the image path.
                if os.path.exists("/usr/sbin/sshd"):  # Image ships the SSH daemon.
                    logging.debug("Container detection: /app path with MistHelper.py and sshd present")  # image signal.
                    return True  # Layout matches the container image.
        except Exception:  # nosec B110
            pass  # Ignore path-probing errors on host.
        return False  # Layout not present: inconclusive.

    @staticmethod
    def _run_container_detectors() -> bool:
        """Run the ordered fallback container detectors; return True if any positive."""
        checks = [  # Ordered fallback detectors in reliability order
            EnvironmentUtils._check_dockerenv_file,
            EnvironmentUtils._check_container_env_vars,
            EnvironmentUtils._check_cgroup_markers,
            EnvironmentUtils._check_runtime_user,
            EnvironmentUtils._check_app_path_with_sshd,
        ]
        for check in checks:  # Run each detector in order
            if check():  # First positive detector wins
                return True
        return False  # No detector matched

    @staticmethod
    def is_running_in_container() -> bool:  # Public aggregate container check.
        """Multi-factor container detection: override env -> /.dockerenv -> env vars -> cgroup -> user -> /app."""
        try:
            override_result = EnvironmentUtils._check_override_env_vars()  # Operator override wins first
            if override_result is not None:  # Override explicitly set the answer
                return override_result  # Honor the forced value
            if EnvironmentUtils._run_container_detectors():  # Run the chained detectors
                return True  # A detector confirmed container
        except Exception as container_detection_error:  # Never let detection crash startup
            logging.debug("Container detection failed with exception: %s", container_detection_error)  # log failure
        logging.debug("Container detection: no container indicators found - running in direct mode")  # direct mode
        return False  # Default: not containerized
