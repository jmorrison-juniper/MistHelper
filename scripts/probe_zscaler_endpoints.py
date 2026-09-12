"""Probe Zscaler synthetic-test endpoints and record protocol/server behavior.

Why:
    Menu option 206 (org synthetic-probes manager) seeds Mist synthetic tests from
    ``data/zscaler_client_connector_probes.json`` and ``data/zscaler_cenr_hostnames.json``.
    The JSON catalogues declare which ports Zscaler *documents*, but not which
    protocols each endpoint actually answers on today. This script probes each
    FQDN across ICMP, TCP (80/443/8080), HTTP, and HTTPS, classifies the server,
    and writes a markdown report so operators can audit the seeded probe plan
    against reality before pushing it to Mist.

    The probe primitives themselves live in :mod:`src.utils.zscaler_probe` so
    the same code path is used by the menu-206 auto-refresh gate in
    :mod:`src.utils.zscaler_catalogue`. This script is now a thin CLI wrapper
    that reads the two JSON catalogues, invokes the shared probe runner, and
    renders the markdown report.

Usage:
    python scripts/probe_zscaler_endpoints.py [--cenr-sample N] [--timeout SEC]

Notes:
    - Uses only Python stdlib so it runs anywhere MistHelper does.
    - UDS is Zscaler-internal (loopback IPC) and cannot be probed remotely; that
      is called out in the report rather than tested.
    - The CENR list has ~990 proxy hostnames that all share behavior; by default
      we sample the first 15 to keep runtime reasonable.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Repo layout: this script lives in <repo>/scripts, and the reusable probe
# primitives live in <repo>/src/utils/zscaler_probe.py. Make ``src`` importable
# so ``from src.utils.zscaler_probe import ...`` works when the script is run
# directly (e.g. ``python scripts/probe_zscaler_endpoints.py``).
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.zscaler_probe import (  # noqa: E402 -- sys.path tweak above must run first
    DEFAULT_TIMEOUT,
    DEFAULT_WORKERS,
    ProbeResult,
    _run_probes,
)

DATA_DIR = REPO_ROOT / "data"
PROBE_FILE = DATA_DIR / "zscaler_client_connector_probes.json"
CENR_FILE = DATA_DIR / "zscaler_cenr_hostnames.json"

DEFAULT_CENR_SAMPLE = 15


def _load_roles() -> list[tuple[str, dict[str, Any]]]:
    """Return a flat ``[(fqdn, role_dict)]`` list from the ZCC probe JSON.

    Why:
        The ZCC catalogue nests FQDNs under roles, but the probe runner takes
        a flat list of ``(fqdn, role)`` tuples. Flattening here keeps the
        probe API narrow and easy to unit-test.

    Returns:
        List of ``(fqdn, role_dict)`` tuples in catalogue order.
    """
    doc = json.loads(PROBE_FILE.read_text(encoding="utf-8"))
    out: list[tuple[str, dict[str, Any]]] = []
    for role in doc.get("roles", []):
        for fqdn in role.get("fqdns", []) or []:
            out.append((str(fqdn), role))
    return out


def _load_cenr(sample: int) -> list[tuple[str, dict[str, Any]]]:
    """Return a sampled ``[(fqdn, synthetic_role)]`` list from the CENR hostnames JSON.

    Why:
        The CENR feed exposes ~990 proxy hostnames that all behave identically
        at HTTPS/443. Probing every one on every CLI run is overkill; the
        script defaults to the first *sample* hosts so operators can spot-check
        quickly. (The menu-206 auto-refresh path in
        :mod:`src.utils.zscaler_catalogue` uses the full fleet instead.)

    Args:
        sample: Number of hostnames to include (from the top of the list).

    Returns:
        List of ``(fqdn, synthetic_role_dict)`` tuples; empty if the file has
        no ``proxy_hostnames``.
    """
    doc = json.loads(CENR_FILE.read_text(encoding="utf-8"))
    hosts = list(doc.get("proxy_hostnames", []))
    picked = hosts[:sample]
    role = {
        "role": "cenr_zen_proxy",
        "description": "Zscaler ZEN cloud-enforcement proxy (sampled)",
        "ports": [80, 443, 8080],
        "critical": False,
    }
    return [(h, role) for h in picked]


def _fmt_ports(res: ProbeResult) -> str:
    """Render the TCP port scan as a compact string.

    Args:
        res: Probe result whose ``tcp`` dict should be rendered.

    Returns:
        Space-separated ``"PORT=STATE"`` string; ``"-"`` when no ports were
        scanned.
    """
    if not res.tcp:
        return "-"
    parts: list[str] = []
    for port, state in sorted(res.tcp.items()):
        mark = "OPEN" if state == "open" else ("CLOSED" if state == "closed" else state)
        parts.append(f"{port}={mark}")
    return " ".join(parts)


def _write_report(
    zcc_results: list[ProbeResult],
    cenr_results: list[ProbeResult],
    out_path: Path,
    timeout: float,
    cenr_sample: int,
) -> None:
    """Write a human-readable markdown report for both probe sets.

    Why:
        Operators auditing menu 206's synthetic-probe plan want a single
        artefact they can commit / attach to a ticket. Markdown renders in
        GitHub and Jira without extra tooling.

    Args:
        zcc_results: Probe results for the ZCC required-destinations catalogue.
        cenr_results: Probe results for the sampled CENR proxy hostnames.
        out_path: Destination markdown file.
        timeout: Per-probe timeout in seconds (rendered in the header).
        cenr_sample: How many CENR hostnames were sampled (rendered in the header).
    """
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")
    lines: list[str] = []
    lines.append("# Zscaler Synthetic-Probe Endpoint Audit")
    lines.append("")
    lines.append(f"- **Generated:** {now}")
    lines.append(f"- **Timeout per probe:** {timeout:.1f}s")
    lines.append(f"- **Source (roles):** `{PROBE_FILE.relative_to(REPO_ROOT)}`")
    lines.append(f"- **Source (CENR):** `{CENR_FILE.relative_to(REPO_ROOT)}` (sampled {cenr_sample} hostnames)")
    lines.append("- **Menu option:** 206 -- Org Synthetic Probes Manager")
    lines.append("")
    lines.append("Legend for **Actual protocols**: probes that returned a live response.")
    lines.append(
        "`UDS` is intentionally excluded -- Zscaler Client Connector's UDS "
        "channel is loopback IPC and not reachable over the network."
    )
    lines.append("")

    lines.extend(_render_section("ZCC required destinations (per role)", zcc_results))
    lines.append("")
    lines.extend(_render_section("Zscaler CENR proxy hostnames (sampled)", cenr_results))
    lines.append("")

    lines.append("## Column meanings")
    lines.append("")
    lines.append("| Column | Meaning |")
    lines.append("|---|---|")
    lines.append("| FQDN | Hostname pulled from the JSON catalogue. |")
    lines.append("| Role | `roles[].role` from the catalogue. |")
    lines.append("| Declared ports | `roles[].ports` -- what Zscaler *documents* the endpoint needs. |")
    lines.append("| IP | First A-record returned by `getaddrinfo`. |")
    lines.append("| ICMP | Whether the host answered a single system `ping`. |")
    lines.append("| TCP ports | Handshake result for the union of declared ports + 80/443/8080. |")
    lines.append("| HTTP / HTTPS status | Response code from `HEAD /` (falls back to `GET /` on 405). |")
    lines.append("| Server | `Server:` response header. |")
    lines.append("| TLS issuer | Certificate issuer CN/O (identifies the CA / operator). |")
    lines.append("| Server class | Inferred category from FQDN + headers + cert. |")
    lines.append("| Actual protocols | Protocols we confirmed a response on right now. |")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def _render_section(title: str, results: list[ProbeResult]) -> list[str]:
    """Render one titled table plus per-row notes.

    Args:
        title: Section heading.
        results: Probe results to render.

    Returns:
        List of markdown lines (no trailing newline).
    """
    lines: list[str] = [f"## {title}", ""]
    if not results:
        lines.append("_No entries._")
        return lines
    lines.extend(_render_table(results))  # Add the table rows for this section.
    lines.extend(_render_notes(results))  # Add the notes block when entries have notes.
    return lines


def _render_table(results: list[ProbeResult]) -> list[str]:
    """Render the endpoint result table.

    Why:
        A separate table helper keeps the section builder small and keeps the
        column order in one place.
    """
    lines = [_table_header(), "|---|---|---|---|---|---|---|---|---|---|---|---|"]  # Start with the markdown header.
    for result in results:  # Preserve the input order from the probe runner.
        lines.append(_render_result_row(result))  # Convert each result into one markdown row.
    return lines  # Return the complete table block.


def _table_header() -> str:
    """Return the markdown header for a probe result table.

    Why:
        The header string is long, so this helper keeps the caller readable.
    """
    return (
        "| FQDN | Role | Declared ports | IP | ICMP | TCP ports | HTTP | HTTPS"
        " | Server | TLS issuer | Server class | Actual protocols |"
    )  # Preserve the old header text.


def _render_result_row(result: ProbeResult) -> str:
    """Render one probe result as a markdown table row.

    Why:
        Each cell has a small fallback rule, and the row helper keeps those
        rules near the row format.
    """
    endpoint = _render_endpoint_cells(result)  # Build the identity and network cells.
    services = _render_service_cells(result)  # Build the HTTP, TLS, and protocol cells.
    return (
        f"| `{result.fqdn}` | `{result.role}` | {endpoint['declared']} | {endpoint['ip']} | "
        f"{endpoint['icmp']} | {_fmt_ports(result)} | {services['http']} | {services['https']} | "
        f"{_md_escape(services['server'])} | {_md_escape(services['issuer'])} | "
        f"{result.server_class} | {services['protocols']} |"
    )  # Preserve the old row format.


def _render_endpoint_cells(result: ProbeResult) -> dict[str, str]:
    """Render the identity and network cells for one result.

    Why:
        DNS, ICMP, and declared port fallbacks are independent of service
        probe results.
    """
    return {
        "declared": ",".join(str(port) for port in result.declared_ports) or "-",  # Preserve declared port display.
        "icmp": "yes" if result.icmp_ok else "no",  # Preserve ICMP yes/no text.
        "ip": result.ip
        or (f"DNS FAIL ({result.dns_error})" if result.dns_error else "-"),  # Preserve DNS fallback text.
    }  # Return named cells so the row format stays readable.


def _render_service_cells(result: ProbeResult) -> dict[str, str]:
    """Render the HTTP, TLS, and protocol cells for one result.

    Why:
        The service cells share fallback rules and must keep their old text.
    """
    return {
        "http": _status_with_location(result.http_status, result.http_location),  # Render the HTTP status cell.
        "https": _status_with_location(result.https_status, result.https_location),  # Render the HTTPS status cell.
        "issuer": result.tls_issuer or "-",  # Preserve the old empty issuer fallback.
        "protocols": ", ".join(result.responding_protocols) or "none",  # Preserve the old empty protocol fallback.
        "server": result.https_server or result.http_server or "-",  # Prefer HTTPS server, as before.
    }  # Return named cells so the row format stays readable.


def _status_with_location(status: int | None, location: str | None) -> str:
    """Render a status code with an optional redirect location.

    Why:
        The old report included the redirect target only when the probe found
        one.
    """
    if status is None:  # Missing status means the probe did not receive a response.
        return "-"  # Preserve the old no-status marker.
    suffix = f" -> {location}" if location else ""  # Preserve redirect text when present.
    return f"{status}{suffix}"  # Preserve the old status display.


def _render_notes(results: list[ProbeResult]) -> list[str]:
    """Render per-host notes for results that have notes.

    Why:
        Notes stay below the table, and empty note sets must produce no lines.
    """
    note_lines: list[str] = []  # Collect note rows without touching the caller's list.
    for result in results:  # Preserve result order in the notes block.
        note_lines.extend(f"- `{result.fqdn}`: {note}" for note in result.notes)  # Preserve one bullet per note.
    if not note_lines:  # No notes means the old function added no note heading.
        return []  # Return no markdown lines for empty note sets.
    return ["", "### Notes", "", *note_lines]  # Preserve the old note heading and spacing.


def _md_escape(text: str) -> str:
    r"""Escape pipes so the value doesn't break the markdown table.

    Args:
        text: Raw cell text.

    Returns:
        Text with ``|`` replaced by ``\|``.
    """
    return text.replace("|", "\\|")


def main() -> int:
    """Parse CLI args, run the probes, and write the markdown report.

    Why:
        Thin CLI wrapper over :func:`src.utils.zscaler_probe._run_probes`.
        Kept as an operator entry point so folks can audit endpoint reality
        without importing the menu 206 machinery.

    Returns:
        Process exit code (0 on success).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Per-probe timeout in seconds.")
    parser.add_argument("--cenr-sample", type=int, default=DEFAULT_CENR_SAMPLE, help="How many CENR proxies to probe.")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Concurrent probe workers.")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output markdown path; default: data/zscaler_probe_results_<UTC>.md",
    )
    args = parser.parse_args()

    zcc_entries = _load_roles()
    cenr_entries = _load_cenr(max(0, args.cenr_sample))

    print(f"Probing {len(zcc_entries)} ZCC FQDNs and {len(cenr_entries)} CENR hostnames ...", flush=True)
    start = time.monotonic()
    zcc_results = _run_probes(zcc_entries, args.timeout, args.workers)
    cenr_results = _run_probes(cenr_entries, args.timeout, args.workers)
    elapsed = time.monotonic() - start
    print(f"Probes complete in {elapsed:.1f}s.", flush=True)

    if args.out:
        out_path = args.out
    else:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out_path = DATA_DIR / f"zscaler_probe_results_{stamp}.md"

    _write_report(zcc_results, cenr_results, out_path, args.timeout, args.cenr_sample)
    print(f"Report written: {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
