"""Management/action helper cluster for :mod:`src.device.utility_commands`.

Owns the 10 device-management commands (locate, unlocate, bounce port,
reprovision, readopt, ZTP password, config CLI commands, support-file
upload, poll switch stats, create snapshot). These are user-triggered
operations that mutate device state or produce operator-visible output
but are not classified as clear/reset operations (see
:mod:`src.device._utility_commands_clear` for those).

Uses the same wrapper + ``__getattr__`` proxy pattern as the earlier
Phase-1/2/3 splits: the parent binds an instance as ``self._action`` and
its ``__getattr__`` proxies unknown lookups here so shared state
(dependency callables, mistapi module) stays transparent. Peer-method
calls inside this cluster route through ``self._method(...)`` and the
cluster's ``__getattr__`` delegates to the parent, which in turn resolves
via its own ``__getattr__`` to sibling clusters when needed.
"""

# pylint: disable=logging-fstring-interpolation

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: exception-level logging when API calls fail
from typing import Any  # WHY: Any narrows the SDK response type

import mistapi  # WHY: direct SDK access mirrors parent module's usage

from src.device._utility_commands_cluster import _ClusterBase  # WHY: shared proxy base

# WHY: menu-selected support-file categories exposed to the operator.
_SUPPORT_FILE_TYPES: tuple[str, ...] = (
    "full",  # WHY: full support bundle (default)
    "process",  # WHY: per-process diagnostics
    "outbound-ssh",  # WHY: outbound-ssh session logs
    "messages",  # WHY: /var/log/messages
    "core-dumps",  # WHY: kernel/process core files
    "var-logs",  # WHY: full /var/log tree
    "jma-logs",  # WHY: Juniper Mist Agent logs
)


