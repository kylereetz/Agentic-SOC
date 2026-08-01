"""
QUILL-HUNTER: Proactive Threat Hunter.
Actively combs through shared RAG memory for hidden APTs.

IQ Capabilities:
- Hypothesis Engine (CISA/Intel to RAG query).
- Continuous Hunt (Re-scanning historical telemetry).
- Pattern Backtracking (Linking new leads to old events).

# Satisfies NIST 800-171 Rev 3:
# 3.14.6 - Monitor organizational systems to detect attacks.
# 3.14.3 - Monitor system security alerts and take action.
"""

import asyncio
import json
import logging
import os
import glob
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logger = logging.getLogger("RCA-Hunter")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - RCA Hunter - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

HUNTER_RULES_PATH = get_soc_path("configs", "hunter_rules.json")
BUS_ROOT = get_soc_path("bus")


class HunterAgent:
    """
    Proactive Hunter. Finds hidden threats in historical data.
    """

    def __init__(self, rules_path: str = HUNTER_RULES_PATH):
        self.in_bus = EventBus("hunting_events")
        self.triage_bus = EventBus("triage_alerts")
        self.rules = self._load_rules(rules_path)
        self.is_running = False

    def _load_rules(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Hunter rules: {e}")
            return {"hunting_playbooks": [], "intel_mappings": {}}

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Hunter Proactive Specialist started.")

        while self.is_running:
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                await self._process_hunting_event(event)
            else:
                await asyncio.sleep(1.0)

    async def _process_hunting_event(self, event: Dict[str, Any]):
        """[IQ] Ingest new intel lead and start a hunt."""
        event_type = event.get("event_type")

        if event_type == "new_intel_lead":
            hypothesis = event.get("hypothesis", "Unknown Intel")
            lookback = event.get("lookback_days", 30)
            target_keywords = event.get("keywords", [])

            logger.info(f"[IQ] Starting Hunt: {hypothesis} (Lookback: {lookback} days)")
            matches = await self._search_historical_data(target_keywords, lookback)

            if matches:
                await self._report_hunt_findings(hypothesis, matches, event)
            else:
                logger.info(
                    f"[VQ] Hunt complete for {hypothesis}: No matches found in history."
                )

    async def _search_historical_data(
        self, keywords: List[str], days: int
    ) -> List[Dict[str, Any]]:
        """
        Simulates querying the Librarian/RAG by scanning the 'processed' directories
         of all event buses for matching keywords.
        """
        matches = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Scan all channels in the bus root
        if not os.path.exists(BUS_ROOT):
            return []

        channels = [
            d for d in os.listdir(BUS_ROOT) if os.path.isdir(os.path.join(BUS_ROOT, d))
        ]

        for channel in channels:
            processed_dir = os.path.join(BUS_ROOT, channel, "processed")
            if not os.path.exists(processed_dir):
                continue

            for file_path in glob.glob(os.path.join(processed_dir, "event_*.json")):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        data_str = json.dumps(data).lower()

                        # Check timestamp
                        event_ts = data.get("timestamp")
                        if event_ts:
                            try:
                                dt = datetime.fromisoformat(
                                    event_ts.replace("Z", "+00:00")
                                )
                                if dt < cutoff:
                                    continue
                            except:
                                pass  # Ignore bad formats

                        # Keyword match
                        if any(kw.lower() in data_str for kw in keywords):
                            matches.append(
                                {
                                    "asset_id": data.get(
                                        "asset_id", data.get("source_ip", "Unknown")
                                    ),
                                    "match_timestamp": event_ts,
                                    "context": f"Found in channel: {channel}",
                                    "raw_data": data,
                                }
                            )
                except Exception:
                    continue

        return matches

    async def _report_hunt_findings(
        self, hypothesis: str, matches: List[Dict[str, Any]], lead_event: Dict[str, Any]
    ):
        """[EQ] Pattern Backtracking: Linking new leads to old events."""
        logger.warning(
            f"[EQ] HUNT SUCCESS: Found {len(matches)} historical matches for hypothesis: {hypothesis}"
        )

        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": "HUNTER_APT_MATCH",
            "rule_name": f"HUNT MATCH: {hypothesis}",
            "severity": "HIGH",
            "source_ip": matches[0].get("asset_id"),  # Representative
            "description": f"Proactive hunt identified {len(matches)} suspicious historical events matching the lead: {hypothesis}",
            "nist_control": "3.14.6",
            "mitre_ttp": "T1589",  # Gather Victim Identity Information (pre-attack)
            "metadata": {
                "matched_events": len(matches),
                "is_proactive_hunt": True,
                "intel_source": lead_event.get("intel_source"),
            },
            "raw_event": lead_event,
        }
        self.triage_bus.push(alert)


if __name__ == "__main__":
    hunter = HunterAgent()
    asyncio.run(hunter.run())
