"""
QUILL-VANGUARD: Supply Chain & Vendor Risk Specialist.
Monitors external ecosystem risks and software dependencies.

IQ Capabilities:
- SBOM Analysis (Zero-day library mapping).
- BEC/Impersonation Detection (Vendor communication patterns).

# Satisfies NIST 800-171 Rev 3:
# 3.14.6 - Monitor organizational systems to detect attacks.
# 3.14.3 - Monitor system security alerts and take action.
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logger = logging.getLogger("RCA-Vanguard")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - RCA Vanguard - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

VANGUARD_RULES_PATH = get_soc_path("configs", "vanguard_rules.json")


class VanguardAgent:
    """
    Watchtower for external risks. Analyzes SBOMs and external communications.
    """

    def __init__(self, rules_path: str = VANGUARD_RULES_PATH):
        self.in_bus = EventBus("vanguard_events")
        self.triage_bus = EventBus("triage_alerts")
        self.rules = self._load_rules(rules_path)
        self.is_running = False

    def _load_rules(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Vanguard rules: {e}")
            return {"supply_chain_rules": [], "vendor_risk_rules": []}

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Vanguard Supply Chain Specialist started.")

        while self.is_running:
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                await self._process_vanguard_event(event)
            else:
                await asyncio.sleep(0.5)

    async def _process_vanguard_event(self, event: Dict[str, Any]):
        event_type = event.get("event_type")

        if event_type == "sbom_ingestion":
            await self._analyze_sbom(event)
        elif event_type == "external_comm":
            await self._analyze_vendor_risk(event)

    async def _analyze_sbom(self, event: Dict[str, Any]):
        """[IQ] SBOM Analysis: Flag vulnerable libraries."""
        components = event.get("components", [])
        asset_id = event.get("asset_id", "Unknown Asset")

        supply_rules = self.rules.get("supply_chain_rules", [])
        for rule in supply_rules:
            cve_map = rule.get("cve_mapping", {})
            for comp in components:
                name = comp.get("name")
                version = comp.get("version")

                if name in cve_map:
                    vuln_info = cve_map[name]
                    if version in vuln_info.get("vulnerable_versions", []):
                        await self._alert_supply_chain_threat(
                            asset_id, name, version, rule, vuln_info, event
                        )

    async def _analyze_vendor_risk(self, event: Dict[str, Any]):
        """[EQ] BEC Detection: Monitor for impersonation patterns."""
        sender = event.get("sender", "")
        subject = event.get("subject", "").lower()
        content = event.get("content", "").lower()

        vendor_rules = self.rules.get("vendor_risk_rules", [])
        for rule in vendor_rules:
            # 1. Lookalike Domain Detection
            lookalike_map = rule.get("lookalike_domains", {})
            for target_domain, lookalikes in lookalike_map.items():
                for la in lookalikes:
                    if la in sender.lower():
                        await self._alert_vendor_threat(
                            sender,
                            rule,
                            event,
                            detail=f"Lookalike domain for {target_domain} detected.",
                        )
                        return  # Only one alert per event

            # 2. Key-phrase BEC Detection
            keywords = rule.get("keywords", [])
            matches = [kw for kw in keywords if kw in subject or kw in content]
            if matches:
                await self._alert_vendor_threat(
                    sender,
                    rule,
                    event,
                    detail=f"BEC Keywords detected: {', '.join(matches)}",
                )

    async def _alert_supply_chain_threat(
        self,
        asset: str,
        name: str,
        version: str,
        rule: Dict[str, Any],
        vuln_info: Dict[str, Any],
        event: Dict[str, Any],
    ):
        # [IQ] Doctrine Reference: QUILL-VANGUARD
        logger.info(
            f"Synchronized with doctrine: {get_soc_path('ethos', 'ethos_quill_vanguard.md')}"
        )
        logger.warning(
            f"[IQ] Supply Chain Threat on {asset}: {name}@{version} ({vuln_info['cve']})"
        )
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "severity": rule["severity"],
            "source_ip": "External",  # Supply chain is per-asset, not per-IP
            "description": f"{rule['description']} Found {name}@{version} (CVE: {vuln_info['cve']}: {vuln_info['title']}) on {asset}",
            "nist_control": "3.14.6",
            "mitre_ttp": "T1195",  # Supply Chain Compromise
            "raw_event": event,
        }
        self.triage_bus.push(alert)

    async def _alert_vendor_threat(
        self, sender: str, rule: Dict[str, Any], event: Dict[str, Any], detail: str = ""
    ):
        logger.warning(f"[EQ] Vendor Risk Alert from {sender}: {rule['name']}")
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "severity": rule["severity"],
            "source_ip": "External",
            "description": f"{rule['description']} Sender: {sender}. {detail}",
            "nist_control": "3.14.3",
            "mitre_ttp": "T1566",  # Phishing
            "raw_event": event,
        }
        self.triage_bus.push(alert)


if __name__ == "__main__":
    vanguard = VanguardAgent()
    asyncio.run(vanguard.run())
