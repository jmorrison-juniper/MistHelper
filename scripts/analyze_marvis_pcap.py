"""Ad-hoc analysis of a Marvis mini-test failure pcap.

Why:
    Mist Marvis "Minis" run synthetic probes from the AP. When a mini test
    fails, the AP saves the on-wire trace as a .pcap. This script walks the
    capture and prints a high-level protocol summary so the operator can see
    which stage (DHCP/DNS/TCP/TLS/HTTP) broke.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scapy.all import DNS, DNSRR, IP, TCP, UDP, rdpcap  # type: ignore[import-untyped]
from scapy.layers.dhcp import DHCP  # type: ignore[import-untyped]
from scapy.layers.tls.handshake import (  # type: ignore[import-untyped]
    TLSClientHello,
    TLSServerHello,
)
from scapy.layers.tls.record import TLS  # type: ignore[import-untyped]


def _record_ip_hosts(pkt: Any, hosts: Counter[str]) -> None:
    """Count packet endpoints when the packet has an IP layer.

    Why:
        The summary prints top talkers, so each IP packet must add its source
        and destination addresses to the same counter.

    Args:
        pkt: Packet from the capture.
        hosts: Counter that receives source and destination addresses.
    """
    if not pkt.haslayer(IP):  # Skip packets that cannot identify endpoint addresses.
        return  # Keep non-IP frames out of the top talker list.
    hosts[pkt[IP].src] += 1  # Count the source address as a talker.
    hosts[pkt[IP].dst] += 1  # Count the destination address as a talker.


def _tcp_flags(tcp_layer: Any) -> list[str]:
    """Return the readable TCP flags that this summary prints.

    Why:
        The report shows connection progress through flag names, not numeric
        bit masks.
    """
    flag_specs = ((0x02, "SYN"), (0x10, "ACK"), (0x01, "FIN"), (0x04, "RST"))  # Preserve the old flag order.
    return [name for mask, name in flag_specs if tcp_layer.flags & mask]  # Keep only the flags set on this packet.


def _record_tcp_flow(pkt: Any, proto: Counter[str], tcp_flows: dict[tuple, list[str]]) -> None:
    """Count TCP packets and record their handshake flags.

    Why:
        The flow table helps an operator find SYN retries, resets, and closes
        without opening the capture.
    """
    if not pkt.haslayer(TCP):  # Leave non-TCP packets for other protocol counters.
        return  # Keep this helper focused on TCP only.
    proto["tcp"] += 1  # Count this packet in the protocol section.
    tcp_layer = pkt[TCP]  # Reuse the TCP layer for port and flag reads.
    flow_key = tuple(
        sorted([(pkt[IP].src, int(tcp_layer.sport)), (pkt[IP].dst, int(tcp_layer.dport))])
    )  # Normalize both directions.
    flags = _tcp_flags(tcp_layer)  # Convert bit flags to the existing names.
    if flags:  # Store only packets that add handshake information.
        tcp_flows[flow_key].append("+".join(flags))  # Preserve the original joined flag format.


def _dns_answers(dns_layer: Any) -> list[str]:
    """Return answer rows for a DNS response.

    Why:
        DNS answer extraction can fail on unusual record payloads, so each
        record stays isolated from the rest of the response.
    """
    answers: list[str] = []  # Preserve the empty answer list for no-answer responses.
    answer = dns_layer.an  # Start at the first DNS answer record.
    while answer is not None:  # Walk the linked DNS answer chain.
        try:  # Keep the summary best-effort for malformed records.
            rdata = answer.rdata  # Read the raw answer value from Scapy.
            if isinstance(rdata, bytes):  # Decode byte values for readable output.
                rdata = rdata.decode(errors="replace")  # Match the previous decode policy.
            answers.append(f"{answer.type}:{rdata}")  # Preserve the old type:value format.
        except Exception:
            pass  # Preserve the old behavior for unreadable answer records.
        answer = (
            answer.payload if hasattr(answer, "payload") else None
        )  # Advance to the next record when Scapy exposes one.
        if not isinstance(answer, DNSRR):  # Stop when the payload no longer holds an answer record.
            break  # Prevent traversal into unrelated packet payloads.
    return answers  # Return all readable answers for this DNS response.


def _record_dns(pkt: Any, proto: Counter[str], dns_q: list[str], dns_r: dict[str, list[str]]) -> None:
    """Count DNS packets and record query and response details.

    Why:
        The report compares each query with collected responses to show names
        that did not receive an answer.
    """
    if not pkt.haslayer(DNS):  # Leave packets without DNS untouched.
        return  # Keep DNS state stable for non-DNS traffic.
    proto["dns"] += 1  # Count this packet in the protocol section.
    dns_layer = pkt[DNS]  # Reuse the DNS layer for query and response reads.
    if dns_layer.qd is None:  # A packet without a question cannot index the summary.
        return  # Preserve the old behavior, which skipped packets without qd.
    query_name = dns_layer.qd.qname.decode(errors="replace").rstrip(".")  # Match the old display name.
    if dns_layer.qr == 0:  # DNS query packets populate the query order.
        dns_q.append(query_name)  # Preserve query order for report output.
        return  # Query packets do not have response text.
    if dns_layer.qr == 1:  # DNS response packets populate the answer map.
        answers = _dns_answers(dns_layer) if dns_layer.ancount else []  # Preserve no-answer response formatting.
        dns_r[query_name].append(f"rcode={dns_layer.rcode} answers={answers}")  # Preserve the old response row.


def _record_dhcp(pkt: Any, dhcp_events: list[str]) -> None:
    """Append DHCP message types from a packet.

    Why:
        The report shows the DHCP exchange shape without exposing option noise.
    """
    if not pkt.haslayer(DHCP):  # Leave packets without DHCP untouched.
        return  # Keep this helper focused on DHCP options.
    for option in pkt[DHCP].options:  # Walk each DHCP option from Scapy.
        if isinstance(option, tuple) and option[0] == "message-type":  # Keep only the event type.
            dhcp_events.append(str(option[1]))  # Preserve Scapy's message value text.


def _client_hello_sni(client_hello: Any) -> str:
    """Return the SNI from a TLS client hello.

    Why:
        The SNI often names the failed destination, but malformed extensions
        must not stop the capture summary.
    """
    try:  # Keep malformed TLS extension parsing non-fatal.
        for extension in client_hello.ext or []:  # Scan extensions in wire order.
            if hasattr(extension, "servernames") and extension.servernames:  # Find the first SNI extension.
                return extension.servernames[0].servername.decode(errors="replace")  # Preserve the old decode policy.
    except Exception:
        pass  # Preserve the old behavior when SNI extraction fails.
    return "?"  # Preserve the old unknown SNI marker.


def _record_tls(pkt: Any, tls_events: list[str]) -> None:
    """Append TLS handshake and alert events from a packet.

    Why:
        TLS events show whether the flow reached handshake or failed with an
        alert.
    """
    if pkt.haslayer(TLSClientHello):  # ClientHello provides the optional SNI value.
        sni = _client_hello_sni(pkt[TLSClientHello])  # Extract SNI with malformed-extension safety.
        tls_events.append(f"ClientHello SNI={sni}")  # Preserve the old ClientHello row.
    if pkt.haslayer(TLSServerHello):  # ServerHello shows the server accepted TLS negotiation.
        tls_events.append("ServerHello")  # Preserve the old ServerHello row.
    if not pkt.haslayer(TLS):  # Alert records only exist inside the TLS layer.
        return  # Keep non-TLS packets out of the alert scan.
    for message in pkt[TLS].msg or []:  # Scan decoded TLS messages in this record.
        if "Alert" in type(message).__name__:  # Keep only TLS alerts for the event list.
            tls_events.append(
                f"Alert level={getattr(message, 'level', '?')} descr={getattr(message, 'descr', '?')}"
            )  # Preserve alert text.


def _record_icmp(pkt: Any, proto: Counter[str]) -> int:
    """Count an ICMP packet when Scapy can test for the layer.

    Why:
        Some Scapy packet shapes can raise during string layer lookup, so the
        summary must keep the same best-effort behavior.
    """
    try:  # Preserve the old non-fatal ICMP layer check.
        if pkt.haslayer("ICMP"):  # Count ICMP packets by layer name.
            proto["icmp"] += 1  # Keep the protocol count in sync with the return value.
            return 1  # Add one packet to the ICMP total.
    except Exception:
        pass  # Preserve the old behavior when layer lookup fails.
    return 0  # Report no ICMP packet for all other cases.


def _print_counts(proto: Counter[str], hosts: Counter[str]) -> None:
    """Print protocol counts and top talkers.

    Why:
        These two sections share only counters, so they stay separate from the
        packet parsing loop.
    """
    print("\n=== protocol counts ===")
    for k, v in proto.most_common():
        print(f"  {k}: {v}")

    print("\n=== top talkers ===")
    for h, c in hosts.most_common(10):
        print(f"  {h}: {c}")


def _print_dhcp_dns(dhcp_events: list[str], dns_q: list[str], dns_r: dict[str, list[str]]) -> None:
    """Print DHCP and DNS sections.

    Why:
        DHCP and DNS explain address assignment and name resolution before the
        later transport sections.
    """
    print("\n=== DHCP ===")
    if dhcp_events:
        print(f"  msg types: {Counter(dhcp_events)}")
    else:
        print("  (none)")

    print("\n=== DNS queries ===")
    for q in dns_q[:20]:
        answered = q in dns_r
        print(f"  Q: {q}  -> {'RESPONSE' if answered else 'NO RESPONSE'}")
        if answered:
            for r in dns_r[q][:3]:
                print(f"      {r}")


def _print_tcp_tls(tcp_flows: dict[tuple, list[str]], tls_events: list[str], icmp_count: int) -> None:
    """Print TCP, TLS, and ICMP sections.

    Why:
        These sections describe connection progress after DHCP and DNS.
    """
    print("\n=== TCP flows ===")
    for (a, b), flags in list(tcp_flows.items())[:15]:
        print(f"  {a[0]}:{a[1]} <-> {b[0]}:{b[1]}  flags={flags[:12]}")

    print("\n=== TLS events ===")
    if tls_events:
        for e in tls_events[:20]:
            print(f"  {e}")
    else:
        print("  (none)")

    print(f"\nicmp packets: {icmp_count}")


def summarize(path: Path) -> None:
    """Emit a per-stage summary of a synthetic-test pcap.

    Args:
        path: Path to the .pcap capture to inspect.
    """
    pkts = rdpcap(str(path))  # Read the capture through Scapy.
    print(f"packets: {len(pkts)}")  # Preserve the first summary line.
    if not pkts:  # Stop when the capture has no frames.
        return  # Preserve the old empty-capture behavior.
    print(f"duration: {float(pkts[-1].time) - float(pkts[0].time):.3f}s")  # Preserve the old duration format.

    proto: Counter[str] = Counter()  # Collect protocol totals for the first section.
    hosts: Counter[str] = Counter()  # Collect source and destination talkers.
    dns_q: list[str] = []  # Preserve DNS query order for report output.
    dns_r: dict[str, list[str]] = defaultdict(list)  # Group DNS responses by question name.
    tcp_flows: dict[tuple, list[str]] = defaultdict(list)  # Group TCP flag rows by bidirectional flow.
    tls_events: list[str] = []  # Keep TLS events in packet order.
    dhcp_events: list[str] = []  # Keep DHCP message types in packet order.
    icmp_count = 0  # Track the ICMP total separately for the final line.

    for pkt in pkts:  # Parse each packet once to preserve output order.
        _record_ip_hosts(pkt, hosts)  # Update the top talker counter.
        _record_tcp_flow(pkt, proto, tcp_flows)  # Update TCP protocol and flow state.
        proto["udp"] += 1 if pkt.haslayer(UDP) else 0  # Preserve the UDP protocol count.
        _record_dns(pkt, proto, dns_q, dns_r)  # Update DNS query and response state.
        _record_dhcp(pkt, dhcp_events)  # Update DHCP message type state.
        _record_tls(pkt, tls_events)  # Update TLS event state.
        icmp_count += _record_icmp(pkt, proto)  # Update ICMP totals with safe layer lookup.

    _print_counts(proto, hosts)  # Print the first two report sections.
    _print_dhcp_dns(dhcp_events, dns_q, dns_r)  # Print DHCP and DNS sections.
    _print_tcp_tls(tcp_flows, tls_events, icmp_count)  # Print connection and ICMP sections.


def main() -> None:
    """CLI entrypoint.

    Why:
        Called ad-hoc from the shell; nothing imports this module.
    """
    if len(sys.argv) < 2:
        print("usage: analyze_marvis_pcap.py <path.pcap>")
        sys.exit(2)
    summarize(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
