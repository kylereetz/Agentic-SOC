"""
RCA Industrial: "Polite" OT Protocol Discovery Module.
Performs gentle, read-only probes for common industrial protocols:
  - Modbus/TCP  (port 502)
  - EtherNet/IP (port 44818)
  - PROFINET DCP (UDP discovery, port 34964)

Design philosophy:
  - ONE probe per host — never flood.
  - Read-only function codes only (no writes, no resets).
  - Configurable inter-probe delay to avoid overwhelming legacy PLCs.
  - Graceful timeout handling — silence ≠ crash.

Uses raw Scapy for PROFINET DCP and stdlib sockets for Modbus/EtherNet/IP
to keep dependencies minimal and maintain full control over timing.

# Satisfies NIST 800-171 Rev 3:
# 3.4.1  - Establish and maintain baseline configurations and inventories.
# 3.13.1 - Monitor, control, and protect organisational communications.
# 3.14.6 - Monitor organisational systems to detect attacks and indicators
#           of potential attacks.
"""

import logging
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from scapy.all import Ether, IP, UDP, sendp, sniff, conf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Industrial - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODBUS_PORT = 502
ENIP_PORT = 44818
PROFINET_DCP_PORT = 34964

# Modbus Function Code 0x11 = Report Server ID (read-only, safe)
MODBUS_REPORT_SERVER_ID_FC = 0x11

# EtherNet/IP: ListIdentity command (read-only)
ENIP_LIST_IDENTITY_CMD = 0x0063


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class IndustrialAsset:
    """Represents a discovered industrial device."""

    ip_address: str
    protocol: str  # "modbus", "ethernetip", "profinet"
    port: int
    device_info: str = ""  # Protocol-specific identification string
    discovery_method: str = "industrial_probe"


# ---------------------------------------------------------------------------
# Modbus/TCP Probe
# ---------------------------------------------------------------------------
class ModbusProbe:
    """
    Send a single Modbus Report Server ID request (FC 0x11).
    This is the safest read-only function code — it asks the device
    to identify itself without touching any coils or registers.

    # Satisfies NIST 800-171 3.4.1
    """

    @staticmethod
    def probe(ip: str, timeout: float = 2.0) -> Optional[IndustrialAsset]:
        """
        Probe a single IP for Modbus/TCP.
        Returns an IndustrialAsset if the host responds, else None.
        """
        # Build a minimal Modbus/TCP ADU:
        #   Transaction ID (2B) | Protocol ID (2B) | Length (2B) | Unit ID (1B) | FC (1B)
        transaction_id = 0x0001
        protocol_id = 0x0000  # Modbus protocol
        length = 0x0002  # Unit ID + FC
        unit_id = 0x01  # Default unit
        fc = MODBUS_REPORT_SERVER_ID_FC

        request = struct.pack(
            ">HHHBB", transaction_id, protocol_id, length, unit_id, fc
        )

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, MODBUS_PORT))
            sock.sendall(request)
            response = sock.recv(256)
            sock.close()

            if len(response) > 8:
                device_info = response[9:].decode("ascii", errors="replace").strip()
            else:
                device_info = "Modbus device (minimal response)"

            logger.info(f"[Modbus] Device found at {ip}: {device_info}")
            return IndustrialAsset(
                ip_address=ip,
                protocol="modbus",
                port=MODBUS_PORT,
                device_info=device_info,
            )
        except socket.timeout:
            return None
        except ConnectionRefusedError:
            return None
        except Exception as exc:
            logger.debug(f"[Modbus] Probe error on {ip}: {exc}")
            return None


# ---------------------------------------------------------------------------
# EtherNet/IP Probe
# ---------------------------------------------------------------------------
class EtherNetIPProbe:
    """
    Send a ListIdentity command over EtherNet/IP (CIP).
    This is a standard, read-only discovery mechanism supported by
    Allen-Bradley / Rockwell controllers.

    # Satisfies NIST 800-171 3.4.1
    """

    @staticmethod
    def probe(ip: str, timeout: float = 2.0) -> Optional[IndustrialAsset]:
        """Send ListIdentity and parse the product name from the reply."""
        # EtherNet/IP encapsulation header (24 bytes):
        #   Command (2B) | Length (2B) | Session Handle (4B) | Status (4B) |
        #   Sender Context (8B) | Options (4B)
        header = struct.pack(
            "<HH I I 8s I",
            ENIP_LIST_IDENTITY_CMD,  # Command: ListIdentity
            0,  # Data length: 0
            0,  # Session handle
            0,  # Status
            b"\x00" * 8,  # Sender context
            0,  # Options
        )

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, ENIP_PORT))
            sock.sendall(header)
            response = sock.recv(1024)
            sock.close()

            # Attempt to extract the product name from the response payload
            # The product name sits after a variable-length structure
            device_info = "EtherNet/IP device"
            if len(response) > 48:
                # Product name length byte is at offset 47 in typical responses
                try:
                    name_len = response[47]
                    if 0 < name_len < 64:
                        device_info = response[48 : 48 + name_len].decode(
                            "ascii", errors="replace"
                        )
                except (IndexError, ValueError):
                    pass

            logger.info(f"[EtherNet/IP] Device found at {ip}: {device_info}")
            return IndustrialAsset(
                ip_address=ip,
                protocol="ethernetip",
                port=ENIP_PORT,
                device_info=device_info,
            )
        except socket.timeout:
            return None
        except ConnectionRefusedError:
            return None
        except Exception as exc:
            logger.debug(f"[EtherNet/IP] Probe error on {ip}: {exc}")
            return None


