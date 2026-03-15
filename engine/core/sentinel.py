"""
RCA Sentinel: Asset Discovery Engine for OT/IT Environments.
Performs safe, non-disruptive asset identification using:
  1. Passive sniffing (Scapy) — zero-footprint listening
  2. Active ARP scanning — targeted L2 sweeps
  3. Active ICMP sweeps — targeted L3 ping sweeps

Optimised for manufacturing networks with legacy Windows (XP/7/10)
and industrial hardware (PLCs, CNCs, HMIs).

# Satisfies NIST 800-171 Rev 3:
# 3.4.1  - Establish and maintain baseline configurations and inventories.
# 3.13.1 - Monitor, control, and protect organisational communications.
# 3.11.2 - Scan for vulnerabilities in organisational systems periodically.
"""

import logging
from typing import Dict, List, Set

from scapy.all import ARP, Ether, IP, ICMP, srp, sr1, sniff

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Sentinel - %(message)s",
)
logger = logging.getLogger(__name__)


class SentinelEngine:
    """
    Multi-method network scanner for "Hidden OT" discovery.

    Discovery order recommendation for sensitive OT environments:
      1. passive_sniffing()   — safest, listens only
      2. active_arp_scan()    — L2, low-risk on same subnet
      3. icmp_sweep()         — L3, use sparingly on fragile segments
    """

    def __init__(self):
        # In-memory inventory of discovered assets
        # Satisfies NIST 800-171 3.4.1 (Inventories)
        self.inventory: Dict[str, Dict[str, str]] = {}
        self.seen_ips: Set[str] = set()

    # ------------------------------------------------------------------
    # 1. Passive Sniffing
    # ------------------------------------------------------------------
    def passive_sniffing(
        self, iface: str = None, packet_count: int = 100, timeout: int = 30
    ) -> None:
        """
        Listen to network traffic passively to discover chatty nodes
        (PLCs, Windows endpoints, HMIs) without sending any frames.

        # Satisfies NIST 800-171 3.13.1 and 3.4.1
        """
        logger.info(
            f"Starting passive sniffing for {timeout}s / {packet_count} packets …"
        )
        sniff(
            iface=iface,
            prn=self._packet_callback,
            store=False,
            count=packet_count,
            timeout=timeout,
        )
        logger.info("Passive sniffing session complete.")

    def _packet_callback(self, packet) -> None:
        """Extract source IP/MAC from every observed packet."""
        if packet.haslayer(IP):
            src_ip = packet[IP].src
            src_mac = packet[Ether].src if packet.haslayer(Ether) else "Unknown"
            if src_ip not in self.seen_ips:
                self.seen_ips.add(src_ip)
                asset = {
                    "ip_address": src_ip,
                    "mac_address": src_mac,
                    "discovery_method": "passive_sniff",
                }
                self.inventory[src_ip] = asset
                logger.info(f"[Passive] New asset: {src_ip} ({src_mac})")

    # ------------------------------------------------------------------
    # 2. Active ARP Scan (Layer 2)
    # ------------------------------------------------------------------
    def active_arp_scan(
        self, target_subnet: str, timeout: int = 2
    ) -> List[Dict[str, str]]:
        """
        ARP sweep across a subnet. Safe on the local broadcast domain.

        # Satisfies NIST 800-171 3.4.1
        """
        logger.info(f"ARP scan on {target_subnet} …")

        packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=target_subnet)
        answered, _ = srp(packet, timeout=timeout, verbose=False)

        discovered: List[Dict[str, str]] = []
        for _, rcv in answered:
            ip, mac = rcv.psrc, rcv.hwsrc
            if ip not in self.seen_ips:
                self.seen_ips.add(ip)
                asset = {
                    "ip_address": ip,
                    "mac_address": mac,
                    "discovery_method": "active_arp",
                }
                self.inventory[ip] = asset
                discovered.append(asset)

        logger.info(f"ARP scan complete — {len(discovered)} new devices.")
        return discovered

    # ------------------------------------------------------------------
    # 3. ICMP Sweep (Layer 3)
    # ------------------------------------------------------------------
    def icmp_sweep(
        self, targets: List[str], timeout: int = 1
    ) -> List[Dict[str, str]]:
        """
        Send a single ICMP Echo Request to each target IP.
        Use sparingly on fragile OT segments — one packet per host.

        Args:
            targets:  List of individual IPs to probe.
            timeout:  Seconds to wait for each reply.

        # Satisfies NIST 800-171 3.11.2 (Scanning)
        """
        logger.info(f"ICMP sweep — probing {len(targets)} targets …")
        discovered: List[Dict[str, str]] = []

        for ip in targets:
            if ip in self.seen_ips:
                continue
            pkt = IP(dst=ip) / ICMP()
            reply = sr1(pkt, timeout=timeout, verbose=False)
            if reply is not None:
                self.seen_ips.add(ip)
                asset = {
                    "ip_address": ip,
                    "mac_address": "Unknown",  # ICMP is L3; no MAC in reply
                    "discovery_method": "icmp_sweep",
                }
                self.inventory[ip] = asset
                discovered.append(asset)
                logger.info(f"[ICMP] Alive: {ip}")

        logger.info(f"ICMP sweep complete — {len(discovered)} new devices.")
        return discovered

    # ------------------------------------------------------------------
    # Inventory accessor
    # ------------------------------------------------------------------
    def get_inventory(self) -> Dict[str, Dict[str, str]]:
        """Return the combined inventory from all discovery methods."""
        return self.inventory


if __name__ == "__main__":
    sentinel = SentinelEngine()
    print("Sentinel engine loaded successfully.")
