#!/usr/bin/env python3
"""
Cross-platform MistHelper container wrapper.

Goals:
    - Support BOTH Podman and Docker engines automatically.
    - Work on Windows and Linux (and macOS for Docker) without edits.
    - Provide optional host ("bridge") networking ONLY where truly supported.
    - Preserve prior behavior for legacy Podman-only usage.

Security / Safety Notes:
    - This script never prints environment variable secrets.
    - Host networking is potentially less isolated; we clearly warn when enabling.
    - We avoid SELinux relabel flags for Docker which does not support ":Z" uniformly.
"""

import sys
import subprocess
import os
import shutil
import platform
from pathlib import Path

# Engine detection results will be stored here after initialization
CONTAINER_ENGINE_EXECUTABLE = None
CONTAINER_ENGINE_NAME = None  # "podman" or "docker"

def detect_container_engine(preference: str = "auto"):
    """Detect an available container engine.

    Order of detection when preference == auto:
        1. Podman (preferred for rootless + SELinux compatibility)
        2. Docker

    When preference is explicit (podman/docker) we only test that engine.
    Returns (engine_name, executable_path) or exits with clear message.
    """
    candidates = []
    if preference == "auto":
        candidates = ["podman", "docker"]
    elif preference in ("podman", "docker"):
        candidates = [preference]
    else:
        print(f"[ERROR] Invalid engine preference: {preference}")
        sys.exit(2)

    for name in candidates:
        exe = shutil.which(name)
        if exe:
            print(f"[ENGINE] Using {name} at: {exe}")
            return name, exe

    print("[ERROR] No supported container engine found (looked for podman, docker).")
    print("[ACTION] Install Podman or Docker and ensure it is on PATH.")
    sys.exit(1)

def host_network_supported(engine_name: str) -> bool:
    """Return True if host networking can provide meaningful LAN exposure.

    Notes:
        - Docker Desktop on macOS/Windows: --network host is limited (VM internal network).
        - Podman on Windows: host networking often unsupported / mapped to user-mode network.
        - We only claim support on native Linux for reliability.
    """
    system_name = platform.system().lower()
    if system_name == "linux":
        return True  # Native Linux: both podman and docker host mode meaningful
    return False

def setup_networking(bridge_mode: bool = False, engine_name: str = "podman", engine_exe: str = "podman"):
    """Set up container networking.

    bridge_mode:
        If True and supported, we use host networking. If unsupported, we warn and fall back.
    engine_name:
        "podman" or "docker".
    Returns:
        "host" | network_name | None (default engine network)
    """
    if bridge_mode:
        if host_network_supported(engine_name):
            print("[NETWORK] Host networking requested and supported. Container shares host stack.")
            print("[WARNING] Reduced isolation. Ensure you trust the container contents.")
            return "host"
        else:
            print("[WARNING] Host networking requested but not supported on this platform.")
            print("[INFO] Falling back to standard bridged network with port publishing.")
            # Continue with normal network creation (below) without host mode.

    network_name = "misthelper-net"

    # Check if network exists (both engines support a similar list command)
    list_cmd = [engine_exe, "network", "ls"]
    # Podman provides --format; Docker uses --format with Go templates too. We will parse plain output.
    result = subprocess.run(list_cmd, capture_output=True, text=True)
    existing = result.stdout if result.returncode == 0 else ""
    if network_name not in existing:
        print(f"[NETWORK] Creating network: {network_name}")
        # Subnet creation works for both; if it fails we fall back.
        create_cmd = [engine_exe, "network", "create", "--driver", "bridge", "--subnet", "10.89.0.0/24", network_name]
        create_result = subprocess.run(create_cmd, capture_output=True, text=True)
        if create_result.returncode != 0:
            print("[WARNING] Failed to create custom network; using default engine network.")
            return None
        else:
            print(f"[NETWORK] Created network {network_name}")
    else:
        print(f"[NETWORK] Using existing network: {network_name}")

    return network_name

def cleanup_container(container_name: str):
    """Remove existing container with the same name if it exists."""
    global CONTAINER_ENGINE_EXECUTABLE
    print(f"[CLEANUP] Removing any existing container: {container_name}")
    cleanup_cmd = [CONTAINER_ENGINE_EXECUTABLE, "rm", "-f", container_name]
    subprocess.run(cleanup_cmd, capture_output=True)  # Suppress output, ignore errors