# ---------------------------------------------------------------------------
# PROFINET DCP Probe (broadcast discovery)
# ---------------------------------------------------------------------------
class PROFINETProbe:
    """
    Broadcast a PROFINET DCP Identify request on the local segment.
    DCP (Discovery and basic Configuration Protocol) is designed
    specifically for this purpose and is inherently safe.

    NOTE: Must run with raw socket privileges (Administrator / root).

    # Satisfies NIST 800-171 3.4.1
    """

    # PROFINET DCP Ethertype
    PROFINET_ETHERTYPE = 0x8892

    @staticmethod
    def probe(iface: str = None, timeout: float = 3.0) -> List[IndustrialAsset]:
        """
        Send a DCP Identify All broadcast and collect responses.
        Returns a list of discovered PROFINET devices.
        """
        discovered: List[IndustrialAsset] = []

        # DCP Identify All payload (minimal)
        #   ServiceID(1B)=5 (Identify) | ServiceType(1B)=0 (Request) |
        #   Xid(4B) | ResponseDelay(2B) | DCPDataLength(2B) |
        #   Option(1B)=0xFF (All) | SubOption(1B)=0xFF (All) | BlockLength(2B)=0
        dcp_payload = struct.pack(
            ">BB I HH BB H",
            0x05,  # ServiceID: Identify
            0x00,  # ServiceType: Request
            0x00000001,  # Xid (transaction)
            0x0080,  # ResponseDelay factor
            0x0004,  # DCPDataLength
            0xFF,  # Option: All
            0xFF,  # SubOption: All
            0x0000,  # BlockLength
        )

        # Build the raw Ethernet frame
        frame = (
            Ether(dst="01:0e:cf:00:00:00", type=PROFINETProbe.PROFINET_ETHERTYPE)
            / dcp_payload
        )

        try:
            sendp(frame, iface=iface, verbose=False)
            logger.info("[PROFINET] DCP Identify broadcast sent.")

            # Listen for DCP responses
            replies = sniff(
                iface=iface,
                filter=f"ether proto 0x{PROFINETProbe.PROFINET_ETHERTYPE:04x}",
                timeout=timeout,
                count=50,
            )

            for pkt in replies:
                if pkt.haslayer(Ether):
                    src_mac = pkt[Ether].src
                    src_ip = pkt[IP].src if pkt.haslayer(IP) else "N/A"
                    asset = IndustrialAsset(
                        ip_address=src_ip,
                        protocol="profinet",
                        port=PROFINET_DCP_PORT,
                        device_info=f"PROFINET device (MAC: {src_mac})",
                    )
                    discovered.append(asset)
                    logger.info(f"[PROFINET] Discovered: {src_mac} / {src_ip}")

        except Exception as exc:
            logger.error(f"[PROFINET] DCP probe failed: {exc}")

        logger.info(f"[PROFINET] Discovery complete — {len(discovered)} devices.")
        return discovered


# ---------------------------------------------------------------------------
# Unified Industrial Scanner
# ---------------------------------------------------------------------------
class IndustrialScanner:
    """
    Orchestrates polite industrial protocol discovery across a target list.
    Adds a configurable inter-probe delay to prevent overwhelming
    fragile legacy devices.

    # Satisfies NIST 800-171 3.4.1 and 3.14.6
    """

    def __init__(self, inter_probe_delay: float = 0.5):
        """
        Args:
            inter_probe_delay: Seconds to wait between probes. Increase for
                               extremely fragile environments.
        """
        self.delay = inter_probe_delay
        self.discovered: List[IndustrialAsset] = []

    def scan_targets(
        self,
        targets: List[str],
        protocols: Optional[List[str]] = None,
    ) -> List[IndustrialAsset]:
        """
        Probe a list of IPs for industrial protocols.

        Args:
            targets:   List of IP addresses.
            protocols: Subset of ["modbus", "ethernetip"]. Default: both.
                       PROFINET uses broadcast and is run separately.
        """
        if protocols is None:
            protocols = ["modbus", "ethernetip"]

        logger.info(
            f"Industrial scan starting — {len(targets)} hosts, "
            f"protocols: {protocols}, delay: {self.delay}s"
        )

        for ip in targets:
            if "modbus" in protocols:
                result = ModbusProbe.probe(ip)
                if result:
                    self.discovered.append(result)
                time.sleep(self.delay)

            if "ethernetip" in protocols:
                result = EtherNetIPProbe.probe(ip)
                if result:
                    self.discovered.append(result)
                time.sleep(self.delay)

        logger.info(f"Industrial scan complete — {len(self.discovered)} devices found.")
        return self.discovered

    def scan_profinet(self, iface: str = None) -> List[IndustrialAsset]:
        """Run a PROFINET DCP broadcast discovery."""
        results = PROFINETProbe.probe(iface=iface)
        self.discovered.extend(results)
        return results

    def get_all_discovered(self) -> List[IndustrialAsset]:
        """Return all industrially discovered assets."""
        return self.discovered


if __name__ == "__main__":
    scanner = IndustrialScanner()
    print("Industrial scanner loaded successfully.")
