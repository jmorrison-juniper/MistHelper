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

# ---------------------------------------------------------------------------
# Local .env loader (lightweight, no external dependency)
# SECURITY: Does NOT log values; only counts variables applied. Existing
# environment variables are NOT overridden unless explicitly requested.
# ---------------------------------------------------------------------------
def load_local_env_file(env_file_path: Path, override: bool = False) -> int:
    """Parse a simple .env file and inject variables into os.environ.

    Rules:
        - Lines starting with '#' or blank lines are ignored.
        - First '=' splits key and value; remaining '=' retained in value.
        - Surrounding single or double quotes are stripped from value.
        - Existing environment variables are preserved unless override=True.
        - Whitespace around key and value is trimmed.
    Returns:
        Count of variables newly set (or overwritten if override=True).
    """
    applied_count = 0
    try:
        if not env_file_path.exists():
            return 0
        with env_file_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue  # Skip malformed line silently (safety: do not guess)
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Strip symmetrical quotes
                if (value.startswith("\"") and value.endswith("\"")) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                if not override and key in os.environ:
                    continue
                # SECURITY: Do NOT log secret values
                os.environ[key] = value
                applied_count += 1
    except Exception as exc:  # Broad catch to avoid breaking caller for env parsing issues
        print(f"[WARNING] Failed to parse .env file '{env_file_path}': {exc}")
    return applied_count

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

    network_name = os.environ.get("MISTHELPER_NETWORK_NAME", "misthelper-net")
    network_subnet = os.environ.get("MISTHELPER_NETWORK_SUBNET", "10.89.0.0/24")
    network_driver = os.environ.get("MISTHELPER_NETWORK_DRIVER", "bridge")

    # Check if network exists (both engines support a similar list command)
    list_cmd = [engine_exe, "network", "ls"]
    # Podman provides --format; Docker uses --format with Go templates too. We will parse plain output.
    result = subprocess.run(list_cmd, capture_output=True, text=True)
    existing = result.stdout if result.returncode == 0 else ""
    if network_name not in existing:
        print(f"[NETWORK] Creating network: {network_name}")
        # Subnet creation works for both; if it fails we fall back.
        create_cmd = [engine_exe, "network", "create", "--driver", network_driver, "--subnet", network_subnet, network_name]
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
    ssh_container_name = os.environ.get("MISTHELPER_SSH_CONTAINER_NAME", "misthelper-ssh")
    main_container_name = os.environ.get("MISTHELPER_MAIN_CONTAINER_NAME", "misthelper-main")
    for container_name in [main_container_name, ssh_container_name]:
        inspect_cmd = [CONTAINER_ENGINE_EXECUTABLE, "inspect", container_name, "--format", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"]
        result = subprocess.run(inspect_cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print(f"{container_name}: {result.stdout.strip()}")
        else:
            print(f"{container_name}: Not running or no IP assigned")

    network_name = os.environ.get("MISTHELPER_NETWORK_NAME", "misthelper-net")
    print("\n[NETWORK INFO] MistHelper Network Definition:")
    print("=" * 60)
    network_cmd = [CONTAINER_ENGINE_EXECUTABLE, "network", "inspect", network_name]
    subprocess.run(network_cmd)

def cleanup_all():
    """Clean up all MistHelper containers and networks."""
    global CONTAINER_ENGINE_EXECUTABLE
    print("[CLEANUP] Removing all MistHelper containers and networks...")

    ssh_container_name = os.environ.get("MISTHELPER_SSH_CONTAINER_NAME", "misthelper-ssh")
    main_container_name = os.environ.get("MISTHELPER_MAIN_CONTAINER_NAME", "misthelper-main")
    for container_name in [main_container_name, ssh_container_name]:
        print(f"[CLEANUP] Stopping and removing container: {container_name}")
        stop_cmd = [CONTAINER_ENGINE_EXECUTABLE, "stop", container_name]
        subprocess.run(stop_cmd, capture_output=True)
        rm_cmd = [CONTAINER_ENGINE_EXECUTABLE, "rm", "-f", container_name]
        subprocess.run(rm_cmd, capture_output=True)

    network_name = os.environ.get("MISTHELPER_NETWORK_NAME", "misthelper-net")
    print(f"[CLEANUP] Removing network: {network_name}")
    network_rm_cmd = [CONTAINER_ENGINE_EXECUTABLE, "network", "rm", network_name]
    subprocess.run(network_rm_cmd, capture_output=True)
    print("[CLEANUP] Cleanup completed!")

def run_misthelper(output_format="csv", menu=None, test=False, fast=False, debug=False, no_env=False, ssh_mode=False, bridge_mode=False):
    """Run MistHelper in a container (Podman or Docker)."""
    global CONTAINER_ENGINE_EXECUTABLE, CONTAINER_ENGINE_NAME

    # Preparation: ensure required paths exist
    data_dir_name = os.environ.get("MISTHELPER_DATA_DIR", "data")
    script_log_name = os.environ.get("MISTHELPER_SCRIPT_LOG", "script.log")
    env_file_name = os.environ.get("MISTHELPER_ENV_FILE", ".env")
    
    data_dir = Path(f"./{data_dir_name}")
    data_dir.mkdir(exist_ok=True)
    script_log_path = Path(f"./{script_log_name}")
    if not script_log_path.exists():
        script_log_path.touch()
        print(f"[INFO] Created {script_log_name} file: {script_log_path}")
    # Ensure .env exists (empty) so volume mount does not fail on Docker / Windows
    env_path = Path(f"./{env_file_name}")
    if not env_path.exists():
        env_path.write_text("")
        print(f"[INFO] Created placeholder {env_file_name} file (empty): {env_path}")

    # Build image
    print(f"[BUILD] Building image with {CONTAINER_ENGINE_NAME}...")
    image_name = os.environ.get("MISTHELPER_IMAGE_NAME", "misthelper")
    build_cmd = [CONTAINER_ENGINE_EXECUTABLE, "build", "-t", image_name, "."]
    build_result = subprocess.run(build_cmd)
    if build_result.returncode != 0:
        print(f"[ERROR] Failed to build image using {CONTAINER_ENGINE_NAME}")
        return False
    print(f"[SUCCESS] Image built successfully with {CONTAINER_ENGINE_NAME}.")

    # Load .env into current process environment (unless explicitly disabled)
    if not no_env:
        env_file_name = os.environ.get("MISTHELPER_ENV_FILE", ".env")
        applied = load_local_env_file(Path(f"./{env_file_name}"), override=False)
        print(f"[ENV] Loaded {env_file_name} file ({applied} variables applied, override=False)")
    else:
        print("[ENV] Skipping .env load due to --no-env flag")

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
    ssh_container_name = os.environ.get("MISTHELPER_SSH_CONTAINER_NAME", "misthelper-ssh")
    main_container_name = os.environ.get("MISTHELPER_MAIN_CONTAINER_NAME", "misthelper-main")
    container_name = ssh_container_name if ssh_mode else main_container_name
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
        ssh_port = os.environ.get("MISTHELPER_SSH_PORT", "2200")
        run_cmd.extend(["-p", f"{ssh_port}:{ssh_port}"])

    # Interactive mode required for:
    # 1. No menu specified (interactive menu selection)
    # 2. Menu 101 (TUI mode requires terminal control)
    # 3. Not in SSH daemon mode (daemon runs detached)
    if (not menu or menu == "101") and not ssh_mode:
        run_cmd.append("-it")

    # Volume option differences: Podman benefits from :Z, Docker may not support.
    selinux_label = ":Z" if CONTAINER_ENGINE_NAME == "podman" and platform.system().lower() == "linux" else ""

    cwd = os.getcwd()
    # Build volume specs carefully to avoid Windows path + option ambiguity
    data_dir = os.environ.get("MISTHELPER_DATA_DIR", "data")
    env_file = os.environ.get("MISTHELPER_ENV_FILE", ".env")
    script_log = os.environ.get("MISTHELPER_SCRIPT_LOG", "script.log")
    container_data_path = os.environ.get("MISTHELPER_CONTAINER_DATA_PATH", "/app/data")
    container_env_path = os.environ.get("MISTHELPER_CONTAINER_ENV_PATH", "/app/.env")
    container_log_path = os.environ.get("MISTHELPER_CONTAINER_LOG_PATH", "/app/script.log")
    
    volumes = [
        f"{cwd}/{data_dir}:{container_data_path}{selinux_label}",
        f"{cwd}/{env_file}:{container_env_path}{selinux_label}",
        f"{cwd}/{script_log}:{container_log_path}{selinux_label}",
    ]
    for v in volumes:
        run_cmd.extend(["-v", v])

    # Common environment variables (read from .env with fallback defaults)
    env_vars = {
        "OUTPUT_FORMAT": output_format,
        "PYTHONHTTPSVERIFY": os.environ.get("PYTHONHTTPSVERIFY", "0"),
        "SSL_VERIFY": os.environ.get("SSL_VERIFY", "false"),
        "REQUESTS_CA_BUNDLE": os.environ.get("REQUESTS_CA_BUNDLE", ""),
        "CURL_CA_BUNDLE": os.environ.get("CURL_CA_BUNDLE", ""),
        "DISABLE_UV_CHECK": os.environ.get("DISABLE_UV_CHECK", "true"),
        "DISABLE_AUTO_INSTALL": os.environ.get("DISABLE_AUTO_INSTALL", "true"),
        "AUTO_UPGRADE_UV": os.environ.get("AUTO_UPGRADE_UV", "false"),
        "AUTO_UPGRADE_DEPENDENCIES": os.environ.get("AUTO_UPGRADE_DEPENDENCIES", "false"),
        "PYTHONPATH": os.environ.get("PYTHONPATH", "/app"),
    }
    # Defer injecting env (-e flags) until after optional SSH credential enrichment.

    # For SSH mode we need -d (detached) BEFORE image reference
    ssh_username_masked_for_later = None  # Stored for final connection instructions
    if ssh_mode:
        run_cmd.append("-d")


    # ------------------------------------------------------------------
    # SSH credential handling (read from environment / .env)
    # SECURITY: We NEVER print actual credential values. Mask length only.
    # Variable precedence (first non-empty wins):
    #   Username: MISTHELPER_SSH_USERNAME, SSH_USERNAME, fallback: 'misthelper'
    #   Password: MISTHELPER_SSH_PASSWORD, SSH_PASSWORD, fallback: 'misthelper123!'
    # These are only injected when ssh_mode=True.
    # ------------------------------------------------------------------
    if ssh_mode:
        # SECURITY: SSH mode now REQUIRES explicit credentials. No defaults.
        # Required variables (first form preferred):
        #   MISTHELPER_SSH_USERNAME  (or SSH_USERNAME)
        #   MISTHELPER_SSH_PASSWORD  (or SSH_PASSWORD)
        # If either is missing or blank, we abort with clear instructions.
        raw_user = os.environ.get("MISTHELPER_SSH_USERNAME") or os.environ.get("SSH_USERNAME") or ""
        raw_pass = os.environ.get("MISTHELPER_SSH_PASSWORD") or os.environ.get("SSH_PASSWORD") or ""

        if not raw_user.strip() or not raw_pass.strip():
            print("[ERROR] Missing required SSH credentials for --ssh mode.")
            print("[INFO] Set BOTH of the following in your .env (or environment):")
            print("       MISTHELPER_SSH_USERNAME=youruser")
            print("       MISTHELPER_SSH_PASSWORD=yourStrongPassword")
            print("[REFERENCE] See agents.md section 'EnhancedSSHRunner Design Notes' for security guidance.")
            print("[ABORT] Stopping before container launch to avoid insecure defaults.")
            return False

        ssh_username = raw_user.strip()
        ssh_password = raw_pass.strip()

        # Inject into container environment (not logged in cleartext)
        env_vars["MISTHELPER_SSH_USERNAME"] = ssh_username
        env_vars["MISTHELPER_SSH_PASSWORD"] = ssh_password

        masked_user = ssh_username[:1] + "*" * (len(ssh_username) - 1)
        print(f"[CONFIG] SSH username (masked): {masked_user}")
        print(f"[CONFIG] SSH password (masked length): {len(ssh_password)} characters")
        ssh_username_masked_for_later = ssh_username  # Username itself is not secret; display later

    # Now that env_vars dict is finalized, inject them as -e flags.
    for k, v in env_vars.items():
        run_cmd.extend(["-e", f"{k}={v}"])
    # Add image name
    image_name = os.environ.get("MISTHELPER_IMAGE_NAME", "misthelper")
    run_cmd.append(image_name)

    if ssh_mode:
        # Command inside container to start SSH service + session handling
        start_script = os.environ.get("MISTHELPER_SSH_START_SCRIPT", "/start.sh")
        run_cmd.append(start_script)
    else:
        main_script = os.environ.get("MISTHELPER_MAIN_SCRIPT", "MistHelper.py")
        run_cmd.extend(["python", main_script, "--output-format", output_format])
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
        ssh_port = os.environ.get("MISTHELPER_SSH_PORT", "2200")
        print(f"[NETWORK] Host mode active. Use host's LAN IP with port {ssh_port} for SSH.")
    elif network_name:
        print(f"[NETWORK] Custom network: {network_name}")
    else:
        print("[NETWORK] Default engine network in use.")

    # Launch
    result = subprocess.run(run_cmd)

    if ssh_mode:
        if result.returncode == 0:
            print("[SUCCESS] SSH container started.")
            ssh_port = os.environ.get("MISTHELPER_SSH_PORT", "2200")
            if network_name == "host":
                connect_user = ssh_username_masked_for_later or "<user>"
                print(f"[INFO] Connect: ssh -p {ssh_port} {connect_user}@<host-lan-ip>")
            else:
                connect_user = ssh_username_masked_for_later or "<user>"
                print(f"[INFO] Connect: ssh -p {ssh_port} {connect_user}@localhost")
            print("[INFO] Password is the value you supplied in MISTHELPER_SSH_PASSWORD (not displayed).")
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
    env_engine = os.environ.get("MISTHELPER_CONTAINER_ENGINE", "auto").strip().lower()
    engine_pref = env_engine if env_engine != "auto" else args.engine
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
