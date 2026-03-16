"""
RCA Triage Agent: IT Noise vs. OT Threat Classifier.
Ingests events from the Scout agent (inventory diffs) and raw packet
metadata, then applies a deterministic rule engine to classify each
event as:
  - INFO     (benign IT noise)
  - WARNING  (suspicious, needs investigation)
  - CRITICAL (likely malicious OT activity)

Rules are loaded from triage_rules.json so clients can tune
thresholds without modifying code.

# Satisfies NIST 800-171 Rev 3:
# 3.14.6 - Monitor organisational systems to detect attacks.
# 3.14.3 - Monitor system security alerts and take action in response.
# 3.6.1  - Establish an operational incident-handling capability.
# 3.3.5  - Correlate audit record review for investigation and response.
"""

import ipaddress
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Triage - %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_RULES_PATH = get_soc_path("configs", "triage_rules.json")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class TriageAlert:
    """A single classified alert."""
    timestamp: str
    rule_id: str
    rule_name: str
    severity: str           # INFO, WARNING, CRITICAL
    classification: str     # benign, suspicious, malicious
    source_ip: str
    description: str
    nist_control: str
    raw_event: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # 0.0–1.0


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------
class TriageEngine:
    """
    Deterministic rule engine that evaluates Scout events against
    configurable JSON rules.

    # Satisfies NIST 800-171 3.14.6 and 3.14.3
    """

    def __init__(self, rules_path: str = DEFAULT_RULES_PATH):
        self.rules: List[Dict[str, Any]] = []
        self.whitelisted_sources: List[str] = []
        self.ot_subnets: List[str] = []
        self.printer_prefixes: List[str] = []
        self._load_rules(rules_path)

    def _load_rules(self, path: str) -> None:
        """Load triage rules from JSON config."""
        try:
            with open(path, "r") as fh:
                data = json.load(fh)
                self.rules = data.get("rules", [])
                self.whitelisted_sources = data.get("whitelisted_sources", [])
                self.ot_subnets = data.get("ot_subnets", [])
                self.printer_prefixes = data.get("printer_mac_prefixes", [])
                logger.info(
                    f"Loaded {len(self.rules)} triage rules from {path}"
                )
        except FileNotFoundError:
            logger.error(f"Triage rules not found: {path}")
        except Exception as exc:
            logger.error(f"Failed to load triage rules: {exc}")

    # ------------------------------------------------------------------
    # IP / MAC helpers
    # ------------------------------------------------------------------
    def _is_ot_subnet(self, ip: str) -> bool:
        """Check if an IP falls within a configured OT subnet."""
        try:
            addr = ipaddress.ip_address(ip)
            return any(
                addr in ipaddress.ip_network(subnet, strict=False)
                for subnet in self.ot_subnets
            )
        except ValueError:
            return False

    def _is_printer_mac(self, mac: str) -> bool:
        """Check if a MAC address matches a known printer OUI prefix."""
        if not mac:
            return False
        mac_upper = mac.upper().replace("-", ":")
        return any(
            mac_upper.startswith(prefix.upper())
            for prefix in self.printer_prefixes
        )

    def _is_whitelisted(self, ip: str) -> bool:
        """Check if a source IP is whitelisted."""
        return ip in self.whitelisted_sources

    # ------------------------------------------------------------------
    # Core classification
    # ------------------------------------------------------------------
    def classify_event(self, event: Dict[str, Any]) -> Optional[TriageAlert]:
        """
        Evaluate a single event against all loaded rules.
        Returns the highest-severity matching alert, or None if no rule matches.

        # Satisfies NIST 800-171 3.14.6
        """
        best_match: Optional[TriageAlert] = None
        severity_order = {"INFO": 0, "WARNING": 1, "CRITICAL": 2}

        for rule in self.rules:
            pattern = rule.get("pattern", {})
            matched = True

            # Match by event_type
            if "event_type" in pattern:
                if event.get("event_type") != pattern["event_type"]:
                    matched = False

            # Match by MAC prefix (e.g. printer detection)
            if "mac_prefix" in pattern and matched:
                mac = event.get("mac", "")
                if not any(
                    mac.upper().startswith(p.upper())
                    for p in pattern["mac_prefix"]
                ):
                    matched = False

            # Match by subnet
            if "subnet_match" in pattern and matched:
                ip = event.get("ip", "")
                try:
                    addr = ipaddress.ip_address(ip)
                    if not any(
                        addr in ipaddress.ip_network(s, strict=False)
                        for s in pattern["subnet_match"]
                    ):
                        matched = False
                except ValueError:
                    matched = False

            # Match by protocol
            if "protocol" in pattern and matched:
                if event.get("protocol") != pattern["protocol"]:
                    matched = False

            # Match by function codes (Modbus)
            if "function_codes" in pattern and matched:
                fc = event.get("function_code")
                if fc not in pattern["function_codes"]:
                    matched = False

            # Match by whitelisted source
            if "source_whitelisted" in pattern and matched:
                ip = event.get("ip", "")
                is_wl = self._is_whitelisted(ip)
                if pattern["source_whitelisted"] != is_wl:
                    matched = False

            if matched:
                alert = TriageAlert(
                    timestamp=event.get(
                        "timestamp", datetime.utcnow().isoformat()
                    ),
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    severity=rule["severity"],
                    classification=rule["classification"],
                    source_ip=event.get("ip", "Unknown"),
                    description=rule["description"],
                    nist_control=rule.get("nist_control", ""),
                    raw_event=event,
                )
                # Keep the highest severity match
                if best_match is None or severity_order.get(
                    alert.severity, 0
                ) > severity_order.get(best_match.severity, 0):
                    best_match = alert

        return best_match


