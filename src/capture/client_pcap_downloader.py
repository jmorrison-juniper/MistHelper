"""Menu 197: Interactive client packet capture downloader.

Guides the operator through selecting a site, a wireless client, a VLAN
grouping and then downloads all matching packet captures into
``data/packet_captures/<mac>/vlan_<id>/`` on disk. Issue #421.
"""

from __future__ import annotations  # WHY: enable PEP 604 union syntax on Python 3.13.

import logging  # WHY: NON-NEGOTIABLE action-log before/after each side-effect.
import re  # WHY: MAC normalisation strips punctuation via regex.
from collections import defaultdict  # WHY: group captures by VLAN id in one pass.
from dataclasses import dataclass  # WHY: bundle multi-field context immutably per project rule.
from pathlib import Path  # WHY: cross-platform-safe filesystem paths.
from typing import Any  # WHY: mistapi payloads are loosely typed dicts.

import requests  # WHY: streaming HTTP download of PCAP blobs from Mist pre-signed URLs.

try:  # WHY: mistapi is required at runtime but tolerated missing during static analysis / tests.
    import mistapi  # WHY: primary Mist SDK used for site clients + pcaps endpoints.

    MISTAPI_AVAILABLE = True  # WHY: feature flag consumed by callers to guard SDK usage.
except ImportError:  # WHY: allow module import without SDK for offline tooling/tests.
    mistapi = None  # WHY: sentinel so accidental use fails loudly.
    MISTAPI_AVAILABLE = False  # WHY: signals disabled state to downstream consumers.

_HTTP_OK = 200  # WHY: named constant replaces repeated magic 200 across status checks.
_DEFAULT_TIMEOUT_SEC = 300  # WHY: matches historic PacketCaptureDownloadManager timeout budget.
_STREAM_CHUNK_BYTES = 8192  # WHY: 8 KiB chunk size shared with existing PCAP download helpers.
_BYTES_PER_MB = 1024 * 1024  # WHY: reused MB conversion constant avoids duplicated arithmetic.
_DEFAULT_DURATION = "7d"  # WHY: seven-day query window per issue #421 spec.
_CLIENT_PAGE_LIMIT = 1000  # WHY: matches PromptUtils._fetch_site_wireless_clients page size.
_PCAP_PAGE_LIMIT = 1000  # WHY: max page size supported by /sites/{site}/pcaps.
_OUTPUT_ROOT = Path("data") / "packet_captures"  # WHY: hard-coded per issue #421 layout spec.

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for #886 print-to-logger migration.


def _get_config_utils() -> Any:  # WHY: module-level factory for deferred ConfigUtils access.
    """Lazy import ConfigUtils to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: break capture<->MistHelper cycle.

    return _mh.ConfigUtils  # WHY: exposes cached org-id lookup helpers.


def _get_input_utils() -> Any:  # WHY: module-level factory for deferred InputUtils access.
    """Lazy import InputUtils to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: break capture<->MistHelper cycle.

    return _mh.InputUtils  # WHY: exposes safe_input EOF-safe wrapper.


def _get_prompt_utils() -> Any:  # WHY: module-level factory for deferred PromptUtils access.
    """Lazy import PromptUtils to avoid circular imports."""
    import MistHelper as _mh  # pylint: disable=import-outside-toplevel  # WHY: break capture<->MistHelper cycle.

    return _mh.PromptUtils  # WHY: exposes select_site_with_logging helper.


def normalise_mac(raw: str) -> str:
    """Return canonical ``aa:bb:cc:dd:ee:ff`` form from any punctuated 12-hex MAC.

    Accepts ``aabbccddeeff``, ``aa:bb:cc:dd:ee:ff``, ``AA-BB-CC-DD-EE-FF``,
    ``aabb.ccdd.eeff`` and any other punctuation blend. Raises ``ValueError``
    when the stripped input is not exactly 12 hex chars.
    """
    hex_only = re.sub(r"[^0-9a-fA-F]", "", raw)  # WHY: drop separators before length check.
    if len(hex_only) != 12:  # WHY: MAC must be exactly 48 bits (12 hex nibbles).
        raise ValueError(f"Invalid MAC address: {raw!r}")  # WHY: fail loudly on caller mistake.
    return ":".join(hex_only[i : i + 2].lower() for i in range(0, 12, 2))  # WHY: canonical form.


def capture_dir(base: Path, mac: str, vlan_id: int | str) -> Path:
    """Compute ``base/packet_captures/<mac>/vlan_<id>`` per issue #421 spec."""
    mac_folder = mac.replace(":", "_")  # WHY: colons are illegal in Windows path segments.
    vlan_folder = f"vlan_{vlan_id}"  # WHY: keep VLAN grouping visible in on-disk layout.
    return base / "packet_captures" / mac_folder / vlan_folder  # WHY: hierarchical isolation per client.


