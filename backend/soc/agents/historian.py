"""
SENTINEL-HISTORIAN: The Long-Term Dormancy Tracker (Rare Event Model)
Detects entities (IPs, Users, MACs) that awaken after a long period of silence.

Score 9.5 Features:
- SQ: Ultra-lightweight local SQLite persistence for long-dwell entity state.
- IQ: Automatically extracts multi-entity formats (IP, user) from incoming telemetry.
- EQ: Eliminates temporal noise by ignoring active entities; specifically hunts "threshold of silence" awakenings.
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Set, Tuple

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.network.service_mesh import ServiceMesh

logger = logging.getLogger("RCA-Historian")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA Historian - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

HISTORIAN_DB_PATH = get_soc_path("reports", "historian_memory.db")

# Default to 30 days of standard SILENCE (Long-dwell APTs)
DEFAULT_THRESHOLD_DAYS = float(os.environ.get("SILENCE_THRESHOLD_DAYS", 30))
THRESHOLD_SECONDS = DEFAULT_THRESHOLD_DAYS * 86400

# Overwrite for Lab testing (if set in env variables)
if os.environ.get("SILENCE_THRESHOLD_TEST_SECONDS"):
    THRESHOLD_SECONDS = float(os.environ["SILENCE_THRESHOLD_TEST_SECONDS"])

class HistorianAgent:
    """
    Tracks the 'last_seen' footprint of every known entity in the environment across months/years.
    Fires on the 'Threshold of Silence' mathematical anomaly.
    """
    def __init__(self):
        self.in_bus = EventBus("discovery_events")
        self.out_bus = EventBus("triage_alerts")
        self.is_running = False
        
        # Initialize SQLite DB
        self._init_db()

        # [IQ] Doctrine Reference: SENTINEL-HISTORIAN
        logger.info(f"Synchronized with doctrine: {get_soc_path('ethos', 'ethos_sentinel_historian.md')}")

    def _init_db(self):
        self.conn = ServiceMesh.connect_db(client_identity="historian", db_path=HISTORIAN_DB_PATH, negotiated_cipher="TLS_AES_256_GCM_SHA384")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_activity (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT,
                first_seen FLOAT,
                last_seen FLOAT
            )
        """)
        self.conn.commit()

    async def run(self):
        self.is_running = True
        logger.info(f"[SQ] SENTINEL-HISTORIAN awakened. Silence Threshold set to: {THRESHOLD_SECONDS} seconds.")
        
        while self.is_running:
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                await self._process_event(event)
            else:
                await asyncio.sleep(0.5)

    def _extract_entities(self, event: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Parses raw logs and structured OCSF payloads to isolate entity identifiers."""
        entities = []
        
        # OCSF Formats
        if "src_endpoint" in event and event["src_endpoint"]:
            ip = event["src_endpoint"].get("ip")
            if ip:
                entities.append((f"IP::{ip}", "ip_address"))
                
        if "user" in event and event["user"]:
            user = event["user"]
            entities.append((f"USER::{user}", "user_account"))
            
        # Legacy formats
        legacy_ip = event.get("ip", event.get("source_ip"))
        if legacy_ip and not any(e[0] == f"IP::{legacy_ip}" for e in entities):
            entities.append((f"IP::{legacy_ip}", "ip_address"))
            
        legacy_mac = event.get("mac")
        if legacy_mac:
            entities.append((f"MAC::{legacy_mac}", "mac_address"))
            
        return entities

    async def _process_event(self, event: Dict[str, Any]):
        entities = self._extract_entities(event)
        now = time.time()
        
        for entity_id, entity_type in entities:
            # Query Database
            cursor = self.conn.execute("SELECT last_seen FROM entity_activity WHERE entity_id = ?", (entity_id,))
            row = cursor.fetchone()
            
            if row is None:
                # Brand new entity, log it and move on.
                self.conn.execute(
                    "INSERT INTO entity_activity (entity_id, entity_type, first_seen, last_seen) VALUES (?, ?, ?, ?)",
                    (entity_id, entity_type, now, now)
                )
            else:
                last_seen = float(row["last_seen"])
                silence_duration = now - last_seen
                
                # [IQ] Rare Event Mathematic Trigger
                if silence_duration > THRESHOLD_SECONDS:
                    logger.warning(f"[IQ] Threshold of Silence broken for {entity_id}. Dormant for {silence_duration} seconds.")
                    
                    alert = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "rule_id": "HISTORIAN_DORMANT_WAKE",
                        "rule_name": "Dormant Entity Awakening",
                        "severity": "CRITICAL" if entity_type == "user_account" else "WARNING",
                        "classification": "suspicious",
                        "source_ip": entity_id.split("::")[1] if entity_type == "ip_address" else "Unknown",
                        "description": f"The entity '{entity_id}' communicated on the network after a dormant period of {round(silence_duration / 86400, 2)} days.",
                        "nist_control": "3.1.8",
                        "mitre_ttp": "T1078",
                        "semantic_detail": f"System threshold mandates activity within {THRESHOLD_SECONDS}s. This event violated standard lifecycle heuristics.",
                        "vector_id": "historian_dormancy_vector",
                        "raw_event": event
                    }
                    self.out_bus.push(alert)
                    
                # Upsert/Update last_seen timestamp
                self.conn.execute("UPDATE entity_activity SET last_seen = ? WHERE entity_id = ?", (now, entity_id))
        
        self.conn.commit()

if __name__ == "__main__":
    agent = HistorianAgent()
    asyncio.run(agent.run())
