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

from scapy.all import DNS, DNSQR, DNSRR, IP, TCP, UDP, Ether, rdpcap  # type: ignore[import-untyped]
from scapy.layers.dhcp import BOOTP, DHCP  # type: ignore[import-untyped]
from scapy.layers.tls.handshake import (  # type: ignore[import-untyped]
    TLSClientHello,
    TLSServerHello,
)
from scapy.layers.tls.record import TLS  # type: ignore[import-untyped]


def summarize(path: Path) -> None:
    """Emit a per-stage summary of a synthetic-test pcap.

    Args:
        path: Path to the .pcap capture to inspect.
    """
    pkts = rdpcap(str(path))
    print(f"packets: {len(pkts)}")
    if not pkts:
        return
    t0 = float(pkts[0].time)
    tN = float(pkts[-1].time)
    print(f"duration: {tN - t0:.3f}s")

    proto: Counter[str] = Counter()
    hosts: Counter[str] = Counter()
    dns_q: list[str] = []
    dns_r: dict[str, list[str]] = defaultdict(list)
    tcp_flows: dict[tuple, list[str]] = defaultdict(list)
    tls_events: list[str] = []
    dhcp_events: list[str] = []
    icmp_count = 0

    for pkt in pkts:
        if pkt.haslayer(IP):
            hosts[pkt[IP].src] += 1
            hosts[pkt[IP].dst] += 1
        if pkt.haslayer(TCP):
            proto["tcp"] += 1
            t = pkt[TCP]
            key = tuple(sorted([(pkt[IP].src, int(t.sport)), (pkt[IP].dst, int(t.dport))]))
            flags = []
            if t.flags & 0x02:
                flags.append("SYN")
            if t.flags & 0x10:
                flags.append("ACK")
            if t.flags & 0x01:
                flags.append("FIN")
            if t.flags & 0x04:
                flags.append("RST")
            if flags:
                tcp_flows[key].append("+".join(flags))
        if pkt.haslayer(UDP):
            proto["udp"] += 1
        if pkt.haslayer(DNS):
            proto["dns"] += 1
            d = pkt[DNS]
            if d.qr == 0 and d.qd is not None:
                q = d.qd.qname.decode(errors="replace").rstrip(".")
                dns_q.append(q)
            elif d.qr == 1 and d.qd is not None:
                q = d.qd.qname.decode(errors="replace").rstrip(".")
                answers = []
                if d.ancount:
                    an = d.an
                    while an is not None:
                        try:
                            rdata = an.rdata
                            if isinstance(rdata, bytes):
                                rdata = rdata.decode(errors="replace")
                            answers.append(f"{an.type}:{rdata}")
                        except Exception:
                            pass
                        an = an.payload if hasattr(an, "payload") else None
                        if not isinstance(an, DNSRR):
                            break
                dns_r[q].append(f"rcode={d.rcode} answers={answers}")
        if pkt.haslayer(DHCP):
            for opt in pkt[DHCP].options:
                if isinstance(opt, tuple) and opt[0] == "message-type":
                    dhcp_events.append(str(opt[1]))
        if pkt.haslayer(TLSClientHello):
            ch = pkt[TLSClientHello]
            sni = "?"
            try:
                for ext in ch.ext or []:
                    if hasattr(ext, "servernames") and ext.servernames:
                        sni = ext.servernames[0].servername.decode(errors="replace")
            except Exception:
                pass
            tls_events.append(f"ClientHello SNI={sni}")
        if pkt.haslayer(TLSServerHello):
            tls_events.append("ServerHello")
        if pkt.haslayer(TLS):
            for msg in pkt[TLS].msg or []:
                name = type(msg).__name__
                if "Alert" in name:
                    tls_events.append(f"Alert level={getattr(msg, 'level', '?')} descr={getattr(msg, 'descr', '?')}")
        # ICMP
        try:
            if pkt.haslayer("ICMP"):
                icmp_count += 1
                proto["icmp"] += 1
        except Exception:
            pass

    print("\n=== protocol counts ===")
    for k, v in proto.most_common():
        print(f"  {k}: {v}")

    print("\n=== top talkers ===")
    for h, c in hosts.most_common(10):
        print(f"  {h}: {c}")

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