def show_network_info():
    """Show network information for MistHelper containers (engine agnostic)."""
    global CONTAINER_ENGINE_EXECUTABLE
    print("[NETWORK INFO] MistHelper Container Status:")
    print("=" * 60)

    # Show running containers filtered by name substring
    ps_cmd = [CONTAINER_ENGINE_EXECUTABLE, "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"]
    subprocess.run(ps_cmd)

    print("\n[NETWORK INFO] Container IP Addresses (may be blank in host mode):")
    print("=" * 60)
    for container_name in ["misthelper-main", "misthelper-ssh"]:
        inspect_cmd = [CONTAINER_ENGINE_EXECUTABLE, "inspect", container_name, "--format", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"]
        result = subprocess.run(inspect_cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print(f"{container_name}: {result.stdout.strip()}")
        else:
            print(f"{container_name}: Not running or no IP assigned")

    print("\n[NETWORK INFO] MistHelper Network Definition:")
    print("=" * 60)
    network_cmd = [CONTAINER_ENGINE_EXECUTABLE, "network", "inspect", "misthelper-net"]
    subprocess.run(network_cmd)

def cleanup_all():
    """Clean up all MistHelper containers and networks."""
    global CONTAINER_ENGINE_EXECUTABLE
    print("[CLEANUP] Removing all MistHelper containers and networks...")

    for container_name in ["misthelper-main", "misthelper-ssh"]:
        print(f"[CLEANUP] Stopping and removing container: {container_name}")
        stop_cmd = [CONTAINER_ENGINE_EXECUTABLE, "stop", container_name]
        subprocess.run(stop_cmd, capture_output=True)
        rm_cmd = [CONTAINER_ENGINE_EXECUTABLE, "rm", "-f", container_name]
        subprocess.run(rm_cmd, capture_output=True)

    print("[CLEANUP] Removing network: misthelper-net")
    network_rm_cmd = [CONTAINER_ENGINE_EXECUTABLE, "network", "rm", "misthelper-net"]
    subprocess.run(network_rm_cmd, capture_output=True)
    print("[CLEANUP] Cleanup completed!")

def run_misthelper(output_format="csv", menu=None, test=False, fast=False, debug=False, no_env=False, ssh_mode=False, bridge_mode=False):
    """Run MistHelper in a container (Podman or Docker)."""
    global CONTAINER_ENGINE_EXECUTABLE, CONTAINER_ENGINE_NAME

    # Preparation: ensure required paths exist
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    script_log_path = Path("./script.log")
    if not script_log_path.exists():
        script_log_path.touch()
        print(f"[INFO] Created script.log file: {script_log_path}")
    # Ensure .env exists (empty) so volume mount does not fail on Docker / Windows
    env_path = Path("./.env")
    if not env_path.exists():
        env_path.write_text("")
        print(f"[INFO] Created placeholder .env file (empty): {env_path}")

    # Build image
    print(f"[BUILD] Building image with {CONTAINER_ENGINE_NAME}...")
    build_cmd = [CONTAINER_ENGINE_EXECUTABLE, "build", "-t", "misthelper", "."]
    build_result = subprocess.run(build_cmd)
    if build_result.returncode != 0:
        print(f"[ERROR] Failed to build image using {CONTAINER_ENGINE_NAME}")
        return False
    print(f"[SUCCESS] Image built successfully with {CONTAINER_ENGINE_NAME}.")

    # Configuration summary
    print("[RUN] Launching MistHelper container...")
    print(f"[CONFIG] Output format: {output_format}")
    print(f"[CONFIG] Menu option: {menu if menu else 'Interactive mode'}")
    print(f"[CONFIG] Test mode: {'enabled' if test else 'disabled'}")
    print(f"[CONFIG] Fast mode: {'enabled' if fast else 'disabled'}")
    print(f"[CONFIG] Debug mode: {'enabled' if debug else 'disabled'}")
    print(f"[CONFIG] No-env mode: {'enabled' if no_env else 'disabled'}")
    print(f"[CONFIG] SSH mode: {'enabled' if ssh_mode else 'disabled'}")
    print(f"[CONFIG] Host networking requested: {'yes' if bridge_mode else 'no'}")

    run_cmd = [CONTAINER_ENGINE_EXECUTABLE, "run"]
    container_name = "misthelper-ssh" if ssh_mode else "misthelper-main"
    cleanup_container(container_name)
    network_name = setup_networking(bridge_mode, CONTAINER_ENGINE_NAME, CONTAINER_ENGINE_EXECUTABLE)

    run_cmd.extend(["--name", container_name])
    if not ssh_mode:
        run_cmd.append("--rm")

    # Networking options
    if network_name == "host":
        run_cmd.extend(["--network", "host"])
    elif network_name:
        run_cmd.extend(["--network", network_name])
    else:
        # Default network (engine managed)
        pass

    # Port publishing: if SSH mode and NOT host network
    if ssh_mode and network_name != "host":
        run_cmd.extend(["-p", "2200:2200"])

    # Interactive only when no menu and not in SSH daemon mode
    if not menu and not ssh_mode:
        run_cmd.append("-it")

    # Volume option differences: Podman benefits from :Z, Docker may not support.
    selinux_label = ":Z" if CONTAINER_ENGINE_NAME == "podman" and platform.system().lower() == "linux" else ""

    cwd = os.getcwd()
    # Build volume specs carefully to avoid Windows path + option ambiguity
    volumes = [
        f"{cwd}/data:/app/data{selinux_label}",
        f"{cwd}/.env:/app/.env{selinux_label}",
        f"{cwd}/script.log:/app/script.log{selinux_label}",
    ]
    for v in volumes:
        run_cmd.extend(["-v", v])

    # Common environment variables
    env_vars = {
        "OUTPUT_FORMAT": output_format,
        "PYTHONHTTPSVERIFY": "0",
        "SSL_VERIFY": "false",
        "REQUESTS_CA_BUNDLE": "",
        "CURL_CA_BUNDLE": "",
        "DISABLE_UV_CHECK": "true",
        "DISABLE_AUTO_INSTALL": "true",
        "AUTO_UPGRADE_UV": "false",
        "AUTO_UPGRADE_DEPENDENCIES": "false",
        "PYTHONPATH": "/app",
    }
    for k, v in env_vars.items():
        run_cmd.extend(["-e", f"{k}={v}"])

    # For SSH mode we need -d (detached) BEFORE image reference
    if ssh_mode:
        run_cmd.append("-d")

    # Add image name
    run_cmd.append("misthelper")

    if ssh_mode:
        # Command inside container to start SSH service + session handling
        run_cmd.append("/start.sh")
    else:
        run_cmd.extend(["python", "MistHelper.py", "--output-format", output_format])
        if menu:
            run_cmd.extend(["--menu", menu])
        if test:
            run_cmd.append("--test")
        if fast:
            run_cmd.append("--fast")
        if debug:
            run_cmd.append("--debug")
        if no_env:
            run_cmd.append("--no-env")

    # Network summary
    print(f"[NETWORK] Container name: {container_name}")
    if network_name == "host":
        print("[NETWORK] Host mode active. Use host's LAN IP with port 2200 for SSH.")
    elif network_name:
        print(f"[NETWORK] Custom network: {network_name}")
    else:
        print("[NETWORK] Default engine network in use.")

    # Launch
    result = subprocess.run(run_cmd)

    if ssh_mode:
        if result.returncode == 0:
            print("[SUCCESS] SSH container started.")
            if network_name == "host":
                print("[INFO] Connect: ssh -p 2200 misthelper@<host-lan-ip>")
            else:
                print("[INFO] Connect: ssh -p 2200 misthelper@localhost")
            print("[INFO] Password: misthelper123!")
        else:
            print("[ERROR] Failed to start SSH container.")
    else:
        if result.returncode == 0:
            print("[SUCCESS] MistHelper run completed.")
        else:
            print("[ERROR] MistHelper encountered an error during execution.")

    return result.returncode == 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cross-platform MistHelper container runner (Podman or Docker)")
    parser.add_argument("--output-format", default="csv", choices=["csv", "sqlite"], help="Output format (default: csv)")
    parser.add_argument("--menu", default=None, help="Menu option to execute (default: interactive mode)")
    parser.add_argument("--test", action="store_true", default=False, help="Enable test mode (default: disabled)")
    parser.add_argument("--fast", action="store_true", default=False, help="Enable fast mode (default: disabled)")
    parser.add_argument("--debug", action="store_true", default=False, help="Enable debug output (default: disabled)")
    parser.add_argument("--no-env", action="store_true", default=False, help="Disable .env file loading for SSH operations (default: disabled)")
    parser.add_argument("--ssh", action="store_true", default=False, dest="ssh_mode", help="Run container with SSH server on port 2200 (default: disabled)")
    parser.add_argument("--bridge", action="store_true", default=False, dest="bridge_mode", help="Attempt host network (only effective on native Linux)")
    parser.add_argument("--network-info", action="store_true", default=False, help="Show network information for running MistHelper containers")
    parser.add_argument("--cleanup", action="store_true", default=False, help="Clean up all MistHelper containers and networks")
    parser.add_argument("--engine", default="auto", choices=["auto", "podman", "docker"], help="Container engine preference (default: auto)")

    args = parser.parse_args()

    # Detect engine early
    # Environment variable override takes precedence if provided
    env_engine = os.environ.get("MISTHELPER_CONTAINER_ENGINE", "").strip().lower()
    engine_pref = env_engine or args.engine
    name, exe = detect_container_engine(engine_pref)
    CONTAINER_ENGINE_NAME = name
    CONTAINER_ENGINE_EXECUTABLE = exe

    # Utility commands (do not run main logic if invoked)
    if args.network_info:
        show_network_info()
        sys.exit(0)
    if args.cleanup:
        cleanup_all()
        sys.exit(0)

    success = run_misthelper(
        args.output_format,
        args.menu,
        args.test,
        args.fast,
        args.debug,
        args.no_env,
        args.ssh_mode,
        args.bridge_mode,
    )
    sys.exit(0 if success else 1)
