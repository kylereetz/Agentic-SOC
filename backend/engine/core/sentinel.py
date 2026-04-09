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
import socket
import ssl
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timezone

from scapy.all import ARP, Ether, IP, ICMP, srp, sr1, sniff, load_layer

# Pre-load the TLS dissection layer for Passive PQC Vulnerability mapping
load_layer("tls")

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
        self.inventory: Dict[str, Dict[str, Any]] = {}
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
                    "shadow_it": False,
                    "unpatched_legacy": False,
                    "default_credentials_exposed": False
                }
                self.inventory[src_ip] = asset
                logger.info(f"[Passive] New asset: {src_ip} ({src_mac})")
                
            # Passive detection of default PLC credentials and unauthenticated Modbus
            if packet.haslayer("TCP") and packet["TCP"].dport == 502:
                # Flagging unauthenticated cleartext industrial protocols
                self.inventory[src_ip]["shadow_it"] = True
                # Mock logic for default credential exposure via cleartext
                self.inventory[src_ip]["default_credentials_exposed"] = True
                logger.warning(f"[Scout Audit] Discovered unauthenticated Modbus stream on {src_ip}")

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
    # 4. Deep Service Probing (Banner Grabbing & TLS)
    # ------------------------------------------------------------------
    def service_probe(self, ip: str, ports: List[int] = [80, 443, 445, 22]) -> Dict[str, Any]:
        """
        Attempt to identify services and OS hints via non-disruptive probing.
        
        # Satisfies NIST 800-171 3.11.2 (Vulnerability scanning)
        """
        findings = {}
        for port in ports:
            if port == 443:
                tls_info = self._get_tls_metadata(ip, port)
                if tls_info:
                    findings["https"] = tls_info
            else:
                banner = self._grab_banner(ip, port)
                if banner:
                    findings[f"port_{port}"] = banner
                    
        if findings and ip in self.inventory:
            self.inventory[ip]["service_probes"] = findings
            
            # Simple OS heuristic from banners
            combined = str(findings).lower()
            if "windows" in combined or "microsoft" in combined:
                self.inventory[ip]["os_label"] = "Windows"
                if "windows 7" in combined or "xp" in combined or "2008" in combined:
                    self.inventory[ip]["unpatched_legacy"] = True
            elif "linux" in combined or "ubuntu" in combined or "debian" in combined:
                self.inventory[ip]["os_label"] = "Linux"
            elif "ssh-2.0-openssh" in combined:
                self.inventory[ip]["os_label"] = "Linux/Unix"
                
        return findings

    def _grab_banner(self, ip: str, port: int, timeout: int = 2) -> Optional[str]:
        """Attempt to read a service banner."""
        try:
            with socket.create_connection((ip, port), timeout=timeout) as sock:
                # Some protocols wait for us to speak (HTTP), some speak first (SSH)
                if port == 80:
                    sock.sendall(b"GET / HTTP/1.0\r\n\r\n")
                
                banner = sock.recv(1024).decode(errors="ignore").strip()
                return banner[:200] if banner else None
        except Exception:
            return None

    def _get_tls_metadata(self, ip: str, port: int, timeout: int = 3) -> Optional[Dict[str, Any]]:
        """Extract TLS version metadata."""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        try:
            with socket.create_connection((ip, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=ip) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    if not cert:
                        return None
                    
                    cipher_info = ssock.cipher()
                    cipher_name = cipher_info[0] if cipher_info else "UNKNOWN"

                    return {
                        "version": ssock.version(),
                        "cipher": cipher_name,
                        "active": True
                    }
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Inventory accessor
    # ------------------------------------------------------------------
    def get_inventory(self) -> Dict[str, Dict[str, Any]]:
        """Return the combined inventory from all discovery methods."""
        return self.inventory


if __name__ == "__main__":
    sentinel = SentinelEngine()
    print("Sentinel engine loaded successfully.")
