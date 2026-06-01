"""Package installation helpers for early dependency bootstrap."""

from __future__ import annotations

import sysconfig
from dataclasses import dataclass
from typing import Any


@dataclass
class PackageInstaller:
    """Install and upgrade packages using UV with pip fallback."""

    os_module: Any
    subprocess_module: Any
    sys_module: Any
    logging_module: Any

    def find_uv_executable(self) -> tuple[list[str] | None, str | None]:
        """Find an executable UV command and return command + version."""
        uv_commands: list[list[str]] = [["uv"]]
        scripts_dir = sysconfig.get_path("scripts")
        if scripts_dir:
            uv_in_scripts = self.os_module.path.join(scripts_dir, "uv")
            if self.os_module.name == "nt":
                uv_in_scripts += ".exe"
            uv_commands.append([uv_in_scripts])
        python_bin_dir = self.os_module.path.dirname(self.sys_module.executable)
        uv_beside_python = self.os_module.path.join(python_bin_dir, "uv")
        if self.os_module.name == "nt":
            uv_beside_python += ".exe"
        uv_commands.append([uv_beside_python])
        uv_commands.append([self.sys_module.executable, "-m", "uv"])
        for cmd in uv_commands:
            try:
                if len(cmd) == 1 and self.os_module.path.sep in cmd[0]:
                    if not self.os_module.path.isfile(cmd[0]):
                        continue
                result = self.subprocess_module.run(
                    cmd + ["--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return cmd, result.stdout.strip()
            except (FileNotFoundError, self.subprocess_module.SubprocessError, OSError):
                continue
        return None, None

    def install_uv_with_pip(self) -> bool:
        """Install UV using pip in the active Python environment."""
        try:
            result = self.subprocess_module.run(
                [self.sys_module.executable, "-m", "pip", "install", "uv"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0
        except Exception as error:
            self.logging_module.warning("Could not install UV: %s", error)
            return False

    def install_with_uv(self, uv_cmd: list[str], package_spec: str, upgrade: bool = False) -> bool:
        """Install or upgrade a package with UV."""
        command = uv_cmd + ["pip", "install"]
        if upgrade:
            command.append("--upgrade")
        command.extend(["--python", self.sys_module.executable, package_spec])
        try:
            result = self.subprocess_module.run(command, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
        except Exception as error:
            self.logging_module.warning("UV package action failed for %s: %s", package_spec, error)
            return False

    def install_with_pip(self, package_spec: str, upgrade: bool = False) -> bool:
        """Install or upgrade a package with pip."""
        command = [self.sys_module.executable, "-m", "pip", "install"]
        if upgrade:
            command.append("--upgrade")
        command.append(package_spec)
        try:
            result = self.subprocess_module.run(command, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
        except Exception as error:
            self.logging_module.error("Pip package action failed for %s: %s", package_spec, error)
            return False
