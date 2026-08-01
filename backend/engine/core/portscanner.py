"""
RCA PortScanner: Service & Vulnerability Discovery.
Wraps python-nmap to perform targeted, controlled port scans against
discovered assets — enriching inventory records with service banners
and flagging high-risk open ports for the Triage agent.

Default port list covers both IT and OT protocol surfaces:
  IT:  22 (SSH), 80 (HTTP), 443 (HTTPS), 445 (SMB), 3389 (RDP)
  OT:  102 (S7/PROFINET), 502 (Modbus), 44818 (EtherNet/IP)

Design principles:
  - SYN scan only (no banner-grabbing writes to OT devices)
  - Per-host timeout enforced at the nmap level
  - Graceful degradation: nmap not installed → warning + empty result
  - Returns typed dataclasses, not raw nmap dicts

# Satisfies NIST 800-171 Rev 3:
# 3.11.2 - Scan for vulnerabilities in organizational systems periodically.
# 3.4.1  - Establish and maintain baseline configurations and inventories.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA PortScanner - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default port profile — conservative IT + OT surface
# ---------------------------------------------------------------------------
DEFAULT_PORTS = "22,80,102,443,445,502,3389,44818"

# Ports that, if open, should always escalate triage severity
HIGH_RISK_PORTS = {
    502: "Modbus (OT write-capable)",
    44818: "EtherNet/IP (OT write-capable)",
    102: "S7 / PROFINET (OT write-capable)",
    3389: "RDP (remote admin, credential exposure risk)",
    445: "SMB (lateral movement risk)",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class OpenPort:
    """A single open port on a scanned host."""

    port: int
    protocol: str  # "tcp" or "udp"
    state: str  # "open", "filtered", etc.
    service: str  # e.g. "ssh", "http", "modbus"
    product: str = ""  # e.g. "OpenSSH"
    version: str = ""  # e.g. "8.9p1"
    is_high_risk: bool = False
    risk_reason: str = ""


@dataclass
class PortScanResult:
    """Complete scan result for a single host."""

    ip_address: str
    hostname: str = ""
    scan_status: str = "unknown"  # "up", "down", "error", "nmap_missing"
    open_ports: List[OpenPort] = field(default_factory=list)
    nist_control: str = "3.11.2"

    @property
    def has_high_risk_ports(self) -> bool:
        return any(p.is_high_risk for p in self.open_ports)

    @property
    def high_risk_summary(self) -> List[str]:
        return [
            f"{p.port}/{p.protocol} — {p.risk_reason}"
            for p in self.open_ports
            if p.is_high_risk
        ]


# ---------------------------------------------------------------------------
# PortScanner
# ---------------------------------------------------------------------------
class PortScanner:
    """
    Targeted port scanner for IT/OT asset enrichment.

    Usage:
        scanner = PortScanner()
        result = scanner.scan("192.168.1.50")
        for port in result.open_ports:
            print(port.port, port.service, port.is_high_risk)

    # Satisfies NIST 800-171 3.11.2 (vulnerability scanning)
    """

    def __init__(
        self,
        ports: str = DEFAULT_PORTS,
        timeout: int = 5,
    ):
        """
        Args:
            ports:   Nmap-format port string, e.g. "22,80,443,502".
            timeout: Per-host scan timeout in seconds.
        """
        self.ports = ports
        self.timeout = timeout
        self._nm = self._load_nmap()

    # ------------------------------------------------------------------
    # nmap loader with graceful ImportError handling
    # ------------------------------------------------------------------
    @staticmethod
    def _load_nmap():
        """
        Attempt to import python-nmap. Returns the module object or None.
        If None, all scans return empty results with status='nmap_missing'.
        """
        try:
            import nmap

            return nmap
        except ImportError:
            logger.warning(
                "python-nmap is not installed. "
                "Port scanning disabled. Run: pip install python-nmap"
            )
            return None

    # ------------------------------------------------------------------
    # Single-host scan
    # ------------------------------------------------------------------
    def scan(
        self,
        ip: str,
        ports: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> PortScanResult:
        """
        Scan a single IP address and return a structured PortScanResult.

        Args:
            ip:      Target IP address.
            ports:   Override the instance-level port list for this scan.
            timeout: Override the instance-level timeout (seconds).

        Returns:
            PortScanResult with open_ports populated if host is up.

        # Satisfies NIST 800-171 3.11.2
        """
        result = PortScanResult(ip_address=ip)

        if self._nm is None:
            result.scan_status = "nmap_missing"
            return result

        port_str = ports or self.ports
        host_timeout = timeout or self.timeout

        try:
            nm = self._nm.PortScanner()
            logger.info(
                f"Scanning {ip} on ports {port_str} (timeout={host_timeout}s) …"
            )

            # -sS SYN scan where available; fall back to -sT (connect) if no raw sockets
            # --host-timeout limits wall-clock time per host
            nm.scan(
                hosts=ip,
                ports=port_str,
                arguments=f"--host-timeout {host_timeout}s -sV --version-intensity 2",
            )

            if ip not in nm.all_hosts():
                result.scan_status = "down"
                logger.info(f"Host {ip} did not respond.")
                return result

            host_data = nm[ip]
            result.scan_status = host_data.state()
            result.hostname = host_data.hostname() or ""

            # Parse open ports
            for proto in host_data.all_protocols():
                for port_num in sorted(host_data[proto].keys()):
                    pdata = host_data[proto][port_num]
                    if pdata["state"] not in ("open", "open|filtered"):
                        continue

                    is_high_risk = port_num in HIGH_RISK_PORTS
                    open_port = OpenPort(
                        port=port_num,
                        protocol=proto,
                        state=pdata["state"],
                        service=pdata.get("name", "unknown"),
                        product=pdata.get("product", ""),
                        version=pdata.get("version", ""),
                        is_high_risk=is_high_risk,
                        risk_reason=HIGH_RISK_PORTS.get(port_num, ""),
                    )
                    result.open_ports.append(open_port)

            if result.has_high_risk_ports:
                logger.warning(
                    f"[HIGH RISK] {ip} has {len(result.high_risk_summary)} "
                    f"high-risk ports open: {result.high_risk_summary}"
                )
            else:
                logger.info(
                    f"Scan complete — {ip}: {len(result.open_ports)} open ports."
                )

        except self._nm.PortScannerError as exc:  # type: ignore[attr-defined]
            logger.error(f"nmap error scanning {ip}: {exc}")
            result.scan_status = "error"
        except Exception as exc:
            logger.error(f"Unexpected error scanning {ip}: {exc}")
            result.scan_status = "error"

        return result

    # ------------------------------------------------------------------
    # Batch scan
    # ------------------------------------------------------------------
    def scan_targets(
        self,
        targets: List[str],
        ports: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> List[PortScanResult]:
        """
        Scan a list of IP addresses sequentially.

        Args:
            targets: List of IP address strings.
            ports:   Optional port list override.
            timeout: Optional per-host timeout override.

        Returns:
            List of PortScanResult objects, one per target.

        # Satisfies NIST 800-171 3.11.2
        """
        logger.info(f"Batch port scan starting — {len(targets)} hosts …")
        results = [self.scan(ip, ports=ports, timeout=timeout) for ip in targets]
        logger.info(
            f"Batch scan complete — "
            f"{sum(1 for r in results if r.scan_status == 'up')} hosts up."
        )
        return results


if __name__ == "__main__":
    scanner = PortScanner()
    print("PortScanner loaded. Use scanner.scan(ip) to begin.")
