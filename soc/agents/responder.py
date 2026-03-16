"""
RCA Responder Agent: The Action Arm of the SOC.
Listens for CRITICAL alerts on the 'triage_alerts' Bus channel and
drafts containment actions.

Containment Strategy:
  - New OT Host -> Draft block rule for local firewall
  - Known Vulnerability -> Draft isolation script
  - Critical Protocol Violation -> Draft quarantine policy

# Satisfies NIST 800-171 Rev 3:
# 3.6.1 - Establish an operational incident-handling capability.
# 3.6.2 - Track, document, and report incidents to designated officials.
# 3.14.3 - Monitor system security alerts and take action in response.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Responder - %(message)s",
)
logger = logging.getLogger(__name__)

PENDING_ACTIONS_PATH = get_soc_path("reports", "incidents", "pending_actions.json")
INCIDENT_LOG_PATH = get_soc_path("reports", "incidents", "incident_log.json")


class ResponderAgent:
    """
    Autonomous response agent with a mandatory human approval gate.
    
    # Satisfies NIST 800-171 3.6.1 and 3.14.3
    """

    def __init__(self):
        self.bus = EventBus("triage_alerts")
        self.pending_actions: List[Dict[str, Any]] = []
        self._load_pending()

    def _load_pending(self):
        """Load any existing pending actions from disk."""
        if os.path.exists(PENDING_ACTIONS_PATH):
            try:
                with open(PENDING_ACTIONS_PATH, "r") as fh:
                    self.pending_actions = json.load(fh)
            except Exception:
                self.pending_actions = []

    def _save_pending(self):
        """Save pending actions to disk for human review."""
        with open(PENDING_ACTIONS_PATH, "w") as fh:
            json.dump(self.pending_actions, fh, indent=2)

    def run_cycle(self) -> int:
        """
        Pop alerts from the bus and generate response drafts.
        Only processes CRITICAL alerts for now.
        """
        processed_count = 0
        new_actions = 0

        while True:
            alert = self.bus.pop()
            if not alert:
                break
            
            processed_count += 1
            
            # We only respond to CRITICAL alerts automatically
            if alert.get("severity") == "CRITICAL":
                action = self._determine_action(alert)
                if action:
                    self.pending_actions.append(action)
                    new_actions += 1
                    logger.warning(
                        f"CRITICAL Alert -> Action Drafted: {action['strategy']} "
                        f"for {action['target_ip']}"
                    )

        if new_actions > 0:
            self._save_pending()
        
        return new_actions

    def _determine_action(self, alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Match an alert to a containment strategy.
        Returns a draft action dictionary.
        """
        ts = datetime.utcnow().isoformat()
        target_ip = alert.get("source_ip", "unknown")
        rule_id = alert.get("rule_id", "unknown")
        
        action = {
            "id": f"ACT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            "created_at": ts,
            "target_ip": target_ip,
            "trigger_alert": alert,
            "status": "PENDING_APPROVAL",
            "strategy": "UNKNOWN",
            "commands": []
        }

        # Strategy 1: New OT device (Rule 101/102 in triage_rules)
        if "ot_device" in rule_id.lower() or "modbus" in rule_id.lower():
            action["strategy"] = "QUARANTINE_NEW_OT"
            action["commands"] = [
                f"# Windows Firewall: Block all from {target_ip}",
                f"New-NetFirewallRule -DisplayName 'RCA-Quarantine-{target_ip}' -Direction Inbound -RemoteAddress {target_ip} -Action Block",
                f"New-NetFirewallRule -DisplayName 'RCA-Quarantine-{target_ip}' -Direction Outbound -RemoteAddress {target_ip} -Action Block"
            ]
        
        # Strategy 2: Lateral Movement / Unauthorized Scan
        elif "scan" in rule_id.lower():
            action["strategy"] = "SCAN_ISOLATION"
            action["commands"] = [
                f"# Isolate scanning host {target_ip}",
                f"route add {target_ip} mask 255.255.255.255 127.0.0.1"
            ]
            
        else:
            # Default generic investigation if we don't have a specific strategy
            action["strategy"] = "INVESTIGATIVE_LOGGING"
            action["commands"] = [
                f"# No auto-remediation for rule {rule_id}. Increase logging for {target_ip}."
            ]

        return action

    def approve_action(self, action_id: str):
        """
        Move an action from PENDING to EXECUTED.
        In this MVP, we just log it as approved.
        """
        for action in self.pending_actions:
            if action["id"] == action_id:
                action["status"] = "APPROVED"
                action["executed_at"] = datetime.utcnow().isoformat()
                
                # Log to incident log
                self._log_incident(action)
                
                # Remove from pending
                self.pending_actions.remove(action)
                self._save_pending()
                logger.info(f"Action {action_id} APPROVED and archived.")
                return True
        return False

    def _log_incident(self, action: Dict[str, Any]):
        """Persist executed/approved actions to the permanent log."""
        log = []
        if os.path.exists(INCIDENT_LOG_PATH):
            try:
                with open(INCIDENT_LOG_PATH, "r") as fh:
                    log = json.load(fh)
            except Exception:
                log = []
        
        log.append(action)
        with open(INCIDENT_LOG_PATH, "w") as fh:
            json.dump(log, fh, indent=2)


if __name__ == "__main__":
    responder = ResponderAgent()
    count = responder.run_cycle()
    print(f"Responder cycle complete. {count} new actions drafted.")
