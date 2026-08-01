"""
RCA Forensics Agent: The Evidence Collector.

Simulates the collection of forensic artifacts from target hosts during
an investigation. It creates realistic-looking data structures for the
'Evidence Inspector' UI component.

Artifact Types:
  - REGISTRY: Snapshots of suspicious registry keys (Run keys, etc.)
  - MEMORY: Simulated process memory metadata (Reflective injections)
  - PCAP: Small fragments of network traffic (encoded protocols)
  - LOGS: Host-specific event logs (Powershell, Security)

# Satisfies NIST 800-171 Rev 3:
# 3.3.1 - Create and retain system audit logs and records.
# 3.6.1 - Establish an operational incident-handling capability.
"""

import hashlib
import json
import logging
import os
import random
import zlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Forensics - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
FORENSICS_ROOT = get_soc_path("reports", "forensics")


# ---------------------------------------------------------------------------
# Forensics Agent
# ---------------------------------------------------------------------------
class ForensicsAgent:
    """
    Collects and stores simulated forensic evidence.
    """

    def __init__(self):
        os.makedirs(FORENSICS_ROOT, exist_ok=True)
        self.is_running = False

        # [IQ] Doctrine Reference: QUILL-FORENSICS
        from soc.bootstrap import get_soc_path

        logger.info(
            f"Synchronized with doctrine: {get_soc_path('ethos', 'ethos_quill_forensics.md')}"
        )
        self.coc_file = os.path.join(FORENSICS_ROOT, "chain_of_custody.json")
        self.raw_alerts_bus = EventBus("raw_alerts")
        self._init_coc()

    def _init_coc(self):
        """Initialise the global Chain of Custody log if not present."""
        if not os.path.exists(self.coc_file):
            header = {
                "document_title": "Enterprise Chain of Custody Log",
                "compliance": "NIST 800-171 Rev 3 (3.3.1, 3.6.1)",
                "organisation": "Reetz Cyber Automation",
                "events": [],
            }
            with open(self.coc_file, "w") as f:
                json.dump(header, f, indent=2)

    def _log_coc_event(
        self,
        event_type: str,
        evidence_id: str,
        case_id: str,
        target: str,
        collector: str = "FORENSICS-01",
    ):
        """Append an entry to the Chain of Custody."""
        try:
            with open(self.coc_file, "r") as f:
                coc = json.load(f)

            coc["events"].append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": event_type,
                    "evidence_id": evidence_id,
                    "case_id": case_id,
                    "target": target,
                    "actor": collector,
                    "status": "SECURED",
                }
            )

            with open(self.coc_file, "w") as f:
                json.dump(coc, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to log CoC event: {e}")

    def collect_evidence(
        self, case_id: str, target_ip: str, artifact_type: str
    ) -> Dict[str, Any]:
        """
        Produce a high-integrity forensic artifact with shellcode detection and paging.
        """
        case_dir = os.path.join(FORENSICS_ROOT, case_id)
        os.makedirs(case_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{artifact_type}_{timestamp}.json"
        path = os.path.join(case_dir, filename)

        raw_data = self._generate_simulated_data(artifact_type, target_ip)
        payload_str = json.dumps(raw_data)

        # [IQ] Pattern Matching: Auto-flag known shellcode headers
        patterns = []
        if artifact_type == "MEMORY":
            if "reflective_load" in payload_str or "0x90" in payload_str:
                patterns.append(
                    {
                        "header": "SHELLCODE_STUB",
                        "offset": "0x00000450",
                        "risk": "CRITICAL",
                    }
                )
            if "MZ" in payload_str or "svchost" in payload_str:
                patterns.append(
                    {
                        "header": "PE_HEADER_IN_MEM",
                        "offset": "0x00400000",
                        "risk": "HIGH",
                    }
                )

        # [EQ] Integrity Seals: SHA-256 hashing at point of collection
        sha256_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        # [SQ] Paged Collection: Avoid OOM by chunking large records
        # We simulate this by returning data as a list of pages if it's "large"
        pages = []
        chunk_size = 500  # Simulated chunk limit
        if len(payload_str) > chunk_size:
            pages = [
                payload_str[i : i + chunk_size]
                for i in range(0, len(payload_str), chunk_size)
            ]
            storage_mode = "PAGED"
        else:
            pages = [payload_str]
            storage_mode = "SINGLE_PAGE"

        # Summary generation logic
        summary = "Standard forensic collection."
        if patterns:
            summary = f"Potential threat headers found: {', '.join([p['header'] for p in patterns])}."

        evidence_object = {
            "evidence_id": f"EVD_{timestamp}_{random.randint(100, 999)}",
            "case_id": case_id,
            "target_ip": target_ip,
            "artifact_type": artifact_type,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "findings_summary": summary,
            "artifact_path": path,
            "iq_analysis": {
                "pattern_detection": patterns,
                "threat_score": 90 if patterns else 0,
            },
            "eq_integrity": {
                "algorithm": "SHA-256",
                "hash": sha256_hash,
                "seal": "ALIGNED_WITH_NIST_3.14.3",
            },
            "sq_optimization": {
                "storage_mode": storage_mode,
                "page_count": len(pages),
                "total_size_bytes": len(payload_str),
            },
            "data_pages": pages,  # Actual content is now paged
        }

        from soc.network.service_mesh import CloudStorageGateway

        # [IAM-Enforced] Route via Storage Gateway to prove Strict IAM Execution Role
        CloudStorageGateway.put_object(
            client_role="forensics",
            file_path=path,
            data=json.dumps(evidence_object, indent=2),
        )

        # [VQ] Chain of Custody / Evidence Timeline
        self._log_coc_event(
            event_type="COLLECTION",
            evidence_id=evidence_object["evidence_id"],
            case_id=case_id,
            target=target_ip,
        )

        # [IQ] Intel Feed: Push malicious hash to Correlator for linkage
        if patterns:
            self.raw_alerts_bus.push(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "rule_id": "FORENSICS_THREAT_HASH",
                    "rule_name": f"Malicious Artifact: {artifact_type}",
                    "severity": "WARNING",
                    "source_ip": target_ip,
                    "file_hash": sha256_hash,
                    "description": f"Forensic analysis detected threat patterns in {artifact_type}. Linking via hash.",
                }
            )

        logger.info(
            f"COLLECTED {artifact_type} for {case_id} [IQ:{len(patterns)} PATTERNS] [SQ:{storage_mode}]"
        )
        return evidence_object

    def _generate_simulated_data(self, atype: str, ip: str) -> Any:
        """Helper to create realistic mock data."""
        if atype == "REGISTRY":
            return {
                "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run": {
                    "RCA_Update": "C:\\Windows\\Temp\\svchost_update.exe",
                    "OneDrive": "C:\\Users\\admin\\AppData\\Local\\Microsoft\\OneDrive\\OneDrive.exe",
                },
                "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce": {
                    "InstallUpdate": "powershell.exe -ExecutionPolicy Bypass -File C:\\Temp\\s.ps1"
                },
            }
        elif atype == "MEMORY":
            return {
                "pid": 9912,
                "process": "svchost.exe",
                "indicators": [
                    {
                        "type": "reflective_load",
                        "address": "0x00401000",
                        "size": "1.2MB",
                    },
                    {"type": "suspicious_string", "value": "sekurlsa::logonpasswords"},
                    {"type": "beacon_pattern", "interval": "60s"},
                ],
            }
        elif atype == "PCAP":
            return [
                {
                    "timestamp": "10:01:22",
                    "proto": "TCP",
                    "src": ip,
                    "dst": "203.0.113.45",
                    "len": 1024,
                    "flag": "PSH,ACK",
                },
                {
                    "timestamp": "10:02:22",
                    "proto": "TCP",
                    "src": ip,
                    "dst": "203.0.113.45",
                    "len": 128,
                    "flag": "PSH,ACK",
                },
                {
                    "timestamp": "10:03:22",
                    "proto": "TCP",
                    "src": ip,
                    "dst": "203.0.113.45",
                    "len": 512,
                    "flag": "PSH,ACK",
                },
            ]
        else:
            return {
                "detail": f"Raw log fragment from host {ip} collected for manual analysis."
            }


if __name__ == "__main__":
    agent = ForensicsAgent()
    p = agent.collect_evidence("INC-DEBUG-001", "192.168.1.105", "MEMORY")
    print(f"Artifact created: {p}")
