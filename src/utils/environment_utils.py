"""EnvironmentUtils -- runtime/container environment detection.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 33).
Self-contained module: no live-global reads, so no lazy MistHelper import
is required. Direct imports cover stdlib only (os, logging). Callers
continue to reach the class through the ``MistHelper.EnvironmentUtils``
re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: dynamically load Unix-only pwd without static Windows-stub access.
import logging  # WHY: structured trace for container detection lifecycle events.
import os  # WHY: environment variable + filesystem probes for container detection.


class EnvironmentUtils:
    """Centralized environment detection utilities.

    Handles container detection, runtime environment identification, and so on
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
        return None  # No override set. Defer to other detectors.

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
        return False  # None present. Inconclusive here.

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
        if os.name != "posix":  # WHY: the image-specific account check only applies to Unix containers.
            logging.debug(
                "Container detection: runtime-user check unavailable on this platform"
            )  # WHY: trace the safe fallback.
            return False  # WHY: Windows cannot provide the Unix account identity used by this heuristic.
        try:
            pwd_module = importlib.import_module(
                "pwd"
            )  # WHY: defer Unix-only module resolution until after platform validation.
        except ModuleNotFoundError:  # WHY: minimal or unusual Unix runtimes can omit the account database module.
            logging.debug(
                "Container detection: pwd module unavailable"
            )  # WHY: record why this optional detector was skipped.
            return False  # WHY: without pwd, this detector cannot confirm the image user.
        getuid = getattr(os, "getuid", None)  # WHY: protect Windows type stubs from a Unix-only attribute access.
        getpwuid = getattr(pwd_module, "getpwuid", None)  # WHY: avoid static access to a Windows-incomplete pwd stub.
        if not callable(getuid) or not callable(getpwuid):  # WHY: nonstandard runtimes can omit either required lookup.
            logging.debug(
                "Container detection: UID account lookup unavailable"
            )  # WHY: trace why the optional detector was skipped.
            return False  # WHY: without both lookups, account resolution is not possible.
        try:
            current_user_name = getpwuid(
                getuid()
            ).pw_name  # WHY: resolve the effective Unix account used by this process.
        except KeyError:  # WHY: account databases can omit an otherwise valid numeric UID.
            logging.debug(
                "Container detection: no account found for current UID"
            )  # WHY: record the benign lookup miss.
            return False  # WHY: no matching account means this detector cannot confirm the image user.
        if current_user_name == "misthelper":  # Image runs as the misthelper user.
            logging.debug("Container detection: running as user 'misthelper'")  # Trace the user-based signal.
            return True  # Running as misthelper means containerized.
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
        """Run the ordered fallback container detectors. Return True if any positive."""
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