# ---------------------------------------------------------------------------
# Triage Agent (Bus-based I/O)
# ---------------------------------------------------------------------------
class TriageAgent:
    """
    Consumes events from the 'discovery_events' Bus channel and
    pushes classified alerts to the 'triage_alerts' Bus channel.

    # Satisfies NIST 800-171 3.6.1 (Incident handling)
    """

    def __init__(self, rules_path: str = DEFAULT_RULES_PATH):
        self.engine = TriageEngine(rules_path)
        self.in_bus = EventBus("discovery_events")
        self.out_bus = EventBus("triage_alerts")
        self.report_path = get_soc_path("reports", "triage", "triage_alerts.json")

    def run_cycle(self) -> int:
        """
        Process all pending events on the bus.
        Returns the number of alerts generated.
        """
        processed_count = 0
        all_alerts: List[TriageAlert] = []

        while True:
            event = self.in_bus.pop()
            if not event:
                break
            
            alert = self.engine.classify_event(event)
            if alert:
                all_alerts.append(alert)
                # Push to outbound bus for Responder consumption
                self.out_bus.push(self._serialise_alert(alert))
                logger.info(
                    f"[{alert.severity}] {alert.rule_name} — "
                    f"{alert.source_ip}: {alert.description}"
                )
            
            processed_count += 1

        if all_alerts:
            self._update_persistent_log(all_alerts)
        
        return len(all_alerts)

    def _serialise_alert(self, a: TriageAlert) -> Dict[str, Any]:
        return {
            "timestamp": a.timestamp,
            "rule_id": a.rule_id,
            "rule_name": a.rule_name,
            "severity": a.severity,
            "classification": a.classification,
            "source_ip": a.source_ip,
            "description": a.description,
            "nist_control": a.nist_control,
            "confidence": a.confidence,
        }

    def _update_persistent_log(self, new_alerts: List[TriageAlert]) -> None:
        """Maintain a cumulative JSON log of alerts in soc/reports/triage/."""
        existing = []
        if os.path.exists(self.report_path):
            try:
                with open(self.report_path, "r") as fh:
                    existing = json.load(fh)
            except Exception:
                existing = []

        serialised_new = [self._serialise_alert(a) for a in new_alerts]
        existing.extend(serialised_new)
        
        # Keep only last 1000 alerts
        if len(existing) > 1000:
            # Rebuild list from tail to avoid slice type errors
            keep_start = len(existing) - 1000
            existing = [existing[i] for i in range(keep_start, len(existing))]

        with open(self.report_path, "w") as fh:
            json.dump(existing, fh, indent=2)
        logger.debug(f"Updated triage log at {self.report_path}")

    def summary(self, alerts: List[TriageAlert]) -> Dict[str, int]:
        """Quick count by severity."""
        return {
            "INFO": sum(1 for a in alerts if a.severity == "INFO"),
            "WARNING": sum(1 for a in alerts if a.severity == "WARNING"),
            "CRITICAL": sum(1 for a in alerts if a.severity == "CRITICAL"),
        }


if __name__ == "__main__":
    agent = TriageAgent()
    print("Triage agent loaded. Feed it event files for classification.")
