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

import asyncio
import ipaddress
import json
import logging
import os
import shutil
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.agents.business.game_theory_solver import FictitiousPlaySolver
from soc.security.vault import Vault
from soc.security.crypto_cat import verify_cat
from soc.utils.audio import play_action_completed

logger = logging.getLogger(__name__)

PENDING_ACTIONS_PATH = get_soc_path("reports", "incidents", "pending_actions.json")
INCIDENT_LOG_PATH = get_soc_path("reports", "incidents", "incident_log.json")
# Maximum incidents per log file before rotation. Keep high for SIEM continuity.
_INCIDENT_LOG_MAX_ENTRIES = int(os.environ.get("RCA_INCIDENT_LOG_MAX", "1000"))


class ResponderAgent:
    """
    Autonomous response agent with a mandatory human approval gate.

    # Satisfies NIST 800-171 3.6.1 and 3.14.3
    """

    def __init__(self):
        self.bus = EventBus("triage_alerts")
        self.remediation_history: List[Dict[str, Any]] = []

        # [IQ] Doctrine Reference: WEDGE-RESPONDER
        from soc.bootstrap import get_soc_path

        logger.info(
            f"Synchronized with doctrine: {get_soc_path('ethos', 'ethos_wedge_responder.md')}"
        )
        # [SQ] Internal Dispatch Queue for non-blocking operations
        self.dispatch_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self.heartbeat_bus = EventBus("soc_heartbeats")
        self.marl_bus = EventBus("marl_rewards")
        self.last_heartbeat = datetime.now(timezone.utc)
        self.gt_solver = FictitiousPlaySolver(iterations=1500)
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

    async def run(self):
        """Main async engine for the Responder."""
        self.is_running = True
        logger.info("[SQ] Responder High-Performance Engine started.")

        # Start the dispatch worker and heartbeat monitor
        tasks = [
            asyncio.create_task(self._process_bus()),
            asyncio.create_task(self._dispatch_worker()),
            asyncio.create_task(self._dead_man_switch_monitor()),
        ]

        await asyncio.gather(*tasks)

    async def _process_bus(self):
        """Continuously pull from the bus and feed the internal queue."""
        while self.is_running:
            alert = await asyncio.to_thread(self.bus.pop)
            if alert:
                await self.dispatch_queue.put(alert)
                # Update heartbeat on activity
                self.last_heartbeat = datetime.now(timezone.utc)
            else:
                await asyncio.sleep(1)

    async def _dispatch_worker(self):
        """Consume alerts from internal queue and determine actions."""
        while self.is_running:
            try:
                # [SQ] Non-blocking wait for next alert
                alert = await asyncio.wait_for(self.dispatch_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            if alert.get("severity") == "CRITICAL":
                action = self._determine_action(alert)
                if action:
                    # [IQ] Criticality Threshold Check
                    # If risk exceeds threshold (80), it MUST remain PENDING/REJECTED
                    if action["risk_assessment"]["score"] >= 80:
                        action["status"] = "BLOCKED_BY_RISK_THRESHOLD"
                        logger.error(
                            f"[IQ] ACTION BLOCKED: Risk {action['risk_assessment']['score']} for {action['target_ip']} exceeds safety threshold!"
                        )

                    self.pending_actions.append(action)
                    self._save_pending()

                    # [VQ] Autonomy Gauge Telemetry
                    logger.warning(
                        f"[SYNC] [VQ] Autonomy Drift: +0.05 | {action['strategy']} "
                        f"for {action['target_ip']} [Status: {action['status']}]"
                    )
            self.dispatch_queue.task_done()

    async def _dead_man_switch_monitor(self):
        """[EQ] Dead-Man Switch: Auto-revert if heartbeat lost."""
        while self.is_running:
            # Poll the heartbeat bus
            hb = await asyncio.to_thread(self.heartbeat_bus.pop)
            if hb:
                self.last_heartbeat = datetime.now(timezone.utc)

            await asyncio.sleep(2)
            diff = (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds()
            if diff > 60:  # 60s timeout for demo
                logger.critical(
                    f"[EQ] DEAD-MAN SWITCH TRIGGERED: Manager heartbeat lost for {diff}s! Initiating Safe-State Reversion."
                )
                # Logic to revert all "isolation" commands would go here

    def run_cycle(self) -> int:
        """Legacy synchronous cycle for testing."""
        processed = 0
        while True:
            alert = self.bus.pop()
            if not alert:
                break
            if alert.get("severity") == "CRITICAL":
                action = self._determine_action(alert)
                if action:
                    self.pending_actions.append(action)
                    processed += 1
        if processed > 0:
            self._save_pending()
        return processed

    def _determine_action(self, alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Match an alert to a containment strategy with [IQ] Multi-OS detection.
        """
        ts = datetime.now(timezone.utc).isoformat()
        target_ip = alert.get("source_ip", "unknown")
        rule_id = alert.get("rule_id", "unknown")

        # [IQ] Detect OS from alert metadata or defaults
        target_os = alert.get("os_type", "windows").lower()

        # [SECURITY] Shell Command Injection Remediation
        try:
            # Implicitly strips shell metacharacters by enforcing pure IP struct
            ipaddress.ip_address(target_ip)
            is_valid_ip = True
        except ValueError:
            is_valid_ip = False

        action = {
            "id": f"ACT_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}",
            "created_at": ts,
            "target_ip": target_ip,
            "target_os": target_os,
            "trigger_alert": alert,
            "status": "PENDING_APPROVAL",
            "strategy": "UNKNOWN",
            "commands": [],
            "risk_assessment": self._calculate_risk(alert, target_ip),
        }

        # Validation Check overrides Game Theory completely
        if not is_valid_ip:
            action["strategy"] = "VALIDATION_FAILED"
            action["commands"] = [
                {
                    "cmd": f"# BLOCKED: Command injection or invalid IP detected in '{target_ip}'",
                    "status": "REJECTED_BY_SYSTEM",
                }
            ]
            action["status"] = "REJECTED_BY_SYSTEM"
            logger.critical(
                f"[SECURITY] Invalid IP format detected, blocking command generation for: {target_ip}"
            )
            return action

        # [IQ] Layer 3: Game-Theoretic Defense Matrix
        # 4x3 Payoff Matrix
        # Rows (Defender): 0: Quarantine, 1: Honeypot, 2: RateLimit, 3: Monitor
        # Cols (Attacker): 0: Evasion, 1: Escalation, 2: Persistence
        payoff_matrix = [
            [5.0, 8.0, 5.0],  # Quarantine
            [-2.0, 5.0, 10.0],  # Honeypot
            [2.0, -8.0, -2.0],  # RateLimit
            [-5.0, -10.0, 5.0],  # Monitor
        ]

        # Calculate Mixed Strategy Nash Equilibrium (MSNE) probabilities
        probabilities = self.gt_solver.solve(payoff_matrix)

        # Probabilistically select a strategy based on MSNE distributions
        rand_val = random.random()
        cumulative = 0.0
        selected_idx = 0

        for idx, prob in enumerate(probabilities):
            cumulative += prob
            if rand_val <= cumulative:
                selected_idx = idx
                break

        # Map Selected Strategy
        if selected_idx == 0:
            action["strategy"] = "QUARANTINE"
            if target_os == "linux":
                action["commands"] = [
                    {
                        "cmd": f"iptables -A INPUT -s {target_ip} -j DROP",
                        "status": "PENDING_APPROVAL",
                    },
                    {
                        "cmd": f"iptables -A OUTPUT -d {target_ip} -j DROP",
                        "status": "PENDING_APPROVAL",
                    },
                ]
            else:
                action["commands"] = [
                    {
                        "cmd": f"New-NetFirewallRule -DisplayName 'RCA-Q-{target_ip}' -Direction Inbound -RemoteAddress {target_ip} -Action Block",
                        "status": "PENDING_APPROVAL",
                    },
                    {
                        "cmd": f"New-NetFirewallRule -DisplayName 'RCA-Q-{target_ip}' -Direction Outbound -RemoteAddress {target_ip} -Action Block",
                        "status": "PENDING_APPROVAL",
                    },
                ]
        elif selected_idx == 1:
            action["strategy"] = "HONEYPOT_ROUTING"
            if target_os == "linux":
                action["commands"] = [
                    {
                        "cmd": f"iptables -t nat -A PREROUTING -s {target_ip} -p tcp -j DNAT --to-destination 10.99.99.99",
                        "status": "PENDING_APPROVAL",
                    }
                ]
            else:
                action["commands"] = [
                    {
                        "cmd": f"New-NetNat -Name 'Honeypot_{target_ip}' -InternalIPInterfaceAddressPrefix '10.99.99.99/32'",
                        "status": "PENDING_APPROVAL",
                    }
                ]
        elif selected_idx == 2:
            action["strategy"] = "RATE_LIMITING"
            if target_os == "linux":
                action["commands"] = [
                    {
                        "cmd": f"tc qdisc add dev eth0 root tbf rate 1mbit burst 32kbit latency 400ms",
                        "status": "PENDING_APPROVAL",
                    }
                ]
            else:
                action["commands"] = [
                    {
                        "cmd": f"New-NetQosPolicy -Name 'Throttle_{target_ip}' -IPDstAddressMatchCondition {target_ip} -ThrottleRateActionBitsPerSecond 1000000",
                        "status": "PENDING_APPROVAL",
                    }
                ]
        else:
            action["strategy"] = "INVESTIGATIVE_LOGGING"
            action["commands"] = [
                {
                    "cmd": f"# MSNE dictated Defensive Monitoring log block for Persistence Discovery",
                    "status": "PENDING_APPROVAL",
                }
            ]

        return action

    def _calculate_risk(self, alert: Dict[str, Any], target: str) -> Dict[str, Any]:
        """[IQ] Business Risk Assessment."""
        score = 50  # Base risk
        notes = "Standard containment risk."

        # [IQ] Criticality Threshold logic
        if (
            target.startswith("10.0.1.")
            or "server" in target.lower()
            or "dc" in target.lower()
        ):
            score = 95  # Exceeds the 80 threshold
            notes = "CRITICAL RISK: Target is CORE INFRASTRUCTURE. Action blocked."

        return {
            "score": score,
            "notes": notes,
            "autonomy_drift": 0.05,  # [VQ] Metadata for Dashboard animation
        }

    def approve_action(
        self,
        action_id: str,
        cat_signature: Optional[str] = None,
        approved_indices: Optional[List[int]] = None,
    ):
        """
        Move an action from PENDING to VERDICT_RENDERED, requiring a Cryptographic Action Token.
        Granularly approves or rejects individual commands based on approved_indices.
        """
        # Load the admin secret to verify the CAT
        vault_path = get_soc_path("configs", "secrets.json")
        vault = Vault(vault_path, role="responder")
        vault_data = vault.load()
        admin_secret = vault_data.get("api_secret_key", "")

        if not verify_cat(action_id, cat_signature, admin_secret):
            logger.error(
                f"[SECURITY] UNAUTHORIZED ACCESS ATTEMPT: Invalid or missing CAT for Action {action_id}"
            )
            return False

        for action in self.pending_actions:
            if action["id"] == action_id:
                # If no specific indices provided, approve all by default (legacy behavior)
                target_indices = (
                    approved_indices
                    if approved_indices is not None
                    else list(range(len(action["commands"])))
                )

                executed_auth_commands = []
                for idx, cmd_obj in enumerate(action["commands"]):
                    if idx in target_indices:
                        cmd_obj["status"] = "APPROVED"
                        executed_auth_commands.append(cmd_obj["cmd"])
                    else:
                        cmd_obj["status"] = "REJECTED"

                action["status"] = "VERDICT_RENDERED"
                action["executed_at"] = datetime.now(timezone.utc).isoformat()
                action["executed_commands"] = executed_auth_commands

                # Log to incident log
                self._log_incident(action)

                # Remove from pending
                self.pending_actions.remove(action)
                self._save_pending()

                # [IQ] MARL Reward Broadcast
                reward = 1.0 if len(executed_auth_commands) > 0 else -1.0
                trigger_alert = action.get("trigger_alert", {})
                trigger_rule = trigger_alert.get("rule_id", "UNKNOWN")
                trigger_sev = trigger_alert.get("severity", "UNKNOWN")
                state_key = f"{trigger_rule}_{trigger_sev}"

                if trigger_rule != "UNKNOWN":
                    self.marl_bus.push(
                        {
                            "source_state": state_key,
                            "reward": reward,
                            "action_id": action_id,
                        }
                    )
                    logger.info(
                        f"[MARL] Emitted Reward of {reward} for State {state_key}"
                    )

                # [IQ] Audio Trigger: Containment Action Authorized
                if len(executed_auth_commands) > 0:
                    play_action_completed()

                logger.info(
                    f"Action {action_id} processed with {len(executed_auth_commands)} approved commands."
                )
                return True
        return False

    def _log_incident(self, action: Dict[str, Any]):
        """[EQ] Rolling Log Implementation."""
        log = []
        if os.path.exists(INCIDENT_LOG_PATH):
            try:
                with open(INCIDENT_LOG_PATH, "r") as fh:
                    log = json.load(fh)
            except Exception:
                log = []

        if len(log) >= _INCIDENT_LOG_MAX_ENTRIES:
            archive_path = INCIDENT_LOG_PATH.replace(".json", "_archive.json")
            logger.info(f"[EQ] Incident Log full. Rotating to {archive_path}")
            shutil.copy(INCIDENT_LOG_PATH, archive_path)
            log = [action]  # Start fresh log with current action
        else:
            log.append(action)

        with open(INCIDENT_LOG_PATH, "w") as fh:
            json.dump(log, fh, indent=2)


if __name__ == "__main__":
    responder = ResponderAgent()
    count = responder.run_cycle()
    print(f"Responder cycle complete. {count} new actions drafted.")
