"""
SENTINEL-GATEKEEPER: Identity & Zero Trust Specialist.
Enforces Identity-based security and manages non-human identities (NHI).

IQ Capabilities:
- Detect MFA Fatigue (failed login threshold).
- Detect Impossible Travel (geographic speed correlation).
- NHI Governance (Automated agent key rotation).

# Satisfies NIST 800-171 Rev 3:
# 3.1.1 - Limit system access to authorized users.
# 3.5.1 - Identify and authenticate system users.
# 3.5.10 - Store and transmit only encrypted representation of passwords.
"""

import asyncio
import json
import logging
import os
import secrets
import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logger = logging.getLogger("RCA-Gatekeeper")
# Ensure it shows up even if basicConfig was called elsewhere
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA Gatekeeper - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

GATEKEEPER_RULES_PATH = get_soc_path("configs", "gatekeeper_rules.json")
SECRETS_PATH = get_soc_path("configs", "secrets.json")

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in km between two points."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class GatekeeperAgent:
    """
    Guardian of Identity. Detects account compromise and rotates machine IDs.
    """
    def __init__(self, rules_path: str = GATEKEEPER_RULES_PATH):
        self.in_bus = EventBus("identity_events")
        self.triage_bus = EventBus("triage_alerts")
        self.rules = self._load_rules(rules_path)
        self.user_states: Dict[str, Dict[str, Any]] = {} # user_id -> state
        self.is_running = False

    def _load_rules(self, path: str) -> List[Dict[str, Any]]:
        try:
            with open(path, "r") as f:
                return json.load(f).get("rules", [])
        except Exception as e:
            logger.error(f"Failed to load Gatekeeper rules: {e}")
            return []

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Gatekeeper Identity Specialist started.")
        
        while self.is_running:
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                await self._process_identity_event(event)
            else:
                await asyncio.sleep(0.5)

    async def _process_identity_event(self, event: Dict[str, Any]):
        user_id = event.get("user_id")
        event_type = event.get("event_type")
        if not user_id: return

        # Get/Initialize state
        state = self.user_states.get(user_id, {
            "last_login": None,
            "mfa_fails": [],
            "last_loc": None
        })

        # --- 1. Detect MFA Fatigue ---
        if event_type == "mfa_failure":
            now = time.time()
            state["mfa_fails"] = [f for f in state["mfa_fails"] if now - f < 60]
            state["mfa_fails"].append(now)
            
            rule = next((r for r in self.rules if r["id"] == "GK_MFA_001"), None)
            if rule and len(state["mfa_fails"]) >= rule["threshold"]:
                await self._alert_identity_threat(user_id, rule, event)
                state["mfa_fails"] = [] # Reset after alert

        # --- 2. Detect Impossible Travel ---
        loc = event.get("location")
        if loc and state["last_loc"] and state["last_login"]:
            dist = haversine(
                state["last_loc"]["lat"], state["last_loc"]["lon"],
                loc["lat"], loc["lon"]
            )
            time_diff = (datetime.fromisoformat(event["timestamp"]) - 
                         datetime.fromisoformat(state["last_login"])).total_seconds() / 3600.0
            
            if time_diff > 0:
                speed = dist / time_diff
                rule = next((r for r in self.rules if r["id"] == "GK_TRAV_001"), None)
                if rule and speed > rule["min_speed_kmh"]:
                    await self._alert_identity_threat(user_id, rule, event, 
                        detail=f"Speed: {speed:.2f} km/h over {dist:.2f} km")

        # Update state
        if event_type in ["login_success", "mfa_success"]:
            state["last_login"] = event["timestamp"]
            state["last_loc"] = loc
            state["mfa_fails"] = []

        self.user_states[user_id] = state

    async def _alert_identity_threat(self, user_id: str, rule: Dict[str, Any], event: Dict[str, Any], detail: str = ""):
        logger.warning(f"[IQ] Identity Threat Detected for {user_id}: {rule['name']}")
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "severity": rule["severity"],
            "source_ip": event.get("source_ip", "Unknown"),
            "description": f"{rule['description']} (User: {user_id}) {detail}",
            "nist_control": "3.5.1",
            "mitre_ttp": "T1621", # Multi-Factor Authentication Request Generation
            "raw_event": event
        }
        self.triage_bus.push(alert)

    async def rotate_identities(self):
        """[EQ] Governance: Rotate NHI keys for all agents."""
        logger.info("[EQ] Triggering Non-Human Identity (NHI) rotation...")
        try:
            with open(SECRETS_PATH, "r") as f:
                secrets_data = json.load(f)
            
            for agent, data in secrets_data.get("agents", {}).items():
                new_key = f"sk-{agent.lower()}-{secrets.token_hex(8)}"
                data["api_key"] = new_key
                data["last_rotated"] = datetime.now(timezone.utc).isoformat()
            
            with open(SECRETS_PATH, "w") as f:
                json.dump(secrets_data, f, indent=2)
            
            logger.info("[EQ] All agent identities rotated successfully.")
        except Exception as e:
            logger.error(f"Identity rotation failed: {e}")

if __name__ == "__main__":
    import time
    gk = GatekeeperAgent()
    asyncio.run(gk.run())