class _UtilityCommandsAction(_ClusterBase):  # WHY: cluster wrapper mirroring earlier phase clusters
    """Wrapper class holding the 10 device-management commands."""

    # ------------------------------------------------------------------
    # locate / unlocate
    # ------------------------------------------------------------------

    def locate_device(self) -> None:  # WHY: menu 138 entry point for LED blink
        """Menu 138: Locate device by blinking LED."""
        logging.info("Menu #138: Locate Device")  # WHY: audit menu entry
        selection = self._select_site_and_device("locate")  # WHY: pick site + AP/switch
        if not selection:  # WHY: cancelled -> abort
            return  # WHY: no work when operator cancels
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        duration = self._prompt_locate_duration()  # WHY: get validated minute count
        self._invoke_locate(site_id, device_id, duration)  # WHY: call SDK + report

    def _prompt_locate_duration(self) -> int:  # WHY: encapsulate clamp + default logic
        """Prompt for LED-blink minutes, clamped to 1-120 with a default of 5."""
        raw = self._safe_input_fn(
            "LED blink duration in minutes (1-120, default 5): ",
            default_value="5",
            context="locate_duration",
        )  # WHY: EOF-safe prompt with default
        try:  # WHY: guard against non-numeric raw input
            return max(1, min(120, int(raw)))  # WHY: clamp into valid API range
        except ValueError:  # WHY: bad input -> default rather than crash
            return 5  # WHY: non-numeric input falls back to default

    def _invoke_locate(self, site_id: str, device_id: str, duration: int) -> None:  # WHY: isolate SDK call
        """Call the locate SDK and report success/failure to the operator."""
        try:
            response = mistapi.api.v1.sites.devices.startSiteLocateDevice(
                self._apisession, site_id, device_id, {"duration": duration},
            )  # WHY: kick off LED blink for `duration` minutes
            if self._print_api_result(
                response,
                f"Device LED blinking for {duration} minutes.",
                "Locate device failed",
            ):  # WHY: emit success/error line based on HTTP status
                print("-> Use 'Unlocate Device' (menu 139) to stop.")  # WHY: teach follow-up action
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Locate device failed: %s", error)  # WHY: audit failure with stack
            print(f"! Locate failed: {error}")  # WHY: surface error to operator

    def unlocate_device(self) -> None:  # WHY: menu 139 counterpart to locate_device
        """Menu 139: Stop device LED blinking."""
        logging.info("Menu #139: Unlocate Device")  # WHY: audit menu entry
        selection = self._select_site_and_device("unlocate")  # WHY: pick site + AP/switch
        if not selection:  # WHY: cancelled -> abort
            return  # WHY: no work when operator cancels
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        try:
            response = mistapi.api.v1.sites.devices.stopSiteLocateDevice(
                self._apisession, site_id, device_id,
            )  # WHY: instruct device to stop blinking LED
            self._print_api_result(
                response,
                "Device LED blinking stopped.",
                "Unlocate failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Unlocate device failed: %s", error)  # WHY: audit failure with stack
            print(f"! Unlocate failed: {error}")  # WHY: surface error to operator

    # ------------------------------------------------------------------
    # bounce_port
    # ------------------------------------------------------------------

    def bounce_port(self) -> None:  # WHY: menu 140 entry for port bounce flow
        """Menu 140: Bounce switch/gateway port (y/N confirmation)."""
        logging.info("Menu #140: Bounce Port")  # WHY: audit menu entry
        selection = self._select_site_and_device("bounce_port")  # WHY: pick site + device
        if not selection:  # WHY: cancelled -> abort
            return  # WHY: no work when operator cancels
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        port_id = self._resolve_bounceable_port(site_id, device_id)  # WHY: pick + validate port
        if not port_id:  # WHY: none picked or blocked prefix
            return  # WHY: bail without confirming when port invalid
        if not self._confirm_bounce(port_id):  # WHY: require y/N confirmation
            return  # WHY: operator declined confirmation
        self._invoke_port_bounce(site_id, device_id, port_id)  # WHY: run WebSocket bounce

    def _resolve_bounceable_port(self, site_id: str, device_id: str) -> str | None:  # WHY: reject unsafe port kinds
        """Prompt for a port and reject management/aggregate/IRB targets."""
        port_id = self._select_port_from_device(site_id, device_id)  # WHY: interactive port picker
        if not port_id:  # WHY: cancelled or empty -> abort
            return None
        if port_id.startswith(("vme", "ae", "irb")):  # WHY: block prefixes unsafe to bounce
            print(f"! Port '{port_id}' cannot be bounced (management/aggregate/IRB port).")  # WHY: signal reject
            return None
        return str(port_id)  # WHY: proxied picker returns Any; coerce to satisfy mypy strict

    def _confirm_bounce(self, port_id: str) -> bool:
        """Confirm the port-bounce with a y/N prompt."""
        confirm = self._safe_input_fn(
            f"Bounce port {port_id}? This will briefly disrupt traffic. (y/N): ",
            context="bounce_port",
        )  # WHY: destructive-op confirmation
        if confirm.lower() != "y":  # WHY: anything other than 'y' aborts
            print("! Operation cancelled.")  # WHY: acknowledge cancel
            return False
        return True

    def _invoke_port_bounce(self, site_id: str, device_id: str, port_id: str) -> None:
        """Kick off the WebSocket-backed port-bounce and report result."""
        print(f"\n-> Bouncing port {port_id}...")  # WHY: operator feedback
        result = self._run_websocket_command(
            site_id,
            device_id,
            mistapi.api.v1.sites.devices.bounceDevicePort,
            {"ports": [port_id]},
        )  # WHY: WebSocket request/response for the bounce
        if result:  # WHY: non-empty result -> success
            print("-> Port bounce complete.")  # WHY: signal success
        else:
            print("! Port bounce may have timed out. Check device status.")  # WHY: signal timeout/fail

    # ------------------------------------------------------------------
    # reprovision / readopt
    # ------------------------------------------------------------------

    def reprovision_device(self) -> None:
        """Menu 142: Reprovision switch/gateway (y/N confirmation)."""
        logging.info("Menu #142: Reprovision Device")  # WHY: audit menu entry
        selection = self._select_site_and_device("reprovision")  # WHY: pick site + device
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        confirm = self._safe_input_fn(
            "Reprovision this device? This will push fresh config. (y/N): ",
            context="reprovision",
        )  # WHY: destructive-op confirmation
        if confirm.lower() != "y":  # WHY: abort unless explicit y
            print("! Operation cancelled.")  # WHY: acknowledge cancel
            return
        self._invoke_reprovision(site_id, device_id)  # WHY: run API + report

    def _invoke_reprovision(self, site_id: str, device_id: str) -> None:
        """Call the reprovision SDK and report success/failure."""
        try:
            response = mistapi.api.v1.sites.devices.reprovisionSiteOctermDevice(
                self._apisession, site_id, device_id,
            )  # WHY: trigger fresh-config push
            self._print_api_result(
                response,
                "Device reprovisioning initiated.",
                "Reprovision failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Reprovision failed: %s", error)  # WHY: audit failure with stack
            print(f"! Reprovision failed: {error}")  # WHY: surface error to operator

    def readopt_device(self) -> None:
        """Menu 143: Re-adopt switch device.

        Preflight the device's Virtual Chassis (VC) membership before
        calling the readopt API to avoid a 400 response.
        """
        logging.info("Menu #143: Re-adopt Device")  # WHY: audit menu entry
        selection = self._select_site_and_device("readopt", "switch")  # WHY: switch-only op
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        if not self._readopt_vc_preflight(site_id, device_id):  # WHY: bail on non-VC device
            return
        self._invoke_readopt(site_id, device_id)  # WHY: run readopt + report

    def _readopt_vc_preflight(self, site_id: str, device_id: str) -> bool:
        """Return False (and print) when the device is not a VC member."""
        try:
            vc_resp = mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis(
                self._apisession, site_id, device_id,
            )  # WHY: query VC membership
            vc_data = getattr(vc_resp, "data", None) or {}  # WHY: guard missing .data
            if not vc_data.get("is_virtual_chassis", False):  # WHY: readopt requires VC
                print("! Device is not a Virtual Chassis member. 'readopt' applies only to VC devices. Skipping.")
                return False
        except Exception as error:  # WHY: warn-and-continue; readopt may still work
            logging.warning("VC preflight check failed: %s", error, exc_info=True)  # WHY: audit warning
        return True  # WHY: preflight passed or was inconclusive

    def _invoke_readopt(self, site_id: str, device_id: str) -> None:
        """Call the readopt SDK and report success/failure."""
        try:
            response = mistapi.api.v1.sites.devices.readoptSiteOctermDevice(
                self._apisession, site_id, device_id,
            )  # WHY: request re-adoption
            self._print_api_result(
                response,
                "Device re-adoption initiated.",
                "Re-adopt failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Re-adopt failed: %s", error)  # WHY: audit failure with stack
            print(f"! Re-adopt failed: {error}")  # WHY: surface error to operator

    # ------------------------------------------------------------------
    # ZTP password / config CLI commands
    # ------------------------------------------------------------------

    def get_ztp_password(self) -> None:
        """Menu 144: Get ZTP password for switch/gateway."""
        logging.info("Menu #144: Get ZTP Password")  # WHY: audit menu entry
        selection = self._select_site_and_device("ztp_password")  # WHY: pick site + device
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        try:
            response = mistapi.api.v1.sites.devices.getSiteDeviceZtpPassword(
                self._apisession, site_id, device_id,
            )  # WHY: fetch one-time ZTP credential
            self._render_ztp_response(response)  # WHY: display on console only
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            error_msg = f"{type(error).__name__}: {str(error)}"  # WHY: qualify error type
            logging.error("ZTP password request failed: %s", error_msg)  # WHY: audit failure
            print(f"! ZTP password request failed: {error_msg}")  # WHY: surface error

    @staticmethod
    def _render_ztp_response(response: Any) -> None:
        """Render the ZTP password to the console, never to logs."""
        if not hasattr(response, "data"):  # WHY: no payload -> nothing to show
            print("! No password data returned.")  # WHY: signal empty payload
            return
        data = response.data if isinstance(response.data, dict) else {}  # WHY: guard shape
        ztp_credential = data.get("password", str(response.data))  # WHY: prefer dict field
        # Intentional: user-requested display of ZTP credential to console
        # only. Not sent to logging framework.
        print(f"\n-> ZTP Password: {ztp_credential}")  # noqa: T201
        print("-> (Password displayed on console only - not logged or saved)")  # WHY: reassure operator

    def get_config_commands(self) -> None:
        """Menu 145: Get configuration CLI commands for switch."""
        logging.info("Menu #145: Get Config CLI Commands")  # WHY: audit menu entry
        selection = self._select_site_and_device("config_cmd", "switch")  # WHY: switch-only op
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        try:
            response = mistapi.api.v1.sites.devices.getSiteDeviceConfigCmd(
                self._apisession, site_id, device_id,
            )  # WHY: fetch generated CLI config bundle
            self._render_config_response(response)  # WHY: pretty-print each section
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Config commands request failed: %s", error)  # WHY: audit failure
            print(f"! Config commands request failed: {error}")  # WHY: surface error

    @staticmethod
    def _render_config_response(response: Any) -> None:
        """Render the CLI-config bundle grouped by section."""
        if not hasattr(response, "data"):  # WHY: no payload -> nothing to show
            print("! No configuration commands returned.")  # WHY: signal empty payload
            return
        print("\n" + "=" * 60)  # WHY: banner separates command output block
        print("CONFIGURATION CLI COMMANDS:")  # WHY: identify command in operator log
        print("=" * 60)  # WHY: close banner
        data = response.data  # WHY: capture payload
        if isinstance(data, dict):  # WHY: dict -> per-key sections
            for key, value in data.items():  # WHY: emit one block per key
                print(f"\n--- {key} ---")  # WHY: section header
                print(str(value))  # WHY: CLI text for that section
        else:
            print(str(data))  # WHY: fallback for non-dict payloads

    # ------------------------------------------------------------------
    # upload_support_file
    # ------------------------------------------------------------------

    def upload_support_file(self) -> None:
        """Menu 146: Upload support file from switch/gateway."""
        logging.info("Menu #146: Upload Support File")  # WHY: audit menu entry
        selection = self._select_site_and_device("support_upload")  # WHY: pick site + device
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        info = self._prompt_support_file_type()  # WHY: pick category
        body = self._build_support_body(info)  # WHY: assemble API body
        self._invoke_support_upload(site_id, device_id, body, info)  # WHY: run API + report

    def _prompt_support_file_type(self) -> str:
        """Present the menu of support-file categories and return the selection."""
        print("\nSupport file types:")  # WHY: banner
        for idx, file_type in enumerate(_SUPPORT_FILE_TYPES, 1):  # WHY: enumerate 1-based for humans
            print(f"  {idx}. {file_type}")  # WHY: numbered option list
        raw = self._safe_input_fn(
            "Select type (1-7, default: 1 = full): ",
            default_value="1",
            context="support_type",
        )  # WHY: EOF-safe prompt with default
        return _resolve_support_file_type(raw)  # WHY: pure helper keeps this method C<=5

    def _build_support_body(self, info: str) -> dict[str, Any]:
        """Build the support-upload request body from the operator prompts."""
        body: dict[str, Any] = {"info": info}  # WHY: category is required
        node = self._safe_input_fn(
            "Node (node0/node1, Enter for both): ",
            context="support_node",
        )  # WHY: optional node override
        if node:  # WHY: skip when the operator wants both
            body["node"] = node  # WHY: constrain to a single VC node
        return body

    def _invoke_support_upload(
        self,
        site_id: str,
        device_id: str,
        body: dict[str, Any],
        info: str,
    ) -> None:
        """Call the support-upload SDK and report success/failure."""
        try:
            response = mistapi.api.v1.sites.devices.uploadSiteDeviceSupportFile(
                self._apisession, site_id, device_id, body,
            )  # WHY: initiate upload to Mist support bucket
            if self._print_api_result(
                response,
                f"Support file upload ({info}) initiated.",
                "Support file upload failed",
            ):  # WHY: emit success/error line
                print("-> Files will be available in the Mist dashboard.")  # WHY: teach follow-up
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Support file upload failed: %s", error)  # WHY: audit failure with stack
            print(f"! Support file upload failed: {error}")  # WHY: surface error to operator

    # ------------------------------------------------------------------
    # HARDWARE COMMANDS: poll stats / snapshot
    # ------------------------------------------------------------------

    def poll_switch_stats(self) -> None:
        """Menu 156: Poll fresh statistics from switch."""
        logging.info("Menu #156: Poll Switch Stats")  # WHY: audit menu entry
        selection = self._select_site_and_device("poll_stats", "switch")  # WHY: switch-only op
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        try:
            response = mistapi.api.v1.sites.devices.pollSiteSwitchStats(
                self._apisession, site_id, device_id,
            )  # WHY: force a fresh telemetry poll
            if self._print_api_result(
                response,
                "Fresh statistics polled from switch.",
                "Poll switch stats failed",
            ):  # WHY: emit success/error line
                print("-> Updated stats will appear in next stats export.")  # WHY: manage expectations
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Poll switch stats failed: %s", error)  # WHY: audit failure with stack
            print(f"! Poll switch stats failed: {error}")  # WHY: surface error to operator

    def create_device_snapshot(self) -> None:
        """Menu 157: Create device snapshot on switch."""
        logging.info("Menu #157: Create Device Snapshot")  # WHY: audit menu entry
        selection = self._select_site_and_device("snapshot", "switch")  # WHY: switch-only op
        if not selection:  # WHY: cancelled -> abort
            return
        site_id, device_id, _ = selection  # WHY: unpack (site, device, name)
        try:
            response = mistapi.api.v1.sites.devices.createSiteDeviceSnapshot(
                self._apisession, site_id, device_id,
            )  # WHY: capture in-band device snapshot
            self._print_api_result(
                response,
                "Device snapshot created successfully.",
                "Create snapshot failed",
            )  # WHY: emit success/error line
        except Exception as error:  # WHY: log-and-continue on SDK/transport failure
            logging.exception("Create snapshot failed: %s", error)  # WHY: audit failure with stack
            print(f"! Create snapshot failed: {error}")  # WHY: surface error to operator


def _resolve_support_file_type(raw: str) -> str:
    """Map a raw numeric prompt string to a support-file category.

    Falls back to ``"full"`` on non-numeric input or out-of-range index.
    """
    try:
        type_idx = int(raw) - 1  # WHY: convert 1-based prompt to 0-based index
    except ValueError:
        return "full"  # WHY: non-numeric input falls back to default
    if 0 <= type_idx < len(_SUPPORT_FILE_TYPES):  # WHY: guard against out-of-range indices
        return _SUPPORT_FILE_TYPES[type_idx]  # WHY: valid selection
    return "full"  # WHY: out-of-range falls back to default