@dataclass(frozen=True, slots=True)  # WHY: frozen slots keep per-capture rows immutable and hashable.
class _CaptureRow:
    """Row-shape for a completed PCAP awaiting download."""

    capture_id: str  # WHY: unique Mist capture identifier used for logging + filename fallback.
    pcap_url: str  # WHY: pre-signed download URL returned by the pcaps endpoint.
    vlan_id: str  # WHY: normalised VLAN identifier used for grouping and folder naming.
    filename: str  # WHY: server-suggested filename (falls back to capture-id derived name).


class ClientPacketCaptureDownloader:
    """Menu 197 orchestrator: site -> client -> VLAN -> download PCAPs."""

    def __init__(self, apisession: Any, org_id: str | None = None) -> None:
        """Store the mist session and resolve the org-id lazily."""
        logging.debug("ClientPacketCaptureDownloader.__init__ (org_id=%s)", org_id)  # WHY: action-log entry.
        self._session = apisession  # WHY: injected mistapi APISession used by every step.
        self._org_id = org_id or _get_config_utils().get_cached_or_prompted_org_id()  # WHY: cached lookup.
        logging.info("ClientPacketCaptureDownloader ready (org_id=%s)", self._org_id)  # WHY: audit ready state.

    def run(self) -> None:
        """Execute the four-step interactive download flow."""
        logging.info("Menu 197 client PCAP downloader: starting flow")  # WHY: audit start of side-effect chain.
        site_id = self._step1_select_site()  # WHY: fail fast when no site is chosen.
        if not site_id:  # WHY: operator cancelled or no sites available -> abort cleanly.
            return  # WHY: caller (menu dispatch) tolerates None return.
        mac = self._step2_select_client(site_id)  # WHY: fail fast when no client is chosen.
        if not mac:  # WHY: operator cancelled or no matches -> abort cleanly.
            return  # WHY: caller (menu dispatch) tolerates None return.
        vlan_captures = self._step3_select_vlan(site_id, mac)  # WHY: gather VLAN-grouped rows to download.
        if not vlan_captures:  # WHY: no PCAPs matched or operator aborted -> exit quietly.
            return  # WHY: caller (menu dispatch) tolerates None return.
        self._step4_download(mac, vlan_captures)  # WHY: side-effect stage isolated behind the guards.
        logging.info("Menu 197 client PCAP downloader: flow complete")  # WHY: audit end of flow.

    def _step1_select_site(self) -> str | None:
        """Prompt for a site via the shared PromptUtils helper."""
        logging.debug("Step 1: prompting for site selection")  # WHY: action-log entry.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n[Step 1/4] Select a site")  # WHY: operator-visible step banner.
        site_id = _get_prompt_utils().select_site_with_logging()  # WHY: shared CSV-driven chooser.
        logging.info("Step 1 selected site_id=%s", site_id)  # WHY: audit selection outcome.
        return str(site_id) if site_id else None  # WHY: normalise Any->str|None for typing.

    def _step2_select_client(self, site_id: str) -> str | None:
        """Fetch site wireless clients and let operator pick by index or MAC."""
        logging.debug("Step 2: fetching wireless clients for site %s", site_id)  # WHY: action-log entry.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n[Step 2/4] Select a wireless client")  # WHY: operator-visible step banner.
        clients = self._fetch_wireless_clients(site_id)  # WHY: isolate SDK call for testability.
        if not clients:  # WHY: no clients seen in the query window -> abort.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("  No wireless clients found in the last 7 days.")  # WHY: operator feedback.
            logging.warning("Step 2 aborted: no wireless clients for site %s", site_id)  # WHY: audit no-op.
            return None  # WHY: caller treats None as cancel/abort.
        self._render_client_table(clients)  # WHY: display index table before prompting.
        return self._prompt_client_choice(clients)  # WHY: dedicated prompt keeps this function short.

    def _fetch_wireless_clients(self, site_id: str) -> list[dict[str, Any]]:
        """Return all wireless clients seen at ``site_id`` in the past 7 days."""
        if not MISTAPI_AVAILABLE:  # WHY: guard offline execution paths.
            logging.error("mistapi unavailable; cannot fetch wireless clients")  # WHY: audit failure.
            return []  # WHY: empty list drives operator-visible abort.
        try:  # WHY: network/SDK errors must not crash the menu dispatcher.
            response = mistapi.api.v1.sites.clients.searchSiteWirelessClients(
                self._session, site_id, duration=_DEFAULT_DURATION, limit=_CLIENT_PAGE_LIMIT
            )  # WHY: 7-day window scoped to the chosen site.
            clients = mistapi.get_all(response=response, mist_session=self._session) or []
            logging.info("Fetched %s wireless clients for site %s", len(clients), site_id)  # WHY: audit count.
            return clients  # WHY: caller renders and prompts.
        except Exception as exc:  # pylint: disable=broad-exception-caught  # WHY: keep menu resilient.
            logging.exception("Failed to fetch wireless clients: %s", exc)  # WHY: capture stack for triage.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("  Error fetching wireless clients: %s", exc)  # WHY: operator-visible feedback.
            return []  # WHY: empty list drives abort path.

    @staticmethod
    def _render_client_table(clients: list[dict[str, Any]]) -> None:
        """Display an index/hostname/MAC/last-seen table to the operator."""
        logging.debug("Rendering %s client rows", len(clients))  # WHY: action-log entry.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n  %4s  %-32s  %-17s  Last IP", "#", "Hostname", "MAC")  # WHY: column header.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("  %s  %s  %s  %s", "-" * 4, "-" * 32, "-" * 17, "-" * 15)  # WHY: divider row.
        for idx, client in enumerate(clients, start=1):  # WHY: 1-based index matches operator prompt.
            hostname = str(client.get("hostname") or client.get("username") or "-")[:32]  # WHY: truncate wide names.
            mac = str(client.get("mac") or "-")  # WHY: guard missing MAC.
            last_ip = str(client.get("ip") or client.get("last_ip") or "-")  # WHY: helps disambiguate hosts.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("  %4d  %-32s  %-17s  %s", idx, hostname, mac, last_ip)  # WHY: uniform aligned rendering.

    def _prompt_client_choice(self, clients: list[dict[str, Any]]) -> str | None:
        """Read a 1-based index or free-form MAC and return the normalised MAC."""
        logging.debug("Prompting operator for client choice among %s rows", len(clients))  # WHY: action-log.
        prompt = "\nEnter row number or full MAC address (blank to cancel): "  # WHY: dual input mode.
        raw = _get_input_utils().safe_input(prompt, context="menu_197_client")  # WHY: EOF-safe wrapper.
        if not raw:  # WHY: blank input signals cancel per InputUtils contract.
            logging.info("Step 2 cancelled by operator (blank input)")  # WHY: audit cancel.
            return None  # WHY: caller treats None as cancel.
        return self._resolve_client_choice(raw, clients)  # WHY: split parse logic to stay under line cap.

    @staticmethod
    def _resolve_client_choice(raw: str, clients: list[dict[str, Any]]) -> str | None:
        """Interpret ``raw`` as either a 1-based index or a MAC address."""
        if raw.isdigit():  # WHY: numeric input -> index lookup path.
            idx = int(raw)  # WHY: parse 1-based row number.
            if 1 <= idx <= len(clients):  # WHY: bounds-check before dereference.
                mac = str(clients[idx - 1].get("mac") or "")  # WHY: pull MAC from selected row.
                if mac:  # WHY: guard rows without a MAC field.
                    return normalise_mac(mac)  # WHY: normalise before returning to caller.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("  Invalid row number: %s", raw)  # WHY: operator feedback on bad index.
            logging.warning("Step 2 rejected bad index: %s", raw)  # WHY: audit bad input.
            return None  # WHY: cancel path.
        try:  # WHY: non-numeric input treated as MAC; catch bad format loudly.
            return normalise_mac(raw)  # WHY: accept any punctuation blend.
        except ValueError as exc:  # WHY: normalise_mac raises on non-12-hex input.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("  %s", exc)  # WHY: operator feedback on bad MAC.
            logging.warning("Step 2 rejected bad MAC: %s", raw)  # WHY: audit bad input.
            return None  # WHY: cancel path.

    def _step3_select_vlan(self, site_id: str, mac: str) -> list[_CaptureRow]:
        """List PCAPs for ``mac`` at ``site_id`` grouped by VLAN and let operator choose."""
        logging.debug("Step 3: listing PCAPs for site %s client %s", site_id, mac)  # WHY: action-log entry.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n[Step 3/4] Select a VLAN for client %s", mac)  # WHY: operator-visible step banner.
        captures = self._fetch_captures(site_id, mac)  # WHY: isolate SDK call for testability.
        if not captures:  # WHY: no PCAPs matched -> abort with feedback.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("  No packet captures found for this client in the last 7 days.")  # WHY: feedback.
            logging.warning("Step 3 aborted: no PCAPs for %s at %s", mac, site_id)  # WHY: audit no-op.
            return []  # WHY: empty list signals abort to caller.
        grouped = self._group_by_vlan(captures)  # WHY: bucket captures into per-VLAN lists.
        return self._prompt_vlan_choice(grouped)  # WHY: dedicated prompt keeps this function short.

    def _fetch_captures(self, site_id: str, mac: str) -> list[dict[str, Any]]:
        """Return all PCAPs for ``mac`` at ``site_id`` in the past 7 days."""
        if not MISTAPI_AVAILABLE:  # WHY: guard offline execution paths.
            logging.error("mistapi unavailable; cannot fetch PCAPs")  # WHY: audit failure.
            return []  # WHY: empty list drives operator-visible abort.
        try:  # WHY: network/SDK errors must not crash the menu dispatcher.
            response = mistapi.api.v1.sites.pcaps.listSitePacketCaptures(
                self._session,
                site_id,
                client_mac=mac.replace(":", ""),
                duration=_DEFAULT_DURATION,
                limit=_PCAP_PAGE_LIMIT,
            )  # WHY: Mist expects unpunctuated MAC in query filter.
            captures = mistapi.get_all(response=response, mist_session=self._session) or []
            logging.info("Fetched %s PCAPs for %s", len(captures), mac)  # WHY: audit count.
            return captures  # WHY: caller normalises/groups.
        except Exception as exc:  # pylint: disable=broad-exception-caught  # WHY: keep menu resilient.
            logging.exception("Failed to fetch PCAPs: %s", exc)  # WHY: capture stack for triage.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("  Error fetching PCAPs: %s", exc)  # WHY: operator-visible feedback.
            return []  # WHY: empty list drives abort path.

    @staticmethod
    def _group_by_vlan(captures: list[dict[str, Any]]) -> dict[str, list[_CaptureRow]]:
        """Bucket capture dicts into per-VLAN ordered rows, skipping URL-less entries."""
        groups: dict[str, list[_CaptureRow]] = defaultdict(list)  # WHY: default-dict avoids key-exists checks.
        for capture in captures:  # WHY: single pass over API payload.
            pcap_url = str(capture.get("pcap_url") or "")  # WHY: guard missing URL (still in-progress capture).
            if not pcap_url:  # WHY: skip captures that have no download URL yet.
                continue  # WHY: cannot download without URL.
            vlan_id = str(capture.get("vlan_id") or capture.get("vlan") or "unknown")  # WHY: safe grouping key.
            capture_id = str(capture.get("id") or capture.get("capture_id") or "unknown")  # WHY: fallback id.
            filename = str(capture.get("filename") or f"{capture_id}.pcap")  # WHY: server name or derived.
            groups[vlan_id].append(_CaptureRow(capture_id, pcap_url, vlan_id, filename))  # WHY: enqueue row.
        return groups  # WHY: caller ranks and displays.

    def _prompt_vlan_choice(self, grouped: dict[str, list[_CaptureRow]]) -> list[_CaptureRow]:
        """Show one VLAN row per bucket with a count column and return the chosen rows."""
        if not grouped:  # WHY: all captures were URL-less -> nothing to download.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("  No completed PCAPs available (all still in progress).")  # WHY: operator feedback.
            logging.warning("Step 3: no VLAN groups had downloadable URLs")  # WHY: audit no-op.
            return []  # WHY: caller aborts flow.
        vlan_ids = sorted(grouped.keys())  # WHY: deterministic ordering for stable operator UX.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n  %4s  %-10s  Captures", "#", "VLAN")  # WHY: column header for readability.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("  %s  %s  %s", "-" * 4, "-" * 10, "-" * 8)  # WHY: divider separates header/rows.
        for idx, vlan_id in enumerate(vlan_ids, start=1):  # WHY: 1-based index matches prompt.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("  %4d  %-10s  %d", idx, vlan_id, len(grouped[vlan_id]))  # WHY: show count per bucket.
        raw = _get_input_utils().safe_input(
            "\nEnter row number to download all captures for that VLAN (blank to cancel): ",
            context="menu_197_vlan",
        )  # WHY: EOF-safe read of operator choice.
        return self._resolve_vlan_choice(raw, vlan_ids, grouped)  # WHY: extract parse to stay under line cap.

    @staticmethod
    def _resolve_vlan_choice(raw: str, vlan_ids: list[str], grouped: dict[str, list[_CaptureRow]]) -> list[_CaptureRow]:
        """Validate the row number and return the matching VLAN's capture rows."""
        if not raw:  # WHY: blank input signals cancel per InputUtils contract.
            logging.info("Step 3 cancelled by operator (blank input)")  # WHY: audit cancel.
            return []  # WHY: caller treats [] as cancel.
        if not raw.isdigit():  # WHY: only accept numeric row selection here.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("  Invalid row number: %s", raw)  # WHY: operator feedback on non-numeric.
            logging.warning("Step 3 rejected non-numeric: %s", raw)  # WHY: audit bad input.
            return []  # WHY: cancel path.
        idx = int(raw)  # WHY: parse 1-based row number.
        if not 1 <= idx <= len(vlan_ids):  # WHY: bounds-check before dereference.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("  Row number out of range: %s", raw)  # WHY: operator feedback on bad index.
            logging.warning("Step 3 rejected out-of-range: %s", raw)  # WHY: audit bad input.
            return []  # WHY: cancel path.
        chosen = vlan_ids[idx - 1]  # WHY: translate 1-based index to key.
        logging.info("Step 3 selected VLAN %s (%s captures)", chosen, len(grouped[chosen]))  # WHY: audit.
        return grouped[chosen]  # WHY: hand off rows to download step.

    def _step4_download(self, mac: str, rows: list[_CaptureRow]) -> None:
        """Download each PCAP row into ``data/packet_captures/<mac>/vlan_<id>/``."""
        vlan_id = rows[0].vlan_id  # WHY: all rows in this call share the same VLAN by construction.
        target = capture_dir(Path("data"), mac, vlan_id)  # WHY: single spec-defined path builder.
        logging.debug("Step 4: creating output dir %s", target)  # WHY: action-log entry.
        target.mkdir(parents=True, exist_ok=True)  # WHY: idempotent; safe on repeat runs.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n[Step 4/4] Downloading %d PCAP(s) to %s", len(rows), target)  # WHY: banner.
        succeeded = self._download_all(rows, target)  # WHY: isolate loop for testability.
        logging.info("Step 4 done: %s/%s PCAPs downloaded", succeeded, len(rows))  # WHY: audit result.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n  Complete: %d/%d files written to %s", succeeded, len(rows), target)  # WHY: summary.

    def _download_all(self, rows: list[_CaptureRow], target: Path) -> int:
        """Iterate over rows and download each; return the count of successful writes."""
        succeeded = 0  # WHY: accumulator for summary line.
        for row in rows:  # WHY: sequential to preserve per-file operator feedback ordering.
            if self._download_one(row, target):  # WHY: bool return keeps accumulator arithmetic simple.
                succeeded += 1  # WHY: increment only on success.
        return succeeded  # WHY: caller emits summary line with this count.

    @staticmethod
    def _download_one(row: _CaptureRow, target: Path) -> bool:
        """Stream a single PCAP to disk under ``target``. Return True on success."""
        local_path = target / row.filename  # WHY: join via pathlib for cross-platform safety.
        logging.info("Downloading PCAP %s from %s", row.capture_id, row.pcap_url)  # WHY: audit before HTTP.
        try:  # WHY: transfer + write must not crash the batch.
            response = requests.get(row.pcap_url, stream=True, timeout=_DEFAULT_TIMEOUT_SEC)  # WHY: stream.
            if response.status_code != _HTTP_OK:  # WHY: guard non-200 responses before write.
                # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
                logger.error("    Failed %s: HTTP %s", row.filename, response.status_code)  # WHY: feedback.
                logging.error("Download failed %s: %s", row.capture_id, response.status_code)  # WHY: audit.
                return False  # WHY: skip write on failure.
            with open(local_path, "wb") as pcap_file:  # WHY: binary write for PCAP payload.
                for chunk in response.iter_content(chunk_size=_STREAM_CHUNK_BYTES):  # WHY: chunked stream.
                    pcap_file.write(chunk)  # WHY: persist each chunk incrementally.
            size_mb = local_path.stat().st_size / _BYTES_PER_MB  # WHY: compute size for user feedback.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("    Downloaded %s (%.2f MB)", row.filename, size_mb)  # WHY: operator success line.
            logging.info("Downloaded %s: %.2f MB -> %s", row.capture_id, size_mb, local_path)  # WHY: audit.
            return True  # WHY: successful write.
        except Exception as exc:  # pylint: disable=broad-exception-caught  # WHY: keep batch resilient.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("    Error downloading %s: %s", row.filename, exc)  # WHY: operator failure line.
            logging.exception("Download exception for %s: %s", row.capture_id, exc)  # WHY: audit stack.
            return False  # WHY: signal failure to accumulator.
